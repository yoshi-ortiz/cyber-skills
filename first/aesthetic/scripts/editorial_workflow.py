#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import re
import tempfile
from html import escape as html_escape
from pathlib import Path
from typing import Any, Mapping, Sequence

from asset_contract import AssetError, validate_assets
from burndown_view import BURNDOWN_STYLE
from direction_context import load_decisions, validate_brief_constraints


STORE = Path("spec/design-harness")
CORPUS_FILE = "corpus.json"
EDITORIAL_FILE = "editorial.json"
EVENTS_FILE = "editorial-events.jsonl"
THEME_FILE = "theme.json"
DECISIONS_FILE = "decisions.json"
ART_DIRECTION_FILE = "art-direction.json"
TEXT_SUFFIXES = {".md", ".txt", ".html", ".htm", ".csv", ".json", ".yaml", ".yml"}
IMAGE_SUFFIXES = {".avif", ".gif", ".jpeg", ".jpg", ".png", ".webp"}
VAGUE_LABEL = re.compile(r"\b(clean|modern|bold|editorial|premium)\b", re.I)
# A premise is inference, so it must cite doctrine that exists outside this run.
KNOWN_BASES = {
    "graphic-design-fundamentals", "aesthetics-philosophy", "art-history", "golden-rules",
    "frontend-layout", "art-direction", "motion", "composition",
    "physical-space", "product-design", "copywriting", "mockup-layering",
}
EVENT_STATES = {"unresolved", "resolved", "discarded"}
DEFAULT_THEME = {
    "bg": "#f5f5f7",
    "ink": "#1d1d1f",
    "accent": "#0066cc",
    "font": "system-ui, sans-serif",
}

class WorkflowError(ValueError):
    pass


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _atomic_json(path: Path, value: Any) -> None:
    _atomic_text(path, json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n")


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise WorkflowError(f"missing required artifact: {path}") from exc
    except json.JSONDecodeError as exc:
        raise WorkflowError(f"invalid JSON in {path}: {exc}") from exc


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise WorkflowError(f"{label} must be non-empty text")
    return value.strip()


def preference_state(entry: Mapping[str, Any]) -> str:
    sentiment = entry.get("sentiment")
    ranked = entry.get("source") == "user" and entry.get("scored") is True
    stars = int(entry.get("stars") or 0)
    if ranked and sentiment == "like":
        return "anchor" if stars >= 3 else "polish"
    if ranked and sentiment == "dislike":
        return "conflict" if stars >= 3 else "discard"
    if sentiment == "like":
        return "direction-like"
    if sentiment == "dislike":
        return "direction-dislike"
    if ranked:
        return "strong-execution" if stars >= 3 else "weak-execution"
    return "explore"


def preference_brief(decisions: Mapping[str, Any]) -> dict[str, Any]:
    elements = []
    user_ranked = 0
    for entry in sorted(decisions.get("elements", []), key=lambda item: str(item.get("element", ""))):
        if not isinstance(entry, Mapping) or not isinstance(entry.get("element"), str):
            continue
        ranked = entry.get("source") == "user" and entry.get("scored") is True
        user_ranked += int(ranked)
        item = {
            "element": entry["element"],
            "preferenceState": preference_state(entry),
            "rank": int(entry.get("stars") or 0) if ranked else None,
            "sentiment": entry.get("sentiment") if entry.get("sentiment") in {"like", "dislike"} else None,
            "lifecycle": entry.get("state") or "proposed",
            "rankProvenance": entry.get("source") if ranked else None,
            "preview": entry.get("preview"),
            "evidence": entry.get("evidence") or "",
        }
        elements.append(item)
    total = len([item for item in decisions.get("elements", []) if isinstance(item, Mapping)])
    return {
        "version": 1,
        "coverage": {"userRanked": user_ranked, "elements": total,
                     "fraction": user_ranked / total if total else 0},
        "elements": elements,
    }


def validate_art_direction(raw: Any, corpus: Mapping[str, Any],
                           preferences: Mapping[str, Any],
                           accountable: Any = None,
                           brief: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Validate direction evidence; accountable may group tagged references."""
    if not isinstance(raw, Mapping):
        raise WorkflowError("art direction must be an object")

    def prohibit(value: Any, path: str = "root") -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                if str(key).lower() in {"average", "reward", "overallscore", "totalscore"}:
                    raise WorkflowError(f"{path}.{key}: averages and reward scores are forbidden")
                prohibit(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                prohibit(child, f"{path}[{index}]")
    prohibit(raw)

    normalized_constraints = validate_brief_constraints(
        raw.get("briefConstraints", []), brief, WorkflowError)

    corpus_ids = {item.get("id") for item in corpus.get("items", []) if isinstance(item, Mapping)}
    try:
        assets = validate_assets(raw.get("assets"), corpus_ids)
    except AssetError as exc:
        raise WorkflowError(str(exc)) from exc
    preference_ids = {item.get("element") for item in preferences.get("elements", [])
                      if isinstance(item, Mapping)}
    # A project with no reference folder still gets to direct the work. It
    # argues from declared premises instead, and the grounding says which.
    seeded = not corpus_ids
    premises = raw.get("premises", [])
    if not isinstance(premises, list):
        raise WorkflowError("premises must be a list")
    if premises and not seeded:
        raise WorkflowError("premises are inference; a real corpus must be cited as observations")
    normalized_premises = []
    if seeded:
        if not premises:
            raise WorkflowError("a seeded corpus needs premises: declare what you are directing from")
        for index, premise in enumerate(premises):
            if not isinstance(premise, Mapping):
                raise WorkflowError(f"premises[{index}] must be an object")
            basis = _text(premise.get("basis"), f"premises[{index}].basis")
            if basis not in KNOWN_BASES:
                raise WorkflowError(f"unknown premise basis {basis}")
            claim = _text(premise.get("claim"), f"premises[{index}].claim")
            if VAGUE_LABEL.search(claim):
                raise WorkflowError("premise claim must name an observable relationship")
            counter = premise.get("counterevidence")
            if not isinstance(counter, list) or not counter:
                raise WorkflowError("premise must state counterevidence")
            normalized_premises.append({"basis": basis, "claim": claim,
                                        "counterevidence": [str(item) for item in counter]})

    observations = raw.get("observations", [])
    if not isinstance(observations, list):
        raise WorkflowError("observations must be a list")
    if seeded and observations:
        raise WorkflowError("a seeded corpus has nothing to observe; use premises")
    if not seeded and not observations:
        raise WorkflowError("art direction needs corpus observations")
    seen_corpus: set[str] = set()
    normalized_observations = []
    for index, observation in enumerate(observations):
        if not isinstance(observation, Mapping):
            raise WorkflowError(f"observations[{index}] must be an object")
        corpus_id = _text(observation.get("corpusItem"), f"observations[{index}].corpusItem")
        if corpus_id not in corpus_ids:
            raise WorkflowError(f"unknown corpus item {corpus_id}")
        seen_corpus.add(corpus_id)
        normalized_observations.append({
            "corpusItem": corpus_id,
            "locator": _text(observation.get("locator"), f"observations[{index}].locator"),
            "observation": _text(observation.get("observation"), f"observations[{index}].observation"),
        })
    omissions = raw.get("omissions", [])
    if not isinstance(omissions, list):
        raise WorkflowError("omissions must be a list")
    normalized_omissions = []
    for index, omission in enumerate(omissions):
        if not isinstance(omission, Mapping):
            raise WorkflowError(f"omissions[{index}] must be an object")
        corpus_id = _text(omission.get("corpusItem"), f"omissions[{index}].corpusItem")
        if corpus_id not in corpus_ids:
            raise WorkflowError(f"unknown corpus item {corpus_id}")
        if corpus_id in seen_corpus:
            raise WorkflowError(f"corpus item {corpus_id} is both observed and omitted")
        seen_corpus.add(corpus_id)
        normalized_omissions.append({"corpusItem": corpus_id,
                                     "reason": _text(omission.get("reason"), "omission.reason")})
    # Untagged projects account for every item, as they always have. Once the
    # user has tagged their reference folders, the folder is the unit: one
    # observation inside it accounts for it. A 135-item corpus was costing 127
    # boilerplate omissions per round, rewritten every time.
    missing = (sorted(str(item) for item in corpus_ids - seen_corpus)
               if accountable is None else accountable(seen_corpus))
    if missing:
        raise WorkflowError("unaccounted corpus items: " + ", ".join(missing))

    patterns = raw.get("preferencePatterns")
    if not isinstance(patterns, list):
        raise WorkflowError("preferencePatterns must be a list")
    normalized_patterns = []
    vague = VAGUE_LABEL
    for index, pattern in enumerate(patterns):
        if not isinstance(pattern, Mapping):
            raise WorkflowError(f"preferencePatterns[{index}] must be an object")
        claim = _text(pattern.get("claim"), f"preferencePatterns[{index}].claim")
        if vague.search(claim):
            raise WorkflowError("preference claim must name an observable relationship")
        support = pattern.get("support")
        counter = pattern.get("counterevidence")
        if not isinstance(support, list) or not support:
            raise WorkflowError("preference pattern needs supporting element ids")
        if not isinstance(counter, list):
            raise WorkflowError("preference pattern counterevidence must be a list")
        unknown = [item for item in support + counter if item not in preference_ids]
        if unknown:
            raise WorkflowError("unknown preference element " + str(unknown[0]))
        n = pattern.get("n")
        coverage = pattern.get("coverage")
        confidence = pattern.get("confidence")
        if not isinstance(n, int) or isinstance(n, bool) or n < len(set(support + counter)):
            raise WorkflowError("preference pattern n is inconsistent")
        if not isinstance(coverage, (int, float)) or isinstance(coverage, bool) or not 0 <= coverage <= 1:
            raise WorkflowError("preference pattern coverage must be 0..1")
        if confidence not in {"low", "medium", "high"}:
            raise WorkflowError("preference pattern confidence must be low, medium, or high")
        normalized_patterns.append({"claim": claim, "support": support,
                                    "counterevidence": counter, "n": n,
                                    "coverage": coverage, "confidence": confidence})

    hypotheses = raw.get("hypotheses")
    if not isinstance(hypotheses, list) or not 1 <= len(hypotheses) <= 4:
        raise WorkflowError("art direction needs one to four hypotheses")
    system_keys = ("palette", "typography", "grid", "hierarchy", "imagery", "voice", "motion")
    normalized_hypotheses = []
    ids: set[str] = set()
    signatures: set[str] = set()
    for index, hypothesis in enumerate(hypotheses):
        if not isinstance(hypothesis, Mapping):
            raise WorkflowError(f"hypotheses[{index}] must be an object")
        identifier = _text(hypothesis.get("id"), f"hypotheses[{index}].id")
        signature = _text(hypothesis.get("signatureMove"), f"{identifier}.signatureMove")
        if identifier in ids or signature.lower() in signatures:
            raise WorkflowError("hypotheses need unique ids and signature moves")
        ids.add(identifier); signatures.add(signature.lower())
        system = hypothesis.get("visualSystem")
        if not isinstance(system, Mapping):
            raise WorkflowError(f"{identifier}.visualSystem must be an object")
        normalized_hypotheses.append({
            "id": identifier, "thesis": _text(hypothesis.get("thesis"), f"{identifier}.thesis"),
            "signatureMove": signature,
            "visualSystem": {key: _text(system.get(key), f"{identifier}.{key}") for key in system_keys},
        })

    comparison = raw.get("comparison")
    if not isinstance(comparison, list) or len(comparison) != len(ids):
        raise WorkflowError("comparison needs one row per hypothesis")
    dimensions = ("corpusFit", "preferenceFit", "subjectSpecificity", "coherence", "executionLeverage")
    user_ranked = int(preferences.get("coverage", {}).get("userRanked") or 0)
    compared: set[str] = set()
    normalized_comparison = []
    for row in comparison:
        if not isinstance(row, Mapping) or row.get("hypothesis") not in ids:
            raise WorkflowError("comparison names an unknown hypothesis")
        identifier = str(row["hypothesis"])
        if identifier in compared:
            raise WorkflowError("comparison repeats a hypothesis")
        compared.add(identifier)
        values = {}
        for dimension in dimensions:
            value = row.get(dimension)
            missing_evidence = ((dimension == "corpusFit" and seeded) or
                                (dimension == "preferenceFit" and not user_ranked))
            if missing_evidence:
                if value is not None:
                    raise WorkflowError(
                        f"{identifier}.{dimension} must be null without supporting evidence")
                values[dimension] = None
                continue
            if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 5:
                raise WorkflowError(f"{identifier}.{dimension} must be 1..5")
            values[dimension] = value
        normalized_comparison.append({"hypothesis": identifier, **values,
                                      "tradeoff": _text(row.get("tradeoff"), f"{identifier}.tradeoff")})
    selected = _text(raw.get("selected"), "selected")
    if selected not in ids:
        raise WorkflowError("selected must name a hypothesis")
    cohort = raw.get("cohort")
    if not isinstance(cohort, list) or not 3 <= len(cohort) <= 6 or len(set(cohort)) != len(cohort):
        raise WorkflowError("cohort must contain three to six unique elements")
    # With nothing ranked yet the cohort is necessarily new work. Once the user
    # has ranked anything, the cohort must stay inside that set so a round
    # cannot quietly drift off the elements under judgement.
    if preference_ids:
        unknown_cohort = [item for item in cohort if item not in preference_ids]
        if unknown_cohort:
            raise WorkflowError("unknown cohort element " + str(unknown_cohort[0]))
    return {
        "version": 1, "observations": normalized_observations, "omissions": normalized_omissions,
        "premises": normalized_premises, "grounding": "inference" if seeded else "corpus",
        "preferencePatterns": normalized_patterns, "hypotheses": normalized_hypotheses,
        "comparison": normalized_comparison, "selected": selected,
        "selectionRationale": _text(raw.get("selectionRationale"), "selectionRationale"),
        "cohort": cohort, "assets": assets,
        "briefConstraints": normalized_constraints,
    }


def save_art_direction(project_root: Path, raw: Any) -> dict[str, Any]:
    root = Path(project_root)
    if any((root / STORE / name).is_file()
           for name in ("scene-spec.json", "graphics-manifest.json")):
        raise WorkflowError(
            "graphics project detected; run text_to_graphics.py status instead of direction")
    corpus = _read_json(root / STORE / CORPUS_FILE)
    # Nothing ranked yet is a normal first round, not a missing artifact.
    preferences = preference_brief(load_decisions(root))
    # Imported here, not at module scope: `corpus_tags` imports this module.
    from corpus_tags import load_tags, missing_evidence
    from brief_workflow import load_brief
    tags = load_tags(root)
    value = validate_art_direction(
        raw, corpus, preferences,
        lambda seen: missing_evidence(corpus, tags, seen),
        load_brief(root))
    try:
        validate_assets(value["assets"], {item.get("id") for item in corpus["items"]}, root)
    except AssetError as exc:
        raise WorkflowError(str(exc)) from exc
    _atomic_json(root / STORE / ART_DIRECTION_FILE, value)
    return value


def validate_editorial_spec(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise WorkflowError("editorial spec must be an object")
    epics = raw.get("epics")
    elements = raw.get("elements")
    if not isinstance(epics, list) or not epics:
        raise WorkflowError("editorial spec needs at least one epic")
    if not isinstance(elements, Mapping):
        raise WorkflowError("editorial spec elements must map each element to one primary epic")
    epic_ids: set[str] = set()
    normalized_epics = []
    for index, epic in enumerate(epics):
        if not isinstance(epic, Mapping):
            raise WorkflowError(f"epics[{index}] must be an object")
        identifier = _text(epic.get("id"), f"epics[{index}].id")
        if identifier in epic_ids:
            raise WorkflowError(f"duplicate epic id {identifier}")
        epic_ids.add(identifier)
        normalized_epics.append({
            "id": identifier,
            "title": _text(epic.get("title"), f"{identifier}.title"),
            "critical": bool(epic.get("critical", False)),
        })
    normalized_elements: dict[str, str] = {}
    for element, epic_id in elements.items():
        if not isinstance(element, str) or not element.strip():
            raise WorkflowError("every scoped element needs a stable id")
        if not isinstance(epic_id, str):
            raise WorkflowError(f"{element} must have one primary epic")
        if epic_id not in epic_ids:
            raise WorkflowError(f"{element} names unknown epic {epic_id}")
        normalized_elements[element] = epic_id
    baseline = _text(raw.get("baselineAt"), "baselineAt")
    return {"version": 1, "baselineAt": baseline,
            "epics": normalized_epics, "elements": normalized_elements}


def save_editorial_spec(project_root: Path, raw: Any) -> dict[str, Any]:
    value = validate_editorial_spec(raw)
    _atomic_json(Path(project_root) / STORE / EDITORIAL_FILE, value)
    events = Path(project_root) / STORE / EVENTS_FILE
    if not events.exists():
        _atomic_text(events, "")
    return value


def load_scope_events(project_root: Path) -> list[dict[str, Any]]:
    path = Path(project_root) / STORE / EVENTS_FILE
    if not path.exists():
        return []
    events = []
    seen: set[str] = set()
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise WorkflowError(f"invalid scope event on line {line_number}: {exc}") from exc
        identifier = _text(event.get("eventId"), "eventId")
        if identifier in seen:
            raise WorkflowError(f"duplicate scope event {identifier}")
        seen.add(identifier)
        events.append(event)
    return events


def _validate_event(event: Mapping[str, Any], spec: Mapping[str, Any]) -> dict[str, str]:
    identifier = _text(event.get("eventId"), "eventId")
    at = _text(event.get("at"), "event.at")
    kind = _text(event.get("kind"), "event.kind")
    subject = _text(event.get("id"), "event.id")
    state = _text(event.get("to"), "event.to")
    if kind not in {"epic", "element"}:
        raise WorkflowError("event.kind must be epic or element")
    if state not in EVENT_STATES:
        raise WorkflowError(f"event.to must be one of {', '.join(sorted(EVENT_STATES))}")
    known = ({item["id"] for item in spec["epics"]} if kind == "epic"
             else set(spec["elements"]))
    if subject not in known:
        raise WorkflowError(f"unknown {kind} {subject}")
    return {"eventId": identifier, "at": at, "kind": kind, "id": subject, "to": state}


def append_scope_event(project_root: Path, event: Mapping[str, Any]) -> bool:
    root = Path(project_root)
    spec = validate_editorial_spec(_read_json(root / STORE / EDITORIAL_FILE))
    normalized = _validate_event(event, spec)
    existing = load_scope_events(root)
    if normalized["eventId"] in {item["eventId"] for item in existing}:
        return False
    path = root / STORE / EVENTS_FILE
    prior = path.read_text(encoding="utf-8") if path.exists() else ""
    _atomic_text(path, prior + json.dumps(normalized, ensure_ascii=False, sort_keys=True) + "\n")
    return True


def editorial_burndown(spec_raw: Any, events_raw: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    spec = validate_editorial_spec(spec_raw)
    epic_states = {item["id"]: "unresolved" for item in spec["epics"]}
    element_states = {item: "unresolved" for item in spec["elements"]}

    def point(at: str) -> dict[str, Any]:
        return {
            "at": at,
            "unresolvedEpics": sum(state == "unresolved" for state in epic_states.values()),
            "unresolvedElements": sum(state == "unresolved" for state in element_states.values()),
        }

    points = [point(spec["baselineAt"])]
    seen: set[str] = set()
    for raw in events_raw:
        event = _validate_event(raw, spec)
        if event["eventId"] in seen:
            continue
        seen.add(event["eventId"])
        target = epic_states if event["kind"] == "epic" else element_states
        target[event["id"]] = event["to"]
        points.append(point(event["at"]))
    return {
        "points": points,
        "criticalEpics": [item["id"] for item in spec["epics"] if item["critical"]],
    }


def project_burndown(project_root: Path) -> dict[str, Any] | None:
    root = Path(project_root)
    path = root / STORE / EDITORIAL_FILE
    if not path.exists():
        return None
    return editorial_burndown(_read_json(path), load_scope_events(root))


def render_burndown(project_root: Path) -> str:
    burndown = project_burndown(project_root)
    if not burndown or not burndown.get("points"):
        return ""
    points = burndown["points"]
    latest = points[-1]
    peak_epics = max(1, max(int(point["unresolvedEpics"]) for point in points))
    peak_elements = max(1, max(int(point["unresolvedElements"]) for point in points))

    def steps(key: str, peak: int) -> str:
        return "".join(
            '<i style="block-size:' + str(max(3, round(26 * int(point[key]) / peak)))
            + 'px" aria-hidden="true"></i>' for point in points)

    epics = int(latest["unresolvedEpics"])
    elements = int(latest["unresolvedElements"])
    epic_values = html_escape(", ".join(str(point["unresolvedEpics"]) for point in points))
    element_values = html_escape(", ".join(str(point["unresolvedElements"]) for point in points))
    return "".join([
        BURNDOWN_STYLE,
        '<section class="dh-burndown" aria-labelledby="dh-burndown-title" aria-label="',
        f'Editorial burndown: {epics} unresolved epics; {elements} unresolved elements">',
        '<div><h2 id="dh-burndown-title">Editorial burndown</h2>',
        '<p class="dh-burndown-summary">',
        f'<span><b>{epics}</b> unresolved epics</span>',
        f'<span><b>{elements}</b> unresolved elements</span>',
        '</p></div><dl class="dh-burndown-series">',
        '<div class="dh-burndown-row"><dt>Epics</dt><dd aria-label="Unresolved epics: ',
        epic_values, '">', steps("unresolvedEpics", peak_epics), '</dd></div>',
        '<div class="dh-burndown-row dh-burndown-row-elements"><dt>Elements</dt>',
        '<dd aria-label="Unresolved elements: ', element_values, '">',
        steps("unresolvedElements", peak_elements), '</dd></div>',
        '</dl></section>',
    ])


def _rgb(value: str) -> tuple[int, int, int] | None:
    match = re.fullmatch(r"#([0-9a-fA-F]{6})", str(value).strip())
    if not match:
        return None
    raw = match.group(1)
    return tuple(int(raw[index:index + 2], 16) for index in (0, 2, 4))


def contrast(first: str, second: str) -> float:
    def luminance(value: str) -> float:
        rgb = _rgb(value)
        if rgb is None:
            raise WorkflowError(f"color must be six-digit hex: {value}")
        channels = []
        for channel in rgb:
            scaled = channel / 255
            channels.append(scaled / 12.92 if scaled <= .04045 else ((scaled + .055) / 1.055) ** 2.4)
        return .2126 * channels[0] + .7152 * channels[1] + .0722 * channels[2]
    a, b = luminance(first), luminance(second)
    return (max(a, b) + .05) / (min(a, b) + .05)


def validate_theme_elements(candidate: Mapping[str, Any], safe: Mapping[str, Any] | None = None) -> dict[str, Any]:
    previous = dict(DEFAULT_THEME)
    previous.update({key: value for key, value in (safe or {}).items() if key in previous})
    active = dict(previous)
    errors: list[dict[str, Any]] = []
    requested = {key: candidate.get(key, previous[key]) for key in previous}
    if _rgb(str(requested["bg"])) is None:
        errors.append({"element": "bg", "message": "background must be six-digit hex"})
    else:
        active["bg"] = str(requested["bg"])
    ink_ratio = contrast(str(requested["ink"]), active["bg"]) if _rgb(str(requested["ink"])) else 0
    if ink_ratio < 4.5:
        errors.append({"element": "ink", "message": "text contrast is below 4.5:1",
                       "contrast": round(ink_ratio, 2)})
    else:
        active["ink"] = str(requested["ink"])
    accent_ratio = contrast(str(requested["accent"]), active["bg"]) if _rgb(str(requested["accent"])) else 0
    if accent_ratio < 3:
        errors.append({"element": "accent", "message": "control contrast is below 3:1",
                       "contrast": round(accent_ratio, 2)})
    else:
        active["accent"] = str(requested["accent"])
    font = str(requested["font"]).strip()
    if not font or len(font) > 200 or not re.fullmatch(r"[A-Za-z0-9 ,.'\"_-]+", font):
        errors.append({"element": "font", "message": "font stack is not a safe CSS value"})
    else:
        active["font"] = font
    if contrast(active["ink"], active["bg"]) < 4.5:
        active["bg"] = previous["bg"]
        errors.append({"element": "bg", "message": "background conflicts with the last safe ink"})
    return {"active": active, "errors": errors}


def _theme_spec(project_root: Path) -> dict[str, Any]:
    path = Path(project_root) / STORE / THEME_FILE
    if not path.exists():
        return {"version": 1, "selected": None, "followArtDirection": False, "themes": []}
    value = _read_json(path)
    if not isinstance(value, Mapping) or not isinstance(value.get("themes"), list):
        raise WorkflowError("theme.json has an invalid shape")
    return dict(value)


def save_theme(project_root: Path, mode: str, identifier: str,
               elements: Mapping[str, Any], name: str = "") -> dict[str, Any]:
    if mode not in {"current", "new"}:
        raise WorkflowError("theme save mode must be current or new")
    identifier = _text(identifier, "theme id")
    spec = _theme_spec(project_root)
    by_id = {theme.get("id"): dict(theme) for theme in spec["themes"] if isinstance(theme, Mapping)}
    target_id = spec.get("selected") if mode == "current" and spec.get("selected") else identifier
    if mode == "new" and identifier in by_id:
        raise WorkflowError(f"theme {identifier} already exists")
    prior = by_id.get(target_id, {}).get("elements") or DEFAULT_THEME
    checked = validate_theme_elements(elements, prior)
    by_id[target_id] = {
        "id": target_id,
        "name": name.strip() or by_id.get(target_id, {}).get("name") or target_id,
        "elements": checked["active"],
        "issues": checked["errors"],
    }
    result = {
        "version": 1,
        "selected": target_id,
        "followArtDirection": bool(spec.get("followArtDirection", False)),
        "themes": sorted(by_id.values(), key=lambda item: item["id"]),
    }
    _atomic_json(Path(project_root) / STORE / THEME_FILE, result)
    return result


def set_follow_art_direction(project_root: Path, enabled: bool) -> dict[str, Any]:
    spec = _theme_spec(project_root)
    spec["followArtDirection"] = bool(enabled)
    _atomic_json(Path(project_root) / STORE / THEME_FILE, spec)
    return spec


def selected_theme(project_root: Path) -> dict[str, Any] | None:
    spec = _theme_spec(project_root)
    selected = spec.get("selected")
    for theme in spec["themes"]:
        if theme.get("id") == selected:
            return {"followArtDirection": bool(spec.get("followArtDirection")), **theme}
    return None


def _kind(path: Path) -> str | None:
    if path.suffix.lower() in IMAGE_SUFFIXES:
        return "image"
    if path.suffix.lower() in TEXT_SUFFIXES:
        return "text"
    return None


def seed_corpus_value(profile: str, subject: str) -> dict[str, Any]:
    """An honest stand-in for a corpus the user has not supplied.

    It holds no items on purpose: nothing here may later be cited as if the
    user had shown it to us."""
    if profile not in KNOWN_BASES:
        raise WorkflowError(f"unknown profile {profile}")
    return {"version": 1, "grounding": "inference", "profile": profile,
            "subject": _text(subject, "subject"), "modalities": [], "items": []}


def seed_corpus(project_root: Path, profile: str, subject: str) -> dict[str, Any]:
    path = Path(project_root) / STORE / CORPUS_FILE
    if path.exists():
        raise WorkflowError("corpus already exists; keep it or run observe, never seed over it")
    result = seed_corpus_value(profile, subject)
    _atomic_json(path, result)
    return result


def observe_corpus(project_root: Path, source_root: Path) -> dict[str, Any]:
    root = Path(source_root).resolve()
    if not root.is_dir():
        raise WorkflowError(f"corpus is not a directory: {root}")
    items = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        kind = _kind(path)
        if kind is None:
            continue
        relative = path.relative_to(root).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        item = {
            "id": f"{kind}-{hashlib.sha256((relative + digest).encode()).hexdigest()[:12]}",
            "path": relative, "kind": kind,
            "mediaType": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
            "bytes": path.stat().st_size, "sha256": digest, "inspectPath": str(path),
        }
        if kind == "text":
            item["textExcerpt"] = path.read_text(encoding="utf-8", errors="replace")[:4000]
        items.append(item)
    if not items:
        raise WorkflowError("corpus has no supported image or text material")
    result = {"version": 1, "root": str(root),
              "modalities": sorted({item["kind"] for item in items}), "items": items}
    _atomic_json(Path(project_root) / STORE / CORPUS_FILE, result)
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    observe = commands.add_parser("observe")
    observe.add_argument("--project-root", type=Path, required=True)
    observe.add_argument("--source-root", type=Path, required=True)
    seed = commands.add_parser("seed")
    seed.add_argument("--project-root", type=Path, required=True)
    seed.add_argument("--profile", required=True)
    seed.add_argument("--subject", required=True)
    preferences = commands.add_parser("preferences")
    preferences.add_argument("--project-root", type=Path, required=True)
    preferences.add_argument("--out", type=Path)
    direction = commands.add_parser("direction")
    direction.add_argument("--project-root", type=Path, required=True)
    direction.add_argument("--spec", type=Path, required=True)
    scope = commands.add_parser("scope")
    scope.add_argument("--project-root", type=Path, required=True)
    scope.add_argument("--spec", type=Path, required=True)
    advance = commands.add_parser("advance")
    advance.add_argument("--project-root", type=Path, required=True)
    advance.add_argument("--event", type=Path, required=True)
    status = commands.add_parser("status")
    status.add_argument("--project-root", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "observe":
            result = observe_corpus(args.project_root, args.source_root)
        elif args.command == "seed":
            result = seed_corpus(args.project_root, args.profile, args.subject)
        elif args.command == "preferences":
            result = preference_brief(load_decisions(args.project_root))
            if args.out:
                _atomic_json(args.out, result)
        elif args.command == "direction":
            result = save_art_direction(args.project_root, _read_json(args.spec))
        elif args.command == "scope":
            result = save_editorial_spec(args.project_root, _read_json(args.spec))
        elif args.command == "advance":
            result = {"changed": append_scope_event(args.project_root, _read_json(args.event))}
        else:
            result = project_burndown(args.project_root) or {"points": []}
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    except WorkflowError as exc:
        _parser().error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
