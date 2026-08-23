#!/usr/bin/env python3
"""The channel split: `main` drops alpha skills, `alpha` carries them."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fog import is_fog


def test() -> None:
    assert is_fog("aesthetic/SKILL.md")                    # KEEP_ALWAYS loses to alpha
    assert is_fog("aesthetic/references/loop.md")
    assert not is_fog("aesthetic/SKILL.md", "alpha")
    assert is_fog("aesthetic/AGENTS.md", "alpha")          # fog is still fog on alpha
    assert not is_fog("ora/SKILL.md")                      # stable skills unaffected
    assert not is_fog("README.md")
    print("OK")


if __name__ == "__main__":
    test()
