#!/usr/bin/env python3
"""The channel split: `main` drops alpha skills, `alpha` carries them."""
import sys
import subprocess
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fog import (ALPHA_SKILLS, FOG_DIRS, FOG_FILES, FOG_FILES_EXTRA,
                 FOG_GLOBS, is_fog, reasons)
from publish import publish, published_paths
from skill_discovery import catalog


def test() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        fixture = Path(tmp)
        skill = fixture / "first" / "genesis"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\nname: genesis\n---\n")
        records = catalog(fixture)
        assert is_fog("first/genesis/SKILL.md", records=records)
        assert not is_fog("assets/genesis/icon.svg", records=records)
        private = fixture / '.audit' / 'shots' / 'private.json'
        private.parent.mkdir(parents=True)
        private.write_text('{}')
        (fixture / 'NEXT.md').write_text('local plan')
        scratch = fixture / '.scratch' / 'plan.md'
        scratch.parent.mkdir()
        scratch.write_text('local scratch')
        (fixture / 'README.md').write_text('payload')
        subprocess.run(['git', 'init', '-q', str(fixture)], check=True)
        subprocess.run(['git', '-C', str(fixture), 'add', '.'], check=True)
        for channel in ('main', 'alpha'):
            assert '.audit/shots/private.json' not in {
                path.as_posix() for path in published_paths(fixture, channel)}
            out = fixture.parent / f'published-{channel}'
            publish(fixture, out, channel)
            assert (out / 'README.md').is_file()
            assert not (out / 'NEXT.md').exists()
            assert not (out / '.audit').exists()
            assert not (out / '.scratch').exists()

    assert is_fog("first/genesis/SKILL.md")                # alpha skill on main
    assert is_fog("first/genesis/references/architecture.md")
    assert not is_fog("first/genesis/SKILL.md", "alpha")
    assert is_fog("first/aesthetic/AGENTS.md", "alpha")    # fog is still fog on alpha
    assert not is_fog("kit/spanish/ora/SKILL.md")          # stable skills unaffected
    assert not is_fog("first/aesthetic/SKILL.md")          # graduated off alpha, R-59
    assert not is_fog("README.md")

    # Learning artifacts leave on neither channel. R-50 turns on this.
    for channel in ("main", "alpha"):
        assert is_fog("NEXT.md", channel)
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
    rules = set(FOG_FILES + FOG_FILES_EXTRA + FOG_DIRS + FOG_GLOBS
                + ALPHA_SKILLS)
    for rule in sorted(rules):
        assert rule in why, f"{rule} has no reason"
    assert set(why) == rules, f"reasons for no rule: {sorted(set(why) - rules)}"

    # A file nobody committed is a file nobody chose to ship.
    root = Path(__file__).resolve().parents[1]
    stray = root / "test_fog_stray.md"
    stray.write_text("stray\n")
    try:
        for channel in ("main", "alpha"):
            published = {path.as_posix() for path in published_paths(root, channel)}
            assert stray.name not in published, f"{stray.name} reached {channel}"
    finally:
        stray.unlink()
    print("OK")


if __name__ == "__main__":
    test()
