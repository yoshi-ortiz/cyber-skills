"""End-to-end contracts for the corpus-to-editorial-board workflow."""

from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

import editorial_workflow as ew


class BoardParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.script_count = 0
        self.column_count = 0
        self.text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        classes = (values.get("class") or "").split()
        if tag == "script":
            self.script_count += 1
        if tag == "section" and "column" in classes:
            self.column_count += 1

    def handle_data(self, data: str) -> None:
        value = data.strip()
        if value:
            self.text.append(value)


class EditorialWorkflowTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.project = root / "project"
        self.corpus = root / "corpus"
        self.project.mkdir()
        self.corpus.mkdir()
        (self.corpus / "reference.png").write_bytes(b"\x89PNG\r\n\x1a\nreference")
        (self.corpus / "brief.md").write_text(
            "# Field notes\nUse severe type, close crops, and visible revision marks.\n",
            encoding="utf-8",
        )
        self.corpus_packet = ew.observe_corpus(self.project, self.corpus)
        self.ids = {item["kind"]: item["id"] for item in self.corpus_packet["items"]}

    def direction(self, identifier: str, place: int) -> dict[str, object]:
        image = self.ids["image"]
        text = self.ids["text"]
        return {
            "id": identifier,
            "name": identifier.replace("-", " ").title(),
            "thesis": f"Use the corpus tension to make {identifier} unmistakable.",
            "signatureMove": f"A unique {identifier} crop interrupts the reading grid.",
            "evidence": [
                {
                    "corpusItem": image,
                    "locator": "full frame",
                    "observation": f"The image supports the {identifier} crop and hard edge.",
                },
                {
                    "corpusItem": text,
                    "locator": "Field notes, paragraph 1",
                    "observation": f"The brief names the {identifier} editorial pressure.",
                },
            ],
            "visualSystem": {
                "palette": "warm paper, black ink, signal red",
                "typography": "compressed display with a quiet text serif",
                "grid": "twelve columns with deliberate interruptions",
                "hierarchy": "one dominant statement per view",
                "imagery": "tight documentary crops",
                "voice": "direct, concrete, editorial",
                "motion": "cuts only when state changes",
            },
            "scorecard": {
                "corpusFit": 5 if place == 1 else 4,
                "subjectSpecificity": 5,
                "systemCoherence": 4,
                "distinctiveness": 5 - place + 1,
                "executionLeverage": 4,
            },
            "agentRank": {
                "place": place,
                "rationale": f"Rank {place} because its system turns corpus evidence into a coherent build.",
            },
        }

    def inference(self) -> dict[str, object]:
        return {
            "version": 1,
            "coverage": {"observed": list(self.ids.values()), "omitted": []},
            "directions": [
                self.direction("hard-crop", 1),
                self.direction("redline-ledger", 2),
                self.direction("quiet-index", 3),
            ],
            "selected": "hard-crop",
            "sprint": {
                "name": "Issue 01",
                "goal": "Turn the selected direction into one testable editorial page.",
                "items": [
                    {
                        "id": "hero-compose",
                        "direction": "hard-crop",
                        "title": "Compose the opening spread",
                        "deliverable": "A responsive opening spread with the hard crop in place.",
                        "points": 5,
                        "acceptance": [
                            {"check": "Desktop and narrow screenshots keep the headline readable.",
                             "evidenceKind": "screenshot"}
                        ],
                        "executionElement": "composition.hero",
                    },
                    {
                        "id": "type-lockup",
                        "direction": "hard-crop",
                        "title": "Lock the type hierarchy",
                        "deliverable": "A heading and deck pair with measured line lengths.",
                        "points": 3,
                        "acceptance": [
                            {"check": "The deck remains between 45 and 75 characters per line.",
                             "evidenceKind": "measurement"}
                        ],
                        "executionElement": "typography.hierarchy",
                    },
                ],
            },
        }

    def write_inference(self, value: dict[str, object] | None = None) -> Path:
        path = Path(self.temp.name) / "directions.json"
        path.write_text(json.dumps(value or self.inference()), encoding="utf-8")
        return path

    def test_observe_preserves_inspectable_text_and_image_material(self) -> None:
        self.assertEqual(self.corpus_packet["modalities"], ["image", "text"])
        image = next(item for item in self.corpus_packet["items"] if item["kind"] == "image")
        text = next(item for item in self.corpus_packet["items"] if item["kind"] == "text")
        self.assertEqual(Path(image["inspectPath"]), (self.corpus / "reference.png").resolve())
        self.assertIn("visible revision marks", text["textExcerpt"])
        self.assertEqual(Path(text["inspectPath"]), (self.corpus / "brief.md").resolve())

    def test_publish_is_grounded_bounded_and_keeps_user_stars_separate(self) -> None:
        ledger = self.project / "spec" / "design-harness" / "decisions.json"
        ledger.parent.mkdir(parents=True, exist_ok=True)
        ledger.write_text(json.dumps({"elements": [{
            "element": "composition.hero", "stars": 5, "source": "user",
            "scored": True, "state": "proposed", "sentiment": "like",
        }]}), encoding="utf-8")
        before = ledger.read_bytes()
        out = self.project / "design" / "editorial-board.html"

        ew.publish(self.project, self.write_inference(), out)

        markup = out.read_text(encoding="utf-8")
        parsed = BoardParser()
        parsed.feed(markup)
        rendered_text = " ".join(parsed.text)
        self.assertLess(len(markup.encode("utf-8")), 40_000)
        self.assertIn("Hard Crop", rendered_text)
        self.assertIn("8 points remaining", rendered_text)
        self.assertIn("User execution 5/5", rendered_text)
        self.assertIn("Agent rank 1", rendered_text)
        self.assertEqual(parsed.column_count, 4)
        self.assertEqual(parsed.script_count, 0)
        self.assertEqual(ledger.read_bytes(), before)
        stored = json.loads((ledger.parent / "art-direction.json").read_text(encoding="utf-8"))
        self.assertNotIn("stars", json.dumps(stored))

    def test_advance_reduces_remaining_points_and_duplicate_event_is_a_no_op(self) -> None:
        out = self.project / "design" / "editorial-board.html"
        ew.publish(self.project, self.write_inference(), out)

        ew.advance(self.project, "hero-compose", "done", "hero-done-1", "2026-08-20T12:00:00Z")
        events = self.project / "spec" / "design-harness" / "editorial-events.jsonl"
        first = events.read_bytes()
        ew.advance(self.project, "hero-compose", "done", "hero-done-1", "2026-08-20T12:00:00Z")

        self.assertEqual(events.read_bytes(), first)
        ew.render_project(self.project, out)
        markup = out.read_text(encoding="utf-8")
        parsed = BoardParser()
        parsed.feed(markup)
        rendered_text = " ".join(parsed.text)
        self.assertIn("3 points remaining", rendered_text)
        self.assertIn("1 of 2 done", rendered_text)
        self.assertRegex(rendered_text, r'Done.*Compose the opening spread')

    def test_publish_fails_closed_when_selected_direction_ignores_text(self) -> None:
        inference = self.inference()
        selected = inference["directions"][0]
        selected["evidence"] = [selected["evidence"][0]]
        out = self.project / "design" / "editorial-board.html"

        with self.assertRaisesRegex(ew.WorkflowError, "selected direction.*text"):
            ew.publish(self.project, self.write_inference(inference), out)

        self.assertFalse(out.exists())
        self.assertFalse((self.project / "spec" / "design-harness" / "art-direction.json").exists())

    def test_publish_rejects_invalid_work_and_rankings_without_mutation(self) -> None:
        cases = []
        empty_work = self.inference()
        empty_work["sprint"]["items"] = []
        cases.append(empty_work)
        duplicate_rank = self.inference()
        duplicate_rank["directions"][1]["agentRank"]["place"] = 1
        cases.append(duplicate_rank)
        invented_evidence = self.inference()
        invented_evidence["directions"][2]["evidence"][0]["corpusItem"] = "missing-item"
        cases.append(invented_evidence)

        for index, inference in enumerate(cases):
            out = self.project / "design" / f"invalid-{index}.html"
            with self.assertRaises(ew.WorkflowError):
                ew.publish(self.project, self.write_inference(inference), out)
            self.assertFalse(out.exists())


class CompanionRankStateTest(unittest.TestCase):
    def test_zero_control_is_only_on_for_zero_stars(self) -> None:
        helper = Path(__file__).parents[1] / "companion" / "helper.js"
        script = (
            f"const h=require({json.dumps(str(helper))});"
            "if(!h.rankIsOn(0,0)||h.rankIsOn(0,5)||!h.rankIsOn(5,5))process.exit(1);"
        )
        completed = subprocess.run(["node", "-e", script], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
