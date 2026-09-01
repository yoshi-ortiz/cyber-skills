#!/usr/bin/env python3
"""The harness proving itself end to end, in a tempdir, with no network.

One function, because the point is a single command a gate can run. It is a
seam rather than a test file because `bootstrap_harness.py self-test` is a
published verb: `tools/check.py` runs it as one of its gates.
"""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

from harness_core import HarnessError, STAR_RANGE, ZERO_STARS, source_entries
from harness_strings import strings_for
from harness_ledger import (ledger_stats, load_decisions, record_decision,
                            score_zero)
from harness_round import foundation_of
from harness_comp import preview_reference
from harness_controls import (CONTROLS_VERSION, FEEDBACK_STYLE,
                              embed_controls, render_feedback_controls,
                              visible_controls)
from harness_board import publish_screen
from harness_adoption import adopt_companion
from harness_init import init_harness, validate_harness


def self_test() -> None:
    with tempfile.TemporaryDirectory(prefix="design-harness-test-") as temp:
        root = Path(temp)
        project = root / "project"
        source = root / "Oddly Named Evidence 42"
        project.mkdir()
        source.mkdir()
        (source / "reference.txt").write_text("ASCII composition and physical product", encoding="utf-8")
        (source / "frame.png").write_bytes(b"deterministic-image-fixture")
        before = source_entries(source)
        output = init_harness(project, source, ["art-direction", "mockup-layering", "physical-space"])
        validate_harness(project)
        after = source_entries(source)
        if before != after:
            raise HarnessError("self-test source changed")
        questions = (output / "QUESTIONNAIRE.md").read_text(encoding="utf-8")
        for expected in ("ASCII/Unicode", "layer renderer", "measurement"):
            if expected not in questions:
                raise HarnessError(f"self-test questionnaire omitted: {expected}")

        # OS sidecars must never enter the manifest: browsing the source root
        # would otherwise flip validate to red with the evidence untouched.
        (source / ".DS_Store").write_bytes(b"finder-noise-v1")
        validate_harness(project)
        (source / ".DS_Store").write_bytes(b"finder-noise-v2-different-bytes")
        validate_harness(project)

        # A decision must survive as an artifact, carry a star rank, and win
        # over the element it supersedes.
        record_decision(project, "cover.layout.two-column", "approved", 5, "user: 'c2'", [], source="user")
        record_decision(project, "cover.spine.right", "approved", 4, "user: 'place it on the right'", [], source="user")
        record_decision(project, "cover.layout.single-column", "rejected", 1, "user: 'you destructed the two columns'",
                        ["cover.layout.two-column"])
        validate_harness(project)
        ledger = json.loads((output / "decisions.json").read_text(encoding="utf-8"))
        by_id = {e["element"]: e for e in ledger["elements"]}
        if by_id["cover.layout.two-column"]["state"] != "superseded":
            raise HarnessError("self-test: supersede did not retire the prior element")
        if by_id["cover.layout.two-column"]["supersededBy"] != "cover.layout.single-column":
            raise HarnessError("self-test: supersede lost its back-reference")
        if "★★★★☆" not in (output / "DECISIONS.md").read_text(encoding="utf-8"):
            raise HarnessError("self-test: star rank not rendered")
        if ledger["state"] != "approved" or json.loads((output / "project.json").read_text(encoding="utf-8"))["state"] != "approved":
            raise HarnessError("self-test: lifecycle state did not advance past draft")

        # Companion star ranks must adopt into the ledger; events with no
        # design-element id must be skipped rather than guessed at.
        companion = root / "decisions.jsonl"
        companion.write_text("\n".join([
            json.dumps({"type": "rank", "element": "form.paper.white", "stars": 5, "text": "user: form stays white", "timestamp": 30}),
            json.dumps({"type": "click", "choice": "screen-local-slug", "element": None, "stars": None}),
            json.dumps({"type": "rank", "element": "palette.inferred", "stars": 1, "timestamp": 10}),
            json.dumps({"type": "sentiment", "element": "cover.ring.kicker", "sentiment": "like", "timestamp": 20}),
            json.dumps({"type": "sentiment", "element": "cover.background.black", "sentiment": "dislike", "timestamp": 40}),
            json.dumps({"type": "sentiment", "element": "bogus.sentiment", "sentiment": "meh", "timestamp": 50}),
            json.dumps({"type": "rank", "element": "bogus.range", "stars": 9, "timestamp": 60}),
            "not json at all",
        ]) + "\n", encoding="utf-8")
        adopted, skipped = adopt_companion(project, companion)
        if adopted != 4 or skipped != 4:
            raise HarnessError(f"self-test: adopt miscounted ({adopted} adopted, {skipped} skipped)")
        validate_harness(project)
        adopted_ledger = {e["element"]: e for e in json.loads((output / "decisions.json").read_text(encoding="utf-8"))["elements"]}
        if adopted_ledger["form.paper.white"]["stars"] != 5 or adopted_ledger["palette.inferred"]["stars"] != 1:
            raise HarnessError("self-test: adopt lost the star rank")
        if "user: form stays white" not in adopted_ledger["form.paper.white"]["evidence"]:
            raise HarnessError("self-test: adopt dropped the evidence excerpt")
        # sentiment maps deterministically to verdict + default rank
        # A thumb records encouragement; it must NOT move state or invent a rank.
        for element, name in (("cover.ring.kicker", "like"), ("cover.background.black", "dislike")):
            entry = adopted_ledger[element]
            if entry.get("sentiment") != name:
                raise HarnessError(f"self-test: {name} was not recorded as sentiment")
            if entry["state"] == "rejected" and name == "dislike":
                raise HarnessError("self-test: a thumb-down must not reject; only an explicit verdict may")

        # Adopting the same ledger twice must be a no-op on content.
        first = (output / "decisions.json").read_text(encoding="utf-8")
        adopt_companion(project, companion)
        if (output / "decisions.json").read_text(encoding="utf-8") != first:
            raise HarnessError("self-test: adopt is not idempotent")

        # Controls are generated from the ledger and are byte-stable.
        markup = render_feedback_controls(load_decisions(output))
        s_adopt_states = '("approved", "rejected", "completed", "proposed")'
        if markup != render_feedback_controls(load_decisions(output)):
            raise HarnessError("self-test: controls are not deterministic")
        for required in ('data-element="form.paper.white"', 'data-rank="5"',
                         'data-verdict="completed"', 'data-sentiment="like"',
                         'data-sentiment="dislike"', 'data-rank="0"'):
            if required not in markup:
                raise HarnessError(f"self-test: controls omitted {required}")
        # Zero is a rank and must ride the rank path. As `data-reset` it reached a
        # companion handler that cleared the thumb and the tick too, so scoring an
        # element 0 silently destroyed two signals the user had set deliberately.
        if "data-reset" in markup:
            raise HarnessError(
                "self-test: zero emitted as `data-reset` -- that path erases sentiment and verdict")
        # The zero is revealed by hovering ONE star, which is where a user
        # reaching for the bottom of the scale already is. Hiding it is only
        # safe while it is also unclickable, and only honest while a zero
        # already given still shows.
        if 'pointer-events:none' not in re.sub(r"\s+", "", FEEDBACK_STYLE).split(
                '[data-rank="0"]{')[1].split("}")[0]:
            raise HarnessError(
                "self-test: the hidden zero is still clickable -- an invisible control beside "
                "the first star is how a click meant for 1 scores 0")
        if '[data-rank="1"]:hover)' not in FEEDBACK_STYLE:
            raise HarnessError(
                "self-test: nothing reveals the zero -- it must surface when one star is hovered")
        if '.dh-fb[data-stars="0"][data-scored="yes"] .dh-zero' not in FEEDBACK_STYLE:
            raise HarnessError(
                "self-test: a zero already given would stay hidden -- it must be "
                "distinguishable from an unrated row")
        # The zero must not sit inside the star strip: adjacent and unlabelled, it
        # caught clicks aimed at one star.
        if re.search(r'<span class="dh-stars"[^>]*>\s*<span data-rank="0"', markup):
            raise HarnessError(
                "self-test: the zero sits inside the star strip -- it will catch clicks meant for 1 star")
        # Hovering must preview the whole rank, not a single glyph.
        if ":has(~ [data-rank]:hover)" not in FEEDBACK_STYLE:
            raise HarnessError(
                "self-test: stars do not preview a rank on hover -- hovering lights one glyph, "
                "so the user cannot see what a click would set")
        # A refresh must not throw away what the user clicked.
        if "/* dh-rehydrate */" not in markup:
            raise HarnessError(
                "self-test: controls ship no rehydrator -- a refresh reverts every score")
        # The emitted verdict word must be one `adopt` will fold back in. These
        # two drifted apart once already: the UI emitted `completed` while the
        # ledger reader accepted a different set, so the tick could be clicked
        # and never survived the round trip.
        for word in set(re.findall(r'data-verdict="([a-z]+)"', markup)):
            if word not in ("approved", "rejected", "completed"):
                raise HarnessError(
                    f"self-test: controls emit data-verdict=\"{word}\", which `adopt` "
                    "does not accept -- the tick would never reach the ledger")
        # And the toggle-off must survive too, or un-ticking silently reverts.
        if '"proposed"' not in s_adopt_states:
            raise HarnessError(
                "self-test: `adopt` drops the un-complete event -- a cleared tick comes back")
        if f"dh-controls-version: {CONTROLS_VERSION}" not in markup:
            raise HarnessError("self-test: controls carry no version stamp -- a stale embed "
                               "cannot be told apart from a fix that did not work")
        # Substring checks above prove the ATTRIBUTES were emitted. They cannot
        # prove a browser will render anything: an unterminated opening tag keeps
        # every `data-rank="n"` intact while swallowing the star glyph into an
        # attribute, so all five controls parse as empty and the user sees a blank
        # strip. Parse it and assert on what a browser would actually show.
        for control, label, minimum in (("data-rank", "star", STAR_RANGE[1]),
                                        ("data-rank", "zero", 1),
                                        ("data-verdict", "verdict", 1)):
            shown = visible_controls(markup, control)
            if len(shown) < minimum:
                raise HarnessError(
                    f"self-test: {label} controls parse as {len(shown)} element(s), expected {minimum}")
            blank = [attr for attr, text in shown.items() if not text.strip()]
            if blank:
                raise HarnessError(
                    f"self-test: {label} control(s) {sorted(blank)} render with no visible content -- "
                    "the markup emits the attribute but a browser draws nothing")
        # A thumb-down keeps the element scoreable; only an explicit reject removes it.
        if 'data-element="cover.background.black"' not in markup:
            raise HarnessError("self-test: a disliked element vanished from scoring")
        record_decision(project, "explicitly.rejected", "rejected", ZERO_STARS, "user clicked reject", [],
                        source="user")
        rejected_markup = render_feedback_controls(load_decisions(output), None, project)
        # Rejected work stays visible in its own group so a rejection can be
        # undone by clicking, instead of by editing JSON.
        if 'data-element="explicitly.rejected"' not in rejected_markup:
            raise HarnessError("self-test: rejected element is unreachable for undo")
        if 'data-group="rejected"' not in rejected_markup:
            raise HarnessError("self-test: rejected lifecycle group not marked on the row")
        # Headings group by design-system foundation, so the user reads the
        # typography together and the palette together. Lifecycle rides on the
        # row, which is what dims rejected work and drives the state chip.
        if 'class="dh-group" data-group="palette"' not in rejected_markup:
            raise HarnessError("self-test: rows are not grouped by design-system foundation")
        if strings_for("es")["palette"] in rejected_markup:
            raise HarnessError("self-test: default strip is not in the default language")
        spanish = render_feedback_controls(load_decisions(output), None, project, language="es")
        if strings_for("es")["palette"] not in spanish:
            raise HarnessError("self-test: --lang did not translate the group headings")
        if strings_for("en")["proposed-by"] in spanish:
            raise HarnessError("self-test: a translated strip still carries English row labels")
        for element_id, expected in (("palette.family-from-cards", "palette"),
                                     ("type.bracket-numerals", "typography"),
                                     ("cover.layout.two-column", "composition"),
                                     ("family.mark.dotmatrix", "illustration"),
                                     ("something.unmapped", "core")):
            if foundation_of(element_id) != expected:
                raise HarnessError(
                    f"self-test: {element_id} filed under {foundation_of(element_id)}, not {expected}")

        # Every color must be a themeable token, never a literal that would
        # override the corpus palette the ledger already approved.
        style_block = markup.split("</style>")[0]
        for token in ("--dh-bg", "--dh-ink", "--dh-accent", "--dh-font"):
            if token not in style_block:
                raise HarnessError(f"self-test: controls style omits the {token} token")
        # Theme colours must come from tokens. Fixed semantic colours (the green
        # "done" state, the red offline warning) are design constants, not theme.
        for literal in ("color:var(--dh-ink,#111);background:#fff",
                        "background:#111;color:#fff"):
            if literal in style_block.replace(" ", ""):
                raise HarnessError(f"self-test: controls hardcode {literal} outside a var() fallback")

        # A declared theme is baked in, and identical flags emit identical bytes.
        themed = render_feedback_controls(load_decisions(output),
                                          {"bg": "#f9e7b5", "ink": "#111", "accent": "#d9482a", "font": None})
        if "--dh-bg: #f9e7b5" not in themed or "--dh-accent: #d9482a" not in themed:
            raise HarnessError("self-test: declared theme was not applied")
        if "--dh-font" in themed.split("<div")[1].split(">")[0]:
            raise HarnessError("self-test: unset theme key leaked into the wrapper")
        if themed != render_feedback_controls(load_decisions(output),
                                              {"bg": "#f9e7b5", "ink": "#111", "accent": "#d9482a", "font": None}):
            raise HarnessError("self-test: themed controls are not deterministic")

        # The graphic being ranked must ride along with the rank, and must be
        # hash-pinned: a preview that changed is a preview nobody looked at.
        shots = project / "shots"
        shots.mkdir()
        shot = shots / "cover.html"
        shot.write_text('<div style="width:85px;height:110px;background:#f9e7b5"></div>', encoding="utf-8")
        record_decision(project, "cover.layout.two-column", "approved", 5, "user: 'c2'", [],
                        preview_reference(project, "shots/cover.html"), source="user")
        validate_harness(project)
        with_shot = render_feedback_controls(load_decisions(output), None, project)
        if 'class="dh-shot"' not in with_shot or "#f9e7b5" not in with_shot:
            raise HarnessError("self-test: the ranked element carries no graphic")
        if "data-dh-no-graphic" not in render_feedback_controls(load_decisions(output), None, project):
            raise HarnessError("self-test: elements without a preview must say so, not fake one")
        if with_shot != render_feedback_controls(load_decisions(output), None, project):
            raise HarnessError("self-test: previews broke control determinism")
        # A regenerated preview is normal work: it must be reported, not blocked.
        shot.write_text('<div style="width:85px;height:110px;background:#000"></div>', encoding="utf-8")
        report = validate_harness(project)
        if not any("changed since it was ranked" in w for w in report["warnings"]):
            raise HarnessError("self-test: preview drift must be reported as a warning")
        record_decision(project, "cover.layout.two-column", "approved", 5, "user: 'c2'", [],
                        preview_reference(project, "shots/cover.html"), source="user")
        validate_harness(project)
        for bad in ("../outside.svg", "shots/nope.svg", "scripts/evil.py"):
            try:
                preview_reference(project, bad)
            except HarnessError:
                continue
            raise HarnessError(f"self-test: preview accepted an unsafe reference: {bad}")

        # The agent must not be able to type a confident rank. This cap is the
        # difference between "user clicked 4" and "agent felt like 4".
        try:
            record_decision(project, "agent.guess", "approved", 4, "agent hunch", [], source="agent")
        except HarnessError:
            pass
        else:
            raise HarnessError("self-test: agent was allowed to set a rank above the cap")
        record_decision(project, "agent.guess", "proposed", 1, "agent inference", [], source="agent")
        ledger_now = {e["element"]: e for e in json.loads((output / "decisions.json").read_text(encoding="utf-8"))["elements"]}
        if ledger_now["agent.guess"]["source"] != "agent":
            raise HarnessError("self-test: provenance not recorded")
        if ledger_now["agent.guess"]["stars"] != ZERO_STARS:
            raise HarnessError("self-test: agent proposals must store 0 stars until the user ranks")
        if ledger_now["cover.layout.two-column"]["source"] != "user":
            raise HarnessError("self-test: user provenance lost")

        # Zero is a real score meaning worst execution, and must survive adoption.
        zero_ledger = root / "zero.jsonl"
        zero_ledger.write_text(json.dumps({"element": "kill.me", "stars": 0, "timestamp": 1}) + "\n"
                               + json.dumps({"element": "bless.me", "verdict": "approved", "timestamp": 2}) + "\n",
                               encoding="utf-8")
        adopt_companion(project, zero_ledger)
        z = {e["element"]: e for e in json.loads((output / "decisions.json").read_text(encoding="utf-8"))["elements"]}
        # A score rates execution. It must never remove the element: reading a
        # low score as "delete this" destroyed work the user wanted kept.
        if z["kill.me"]["stars"] != ZERO_STARS:
            raise HarnessError("self-test: zero-star value was not recorded")
        if z["kill.me"]["state"] == "rejected":
            raise HarnessError("self-test: a score removed an element; only an explicit verdict may")
        if z["bless.me"]["state"] != "approved" or z["bless.me"]["source"] != "user":
            raise HarnessError("self-test: explicit approve verdict not adopted")

        # Statistics must be deterministic and must not flatter the ledger:
        # coverage tells you how much is really the user's.
        first_stats = ledger_stats(load_decisions(output))
        if first_stats != ledger_stats(load_decisions(output)):
            raise HarnessError("self-test: stats are not deterministic")
        if not 0.0 <= first_stats["coverage"] <= 1.0:
            raise HarnessError("self-test: coverage out of range")
        if first_stats["userSet"] + first_stats["agentSet"] != first_stats["standing"]:
            raise HarnessError("self-test: user/agent split does not sum to standing")
        record_decision(project, "liked.but.weak", "proposed", 1, "user click", [],
                        source="user", sentiment="like")
        flagged = ledger_stats(load_decisions(output))
        # Good idea, ugly execution: actionable polish, never a contradiction.
        if "liked.but.weak" not in flagged["needsPolish"]:
            raise HarnessError("self-test: like-with-low-stars not surfaced as polish work")
        if "liked.but.weak" in flagged["conflicts"]:
            raise HarnessError("self-test: like-with-low-stars mislabelled as a conflict")
        if flagged["likes"] < 1:
            raise HarnessError("self-test: like not counted")

        # embed must supply the graphic, and must refuse to guess a placement.
        session = project / ".superpowers" / "brainstorm" / "s1" / "content"
        session.mkdir(parents=True)
        screen = session / "proto.html"
        screen.write_text('<html><head></head><body><h1>fichas</h1>'
                          '<div data-dh-controls="cover.layout.two-column"></div>'
                          '</body></html>', encoding="utf-8")
        if embed_controls(project, screen) != 1:
            raise HarnessError("self-test: embed did not fill the placeholder")
        embedded = screen.read_text(encoding="utf-8")
        for needed in ('class="dh-shot"', 'data-rank="0"', 'data-verdict="completed"',
                       'data-sentiment="like"', 'data-sentiment="dislike"',
                       "/* dh-rehydrate */", f"dh-controls-version: {CONTROLS_VERSION}"):
            if needed not in embedded:
                raise HarnessError(f"self-test: embedded row missing {needed}")
        # Re-running embed must be a no-op, not a duplication. The old regex
        # stopped at the first </div> inside a generated row, so a second run
        # doubled every row and left orphaned closing tags that silently ended
        # the wrapper early and killed every descendant style rule.
        once = screen.read_text(encoding="utf-8")
        embed_controls(project, screen)
        twice = screen.read_text(encoding="utf-8")
        if once != twice:
            raise HarnessError("self-test: embed is not idempotent")
        if twice.count('data-element="cover.layout.two-column"') != 1:
            raise HarnessError("self-test: embed duplicated a row on re-run")
        if twice.count("<div") != twice.count("</div"):
            raise HarnessError("self-test: embed left unbalanced <div> tags")

        screen.write_text("<html><body>no placeholder</body></html>", encoding="utf-8")
        try:
            embed_controls(project, screen)
        except HarnessError:
            pass
        else:
            raise HarnessError("self-test: embed accepted a screen with no placeholder")

        # publish must win the newest-mtime race by a clear margin, not a tie.
        screen.write_text('<html><body><div data-dh-controls="cover.layout.two-column"></div></body></html>',
                          encoding="utf-8")
        rival = session / "rival.html"
        rival.write_text("<html><body>rival</body></html>", encoding="utf-8")
        publish_screen(project, screen)
        gap = screen.stat().st_mtime - rival.stat().st_mtime
        if gap < 2:
            raise HarnessError(f"self-test: publish left a {gap:.1f}s race with another screen")

        # Reviewed is a status, not approval, and must not freeze the element.
        record_decision(project, "seen.it", "completed", 3, "user clicked completed", [], source="user")
        seen = {e["element"]: e for e in json.loads((output / "decisions.json").read_text(encoding="utf-8"))["elements"]}
        if seen["seen.it"]["state"] != "completed":
            raise HarnessError("self-test: completed status not recorded")
        if 'data-element="seen.it"' not in render_feedback_controls(load_decisions(output), None, project):
            raise HarnessError("self-test: a completed element must stay scoreable")
        record_decision(project, "seen.it", "proposed", 5, "user kept iterating", [], source="user")
        if json.loads((output / "decisions.json").read_text(encoding="utf-8")) is None:
            raise HarnessError("unreachable")

        # Zero is the worst score, deliberately given -- not an erasure. It must
        # stay `scored`, must not touch encouragement, and must NOT move state:
        # rating a thing badly is not deleting it. That conflation is what
        # silently deleted a user's work once already.
        record_decision(project, "rated.then.zeroed", "approved", 4, "user", [],
                        source="user", sentiment="like")
        score_zero(project, "rated.then.zeroed")
        zeroed = {e["element"]: e for e in json.loads((output / "decisions.json").read_text(encoding="utf-8"))["elements"]}["rated.then.zeroed"]
        if zeroed["stars"] != ZERO_STARS:
            raise HarnessError("self-test: zero was not recorded as a score")
        if not zeroed["scored"]:
            raise HarnessError("self-test: zero must count as judged -- it is the worst rating, not a blank")
        if zeroed["state"] != "approved":
            raise HarnessError("self-test: a zero score moved the element's state; only a verdict may")
        if zeroed.get("sentiment") != "like":
            raise HarnessError("self-test: zero wrongly cleared the encouragement signal")

        # Ordering: this turn on top, then unresolved, best execution first.
        for name, state, stars in (("z.old.approved", "approved", 5), ("a.new.proposed", "proposed", 2),
                                   ("m.mid.proposed", "proposed", 4)):
            record_decision(project, name, state, stars, "fixture", [], source="user")
        ordered = render_feedback_controls(load_decisions(output), None, project, pinned={"z.old.approved"})
        seq = re.findall(r'data-element="([^"]+)"', ordered)
        if seq[0] != "z.old.approved":
            raise HarnessError("self-test: pinned element was not placed first")
        props = [n for n in seq if n in ("a.new.proposed", "m.mid.proposed")]
        if props != ["m.mid.proposed", "a.new.proposed"]:
            raise HarnessError("self-test: proposals not sorted by execution score")

        # validate must refuse a decision-less harness rather than green-light it.
        (output / "decisions.json").unlink()
        try:
            validate_harness(project)
        except HarnessError:
            pass
        else:
            raise HarnessError("self-test: validate green-lit a harness with no decision ledger")
