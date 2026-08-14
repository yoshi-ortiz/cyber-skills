#!/usr/bin/env python3
"""Bootstrap and validate a portable, read-only-source design harness."""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import shutil
import sys
import tempfile
from pathlib import Path


VERSION = 1
PROFILES = {
    "frontend-layout": ["repository", "knowledge", "http", "image", "pdf", "devtools", "playwright", "lighthouse", "storybook"],
    "art-direction": ["repository", "knowledge", "http", "image", "pdf", "licensing"],
    "motion": ["repository", "knowledge", "browser", "playwright", "motion-renderer"],
    "composition": ["repository", "image", "pdf", "browser"],
    "physical-space": ["repository", "image", "pdf", "geometry", "standards"],
    "product-design": ["repository", "knowledge", "image", "pdf", "materials", "standards"],
    "copywriting": ["repository", "knowledge", "http", "copy-evidence"],
    "mockup-layering": ["repository", "image", "pdf", "layer-renderer", "color-management"],
}
RECOMMENDATIONS = {
    "frontend-layout": [
        ("frontend-browser", "Confirm DevTools MCP, Playwright, Lighthouse, responsive screenshot, and Storybook MCP adapters."),
    ],
    "art-direction": [
        ("ascii-library", "The agent must evaluate whether a pinned, licensed ASCII/Unicode art library fits the evidence; approve, reject, or replace the proposed source."),
        ("art-assets", "Confirm authoritative icon, illustration, texture, or type sources inferred from the visual grammar."),
    ],
    "motion": [
        ("motion-source", "Confirm a pinned motion library or primary choreography reference, including reduced-motion behavior."),
    ],
    "composition": [
        ("composition-source", "Confirm the proposed grid, editorial composition, or framing reference source."),
    ],
    "physical-space": [
        ("spatial-source", "Confirm applicable measurement, accessibility, safety, lighting, and material standards."),
    ],
    "product-design": [
        ("product-source", "Confirm applicable ergonomic, material, manufacturing, packaging, and regulatory sources."),
    ],
    "copywriting": [
        ("copy-source", "Confirm audience research, claim evidence, voice references, legal constraints, and localization sources."),
    ],
    "mockup-layering": [
        ("mockup-renderer", "Confirm a deterministic layer renderer and pin its version, color profile, and export settings."),
    ],
}
TEMPLATE_NAMES = ("CONTEXT.md", "CONTRACTS.md", "WORKFLOWS.md")
# OS-generated sidecars mutate whenever a folder is merely browsed. Hashing them
# wires the integrity gate to noise: Finder opening the source root turns every
# later run red while nothing about the evidence changed.
NOISE_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini", ".localized"}
NOISE_DIRS = {".Spotlight-V100", ".fseventsd", ".TemporaryItems", "__MACOSX"}
# A decision is binding until superseded. `stars` is the deterministic standing
# used to rank competing elements; it is set by the user, never by the agent.
DECISION_STATES = ("proposed", "approved", "superseded", "rejected")
STAR_RANGE = (1, 5)
# Two feedback signals, deliberately separate. Stars carry strength; sentiment
# carries direction. Sentiment maps to a verdict and, when the user gave no
# star, to a fixed default rank -- fixed so replaying a ledger is reproducible.
SENTIMENTS = {"like": ("approved", 4), "dislike": ("rejected", 1)}


class HarnessError(Exception):
    pass


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def source_entries(source_root: Path) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for path in sorted(source_root.rglob("*"), key=lambda item: item.as_posix()):
        if path.is_symlink():
            raise HarnessError(f"source contains a symlink: {path.relative_to(source_root)}")
        if path.is_dir():
            continue
        relative = path.relative_to(source_root)
        if path.name in NOISE_NAMES or NOISE_DIRS.intersection(relative.parts):
            continue
        if not path.is_file():
            raise HarnessError(f"source contains an unsupported entry: {path.relative_to(source_root)}")
        media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        entries.append({
            "path": path.relative_to(source_root).as_posix(),
            "bytes": path.stat().st_size,
            "mediaType": media_type,
            "sha256": sha256_file(path),
        })
    return entries


def parse_profiles(raw: str) -> list[str]:
    profiles = sorted({item.strip() for item in raw.split(",") if item.strip()})
    unknown = sorted(set(profiles) - set(PROFILES))
    if unknown:
        raise HarnessError(f"unknown profile(s): {', '.join(unknown)}")
    if not profiles:
        raise HarnessError("at least one profile is required")
    return profiles


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def questionnaire(profiles: list[str]) -> str:
    lines = [
        "# Design Harness Questionnaire",
        "",
        "Answer each recommendation with approve, reject, or replace. The agent proposes likely sources; the user does not need to invent them.",
        "",
        "## Project constraints",
        "",
        "1. Confirm the intended output, audience, approval authority, and release boundary.",
        "2. Confirm rights for the configured source-root evidence.",
        "3. Confirm which proposed external sources may be fetched and pinned.",
        "",
        "## Sourcing recommendations",
        "",
    ]
    number = 1
    for profile in profiles:
        for recommendation_id, prompt in RECOMMENDATIONS[profile]:
            lines.append(f"{number}. **{recommendation_id}** (`{profile}`): {prompt}")
            number += 1
    lines.extend([
        "",
        "For every approved source, record its primary URL or package, license, pinned version/edition/commit, retrieval method, expected tool cost, and SHA-256.",
        "",
    ])
    return "\n".join(lines)


def empty_decisions() -> dict[str, object]:
    return {"version": VERSION, "state": "draft", "elements": [], "supersededCount": 0}


def load_decisions(output: Path) -> dict[str, object]:
    path = output / "decisions.json"
    if not path.is_file():
        raise HarnessError("decisions.json is missing; run `init` or re-bootstrap")
    return json.loads(path.read_text(encoding="utf-8"))


def render_decisions_md(decisions: dict[str, object]) -> str:
    live = [e for e in decisions["elements"] if e["state"] in ("approved", "proposed")]
    dead = [e for e in decisions["elements"] if e["state"] in ("superseded", "rejected")]
    lines = [
        "# Design Decisions",
        "",
        "Generated by `bootstrap_harness.py decide`. Do not hand-edit.",
        "",
        "**Binding for any agent resuming this project.** An element listed under",
        "Standing may not be replaced, restyled, or dropped without an explicit",
        "`decide --supersedes` recorded here first. Chat history is not a record.",
        "",
        f"Lifecycle state: `{decisions['state']}`",
        "",
        "## Standing",
        "",
    ]
    if live:
        lines += ["| Element | Verdict | Stars | Evidence |", "| --- | --- | --- | --- |"]
        for e in sorted(live, key=lambda x: (-x["stars"], x["element"])):
            stars = "★" * e["stars"] + "☆" * (STAR_RANGE[1] - e["stars"])
            lines.append(f"| `{e['element']}` | {e['state']} | {stars} | {e['evidence']} |")
    else:
        lines.append("_No decisions recorded yet._")
    if dead:
        lines += ["", "## Superseded", ""]
        for e in sorted(dead, key=lambda x: x["element"]):
            note = f" → `{e['supersededBy']}`" if e.get("supersededBy") else ""
            lines.append(f"- ~~`{e['element']}`~~ ({e['state']}){note} — {e['evidence']}")
    return "\n".join(lines) + "\n"


def record_decision(project_root: Path, element: str, verdict: str, stars: int,
                    evidence: str, supersedes: list[str]) -> dict[str, object]:
    output = project_root.resolve(strict=True) / "spec" / "design-harness"
    if verdict not in DECISION_STATES:
        raise HarnessError(f"verdict must be one of: {', '.join(DECISION_STATES)}")
    if not STAR_RANGE[0] <= stars <= STAR_RANGE[1]:
        raise HarnessError(f"stars must be {STAR_RANGE[0]}-{STAR_RANGE[1]}")
    if not evidence.strip():
        raise HarnessError("evidence is required: quote the user, do not paraphrase")
    decisions = load_decisions(output)
    known = {e["element"] for e in decisions["elements"]}
    missing = [s for s in supersedes if s not in known]
    if missing:
        raise HarnessError(f"cannot supersede unknown element(s): {', '.join(missing)}")
    for e in decisions["elements"]:
        if e["element"] in supersedes:
            e["state"] = "superseded"
            e["supersededBy"] = element
            decisions["supersededCount"] += 1
        elif e["element"] == element:
            e["state"], e["stars"], e["evidence"] = verdict, stars, evidence
            break
    else:
        decisions["elements"].append({
            "element": element, "state": verdict, "stars": stars,
            "evidence": evidence, "supersededBy": None,
        })
    if any(e["state"] == "approved" for e in decisions["elements"]):
        decisions["state"] = "approved"
    elif decisions["state"] == "draft":
        decisions["state"] = "proposed"
    write_json(output / "decisions.json", decisions)
    (output / "DECISIONS.md").write_text(render_decisions_md(decisions), encoding="utf-8")
    project_path = output / "project.json"
    project = json.loads(project_path.read_text(encoding="utf-8"))
    project["state"] = decisions["state"]
    write_json(project_path, project)
    return decisions


def adopt_companion(project_root: Path, ledger_path: Path) -> tuple[int, int]:
    """Fold the companion's durable ledger into the harness ledger.

    The companion records what the user actually clicked and ranked. Without this
    step an agent re-types those decisions by hand, which is where design-element
    ids drift and elements in standing get silently rebuilt.
    """
    if not ledger_path.is_file():
        raise HarnessError(f"companion ledger not found: {ledger_path}")

    def is_star(value: object) -> bool:
        return isinstance(value, int) and not isinstance(value, bool) and STAR_RANGE[0] <= value <= STAR_RANGE[1]

    accepted: list[tuple[int, int, str, str, int, str]] = []
    skipped = 0
    for index, line in enumerate(ledger_path.read_text(encoding="utf-8").splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            skipped += 1
            continue
        element = event.get("element")
        stars, sentiment = event.get("stars"), event.get("sentiment")
        # An interaction carrying no design-element id names a screen-local
        # label, not a binding element. Report it rather than guessing an id.
        if not element or not isinstance(element, str):
            skipped += 1
            continue
        if sentiment is not None and sentiment not in SENTIMENTS:
            skipped += 1
            continue
        if sentiment is None and not is_star(stars):
            skipped += 1
            continue
        if sentiment is not None:
            verdict, default_stars = SENTIMENTS[sentiment]
            rank = stars if is_star(stars) else default_stars
        else:
            verdict, rank = "approved", stars
        evidence = str(event.get("text") or "").strip() or (
            f"companion {sentiment}: {rank} star" if sentiment else f"companion rank: {rank} star")
        # Replay order is fixed by (timestamp, file position) so adopting the
        # same ledger twice always yields the same ledger.
        stamp = event.get("timestamp")
        stamp = stamp if isinstance(stamp, (int, float)) and not isinstance(stamp, bool) else 0
        accepted.append((int(stamp), index, element, verdict, rank, evidence[:400]))

    for _, _, element, verdict, rank, evidence in sorted(accepted, key=lambda row: (row[0], row[1])):
        record_decision(project_root, element, verdict, rank, evidence, [])
    return len(accepted), skipped


FEEDBACK_STYLE = """<style>
.dh-fb{font:600 11px/1.3 ui-monospace,SFMono-Regular,Menlo,monospace;color:#111;
 border:1px solid currentColor;padding:6px 8px;display:flex;gap:10px;align-items:center;
 flex-wrap:wrap;background:#fff}
.dh-fb b{font-weight:800}
.dh-fb .dh-stars{display:flex;gap:2px}
.dh-fb [data-rank],.dh-fb [data-sentiment]{cursor:pointer;user-select:none;
 border:1px solid currentColor;padding:1px 5px;background:transparent;line-height:1.4}
.dh-fb [data-rank].on{background:#111;color:#fff}
.dh-fb [data-sentiment].on{background:#111;color:#fff}
</style>"""


def render_feedback_controls(decisions: dict[str, object]) -> str:
    """Emit rank + sentiment controls for every element in standing.

    Generated from the ledger so a screen cannot invent a design-element id.
    Same ledger in, byte-identical markup out.
    """
    live = [e for e in decisions["elements"] if e["state"] in ("approved", "proposed")]
    lines = [FEEDBACK_STYLE, '<div class="dh-feedback">']
    if not live:
        lines.append("<!-- no elements in standing; record one with `decide` first -->")
    for entry in sorted(live, key=lambda item: item["element"]):
        element, stars = entry["element"], entry["stars"]
        lines.append(
            f'<div class="dh-fb" data-element="{element}" data-stars="{stars}" data-label="{element}">'
        )
        lines.append(f"<b>{element}</b>")
        stars_markup = "".join(
            f'<span data-rank="{n}"{" class=\"on\"" if n <= stars else ""}>&#9733;</span>'
            for n in range(STAR_RANGE[0], STAR_RANGE[1] + 1)
        )
        lines.append(f'<span class="dh-stars">{stars_markup}</span>')
        for name in sorted(SENTIMENTS):
            glyph = "&#128077;" if name == "like" else "&#128078;"
            lines.append(f'<span data-sentiment="{name}" title="{name}">{glyph}</span>')
        lines.append("</div>")
    lines.append("</div>")
    return "\n".join(lines) + "\n"


def init_harness(project_root: Path, source_root: Path, profiles: list[str]) -> Path:
    project_root = project_root.resolve(strict=True)
    source_root = source_root.resolve(strict=True)
    if not project_root.is_dir() or not source_root.is_dir():
        raise HarnessError("project root and source root must be directories")
    output = project_root / "spec" / "design-harness"
    if is_within(output.resolve(), source_root):
        raise HarnessError("generated harness cannot live inside the read-only source root")

    before = source_entries(source_root)
    output.mkdir(parents=True, exist_ok=True)
    template_root = Path(__file__).resolve().parent.parent / "assets" / "spec"
    for name in TEMPLATE_NAMES:
        template = template_root / f"{name}.tmpl"
        if not template.is_file():
            raise HarnessError(f"missing skill template: {template}")
        (output / name).write_bytes(template.read_bytes())

    project = {
        "version": VERSION,
        "sourceRoot": str(source_root),
        "sourcePolicy": "read-only",
        "profiles": profiles,
        "state": "draft",
        "budgets": {"toolCalls": 4, "urls": 2, "newVisuals": 4, "extractedChars": 24000, "outputTokens": 1200},
    }
    capabilities = sorted({capability for profile in profiles for capability in PROFILES[profile]})
    matrix = {
        "version": VERSION,
        "profiles": profiles,
        "requiredCapabilities": [{"category": category, "adapter": None, "available": False} for category in capabilities],
        "promotionChecks": ["source-integrity", "lineage", "user-approval", "domain-conformance"],
    }
    manifest = {"version": VERSION, "algorithm": "sha256", "sourceRoot": str(source_root), "entries": before}
    write_json(output / "project.json", project)
    write_json(output / "capability-matrix.json", matrix)
    write_json(output / "source-manifest.json", manifest)
    (output / "QUESTIONNAIRE.md").write_text(questionnaire(profiles), encoding="utf-8")
    if not (output / "decisions.json").is_file():
        decisions = empty_decisions()
        write_json(output / "decisions.json", decisions)
        (output / "DECISIONS.md").write_text(render_decisions_md(decisions), encoding="utf-8")

    after = source_entries(source_root)
    if before != after:
        raise HarnessError("source root changed during bootstrap")
    return output


def validate_harness(project_root: Path) -> None:
    output = project_root.resolve(strict=True) / "spec" / "design-harness"
    required = [*TEMPLATE_NAMES, "project.json", "capability-matrix.json", "source-manifest.json",
                "QUESTIONNAIRE.md", "decisions.json", "DECISIONS.md"]
    missing = [name for name in required if not (output / name).is_file()]
    if missing:
        raise HarnessError(f"missing generated file(s): {', '.join(missing)}")
    project = json.loads((output / "project.json").read_text(encoding="utf-8"))
    manifest = json.loads((output / "source-manifest.json").read_text(encoding="utf-8"))
    matrix = json.loads((output / "capability-matrix.json").read_text(encoding="utf-8"))
    if project.get("sourcePolicy") != "read-only" or project.get("sourceRoot") != manifest.get("sourceRoot"):
        raise HarnessError("source-root contract is missing or contradictory")
    profiles = project.get("profiles")
    if not isinstance(profiles, list) or any(profile not in PROFILES for profile in profiles):
        raise HarnessError("project contains unknown profiles")
    expected_capabilities = sorted({capability for profile in profiles for capability in PROFILES[profile]})
    actual_capabilities = sorted(item.get("category") for item in matrix.get("requiredCapabilities", []))
    if actual_capabilities != expected_capabilities:
        raise HarnessError("capability matrix does not match selected profiles")
    source_root = Path(project["sourceRoot"]).resolve(strict=True)
    actual_entries = source_entries(source_root)
    if manifest.get("algorithm") != "sha256" or manifest.get("entries") != actual_entries:
        raise HarnessError("read-only source manifest mismatch")
    if "read-only" not in (output / "CONTRACTS.md").read_text(encoding="utf-8"):
        raise HarnessError("generated contracts omit the read-only source invariant")

    decisions = load_decisions(output)
    seen: set[str] = set()
    for entry in decisions.get("elements", []):
        element = entry.get("element")
        if not element or element in seen:
            raise HarnessError("decisions.json contains a missing or duplicate element id")
        seen.add(element)
        if entry.get("state") not in DECISION_STATES:
            raise HarnessError(f"decision '{element}' has an unknown state")
        if not isinstance(entry.get("stars"), int) or not STAR_RANGE[0] <= entry["stars"] <= STAR_RANGE[1]:
            raise HarnessError(f"decision '{element}' is missing a {STAR_RANGE[0]}-{STAR_RANGE[1]} star rank")
        if not str(entry.get("evidence", "")).strip():
            raise HarnessError(f"decision '{element}' has no user evidence excerpt")
        target = entry.get("supersededBy")
        if target and target not in {e.get("element") for e in decisions["elements"]}:
            raise HarnessError(f"decision '{element}' is superseded by an unknown element")
    if decisions.get("state") != project.get("state"):
        raise HarnessError("project.json state disagrees with decisions.json state")
    if (output / "DECISIONS.md").read_text(encoding="utf-8") != render_decisions_md(decisions):
        raise HarnessError("DECISIONS.md is stale; regenerate it with `decide`")


def self_test() -> None:
    with tempfile.TemporaryDirectory(prefix="design-harness-test-") as temp:
        root = Path(temp)
        project = root / "project"
        source = root / "Oddly Named Evidence 42"
        project.mkdir()
        source.mkdir()
        (source / "reference.txt").write_text("ASCII composition and physical product", encoding="utf-8")
        (source / "frame.png").write_bytes(b"deterministic-image-fixture")
        before = source_entries(source)
        output = init_harness(project, source, ["art-direction", "mockup-layering", "physical-space"])
        validate_harness(project)
        after = source_entries(source)
        if before != after:
            raise HarnessError("self-test source changed")
        questions = (output / "QUESTIONNAIRE.md").read_text(encoding="utf-8")
        for expected in ("ASCII/Unicode", "layer renderer", "measurement"):
            if expected not in questions:
                raise HarnessError(f"self-test questionnaire omitted: {expected}")

        # OS sidecars must never enter the manifest: browsing the source root
        # would otherwise flip validate to red with the evidence untouched.
        (source / ".DS_Store").write_bytes(b"finder-noise-v1")
        validate_harness(project)
        (source / ".DS_Store").write_bytes(b"finder-noise-v2-different-bytes")
        validate_harness(project)

        # A decision must survive as an artifact, carry a star rank, and win
        # over the element it supersedes.
        record_decision(project, "cover.layout.two-column", "approved", 5, "user: 'c2'", [])
        record_decision(project, "cover.spine.right", "approved", 4, "user: 'place it on the right'", [])
        record_decision(project, "cover.layout.single-column", "rejected", 1, "user: 'you destructed the two columns'",
                        ["cover.layout.two-column"])
        validate_harness(project)
        ledger = json.loads((output / "decisions.json").read_text(encoding="utf-8"))
        by_id = {e["element"]: e for e in ledger["elements"]}
        if by_id["cover.layout.two-column"]["state"] != "superseded":
            raise HarnessError("self-test: supersede did not retire the prior element")
        if by_id["cover.layout.two-column"]["supersededBy"] != "cover.layout.single-column":
            raise HarnessError("self-test: supersede lost its back-reference")
        if "★★★★☆" not in (output / "DECISIONS.md").read_text(encoding="utf-8"):
            raise HarnessError("self-test: star rank not rendered")
        if ledger["state"] != "approved" or json.loads((output / "project.json").read_text(encoding="utf-8"))["state"] != "approved":
            raise HarnessError("self-test: lifecycle state did not advance past draft")

        # Companion star ranks must adopt into the ledger; events with no
        # design-element id must be skipped rather than guessed at.
        companion = root / "decisions.jsonl"
        companion.write_text("\n".join([
            json.dumps({"type": "rank", "element": "form.paper.white", "stars": 5, "text": "user: form stays white", "timestamp": 30}),
            json.dumps({"type": "click", "choice": "screen-local-slug", "element": None, "stars": None}),
            json.dumps({"type": "rank", "element": "palette.inferred", "stars": 1, "timestamp": 10}),
            json.dumps({"type": "sentiment", "element": "cover.ring.kicker", "sentiment": "like", "timestamp": 20}),
            json.dumps({"type": "sentiment", "element": "cover.background.black", "sentiment": "dislike", "timestamp": 40}),
            json.dumps({"type": "sentiment", "element": "bogus.sentiment", "sentiment": "meh", "timestamp": 50}),
            json.dumps({"type": "rank", "element": "bogus.range", "stars": 9, "timestamp": 60}),
            "not json at all",
        ]) + "\n", encoding="utf-8")
        adopted, skipped = adopt_companion(project, companion)
        if adopted != 4 or skipped != 4:
            raise HarnessError(f"self-test: adopt miscounted ({adopted} adopted, {skipped} skipped)")
        validate_harness(project)
        adopted_ledger = {e["element"]: e for e in json.loads((output / "decisions.json").read_text(encoding="utf-8"))["elements"]}
        if adopted_ledger["form.paper.white"]["stars"] != 5 or adopted_ledger["palette.inferred"]["stars"] != 1:
            raise HarnessError("self-test: adopt lost the star rank")
        if "user: form stays white" not in adopted_ledger["form.paper.white"]["evidence"]:
            raise HarnessError("self-test: adopt dropped the evidence excerpt")
        # sentiment maps deterministically to verdict + default rank
        for element, name in (("cover.ring.kicker", "like"), ("cover.background.black", "dislike")):
            entry = adopted_ledger[element]
            if (entry["state"], entry["stars"]) != SENTIMENTS[name]:
                raise HarnessError(f"self-test: {name} did not map to its verdict/rank")

        # Adopting the same ledger twice must be a no-op on content.
        first = (output / "decisions.json").read_text(encoding="utf-8")
        adopt_companion(project, companion)
        if (output / "decisions.json").read_text(encoding="utf-8") != first:
            raise HarnessError("self-test: adopt is not idempotent")

        # Controls are generated from the ledger and are byte-stable.
        markup = render_feedback_controls(load_decisions(output))
        if markup != render_feedback_controls(load_decisions(output)):
            raise HarnessError("self-test: controls are not deterministic")
        for required in ('data-element="form.paper.white"', 'data-rank="5"',
                         'data-sentiment="like"', 'data-sentiment="dislike"'):
            if required not in markup:
                raise HarnessError(f"self-test: controls omitted {required}")
        if 'data-element="cover.background.black"' in markup:
            raise HarnessError("self-test: controls offered a rejected element")

        # validate must refuse a decision-less harness rather than green-light it.
        (output / "decisions.json").unlink()
        try:
            validate_harness(project)
        except HarnessError:
            pass
        else:
            raise HarnessError("self-test: validate green-lit a harness with no decision ledger")


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description=__doc__)
    subcommands = command.add_subparsers(dest="command", required=True)
    init = subcommands.add_parser("init")
    init.add_argument("--project-root", required=True, type=Path)
    init.add_argument("--source-root", required=True, type=Path)
    init.add_argument("--profiles", required=True)
    validate = subcommands.add_parser("validate")
    validate.add_argument("--project-root", required=True, type=Path)
    decide = subcommands.add_parser("decide", help="record a binding design decision")
    decide.add_argument("--project-root", required=True, type=Path)
    decide.add_argument("--element", required=True, help="stable dotted id, e.g. cover.layout.two-column")
    decide.add_argument("--verdict", required=True, choices=DECISION_STATES)
    decide.add_argument("--stars", required=True, type=int, help=f"{STAR_RANGE[0]}-{STAR_RANGE[1]}, set by the user")
    decide.add_argument("--evidence", required=True, help="verbatim user excerpt, not a paraphrase")
    decide.add_argument("--supersedes", default="", help="comma-separated element ids this replaces")
    adopt = subcommands.add_parser("adopt", help="fold companion star ranks into the ledger")
    adopt.add_argument("--project-root", required=True, type=Path)
    adopt.add_argument("--companion-ledger", required=True, type=Path,
                       help="path to the companion's durable decisions.jsonl")
    controls = subcommands.add_parser("controls", help="emit star + like/dislike controls from the ledger")
    controls.add_argument("--project-root", required=True, type=Path)
    controls.add_argument("--out", type=Path, help="write here instead of stdout")
    subcommands.add_parser("self-test")
    return command


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "init":
            output = init_harness(args.project_root, args.source_root, parse_profiles(args.profiles))
            print(output)
        elif args.command == "validate":
            validate_harness(args.project_root)
            print("Design harness is valid; source hashes are unchanged.")
        elif args.command == "decide":
            supersedes = [item.strip() for item in args.supersedes.split(",") if item.strip()]
            decisions = record_decision(args.project_root, args.element, args.verdict,
                                        args.stars, args.evidence, supersedes)
            live = [e for e in decisions["elements"] if e["state"] in ("approved", "proposed")]
            print(f"Recorded {args.element} ({args.verdict}, {args.stars}★). "
                  f"{len(live)} element(s) standing, state={decisions['state']}.")
        elif args.command == "adopt":
            adopted, skipped = adopt_companion(args.project_root, args.companion_ledger)
            print(f"Adopted {adopted} ranked decision(s); skipped {skipped} "
                  f"interaction(s) with no design-element id or usable signal.")
        elif args.command == "controls":
            output = args.project_root.resolve(strict=True) / "spec" / "design-harness"
            markup = render_feedback_controls(load_decisions(output))
            if args.out:
                args.out.write_text(markup, encoding="utf-8")
                print(f"Wrote feedback controls to {args.out}")
            else:
                print(markup, end="")
        else:
            self_test()
            print("Self-test passed.")
        return 0
    except (HarnessError, OSError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

