#!/usr/bin/env python3
"""Turn a scene spec into pixel geometry and an axonometric SVG.

`layout` is the only place scene semantics become coordinates. `render` draws
what `layout` returned and invents nothing. The gate re-reads the drawn road
and checks it with `self_intersections` and `visit_order` from here.
"""
from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

CANVAS = (1600, 900)
CENTER = (800.0, 480.0)
LOBE_X = 700.0
LOBE_Y = 440.0
ROAD_SAMPLES = 96

ROOM = {"hw": 250.0, "hd": 95.0, "h": 40.0}
KIOSK = {"hw": 95.0, "hd": 48.0, "h": 30.0}

BACKGROUND = "#faf5ee"
ROAD_STROKE = "#f4c430"
OUTLINE = "#1b2430"

PALETTE_FILL = {
    "cyan": "#00bcd4",
    "turquoise": "#00bcd4",
    "magenta": "#e91e63",
    "hot-pink": "#e91e63",
    "cobalt": "#1565c0",
    "operational-blue": "#1565c0",
    "emerald": "#2e7d32",
    "project-green": "#2e7d32",
    "ghost-pastel-peach": "#fff5f0",
    "ghost-pastel-blue-gray": "#f5f8fa",
}

# Gerono lemniscate parameter at which each room sits, in road travel order.
ROOM_PHASE = {
    "upper-left": 0.75 * math.pi,
    "lower-left": 1.25 * math.pi,
    "upper-right": 1.75 * math.pi,
    "lower-right": 0.25 * math.pi,
}
KIOSK_OFFSET = {"left-center": -0.5, "right-center": 0.5}


class GeometryError(ValueError):
    pass


def road_point(t: float) -> tuple[float, float]:
    cx, cy = CENTER
    return cx + LOBE_X * math.cos(t), cy + (LOBE_Y / 2.0) * math.sin(2.0 * t)


def road_polyline(samples: int = ROAD_SAMPLES) -> list[tuple[float, float]]:
    """Closed figure-eight, traversed /first, /build, /land, /check.

    Sampling starts half a step past the crossing so no vertex lands on it and
    the two passes read as a genuine segment crossing.
    """
    step = 2.0 * math.pi / samples
    start = 0.5 * math.pi + step / 2.0
    points = [road_point(start + index * step) for index in range(samples)]
    points.append(points[0])
    return points


def _fill(palette: Any) -> str:
    if isinstance(palette, list) and palette:
        palette = palette[0]
    return PALETTE_FILL.get(str(palette), "#cccccc")


def _shade(hex_color: str, factor: float) -> str:
    value = hex_color.lstrip("#")
    channels = (int(value[index:index + 2], 16) for index in (0, 2, 4))
    return "#" + "".join(f"{min(255, int(c * factor)):02x}" for c in channels)


def _place(entry: Mapping[str, Any], size: Mapping[str, float],
           billboards: Mapping[str, Any]) -> dict[str, Any]:
    identifier = str(entry.get("id") or "")
    position = str(entry.get("position") or "")
    if position in ROOM_PHASE:
        cx, cy = road_point(ROOM_PHASE[position])
    elif position in KIOSK_OFFSET:
        cx = CENTER[0] + KIOSK_OFFSET[position] * LOBE_X
        cy = CENTER[1]
    else:
        raise GeometryError(f"unknown position {position!r} for {identifier}")
    return {
        "id": identifier,
        "slug": identifier.strip("/").replace("/", "_"),
        "cx": cx,
        "cy": cy,
        "fill": _fill(entry.get("palette")),
        "text": str(billboards.get(identifier, "")),
        **size,
    }


def _overlaps(a: Mapping[str, Any], b: Mapping[str, Any]) -> bool:
    return (abs(a["cx"] - b["cx"]) < a["hw"] + b["hw"]
            and abs(a["cy"] - b["cy"]) < a["hd"] + b["hd"] + max(a["h"], b["h"]))


DRAWS = {"isometric-x"}


def layout(scene: Mapping[str, Any]) -> dict[str, Any]:
    """Rung 2b. This renderer draws one family of scene, and says so when it cannot.

    Room centres come from the road curve rather than the scene's normalized
    positions, which is why it is a fixture renderer and AVGE is the general one.
    """
    if str(scene.get("layout")) not in DRAWS:
        raise GeometryError(
            f"iso_svg draws {sorted(DRAWS)}, not {scene.get('layout')!r}; use AVGE")
    billboards = scene.get("billboards") or {}
    boxes = [_place(room, ROOM, billboards) for room in scene.get("mainRooms", [])]
    boxes += [_place(kiosk, KIOSK, billboards) for kiosk in scene.get("kiosks", [])]
    for index, box in enumerate(boxes):
        for other in boxes[index + 1:]:
            if _overlaps(box, other):
                raise GeometryError(f"{box['id']} overlaps {other['id']}")
        width, height = CANVAS
        if not (0 <= box["cx"] - box["hw"] and box["cx"] + box["hw"] <= width
                and 0 <= box["cy"] - box["hd"] - 110
                and box["cy"] + box["hd"] + box["h"] <= height):
            raise GeometryError(f"{box['id']} falls outside the canvas")
    return {"canvas": CANVAS, "road": road_polyline(), "boxes": boxes}


def self_intersections(points: Sequence[tuple[float, float]]) -> int:
    """Count proper crossings of a closed polyline.

    ponytail: O(n^2) over 96 segments. Index the segments if a scene ever
    needs thousands of them.
    """
    def side(o, a, b):
        return ((a[0] - o[0]) * (b[1] - o[1])) - ((a[1] - o[1]) * (b[0] - o[0]))

    total = len(points) - 1
    crossings = 0
    for i in range(total):
        for j in range(i + 2, total):
            if i == 0 and j == total - 1:
                continue
            p, q, r, s = points[i], points[i + 1], points[j], points[j + 1]
            d1, d2 = side(p, q, r), side(p, q, s)
            d3, d4 = side(r, s, p), side(r, s, q)
            if d1 * d2 < 0 and d3 * d4 < 0:
                crossings += 1
    return crossings


def visit_order(points: Sequence[tuple[float, float]],
                anchors: Sequence[tuple[str, float, float]]) -> list[str]:
    """Anchor ids in the order the polyline reaches them."""
    nearest = []
    for identifier, ax, ay in anchors:
        index = min(range(len(points)),
                    key=lambda i: (points[i][0] - ax) ** 2 + (points[i][1] - ay) ** 2)
        nearest.append((index, identifier))
    return [identifier for _, identifier in sorted(nearest)]


def _diamond(box: Mapping[str, Any]) -> str:
    cx, cy, hw, hd = box["cx"], box["cy"], box["hw"], box["hd"]
    corners = ((cx, cy - hd), (cx + hw, cy), (cx, cy + hd), (cx - hw, cy))
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in corners)


def _box_svg(box: Mapping[str, Any]) -> list[str]:
    cx, cy, hw, hd, h = box["cx"], box["cy"], box["hw"], box["hd"], box["h"]
    fill = box["fill"]
    left = f"{cx - hw:.1f},{cy:.1f} {cx:.1f},{cy + hd:.1f} " \
           f"{cx:.1f},{cy + hd + h:.1f} {cx - hw:.1f},{cy + h:.1f}"
    right = f"{cx:.1f},{cy + hd:.1f} {cx + hw:.1f},{cy:.1f} " \
            f"{cx + hw:.1f},{cy + h:.1f} {cx:.1f},{cy + hd + h:.1f}"
    return [
        f'<g id="{box["slug"]}">',
        f'<polygon points="{left}" fill="{_shade(fill, 0.62)}" stroke="{OUTLINE}" stroke-width="3"/>',
        f'<polygon points="{right}" fill="{_shade(fill, 0.80)}" stroke="{OUTLINE}" stroke-width="3"/>',
        f'<polygon points="{_diamond(box)}" fill="{fill}" stroke="{OUTLINE}" stroke-width="3"/>',
        "</g>",
    ]


def _billboard_svg(box: Mapping[str, Any]) -> list[str]:
    """Sign above the box, shifted away from the canvas centre.

    The middle of the canvas belongs to the kiosks and the road crossing, so
    room signs lean outward and never land on either.
    """
    cx, cy, hd = box["cx"], box["cy"], box["hd"]
    text = box["text"]
    panel_w = max(150.0, 15.0 * len(text))
    panel_h, pole_h = 46.0, 54.0
    sx = cx + (box["hw"] * 0.5 if cx > CENTER[0] else -box["hw"] * 0.5)
    top = cy - hd - pole_h - panel_h
    parts = [f'<g id="{box["slug"]}_billboard">']
    for offset in (-panel_w / 3.0, panel_w / 3.0):
        parts.append(
            f'<rect x="{sx + offset - 4:.1f}" y="{cy - hd - pole_h:.1f}" '
            f'width="8" height="{pole_h:.1f}" fill="{OUTLINE}"/>')
    parts.append(
        f'<rect x="{sx - panel_w / 2:.1f}" y="{top:.1f}" width="{panel_w:.1f}" '
        f'height="{panel_h:.1f}" rx="6" fill="#ffffff" stroke="{OUTLINE}" stroke-width="3"/>')
    parts.append(_text_svg(sx, top + panel_h / 2 + 8, 24, text))
    parts.append("</g>")
    return parts


def _roof_label_svg(box: Mapping[str, Any]) -> list[str]:
    """Kiosks wear their command on the roof. A pole here would hit a room."""
    return [f'<g id="{box["slug"]}_billboard">',
            _text_svg(box["cx"], box["cy"] + 7, 19, box["text"]),
            "</g>"]


def _text_svg(x: float, y: float, size: int, text: str) -> str:
    return (f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" '
            f'font-family="Menlo, monospace" font-size="{size}" font-weight="700" '
            f'fill="{OUTLINE}">{text}</text>')


def render(plan: Mapping[str, Any]) -> str:
    width, height = plan["canvas"]
    road = " ".join(f"{x:.1f},{y:.1f}" for x, y in plan["road"])
    boxes = sorted(plan["boxes"], key=lambda box: box["cy"])
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}">',
        f'<rect width="{width}" height="{height}" fill="{BACKGROUND}"/>',
        f'<polyline id="road" points="{road}" fill="none" stroke="{OUTLINE}" '
        f'stroke-width="52" stroke-linejoin="round"/>',
        f'<polyline points="{road}" fill="none" stroke="{ROAD_STROKE}" '
        f'stroke-width="44" stroke-linejoin="round"/>',
        f'<polyline points="{road}" fill="none" stroke="#ffffff" stroke-width="4" '
        f'stroke-dasharray="26 22" stroke-linejoin="round"/>',
    ]
    for box in boxes:
        parts += _box_svg(box)
    for box in boxes:
        parts += (_roof_label_svg(box) if box["hw"] == KIOSK["hw"]
                  else _billboard_svg(box))
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def build(scene: Mapping[str, Any]) -> str:
    return render(layout(scene))
