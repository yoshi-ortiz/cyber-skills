#!/usr/bin/env python3
"""Compile a grounded art-direction inference into an editorial sprint board."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import mimetypes
import os
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


STORE = Path("spec/design-harness")
CORPUS_FILE = "corpus.json"
DIRECTION_FILE = "art-direction.json"
EVENTS_FILE = "editorial-events.jsonl"
DECISIONS_FILE = "decisions.json"
MAX_OUTPUT_BYTES = 40_000
TEXT_SUFFIXES = {".md", ".txt", ".html", ".htm", ".csv", ".json", ".yaml", ".yml"}
IMAGE_SUFFIXES = {".avif", ".gif", ".jpeg", ".jpg", ".png", ".webp"}
SYSTEM_FIELDS = ("palette", "typography", "grid", "hierarchy", "imagery", "voice", "motion")
SCORE_FIELDS = (
    "corpusFit", "subjectSpecificity", "systemCoherence", "distinctiveness",
    "executionLeverage",
)
WORK_STATES = ("backlog", "doing", "review", "done")


class WorkflowError(ValueError):
    """The workflow cannot advance without grounded, valid input."""


@dataclass(frozen=True)
class WorkItem:
    identifier: str
    direction: str
    title: str
    deliverable: str
    points: int
    acceptance: tuple[Mapping[str, str], ...]
    execution_element: str | None


@dataclass(frozen=True)
class EditorialEvent:
    event_id: str
    item: str
    to_state: str
    at: str


@dataclass(frozen=True)
class UserFeedback:
    stars: int
    sentiment: str | None


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise WorkflowError(f"missing required artifact: {path}") from exc
    except json.JSONDecodeError as exc:
        raise WorkflowError(f"invalid JSON in {path}: {exc}") from exc


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


def _kind(path: Path) -> str | None:
    suffix = path.suffix.lower()
    if suffix in IMAGE_SUFFIXES:
        return "image"
    if suffix in TEXT_SUFFIXES:
        return "text"
    return None


def _digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            result.update(block)
    return result.hexdigest()


def _item_id(relative: str, digest: str, kind: str) -> str:
    identity = hashlib.sha256(f"{relative}\0{digest}".encode()).hexdigest()[:12]
    return f"{kind}-{identity}"


def observe_corpus(project_root: Path, source_root: Path) -> dict[str, Any]:
    """Record inspectable image and text material without calling it inference."""
    project_root = Path(project_root).resolve()
    source_root = Path(source_root).resolve()
    if not source_root.is_dir():
        raise WorkflowError(f"corpus is not a directory: {source_root}")
    items: list[dict[str, Any]] = []
    for path in sorted(p for p in source_root.rglob("*") if p.is_file()):
        kind = _kind(path)
        if kind is None:
            continue
        relative = path.relative_to(source_root).as_posix()
        digest = _digest(path)
        item: dict[str, Any] = {
            "id": _item_id(relative, digest, kind),
            "path": relative,
            "kind": kind,
            "mediaType": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
            "bytes": path.stat().st_size,
            "sha256": digest,
            "inspectPath": str(path),
        }
        if kind == "text":
            item["textExcerpt"] = path.read_text(encoding="utf-8", errors="replace")[:4000]
        items.append(item)
    if not items:
        raise WorkflowError("corpus has no supported image or text material")
    packet = {
        "version": 1,
        "root": str(source_root),
        "modalities": sorted({item["kind"] for item in items}),
        "items": items,
    }
    _atomic_json(project_root / STORE / CORPUS_FILE, packet)
    return packet


def _required_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise WorkflowError(f"{label} must be non-empty text")
    return value.strip()


def _required_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise WorkflowError(f"{label} must be a list")
    return value


def _assert_no_agent_stars(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key).lower() in {"stars", "rating", "userstars"}:
                raise WorkflowError("art direction cannot contain user execution stars")
            _assert_no_agent_stars(child)
    elif isinstance(value, list):
        for child in value:
            _assert_no_agent_stars(child)


def _parse_work(raw: Mapping[str, Any], selected: str, direction_ids: set[str]) -> WorkItem:
    identifier = _required_text(raw.get("id"), "work item id")
    direction = _required_text(raw.get("direction"), f"{identifier}.direction")
    if direction not in direction_ids:
        raise WorkflowError(f"{identifier} names unknown direction {direction}")
    if direction != selected:
        raise WorkflowError(f"{identifier} belongs to an alternate direction; park alternates outside the sprint")
    points = raw.get("points")
    if not isinstance(points, int) or isinstance(points, bool) or points <= 0:
        raise WorkflowError(f"{identifier}.points must be a positive integer")
    acceptance_raw = _required_list(raw.get("acceptance"), f"{identifier}.acceptance")
    if not acceptance_raw:
        raise WorkflowError(f"{identifier} needs an observable acceptance check")
    acceptance: list[Mapping[str, str]] = []
    for index, check in enumerate(acceptance_raw):
        if not isinstance(check, Mapping):
            raise WorkflowError(f"{identifier}.acceptance[{index}] must be an object")
        acceptance.append({
            "check": _required_text(check.get("check"), f"{identifier}.acceptance[{index}].check"),
            "evidenceKind": _required_text(
                check.get("evidenceKind"), f"{identifier}.acceptance[{index}].evidenceKind"
            ),
        })
    execution = raw.get("executionElement")
    if execution is not None:
        execution = _required_text(execution, f"{identifier}.executionElement")
    return WorkItem(
        identifier=identifier,
        direction=direction,
        title=_required_text(raw.get("title"), f"{identifier}.title"),
        deliverable=_required_text(raw.get("deliverable"), f"{identifier}.deliverable"),
        points=points,
        acceptance=tuple(acceptance),
        execution_element=execution,
    )


def validate_inference(raw: Any, corpus: Mapping[str, Any]) -> tuple[dict[str, Any], tuple[WorkItem, ...]]:
    """Validate the inference boundary before any project artifact changes."""
    if not isinstance(raw, Mapping):
        raise WorkflowError("direction set must be a JSON object")
    _assert_no_agent_stars(raw)
    directions = _required_list(raw.get("directions"), "directions")
    if len(directions) != 3:
        raise WorkflowError("directions must contain exactly three candidates")
    corpus_items = {item["id"]: item for item in corpus.get("items", [])}
    if not corpus_items:
        raise WorkflowError("corpus has no supported items")

    coverage = raw.get("coverage")
    if not isinstance(coverage, Mapping):
        raise WorkflowError("coverage must record observed and omitted corpus items")
    observed = _required_list(coverage.get("observed"), "coverage.observed")
    omitted_raw = _required_list(coverage.get("omitted"), "coverage.omitted")
    omitted: list[str] = []
    for entry in omitted_raw:
        if not isinstance(entry, Mapping):
            raise WorkflowError("each omitted corpus item needs an id and reason")
        identifier = _required_text(entry.get("corpusItem"), "omitted corpus item")
        _required_text(entry.get("reason"), f"omission reason for {identifier}")
        omitted.append(identifier)
    accounted = observed + omitted
    if len(set(accounted)) != len(accounted) or set(accounted) != set(corpus_items):
        raise WorkflowError("every corpus item must be observed or omitted exactly once")

    direction_ids: set[str] = set()
    places: list[int] = []
    selected = _required_text(raw.get("selected"), "selected")
    signatures: set[str] = set()
    selected_modalities: set[str] = set()
    for index, direction in enumerate(directions):
        if not isinstance(direction, Mapping):
            raise WorkflowError(f"directions[{index}] must be an object")
        identifier = _required_text(direction.get("id"), f"directions[{index}].id")
        if identifier in direction_ids:
            raise WorkflowError(f"duplicate direction id {identifier}")
        direction_ids.add(identifier)
        _required_text(direction.get("name"), f"{identifier}.name")
        thesis = _required_text(direction.get("thesis"), f"{identifier}.thesis")
        signature = _required_text(direction.get("signatureMove"), f"{identifier}.signatureMove")
        structural_key = re.sub(r"\W+", "", thesis + signature).lower()
        if structural_key in signatures:
            raise WorkflowError("directions must be structurally distinct")
        signatures.add(structural_key)

        visual = direction.get("visualSystem")
        if not isinstance(visual, Mapping):
            raise WorkflowError(f"{identifier}.visualSystem must be an object")
        for field in SYSTEM_FIELDS:
            _required_text(visual.get(field), f"{identifier}.visualSystem.{field}")
        scorecard = direction.get("scorecard")
        if not isinstance(scorecard, Mapping):
            raise WorkflowError(f"{identifier}.scorecard must be an object")
        for field in SCORE_FIELDS:
            score = scorecard.get(field)
            if not isinstance(score, int) or isinstance(score, bool) or not 1 <= score <= 5:
                raise WorkflowError(f"{identifier}.scorecard.{field} must be an integer from 1 to 5")
        rank = direction.get("agentRank")
        if not isinstance(rank, Mapping):
            raise WorkflowError(f"{identifier}.agentRank must be an object")
        place = rank.get("place")
        if not isinstance(place, int) or isinstance(place, bool):
            raise WorkflowError(f"{identifier}.agentRank.place must be an integer")
        places.append(place)
        _required_text(rank.get("rationale"), f"{identifier}.agentRank.rationale")

        evidence = _required_list(direction.get("evidence"), f"{identifier}.evidence")
        if not evidence:
            raise WorkflowError(f"{identifier} needs corpus evidence")
        for evidence_index, ref in enumerate(evidence):
            if not isinstance(ref, Mapping):
                raise WorkflowError(f"{identifier}.evidence[{evidence_index}] must be an object")
            item_id = _required_text(ref.get("corpusItem"), "evidence corpus item")
            if item_id not in corpus_items:
                raise WorkflowError(f"{identifier} cites unknown corpus item {item_id}")
            if item_id not in observed:
                raise WorkflowError(f"{identifier} cites corpus item {item_id} without observing it")
            _required_text(ref.get("locator"), f"evidence locator for {item_id}")
            _required_text(ref.get("observation"), f"evidence observation for {item_id}")
            if identifier == selected:
                selected_modalities.add(corpus_items[item_id]["kind"])

    if set(places) != {1, 2, 3}:
        raise WorkflowError("agent ranks must be unique and contiguous from 1 through 3")
    if selected not in direction_ids:
        raise WorkflowError("selected must name one direction")
    available = set(corpus.get("modalities", [])) & {"image", "text"}
    missing = sorted(available - selected_modalities)
    if missing:
        raise WorkflowError(f"selected direction must cite {' and '.join(missing)} evidence")

    sprint = raw.get("sprint")
    if not isinstance(sprint, Mapping):
        raise WorkflowError("sprint must be an object")
    _required_text(sprint.get("name"), "sprint.name")
    _required_text(sprint.get("goal"), "sprint.goal")
    item_values = _required_list(sprint.get("items"), "sprint.items")
    if not item_values:
        raise WorkflowError("sprint must contain at least one work item")
    if len(item_values) > 20:
        raise WorkflowError("sprint cannot contain more than 20 work items")
    work = tuple(_parse_work(item, selected, direction_ids) for item in item_values)
    if len({item.identifier for item in work}) != len(work):
        raise WorkflowError("work item ids must be unique")
    return dict(raw), work


def _events_path(project_root: Path) -> Path:
    return Path(project_root) / STORE / EVENTS_FILE


def load_events(project_root: Path) -> tuple[EditorialEvent, ...]:
    path = _events_path(project_root)
    if not path.exists():
        return ()
    events: list[EditorialEvent] = []
    seen: set[str] = set()
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
            event = EditorialEvent(
                event_id=_required_text(raw.get("eventId"), "eventId"),
                item=_required_text(raw.get("item"), "event item"),
                to_state=_required_text(raw.get("to"), "event state"),
                at=_required_text(raw.get("at"), "event timestamp"),
            )
        except (json.JSONDecodeError, WorkflowError) as exc:
            raise WorkflowError(f"invalid event on line {line_number}: {exc}") from exc
        if event.event_id in seen:
            raise WorkflowError(f"duplicate event id {event.event_id}")
        seen.add(event.event_id)
        events.append(event)
    return tuple(events)


def reduce_events(work: Sequence[WorkItem], events: Sequence[EditorialEvent]) -> tuple[dict[str, str], list[tuple[str, int]]]:
    states = {item.identifier: "backlog" for item in work}
    points = {item.identifier: item.points for item in work}
    remaining = sum(points.values())
    burndown = [("start", remaining)]
    for event in events:
        if event.item not in states:
            raise WorkflowError(f"event names unknown work item {event.item}")
        if event.to_state not in WORK_STATES:
            raise WorkflowError(f"event state must be one of {', '.join(WORK_STATES)}")
        before = states[event.item]
        states[event.item] = event.to_state
        if before != "done" and event.to_state == "done":
            remaining -= points[event.item]
        elif before == "done" and event.to_state != "done":
            remaining += points[event.item]
        burndown.append((event.at, remaining))
    return states, burndown


def load_user_feedback(project_root: Path) -> dict[str, UserFeedback]:
    path = Path(project_root) / STORE / DECISIONS_FILE
    if not path.exists():
        return {}
    raw = _read_json(path)
    result: dict[str, UserFeedback] = {}
    for entry in raw.get("elements", []) if isinstance(raw, Mapping) else []:
        if not isinstance(entry, Mapping):
            continue
        source = entry.get("source")
        user_set = source == "user" or (source in (None, "") and entry.get("scored") is True)
        stars = entry.get("stars")
        element = entry.get("element")
        if user_set and isinstance(element, str) and isinstance(stars, int) and 0 <= stars <= 5:
            sentiment = entry.get("sentiment")
            result[element] = UserFeedback(stars, sentiment if sentiment in {"like", "dislike"} else None)
    return result


def _e(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _work_from_inference(raw: Mapping[str, Any]) -> tuple[WorkItem, ...]:
    selected = str(raw["selected"])
    direction_ids = {str(item["id"]) for item in raw["directions"]}
    return tuple(_parse_work(item, selected, direction_ids) for item in raw["sprint"]["items"])


def render_board(raw: Mapping[str, Any], work: Sequence[WorkItem], events: Sequence[EditorialEvent], feedback: Mapping[str, UserFeedback]) -> str:
    states, burndown = reduce_events(work, events)
    directions = sorted(raw["directions"], key=lambda item: item["agentRank"]["place"])
    selected = next(item for item in directions if item["id"] == raw["selected"])
    remaining = burndown[-1][1]
    done = sum(state == "done" for state in states.values())
    total = len(work)
    direction_cards = "".join(
        f'<article class="direction{" selected" if item["id"] == selected["id"] else ""}">'
        f'<p class="rank">Agent rank {_e(item["agentRank"]["place"])}</p>'
        f'<h3>{_e(item["name"])}</h3><p>{_e(item["thesis"])}</p>'
        f'<p class="reason">{_e(item["agentRank"]["rationale"])}</p></article>'
        for item in directions
    )
    evidence = "".join(
        f'<li><b>{_e(ref["locator"])}</b> {_e(ref["observation"])}</li>'
        for ref in selected["evidence"]
    )
    history = "".join(
        f'<li><span>{_e(at)}</span><b>{points} remaining</b></li>' for at, points in burndown
    )
    columns = []
    for state in WORK_STATES:
        cards = []
        for item in work:
            if states[item.identifier] != state:
                continue
            signal = ""
            if item.execution_element and item.execution_element in feedback:
                value = feedback[item.execution_element]
                mood = f" · {value.sentiment}" if value.sentiment else ""
                signal = f'<p class="feedback">User execution {value.stars}/5{_e(mood)}</p>'
            checks = "".join(f'<li>{_e(check["check"])}</li>' for check in item.acceptance)
            cards.append(
                f'<article class="work"><div class="worktop"><span>{item.points} pt</span>'
                f'<span>{_e(item.identifier)}</span></div><h4>{_e(item.title)}</h4>'
                f'<p>{_e(item.deliverable)}</p><ul>{checks}</ul>{signal}</article>'
            )
        columns.append(
            f'<section class="column"><header><h3>{state.title()}</h3><span>{len(cards)}</span></header>'
            f'{"".join(cards) if cards else "<p class=empty>Clear</p>"}</section>'
        )
    alternatives = "".join(
        f'<li><b>#{_e(item["agentRank"]["place"])} {_e(item["name"])}</b> {_e(item["signatureMove"])}</li>'
        for item in directions if item["id"] != selected["id"]
    )
    markup = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_e(raw["sprint"]["name"])} editorial board</title>
<style>
:root{{--paper:#f4f0e6;--ink:#181712;--accent:#d0442e;--muted:#716d63;--line:#c9c1b1;--panel:#fffdf7}}
*{{box-sizing:border-box}}html,body{{max-inline-size:100%;overflow-x:clip}}body{{margin:0;background:var(--paper);color:var(--ink);font:15px/1.45 ui-sans-serif,system-ui,sans-serif}}
main{{max-inline-size:1500px;min-inline-size:0;margin-inline:auto;padding:clamp(18px,3vw,48px)}}h1,h2,h3,h4,p{{margin-block-start:0;overflow-wrap:anywhere}}h1{{font:900 clamp(42px,8vw,112px)/.83 ui-sans-serif;letter-spacing:-.065em;max-inline-size:10ch}}
.eyebrow,.rank,.worktop{{font:700 11px/1.2 ui-monospace,monospace;text-transform:uppercase;letter-spacing:.08em}}.eyebrow,.rank{{color:var(--accent)}}
.mast{{display:grid;grid-template-columns:minmax(0,2fr) minmax(250px,1fr);gap:clamp(24px,5vw,80px);border-block-end:3px solid var(--ink);padding-block-end:32px}}
.summary{{align-self:end}}.remaining{{font:800 clamp(28px,4vw,58px)/1 ui-sans-serif;letter-spacing:-.04em}}.goal{{max-inline-size:48ch;color:var(--muted)}}
.selected-note{{margin-block:32px;display:grid;grid-template-columns:minmax(0,1fr) minmax(260px,.8fr);gap:32px}}.signature{{font:700 clamp(22px,3vw,38px)/1.05 ui-sans-serif}}
.evidence{{padding:0;list-style:none}}.evidence li{{border-block-start:1px solid var(--line);padding-block:10px}}.evidence b{{display:block;font-size:11px;text-transform:uppercase}}
.directions{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-block:32px}}.direction{{border:1px solid var(--line);padding:18px;background:color-mix(in srgb,var(--panel) 70%,transparent)}}.direction.selected{{border:3px solid var(--ink);background:var(--panel)}}.direction h3{{font-size:22px}}.reason{{color:var(--muted);font-size:13px}}
.progress{{display:grid;grid-template-columns:minmax(0,1fr) minmax(260px,.7fr);gap:24px;align-items:start;margin-block:36px}}.history{{list-style:none;padding:0;margin:0;border-block:1px solid var(--line)}}.history li{{display:flex;justify-content:space-between;gap:12px;padding-block:8px;border-block-end:1px solid var(--line)}}.history li:last-child{{border:0}}.history span{{color:var(--muted)}}
.board{{display:grid;inline-size:100%;max-inline-size:100%;min-inline-size:0;grid-template-columns:repeat(4,minmax(230px,1fr));gap:12px;overflow:auto;scrollbar-gutter:stable;overscroll-behavior-inline:contain;padding-block-end:12px}}.column{{min-inline-size:0;background:color-mix(in srgb,var(--panel) 55%,transparent);border-block-start:5px solid var(--ink);padding:12px}}.column>header{{display:flex;justify-content:space-between}}.column>header span{{font:700 12px ui-monospace}}.work{{background:var(--panel);border:1px solid var(--line);padding:14px;margin-block-end:10px}}.worktop{{display:flex;justify-content:space-between;gap:8px;color:var(--muted)}}.work h4{{font-size:18px;margin-block:18px 6px}}.work ul{{padding-inline-start:18px;color:var(--muted);font-size:13px}}.feedback{{border-block-start:1px solid var(--line);padding-block-start:9px;color:var(--accent);font-weight:800}}.empty{{color:var(--muted);font-style:italic}}
details{{margin-block-start:32px;border-block-start:1px solid var(--line);padding-block-start:14px}}details li{{margin-block:8px}}
@media(max-width:760px){{.mast,.selected-note,.progress{{grid-template-columns:1fr}}.directions{{grid-template-columns:1fr}}h1{{max-inline-size:12ch}}}}
</style></head><body><main>
<header class="mast"><div><p class="eyebrow">{_e(raw["sprint"]["name"])} · editorial sprint</p><h1>{_e(selected["name"])}</h1></div><div class="summary"><p class="remaining">{remaining} points remaining</p><p>{done} of {total} done</p><p class="goal">{_e(raw["sprint"]["goal"])}</p></div></header>
<section class="selected-note"><div><p class="eyebrow">Selected direction · Agent rank {_e(selected["agentRank"]["place"])}</p><h2>{_e(selected["thesis"])}</h2><p class="signature">{_e(selected["signatureMove"])}</p></div><ul class="evidence">{evidence}</ul></section>
<section class="directions" aria-label="Ranked directions">{direction_cards}</section>
<section class="progress"><div><p class="eyebrow">Editorial burndown</p><h2>{remaining} of {sum(item.points for item in work)} points remain</h2></div><ol class="history">{history}</ol></section>
<section class="board" aria-label="Editorial work board">{"".join(columns)}</section>
<details><summary>Parked alternatives</summary><ol>{alternatives}</ol></details>
</main></body></html>'''
    if len(markup.encode("utf-8")) > MAX_OUTPUT_BYTES:
        raise WorkflowError(f"editorial board exceeds {MAX_OUTPUT_BYTES} byte output budget")
    return markup


def publish(project_root: Path, directions_path: Path, out: Path) -> Path:
    """Validate, persist, and render as one fail-closed operation."""
    project_root = Path(project_root).resolve()
    store = project_root / STORE
    corpus = _read_json(store / CORPUS_FILE)
    raw, work = validate_inference(_read_json(Path(directions_path)), corpus)
    direction_path = store / DIRECTION_FILE
    events_path = store / EVENTS_FILE
    if direction_path.exists():
        current = _read_json(direction_path)
        current_body = {k: v for k, v in current.items() if k != "publishedAt"}
        if current_body != raw and load_events(project_root):
            raise WorkflowError("cannot replace art direction after editorial events exist")
        published_at = current.get("publishedAt") if current_body == raw else None
    else:
        published_at = None
    stored = dict(raw)
    stored["publishedAt"] = published_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    markup = render_board(stored, work, load_events(project_root), load_user_feedback(project_root))
    _atomic_json(direction_path, stored)
    if not events_path.exists():
        _atomic_text(events_path, "")
    _atomic_text(Path(out), markup)
    return Path(out)


def advance(project_root: Path, item: str, to_state: str, event_id: str, at: str | None = None) -> bool:
    """Append one stable work-state event. Return False for an exact retry."""
    project_root = Path(project_root).resolve()
    raw = _read_json(project_root / STORE / DIRECTION_FILE)
    work = _work_from_inference(raw)
    if item not in {value.identifier for value in work}:
        raise WorkflowError(f"unknown work item {item}")
    if to_state not in WORK_STATES:
        raise WorkflowError(f"state must be one of {', '.join(WORK_STATES)}")
    existing = load_events(project_root)
    if event_id in {event.event_id for event in existing}:
        return False
    stamp = at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    event = EditorialEvent(event_id, item, to_state, stamp)
    reduce_events(work, (*existing, event))
    path = _events_path(project_root)
    payload = {"eventId": event_id, "item": item, "to": to_state, "at": stamp}
    previous = path.read_text(encoding="utf-8") if path.exists() else ""
    _atomic_text(path, previous + json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    return True


def render_project(project_root: Path, out: Path) -> Path:
    project_root = Path(project_root).resolve()
    raw = _read_json(project_root / STORE / DIRECTION_FILE)
    corpus = _read_json(project_root / STORE / CORPUS_FILE)
    _, work = validate_inference({k: v for k, v in raw.items() if k != "publishedAt"}, corpus)
    markup = render_board(raw, work, load_events(project_root), load_user_feedback(project_root))
    _atomic_text(Path(out), markup)
    return Path(out)


def validate_project(project_root: Path) -> None:
    project_root = Path(project_root).resolve()
    raw = _read_json(project_root / STORE / DIRECTION_FILE)
    corpus = _read_json(project_root / STORE / CORPUS_FILE)
    _, work = validate_inference({k: v for k, v in raw.items() if k != "publishedAt"}, corpus)
    reduce_events(work, load_events(project_root))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    observe = commands.add_parser("observe", help="record inspectable corpus material")
    observe.add_argument("--project-root", type=Path, required=True)
    observe.add_argument("--source-root", type=Path, required=True)
    publish_parser = commands.add_parser("publish", help="validate inference and render the board")
    publish_parser.add_argument("--project-root", type=Path, required=True)
    publish_parser.add_argument("--directions", type=Path, required=True)
    publish_parser.add_argument("--out", type=Path, required=True)
    advance_parser = commands.add_parser("advance", help="move one editorial work item")
    advance_parser.add_argument("--project-root", type=Path, required=True)
    advance_parser.add_argument("--item", required=True)
    advance_parser.add_argument("--to", choices=WORK_STATES, required=True)
    advance_parser.add_argument("--event-id", required=True)
    advance_parser.add_argument("--at")
    output = commands.add_parser("output", help="render the current board")
    output.add_argument("--project-root", type=Path, required=True)
    output.add_argument("--out", type=Path, required=True)
    validate = commands.add_parser("validate", help="validate stored workflow artifacts")
    validate.add_argument("--project-root", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "observe":
            packet = observe_corpus(args.project_root, args.source_root)
            print(args.project_root / STORE / CORPUS_FILE)
            print(f"{len(packet['items'])} supported corpus items")
        elif args.command == "publish":
            print(publish(args.project_root, args.directions, args.out))
        elif args.command == "advance":
            changed = advance(args.project_root, args.item, args.to, args.event_id, args.at)
            print("advanced" if changed else "unchanged")
        elif args.command == "output":
            print(render_project(args.project_root, args.out))
        elif args.command == "validate":
            validate_project(args.project_root)
            print("editorial workflow valid")
    except WorkflowError as exc:
        parser = _parser()
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
