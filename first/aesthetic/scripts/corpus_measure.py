#!/usr/bin/env python3
"""Read what a reference image actually looks like.

`observe` records a hash and a byte count per image, so it proves a file exists
and says nothing about its pixels. Everything downstream then directs from prose
and filenames, and the renderer fills shapes from constants no reference
evidences. This module is the read that was missing: PNG in, measured colour
out, so a later step can cite a hex some reference actually contains.

PNG only, 8-bit, colour types 2 and 6, no interlacing. Anything else is reported
unmeasured. A guessed palette is the failure this exists to stop, so refusing to
measure beats inventing a number.

Deterministic by construction: no timestamps, no sampling by chance. The same
bytes in produce the same JSON out, which is what lets a staleness hash mean
something.
"""
from __future__ import annotations

import struct
import zlib
from pathlib import Path
from typing import Any, Iterable, Mapping

SIGNATURE = b"\x89PNG\r\n\x1a\n"

# Two flat fills separated by less than this in RGB are the same brand colour
# seen through antialiasing, not two decisions. Wide enough to absorb edge
# pixels, narrow enough to keep a turquoise and a cobalt apart.
MERGE_DISTANCE = 56

# A colour under this share of the frame is a fleck: a JPEG artefact, one letter
# of a watermark, one antialiased corner. It is not a palette entry.
MIN_COVERAGE = 0.004

# Luminance below this reads as contour rather than fill.
INK_LUMINANCE = 90

# Luminance above this can serve as the ground a drawing sits on. The widest
# colour in a frame is often a large flat shape, not the paper, so "widest"
# alone reported a green as the background of a cartoon on white.
PAPER_LUMINANCE = 200


class MeasureError(ValueError):
    """The file cannot be measured. Never raised to mean 'measured as empty'."""


def _luminance(rgb: tuple[int, int, int]) -> float:
    red, green, blue = rgb
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def _hex(rgb: tuple[int, int, int]) -> str:
    return "#%02x%02x%02x" % rgb


def _distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    return sum((one - two) ** 2 for one, two in zip(a, b)) ** 0.5


def _chunks(data: bytes) -> Iterable[tuple[bytes, bytes]]:
    if not data.startswith(SIGNATURE):
        raise MeasureError("not a PNG")
    position = len(SIGNATURE)
    while position + 8 <= len(data):
        (length,) = struct.unpack(">I", data[position:position + 4])
        kind = data[position + 4:position + 8]
        body = data[position + 8:position + 8 + length]
        yield kind, body
        position += 12 + length


def _undo_filters(raw: bytes, width: int, height: int, sample: int) -> bytearray:
    """Reverse the per-scanline filters PNG applies before compression.

    Rows are reconstructed in order because filters 2, 3 and 4 read the row
    above, so there is no way to decode a subset of the image.
    """
    stride = width * sample
    out = bytearray(stride * height)
    previous = bytearray(stride)
    position = 0
    for row in range(height):
        if position >= len(raw):
            raise MeasureError("PNG data ends before the last scanline")
        kind = raw[position]
        position += 1
        line = bytearray(raw[position:position + stride])
        position += stride
        if len(line) < stride:
            raise MeasureError("PNG scanline is short")
        if kind == 1:
            for index in range(sample, stride):
                line[index] = (line[index] + line[index - sample]) & 0xFF
        elif kind == 2:
            for index in range(stride):
                line[index] = (line[index] + previous[index]) & 0xFF
        elif kind == 3:
            for index in range(stride):
                left = line[index - sample] if index >= sample else 0
                line[index] = (line[index] + ((left + previous[index]) >> 1)) & 0xFF
        elif kind == 4:
            for index in range(stride):
                left = line[index - sample] if index >= sample else 0
                up = previous[index]
                corner = previous[index - sample] if index >= sample else 0
                estimate = left + up - corner
                by_left = abs(estimate - left)
                by_up = abs(estimate - up)
                by_corner = abs(estimate - corner)
                if by_left <= by_up and by_left <= by_corner:
                    nearest = left
                elif by_up <= by_corner:
                    nearest = up
                else:
                    nearest = corner
                line[index] = (line[index] + nearest) & 0xFF
        elif kind != 0:
            raise MeasureError(f"unsupported PNG filter {kind}")
        out[row * stride:(row + 1) * stride] = line
        previous = line
    return out


def decode_png(data: bytes) -> dict[str, Any]:
    """Width, height, and one opaque RGB triple per pixel."""
    header = b""
    body = bytearray()
    for kind, chunk in _chunks(data):
        if kind == b"IHDR":
            header = chunk
        elif kind == b"IDAT":
            body += chunk
        elif kind == b"IEND":
            break
    if len(header) < 13:
        raise MeasureError("PNG has no IHDR")
    width, height, depth, colour, _, _, interlace = struct.unpack(">IIBBBBB", header[:13])
    if depth != 8:
        raise MeasureError(f"unsupported PNG bit depth {depth}")
    if colour not in (2, 6):
        raise MeasureError(f"unsupported PNG colour type {colour}")
    if interlace:
        raise MeasureError("interlaced PNG")
    sample = 3 if colour == 2 else 4
    flat = _undo_filters(zlib.decompress(bytes(body)), width, height, sample)
    pixels = []
    if sample == 3:
        for index in range(0, len(flat), 3):
            pixels.append((flat[index], flat[index + 1], flat[index + 2]))
    else:
        # Composite over white so a transparent margin cannot be counted as
        # black, which would hand every screenshot the same fake ink colour.
        for index in range(0, len(flat), 4):
            alpha = flat[index + 3]
            if alpha == 255:
                pixels.append((flat[index], flat[index + 1], flat[index + 2]))
            else:
                mix = alpha / 255.0
                pixels.append(tuple(
                    round(flat[index + offset] * mix + 255 * (1.0 - mix))
                    for offset in range(3)))
    return {"width": width, "height": height, "pixels": pixels}


def encode_png(width: int, height: int,
               pixels: list[tuple[int, int, int]]) -> bytes:
    """Write 8-bit RGB back out, unfiltered. The inverse of `decode_png`."""
    raw = bytearray()
    index = 0
    for _ in range(height):
        raw.append(0)
        for _ in range(width):
            raw += bytes(pixels[index])
            index += 1

    def chunk(kind: bytes, body: bytes) -> bytes:
        return (struct.pack(">I", len(body)) + kind + body
                + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF))

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (SIGNATURE + chunk(b"IHDR", header)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))


def crop_png(data: bytes, box: tuple[int, int, int, int], scale: int = 1) -> bytes:
    """One region of a reference, enlarged, so a figure can actually be looked at.

    Characters in this corpus are 30 to 60 pixels tall. Claims about how they
    are built cannot be made from the whole frame, and a claim made without
    looking is the guess that keeps getting rejected. Nearest-neighbour, so the
    enlargement invents no colour that was not in the source.
    """
    image = decode_png(data)
    left, top, width, height = box
    if scale < 1:
        raise MeasureError("scale must be at least 1")
    if width < 1 or height < 1:
        raise MeasureError("crop box has no area")
    if left < 0 or top < 0 or left + width > image["width"] or top + height > image["height"]:
        raise MeasureError(
            f"crop {box} falls outside {image['width']}x{image['height']}")
    source = image["pixels"]
    stride = image["width"]
    out: list[tuple[int, int, int]] = []
    for row in range(height * scale):
        base = (top + row // scale) * stride
        for column in range(width * scale):
            out.append(source[base + left + column // scale])
    return encode_png(width * scale, height * scale, out)


def palette_of(pixels: list[tuple[int, int, int]], top: int = 6) -> list[dict[str, Any]]:
    """The flat fills this image is built from, widest coverage first.

    Exact colours are counted, then merged into the nearest heavier neighbour,
    because flat cartoon art is a handful of decisions surrounded by a halo of
    antialiased in-between pixels that are not decisions at all.
    """
    if not pixels:
        return []
    counts: dict[tuple[int, int, int], int] = {}
    for pixel in pixels:
        counts[pixel] = counts.get(pixel, 0) + 1
    ordered = sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))
    representatives: list[tuple[int, int, int]] = []
    for colour, _ in ordered:
        if len(representatives) >= top:
            break
        if all(_distance(colour, chosen) >= MERGE_DISTANCE for chosen in representatives):
            representatives.append(colour)
    if not representatives:
        return []
    totals = {colour: 0 for colour in representatives}
    for colour, count in counts.items():
        nearest = min(representatives, key=lambda chosen: _distance(colour, chosen))
        if _distance(colour, nearest) < MERGE_DISTANCE:
            totals[nearest] += count
    depth = len(pixels)
    palette = [{"hex": _hex(colour), "rgb": list(colour),
                "coverage": round(totals[colour] / depth, 4)}
               for colour in representatives if totals[colour] / depth >= MIN_COVERAGE]
    return sorted(palette, key=lambda entry: -entry["coverage"])


def measure_bytes(data: bytes) -> dict[str, Any]:
    """Every visual fact this module is willing to claim about one image."""
    image = decode_png(data)
    pixels = image["pixels"]
    palette = palette_of(pixels)
    if not palette:
        raise MeasureError("no colour covers enough of the frame to be a palette entry")
    dark = sum(1 for pixel in pixels if _luminance(pixel) < INK_LUMINANCE)
    inks = [entry for entry in palette if _luminance(tuple(entry["rgb"])) < INK_LUMINANCE]
    papers = [entry for entry in palette
              if _luminance(tuple(entry["rgb"])) >= PAPER_LUMINANCE]
    return {
        "width": image["width"],
        "height": image["height"],
        "aspect": round(image["width"] / image["height"], 3),
        "palette": palette,
        # The widest colour overall and the widest light one are different
        # questions, and conflating them is how a green became a background.
        "dominant": palette[0]["hex"],
        "paper": papers[0]["hex"] if papers else None,
        "ink": (min(inks, key=lambda entry: _luminance(tuple(entry["rgb"])))["hex"]
                if inks else None),
        "inkShare": round(dark / len(pixels), 4),
    }


def measure_file(path: Path) -> dict[str, Any]:
    return measure_bytes(Path(path).read_bytes())


def measure_corpus(project_root: Path, items: Iterable[Mapping[str, Any]]
                   ) -> dict[str, Any]:
    """Measure every listed image, and name the ones that could not be read.

    An unreadable reference is recorded rather than dropped: a reference the
    prompt cites but nobody has looked at is exactly the gap this file exists
    to make visible.
    """
    measured: dict[str, Any] = {}
    unmeasured: list[dict[str, str]] = []
    for item in items:
        digest = str(item.get("sha256") or "")
        relative = str(item.get("path") or "")
        source = Path(str(item.get("inspectPath") or ""))
        if not source.is_absolute():
            source = Path(project_root) / source
        try:
            record = measure_file(source)
        except (MeasureError, OSError, zlib.error) as exc:
            unmeasured.append({"path": relative, "sha256": digest, "reason": str(exc)})
            continue
        record["path"] = relative
        measured[digest] = record
    return {"version": 1, "images": measured,
            "unmeasured": sorted(unmeasured, key=lambda entry: entry["path"])}
