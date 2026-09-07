#!/usr/bin/env python3
"""Draw one cartoon figure from parameters, deterministically.

The point of the skill is to out-draw the image generator, and the thing the
generator could do that this renderer could not was put anybody in the rooms.
Six empty coloured diamonds lose to a flawed picture with people in it, however
broken that picture's road is.

Every shape here is an ellipse, a circle or a rounded rect placed by arithmetic
from one number, the figure's height. No hand-typed path coordinates, which is
what `asset-sourcing.md` forbids: the procedure IS the drawing, and the same
inputs give the same bytes.

Construction follows `character-observations.json`, read off the corpus:
large white eyes with the body's own contour, hair in two zones, an ear proud
of the head, an open white mouth, limbs that overlap the body, one contour
weight throughout. Arms pivot at the shoulder and a held prop is drawn inside
the arm's rotation, so it cannot drift out of the hand at any angle.
"""
from __future__ import annotations

from typing import Any, Mapping

INK = "#1b2430"

# Proportions as a fraction of total figure height, measured up from the feet.
# Head is a little under half the figure: chibi, per the observed corpus, and
# explicitly not the 1:5 realistic ratio the user rejected as "ugly cartoons".
SHOE_TOP = 0.075
LEG_TOP = 0.30
BODY_TOP = 0.58
SHOULDER = 0.545
HEAD_R = 0.185
HEAD_CY = 0.775


def _e(cx: float, cy: float, rx: float, ry: float, fill: str, w: float,
       stroke: str = INK) -> str:
    return (f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{w:.1f}"/>')


def _r(x: float, y: float, width: float, height: float, radius: float,
       fill: str, w: float, stroke: str = INK) -> str:
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" '
            f'height="{height:.1f}" rx="{radius:.1f}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{w:.1f}"/>')


def _prop(kind: str, colour: str, x: float, y: float, h: float, w: float) -> list[str]:
    """The signature object, drawn at the hand end of the arm that carries it."""
    if kind == "mic":
        return [_r(x - 0.030 * h, y, 0.060 * h, 0.115 * h, 0.030 * h, colour, w)]
    if kind == "watch":
        return [_r(x - 0.040 * h, y, 0.080 * h, 0.060 * h, 0.015 * h, colour, w)]
    if kind == "mug":
        return [_r(x - 0.045 * h, y, 0.090 * h, 0.090 * h, 0.018 * h, colour, w)]
    if kind == "ball":
        return [_e(x, y + 0.085 * h, 0.085 * h, 0.085 * h, colour, w),
                _e(x - 0.030 * h, y + 0.055 * h, 0.026 * h, 0.019 * h, "#ffffff", 0,
                   "none")]
    if kind == "bag":
        return [_r(x - 0.038 * h, y + 0.020 * h, 0.076 * h, 0.020 * h, 0.010 * h,
                   "none", w),
                _r(x - 0.052 * h, y + 0.032 * h, 0.104 * h, 0.130 * h, 0.014 * h,
                   colour, w)]
    if kind == "lens":
        return [_r(x - 0.014 * h, y, 0.028 * h, 0.075 * h, 0.012 * h, INK, w),
                _e(x, y + 0.150 * h, 0.088 * h, 0.088 * h, colour, w * 1.2),
                _e(x + 0.020 * h, y + 0.140 * h, 0.030 * h, 0.026 * h, "#009a44", w)]
    return []


def _hair(style: str, cx: float, cy: float, r: float, outer: str, inner: str,
          h: float, w: float) -> list[str]:
    """Two stacked zones with a shaped inner edge. Never one flat blob, and
    never a hard block sitting on the head, which reads as a hat."""
    if style == "mane":
        return [_e(cx, cy + 0.030 * h, r * 1.75, r * 1.20, outer, w),
                _e(cx - r * 1.35, cy - 0.030 * h, r * 0.55, r * 0.85, outer, w),
                _e(cx + r * 1.35, cy - 0.030 * h, r * 0.55, r * 0.85, outer, w),
                _e(cx, cy + 0.048 * h, r * 1.02, r * 0.46, inner, w)]
    if style == "styled":
        return [_e(cx, cy + 0.040 * h, r * 1.48, r * 1.02, outer, w),
                _e(cx, cy + 0.050 * h, r * 0.94, r * 0.40, inner, w)]
    if style == "bob":
        return [_e(cx, cy + 0.018 * h, r * 1.26, r * 1.16, outer, w),
                _e(cx, cy + 0.046 * h, r * 0.88, r * 0.40, inner, w)]
    return [_e(cx, cy + 0.058 * h, r * 1.06, r * 0.62, outer, w),
            _e(cx - r * 0.30, cy + 0.070 * h, r * 0.62, r * 0.30, inner, w)]


def figure(spec: Mapping[str, Any], cx: float, base_y: float,
           height: float) -> list[str]:
    """One figure standing with its feet at `base_y`, centred on `cx`."""
    h = float(height) * float(spec.get("build") or 1.0)
    w = max(1.6, h / 40.0)
    skin = str(spec.get("skin") or "#f5c0bc")
    top = str(spec.get("top") or "#128fd1")

    def up(fraction: float) -> float:
        return base_y - fraction * h

    body_w = 0.40 * h
    head_r = HEAD_R * h
    head_cy = up(HEAD_CY)
    shoulder_y = up(SHOULDER)
    arm_len = 0.30 * h
    arm_w = 0.095 * h

    def arm(angle: float, side: int, near: bool) -> list[str]:
        """Pivots at the shoulder. A prop lives inside the same rotation, so
        the hand keeps hold of it whatever the angle is."""
        sx = cx + side * (body_w * 0.52)
        parts = [_r(sx - arm_w / 2, shoulder_y, arm_w, arm_len, arm_w / 2,
                    spec.get("sleeve", top), w)]
        if near and spec.get("prop"):
            parts += _prop(str(spec["prop"]), str(spec.get("propColour") or "#ffffff"),
                           sx, shoulder_y + arm_len - 0.02 * h, h, w)
        return [f'<g transform="rotate({angle:.1f} {sx:.1f} {shoulder_y:.1f})">',
                *parts, "</g>"]

    out: list[str] = []
    # Feet and legs first: everything else overlaps forward from here.
    for side in (-1, 1):
        lx = cx + side * 0.115 * h
        out.append(_r(lx - 0.055 * h, up(LEG_TOP), 0.110 * h,
                      (LEG_TOP - SHOE_TOP) * h, 0.030 * h,
                      str(spec.get("legs") or "#8d88a6"), w))
        out.append(_r(lx - 0.085 * h, up(SHOE_TOP), 0.170 * h, SHOE_TOP * h,
                      0.045 * h, str(spec.get("shoes") or "#ffffff"), w))

    out += arm(float(spec.get("armFar") or 18), -1, near=False)
    out.append(_r(cx - body_w / 2, up(BODY_TOP), body_w, (BODY_TOP - LEG_TOP) * h,
                  0.115 * h, top, w))
    if spec.get("vest"):
        for side in (-1, 1):
            out.append(_r(cx + side * body_w * 0.30 - 0.085 * h, up(BODY_TOP),
                          0.170 * h, (BODY_TOP - LEG_TOP) * h * 1.02, 0.055 * h,
                          str(spec["vest"]), w))
    if spec.get("collar"):
        out.append(_r(cx - body_w * 0.42, up(BODY_TOP) - 0.012 * h, body_w * 0.84,
                      0.070 * h, 0.035 * h, str(spec["collar"]), w))

    out.append(_e(cx - head_r * 0.96, head_cy + 0.018 * h, 0.048 * h, 0.048 * h,
                  skin, w))                                    # ear, proud of the head
    out.append(_e(cx, head_cy, head_r, head_r, skin, w))
    out += _hair(str(spec.get("hairStyle") or "crop"), cx, head_cy, head_r,
                 str(spec.get("hairOuter") or INK),
                 str(spec.get("hairInner") or INK), h, w)

    # Face last of the head, so hair can never paint over it.
    eye_fill = str(spec.get("lens") or "#ffffff")
    for side in (-1, 1):
        ex = cx + side * 0.072 * h
        out.append(_e(ex, head_cy - 0.008 * h, 0.052 * h, 0.058 * h, eye_fill, w * 0.8))
        out.append(_e(ex + side * 0.008 * h, head_cy + 0.008 * h, 0.020 * h,
                      0.024 * h, INK, 0, "none"))
    if spec.get("lens"):
        out.append(_r(cx - 0.026 * h, head_cy - 0.014 * h, 0.052 * h, 0.016 * h,
                      0.008 * h, INK, 0, "none"))
    out.append(_r(cx - 0.038 * h, head_cy + 0.070 * h, 0.076 * h, 0.042 * h,
                  0.018 * h, "#ffffff", w * 0.8))

    if spec.get("headgear") == "headset":
        band = str(spec.get("headgearColour") or "#fd4337")
        # A ring, not an arc path: the band reads the same and the module keeps
        # its promise that no coordinate here is hand-typed.
        out.append(_e(cx, head_cy - 0.010 * h, head_r * 1.12, head_r * 1.02,
                      "none", w * 1.6))
        for side in (-1, 1):
            out.append(_r(cx + side * head_r * 1.12 - 0.040 * h, head_cy - 0.010 * h,
                          0.080 * h, 0.105 * h, 0.022 * h, band, w))

    out += arm(float(spec.get("armNear") or -20), 1, near=True)
    return out
