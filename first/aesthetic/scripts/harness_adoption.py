#!/usr/bin/env python3
"""Adoption: folding the companion's clicks back into the ledger.

The cursor that remembers how far a ledger has been read, the drain that pulls
new interactions off it, and the fold that turns them into stars and sentiment.
The seam is the direction of travel: every other ledger write starts with the
agent, and this is the only one that starts with the user.
"""

from __future__ import annotations

import json
from pathlib import Path

from harness_core import (HarnessError, KEEP_BOOKMARK, KEEP_SENTIMENT,
                          PROBE_ELEMENT, SENTIMENTS, STAR_RANGE, ZERO_STARS,
                          is_within, ledger_digest, write_json)
from harness_ledger import load_decisions, record_decision, score_zero


def ledger_cursor_key(project_root: Path, ledger_path: Path) -> str:
    """Name a companion ledger without baking an absolute path into decisions.json."""
    resolved = ledger_path.resolve()
    root = project_root.resolve(strict=True)
    return str(resolved.relative_to(root)) if is_within(resolved, root) else resolved.name


def drain_companion(project_root: Path, ledger_path: Path | None = None) -> tuple[int, int]:
    """Read everything the user typed or clicked, from every companion inbox.

    The companion queues; nothing applies a queue on its own. An agent that
    forgets this step publishes a new round over the user's ranks and over the
    brief answer that named what they actually asked for, and neither the
    agent nor any gate can tell, because a queue nobody drained looks exactly
    like a user who said nothing.
    """
    base = project_root / ".superpowers" / "brainstorm"
    ledger = ledger_path if ledger_path is not None else base / "decisions.jsonl"
    # A project nobody has clicked in yet has no ledger. That is an empty
    # queue, not a broken one, and refusing it would make `article` impossible
    # to run on a fresh project.
    adopted, skipped = (adopt_companion(project_root, ledger)
                        if Path(ledger).is_file() else (0, 0))
    try:
        import brief_workflow
        said, _ = brief_workflow.adopt_brief_inbox(
            project_root, base / brief_workflow.BRIEF_INBOX_FILE)
        if said:
            print(f"Adopted {said} brief answer(s).")
    except (ImportError, OSError, ValueError):
        pass
    return adopted, skipped


def adopt_companion(project_root: Path, ledger_path: Path) -> tuple[int, int]:
    """Fold the companion's durable ledger into the harness ledger.

    The companion records what the user actually clicked and ranked. Without this
    step an agent re-types those decisions by hand, which is where design-element
    ids drift and elements in standing get silently rebuilt.

    Only lines added since the last adopt are replayed. Replaying the whole
    ledger every run re-litigates settled history: `decide --source user` writes
    straight to decisions.json and never appears in this file, so an approval
    granted after the user un-ticked a box has no position in the chronological
    replay -- and the older `proposed` click lands back on top of it. That
    silently downgraded seven standing elements in one run.
    """
    if not ledger_path.is_file():
        raise HarnessError(f"companion ledger not found: {ledger_path}")

    def is_star(value: object) -> bool:
        if not isinstance(value, int) or isinstance(value, bool):
            return False
        return value == ZERO_STARS or STAR_RANGE[0] <= value <= STAR_RANGE[1]

    output = project_root.resolve(strict=True) / "spec" / "design-harness"
    decisions = load_decisions(output)
    existing = {e["element"]: dict(e) for e in decisions["elements"]}
    lines = ledger_path.read_text(encoding="utf-8").splitlines()
    key = ledger_cursor_key(project_root, ledger_path)
    cursor = (decisions.get("adoptedLedgers") or {}).get(key) or {}
    start = cursor.get("lines") or 0
    # The mark is only trustworthy if the lines it claims to have consumed are
    # still the same lines. A companion restart writes a fresh ledger at the
    # same path; trusting a stale count there would skip real clicks, so an
    # unrecognised prefix falls back to a full replay.
    if not isinstance(start, int) or not 0 <= start <= len(lines) or \
            ledger_digest(lines[:start]) != cursor.get("digest"):
        start = 0
    accepted: list[tuple[int, int, dict[str, object]]] = []
    resets: list[tuple[int, int, str]] = []
    skipped = 0
    for index, line in enumerate(lines):
        line = line.strip()
        if index < start or not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            skipped += 1
            continue
        element = event.get("element")
        if element == PROBE_ELEMENT:
            skipped += 1
            continue
        stars, sentiment = event.get("stars"), event.get("sentiment")
        has_sentiment = "sentiment" in event
        if event.get("type") == "reset" or event.get("reset") is True:
            # The zero-star control. "This is bad" is a rating the user must be
            # able to give, and the 1-5 strip cannot express it.
            resets.append((int(event.get("timestamp") or 0), index, element))
            continue
        # An interaction carrying no design-element id names a screen-local
        # label, not a binding element. Report it rather than guessing an id.
        if not element or not isinstance(element, str):
            skipped += 1
            continue
        # Companions spell the completed status differently, and un-completing
        # arrives as `proposed`. Both were being skipped: 15 real toggle-offs in
        # one ledger were discarded because `proposed` was not on this list, so
        # un-ticking a box did nothing and the tick came back on the next adopt.
        if event.get("verdict") == "reviewed":
            event["verdict"] = "completed"
        if event.get("verdict") not in (None, "approved", "rejected", "completed", "proposed"):
            skipped += 1
            continue
        if sentiment is not None and sentiment not in SENTIMENTS:
            skipped += 1
            continue
        # `"sentiment": null` present is a WITHDRAWAL and carries signal; the key
        # missing entirely means the event never spoke about the thumb. The
        # rehydrate script has always drawn this line (`if('sentiment' in ev)`)
        # -- adopt did not, so the browser cleared the chip and the ledger kept
        # the like forever.
        if not has_sentiment and "bookmark" not in event and event.get("verdict") is None \
                and not is_star(stars):
            skipped += 1
            continue
        # Replay order is fixed by (timestamp, file position) so adopting the
        # same ledger twice always yields the same ledger.
        stamp = event.get("timestamp")
        stamp = stamp if isinstance(stamp, (int, float)) and not isinstance(stamp, bool) else 0
        accepted.append((int(stamp), index, event))

    # Resolve each event against the ledger AS OF that event, not as of the start
    # of the batch. A rank and a verdict on the same element at the same
    # millisecond (max stars auto-fires a completed toggle) used to be resolved
    # against the same pre-batch snapshot, so the verdict -- carrying no stars of
    # its own -- fell back to the pre-batch rank and overwrote the star just set.
    for _, _, event in sorted(accepted, key=lambda row: (row[0], row[1])):
        element = event["element"]
        stars, sentiment = event.get("stars"), event.get("sentiment")
        has_sentiment = "sentiment" in event
        explicit = event.get("verdict")
        prior = existing.get(element, {})
        if explicit in ("approved", "rejected", "completed", "proposed"):
            # Only an explicit verdict control moves state. A star never does.
            verdict = explicit
        else:
            # Scores and thumbs leave state alone: an element already standing
            # stays standing, and a new one arrives as `proposed` for review.
            verdict = prior.get("state") or "proposed"
        # Only the dedicated rank interaction establishes rank provenance.
        # Older companions omitted `type`, so a numeric non-sentiment event is
        # accepted as a rank for compatibility. A thumb event carrying stars=0
        # is never a rank: that historical UI bug poisoned coverage otherwise.
        establishes_rank = event.get("type") == "rank" or (
            event.get("type") is None and not has_sentiment and is_star(stars))
        rank = stars if establishes_rank and is_star(stars) else prior.get("stars", 0)
        rank_was_set = bool(establishes_rank or prior.get("scored"))
        withdrawn = "sentiment" in event and sentiment is None
        bookmark_only = "bookmark" in event and not has_sentiment and event.get("verdict") is None \
            and not is_star(stars)
        evidence = str(event.get("text") or "").strip() or (
            (f"companion {'bookmarked' if event.get('bookmark') else 'unbookmarked'} it"
             if bookmark_only else
             f"companion {sentiment}: {rank} star" if sentiment else
             (f"companion withdrew the thumb: {rank} star" if withdrawn
              else f"companion rank: {rank} star")))
        record_decision(project_root, element, verdict, rank, evidence[:400], [],
                        source="user", scored=rank_was_set,
                        sentiment=sentiment if "sentiment" in event else KEEP_SENTIMENT,
                        bookmarked=event["bookmark"] if "bookmark" in event else KEEP_BOOKMARK)
        existing[element] = dict(prior, element=element, state=verdict, stars=rank,
                                 source="user", scored=rank_was_set)
    for _, _, element in sorted(resets, key=lambda row: (row[0], row[1])):
        score_zero(project_root, element)
    # Re-read: every record_decision above rewrote the file underneath us.
    decisions = load_decisions(output)
    ledgers = dict(decisions.get("adoptedLedgers") or {})
    ledgers[key] = {"lines": len(lines), "digest": ledger_digest(lines)}
    decisions["adoptedLedgers"] = ledgers
    write_json(output / "decisions.json", decisions)
    return len(accepted), skipped
