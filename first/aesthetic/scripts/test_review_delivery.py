"""Contracts for final-chat review image delivery."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import review_delivery as rd


class ReviewDeliveryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.output = self.root / "spec" / "design-harness"
        self.output.mkdir(parents=True)
        (self.root / "content").mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def comp(self, element: str, body: str | None = None) -> Path:
        path = self.root / "content" / f"{element}.html"
        path.write_text(body or f"<html><body>{element}</body></html>", encoding="utf-8")
        return path

    def decisions(self, entries: list[tuple[str, Path, str | None]]) -> None:
        elements = []
        for element, path, digest in entries:
            elements.append({
                "element": element,
                "state": "proposed",
                "preview": {
                    "path": path.relative_to(self.root).as_posix(),
                    "sha256": digest if digest is not None else rd.sha256_file(path),
                },
            })
        (self.output / "decisions.json").write_text(json.dumps({"elements": elements}),
                                                     encoding="utf-8")

    def assessment(self, element: str, **changes: bool) -> dict[str, object]:
        value: dict[str, object] = {
            "element": element,
            "rankable_design": True,
            "subject_specific": True,
            "signature_legible": True,
            "explanatory_only": False,
            "generic_default": False,
        }
        value.update(changes)
        return value

    def assessments_file(self, values: list[dict[str, object]]) -> Path:
        path = self.root / "assessments.json"
        path.write_text(json.dumps({"assessments": values}), encoding="utf-8")
        return path

    def test_review_image_rejects_relative_paths(self) -> None:
        with self.assertRaises(rd.DeliveryError):
            rd.ReviewImage("cover", Path("content/cover.html"), "a" * 64,
                           Path("design/review/cover.png"), "b" * 64)

    def test_missing_canonical_html_is_rejected(self) -> None:
        missing = self.root / "content" / "missing.html"
        self.decisions([("cover", missing, "a" * 64)])

        with self.assertRaisesRegex(rd.DeliveryError, "does not exist"):
            rd.resolve_canonical_previews(self.root, ["cover"])

    def test_source_hash_mismatch_is_rejected_before_render(self) -> None:
        comp = self.comp("cover")
        self.decisions([("cover", comp, "0" * 64)])
        called = False

        def renderer(source: Path, target: Path) -> str:
            nonlocal called
            called = True
            return "fake"

        with self.assertRaisesRegex(rd.DeliveryError, "hash"):
            rd.deliver_review_images(
                self.root, ["cover"],
                self.assessments_file([self.assessment("cover")]), renderer=renderer)
        self.assertFalse(called)

    def test_duplicate_canonical_previews_are_rejected(self) -> None:
        first = self.comp("cover-a", "<html><body>same</body></html>")
        second = self.comp("cover-b", "<html><body>same</body></html>")
        self.decisions([("cover-a", first, None), ("cover-b", second, None)])

        with self.assertRaisesRegex(rd.DeliveryError, "duplicate"):
            rd.resolve_canonical_previews(self.root, ["cover-a", "cover-b"])

    def test_missing_or_failing_assessments_are_rejected(self) -> None:
        comp = self.comp("cover")
        self.decisions([("cover", comp, None)])
        failures = (
            {},
            {"rankable_design": False},
            {"subject_specific": False},
            {"signature_legible": False},
            {"explanatory_only": True},
            {"generic_default": True},
        )
        for changes in failures:
            with self.subTest(changes=changes):
                values = [] if not changes else [self.assessment("cover", **changes)]
                path = self.assessments_file(values)
                with self.assertRaises(rd.DeliveryError):
                    rd.deliver_review_images(self.root, ["cover"], path,
                                             renderer=lambda *_: "fake")

    def test_delivery_emits_only_absolute_existing_paths(self) -> None:
        first = self.comp("cover-a")
        second = self.comp("cover-b")
        self.decisions([("cover-a", first, None), ("cover-b", second, None)])
        assessments = self.assessments_file([
            self.assessment("cover-a"), self.assessment("cover-b")])

        def renderer(source: Path, target: Path) -> str:
            target.write_bytes(b"\x89PNG\r\n\x1a\n" + source.read_bytes())
            return "fake"

        images = rd.deliver_review_images(
            self.root, ["cover-a", "cover-b"], assessments, renderer=renderer)
        payload = rd.delivery_payload(images)

        self.assertEqual([item["element"] for item in payload["images"]],
                         ["cover-a", "cover-b"])
        for item in payload["images"]:
            for key in ("source_html", "image_path"):
                path = Path(item[key])
                self.assertTrue(path.is_absolute())
                self.assertTrue(path.is_file())
            self.assertEqual(item["source_sha256"], rd.sha256_file(Path(item["source_html"])))
            self.assertEqual(item["image_sha256"], rd.sha256_file(Path(item["image_path"])))

    def test_late_render_failure_does_not_partially_publish_the_cohort(self) -> None:
        first = self.comp("cover-a")
        second = self.comp("cover-b")
        self.decisions([("cover-a", first, None), ("cover-b", second, None)])
        assessments = self.assessments_file([
            self.assessment("cover-a"), self.assessment("cover-b")])
        review_dir = self.root / "design" / "review"
        review_dir.mkdir(parents=True)
        existing = review_dir / "cover-a.png"
        existing.write_bytes(b"prior accepted review")

        def renderer(source: Path, target: Path) -> str:
            if source == second:
                raise OSError("late renderer failure")
            target.write_bytes(b"replacement review")
            return "fake"

        with self.assertRaisesRegex(rd.DeliveryError, "late renderer failure"):
            rd.deliver_review_images(
                self.root, ["cover-a", "cover-b"], assessments, renderer=renderer)

        self.assertEqual(existing.read_bytes(), b"prior accepted review")
        self.assertFalse((review_dir / "cover-b.png").exists())
        self.assertEqual([], list(review_dir.glob(".review-stage-*")))

    def test_late_publish_failure_rolls_back_the_whole_cohort(self) -> None:
        first = self.comp("cover-a")
        second = self.comp("cover-b")
        self.decisions([("cover-a", first, None), ("cover-b", second, None)])
        assessments = self.assessments_file([
            self.assessment("cover-a"), self.assessment("cover-b")])
        review_dir = self.root / "design" / "review"
        review_dir.mkdir(parents=True)
        first_target = review_dir / "cover-a.png"
        second_target = review_dir / "cover-b.png"
        first_target.write_bytes(b"old-first")
        second_target.write_bytes(b"old-second")

        def renderer(source: Path, target: Path) -> str:
            target.write_bytes(b"new-" + source.name.encode())
            return "fake"

        calls = 0

        def publisher(source: Path, target: Path) -> None:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("late publish failure")
            source.replace(target)

        with self.assertRaisesRegex(rd.DeliveryError, "publish"):
            rd.deliver_review_images(
                self.root, ["cover-a", "cover-b"], assessments,
                renderer=renderer, publisher=publisher)

        self.assertEqual(first_target.read_bytes(), b"old-first")
        self.assertEqual(second_target.read_bytes(), b"old-second")
        self.assertEqual([], list(review_dir.glob(".review-stage-*")))


if __name__ == "__main__":
    unittest.main()
