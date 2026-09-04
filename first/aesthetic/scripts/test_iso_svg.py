#!/usr/bin/env python3
import json
import unittest
from pathlib import Path

import iso_svg

SCENE = json.loads((Path(__file__).resolve().parents[3]
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


class CorpusPaletteTests(unittest.TestCase):
    """Colour comes from the corpus, or the render admits it did not."""

    # Seven colours for seven requests: four rooms, the road, two kiosks. With
    # fewer, a reuse is unavoidable and `snap_palette` is right to reuse.
    EVIDENCE = {"palette": ["#ffffff", "#128fd1", "#009a44", "#ffdf00",
                            "#c1e5e3", "#d4875b", "#ff6918"],
                "paper": "#fffeef", "ink": "#000000"}

    def test_without_evidence_the_render_says_so(self) -> None:
        plan = iso_svg.layout(SCENE)
        self.assertEqual(plan["paletteSource"], "unevidenced-constants")
        self.assertEqual(plan["paper"], iso_svg.BACKGROUND)

    def test_every_fill_comes_from_the_measured_palette(self) -> None:
        plan = iso_svg.layout(SCENE, self.EVIDENCE)
        self.assertEqual(plan["paletteSource"], "corpus")
        for box in plan["boxes"]:
            self.assertIn(box["fill"], self.EVIDENCE["palette"])
        self.assertEqual(plan["paper"], "#fffeef")
        self.assertEqual(plan["ink"], "#000000")

    def test_no_material_default_survives_into_the_drawing(self) -> None:
        """The bug this exists to stop: #00bcd4 was never in any reference."""
        svg = iso_svg.build(SCENE, self.EVIDENCE)
        for invented in set(iso_svg.PALETTE_FILL.values()) | {iso_svg.ROAD_STROKE}:
            self.assertNotIn(invented, svg)

    def test_two_spaces_do_not_collapse_into_one_fill(self) -> None:
        plan = iso_svg.layout(SCENE, self.EVIDENCE)
        fills = [box["fill"] for box in plan["boxes"]]
        self.assertEqual(len(fills), len(set(fills)))

    def test_main_rooms_pick_before_ghost_kiosks(self) -> None:
        """A near-white kiosk used to take the pale cyan the cyan room wanted."""
        plan = iso_svg.layout(SCENE, self.EVIDENCE)
        rooms = {room["id"] for room in SCENE["mainRooms"]}
        first = next(box for box in plan["boxes"] if box["id"] in rooms)
        self.assertEqual(first["fill"], "#128fd1")

    def test_a_hue_the_corpus_lacks_is_reported_not_hidden(self) -> None:
        plan = iso_svg.layout(SCENE, {"palette": ["#ffffff", "#000000"]})
        wanted = {gap["requested"] for gap in plan["paletteGaps"]}
        self.assertIn(iso_svg.PALETTE_FILL["magenta"], wanted)
        for gap in plan["paletteGaps"]:
            self.assertGreater(gap["distance"], iso_svg.HUE_GAP)

    def test_an_evidenced_hue_is_not_reported_as_a_gap(self) -> None:
        exact = sorted(set(iso_svg.PALETTE_FILL.values()) | {iso_svg.ROAD_STROKE})
        plan = iso_svg.layout(SCENE, {"palette": exact})
        self.assertEqual(plan["paletteGaps"], [])

    def test_snapping_is_stable_across_runs(self) -> None:
        once = iso_svg.snap_palette(["#00bcd4", "#e91e63"], self.EVIDENCE["palette"])
        twice = iso_svg.snap_palette(["#00bcd4", "#e91e63"], self.EVIDENCE["palette"])
        self.assertEqual(once, twice)

    def test_more_hues_than_evidence_reuses_rather_than_inventing(self) -> None:
        resolved = iso_svg.snap_palette(["#00bcd4", "#e91e63", "#1565c0"], ["#123456"])
        self.assertEqual(set(resolved.values()), {"#123456"})


if __name__ == "__main__":
    unittest.main()
