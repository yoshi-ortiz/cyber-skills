#!/usr/bin/env python3
"""Render hash-pinned, assessed proposal images for final-chat review."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from bootstrap_harness import HarnessError, render_html_preview, sha256_file


class DeliveryError(RuntimeError):
    """The review image contract was not satisfied."""


def _valid_digest(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-f]{64}", value))


@dataclass(frozen=True)
class CanonicalPreview:
    element: str
    html_path: Path
    html_sha256: str

    def __post_init__(self) -> None:
        if not self.element:
            raise DeliveryError("canonical preview element is empty")
        if not self.html_path.is_absolute():
            raise DeliveryError(f"canonical HTML path for {self.element} must be absolute")
        if not self.html_path.is_file():
            raise DeliveryError(f"canonical HTML for {self.element} does not exist: {self.html_path}")
        if self.html_path.suffix.lower() != ".html":
            raise DeliveryError(f"canonical preview for {self.element} must be HTML")
        if not _valid_digest(self.html_sha256):
            raise DeliveryError(f"canonical HTML hash for {self.element} is invalid")


@dataclass(frozen=True)
class ProposalAssessment:
    element: str
    rankable_design: bool
    subject_specific: bool
    signature_legible: bool
    explanatory_only: bool
    generic_default: bool

    def __post_init__(self) -> None:
        if not self.element:
            raise DeliveryError("proposal assessment element is empty")
        for field in (
            "rankable_design", "subject_specific", "signature_legible",
            "explanatory_only", "generic_default",
        ):
            if type(getattr(self, field)) is not bool:
                raise DeliveryError(f"assessment {self.element}.{field} must be boolean")

    @property
    def passes(self) -> bool:
        return (self.rankable_design and self.subject_specific and self.signature_legible
                and not self.explanatory_only and not self.generic_default)


@dataclass(frozen=True)
class ReviewImage:
    element: str
    source_html: Path
    source_sha256: str
    image_path: Path
    image_sha256: str

    def __post_init__(self) -> None:
        for label, path in (("source HTML", self.source_html), ("review image", self.image_path)):
            if not path.is_absolute():
                raise DeliveryError(f"{label} path for {self.element} must be absolute")
            if not path.is_file():
                raise DeliveryError(f"{label} for {self.element} does not exist: {path}")
        if sha256_file(self.source_html) != self.source_sha256:
            raise DeliveryError(f"source HTML hash changed for {self.element}")
        if sha256_file(self.image_path) != self.image_sha256:
            raise DeliveryError(f"review image hash changed for {self.element}")


Renderer = Callable[[Path, Path], str]
Publisher = Callable[[Path, Path], None]


def _replace(source: Path, target: Path) -> None:
    source.replace(target)


def _load_object(path: Path, label: str) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise DeliveryError(f"{label} does not exist: {path}") from error
    except json.JSONDecodeError as error:
        raise DeliveryError(f"{label} is not valid JSON: {error}") from error
    if not isinstance(value, Mapping):
        raise DeliveryError(f"{label} must be a JSON object")
    return value


def resolve_canonical_previews(project_root: Path,
                               cohort: Iterable[str]) -> list[CanonicalPreview]:
    root = project_root.resolve(strict=True)
    elements = list(cohort)
    if not elements:
        raise DeliveryError("cohort is empty")
    if len(elements) != len(set(elements)):
        raise DeliveryError("cohort contains duplicate element ids")
    ledger_path = root / "spec" / "design-harness" / "decisions.json"
    ledger = _load_object(ledger_path, "decisions.json")
    raw_elements = ledger.get("elements")
    if not isinstance(raw_elements, list):
        raise DeliveryError("decisions.json elements must be a list")
    by_id: dict[str, Mapping[str, Any]] = {}
    for raw in raw_elements:
        if not isinstance(raw, Mapping) or not isinstance(raw.get("element"), str):
            raise DeliveryError("decisions.json contains an invalid element")
        element = raw["element"]
        if element in by_id:
            raise DeliveryError(f"decisions.json contains duplicate element {element}")
        by_id[element] = raw

    previews: list[CanonicalPreview] = []
    seen_hashes: dict[str, str] = {}
    for element in elements:
        entry = by_id.get(element)
        if entry is None:
            raise DeliveryError(f"cohort element is missing from decisions.json: {element}")
        preview = entry.get("preview")
        if not isinstance(preview, Mapping):
            raise DeliveryError(f"canonical preview is missing for {element}")
        raw_path = preview.get("path")
        digest = preview.get("sha256")
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise DeliveryError(f"canonical HTML path is missing for {element}")
        if not isinstance(digest, str):
            raise DeliveryError(f"canonical HTML hash is missing for {element}")
        candidate = Path(raw_path)
        resolved = (candidate if candidate.is_absolute() else root / candidate).resolve(strict=False)
        if not resolved.is_relative_to(root):
            raise DeliveryError(f"canonical HTML for {element} is outside the project")
        canonical = CanonicalPreview(element, resolved, digest)
        actual = sha256_file(canonical.html_path)
        if actual != canonical.html_sha256:
            raise DeliveryError(
                f"canonical HTML hash mismatch for {element}: expected "
                f"{canonical.html_sha256}, got {actual}")
        duplicate = seen_hashes.get(actual)
        if duplicate is not None:
            raise DeliveryError(
                f"duplicate canonical preview hash for {duplicate} and {element}")
        seen_hashes[actual] = element
        previews.append(canonical)
    return previews


def load_passing_assessments(path: Path,
                             cohort: Sequence[str]) -> dict[str, ProposalAssessment]:
    value = _load_object(path.resolve(strict=False), "assessment JSON")
    raw_assessments = value.get("assessments")
    if not isinstance(raw_assessments, list):
        raise DeliveryError("assessment JSON must contain an assessments list")
    assessments: dict[str, ProposalAssessment] = {}
    expected_keys = {
        "element", "rankable_design", "subject_specific", "signature_legible",
        "explanatory_only", "generic_default",
    }
    for raw in raw_assessments:
        if not isinstance(raw, Mapping) or set(raw) != expected_keys:
            raise DeliveryError("each proposal assessment must contain the six required fields")
        assessment = ProposalAssessment(**raw)
        if assessment.element in assessments:
            raise DeliveryError(f"duplicate assessment for {assessment.element}")
        assessments[assessment.element] = assessment
    expected = set(cohort)
    missing = expected - assessments.keys()
    extra = assessments.keys() - expected
    if missing:
        raise DeliveryError("missing assessment for: " + ", ".join(sorted(missing)))
    if extra:
        raise DeliveryError("assessment includes elements outside the cohort: "
                            + ", ".join(sorted(extra)))
    failed = [element for element in cohort if not assessments[element].passes]
    if failed:
        raise DeliveryError("proposal assessment failed for: " + ", ".join(failed))
    return assessments


def _image_name(element: str) -> str:
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", element).strip(".-")
    if not name:
        raise DeliveryError(f"element cannot form a review image name: {element!r}")
    return f"{name}.png"


def deliver_review_images(project_root: Path, cohort: Iterable[str], assessments_path: Path,
                          renderer: Renderer = render_html_preview,
                          publisher: Publisher = _replace) -> list[ReviewImage]:
    root = project_root.resolve(strict=True)
    elements = list(cohort)
    previews = resolve_canonical_previews(root, elements)
    load_passing_assessments(assessments_path, elements)
    review_dir = root / "design" / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    names = [_image_name(preview.element) for preview in previews]
    if len(names) != len(set(names)):
        raise DeliveryError("cohort element ids collide as review image names")

    staged_images: list[tuple[CanonicalPreview, Path, Path, str]] = []
    rendered_hashes: dict[str, str] = {}
    with tempfile.TemporaryDirectory(prefix=".review-stage-", dir=review_dir) as staging:
        staging_dir = Path(staging)
        for preview, name in zip(previews, names, strict=True):
            staged = staging_dir / name
            try:
                renderer(preview.html_path, staged)
                if not staged.is_file() or not staged.stat().st_size:
                    raise DeliveryError(f"renderer produced no image for {preview.element}")
                image_digest = sha256_file(staged)
            except (HarnessError, OSError) as error:
                raise DeliveryError(
                    f"could not render review image for {preview.element}: {error}") from error
            duplicate = rendered_hashes.get(image_digest)
            if duplicate is not None:
                raise DeliveryError(
                    f"duplicate rendered review image for {duplicate} and {preview.element}")
            rendered_hashes[image_digest] = preview.element
            staged_images.append(
                (preview, staged, (review_dir / name).resolve(), image_digest))

        for preview, _, _, _ in staged_images:
            if sha256_file(preview.html_path) != preview.html_sha256:
                raise DeliveryError(f"canonical HTML changed while rendering {preview.element}")

        backups: dict[Path, Path | None] = {}
        published: list[Path] = []
        try:
            for index, (_, _, target, _) in enumerate(staged_images):
                if target.is_file():
                    backup = staging_dir / f".backup-{index}.png"
                    shutil.copy2(target, backup)
                    backups[target] = backup
                else:
                    backups[target] = None
            for _, staged, target, _ in staged_images:
                publisher(staged, target)
                published.append(target)
        except OSError as error:
            for target in reversed(published):
                backup = backups[target]
                if backup is None:
                    target.unlink(missing_ok=True)
                else:
                    backup.replace(target)
            raise DeliveryError(f"could not publish the review cohort: {error}") from error

    return [
        ReviewImage(preview.element, preview.html_path, preview.html_sha256, target, digest)
        for preview, _, target, digest in staged_images
    ]


def delivery_payload(images: Sequence[ReviewImage]) -> dict[str, list[dict[str, str]]]:
    return {
        "images": [
            {
                "element": image.element,
                "source_html": str(image.source_html),
                "source_sha256": image.source_sha256,
                "image_path": str(image.image_path),
                "image_sha256": image.image_sha256,
            }
            for image in images
        ]
    }


def _cohort(values: Sequence[str]) -> list[str]:
    return [element.strip() for value in values for element in value.split(",") if element.strip()]


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(
        description="Render assessed canonical HTML proposals as absolute review images.")
    command.add_argument("--project-root", required=True, type=Path)
    command.add_argument("--cohort", required=True, action="append",
                         help="comma-separated decisions.json element ids; repeatable")
    command.add_argument("--assessments", required=True, type=Path,
                         help="JSON object containing explicit proposal assessments")
    command.add_argument("--out", type=Path,
                         help="optional path for the emitted review image JSON")
    return command


def main() -> int:
    args = parser().parse_args()
    try:
        images = deliver_review_images(
            args.project_root, _cohort(args.cohort), args.assessments)
        payload = delivery_payload(images)
        encoded = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(encoded, encoding="utf-8")
        print(encoded, end="")
        return 0
    except DeliveryError as error:
        parser().error(str(error))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
