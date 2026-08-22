#!/usr/bin/env python3
"""The project brief, written by the user as a manifesto.

`loop.md` says to infer the subject and its constraints from evidence rather
than interviewing, and asks at most one design question per round. That rule
is about the ROUND, and it stands. This file is a different surface: a small
set of standing questions about what the project has to deliver, answered in
the user's own prose, revisable at any time, and read by every later round as
the thing the work is measured against.

It stores its answers the way the editorial burndown stores scope, because
that pattern has already earned it here: a validated spec file, an
append-only event log keyed by a caller-supplied id so a retry is a no-op,
and a reader that treats an absent spec as "this project has no brief"
rather than as an error.
"""
from __future__ import annotations

import argparse
import json
import sys
from html import escape as html_escape
from pathlib import Path
from typing import Any, Mapping

from editorial_workflow import STORE, WorkflowError, _atomic_json, _atomic_text, _read_json, _text

BRIEF_FILE = "brief.json"
BRIEF_EVENTS_FILE = "brief-events.jsonl"
MAX_ANSWER_CHARS = 4000

# Deliverables first. Each prompt asks for a sentence the user would say out
# loud about their own project, not a field to fill: the answers are read
# back as a manifesto, and a form-shaped question produces form-shaped prose.
# Stored as a list of records rather than fixed keys so the set can grow
# without migrating an existing brief.
PROMPTS: dict[str, tuple[tuple[str, str], ...]] = {
    "en": (
        ("ships", "What are we actually shipping?"),
        ("audience", "Who opens this, and what do they need from it?"),
        ("done", "What does done look like? Name something observable."),
        ("out-of-scope", "What is explicitly NOT in this?"),
        ("fixed", "What cannot move? Brand, format, deadline, platform."),
    ),
    "es": (
        ("ships", "¿Qué vamos a entregar exactamente?"),
        ("audience", "¿Quién lo abre y qué necesita de esto?"),
        ("done", "¿Cómo se ve terminado? Nombra algo observable."),
        ("out-of-scope", "¿Qué queda explícitamente fuera?"),
        ("fixed", "¿Qué no se puede mover? Marca, formato, fecha, plataforma."),
    ),
}
DEFAULT_LANGUAGE = "en"


def prompts_for(language: str | None) -> tuple[tuple[str, str], ...]:
    """The prompt set for a language, falling back rather than failing.

    The prompts are stored INTO the project's own brief, so a Spanish project
    that started with English questions would keep them for its whole life --
    the language has to be resolved once, here, at creation.
    """
    key = (language or DEFAULT_LANGUAGE).strip().lower().split("-")[0]
    return PROMPTS.get(key, PROMPTS[DEFAULT_LANGUAGE])


def default_brief(at: str, language: str | None = None) -> dict[str, Any]:
    """An empty brief with every prompt unanswered."""
    return {
        "version": 1,
        "startedAt": _text(at, "startedAt"),
        "answers": [{"id": key, "prompt": prompt, "answer": ""}
                    for key, prompt in prompts_for(language)],
    }


def validate_brief_spec(raw: Any) -> dict[str, Any]:
    """Normalise a brief, or say exactly which part of it is wrong."""
    if not isinstance(raw, Mapping):
        raise WorkflowError("brief must be an object")
    started = _text(raw.get("startedAt"), "startedAt")
    entries = raw.get("answers")
    if not isinstance(entries, list) or not entries:
        raise WorkflowError("brief.answers must be a non-empty list")
    answers = []
    seen: set[str] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, Mapping):
            raise WorkflowError(f"brief.answers[{index}] must be an object")
        key = _text(entry.get("id"), f"brief.answers[{index}].id")
        if key in seen:
            raise WorkflowError(f"duplicate brief answer {key}")
        seen.add(key)
        prompt = _text(entry.get("prompt"), f"brief.answers[{index}].prompt")
        answer = entry.get("answer") or ""
        if not isinstance(answer, str):
            raise WorkflowError(f"brief.answers[{index}].answer must be text")
        if len(answer) > MAX_ANSWER_CHARS:
            raise WorkflowError(
                f"brief.answers[{index}].answer is {len(answer)} characters, over the "
                f"{MAX_ANSWER_CHARS} limit. A manifesto is a paragraph, not a document.")
        answers.append({"id": key, "prompt": prompt, "answer": answer.strip()})
    return {"version": 1, "startedAt": started, "answers": answers}


def save_brief_spec(project_root: Path, raw: Any) -> dict[str, Any]:
    value = validate_brief_spec(raw)
    root = Path(project_root)
    _atomic_json(root / STORE / BRIEF_FILE, value)
    events = root / STORE / BRIEF_EVENTS_FILE
    if not events.exists():
        _atomic_text(events, "")
    return value


def load_brief(project_root: Path) -> dict[str, Any] | None:
    """The brief as it stands, or None when this project never wrote one."""
    path = Path(project_root) / STORE / BRIEF_FILE
    if not path.exists():
        return None
    return validate_brief_spec(_read_json(path))


def load_brief_events(project_root: Path) -> list[dict[str, Any]]:
    path = Path(project_root) / STORE / BRIEF_EVENTS_FILE
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
            raise WorkflowError(f"invalid brief event on line {line_number}: {exc}") from exc
        identifier = _text(event.get("eventId"), "eventId")
        if identifier in seen:
            raise WorkflowError(f"duplicate brief event {identifier}")
        seen.add(identifier)
        events.append(event)
    return events


def answer_brief(project_root: Path, event: Mapping[str, Any]) -> bool:
    """Record one answer. Returns False when this eventId already landed.

    The event log is the change history: the spec file always holds the
    current answers, and the log holds how they got there, so a brief that
    was rewritten mid-project can still be read back in order.
    """
    root = Path(project_root)
    spec = load_brief(root)
    if spec is None:
        raise WorkflowError(
            f"this project has no {BRIEF_FILE}. Run `brief start` before answering.")
    identifier = _text(event.get("eventId"), "eventId")
    at = _text(event.get("at"), "event.at")
    key = _text(event.get("id"), "event.id")
    answer = event.get("answer") or ""
    if not isinstance(answer, str):
        raise WorkflowError("event.answer must be text")
    known = {item["id"] for item in spec["answers"]}
    if key not in known:
        raise WorkflowError(f"unknown brief answer {key}")
    if identifier in {item["eventId"] for item in load_brief_events(root)}:
        return False
    normalized = {"eventId": identifier, "at": at, "id": key, "answer": answer.strip()}
    path = root / STORE / BRIEF_EVENTS_FILE
    prior = path.read_text(encoding="utf-8") if path.exists() else ""
    _atomic_text(path, prior + json.dumps(normalized, ensure_ascii=False, sort_keys=True) + "\n")
    for item in spec["answers"]:
        if item["id"] == key:
            item["answer"] = normalized["answer"]
    _atomic_json(root / STORE / BRIEF_FILE, validate_brief_spec(spec))
    return True


def brief_progress(spec: Mapping[str, Any]) -> tuple[int, int]:
    """How many prompts carry an answer, out of how many there are."""
    answers = spec["answers"]
    return sum(1 for item in answers if item["answer"]), len(answers)


def next_unanswered(spec: Mapping[str, Any]) -> dict[str, Any] | None:
    """The one prompt to put in front of the user, or None when done.

    One at a time, deliberately. Five questions on screen at once is a form,
    and a form gets skimmed and filled with the shortest thing that dismisses
    it. The brief is only worth having if the answers are considered, so the
    page asks for exactly one and shows what has already been said as the
    manifesto it is building toward.
    """
    for item in spec["answers"]:
        if not item["answer"]:
            return item
    return None


BRIEF_STYLE = """<style>/* dh-brief */
.dh-brief{margin:0 0 var(--s5);border:1px solid var(--dh-rule);border-radius:14px;
 padding:var(--s3) var(--s4)}
.dh-brief > summary{cursor:pointer;list-style:none;display:flex;align-items:baseline;
 gap:var(--s2);flex-wrap:wrap}
.dh-brief > summary::-webkit-details-marker{display:none}
.dh-brief > summary::before{content:"\\25b8";flex:none;font-size:13px;
 transition:transform .12s;color:color-mix(in srgb, currentColor 55%, transparent)}
.dh-brief[open] > summary::before{transform:rotate(90deg)}
.dh-brief > summary:focus-visible{outline:2px solid var(--dh-accent,#d9482a);outline-offset:3px}
.dh-brief-title{font-size:12px;font-weight:700;letter-spacing:.16em;text-transform:uppercase}
.dh-brief-count{font-size:11px;letter-spacing:0;
 color:color-mix(in srgb, var(--dh-ink,#111) 55%, transparent);font-variant-numeric:tabular-nums}
/* The answers read as a manifesto, so they get a measure and a real line
   height rather than the tight metrics of a data table. */
.dh-brief-body{margin:var(--s3) 0 0;display:grid;gap:var(--s3);max-inline-size:68ch}
.dh-brief-item{display:grid;gap:6px}
.dh-brief-prompt{font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;
 color:color-mix(in srgb, var(--dh-ink,#111) 55%, transparent)}
.dh-brief-answer{margin:0;font-size:15px;line-height:1.6}
/* The open question is the only thing here asking for something, so it is
   the only thing that looks like it. */
.dh-brief-asking{padding:var(--s3);border-radius:10px;
 background:color-mix(in srgb, var(--dh-accent,#d9482a) 10%, transparent);
 border:1px solid color-mix(in srgb, var(--dh-accent,#d9482a) 34%, transparent)}
.dh-brief-question{margin:0;font-size:17px;line-height:1.45;font-weight:700;
 letter-spacing:-.01em;text-wrap:balance}
.dh-brief-more{font-size:11px;
 color:color-mix(in srgb, var(--dh-ink,#111) 52%, transparent)}
</style>"""


def render_brief(project_root: Path, txt: Mapping[str, str] | None = None) -> str:
    """The brief as a collapsible section, or nothing at all.

    Absent brief renders as empty string, on the same principle as the
    burndown: a project that never wrote one shows no section rather than an
    empty prompt list nagging from the top of every article.
    """
    try:
        spec = load_brief(project_root)
    except (OSError, WorkflowError):
        return ""
    if spec is None:
        return ""
    words = dict(txt or {})
    answered, total = brief_progress(spec)
    heading = words.get("brief-title", "Project brief")
    counted = words.get("brief-count", "{answered} of {total} answered").format(
        answered=answered, total=total)
    # What has been said already, as prose. These are the manifesto, not a
    # list of completed form fields, so an answered prompt shows its answer
    # and keeps its question small above it.
    items = []
    for entry in spec["answers"]:
        if not entry["answer"]:
            continue
        items.append(
            '<div class="dh-brief-item">'
            f'<span class="dh-brief-prompt">{html_escape(entry["prompt"])}</span>'
            f'<p class="dh-brief-answer">{html_escape(entry["answer"])}</p></div>')
    # Exactly one open question, never the whole set.
    pending = next_unanswered(spec)
    if pending is not None:
        remaining = total - answered - 1
        more = ""
        if remaining > 0:
            more = ('<span class="dh-brief-more">'
                    + html_escape(words.get("brief-more", "{count} more after this")
                                  .format(count=remaining))
                    + "</span>")
        items.append(
            '<div class="dh-brief-item dh-brief-asking">'
            f'<span class="dh-brief-prompt">{html_escape(words.get("brief-now", "Now"))}</span>'
            f'<p class="dh-brief-question">{html_escape(pending["prompt"])}</p>'
            f'{more}</div>')
    # Open while it is still incomplete: an unfinished brief is the one thing
    # on the page the user can act on without waiting for a render.
    state = "" if pending is None else " open"
    return (BRIEF_STYLE
            + f'<details class="dh-brief"{state}>'
            + f'<summary><span class="dh-brief-title">{html_escape(heading)}</span>'
            + f'<span class="dh-brief-count">{html_escape(counted)}</span></summary>'
            + f'<div class="dh-brief-body">{"".join(items)}</div></details>')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    start = sub.add_parser("start", help="create an empty brief for this project")
    start.add_argument("--project-root", required=True, type=Path)
    start.add_argument("--at", required=True, help="ISO 8601 timestamp")
    start.add_argument("--lang", default="", help="prompt language, e.g. es")
    answer = sub.add_parser("answer", help="record one answer (idempotent by --event-id)")
    answer.add_argument("--project-root", required=True, type=Path)
    answer.add_argument("--event-id", required=True)
    answer.add_argument("--at", required=True, help="ISO 8601 timestamp")
    answer.add_argument("--id", required=True, help="which prompt this answers")
    answer.add_argument("--answer", required=True)
    show = sub.add_parser("show", help="print the brief as JSON")
    show.add_argument("--project-root", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.command == "start":
            spec = save_brief_spec(
                args.project_root, default_brief(args.at, args.lang or None))
            answered, total = brief_progress(spec)
            print(f"Brief started: {total} prompts, {answered} answered.")
        elif args.command == "answer":
            changed = answer_brief(args.project_root, {
                "eventId": args.event_id, "at": args.at,
                "id": args.id, "answer": args.answer})
            print(json.dumps({"changed": changed}))
        elif args.command == "show":
            spec = load_brief(args.project_root)
            print(json.dumps(spec, indent=2, ensure_ascii=False, sort_keys=True)
                  if spec else "null")
    except (WorkflowError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
