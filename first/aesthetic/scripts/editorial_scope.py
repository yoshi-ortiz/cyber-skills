#!/usr/bin/env python3
"""Editorial scope: the epic/element spec, its append-only event log, and the burndown read off both.

A seam because scope is the one artifact with history. Everything else in the
harness is a document that gets rewritten; this pairs an immutable event log
with a derived view, and that append-and-replay discipline has no business
leaking into art direction, theme, or corpus."""
from __future__ import annotations

import json
from html import escape as html_escape
from pathlib import Path
from typing import Any, Mapping, Sequence

from burndown_view import BURNDOWN_STYLE
from harness_store import (
    EDITORIAL_FILE, EVENTS_FILE, STORE, WorkflowError,
    _atomic_json, _atomic_text, _read_json, _text,
)

EVENT_STATES = {"unresolved", "resolved", "discarded"}


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
