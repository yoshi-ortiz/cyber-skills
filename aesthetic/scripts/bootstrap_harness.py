#!/usr/bin/env python3
"""Bootstrap and validate a portable, read-only-source design harness."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import mimetypes
import os
import re
import time
import shutil
import subprocess
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
STAR_RANGE = (0, 5)
# Two feedback signals, deliberately separate. Stars carry strength; sentiment
# carries direction. Sentiment maps to a verdict and, when the user gave no
# star, to a fixed default rank -- fixed so replaying a ledger is reproducible.
SENTIMENTS = {"like": ("approved", 4), "dislike": ("rejected", 1)}
# A preview is the graphic the star is actually about.
PREVIEW_SUFFIXES = {".svg", ".html", ".png", ".jpg", ".jpeg", ".webp", ".gif"}
# Who set a rank. The distinction is the whole point: an agent-typed number and
# a user click used to be indistinguishable in the ledger.
SOURCES = ("user", "agent")
AGENT_MAX_STARS = 1


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
                    evidence: str, supersedes: list[str],
                    preview: dict[str, str] | None = None,
                    source: str = "agent",
                    sentiment: str | None = None) -> dict[str, object]:
    output = project_root.resolve(strict=True) / "spec" / "design-harness"
    if verdict not in DECISION_STATES:
        raise HarnessError(f"verdict must be one of: {', '.join(DECISION_STATES)}")
    if not STAR_RANGE[0] <= stars <= STAR_RANGE[1]:
        raise HarnessError(f"stars must be {STAR_RANGE[0]}-{STAR_RANGE[1]}")
    if not evidence.strip():
        raise HarnessError("evidence is required: quote the user, do not paraphrase")
    if source not in SOURCES:
        raise HarnessError(f"source must be one of: {', '.join(SOURCES)}")
    if source == "agent" and stars > AGENT_MAX_STARS:
        raise HarnessError(
            f"agent-set rank is capped at {AGENT_MAX_STARS} star. A higher rank must come from a "
            "user click, adopted with `adopt` -- typing the number yourself is the failure this "
            "cap exists to prevent.")
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
            e["source"] = source
            if sentiment is not None:
                e["sentiment"] = sentiment
            e.setdefault("sentiment", None)
            if preview is not None:
                e["preview"] = preview
            e.setdefault("preview", None)
            break
    else:
        decisions["elements"].append({
            "element": element, "state": verdict, "stars": stars,
            "evidence": evidence, "supersededBy": None, "preview": preview,
            "source": source, "sentiment": sentiment,
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
        if event.get("verdict") not in (None, "approved", "rejected"):
            skipped += 1
            continue
        if sentiment is not None and sentiment not in SENTIMENTS:
            skipped += 1
            continue
        if sentiment is None and event.get("verdict") is None and not is_star(stars):
            skipped += 1
            continue
        explicit = event.get("verdict")
        if explicit in ("approved", "rejected"):
            verdict = explicit
            rank = stars if is_star(stars) else (0 if explicit == "rejected" else AGENT_MAX_STARS + 1)
        elif sentiment is not None:
            verdict, default_stars = SENTIMENTS[sentiment]
            rank = stars if is_star(stars) else default_stars
        else:
            # A zero is the user saying "kill it", not a missing value.
            verdict, rank = ("rejected" if stars == 0 else "approved"), stars
        evidence = str(event.get("text") or "").strip() or (
            f"companion {sentiment}: {rank} star" if sentiment else f"companion rank: {rank} star")
        # Replay order is fixed by (timestamp, file position) so adopting the
        # same ledger twice always yields the same ledger.
        stamp = event.get("timestamp")
        stamp = stamp if isinstance(stamp, (int, float)) and not isinstance(stamp, bool) else 0
        accepted.append((int(stamp), index, element, verdict, rank, evidence[:400]))

    for _, _, element, verdict, rank, evidence in sorted(accepted, key=lambda row: (row[0], row[1])):
        record_decision(project_root, element, verdict, rank, evidence, [], source="user",
                        sentiment=sentiment)
    return len(accepted), skipped


# Every token has a var()-with-fallback, never a bare literal. Two ways to set
# them, both deterministic:
#   1. Pass --bg/--ink/--accent/--font to `controls`; values are baked into an
#      inline style on the wrapper, so the same flags always emit the same
#      bytes.
#   2. Pass none, and nest the output inside a screen that already sets
#      --dh-bg/--dh-ink/--dh-accent/--dh-font on an ancestor (every screen this
#      harness has produced does, since C2/rev13 scope --bg/--acc per card) --
#      the cascade fills the fallback. Either way there is no hardcoded color
#      the harness's own approved palette (`palette.family-from-cards`) can be
#      overridden by.
# Inline so a host stylesheet cannot collapse the one element the user must see.
SHOT_INLINE = ("display:block;flex:0 0 auto;inline-size:var(--dh-shot-w,132px);"
               "block-size:calc(var(--dh-shot-w,132px) * 11 / 8.5);overflow:hidden;"
               "position:relative;border:1px solid currentColor;background:#fff")
SHOT_INNER_INLINE = ("position:absolute;inset-block-start:0;inset-inline-start:0;"
                     "inline-size:850px;block-size:1100px;transform-origin:0 0;"
                     "transform:scale(calc(var(--dh-shot-w,132px) / 850));pointer-events:none")
STYLE_MARKER = "/* dh-controls */"
FEEDBACK_STYLE = """<style>/* dh-controls */
.dh-feedback{container-type:inline-size}
.dh-offline{display:block;background:#b00;color:#fff;font:700 12px/1.4 ui-monospace,monospace;
 padding:8px 10px;margin-bottom:8px}
:root[data-dh-live] .dh-offline{display:none}
.dh-fb{font:600 11px/1.3 var(--dh-font,ui-monospace,SFMono-Regular,Menlo,monospace);
 color:var(--dh-ink,#111);background:var(--dh-bg,#fff);
 border:1px solid var(--dh-ink,#111);padding:8px;display:grid;
 grid-template-columns:var(--dh-shot-w,132px) 1fr auto;gap:12px;align-items:center;
 contain:layout style;content-visibility:auto;contain-intrinsic-size:auto 96px}
.dh-fb + .dh-fb{border-top:0}
.dh-fb b{font-weight:800;overflow-wrap:anywhere}
.dh-fb .dh-meta{display:flex;flex-direction:column;gap:5px;min-width:0}
.dh-fb .dh-signals{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.dh-fb .dh-stars{display:flex;gap:2px;color:var(--dh-accent,var(--dh-ink,#111))}
.dh-fb [data-rank],.dh-fb [data-sentiment]{cursor:pointer;user-select:none;
 border:1px solid var(--dh-ink,#111);padding:1px 5px;background:transparent;line-height:1.4}
.dh-fb [data-rank]:focus-visible,.dh-fb [data-sentiment]:focus-visible{
 outline:2px solid var(--dh-accent,var(--dh-ink,#111));outline-offset:2px}
.dh-fb [data-rank].on{background:var(--dh-accent,var(--dh-ink,#111));color:var(--dh-bg,#fff)}
.dh-fb [data-sentiment].on{background:var(--dh-accent,var(--dh-ink,#111));color:var(--dh-bg,#fff)}
/* The graphic being ranked. Isolated so an injected fragment cannot restyle
   the list around it, and clipped to a fixed frame so a tall screen does not
   stretch its row. */
.dh-shot{inline-size:var(--dh-shot-w,132px);aspect-ratio:8.5/11;overflow:hidden;
 position:relative;border:1px solid var(--dh-ink,#111);background:var(--dh-bg,#fff);
 contain:strict;display:block}
.dh-shot > .dh-shot-inner{position:absolute;inset-block-start:0;inset-inline-start:0;
 inline-size:var(--dh-shot-src-w,850px);block-size:var(--dh-shot-src-h,1100px);
 transform:scale(calc(var(--dh-shot-w,132px) / var(--dh-shot-src-w,850px)));
 transform-origin:0 0;pointer-events:none}
.dh-shot img{inline-size:100%;block-size:100%;object-fit:contain;display:block}
.dh-shot-missing{display:grid;place-items:center;text-align:center;padding:6px;
 font-size:9px;opacity:.62;block-size:100%}
@container (max-width: 520px){
 .dh-fb{grid-template-columns:var(--dh-shot-w,132px) 1fr}
 .dh-fb .dh-signals{grid-column:1 / -1}
}
@media (prefers-reduced-motion:reduce){.dh-fb *{transition:none!important;animation:none!important}}
</style>"""


def preview_reference(project_root: Path, raw: str) -> dict[str, str]:
    """Resolve and hash a preview graphic for a design element.

    Stored as a project-relative path plus a hash, on the same principle as the
    corpus manifest: a preview that silently changed is a preview nobody
    reviewed.
    """
    project_root = project_root.resolve(strict=True)
    candidate = (project_root / raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
    if not is_within(candidate, project_root):
        raise HarnessError("preview must live inside the project root")
    if not candidate.is_file():
        raise HarnessError(f"preview not found: {raw}")
    if candidate.suffix.lower() not in PREVIEW_SUFFIXES:
        raise HarnessError(f"unsupported preview type '{candidate.suffix}'; use one of "
                           + ", ".join(sorted(PREVIEW_SUFFIXES)))
    return {"path": candidate.relative_to(project_root).as_posix(), "sha256": sha256_file(candidate)}


def render_preview(project_root: Path | None, preview: dict[str, str] | None, element: str) -> str:
    """Inline the graphic for one element, or say plainly that there is none."""
    if not preview:
        return (f'<span class="dh-shot" style="{SHOT_INLINE}">'
                '<span class="dh-shot-missing">sin gráfico<br>--preview</span></span>')
    if project_root is None:
        return (f'<span class="dh-shot" style="{SHOT_INLINE}">'
                f'<span class="dh-shot-missing">{preview["path"]}</span></span>')
    path = (project_root / preview["path"])
    if not path.is_file():
        return (f'<span class="dh-shot" style="{SHOT_INLINE}">'
                f'<span class="dh-shot-missing">gráfico ausente<br>{preview["path"]}</span></span>')
    suffix = path.suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
        media = "image/jpeg" if suffix in {".jpg", ".jpeg"} else f"image/{suffix.lstrip('.')}"
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        body = f'<img alt="" src="data:{media};base64,{encoded}">'
        return f'<span class="dh-shot" style="{SHOT_INLINE}">{body}</span>'
    # svg / html fragment: scaled inside a clipped frame rather than reflowed
    fragment = path.read_text(encoding="utf-8")
    if suffix == ".svg":
        # Force the root <svg> to fill the frame regardless of its own width/height attrs.
        fragment = re.sub(r"<svg\b", '<svg preserveAspectRatio="xMidYMid meet" '
                          'style="width:100%;height:100%;display:block"', fragment, count=1)
        return f'<span class="dh-shot" style="{SHOT_INLINE}">{fragment}</span>'
    return (f'<span class="dh-shot" style="{SHOT_INLINE}">'
            f'<span class="dh-shot-inner" style="{SHOT_INNER_INLINE}">{fragment}</span></span>')


def render_feedback_controls(decisions: dict[str, object], theme: dict[str, str] | None = None,
                             project_root: Path | None = None) -> str:
    """Emit rank + sentiment controls for every element in standing.

    Generated from the ledger so a screen cannot invent a design-element id.
    Each row carries the graphic being ranked: a star next to a dotted id is a
    guess, not a judgement. Same ledger, theme and previews in, byte-identical
    markup out.
    """
    live = [e for e in decisions["elements"] if e["state"] in ("approved", "proposed")]
    theme_vars = {
        "--dh-bg": "bg", "--dh-ink": "ink", "--dh-accent": "accent",
        "--dh-font": "font", "--dh-shot-w": "shot",
    }
    wrapper_style = ""
    if theme:
        declared = "; ".join(f"{prop}: {theme[key]}" for prop, key in theme_vars.items() if theme.get(key))
        if declared:
            wrapper_style = f' style="{declared}"'
    lines = [FEEDBACK_STYLE, f'<div class="dh-feedback"{wrapper_style}>',
             '<strong class="dh-offline">Sin conexión al companion: estos clics NO se guardan. '
             'Abre la URL del companion (http://localhost:PORT/?key=...), no el archivo.</strong>']
    if not live:
        lines.append("<!-- no elements in standing; record one with `decide` first -->")
    for entry in sorted(live, key=lambda item: item["element"]):
        element, stars = entry["element"], entry["stars"]
        lines.append(
            f'<div class="dh-fb" data-element="{element}" data-stars="{stars}" data-label="{element}">'
        )
        lines.append(render_preview(project_root, entry.get("preview"), element))
        lines.append('<span class="dh-meta">')
        lines.append(f"<b>{element}</b>")
        lines.append(f'<small>{entry["state"]}</small>')
        lines.append("</span>")
        lines.append('<span class="dh-signals">')
        stars_markup = "".join(
            (f'<span data-rank="0" role="button" tabindex="0" aria-label="cero, descartar"'
             f'{" class=\"on\"" if stars == 0 else ""}>0</span>') if n == 0 else
            (f'<span data-rank="{n}" role="button" tabindex="0" aria-label="{n} de {STAR_RANGE[1]}"'
             f'{" class=\"on\"" if 0 < n <= stars else ""}>&#9733;</span>')
            for n in range(STAR_RANGE[0], STAR_RANGE[1] + 1)
        )
        lines.append(f'<span class="dh-stars" role="group" aria-label="rango {element}">{stars_markup}</span>')
        mood = entry.get("sentiment")
        for name, glyph, label in (("like", "&#128077;", "me gusta"), ("dislike", "&#128078;", "no me gusta")):
            on = ' class="on"' if mood == name else ""
            lines.append(f'<span data-sentiment="{name}" role="button" tabindex="0" '
                         f'aria-label="{label} {element}" title="{label}"{on}>{glyph}</span>')
        on = ' class="on"' if entry["state"] == "approved" else ""
        lines.append(f'<span data-verdict="approved" role="button" tabindex="0" '
                     f'aria-label="aprobar {element}" title="aprobar"{on}>&#10003;</span>')
        lines.append("</span>")
        lines.append("</div>")
    lines.append("</div>")
    return "\n".join(lines) + "\n"


def record_preflight(project_root: Path, available: list[str], missing: list[str]) -> dict[str, object]:
    """Record which adapters were actually observed, per the compute invariant.

    The agent cannot detect its own MCP wiring from inside this script, so
    availability is asserted explicitly and stored. An adapter that was never
    preflighted stays `available: false` -- absence of evidence is not
    availability.
    """
    output = project_root.resolve(strict=True) / "spec" / "design-harness"
    matrix_path = output / "capability-matrix.json"
    if not matrix_path.is_file():
        raise HarnessError("capability-matrix.json is missing; run `init` first")
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    claimed = {item["category"] for item in matrix.get("requiredCapabilities", [])}
    unknown = sorted((set(available) | set(missing)) - claimed)
    if unknown:
        raise HarnessError("capability not required by the selected profiles: " + ", ".join(unknown))
    both = sorted(set(available) & set(missing))
    if both:
        raise HarnessError("capability marked both available and missing: " + ", ".join(both))
    for item in matrix["requiredCapabilities"]:
        if item["category"] in available:
            item["available"] = True
        elif item["category"] in missing:
            item["available"] = False
    write_json(matrix_path, matrix)
    return matrix


def newest_session_dir(project_root: Path) -> Path:
    root = project_root / ".superpowers" / "brainstorm"
    sessions = [d for d in root.glob("*/") if (d / "content").is_dir()] if root.is_dir() else []
    if not sessions:
        raise HarnessError("no companion session found; start the companion first")
    return max(sessions, key=lambda d: d.stat().st_mtime)


def embed_controls(project_root: Path, screen: Path, theme: dict[str, str] | None = None) -> int:
    """Fill a screen's `data-dh-controls` placeholders with generated rows.

    Without this, an agent wanting scoring inside a prototype hand-writes the
    markup and silently drops the component graphic -- which is exactly what
    happened. The placeholder names the elements; the harness supplies the row.
    """
    project_root = project_root.resolve(strict=True)
    output = project_root / "spec" / "design-harness"
    html = screen.read_text(encoding="utf-8")
    generated = render_feedback_controls(load_decisions(output), theme, project_root)
    rows = {m.group(1): m.group(0) for m in re.finditer(
        r'<div class="dh-fb" data-element="([^"]+)".*?\n</div>', generated, re.S)}
    style_match = re.search(r"<style>.*?</style>", generated, re.S)
    style = style_match.group(0) if style_match else ""

    placeholders = list(re.finditer(
        r'<div([^>]*?)data-dh-controls="([^"]*)"([^>]*)>(.*?)</div>', html, re.S))
    if not placeholders:
        raise HarnessError(
            'no <div data-dh-controls="element.a,element.b"></div> placeholder in the screen. '
            "Add one where scoring belongs -- never hand-write the rows.")

    filled = 0
    for match in reversed(placeholders):
        wanted = [e.strip() for e in match.group(2).split(",") if e.strip()]
        missing = [e for e in wanted if e not in rows]
        if missing:
            raise HarnessError("placeholder names element(s) not in standing: " + ", ".join(missing))
        body = "\n".join(rows[e] for e in wanted)
        replacement = f"<div{match.group(1)}data-dh-controls=\"{match.group(2)}\"{match.group(3)}>\n{body}\n</div>"
        html = html[:match.start()] + replacement + html[match.end():]
        filled += len(wanted)

    if style and STYLE_MARKER not in html:
        html = html.replace("</head>", style + "\n</head>", 1) if "</head>" in html else style + "\n" + html
    screen.write_text(html, encoding="utf-8")
    return filled


def publish_screen(project_root: Path, screen: Path, gap_seconds: int = 5) -> Path:
    """Make one screen the served one, deterministically.

    The companion serves only the newest-mtime file. Doing that by hand invites
    both a silent redirect and an mtime race, so the harness does it: the chosen
    screen is stamped a clear margin ahead of every other screen.
    """
    session = newest_session_dir(project_root.resolve(strict=True))
    content = session / "content"
    if screen.resolve().parent != content.resolve():
        raise HarnessError(f"screen must live in the served session: {content}")
    others = [p for p in content.glob("*.html") if p.resolve() != screen.resolve()]
    newest_other = max((p.stat().st_mtime for p in others), default=0.0)
    stamp = max(time.time(), newest_other + gap_seconds)
    os.utime(screen, (stamp, stamp))
    return screen


def ledger_stats(decisions: dict[str, object]) -> dict[str, object]:
    """Deterministic aggregates over the ledger. Same ledger, same numbers.

    The headline is `coverage`: what fraction of standing elements carry a
    signal the user actually set. A high star average means nothing if the
    agent typed all of it.
    """
    elements = decisions["elements"]
    live = [e for e in elements if e["state"] in ("approved", "proposed")]
    user = [e for e in live if e.get("source") == "user"]
    ranked = sorted((e["stars"] for e in user))

    def median(values: list[int]) -> float:
        if not values:
            return 0.0
        mid = len(values) // 2
        return float(values[mid]) if len(values) % 2 else (values[mid - 1] + values[mid]) / 2

    histogram = {str(n): sum(1 for e in user if e["stars"] == n)
                 for n in range(STAR_RANGE[0], STAR_RANGE[1] + 1)}
    # A user who liked something but scored it low, or disliked something still
    # standing, is telling you something an average would hide.
    conflicts = sorted(e["element"] for e in live
                       if (e.get("sentiment") == "like" and e["stars"] <= 1)
                       or (e.get("sentiment") == "dislike" and e["stars"] >= 4))
    return {
        "standing": len(live),
        "userSet": len(user),
        "agentSet": len(live) - len(user),
        "coverage": round(len(user) / len(live), 3) if live else 0.0,
        "meanStars": round(sum(ranked) / len(ranked), 2) if ranked else 0.0,
        "medianStars": median(ranked),
        "histogram": histogram,
        "likes": sum(1 for e in live if e.get("sentiment") == "like"),
        "dislikes": sum(1 for e in live if e.get("sentiment") == "dislike"),
        "approved": sum(1 for e in elements if e["state"] == "approved"),
        "rejected": sum(1 for e in elements if e["state"] == "rejected"),
        "superseded": sum(1 for e in elements if e["state"] == "superseded"),
        "unscored": sorted(e["element"] for e in live if e.get("source") != "user"),
        "conflicts": conflicts,
    }


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
    corpus_drift: list[str] = []
    if manifest.get("algorithm") != "sha256":
        raise HarnessError("source manifest algorithm is not sha256")
    if manifest.get("entries") != actual_entries:
        was = {e["path"]: e["sha256"] for e in manifest.get("entries", [])}
        now = {e["path"]: e["sha256"] for e in actual_entries}
        corpus_drift = ([f"removed: {p}" for p in sorted(set(was) - set(now))]
                        + [f"added: {p}" for p in sorted(set(now) - set(was))]
                        + [f"changed: {p}" for p in sorted(set(was) & set(now)) if was[p] != now[p]])
    if "read-only" not in (output / "CONTRACTS.md").read_text(encoding="utf-8"):
        raise HarnessError("generated contracts omit the read-only source invariant")

    decisions = load_decisions(output)
    warnings: list[str] = []
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
        preview = entry.get("preview")
        if preview is not None:
            if not isinstance(preview, dict) or not preview.get("path") or not preview.get("sha256"):
                raise HarnessError(f"decision '{element}' has a malformed preview reference")
            shot = project_root.resolve(strict=True) / preview["path"]
            if not shot.is_file():
                raise HarnessError(f"decision '{element}' references a missing preview: {preview['path']}")
            if sha256_file(shot) != preview["sha256"]:
                warnings.append(f"preview for '{element}' changed since it was ranked "
                                f"(re-record with `decide --preview` when convenient)")
        target = entry.get("supersededBy")
        if target and target not in {e.get("element") for e in decisions["elements"]}:
            raise HarnessError(f"decision '{element}' is superseded by an unknown element")
    if decisions.get("state") != project.get("state"):
        raise HarnessError("project.json state disagrees with decisions.json state")
    if (output / "DECISIONS.md").read_text(encoding="utf-8") != render_decisions_md(decisions):
        raise HarnessError("DECISIONS.md is stale; regenerate it with `decide`")
    return {"warnings": warnings, "corpusDrift": corpus_drift}


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
        record_decision(project, "cover.layout.two-column", "approved", 5, "user: 'c2'", [], source="user")
        record_decision(project, "cover.spine.right", "approved", 4, "user: 'place it on the right'", [], source="user")
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
                         'data-verdict="approved"', 'data-sentiment="like"',
                         'data-sentiment="dislike"', 'data-rank="0"'):
            if required not in markup:
                raise HarnessError(f"self-test: controls omitted {required}")
        if 'data-element="cover.background.black"' in markup:
            raise HarnessError("self-test: controls offered a rejected element")

        # Every color must be a themeable token, never a literal that would
        # override the corpus palette the ledger already approved.
        style_block = markup.split("</style>")[0]
        for token in ("--dh-bg", "--dh-ink", "--dh-accent", "--dh-font"):
            if token not in style_block:
                raise HarnessError(f"self-test: controls style omits the {token} token")
        for literal in ("color:#111", "background:#fff", "background:#111;color:#fff"):
            if literal in style_block.replace(" ", ""):
                raise HarnessError(f"self-test: controls hardcode {literal} outside a var() fallback")

        # A declared theme is baked in, and identical flags emit identical bytes.
        themed = render_feedback_controls(load_decisions(output),
                                          {"bg": "#f9e7b5", "ink": "#111", "accent": "#d9482a", "font": None})
        if "--dh-bg: #f9e7b5" not in themed or "--dh-accent: #d9482a" not in themed:
            raise HarnessError("self-test: declared theme was not applied")
        if "--dh-font" in themed.split("<div")[1].split(">")[0]:
            raise HarnessError("self-test: unset theme key leaked into the wrapper")
        if themed != render_feedback_controls(load_decisions(output),
                                              {"bg": "#f9e7b5", "ink": "#111", "accent": "#d9482a", "font": None}):
            raise HarnessError("self-test: themed controls are not deterministic")

        # The graphic being ranked must ride along with the rank, and must be
        # hash-pinned: a preview that changed is a preview nobody reviewed.
        shots = project / "shots"
        shots.mkdir()
        shot = shots / "cover.svg"
        shot.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 85 110"><rect width="85" height="110" fill="#f9e7b5"/></svg>', encoding="utf-8")
        record_decision(project, "cover.layout.two-column", "approved", 5, "user: 'c2'", [],
                        preview_reference(project, "shots/cover.svg"), source="user")
        validate_harness(project)
        with_shot = render_feedback_controls(load_decisions(output), None, project)
        if 'class="dh-shot"' not in with_shot or "#f9e7b5" not in with_shot:
            raise HarnessError("self-test: the ranked element carries no graphic")
        if "sin gr" not in render_feedback_controls(load_decisions(output), None, project):
            raise HarnessError("self-test: elements without a preview must say so, not fake one")
        if with_shot != render_feedback_controls(load_decisions(output), None, project):
            raise HarnessError("self-test: previews broke control determinism")
        # A regenerated preview is normal work: it must be reported, not blocked.
        shot.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 85 110"><rect fill="#000"/></svg>', encoding="utf-8")
        report = validate_harness(project)
        if not any("changed since it was ranked" in w for w in report["warnings"]):
            raise HarnessError("self-test: preview drift must be reported as a warning")
        record_decision(project, "cover.layout.two-column", "approved", 5, "user: 'c2'", [],
                        preview_reference(project, "shots/cover.svg"), source="user")
        validate_harness(project)
        for bad in ("../outside.svg", "shots/nope.svg", "scripts/evil.py"):
            try:
                preview_reference(project, bad)
            except HarnessError:
                continue
            raise HarnessError(f"self-test: preview accepted an unsafe reference: {bad}")

        # The agent must not be able to type a confident rank. This cap is the
        # difference between "user clicked 4" and "agent felt like 4".
        try:
            record_decision(project, "agent.guess", "approved", 4, "agent hunch", [], source="agent")
        except HarnessError:
            pass
        else:
            raise HarnessError("self-test: agent was allowed to set a rank above the cap")
        record_decision(project, "agent.guess", "proposed", 1, "agent inference", [], source="agent")
        ledger_now = {e["element"]: e for e in json.loads((output / "decisions.json").read_text(encoding="utf-8"))["elements"]}
        if ledger_now["agent.guess"]["source"] != "agent":
            raise HarnessError("self-test: provenance not recorded")
        if ledger_now["cover.layout.two-column"]["source"] != "user":
            raise HarnessError("self-test: user provenance lost")

        # zero is a real score meaning "kill it", and it must survive adoption
        zero_ledger = root / "zero.jsonl"
        zero_ledger.write_text(json.dumps({"element": "kill.me", "stars": 0, "timestamp": 1}) + "\n"
                               + json.dumps({"element": "bless.me", "verdict": "approved", "timestamp": 2}) + "\n",
                               encoding="utf-8")
        adopt_companion(project, zero_ledger)
        z = {e["element"]: e for e in json.loads((output / "decisions.json").read_text(encoding="utf-8"))["elements"]}
        if z["kill.me"]["state"] != "rejected" or z["kill.me"]["stars"] != 0:
            raise HarnessError("self-test: zero stars did not reject")
        if z["bless.me"]["state"] != "approved" or z["bless.me"]["source"] != "user":
            raise HarnessError("self-test: explicit approve verdict not adopted")

        # Statistics must be deterministic and must not flatter the ledger:
        # coverage tells you how much is really the user's.
        first_stats = ledger_stats(load_decisions(output))
        if first_stats != ledger_stats(load_decisions(output)):
            raise HarnessError("self-test: stats are not deterministic")
        if not 0.0 <= first_stats["coverage"] <= 1.0:
            raise HarnessError("self-test: coverage out of range")
        if first_stats["userSet"] + first_stats["agentSet"] != first_stats["standing"]:
            raise HarnessError("self-test: user/agent split does not sum to standing")
        record_decision(project, "liked.but.weak", "proposed", 1, "user click", [],
                        source="user", sentiment="like")
        flagged = ledger_stats(load_decisions(output))
        if "liked.but.weak" not in flagged["conflicts"]:
            raise HarnessError("self-test: like-with-low-stars conflict not surfaced")
        if flagged["likes"] < 1:
            raise HarnessError("self-test: like not counted")

        # embed must supply the graphic, and must refuse to guess a placement.
        session = project / ".superpowers" / "brainstorm" / "s1" / "content"
        session.mkdir(parents=True)
        screen = session / "proto.html"
        screen.write_text('<html><head></head><body><h1>fichas</h1>'
                          '<div data-dh-controls="cover.layout.two-column"></div>'
                          '</body></html>', encoding="utf-8")
        if embed_controls(project, screen) != 1:
            raise HarnessError("self-test: embed did not fill the placeholder")
        embedded = screen.read_text(encoding="utf-8")
        for needed in ('class="dh-shot"', 'data-rank="0"', 'data-verdict="approved"',
                       'data-sentiment="like"', 'data-sentiment="dislike"'):
            if needed not in embedded:
                raise HarnessError(f"self-test: embedded row missing {needed}")
        screen.write_text("<html><body>no placeholder</body></html>", encoding="utf-8")
        try:
            embed_controls(project, screen)
        except HarnessError:
            pass
        else:
            raise HarnessError("self-test: embed accepted a screen with no placeholder")

        # publish must win the newest-mtime race by a clear margin, not a tie.
        screen.write_text('<html><body><div data-dh-controls="cover.layout.two-column"></div></body></html>',
                          encoding="utf-8")
        rival = session / "rival.html"
        rival.write_text("<html><body>rival</body></html>", encoding="utf-8")
        publish_screen(project, screen)
        gap = screen.stat().st_mtime - rival.stat().st_mtime
        if gap < 2:
            raise HarnessError(f"self-test: publish left a {gap:.1f}s race with another screen")

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
    decide.add_argument("--preview", default="", help="project-relative graphic of the element being ranked")
    decide.add_argument("--source", default="agent", choices=SOURCES,
                        help="agent (capped at 1 star) or user (only via adopt)")
    adopt = subcommands.add_parser("adopt", help="fold companion star ranks into the ledger")
    adopt.add_argument("--project-root", required=True, type=Path)
    adopt.add_argument("--companion-ledger", required=True, type=Path,
                       help="path to the companion's durable decisions.jsonl")
    controls = subcommands.add_parser("controls", help="emit star + like/dislike controls from the ledger")
    controls.add_argument("--project-root", required=True, type=Path)
    controls.add_argument("--out", type=Path, help="write here instead of stdout")
    controls.add_argument("--shot-width", default="", help="preview frame width, e.g. 132px")
    controls.add_argument("--bg", default="", help="background color; declare the corpus palette, don't guess it")
    controls.add_argument("--ink", default="", help="text/border color")
    controls.add_argument("--accent", default="", help="accent color, e.g. the approved family accent")
    controls.add_argument("--font", default="", help="font-family stack")
    preflight = subcommands.add_parser("preflight", help="record observed adapter availability")
    preflight.add_argument("--project-root", required=True, type=Path)
    preflight.add_argument("--available", default="", help="comma-separated capabilities you verified")
    preflight.add_argument("--missing", default="", help="comma-separated capabilities you confirmed absent")
    doctor = subcommands.add_parser("doctor", help="health-check the whole feedback path end to end")
    doctor.add_argument("--project-root", required=True, type=Path)
    embed = subcommands.add_parser("embed", help="fill data-dh-controls placeholders with generated rows")
    embed.add_argument("--project-root", required=True, type=Path)
    embed.add_argument("--screen", required=True, type=Path)
    for token in ("bg", "ink", "accent", "font"):
        embed.add_argument(f"--{token}", default="")
    embed.add_argument("--shot-width", default="")
    publish = subcommands.add_parser("publish", help="make a screen the one the companion serves")
    publish.add_argument("--project-root", required=True, type=Path)
    publish.add_argument("--screen", required=True, type=Path)
    stats = subcommands.add_parser("stats", help="deterministic statistics over the ledger")
    stats.add_argument("--project-root", required=True, type=Path)
    stats.add_argument("--json", action="store_true", help="machine-readable output")
    subcommands.add_parser("self-test")
    return command


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "init":
            output = init_harness(args.project_root, args.source_root, parse_profiles(args.profiles))
            print(output)
        elif args.command == "validate":
            report = validate_harness(args.project_root) or {}
            drift, warns = report.get("corpusDrift", []), report.get("warnings", [])
            print("Ledger is coherent." if not warns else "Ledger is coherent, with notes:")
            for w in warns:
                print(f"  note: {w}")
            if drift:
                print(f"Corpus drift ({len(drift)} file(s)) -- unrelated to the ledger, triage separately:")
                for d in drift[:10]:
                    print(f"  {d}")
            else:
                print("Corpus unchanged.")
        elif args.command == "decide":
            supersedes = [item.strip() for item in args.supersedes.split(",") if item.strip()]
            preview = preview_reference(args.project_root, args.preview) if args.preview else None
            decisions = record_decision(args.project_root, args.element, args.verdict,
                                        args.stars, args.evidence, supersedes, preview,
                                        source=args.source)
            live = [e for e in decisions["elements"] if e["state"] in ("approved", "proposed")]
            print(f"Recorded {args.element} ({args.verdict}, {args.stars}★). "
                  f"{len(live)} element(s) standing, state={decisions['state']}.")
        elif args.command == "adopt":
            adopted, skipped = adopt_companion(args.project_root, args.companion_ledger)
            print(f"Adopted {adopted} ranked decision(s); skipped {skipped} "
                  f"interaction(s) with no design-element id or usable signal.")
        elif args.command == "preflight":
            split = lambda raw: [i.strip() for i in raw.split(",") if i.strip()]
            matrix = record_preflight(args.project_root, split(args.available), split(args.missing))
            ready = [i["category"] for i in matrix["requiredCapabilities"] if i["available"]]
            blocked = [i["category"] for i in matrix["requiredCapabilities"] if not i["available"]]
            print(f"Available: {', '.join(ready) or 'none'}")
            print(f"Not preflighted or missing: {', '.join(blocked) or 'none'}")
        elif args.command == "embed":
            theme = {t: getattr(args, t) for t in ("bg", "ink", "accent", "font") if getattr(args, t)}
            if args.shot_width:
                theme["shot"] = args.shot_width
            count = embed_controls(args.project_root, args.screen, theme or None)
            print(f"Embedded {count} generated row(s) into {args.screen.name}. "
                  f"Run `publish` to make it the served screen.")
        elif args.command == "publish":
            published = publish_screen(args.project_root, args.screen)
            print(f"Serving {published.name}. Any screen written after this steals the route -- "
                  f"re-run `publish` if you write another.")
        elif args.command == "stats":
            output = args.project_root.resolve(strict=True) / "spec" / "design-harness"
            report = ledger_stats(load_decisions(output))
            if args.json:
                print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
            else:
                bars = "  ".join(f"{n}:{report['histogram'][n]}" for n in sorted(report["histogram"]))
                print(f"standing {report['standing']}  "
                      f"user-set {report['userSet']}  agent-set {report['agentSet']}  "
                      f"coverage {report['coverage']:.0%}")
                print(f"stars    mean {report['meanStars']}  median {report['medianStars']}  [{bars}]")
                print(f"signals  {report['likes']} like  {report['dislikes']} dislike  "
                      f"{report['approved']} approved  {report['rejected']} rejected  "
                      f"{report['superseded']} superseded")
                if report["conflicts"]:
                    print(f"conflict {len(report['conflicts'])}: " + ", ".join(report["conflicts"][:5]))
                if report["unscored"]:
                    print(f"unscored {len(report['unscored'])}: " + ", ".join(report["unscored"][:5]))
        elif args.command == "doctor":
            script = Path(__file__).resolve().parent / "companion_doctor.py"
            return subprocess.call([sys.executable, str(script), str(args.project_root)])
        elif args.command == "controls":
            output = args.project_root.resolve(strict=True) / "spec" / "design-harness"
            theme = {"bg": args.bg, "ink": args.ink, "accent": args.accent,
                     "font": args.font, "shot": args.shot_width}
            markup = render_feedback_controls(load_decisions(output), theme,
                                              args.project_root.resolve(strict=True))
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

