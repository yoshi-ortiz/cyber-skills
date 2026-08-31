#!/usr/bin/env python3
import json
import unittest
from pathlib import Path

import iso_svg

SCENE = json.loads((Path(__file__).resolve().parents[2]
                    / "spec/design-harness/scene-spec.json").read_text(encoding="utf-8"))


class RoadTests(unittest.TestCase):
    def test_the_road_closes_and_crosses_itself_once(self) -> None:
        road = iso_svg.road_polyline()
        self.assertEqual(road[0], road[-1])
        self.assertEqual(iso_svg.self_intersections(road), 1)

    def test_the_road_reaches_the_spaces_in_sequence_order(self) -> None:
        plan = iso_svg.layout(SCENE)
        sequence = SCENE["road"]["sequence"][:-1]
        anchors = [(box["id"], box["cx"], box["cy"]) for box in plan["boxes"]
                   if box["id"] in sequence]
        self.assertEqual(iso_svg.visit_order(plan["road"], anchors), sequence)

    def test_a_square_is_not_mistaken_for_a_figure_eight(self) -> None:
        square = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0), (0.0, 0.0)]
        self.assertEqual(iso_svg.self_intersections(square), 0)


class LayoutTests(unittest.TestCase):
    def test_overlapping_spaces_are_refused(self) -> None:
        scene = json.loads(json.dumps(SCENE))
        scene["kiosks"][0]["position"] = "upper-left"
        with self.assertRaises(iso_svg.GeometryError):
            iso_svg.layout(scene)

    def test_a_layout_this_renderer_cannot_draw_is_refused_by_name(self) -> None:
        scene = json.loads(json.dumps(SCENE))
        scene["layout"] = "radial"
        with self.assertRaises(iso_svg.GeometryError) as caught:
            iso_svg.layout(scene)
        self.assertIn("radial", str(caught.exception))


class RenderTests(unittest.TestCase):
    def test_every_billboard_command_is_drawn_as_text(self) -> None:
        svg = iso_svg.build(SCENE)
        for command in SCENE["billboards"].values():
            self.assertIn(f">{command}<", svg)

    def test_the_road_carries_the_id_the_gate_reads(self) -> None:
        self.assertIn('<polyline id="road"', iso_svg.build(SCENE))


if __name__ == "__main__":
    unittest.main()
