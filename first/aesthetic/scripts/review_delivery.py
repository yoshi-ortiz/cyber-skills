#!/usr/bin/env python3
"""Render hash-pinned, assessed proposal images for final-chat review."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from bootstrap_harness import (HarnessError, find_chrome, render_html_preview,
                               sha256_file)
from graphics_flow import PROOF_KIND


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
    # Scoped to graphic proposals: an illustration that only reads at display
    # size is not the illustration that ships. Every rejected character round
    # in this project looked fine at 200px and unreadable at 54px, which is
    # the size the diagram actually uses.
    shown_at_delivery_size: bool

    def __post_init__(self) -> None:
        if not self.element:
            raise DeliveryError("proposal assessment element is empty")
        for field in (
            "rankable_design", "subject_specific", "signature_legible",
            "explanatory_only", "generic_default", "shown_at_delivery_size",
        ):
            if type(getattr(self, field)) is not bool:
                raise DeliveryError(f"assessment {self.element}.{field} must be boolean")

    @property
    def passes(self) -> bool:
        return (self.rankable_design and self.subject_specific and self.signature_legible
                and self.shown_at_delivery_size
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
        "explanatory_only", "generic_default", "shown_at_delivery_size",
    }
    for raw in raw_assessments:
        if not isinstance(raw, Mapping) or set(raw) != expected_keys:
            raise DeliveryError("each proposal assessment must contain the seven required fields")
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


# A review image is not a thumbnail. It is opened at full size in the reply and
# it is the ONLY view of the work a user gets without visiting the companion, so
# it has to show the design.
#
# It used to inherit `render_html_preview`'s default width, `PREVIEW_WIDTH` --
# 510px, which is a phone. Every comp that is a real page therefore shipped its
# MOBILE rendering: on the landing hero, 510px put the headline and the two
# buttons in frame and pushed the isometric rail, the four rooms and every
# station label -- the entire subject of the round -- below the fold. The user
# was asked to rank a graphic that was not in the picture.
#
# 1280 is a desktop viewport, so a page comp renders the layout it was drawn
# for. A comp authored small still reads: it is centred in a wider frame rather
# than cropped by a narrower one, and being surrounded by white is recoverable
# in a way that being cut in half is not.
REVIEW_WIDTH = 1280


def _render_review(html: Path, out: Path) -> str:
    return render_html_preview(html, out, width=REVIEW_WIDTH)


# A proof key pins FOUR things: the artifact's bytes, the viewport it was seen
# at, the renderer that drew it, and which kind of view this is.
#
# The interface this came from named a fifth, `assets_hash`, and it is dropped
# on purpose. A comp here is self-contained -- design/landing-flow-hero.html
# carries no <link>, no @import and no remote src -- so every byte an asset
# hash would cover is already inside the file `artifact_hash` hashes. A fifth
# input fed from the same bytes is one more place to be wrong, not one more
# thing proven. Do not add it back until an artifact genuinely references
# something outside itself; then it has a source, and only then.
def proof_key(artifact_hash: str, viewport: str, renderer_version: str,
              kind: str) -> str:
    return hashlib.sha256("\x1f".join(
        (artifact_hash, str(viewport), renderer_version, kind)).encode()).hexdigest()


_RENDERER_VERSION: str | None = None


def renderer_version() -> str:
    """What the rasteriser says it is, cached for the process.

    Asked of the binary, never guessed. A proof recorded under an invented
    version is worse than no proof at all: it claims a render some other
    build produced. When the binary will not answer, its name stands in --
    that is still something observed rather than something made up.
    """
    global _RENDERER_VERSION
    if _RENDERER_VERSION is not None:
        return _RENDERER_VERSION
    chrome = find_chrome()
    if not chrome:
        _RENDERER_VERSION = "no renderer"
        return _RENDERER_VERSION
    try:
        done = subprocess.run([chrome, "--version"], capture_output=True,
                              text=True, timeout=10)
        _RENDERER_VERSION = done.stdout.strip() or Path(chrome).name
    except (OSError, subprocess.SubprocessError):
        _RENDERER_VERSION = Path(chrome).name
    return _RENDERER_VERSION


def record_proof(project_root: Path, artifact: Path, image: Path,
                 kind: str = PROOF_KIND,
                 viewport: int = REVIEW_WIDTH) -> dict[str, str]:
    """Record that this artifact was rendered, and where the image is.

    Kept in `support.json` beside the adapter verdicts rather than in a file
    of its own: it is the same question -- what did this round actually
    observe -- and one more state file is one more thing to keep in step.
    """
    root = Path(project_root).resolve()
    descriptor = {
        "kind": kind,
        "proofKey": proof_key(sha256_file(Path(artifact)), str(viewport),
                              renderer_version(), kind),
        "image": str(Path(image).resolve()),
        "observedAt": datetime.now(timezone.utc).isoformat(),
    }
    path = root / "spec" / "design-harness" / "support.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = ({} if not path.is_file()
                               else json.loads(path.read_text(encoding="utf-8")))
    payload.setdefault("version", 1)
    payload["proofs"] = [proof for proof in payload.get("proofs") or []
                         if not (isinstance(proof, Mapping)
                                 and proof.get("proofKey") == descriptor["proofKey"])
                         ] + [descriptor]
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")
    return descriptor


def deliver_review_images(project_root: Path, cohort: Iterable[str], assessments_path: Path,
                          renderer: Renderer = _render_review,
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

        # A round with no changed drawing is not a round. Every image here
        # rendering byte-identical to the one already published means the user
        # is being handed the same artwork again and asked to rank it again --
        # and the `--asks` question will be about a design that did not move.
        # The comparison is free: both digests are already in hand.
        unchanged = [preview.element for preview, _, target, digest in staged_images
                     if target.is_file() and sha256_file(target) == digest]
        if len(unchanged) == len(staged_images):
            raise DeliveryError(
                "every review image in this cohort is byte-identical to the one "
                f"already published ({', '.join(unchanged)}). Nothing about the "
                "artwork changed, so there is nothing new to rank. Change the "
                "design, or change the cohort.")

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

    images = [
        ReviewImage(preview.element, preview.html_path, preview.html_sha256, target, digest)
        for preview, _, target, digest in staged_images
    ]
    for image in images:
        record_proof(root, image.source_html, image.image_path)
    return images


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
