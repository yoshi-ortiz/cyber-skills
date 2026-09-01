#!/usr/bin/env python3
"""A comp: the HTML fragment a preview is, scoped so it cannot leak.

Turning a raw comp into a fragment with its own scope class, measuring the
artboard it declares, and recording or re-rendering the reference the ledger
keeps. The seam is scoping -- a comp is authored as a whole page and shown
inside one cell of somebody else's, and this is the only place that conversion
happens.
"""

from __future__ import annotations

import base64
import hashlib
import re
from html import escape as html_escape
from pathlib import Path

from harness_core import (HarnessError, PREVIEW_SUFFIXES, is_within,
                          sha256_file, write_json)
from harness_strings import DEFAULT_LANGUAGE, strings_for
from harness_ledger import render_decisions_md
from harness_preview import check_preview_legible, preferred_preview_path


# Every token has a var()-with-fallback, never a bare literal. Two ways to set
# them, both deterministic:
#   1. Pass --bg/--ink/--accent/--font to `controls`; values are baked into an
#      inline style on the wrapper, so the same flags always emit the same
#      bytes.
#   2. Pass none, and nest the output inside a screen that already sets
#      --dh-bg/--dh-ink/--dh-accent/--dh-font on an ancestor (every screen this
#      harness has produced does, since C2/rev13 scope --bg/--acc per card) --
#      the cascade fills the fallback. Either way there is no hardcoded color
#      the harness's own approved palette (`palette.family-from-cards`) can be
#      overridden by.
# Inline so a host stylesheet cannot collapse the one element the user must see.
# The fallback MUST match the grid track in FEEDBACK_STYLE. When it did not, the
# graphic rendered wider than its column and sat on top of the description text.
SHOT_INLINE = ("display:block;flex:0 0 auto;inline-size:var(--dh-shot-w,clamp(96px,18vw,240px));"
               "block-size:calc(var(--dh-shot-w,clamp(96px,18vw,240px)) * 11 / 8.5);overflow:hidden;"
               "position:relative;border:1px solid currentColor;background:#fff")
SHOT_INNER_INLINE = ("position:absolute;inset-block-start:0;inset-inline-start:0;"
                     "inline-size:850px;block-size:1100px;transform-origin:0 0;"
                     "transform:scale(calc(var(--dh-shot-w,clamp(96px,18vw,240px)) / 850));pointer-events:none")
COMP_SCOPE_CLASS = "dh-comp-scope"


def comp_scope_id(element: str) -> str:
    """A CSS-safe, per-element scope class suffix.

    Two comps that both use `.title` or `.mini` (a common authoring
    convention across similar comps) must not fight over which one's rule
    wins on a page that embeds many comps at once. `@scope` only isolates
    against elements OUTSIDE the scope root -- every comp sharing the same
    root class (`.dh-comp-scope`) is not outside any other comp's scope, so
    their `.title` rules collided globally and the wrong comp's font-size
    (or any other property) could win by source order. Hashing the element
    id keeps the class valid regardless of dots or other characters in it.
    """
    return hashlib.sha256(element.encode("utf-8")).hexdigest()[:12]


def scope_comp_css(css: str, scope_class: str = COMP_SCOPE_CLASS) -> str:
    """Rewrite comp CSS so it cannot restyle the companion frame or leak
    into a different comp embedded elsewhere on the same page.

    Comps are drawn as standalone HTML pages with `body { width: 510px }`.
    Inlined verbatim, every thumbnail overwrites the frame's body and the
    whole page shrinks to one comp width -- exactly the broken layout.
    Rewriting :root/html/body to `.dh-comp-scope` AND wrapping in
    `@scope (.dh-comp-scope)` made host rules miss: a selector inside
    `@scope` is a descendant of the root, so `.dh-comp-scope { background }`
    never matched the host. The drawing went blank (white on the lightbox,
    transparent on the card). `:scope` is the host.

    `scope_class` must be unique PER COMP, not the shared `dh-comp-scope`
    class alone -- see `comp_scope_id`.
    """
    if not css.strip():
        return css
    css = re.sub(r":root\b", ":scope", css)
    css = re.sub(r"(?<![\w-])html(?![\w-])", ":scope", css)
    css = re.sub(r"(?<![\w-])body(?![\w-])", ":scope", css)
    if "@scope" in css:
        return css
    return f"@scope (.{scope_class}) {{\n{css}\n}}\n"


# A page is never 34px wide. Preview scaling reads the comp's page size out of
# its stylesheet, and taking the first px width anywhere in the sheet hands it
# whatever small component happens to be declared first -- a logo, a badge, an
# avatar. The thumbnail is then scaled to that component, so the designer sees
# one magnified corner of the page instead of the page. Below this, a
# declaration is a component, not an artboard.
MIN_ARTBOARD_PX = 320.0

_PAGE_RULE = re.compile(r"(?:^|,)\s*(?::root|html|body|@page)\b", re.I)


def _page_level_css(css: str) -> str:
    """Declarations belonging to the rules that size the page itself."""
    return "\n".join(block for selector, block
                     in re.findall(r"([^{}]+)\{([^{}]*)\}", css)
                     if _PAGE_RULE.search(selector))


def _css_px(css: str, names: tuple[str, ...]) -> float | None:
    """The comp's declared page size in px, or None when it declares none.

    A page-level rule wins outright, whatever it says. Failing that, the first
    declaration big enough to be an artboard is taken and smaller ones are
    passed over, because a fluid comp that never states a page size is better
    served by the caller's default than by the width of its logo.
    """
    for scope, floor in ((_page_level_css(css), 0.0), (css, MIN_ARTBOARD_PX)):
        for name in names:
            for match in re.finditer(rf"(?<![\w-]){name}:\s*(\d+(?:\.\d+)?)px", scope):
                value = float(match.group(1))
                if value >= floor:
                    return value
    return None


def html_comp_fragment(raw: str, element: str = "") -> tuple[str, float, float]:
    """Body + styles from a comp file, and its declared page size.

    `element` seeds a per-comp scope class (see `comp_scope_id`) so that two
    comps embedded on the same page never fight over a shared class name
    like `.title` or `.mini`.
    """
    width, height = 850.0, 1100.0
    if re.search(r"<html", raw, re.I):
        styles = "".join(re.findall(r"<style[^>]*>(.*?)</style>", raw, re.S | re.I))
        body_match = re.search(r"<body[^>]*>(.*)</body>", raw, re.S | re.I)
        body = body_match.group(1) if body_match else raw
        # New comps size the page with inline-size/block-size. Reading only
        # `width`/`min-height` left those at the 850×1100 default, so the
        # slideshow scaled a 510 drawing into the corner of a white stage.
        width = _css_px(styles, ("inline-size", "width")) or width
        height = (_css_px(styles, ("block-size", "min-block-size",
                                   "min-height", "height")) or height)
        scope_class = f"{COMP_SCOPE_CLASS}-{comp_scope_id(element)}" if element else COMP_SCOPE_CLASS
        scoped = scope_comp_css(styles, scope_class)
        return (f"<style>{scoped}</style>"
                f'<div class="{COMP_SCOPE_CLASS} {scope_class}">{body}</div>'), width, height
    return raw, width, height


def preview_inner_style(comp_width: float, comp_height: float) -> str:
    return ("position:absolute;inset-block-start:0;inset-inline-start:0;"
            f"inline-size:{comp_width}px;block-size:{comp_height}px;transform-origin:0 0;"
            f"transform:scale(calc(var(--dh-shot-w,clamp(96px,18vw,240px)) / {comp_width}));pointer-events:none")


def preview_reference(project_root: Path, raw: str, element: str = "") -> dict[str, str]:
    """Resolve and hash a preview graphic for a design element.

    Stored as a project-relative path plus a hash, on the same principle as the
    corpus manifest: a preview that silently changed is a preview nobody
    completed.
    """
    project_root = project_root.resolve(strict=True)
    candidate = (project_root / raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
    if not is_within(candidate, project_root):
        raise HarnessError("preview must live inside the project root")
    if not candidate.is_file():
        raise HarnessError(f"preview not found: {raw}")
    # `shoot` writes a PNG so the agent can inspect the rendered pixels. When
    # the matching HTML comp also exists it is the canonical interactive
    # drawing. Store that identity now instead of silently swapping assets only
    # while rendering the article; cards, chart tooltips, slideshow and ledger
    # then all name the same thing.
    if element:
        candidate = preferred_preview_path(project_root, candidate, element)
    if candidate.suffix.lower() == ".svg":
        raise HarnessError(
            f"{candidate.name} is an .svg file recorded directly as a preview -- unchecked "
            "and unrenderable by the pipeline that gates every other comp. Draw it in "
            "HTML/CSS, `shoot` it to a PNG, and `decide --preview` that comp instead.")
    if candidate.suffix.lower() not in PREVIEW_SUFFIXES:
        raise HarnessError(f"unsupported preview type '{candidate.suffix}'; use one of "
                           + ", ".join(sorted(PREVIEW_SUFFIXES)))
    # A rendered comp can be checked; hand-authored SVG cannot be, which is
    # exactly why it is no longer the way to draw one.
    if candidate.suffix.lower() == ".png":
        check_preview_legible(candidate)
    return {"path": candidate.relative_to(project_root).as_posix(), "sha256": sha256_file(candidate)}


def canonicalize_recorded_previews(project_root: Path,
                                   decisions: dict[str, object]) -> int:
    """Migrate raster-era records to their matching interactive comp.

    Old articles swapped this only at render time, so the ledger named one
    asset while the card and slideshow showed another. Persist the resolution
    once; subsequent rendering is literal and every view stays in sync.
    """
    changed = 0
    for entry in decisions["elements"]:
        preview = entry.get("preview")
        if not preview or not preview.get("path"):
            continue
        recorded = project_root / str(preview["path"])
        if not recorded.is_file():
            continue
        canonical = preferred_preview_path(project_root, recorded, str(entry["element"]))
        if canonical == recorded:
            continue
        entry["preview"] = {
            "path": canonical.relative_to(project_root).as_posix(),
            "sha256": sha256_file(canonical),
        }
        changed += 1
    if changed:
        output = project_root / "spec" / "design-harness"
        write_json(output / "decisions.json", decisions)
        (output / "DECISIONS.md").write_text(render_decisions_md(decisions), encoding="utf-8")
    return changed


def render_preview(project_root: Path | None, preview: dict[str, str] | None, element: str,
                   txt: dict[str, str] | None = None) -> str:
    """Inline the graphic for one element, or say plainly that there is none.

    The "no graphic" state carries a stable CLASS as well as its words: doctor
    used to grep for the Spanish text, so translating the strip would have
    quietly disabled the check that every row shows what is being judged.
    """
    txt = txt or strings_for(DEFAULT_LANGUAGE)
    # Every thumbnail names the element it draws. A click can then open that
    # element's slide wherever the thumbnail sits -- in a row, in a folded
    # backlog strip, or beside a specimen. Without the id the folded strips
    # were 95 pictures that led nowhere.
    tag = f'<div class="dh-shot" data-el="{html_escape(element)}" style="{SHOT_INLINE}">'
    if not preview:
        return (f'{tag}<span class="dh-shot-missing" data-dh-no-graphic="1">{txt["no-graphic"]}'
                '<br>--preview</span></div>')
    if project_root is None:
        return f'{tag}<span class="dh-shot-missing">{preview["path"]}</span></div>'

    path = project_root / preview["path"]
    if not path.is_file():
        return (f'{tag}<span class="dh-shot-missing">gráfico ausente<br>'
                f'{preview["path"]}</span></div>')
    suffix = path.suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
        media = "image/jpeg" if suffix in {".jpg", ".jpeg"} else f"image/{suffix.lstrip('.')}"
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        body = f'<img alt="" src="data:{media};base64,{encoded}">'
        return f"{tag}{body}</div>"
    # Prefer the rendered review image over inlining the comp.
    #
    # A comp inlined into the card is laid out in an 850px box, but it sits
    # INSIDE the host page, so every `vw` unit in it resolves against the
    # browser viewport rather than against that box. Measured on this project's
    # hero, served at a 1280px viewport:
    #
    #     h1 font-size   85.76px  (6.7vw of 1280)   true 850px view:  56.95px
    #     hero columns   370.8px / 300px            true 850px view:  431 / 300
    #     column gap     76.8px   (6vw of 1280)     true 850px view:  51px
    #
    # so the headline rendered half again too large in a column 60px too
    # narrow and wrapped to five lines. The card was not a smaller version of
    # the design, it was a layout that occurs at no viewport at all -- which is
    # why improving the design changed the card so little.
    #
    # `review_delivery` already renders every canonical comp in a REAL browser
    # viewport, at the same 8.5:11 the frame uses. Using that PNG makes the
    # card and the full-size review image the same picture by construction,
    # instead of two renderings that disagree.
    review_png = project_root / "design" / "review" / (
        # Same name `review_delivery._image_name` writes.
        re.sub(r"[^A-Za-z0-9._-]+", "-", element).strip(".-") + ".png")
    if suffix == ".html" and review_png.is_file():
        encoded = base64.b64encode(review_png.read_bytes()).decode("ascii")
        return f'{tag}<img alt="" src="data:image/png;base64,{encoded}"></div>'

    fragment = path.read_text(encoding="utf-8")
    if suffix == ".svg":
        fragment = re.sub(r"<svg\b", '<svg preserveAspectRatio="xMidYMid meet" '
                          'style="width:100%;height:100%;display:block"', fragment, count=1)
        return f"{tag}{fragment}</div>"
    body, comp_width, comp_height = html_comp_fragment(fragment, element)
    return (f'{tag}<div class="dh-shot-inner" data-comp-w="{comp_width}" '
            f'data-comp-h="{comp_height}" style="{preview_inner_style(comp_width, comp_height)}">'
            f'{body}</div></div>')
