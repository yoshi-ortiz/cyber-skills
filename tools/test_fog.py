#!/usr/bin/env python3
"""The channel split: `main` drops alpha skills, `alpha` carries them."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fog import (ALPHA_SKILLS, FOG_DIRS, FOG_FILES, FOG_FILES_EXTRA,
                 FOG_GLOBS, is_fog, reasons)


def test() -> None:
    assert is_fog("first/genesis/SKILL.md")                # alpha skill on main
    assert is_fog("first/genesis/references/architecture.md")
    assert not is_fog("first/genesis/SKILL.md", "alpha")
    assert is_fog("first/aesthetic/AGENTS.md", "alpha")    # fog is still fog on alpha
    assert not is_fog("kit/spanish/ora/SKILL.md")          # stable skills unaffected
    assert not is_fog("first/aesthetic/SKILL.md")          # graduated off alpha, R-59
    assert not is_fog("README.md")

    # Learning artifacts leave on neither channel. R-50 turns on this.
    for channel in ("main", "alpha"):
        assert is_fog("spec/design-harness/inference-attempts.jsonl", channel)
        assert is_fog("first/aesthetic/scripts/inference-trace.json", channel)
        assert is_fog("spec/design-harness/context-tags-inbox.jsonl", channel)
        assert is_fog(".claude/skills/check-transformers-neural-network/SKILL.md", channel)
        assert is_fog("spec/design-harness/brief.json", channel)
        assert is_fog(".superpowers/brainstorm/.server.pid", channel)
        assert is_fog("shots/landing.hero.flow.desktop.png", channel)
    # The preview and everything it needs are development tooling.
    assert is_fog("tools/trace_preview.py", "alpha")
    assert is_fog("tools/trace_preview.html", "alpha")
    # The compiler itself is skill payload and ships with the skill.
    assert not is_fog("first/aesthetic/scripts/direction_context.py", "alpha")
    assert is_fog("first/aesthetic/scripts/test_direction_context.py", "alpha")

    # Every rule can say why it exists; a rule with no reason prints
    # "development state" at the one moment someone needs the real answer.
    why = reasons()
    for rule in (FOG_FILES + FOG_FILES_EXTRA + FOG_DIRS + FOG_GLOBS
                 + ALPHA_SKILLS):
        assert rule in why, f"{rule} has no reason"
    print("OK")


if __name__ == "__main__":
    test()
