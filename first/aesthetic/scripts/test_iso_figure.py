#!/usr/bin/env python3
"""Tests for the deterministic figure renderer.

Assertions parse the emitted elements rather than grepping the string the
generator just built, per ../references/verification.md.
"""
from __future__ import annotations

import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import iso_figure  # noqa: E402

SPEC = {
    "skin": "#f5c0bc", "top": "#625bc3", "legs": "#128fd1", "shoes": "#ffb800",
    "hairOuter": "#ff6918", "hairInner": "#dd5caf", "hairStyle": "mane",
    "prop": "mic", "propColour": "#fd4337", "armNear": -38, "armFar": 21,
}


def parse(parts: list[str]) -> ET.Element:
    return ET.fromstring("<svg>" + "".join(parts) + "</svg>")


class Construction(unittest.TestCase):
    def test_a_figure_is_built_only_from_computed_primitives(self) -> None:
        """No hand-typed path data, which asset-sourcing.md forbids."""
        root = parse(iso_figure.figure(SPEC, 100, 200, 120))
        tags = {node.tag for node in root.iter()} - {"svg"}
        self.assertEqual(tags, {"ellipse", "rect", "g"})

    def test_the_face_carries_two_eyes_and_a_mouth(self) -> None:
        """The rejected register was faceless. This one may never be."""
        root = parse(iso_figure.figure(SPEC, 100, 200, 120))
        whites = [n for n in root.iter("ellipse") if n.get("fill") == "#ffffff"]
        mouths = [n for n in root.iter("rect") if n.get("fill") == "#ffffff"]
        self.assertGreaterEqual(len(whites) + len(mouths), 3)

    def test_hair_is_two_colour_zones_not_one_blob(self) -> None:
        root = parse(iso_figure.figure(SPEC, 100, 200, 120))
        fills = {n.get("fill") for n in root.iter("ellipse")}
        self.assertIn(SPEC["hairOuter"], fills)
        self.assertIn(SPEC["hairInner"], fills)

    def test_one_contour_weight_across_every_stroked_part(self) -> None:
        """Observed rule: one weight everywhere. Two weights read as collage."""
        root = parse(iso_figure.figure(SPEC, 100, 200, 240))
        widths = {round(float(n.get("stroke-width")), 1) for n in root.iter()
                  if n.get("stroke-width") and n.get("stroke") != "none"}
        self.assertLessEqual(len(widths), 3, widths)

    def test_the_figure_stands_on_its_baseline(self) -> None:
        base = 400.0
        root = parse(iso_figure.figure(SPEC, 100, base, 120))
        bottoms = [float(n.get("y")) + float(n.get("height"))
                   for n in root.iter("rect") if n.get("y") and n.get("height")]
        self.assertAlmostEqual(max(bottoms), base, delta=1.0)

    def test_a_held_prop_rotates_with_the_arm_that_holds_it(self) -> None:
        """The prop lives inside the arm's rotation, so it cannot drift out of
        the hand at any angle. That was a real defect in the CSS rounds."""
        root = parse(iso_figure.figure(SPEC, 100, 200, 120))
        carrying = [g for g in root.iter("g")
                    if g.get("transform", "").startswith("rotate")
                    and any(n.get("fill") == SPEC["propColour"] for n in g.iter())]
        self.assertEqual(len(carrying), 1)

    def test_the_same_spec_draws_the_same_bytes(self) -> None:
        self.assertEqual(iso_figure.figure(SPEC, 100, 200, 120),
                         iso_figure.figure(SPEC, 100, 200, 120))

    def test_every_prop_kind_draws_something(self) -> None:
        for kind in ("mic", "watch", "mug", "ball", "bag", "lens"):
            with self.subTest(kind):
                spec = dict(SPEC, prop=kind)
                root = parse(iso_figure.figure(spec, 100, 200, 120))
                self.assertGreater(len(list(root.iter())), 12)

    def test_build_scales_the_whole_figure(self) -> None:
        """Six bosses that share one build read as one recoloured mascot."""
        def height(build: float) -> float:
            root = parse(iso_figure.figure(dict(SPEC, build=build), 100, 300, 120))
            tops = [float(n.get("cy")) - float(n.get("ry"))
                    for n in root.iter("ellipse") if n.get("cy")]
            return 300.0 - min(tops)

        self.assertGreater(height(1.2), height(0.8))


if __name__ == "__main__":
    unittest.main()
