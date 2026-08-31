#!/usr/bin/env python3
"""Read a skill run back against what the user said about it.

`doctor` proves a screen is servable. It cannot see that the designer already
called the round broken, because that lives in the agent's transcript and in
whatever the run changed on disk, not in the served HTML.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from errors import CookError

# Claude Code's transcript directory. Only this one is wired in, because it is
# the only layout with a session here to test against; every other agent app
# arrives through --session rather than through a guess about its filesystem.
SESSIONS = Path.home() / ".claude" / "projects"

# The marker a skill's payload opens with. It is not something the user said,
# so it is skipped as a turn -- but it names the skill directory that ran,
# which is what scopes this whole read.
SKILL_MARKER = re.compile(r"Base directory for this skill: (\S+)")
NOT_A_USER_TURN = ("base directory for this skill:", "<command-name>",
                   "<local-command", "<command-message>")
ANSWERED = re.compile(r'The user answered: "[^"]*"="([^"]*)"')
# ponytail: English keywords. Only ever consulted together with "and nothing
# changed", so a false positive cannot fail a round on its own.
FRUSTRATION = ("broken", "fucked", "dafuq", "wtf", "doesn't work", "does not work",
               "garbage", "useless", "terrible", "all wrong", "no sirve", "roto")

# A correction is stronger evidence than frustration: it names an instruction
# the run did not follow. "It's broken" is a symptom; "I asked for X" is a
# requirement still outstanding.
CORRECTION = tuple(re.compile(p, re.I) for p in (
    r"\byou (did ?n[o']?t|didn't|never|forgot|failed to|were supposed)",
    r"\bi (initially |already |actually |just )?(asked|requested|told you|said)\b",
    r"\bnot what i\b",
    r"\bshould (not |n't )?(be|stick|have|follow|take)\b",
    r"\binstead of\b",
))
# Words too common to prove two corrections are the same instruction.
COMMON = {"should", "would", "could", "that", "this", "with", "from", "have",
          "just", "like", "also", "your", "make", "sure", "want", "need",
          "skill", "thing", "only", "does", "what", "when", "then", "they"}


def session_transcripts(project: Path) -> list[Path]:
    """This project's transcripts, newest first."""
    folder = SESSIONS / str(project.resolve()).replace("/", "-")
    return sorted(folder.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)


def entries(transcript: Path) -> list[dict]:
    out = []
    for line in transcript.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def text_of(entry: dict) -> tuple[str, list]:
    content = entry.get("message", {}).get("content")
    blocks = content if isinstance(content, list) else []
    if isinstance(content, str):
        return content, blocks
    return " ".join(b.get("text", "") for b in blocks
                    if isinstance(b, dict) and b.get("type") == "text"), blocks


def skill_run(rows: list[dict]) -> tuple[str, str]:
    """The first skill invoked, and when. ('', '') when none ran.

    Everything downstream is scoped to this: complaints before a skill was
    invoked are about something else, and a transcript that never ran one is
    not evidence about a skill at all.
    """
    for entry in rows:
        if entry.get("type") != "user":
            continue
        found = SKILL_MARKER.search(text_of(entry)[0])
        if found:
            return Path(found.group(1).split("\\n")[0]).name, entry.get("timestamp", "")
    return "", ""


def user_turns(rows: list[dict], after: str = "") -> list[str]:
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
        if text and not any(m in text.lower()[:120] for m in NOT_A_USER_TURN):
            said.append(text)
        for block in blocks:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                said += ANSWERED.findall(str(block.get("content") or ""))
    # A resend replays the same answer, and one complaint counted twice reads
    # as a designer repeating themselves.
    return list(dict.fromkeys(said))


def tracked_changes(project_root: Path, since: str = "") -> list[str]:
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
    if since:
        changed += git("log", "--oneline", f"--since={since}")
    return changed


def resolve_transcript(project_root: Path, given: Path | None) -> tuple[Path, list[dict]]:
    """The newest transcript in which a skill actually ran."""
    if given is not None:
        return given, entries(given)
    for candidate in session_transcripts(project_root):
        rows = entries(candidate)
        if skill_run(rows)[0]:
            return candidate, rows
    raise CookError(
        f"no transcript for {project_root} under {SESSIONS} in which a skill ran; "
        "there is no record of what the user asked a skill to do, so this proves "
        "nothing. Pass --session if your agent app keeps transcripts elsewhere.")


def feedback(project_root: Path, transcript: Path | None = None) -> dict:
    """Did the run change anything after the user said it was wrong?"""
    path, rows = resolve_transcript(project_root, transcript)
    skill, started = skill_run(rows)
    said = user_turns(rows, after=started)
    complaints = [t for t in said if any(w in t.lower() for w in FRUSTRATION)]
    corrections = [t for t in said if any(p.search(t) for p in CORRECTION)]
    restated = repeated(corrections)
    changed = tracked_changes(project_root, since=started)

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
            "userTurns": len(said), "complaints": complaints,
            "corrections": corrections, "restated": restated, "changed": changed,
            "errors": errors, "passed": not errors}


def repeated(corrections: list[str], floor: int = 3) -> list[str]:
    """Corrections that restate an earlier one.

    Whether an instruction was *satisfied* is a judgement cook cannot make. That
    the user had to say it twice is a fact, and it is the same evidence: an
    instruction repeated is an instruction that did not land.
    """
    words = [set(re.findall(r"[a-z]{4,}", c.lower())) - COMMON for c in corrections]
    out = []
    for i, later in enumerate(words):
        if any(len(later & earlier) >= floor for earlier in words[:i]):
            out.append(corrections[i])
    return out
