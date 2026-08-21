"""Contracts for sentiment inference, hierarchical burndown, and safe themes."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import bootstrap_harness as bh
import editorial_workflow as ew
from asset_contract import AssetError, validate_assets


def decision(element: str, stars: int = 0, sentiment: str | None = None,
             *, scored: bool = True, source: str = "user", state: str = "proposed") -> dict:
    return {
        "element": element, "stars": stars, "sentiment": sentiment,
        "scored": scored, "source": source, "state": state,
        "preview": None, "evidence": "user feedback",
    }


class PerElementPreferencePolicyTest(unittest.TestCase):
    def test_each_signal_pair_keeps_its_distinct_instruction(self) -> None:
        values = [
            decision("anchor", 5, "like"),
            decision("polish", 1, "like"),
            decision("conflict", 5, "dislike"),
            decision("discard", 1, "dislike"),
            decision("liked-direction", 0, "like", scored=False, source="agent"),
            decision("explore", 0, None, scored=False, source="agent"),
        ]
        brief = ew.preference_brief({"elements": values})
        states = {item["element"]: item["preferenceState"] for item in brief["elements"]}
        self.assertEqual(states, {
            "anchor": "anchor",
            "polish": "polish",
            "conflict": "conflict",
            "discard": "discard",
            "liked-direction": "direction-like",
            "explore": "explore",
        })
        self.assertNotIn("reward", json.dumps(brief).lower())
        self.assertNotIn("average", json.dumps(brief).lower())

    def test_sentiment_only_feedback_does_not_increase_rank_coverage(self) -> None:
        decisions = {"elements": [
            decision("core.idea", 0, "like", scored=False, source="agent"),
        ]}
        stats = bh.ledger_stats(decisions)
        self.assertEqual(stats["userSet"], 0)
        self.assertEqual(stats["coverage"], 0)


class ArtDirectionInferenceContractTest(unittest.TestCase):
    def corpus(self) -> dict:
        return {"items": [
            {"id": "image-a", "kind": "image"},
            {"id": "text-a", "kind": "text"},
        ]}

    def preferences(self) -> dict:
        return {"coverage": {"userRanked": 2, "elements": 3, "fraction": 2 / 3},
                "elements": [{"element": name} for name in
                             ("composition.hero", "type.display", "nav.utility")]}

    def spec(self) -> dict:
        return {
            "version": 1,
            "observations": [
                {"corpusItem": "image-a", "locator": "upper crop",
                 "observation": "The crop withholds the subject edge."},
                {"corpusItem": "text-a", "locator": "paragraph 2",
                 "observation": "Revision is part of the finished voice."},
            ],
            "preferencePatterns": [{
                "claim": "The user favors type crossing image boundaries.",
                "support": ["composition.hero", "type.display"],
                "counterevidence": ["nav.utility"], "n": 3,
                "coverage": 0.67, "confidence": "medium",
            }],
            "hypotheses": [
                {"id": "hard-crop", "thesis": "Revision stays visibly unfinished.",
                 "signatureMove": "Hard crops cross a fixed annotation rail.",
                 "visualSystem": {key: key + " rule" for key in
                    ("palette", "typography", "grid", "hierarchy", "imagery", "voice", "motion")}},
                {"id": "open-index", "thesis": "Evidence accumulates in an open index.",
                 "signatureMove": "Captions form the primary reading rail.",
                 "visualSystem": {key: key + " rule" for key in
                    ("palette", "typography", "grid", "hierarchy", "imagery", "voice", "motion")}},
            ],
            "comparison": [{"hypothesis": name, "corpusFit": 4, "preferenceFit": 4,
                            "subjectSpecificity": 4, "coherence": 4,
                            "executionLeverage": 4, "tradeoff": "observable tradeoff"}
                           for name in ("hard-crop", "open-index")],
            "selected": "hard-crop",
            "selectionRationale": "The crop is supported by both modalities; the index is safer but less specific.",
            "cohort": ["composition.hero", "type.display", "nav.utility"],
        }

    def test_validates_grounded_noncollapsed_inference(self) -> None:
        result = ew.validate_art_direction(self.spec(), self.corpus(), self.preferences())
        self.assertEqual(result["selected"], "hard-crop")
        self.assertNotIn("score", result)
        self.assertNotIn("reward", json.dumps(result).lower())

    def test_rejects_invented_evidence_and_vague_patterns(self) -> None:
        broken = self.spec()
        broken["observations"][0]["corpusItem"] = "invented"
        with self.assertRaisesRegex(ew.WorkflowError, "unknown corpus item"):
            ew.validate_art_direction(broken, self.corpus(), self.preferences())
        broken = self.spec()
        broken["preferencePatterns"][0]["claim"] = "The user likes clean premium design."
        with self.assertRaisesRegex(ew.WorkflowError, "observable"):
            ew.validate_art_direction(broken, self.corpus(), self.preferences())

    def test_rejects_averaged_or_incomplete_comparison(self) -> None:
        broken = self.spec()
        broken["comparison"][0]["average"] = 4
        with self.assertRaisesRegex(ew.WorkflowError, "average"):
            ew.validate_art_direction(broken, self.corpus(), self.preferences())

    def test_rejects_generated_from_memory_vectors(self) -> None:
        with self.assertRaisesRegex(AssetError, "generated-from-memory"):
            validate_assets([{"id": "ornament", "provenance": "generated-from-memory",
                              "path": "ornament.svg"}], {"image-a"})


class EditorialBurndownTest(unittest.TestCase):
    def spec(self) -> dict:
        return {
            "version": 1,
            "baselineAt": "2026-08-20T12:00:00Z",
            "epics": [
                {"id": "identity", "title": "Identity", "critical": True},
                {"id": "deployment", "title": "Deployment", "critical": False},
            ],
            "elements": {
                "core.thesis": "identity",
                "typography.pixel-face": "identity",
                "release.production": "deployment",
            },
        }

    def test_burndown_tracks_epics_and_elements_as_separate_series(self) -> None:
        events = [
            {"eventId": "type-done", "at": "2026-08-20T13:00:00Z",
             "kind": "element", "id": "typography.pixel-face", "to": "resolved"},
            {"eventId": "identity-done", "at": "2026-08-20T14:00:00Z",
             "kind": "epic", "id": "identity", "to": "resolved"},
        ]
        result = ew.editorial_burndown(self.spec(), events)
        self.assertEqual(result["points"], [
            {"at": "2026-08-20T12:00:00Z", "unresolvedEpics": 2, "unresolvedElements": 3},
            {"at": "2026-08-20T13:00:00Z", "unresolvedEpics": 2, "unresolvedElements": 2},
            {"at": "2026-08-20T14:00:00Z", "unresolvedEpics": 1, "unresolvedElements": 2},
        ])
        self.assertEqual(result["criticalEpics"], ["identity"])

    def test_every_element_has_exactly_one_primary_epic(self) -> None:
        broken = self.spec()
        broken["elements"]["core.thesis"] = ["identity", "deployment"]
        with self.assertRaisesRegex(ew.WorkflowError, "one primary epic"):
            ew.validate_editorial_spec(broken)

    def test_duplicate_scope_event_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ew.save_editorial_spec(root, self.spec())
            event = {"eventId": "type-done", "at": "2026-08-20T13:00:00Z",
                     "kind": "element", "id": "typography.pixel-face", "to": "resolved"}
            self.assertTrue(ew.append_scope_event(root, event))
            before = (root / ew.STORE / ew.EVENTS_FILE).read_bytes()
            self.assertFalse(ew.append_scope_event(root, event))
            self.assertEqual((root / ew.STORE / ew.EVENTS_FILE).read_bytes(), before)


class ElementLevelThemeSafetyTest(unittest.TestCase):
    def safe(self) -> dict:
        return {
            "bg": "#ffffff", "ink": "#111111", "accent": "#005fcc",
            "font": "system-ui, sans-serif",
        }

    def test_white_text_is_rejected_without_discarding_safe_theme_elements(self) -> None:
        candidate = dict(self.safe(), ink="#ffffff", accent="#8b0000")
        result = ew.validate_theme_elements(candidate, self.safe())
        self.assertEqual(result["active"]["bg"], "#ffffff")
        self.assertEqual(result["active"]["accent"], "#8b0000")
        self.assertEqual(result["active"]["ink"], "#111111")
        self.assertEqual(result["errors"][0]["element"], "ink")
        self.assertLess(result["errors"][0]["contrast"], 4.5)

    def test_save_current_and_save_as_new_preserve_safe_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = ew.save_theme(root, "current", "newsprint", self.safe(), "Newsprint")
            self.assertEqual(first["selected"], "newsprint")
            second = ew.save_theme(root, "new", "night-proof", {
                "bg": "#111111", "ink": "#ffffff", "accent": "#73d2ff",
                "font": "system-ui, sans-serif",
            }, "Night proof")
            self.assertEqual(second["selected"], "night-proof")
            self.assertEqual({theme["id"] for theme in second["themes"]},
                             {"newsprint", "night-proof"})


class OriginalArticleWithBurndownTest(unittest.TestCase):
    def test_article_keeps_original_sections_and_adds_burndown_after_hero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "spec" / "design-harness").mkdir(parents=True)
            bh.write_json(root / "spec" / "design-harness" / "project.json",
                          {"version": bh.VERSION, "state": "draft", "title": "Demo"})
            ew.save_editorial_spec(root, EditorialBurndownTest().spec())
            decisions = {"elements": [
                decision("core.thesis", 5, "like"),
                decision("composition.hero", 2, None),
                decision("composition.secondary", 2, None),
                decision("voice.rejected", 1, "dislike", state="rejected"),
            ]}
            markup = bh.render_article(root, decisions, {"composition.hero"}, "Hero", "en")
            order = [markup.index(fragment) for fragment in (
                'class="dh-hero"',
                'class="dh-burndown"',
                'class="dh-toc"',
                'id="dh-zone-round"',
                'id="dh-zone-fundamentals"',
                'id="dh-zone-backlog"',
                'id="dh-zone-antipattern"',
            )]
            self.assertEqual(order, sorted(order))
            self.assertIn("2 unresolved epics", markup)
            self.assertIn("3 unresolved elements", markup)


if __name__ == "__main__":
    unittest.main()
