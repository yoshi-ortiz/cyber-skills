#!/usr/bin/env python3
"""Read a skill run back against what the user said about it.

`doctor` proves a screen is servable. It cannot see that the designer already
called the round broken, because that lives in the agent's transcript and in
whatever the run changed on disk, not in the served HTML.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from pathlib import Path

from errors import CookError
from interval import invocations, latest_run, pick, text_of, touched_between

TOKENS_QA = (Path(__file__).resolve().parents[1]
             / "check" / "tokens-qa" / "scripts" / "tokens_qa.py")
EXIT = {1: "a hard veto", 2: "schema or arguments", 3: "I/O",
        4: "a write conflict", 5: "an adapter or subprocess failure"}

# Claude Code's transcript directory. Only this one is wired in, because it is
# the only layout with a session here to test against; every other agent app
# arrives through --session rather than through a guess about its filesystem.
SESSIONS = Path.home() / ".claude" / "projects"

NOT_A_USER_TURN = ("base directory for this skill:", "<command-name>",
                   "<local-command", "<command-message>")
ANSWERED = re.compile(r'The user answered: "[^"]*"="([^"]*)"')
COMMAND_ARGS = re.compile(r"<command-args>(.*?)</command-args>", re.S)


def session_transcripts(project: Path) -> list[Path]:
    """This project's transcripts, newest first."""
    folder = SESSIONS / str(project.resolve()).replace("/", "-")
    return sorted(folder.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)


def rows_of(transcript: Path) -> Iterator[dict]:
    with transcript.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                yield json.loads(line)
            except ValueError:
                continue


def entries(transcript: Path) -> list[dict]:
    return list(rows_of(transcript))


def selected(transcript: Path, skill: str = "", run_id: str = ""):
    """The one run under audit. Naming a run that is not there is refused."""
    runs = invocations(rows_of(transcript), skill)
    run = pick(runs, run_id)
    if run is None and run_id:
        raise CookError(
            f"{run_id} is not an invocation in {transcript}. Runs there: "
            + (", ".join(r.run_id for r in runs) or "none"))
    return run


def stream_run(transcript: Path, skill: str = "", run_id: str = "") -> Iterator[dict]:
    """The rows inside one invocation, one line at a time."""
    run = selected(transcript, skill, run_id)
    if run is None:
        return
    for index, entry in enumerate(rows_of(transcript)):
        if run.start < index and (run.end < 0 or index < run.end):
            yield entry


def normalized_evidence(transcript: Path, skill: str = "", run_id: str = "") -> dict:
    """The bundle tokens-qa reads: the user's exact words, one run only."""
    run = selected(transcript, skill, run_id)
    return {"transcript": str(transcript), "skill": run.skill if run else "",
            "invoked_at": run.started if run else "",
            "turns": user_turns(stream_run(transcript, skill, run_id)),
            "artifacts": []}


def assess_feedback(bundle: dict) -> dict:
    """tokens-qa's read of what the user said, through its published CLI.

    Cook owns none of this judgement. It used to keep its own frustration and
    correction patterns beside this call, which made the same rules live in two
    places and put one skill's doctrine inside a loop meant for all of them.
    """
    handle, path = tempfile.mkstemp(suffix=".json")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as out:
            json.dump(bundle, out)
        try:
            done = subprocess.run(
                [sys.executable, str(TOKENS_QA), "shot-audit",
                 "--evidence", path, "--json"],
                capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.SubprocessError) as problem:
            raise CookError(f"tokens-qa never ran ({TOKENS_QA}): {problem}") from problem
    finally:
        os.unlink(path)
    try:
        envelope = json.loads(done.stdout)
    except ValueError:
        envelope = {}
    if done.returncode != 0 or not envelope.get("ok"):
        raise CookError(
            f"tokens-qa shot-audit exited {done.returncode} "
            f"({EXIT.get(done.returncode, 'an exit code cook cannot interpret')}): "
            f"{envelope.get('error') or (done.stderr or done.stdout).strip()}")
    return envelope["result"]


def user_turns(rows, after: str = "") -> list[str]:
    """What the user said once the skill was running.

    Answers given through a question tool arrive as tool results rather than
    user turns; dropping them loses exactly the sentence where a designer says
    the round is wrong.
    """
    said: list[str] = []
    for entry in rows:
        if entry.get("type") != "user":
            continue
        if after and str(entry.get("timestamp", "")) < after:
            continue
        text, blocks = text_of(entry)
        text = text.strip()
        # A slash command wraps the user's own sentence in <command-args>, and
        # the whole turn opens with <command-message>, so the marker check below
        # threw the sentence away with the wrapper. That is where a user says
        # "output is useless" when they say it while invoking a skill -- the
        # single most load-bearing turn in the run, dropped for its envelope.
        args = COMMAND_ARGS.search(text)
        if args:
            text = args.group(1).strip()
        if text and not any(m in text.lower()[:120] for m in NOT_A_USER_TURN):
            said.append(text)
        for block in blocks:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                said += ANSWERED.findall(str(block.get("content") or ""))
    # A resend replays the same answer, and one complaint counted twice reads
    # as a designer repeating themselves.
    return list(dict.fromkeys(said))


def tracked_changes(project_root: Path, since: str = "",
                    until: str = "") -> list[str]:
    """What the run touched: uncommitted edits plus commits made during it.

    Uncommitted work alone was wrong -- committing the fix emptied the list and
    a correctly handled round failed as "changed nothing".
    """
    def git(*argv: str) -> list[str]:
        try:
            done = subprocess.run(["git", "-C", str(project_root), *argv],
                                  capture_output=True, text=True, timeout=10)
        except (OSError, subprocess.SubprocessError):
            return []
        return done.stdout.splitlines() if done.returncode == 0 else []

    changed = [line[3:] for line in git("status", "--porcelain") if line[3:]]
    changed = touched_between(project_root, changed, since, until)
    if since:
        # A commit made after the next run began belongs to that run, not this
        # one. Without the ceiling an audited earlier round is credited with
        # every commit that followed it.
        window = ["--oneline", f"--since={since}"]
        changed += git("log", *window, *([f"--until={until}"] if until else []))
    return changed


def resolve_transcript(project_root: Path, given: Path | None) -> Path:
    """The newest transcript in which a skill actually ran."""
    if given is not None:
        return given
    for candidate in session_transcripts(project_root):
        if latest_run(rows_of(candidate))[0]:
            return candidate
    raise CookError(
        f"no transcript for {project_root} under {SESSIONS} in which a skill ran; "
        "there is no record of what the user asked a skill to do, so this proves "
        "nothing. Pass --session if your agent app keeps transcripts elsewhere.")


def feedback(project_root: Path, transcript: Path | None = None,
             run_id: str = "") -> dict:
    """Did the run change anything after the user said it was wrong?"""
    path = resolve_transcript(project_root, transcript)
    run = selected(path, "", run_id)
    evidence = normalized_evidence(path, "", run_id)
    skill, started, said = evidence["skill"], evidence["invoked_at"], evidence["turns"]
    audit = assess_feedback(evidence)
    complaints, corrections = audit["complaints"], audit["corrections"]
    restated = audit["restated"]
    changed = tracked_changes(project_root, since=started,
                              until=run.ended if run else "")

    errors = []
    if (complaints or corrections) and not changed:
        errors.append(
            f"{len(complaints)} complaint(s) and {len(corrections)} correction(s) "
            f"while `{skill or 'a skill'}` was running, and nothing changed in the "
            "working tree or in commits since it started. The run absorbed the "
            "words and edited nothing.")
    for text in restated:
        errors.append(
            "an instruction was restated after already being given, so the run did "
            f"not act on it the first time: {text[:220]!r}")
    return {"transcript": str(path), "skill": skill, "since": started,
            "run_id": run.run_id if run else "",
            "userTurns": len(said), "complaints": complaints,
            "corrections": corrections, "restated": restated, "changed": changed,
            "warnings": [f"{c['field']} = {c['value']} ({c['confidence']})"
                         for c in audit["candidates"]],
            "errors": errors, "passed": not errors}
