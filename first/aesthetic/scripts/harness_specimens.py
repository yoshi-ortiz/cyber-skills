#!/usr/bin/env python3
"""The article's fixed assets, and the specimen strip built from them.

The stylesheet, the icons, the three scripts, and the one function that lays a
cohort out as specimens. Split from the article because these are what the
article is made of rather than how it is assembled, and they change on a
different clock.
"""

from __future__ import annotations

import re
from html import escape as html_escape

from harness_core import _screen


ARTICLE_STYLE = _screen("article.css")


# Stroke icon, not an emoji: emoji ignore `color`, so a bin glyph could never
# take the bar's ink or invert with the active pill.
# The round's own mark: a target, because the round is the one thing being aimed
# at. Stroke, not emoji -- emoji ignore `color` and cannot invert with the zone.
ROUND_ICON = ('<svg class="dh-round-icon" viewBox="0 0 24 24" fill="none" '
              'stroke="currentColor" stroke-width="1.6" aria-hidden="true">'
              '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4.5"/>'
              '<circle cx="12" cy="12" r="1" fill="currentColor"/></svg>')

def _round_icon(path: str) -> str:
    return ('<svg class="dh-round-icon" viewBox="0 0 24 24" fill="none" '
            'stroke="currentColor" stroke-width="1.6" aria-hidden="true">' + path + '</svg>')

ROUND_ICONS = {
    "core": ROUND_ICON,
    "palette": _round_icon('<rect x="4" y="4" width="7" height="7" rx="1"/>'
                           '<rect x="13" y="4" width="7" height="7" rx="1"/>'
                           '<rect x="4" y="13" width="7" height="7" rx="1"/>'
                           '<rect x="13" y="13" width="7" height="7" rx="1"/>'),
    "typography": _round_icon('<path d="M6 18V6h4l4 8 4-8h4v12"/>'),
    "illustration": _round_icon('<path d="M4 20l5-7 4 5 3-4 4 6"/>'
                                '<circle cx="9" cy="8" r="2"/>'),
    "composition": _round_icon('<rect x="4" y="4" width="16" height="16" rx="1"/>'
                               '<path d="M4 10h16M10 4v16"/>'),
    "voice": _round_icon('<path d="M5 8h14M5 12h10M5 16h12"/>'),
    "motion": _round_icon('<path d="M5 12h3l2-4 2 8 2-5 3 1"/>'),
}

TRASH_ICON = ('<svg class="dh-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
              'stroke-width="2" stroke-linecap="round" aria-hidden="true">'
              '<path d="M3 6h18M8 6V4h8v2M6 6l1 14h10l1-14M10 11v6M14 11v6"/></svg>')

TOC_SCRIPT = _screen("toc.js")


# The slideshow. A 96px thumbnail is a reminder of a drawing, not a view of
# one -- so the page was asking for a judgement it never showed enough to make.
#
# The strip here holds NO state of its own. Every control is a proxy: it finds
# the element's real row and clicks its real control, so the ledger keeps one
# write path and the companion's own rehydrator stays the only thing that
# decides what a click means. Duplicating that logic per language is exactly
# how the JS and Python rules drifted apart before.
SHOT_FIT_SCRIPT = _screen("shot-fit.js")

LIGHTBOX_SCRIPT = _screen("lightbox.js")


def _specimens(entries: list[dict[str, object]], txt: dict[str, str],
               rows: dict[str, str] | None = None) -> str:
    """Show the material itself: the colours, the faces. Rendered from tokens the
    project recorded, so the harness invents no value it was not given."""
    colors, fonts = [], []
    for entry in entries:
        tokens = entry.get("tokens") or {}
        # Carry the OWNING element with each token: a token whose id is
        # just its owner's is not separately rankable, and pretending it is
        # was the whole of the palette defect.
        owner = str(entry["element"])
        colors += [(owner, c) for c in (tokens.get("colors") or [])]
        fonts += [(owner, f) for f in (tokens.get("fonts") or [])]
    rows = rows or {}

    def scoreable(token: dict[str, object], owner: str = "",
                  is_set_header: bool = False) -> str:
        """A specimen the user cannot rank is a picture of a decision.

        Point a token at an element id and its own controls ride beside it, so
        a family, a pairing and a single weight are each ranked where they are
        read -- rather than as a dotted id in a list somewhere below.
        """
        linked = str(token.get("element") or "").strip()
        if linked not in rows:
            return ""
        # A control on a set HEADER ranks the set, which is what it looks
        # like. The same control hung on ONE MEMBER of a set claims to rank
        # that member -- so a palette whose first colour happened to carry
        # the family's id showed a star strip under `amarillo` and nothing
        # under `menta` or `rosa`, as if two thirds of the palette had
        # failed to render. A swatch earns controls by having its OWN id.
        if linked == owner and not is_set_header:
            return ""
        row = rows[linked]
        # Only the controls. The full row keeps the id, the state and the
        # evidence further down; repeating all that beside a specimen that
        # already shows the thing would say everything twice. The graphic in
        # particular carries an inline `display:block`, which no class rule of
        # ours can override -- so it is never emitted here rather than hidden.
        head = re.match(r'<div class="dh-fb"[^>]*>', row)
        start = row.find('<span class="dh-signals">')
        if not head or start < 0:
            return ""
        # To the END of the signals block, not the first `</span>` inside it --
        # a non-greedy match here emitted the zero control alone, a 44px stub
        # where the whole strip belonged. The row closes with the signals span
        # followed by its own </div>.
        body = row[start:].rsplit("</div>", 1)[0].rstrip()
        return '<div class="dh-spec-score">' + head.group(0) + body + "</div></div>"

    out = []
    if colors:
        items = "".join(
            f'<li><span class="dh-chip" style="background:{html_escape(str(c["value"]))}"></span>'
            f'<span class="dh-vals"><b>{html_escape(str(c.get("name") or c["value"]))}</b>'
            f'<code>{html_escape(str(c["value"]))}</code>'
            + (f'<span>{html_escape(str(c["role"]))}</span>' if c.get("role") else "")
            + "</span>" + scoreable(c, owner) + "</li>"
            for owner, c in colors)
        out.append(f'<div class="dh-spec"><ul class="dh-swatches">{items}</ul></div>')
    if fonts:
        items = []
        for owner, f in fonts:
            stack = html_escape(str(f.get("stack") or "inherit"))
            # A family, then every weight it is actually used at, each labelled
            # with the job it does. One sample line and a name is a caption: it
            # cannot tell you which weight sets a heading and which sets a
            # caption, which is most of what a type system decides.
            variants = list(f.get("variants") or [])
            if not variants:
                variants = [{"use": f.get("use") or "", "sample": f.get("sample") or ""}]
            rows_out = []
            for v in variants:
                weight = str(v.get("weight") or "").strip()
                style = str(v.get("style") or "").strip()
                size = str(v.get("size") or "").strip()
                sample = html_escape(str(v.get("sample") or f.get("sample") or "Aa Bb Cc 0123"))
                css = f"font-family:{stack}"
                if weight:
                    css += f";font-weight:{html_escape(weight)}"
                if style:
                    css += f";font-style:{html_escape(style)}"
                if size:
                    css += f";font-size:{html_escape(size)}"
                spec = " · ".join(x for x in (weight, style, size) if x)
                rows_out.append(
                    f'<li><span class="dh-sample" style="{css}">{sample}</span>'
                    f'<span class="dh-var-meta">'
                    f'<b>{html_escape(str(v.get("use") or ""))}</b>'
                    + (f'<code>{html_escape(spec)}</code>' if spec else "")
                    + "</span>" + scoreable(v, owner) + "</li>")
            items.append(
                f'<li class="dh-face"><div class="dh-face-head">'
                f'<b>{html_escape(str(f["name"]))}</b>'
                f'<code>{stack}</code>'
                + (f'<span class="dh-face-use">{html_escape(str(f["use"]))}</span>'
                   if f.get("use") else "")
                + scoreable(f, owner, is_set_header=True)
                + f'</div><ul class="dh-variants">{"".join(rows_out)}</ul></li>')
        out.append(f'<div class="dh-spec"><ul class="dh-faces">{"".join(items)}</ul></div>')
    return "".join(out)
