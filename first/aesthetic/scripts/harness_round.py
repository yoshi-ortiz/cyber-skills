#!/usr/bin/env python3
"""What a round is allowed to be, judged before anything is rendered.

Scope, size, variant count, preview uniqueness, and the foundation an element
name belongs to. These are refusals, not renderings: they run early so a round
that cannot be judged fairly is stopped before a designer is asked to judge it.
The seam is that policy has no output of its own -- it raises or it returns.
"""

from __future__ import annotations

import re

from harness_core import (FOUNDATION_OF_WORD, FOUNDATION_ORDER,
                          GENERIC_ROUND_SLUGS, HarnessError)
from harness_strings import STRINGS, strings_for
from harness_ledger import display_name


def primary_foundation(cohort: set[str]) -> str:
    """Which foundation this round is really about -- one topic, not a batch."""
    if not cohort:
        return "core"
    counts: dict[str, int] = {}
    for element in cohort:
        key = foundation_of(element)
        counts[key] = counts.get(key, 0) + 1
    return min(counts, key=lambda k: (-counts[k], FOUNDATION_ORDER.get(k, 99)))


def round_tag_label(cohort: set[str], decisions: dict[str, object],
                      cohort_name: str = "", round_label: str = "") -> str:
    """What the round header names. Slugs like `objeto` become the object name."""
    if round_label.strip():
        return round_label.strip()
    slug = cohort_name.strip().lower().replace("-", " ")
    if slug and slug not in GENERIC_ROUND_SLUGS and len(slug.split()) <= 3:
        return cohort_name.strip()
    by_id = {e["element"]: e for e in decisions["elements"]}
    ordered = sorted(cohort, key=lambda e: (
        0 if by_id.get(e, {}).get("state") == "proposed" else 1, e))
    if not ordered:
        return cohort_name.strip() or "Round"
    entry = by_id.get(ordered[0], {"element": ordered[0]})
    desc = str(entry.get("description") or "")
    for pattern in (r"\b(?:es el|es la|es un|es una)\s+([^,.;]+)",
                    r"\b(?:the|a|an)\s+([^,.;]+)"):
        match = re.search(pattern, desc, re.I)
        if match:
            phrase = match.group(1).strip()
            words = phrase.split()
            if words:
                label = words[0] if len(words) == 1 else " ".join(words[:2])
                return label[0].upper() + label[1:]
    name = display_name(entry)
    words = name.split()
    return " ".join(words[:3]) if len(words) > 4 else name


def foundation_of(element: str) -> str:
    """Which design-system foundation an element id belongs to.

    Reads the id's leading segments, most specific first: `family.mark.dotmatrix`
    files under illustration on `mark` rather than falling through on `family`.
    """
    parts = [p for p in re.split(r"[.\-_]", element.lower()) if p]
    for part in parts:
        if part in FOUNDATION_OF_WORD:
            return FOUNDATION_OF_WORD[part]
    return "core"
def check_asks(asks: str, cohort: set[str], language: str | None = None) -> None:
    """A cohort without a real question is a questionnaire nobody can answer."""
    if not cohort:
        return
    text = asks.strip()
    generics = {STRINGS["en"]["zone-round-note"].casefold(),
                STRINGS["es"]["zone-round-note"].casefold()}
    if language:
        generics.add(strings_for(language)["zone-round-note"].casefold())
    if not text:
        return
    if text.casefold() in generics:
        raise HarnessError(
            "this round has no question. Pass --asks \"<the one thing to judge>\", "
            "not the zone's purpose line. The last PNG and the user's last rank name that move.")


MAX_COHORT_SIZE = 6


def check_cohort_size(cohort: set[str], max_size: int = MAX_COHORT_SIZE) -> None:
    """A round nobody can finish reading is not a round, it's a backlog.

    `SKILL.md` and `loop.md` have said "3-6 element cohort" in prose since
    this file's own history, and every round drifted past it anyway because
    nothing enforced it: the round zone never folds ("the round is the ask
    and must never be hidden"), so a large cohort renders every card open,
    unfoldable, and slower to draw and shoot than the reader can use.
    """
    if len(cohort) <= max_size:
        return
    raise HarnessError(
        f"this round's cohort has {len(cohort)} elements, over the {max_size}-element "
        "limit. Split it into two rounds instead of asking the user to judge all of "
        "them at once -- see SKILL.md's '3-6 element cohort' convention.")
# The choices that ARE the direction. They belong together whatever their
# lifecycle state: a type system is judged as a system -- the pairings, the
# scale, the palette against the faces -- and scattering half of it into a
# backlog because it is still `proposed` makes that judgement impossible.
FUNDAMENTAL_FOUNDATIONS = ("core", "palette", "typography")


def zone_of(entry: dict[str, object], cohort: set[str]) -> str:
    """Four zones, and every element is in exactly one.

    A flat list of twenty-eight rows cannot say which are settled, which are
    being asked about now, and which were turned down -- so the user re-reads
    decisions they already made looking for the three that matter.
    """
    if entry["element"] in cohort:
        return "round"
    # A thumb up says the DIRECTION is right, so the element cannot be a wrong
    # direction -- whatever became of this particular drawing. Superseded work
    # that the user still likes is history, not an antipattern, and filing it
    # here told the next agent to stop pursuing an idea the user endorsed.
    if entry.get("sentiment") == "dislike":
        return "antipattern"
    if entry["state"] in ("rejected", "superseded"):
        return "backlog" if entry.get("sentiment") == "like" else "antipattern"
    if foundation_of(entry["element"]) in FUNDAMENTAL_FOUNDATIONS:
        return "fundamentals"
    return "backlog"


def incumbent_of(element: str, known: set[str]) -> str:
    """The element a proposal is competing with, read off its own id.

    `cover.ring.kicker.antetitulo-arco` is a new drawing of
    `cover.ring.kicker` -- the convention the skill already requires. Without
    showing that pair the user is asked to score a drawing against nothing:
    "is this good?" has no answer, where "is this better than what stands?"
    does. Longest matching prefix wins, so a third pass compares against the
    second rather than the original.
    """
    parts = element.split(".")
    for cut in range(len(parts) - 1, 0, -1):
        candidate = ".".join(parts[:cut])
        if candidate in known:
            return candidate
    return ""


def lineage_root_of(element: str, known: set[str]) -> str:
    """The original idea an element descends from, following incumbents up.

    `incumbent_of` answers one step -- what this drawing replaces. A third and
    fourth pass at the same idea form a chain, and the chart needs the whole
    chain to say "these five bars are five attempts at one thing" rather than
    five separate concerns.
    """
    seen = {element}
    current = element
    while True:
        parent = incumbent_of(current, known - {current})
        if not parent or parent in seen:
            return current
        seen.add(parent)
        current = parent


def parent_item_of(element: str) -> str:
    """The item a round's work sits under: the id's first dotted segment.

    `cover.layout.two-column` and `cover.ring.kicker` are both work on the
    cover. `type.heading.serif` is not -- it is a different parent item, and a
    round that proposes both is redesigning two things at once.
    """
    return element.split(".")[0]


def check_round_stays_in_scope(cohort: set[str]) -> None:
    """Refuse a round whose cohort spans more than one parent item.

    A round is one object being worked on. Left unenforced, an inference pass
    reads a whole ledger, reasons across every surface in it, and returns a
    thin proposal for each -- the expensive failure: a long run, wide reasoning
    and minimal drawings, because attention that should have gone into one
    cover went into six unrelated things.

    `check_cohort_size` caps how MANY elements a round may carry and says
    nothing about whether they belong together; the foundation-span check in
    `render_article` asks a related question but can be answered with `--asks`.
    Scope is not a prose problem, so this one has no escape hatch: a round that
    spans two parent items is two rounds.
    """
    if len(cohort) < 2:
        return
    by_item: dict[str, list[str]] = {}
    for element in sorted(cohort):
        by_item.setdefault(parent_item_of(element), []).append(element)
    if len(by_item) == 1:
        return
    spans = "; ".join(f"{item} ({', '.join(members)})"
                      for item, members in sorted(by_item.items()))
    raise HarnessError(
        f"this round spans {len(by_item)} parent items: {spans}. A round is one "
        "object -- a cover, a type system, an illustration set -- so proposing "
        "across two of them oversteps the one being judged and spends the run "
        "on breadth the user did not ask for. Split it into one round per "
        "parent item.")


MAX_VARIANTS_PER_IDEA = 3


def check_round_earns_its_place(decisions: dict[str, object], cohort: set[str]) -> None:
    """Refuse a round that sprays new ideas instead of improving ranked ones.

    `loop.md` says polish liked-but-low-scoring work first, and says it in
    prose, so every session drifted past it. The ledger shows what that cost:
    eighteen elements the user liked and scored 1-2 sat untouched while the
    agent proposed eleven fresh siblings, and the mean score FELL to 1.56. A
    thumb up on a two-star drawing is the clearest instruction the ledger can
    carry -- the idea is right, the drawing is not there yet -- and answering
    it with a brand-new idea throws the instruction away.

    Two refusals, both satisfiable by doing the right thing rather than by
    passing a flag:

    1. A round of nothing but new ids, while liked-and-low work is waiting.
       Redrawing one of them (`<parent>.<slug>`) satisfies this, because the
       redraw's incumbent is the element being polished.
    2. More than `MAX_VARIANTS_PER_IDEA` new drawings of the SAME incumbent
       in one round. Up to that many are allowed and render grouped
       together (see `render_article`'s idea-grouping) -- comparing 2-3
       genuine variants of one idea side by side is the whole point of a
       round. Past that cap it becomes the `anti-slop` wallpaper tell again:
       the user cannot usefully compare a wall of near-identical guesses,
       only pick the least-bad one.
    """
    live = [e for e in decisions["elements"] if e["state"] in ("approved", "proposed")]
    known = {e["element"] for e in decisions["elements"]}
    polish = {e["element"] for e in live
              if e.get("sentiment") == "like" and int(e.get("stars") or 0) <= 2}

    # A cohort member is "new" when the ledger has never seen it. Its incumbent
    # is the standing element it redraws, read off its own dotted id.
    incumbents = {c: incumbent_of(c, known - {c}) for c in cohort}
    # Counted against the LEDGER, not just against this cohort. Counting the
    # cohort alone let an idea accumulate variants one round at a time and
    # never trip the cap: two this round, two the next, and nothing ever saw
    # four at once. A real ledger reached seven live drawings under one
    # `family.tab` that way, which is the "too many for the same element"
    # scope failure -- the round was small every time, the family was not.
    live_ids = {e["element"] for e in live}
    standing = {}
    for inc in {i for i in incumbents.values() if i}:
        prefix = inc + "."
        standing[inc] = len([e for e in live_ids
                             if e.startswith(prefix) and e not in cohort])
    overrun = sorted(
        inc for inc in standing
        if standing[inc] + sum(1 for v in incumbents.values() if v == inc)
        > MAX_VARIANTS_PER_IDEA)
    if overrun:
        detail = ", ".join(
            f"{inc} ({standing[inc]} already standing "
            f"+ {sum(1 for v in incumbents.values() if v == inc)} proposed here)"
            for inc in overrun)
        raise HarnessError(
            "this round would leave more than " + str(MAX_VARIANTS_PER_IDEA)
            + " live drawings of one idea: " + detail
            + ". That stops being a choice and becomes wallpaper -- the user cannot "
            "usefully compare a wall of near-identical guesses. Supersede the ones this "
            "round replaces (`decide --supersedes`) instead of stacking another variant "
            "beside them, or ask about a different element.")

    # Asking about nothing is not a round proposing new ideas over unanswered
    # feedback; it is redrawing the page as it already stands. Refusing it left
    # no way to regenerate the article after a code change without inventing a
    # cohort, which is why a workaround snippet lived in ROADMAP.md.
    if not cohort or not polish:
        return
    touches_polish = any(c in polish or incumbents.get(c) in polish for c in cohort)
    if touches_polish:
        return
    waiting = sorted(polish)
    raise HarnessError(
        f"{len(waiting)} element(s) carry a thumb up and a low score -- the user said the idea is "
        "right and the drawing is not there yet -- and this round improves none of them:\n  "
        + "\n  ".join(waiting[:8])
        + (f"\n  ... and {len(waiting) - 8} more" if len(waiting) > 8 else "")
        + "\nRedraw one as `<that-id>.<slug>` so it is scored against what it replaces, or put the "
          "element itself in the cohort to re-ask. New ideas proposed over unanswered feedback are "
          "why the ledger is growing and the scores are not.")


def check_unique_cohort_previews(decisions: dict[str, object], cohort: set[str]) -> None:
    """A copied drawing with a new id is not another proposal."""
    seen: dict[str, str] = {}
    duplicates: list[tuple[str, str]] = []
    for entry in decisions["elements"]:
        element = str(entry["element"])
        if element not in cohort:
            continue
        preview = entry.get("preview") or {}
        digest = str(preview.get("sha256") or "")
        if not digest:
            continue
        if digest in seen:
            duplicates.append((seen[digest], element))
        else:
            seen[digest] = element
    if duplicates:
        pairs = ", ".join(f"{first} / {second}" for first, second in duplicates)
        raise HarnessError(
            "this round presents the same drawing under different names: " + pairs +
            ". Keep one proposal or draw a materially different alternative.")


ZONES = ("round", "fundamentals", "backlog", "antipattern")
# Only the backlog earns a second level of navigation: it is the long one, and
# the reader arrives at it looking for a particular surface.
# Both long zones earn a second level. Only the backlog had one, so the
# critical components -- the section a designer scrolls hardest through --
# offered no way to reach a surface except by scrolling past every other one.
SUBNAV_ZONES = ("fundamentals", "backlog")
# The long zone folds. The round is the ask and must never be hidden; the
# fundamentals are the system on display; antipatterns are already quiet.
FOLDING_ZONES = ("fundamentals", "backlog", "antipattern")
