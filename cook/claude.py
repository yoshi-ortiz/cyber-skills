"""Claude transcript discovery and text normalization; no verdict authority."""
from __future__ import annotations

import re
from pathlib import Path

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


def text_of(entry: dict) -> tuple[str, list]:
    """One transcript row's prose, and its blocks. The Claude Code shape.

    The only place this package knows what an agent app's rows look like. A
    second app is a second reader here, not a second reader in every caller.
    """
    content = entry.get("message", {}).get("content")
    blocks = content if isinstance(content, list) else []
    if isinstance(content, str):
        return content, blocks
    return " ".join(b.get("text", "") for b in blocks
                    if isinstance(b, dict) and b.get("type") == "text"), blocks


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
