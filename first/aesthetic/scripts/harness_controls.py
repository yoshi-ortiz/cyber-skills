#!/usr/bin/env python3
"""The scoring strip: the rows the designer actually clicks.

The stylesheet and scripts the browser needs, the row markup generated from the
ledger, and `embed`, which folds those rows into a screen in place. The seam is
the version stamp: markup and CSS are baked into a screen once, so what is
emitted here and what a served page reports must be comparable.
"""

from __future__ import annotations

import re
from html import escape as html_escape
from html.parser import HTMLParser
from pathlib import Path

from harness_core import (FOUNDATION_ORDER, GROUP_OF, HarnessError,
                          STAR_RANGE, ZERO_STARS, _screen)
from harness_strings import project_language, strings_for
from harness_ledger import display_name, display_names, load_decisions
from harness_round import foundation_of
from harness_comp import render_preview


STYLE_MARKER = "/* dh-controls */"
# Bumped whenever the emitted CSS or markup changes. `embed` bakes both into the
# screen, so a screen embedded by an older skill keeps the older bug forever and
# looks, from the browser, exactly like a fix that did not work. `doctor`
# compares this against the served page and fails on a mismatch.
CONTROLS_VERSION = "39"
VERSION_MARKER = "dh-controls-version"

# Restores the signals a refresh would otherwise throw away.
#
# The served screen is a static snapshot: `embed` bakes each row's stars into
# the HTML, and the companion re-serves that same file on every request. Clicks
# travel out to the durable ledger and nothing ever brings them back, so every
# refresh silently reverted the user's scoring to whatever the agent last
# published -- the single defect behind "the score is not being saved".
#
# The durable ledger stays the source of truth for `adopt`; this only keeps the
# screen from lying to the person clicking it. Capture phase, so it reads each
# control's state before the companion's own handler toggles it.
REHYDRATE_SCRIPT = _screen("rehydrate.js")
FEEDBACK_STYLE = _screen("controls.css")

# The stamp rides the stylesheet because that is the one asset `embed` always
# rewrites into the screen. On the wrapper it never survived: `embed` lifts the
# rows out of the generated block and leaves the wrapper behind.
FEEDBACK_STYLE = FEEDBACK_STYLE.replace(
    STYLE_MARKER, f"{STYLE_MARKER}\n/* dh-controls-version: {CONTROLS_VERSION} */", 1)


def extract_feedback_rows(markup: str) -> dict[str, str]:
    """Pull complete `.dh-fb` rows out of generated controls markup.

    A naive `.*?\\n</div>` stops at the first closing tag inside an inlined
    HTML comp preview, which truncates versus-pair rows and nests the rest of
    the round zone inside a thumbnail.
    """
    rows: dict[str, str] = {}
    for opening in re.finditer(r'<div class="dh-fb" data-element="([^"]+)"[^>]*>', markup):
        element = opening.group(1)
        depth = 1
        end = opening.end()
        for tag in re.finditer(r"<(/?)div\b[^>]*>", markup[opening.end():]):
            depth += -1 if tag.group(1) else 1
            if depth == 0:
                end = opening.end() + tag.end()
                break
        else:
            raise HarnessError(f"unbalanced <div> in feedback row for {element}")
        rows[element] = markup[opening.start():end]
    return rows


def render_feedback_controls(decisions: dict[str, object], theme: dict[str, str] | None = None,
                             project_root: Path | None = None,
                             pinned: set[str] | None = None,
                             language: str | None = None) -> str:
    """Emit rank + sentiment controls for every element in standing.

    Generated from the ledger so a screen cannot invent a design-element id.
    Each row carries the graphic being ranked: a star next to a dotted id is a
    guess, not a judgement. Same ledger, theme and previews in, byte-identical
    markup out.
    """
    pinned = pinned or set()
    txt = strings_for(language or project_language(project_root))
    live = [e for e in decisions["elements"] if e["state"] in GROUP_OF]
    theme_vars = {
        "--dh-bg": "bg", "--dh-ink": "ink", "--dh-accent": "accent",
        "--dh-font": "font", "--dh-shot-w": "shot",
    }
    wrapper_style = ""
    if theme:
        declared = "; ".join(f"{prop}: {theme[key]}" for prop, key in theme_vars.items() if theme.get(key))
        if declared:
            wrapper_style = f' style="{declared}"'
    lines = [FEEDBACK_STYLE, REHYDRATE_SCRIPT,
             f'<div class="dh-feedback" data-{VERSION_MARKER}="{CONTROLS_VERSION}" '
             f'data-saved="{html_escape(txt["saved"])}"{wrapper_style}>',
             f'<strong class="dh-offline">{txt["offline"]}</strong>']
    if not live:
        lines.append("<!-- no elements in standing; record one with `decide` first -->")
    # Grouped by design-system foundation, not by lifecycle. The user asked to
    # see the typography together, the palette together -- that is a design
    # system with a rank against each part. Lifecycle still rides on each row's
    # own state chip, where it belongs.
    def group_of(item: dict[str, object]) -> str:
        return "pinned" if item["element"] in pinned else foundation_of(item["element"])
    def order(item: dict[str, object]) -> tuple:
        # This round first, then the foundations in reading order, then best
        # execution first, then id so the output stays byte-stable.
        return (0 if item["element"] in pinned else 1,
                FOUNDATION_ORDER.get(group_of(item), len(FOUNDATION_ORDER)),
                -int(item.get("stars") or 0),
                item["element"])
    names = display_names(live)
    rendered_group = None
    for entry in sorted(live, key=order):
        group_key = group_of(entry)
        if group_key != rendered_group:
            rendered_group = group_key
            label = txt["from-this-round"] if group_key == "pinned" else txt.get(group_key, group_key)
            tally = sum(1 for e in live if group_of(e) == group_key)
            lines.append(f'<h4 class="dh-group" data-group="{group_key}">{label}<span class="dh-count">{tally}</span></h4>')
        element, stars = entry["element"], entry["stars"]
        # The strip already greys an unscored bar; the ROW painted its
        # stars straight from the number regardless of who put it there.
        user_ranked = entry.get("source") == "user" and bool(entry.get("scored"))
        lines.append(
            f'<div class="dh-fb" data-element="{element}" data-stars="{stars if user_ranked else 0}" '
            f'data-scored="{"yes" if user_ranked else "no"}" '
            f'data-state="{entry["state"]}" '
            f'data-group="{GROUP_OF[entry["state"]]}" data-foundation="{foundation_of(element)}" '
            f'data-label="{element}">'
        )
        lines.append(render_preview(project_root, entry.get("preview"), element, txt))
        lines.append('<span class="dh-meta">')
        # Legacy rows carry scored=True from when an agent placeholder was
        # written as a score, so the marker keys off who ranked it, not off
        # the stale flag -- otherwise old agent rows still read as judged.
        unscored = "" if user_ranked else f' &middot; {txt["unscored"]}'
        # The state rides beside the id instead of trailing the block as a fifth
        # line of near-identical grey text.
        # The NAME leads and the id becomes a tag under it. A designer should
        # not have to read a namespace to learn what they are scoring.
        lines.append(f'<span class="dh-head"><span class="dh-id">'
                     f'{html_escape(names.get(element) or display_name(entry))}</span>'
                     f'<span class="dh-state">{html_escape(txt.get("state-" + str(entry["state"]), str(entry["state"])))}{unscored}</span></span>')
        what = str(entry.get("description") or "").strip()
        if what:
            lines.append(f'<span class="dh-desc">{what}</span>')
        lines.append("</span>")
        lines.append('<span class="dh-signals">')
        # Leads the strip. A bookmark is "keep this where I can find it", which
        # is a decision ABOUT the card rather than a judgement of it, so it sits
        # before the scale instead of trailing the verdict where it read as a
        # fifth opinion. The ribbon is clip-path on a box, not an emoji and not
        # hand-authored SVG -- `check_no_hand_authored_svg` refuses the latter,
        # and asset-sourcing.md allows a deterministic CSS primitive.
        bookmarked = bool(entry.get("bookmarked"))
        on = ' class="on"' if bookmarked else ""
        lines.append(f'<span data-bookmark role="button" tabindex="0" '
                     f'aria-pressed="{"true" if bookmarked else "false"}" '
                     f'aria-label="{txt["bookmark"]}: {element}" title="{txt["bookmark"]}"{on}>'
                     f'<i class="dh-ribbon" aria-hidden="true"></i></span>')
        stars_markup = "".join(
            f'<span data-rank="{n}" role="button" tabindex="0" '
            f'aria-label="{n} {txt["stars-of"]} {STAR_RANGE[1]}: {txt["execution-quality"]}"'
            + (' class="on"' if user_ranked and 0 < n <= stars else "")
            + ">&#9733;</span>"
            for n in range(STAR_RANGE[0], STAR_RANGE[1] + 1)
        )
        # The zero is a rank, so it rides the rank code path: it scores 0 and
        # touches nothing else. Emitted as `data-reset` it hit a companion
        # handler that also stripped the thumb and the tick -- a score silently
        # erasing two unrelated signals, which is the one thing the contract
        # says a score must never do.
        zero_on = ' class="on"' if user_ranked and stars == ZERO_STARS else ""
        lines.append(
            f'<span class="dh-zero"><span data-rank="0" role="button" tabindex="0" '
            f'title="{txt["zero-title"]}" '
            f'aria-label="{txt["zero-label"].format(element=element)}"{zero_on}>0</span></span>'
            # data-stars is mirrored onto the strip so the numeric readout can be
            # pure CSS (attr()) and still track a click: `paint` writes it here
            # as well as on the row.
            f'<span class="dh-stars" role="group" data-stars="{stars if user_ranked else 0}" '
            f'data-scored="{"yes" if user_ranked else "no"}" '
            f'aria-label="{txt["execution-of"]} {element}">'
            f'{stars_markup}</span>')
        mood = entry.get("sentiment")
        for name, glyph, label in (("like", "&#128077;", txt["like"]),
                                   ("dislike", "&#128078;", txt["dislike"])):
            on = ' class="on"' if mood == name else ""
            lines.append(f'<span data-sentiment="{name}" role="button" tabindex="0" '
                         f'aria-label="{label} {element}" title="{label}"{on}>{glyph}</span>')
        # A status, not a lock: "this one is done for now". Toggleable, and it never
        # freezes the element -- iteration continues after it is checked.
        done = entry["state"] in ("completed", "approved")
        on = ' class="on"' if done else ""
        lines.append(f'<span data-verdict="completed" role="button" tabindex="0" '
                     f'aria-pressed="{"true" if done else "false"}" '
                     f'aria-label="{txt["completed"]}: {element}" title="{txt["completed"]}"{on}>'
                     f'<span>&#10003;</span></span>')
        lines.append("</span>")
        lines.append("</div>")
    lines.append("</div>")
    return "\n".join(lines) + "\n"


def embed_controls(project_root: Path, screen: Path, theme: dict[str, str] | None = None,
                   pinned: set[str] | None = None, language: str | None = None) -> int:
    """Fill a screen's `data-dh-controls` placeholders with generated rows.

    Without this, an agent wanting scoring inside a prototype hand-writes the
    markup and silently drops the component graphic -- which is exactly what
    happened. The placeholder names the elements; the harness supplies the row.
    """
    project_root = project_root.resolve(strict=True)
    output = project_root / "spec" / "design-harness"
    html = screen.read_text(encoding="utf-8")
    language = language or project_language(project_root)
    txt = strings_for(language)
    generated = render_feedback_controls(load_decisions(output), theme, project_root,
                                         pinned, language)
    rows = extract_feedback_rows(generated)
    style_match = re.search(r"<style>.*?</style>", generated, re.S)
    style = style_match.group(0) if style_match else ""
    script_match = re.search(r"<script>/\* dh-rehydrate \*/.*?</script>", generated, re.S)
    script = script_match.group(0) if script_match else ""

    # Match the placeholder's OWN closing tag by counting nested divs. The old
    # non-greedy `(.*?)</div>` stopped at the first </div> inside a generated
    # row, so re-running embed duplicated every row and orphaned the remainder.
    placeholders = []
    for opening in re.finditer(r'<div([^>]*?)data-dh-controls="([^"]*)"([^>]*?)>', html):
        depth, cursor = 1, opening.end()
        for tag in re.finditer(r"<(/?)div\b[^>]*>", html[opening.end():]):
            depth += -1 if tag.group(1) else 1
            if depth == 0:
                cursor = opening.end() + tag.end()
                break
        else:
            raise HarnessError("unbalanced <div> around a data-dh-controls placeholder")
        placeholders.append((opening, cursor))
    if not placeholders:
        raise HarnessError(
            'no <div data-dh-controls="element.a,element.b"></div> placeholder in the screen. '
            "Add one where scoring belongs -- never hand-write the rows.")

    filled = 0
    # A foundation heads its section once per screen, at its first appearance.
    # This screen carries sixteen placeholders, so heading each one in isolation
    # printed "Composition & layout" four times -- a repetition that reads as
    # noise rather than as a design system. Decided in document order here,
    # because the rewrite below has to run backwards.
    headed: set[str] = set()
    heads_at: dict[int, set[str]] = {}
    for position, (opening, _) in enumerate(placeholders):
        names = [e.strip() for e in opening.group(2).split(",") if e.strip()]
        fresh = {foundation_of(n) for n in names} - headed
        heads_at[position] = fresh
        headed |= fresh
    # Right to left so earlier offsets stay valid. Each placeholder's contents
    # are replaced wholesale, which is what makes embed safe to re-run.
    for position, (opening, close_end) in reversed(list(enumerate(placeholders))):
        wanted = [e.strip() for e in opening.group(2).split(",") if e.strip()]
        missing = [e for e in wanted if e not in rows]
        if missing:
            raise HarnessError("placeholder names element(s) not in standing: " + ", ".join(missing))
        # Group the placeholder's own elements by design-system foundation.
        # `embed` lifts bare rows out of the generated wrapper, so the headings
        # rendered there never reached an embedded screen -- the grouping
        # existed and was invisible on the only page the user actually scores.
        # Ordered by foundation, author's order kept inside each one.
        by_id = {e["element"]: e for e in load_decisions(output)["elements"]}
        buckets: dict[str, list[str]] = {}
        for name in wanted:
            buckets.setdefault(foundation_of(name), []).append(name)
        # Best execution on top within each foundation. The author's typing order
        # carried no information, so the strongest work could sit last and the
        # user had to read every row to find what was working.
        for names in buckets.values():
            names.sort(key=lambda n: (-int((by_id.get(n) or {}).get("stars") or 0), n))
        ordered = sorted(buckets.items(),
                         key=lambda kv: FOUNDATION_ORDER.get(kv[0], len(FOUNDATION_ORDER)))
        body = "\n".join(
            (f'<h4 class="dh-group" data-group="{key}">{txt.get(key, key)}'
             f'<span class="dh-count">{len(names)}</span></h4>\n'
             if key in heads_at[position] else "")
            + "\n".join(rows[e] for e in names)
            for key, names in ordered)
        # A round names its cohort so the user knows what is being asked and what
        # is deliberately out of scope. Read it off THIS div: an outer wrapper's
        # attributes never survive into the placeholder embed rewrites.
        attributes = opening.group(1) + opening.group(3)
        cohort = re.search(r'data-dh-cohort="([^"]*)"', attributes)
        if cohort and cohort.group(1).strip():
            banner = (f'<p class="dh-cohort"><b>{txt["this-round"]}</b>'
                      f'<span>{html_escape(cohort.group(1).strip())}</span>'
                      f'{len(wanted)} {txt["to-score"]}</p>\n')
            body = banner + body
        replacement = (f'<div{opening.group(1)}data-dh-controls="{opening.group(2)}"'
                       f'{opening.group(3)}>\n{body}\n</div>')
        html = html[:opening.start()] + replacement + html[close_end:]
        filled += len(wanted)

    # Replace the assets, never skip them. `embed` used to inject the stylesheet
    # only when the screen carried none, so a screen embedded by an older skill
    # kept that older CSS for the rest of its life: fixing a control bug in the
    # skill changed nothing the user could see, and the only symptom was "the
    # fix did not work". Stripping first also keeps `embed` byte-idempotent.
    html = re.sub(r"<style>/\* dh-controls \*/.*?</style>\n?", "", html, flags=re.S)
    html = re.sub(r"<script>/\* dh-rehydrate \*/.*?</script>\n?", "", html, flags=re.S)
    head = "\n".join(part for part in (style, script) if part)
    if head:
        html = (html.replace("</head>", head + "\n</head>", 1)
                if "</head>" in html else head + "\n" + html)
    screen.write_text(html, encoding="utf-8")
    return filled


def visible_controls(markup: str, attribute: str) -> dict[str, str]:
    """Map each control carrying `attribute` to the text a browser would draw.

    Counting substrings in generated markup is not verification -- it asserts
    what the generator meant, not what a parser builds. This walks the markup
    the way a browser does, so a control whose glyph got absorbed into a broken
    opening tag comes back empty instead of coming back "present".
    """
    class _Walk(HTMLParser):
        def __init__(self) -> None:
            super().__init__(convert_charrefs=True)
            self.open: list[tuple[str, str | None, list[str]]] = []
            self.found: dict[str, str] = {}

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            keys = dict(attrs)
            # A valueless attribute (`data-reset`) parses to None. That is still
            # a control -- key it by the attribute name, not by "absent".
            key = keys.get(attribute) or attribute if attribute in keys else None
            self.open.append((tag, key, []))

        def handle_data(self, data: str) -> None:
            for frame in self.open:
                frame[2].append(data)

        def handle_endtag(self, tag: str) -> None:
            while self.open:
                name, key, text = self.open.pop()
                if key is not None:
                    self.found.setdefault(key or attribute, "".join(text))
                if name == tag:
                    break

    walk = _Walk()
    walk.feed(markup)
    walk.close()
    while walk.open:                       # unclosed tags at EOF still count
        _, key, text = walk.open.pop()
        if key is not None:
            walk.found.setdefault(key or attribute, "".join(text))
    return walk.found
