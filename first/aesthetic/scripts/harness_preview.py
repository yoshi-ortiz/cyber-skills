#!/usr/bin/env python3
"""The Chrome rasterisation adapter, and the pixels it is gated on.

Finding a browser, driving it headless to a PNG, trimming the shot to its
content, and measuring the ink so a blank or near-invisible comp is refused
before it can be recorded. The seam is the process boundary: everything here
shells out or reads bytes back, and nothing above it needs to know that.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from harness_core import HarnessError


# Drawing a comp as raw SVG is the one job the model is worst at: it authors a
# coordinate system it never sees. The ledger recorded the cost -- 59 previews
# holding 6352 <rect> and 15 <path>, and 34 of them carrying a near-zero opacity
# somewhere. One session shipped a comp wrapped in a nested `opacity="0.13"` and
# the NEXT session's entire round was spent repairing it, not improving it.
#
# So a preview is drawn in HTML/CSS -- which the model is good at, and which the
# browser lays out instead of the model -- rendered to a small PNG, and gated on
# its own PIXELS before it can be recorded. "Nearly invisible" stops being a
# thing a session can discover one score later.
CHROME_CANDIDATES = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
)
# 8.5x11 at a deliberately cheap resolution. The thumbnail is read at 96px and
# the slideshow at roughly 700px tall, so this is already generous, and every
# preview is base64-inlined into the article -- a 2x render would triple a page
# that is already over a megabyte for nothing the reader can see.
PREVIEW_WIDTH = 510
PREVIEW_RATIO = 11 / 8.5
# Below this fraction of non-background pixels the comp is not "minimal", it is
# absent. Deliberately loose: coverage is a blank-page check and nothing more.
# Measured on real renders, a faded comp and a good one sit only 2.5x apart on
# coverage (1.26% against 3.11%) but 7x apart on contrast (94 against 699), so a
# coverage threshold tight enough to catch fading would start refusing sparse
# comps that are perfectly legible. Contrast is the discriminator; this only
# catches a page with nothing on it at all.
MIN_INK_COVERAGE = 0.005
# And ink that IS there has to be distinguishable from the ground it sits on.
# This is the threshold that actually catches the opacity failure: a comp faded
# to 13% still covers a THIRD of the page in pixels that differ from the ground,
# so coverage alone waves it through -- it is not blank, it is weak. What
# separates it is that its strongest mark reaches only ~60/765 of contrast,
# where a real comp (even a deliberately sparse one) puts something at 650+.
# Coverage answers "is anything there"; contrast answers "can any of it be seen".
MIN_INK_CONTRAST = 180


def find_chrome() -> str:
    for candidate in CHROME_CANDIDATES:
        if Path(candidate).is_file():
            return candidate
    for name in ("chromium", "google-chrome", "google-chrome-stable", "chrome"):
        found = shutil.which(name)
        if found:
            return found
    return ""


def check_no_hand_authored_svg(html: Path) -> None:
    """Refuse a comp that draws its own `<svg>` instead of writing HTML/CSS.

    loop.md has said "never hand-author SVG" since this file's own history: a
    session once carried 59 such previews holding 6352 `<rect>` and 15 `<path>`
    the model invented rather than sourced, 34 of them faded to near-zero
    opacity. That was a prose rule nobody mechanically checked, so it kept
    getting written anyway. A comp needing a real graphic references a fetched
    or project asset with `<img src="...">` -- that never matches this check,
    because the SVG markup lives in the referenced file, not in the comp.
    """
    text = html.read_text(encoding="utf-8", errors="replace")
    if re.search(r"<svg\b", text, re.I):
        raise HarnessError(
            f"{html.name} hand-authors an <svg> element. Comps are drawn in HTML/CSS; "
            "a graphic is reused from the project, fetched from a pinned licensed source "
            "and referenced with <img src=\"...\">, generated deterministically in CSS, "
            "or omitted. See asset-sourcing.md. Remove the inline <svg> and redraw the "
            "comp before shooting it.")


def audit_recorded_svg(project_root: Path) -> list[dict[str, str]]:
    """Find elements ALREADY in the ledger whose recorded preview hand-authors SVG.

    `check_no_hand_authored_svg` only stops a NEW comp from being shot. It has
    no opinion on what a session recorded before that gate existed -- and a
    project that hit this failure for real can carry dozens of them, each one
    an element a designer cannot see rendered because there is no PNG to
    canonicalise, only the raw markup that made it into the article. This
    reads the ledger and reports every one by element id and recorded path, so
    they can be found and redrawn instead of discovered one crash at a time.
    """
    project_root = project_root.resolve(strict=True)
    output = project_root / "spec" / "design-harness"
    decisions_path = output / "decisions.json"
    if not decisions_path.is_file():
        return []
    decisions = json.loads(decisions_path.read_text(encoding="utf-8"))
    hits = []
    for entry in decisions.get("elements", []):
        preview = entry.get("preview")
        if not isinstance(preview, dict):
            continue
        rel = preview.get("path")
        if not rel or not str(rel).lower().endswith((".html", ".svg")):
            continue
        candidate = project_root / rel
        if not candidate.is_file():
            continue
        try:
            text = candidate.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if re.search(r"<svg\b", text, re.I):
            hits.append({"element": entry.get("element", ""), "path": str(rel)})
    return hits


def render_html_preview(html: Path, out: Path, width: int = PREVIEW_WIDTH,
                        timeout: int = 45, chrome_timeout: int = 12) -> str:
    """Rasterise a comp. Returns the renderer used, or raises.

    Chrome is preferred because it honours the CSS the comp was written in.
    `qlmanage` is the fallback that needs nothing installed, but QuickLook fits
    the page into a square thumbnail, so the comp must not depend on its own
    aspect ratio to read.

    Chrome and qlmanage get SEPARATE budgets. A local static-HTML screenshot
    should resolve in well under `chrome_timeout` seconds -- sharing one long
    `timeout` between both legs meant a hung or GPU-flaky Chrome process ate
    the whole budget before falling back, turning one slow shot into the
    worst-case wait for every shot in a round.
    """
    html = html.resolve(strict=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    height = int(round(width * PREVIEW_RATIO))
    chrome = find_chrome()
    if chrome:
        profile = tempfile.mkdtemp(prefix="dh-shot-")
        try:
            result = subprocess.run(
                [chrome, "--headless=new", "--disable-gpu", "--no-first-run",
                 "--no-default-browser-check", "--disable-extensions", "--disable-sync",
                 f"--user-data-dir={profile}", "--hide-scrollbars",
                 "--force-device-scale-factor=1", "--virtual-time-budget=3000",
                 f"--window-size={width},{height}",
                 f"--screenshot={out}", html.as_uri()],
                capture_output=True, timeout=chrome_timeout)
            if out.is_file() and out.stat().st_size:
                return "chrome"
            detail = (result.stderr or b"").decode("utf-8", "replace").strip()[:200]
        except subprocess.TimeoutExpired:
            # Chrome can finish writing the screenshot and then hang on exit
            # (GPU-process teardown, sandboxed disk) -- that hang fired this
            # timeout, but the file on disk is still a complete, correct
            # render. Discarding it here was falling back to qlmanage, whose
            # QuickLook thumbnail cache is keyed by path, not content: it
            # served a stale, garbled composite of a PREVIOUS render of this
            # same path as the "current" comp, which is what actually shipped
            # to the user as a bogus low-starred preview once.
            if out.is_file() and out.stat().st_size:
                return "chrome"
            detail = "timed out"
        finally:
            shutil.rmtree(profile, ignore_errors=True)
    else:
        detail = "no chrome/chromium found"
    if not shutil.which("qlmanage"):
        raise HarnessError(f"could not render {html.name}: {detail}, and qlmanage "
                           "is unavailable. Install Chrome or render the PNG yourself.")
    with tempfile.TemporaryDirectory() as staging:
        # Render LARGER than the target: QuickLook fits the page inside a square
        # and anchors it top-left, so the comp comes back small in a big empty
        # frame. Oversampling means the crop below still has pixels to keep.
        subprocess.run(["qlmanage", "-t", "-s", str(width * 3), "-o", staging, str(html)],
                       capture_output=True, timeout=timeout)
        made = list(Path(staging).glob("*.png"))
        if not made:
            raise HarnessError(f"could not render {html.name}: {detail}, and QuickLook "
                               "produced nothing either.")
        shutil.copyfile(made[0], out)
    trim_to_content(out, width)
    return "qlmanage"


def trim_to_content(png: Path, width: int) -> None:
    """Crop a render down to what was actually drawn, then scale it to width.

    QuickLook returns a SQUARE thumbnail with the page anchored top-left: a
    letter-shaped comp arrived as 171x221 of drawing inside 510x510 of white --
    85% empty. The article then fitted that whole square into a 96px portrait
    frame, so the comp itself rendered about 32px across and read as a blank
    card. Cropping to the content restores the comp's own aspect, and the frame
    fills the way it does for a Chrome render.

    A no-op on Chrome output, whose bounding box is already the whole image.
    """
    try:
        from PIL import Image, ImageChops
    except ImportError:
        return
    target = 1 / PREVIEW_RATIO          # width/height of the page we asked for
    with Image.open(png) as handle:
        image = handle.convert("RGB")
        # The corner pixel is the letterbox on a padded render -- but on a
        # FULL-BLEED one it is the comp's own ground, and cropping to "what
        # differs from it" then eats the design down to its ink. A test caught
        # that shaving 41px off a correct 510x660 render.
        #
        # So crop only when doing so RECOVERS the shape we asked for: the
        # padded square moves from 1.00 toward 0.77, while a full-bleed render
        # is already there and any crop takes it further away.
        ground = image.getpixel((0, 0))
        box = ImageChops.difference(
            image, Image.new("RGB", image.size, ground)).getbbox()
        if box:
            cropped_w, cropped_h = box[2] - box[0], box[3] - box[1]
            if cropped_w and cropped_h:
                before = abs(image.width / image.height - target)
                after = abs(cropped_w / cropped_h - target)
                if after < before:
                    image = image.crop(box)
        if image.width != width and image.width:
            height = max(1, round(image.height * width / image.width))
            image = image.resize((width, height), Image.LANCZOS)
        image.save(png)


def preview_ink(png: Path) -> dict[str, float]:
    """Measure what a rendered comp actually puts on the page.

    Reported as numbers rather than a verdict so the caller can say WHY it is
    refusing, and so a legitimately sparse comp can be argued about against a
    figure instead of an opinion.
    """
    try:
        from PIL import Image
    except ImportError:
        return {}
    with Image.open(png) as handle:
        image = handle.convert("RGB")
        if max(image.size) > 400:  # measuring does not need full resolution
            image.thumbnail((400, 400))
        # `getdata` is deprecated in Pillow 12 and gone in 14; `getpixel` over a
        # thumbnailed image is small enough that the loop costs nothing.
        width, height = image.size
        pixels = [image.getpixel((x, y)) for y in range(height) for x in range(width)]
    if not pixels:
        return {"coverage": 0.0, "contrast": 0.0}
    counts: dict[tuple, int] = {}
    for pixel in pixels:
        counts[pixel] = counts.get(pixel, 0) + 1
    ground = max(counts, key=counts.get)

    def distance(pixel: tuple) -> int:
        return sum(abs(a - b) for a, b in zip(pixel, ground))

    ink = [p for p in pixels if distance(p) > 40]
    return {"coverage": len(ink) / len(pixels),
            "contrast": float(max((distance(p) for p in ink), default=0)),
            "ground": ground}


def check_preview_legible(png: Path) -> None:
    """Refuse a comp the user would be asked to score without being able to see it."""
    ink = preview_ink(png)
    if not ink:  # no Pillow: measuring is unavailable, not failing
        return
    if ink["coverage"] < MIN_INK_COVERAGE:
        raise HarnessError(
            f"{png.name} renders essentially blank -- {ink['coverage'] * 100:.2f}% of the "
            f"page differs from its own ground. This is the `opacity=0.13` failure: the "
            "markup is there and the drawing is not. Open the HTML, fix what is hiding it, "
            "and shoot it again. Do not record a preview the user cannot see.")
    if ink["contrast"] < MIN_INK_CONTRAST:
        raise HarnessError(
            f"{png.name} has ink but no contrast -- the strongest mark is only "
            f"{ink['contrast']:.0f}/765 away from the ground. Nothing on this page can be "
            "read at thumbnail size, so a score would be a score of nothing.")


def preferred_preview_path(project_root: Path, preview_path: Path, element: str) -> Path:
    """Prefer the drawn HTML comp over a raster thumbnail when both exist."""
    if preview_path.suffix.lower() == ".html":
        return preview_path
    for candidate in (
        project_root / "content" / f"{element}.html",
        project_root / "content" / f"{preview_path.stem}.html",
    ):
        if candidate.is_file():
            return candidate
    return preview_path
