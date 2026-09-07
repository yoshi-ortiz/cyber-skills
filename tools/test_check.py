#!/usr/bin/env python3
"""A runner that quietly skips a gate is worse than no runner."""
import sys
import tempfile
import unittest.mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check

names = [name for name, _ in check.gates(Path("/tmp/unused"))]

# Every documented gate is on the board. The whole point of the file is that
# the two lists it replaces each missed half the other.
for expected in ("contracts-declared", "contracts-budget",
                 "harness self-test", "index gate", "loanwords",
                 "publish main", "publish alpha"):
    assert expected in names, f"{expected} is not a gate"

# B-023: a test file that no gate runs is the failure this asserts away. Every
# `test_*.py` is either discovered with its directory or run as the script it
# is, and the runner is the one place that has to be true.
covered = {argv[argv.index("-s") + 1] if "discover" in argv else argv[-1]
           for _name, argv in check.gates(Path("/tmp/unused"))}
for path in check.ROOT.rglob("test_*.py"):
    relative = path.relative_to(check.ROOT)
    if any(part.startswith(".") or part == "__pycache__" for part in relative.parts):
        continue
    assert str(relative) in covered or str(relative.parent) in covered, \
        f"{relative} is run by no gate"

# The split is the point: one half is allowed to be red, the other is not, and
# a substring filter of "contracts" must still reach both.
assert [n for n in names if "contracts" in n] == ["contracts-declared", "contracts-budget"]

assert len(set(names)) == len(names), f"two gates share a name: {names}"

for name, argv in check.gates(Path("/tmp/unused")):
    assert all(isinstance(part, str) for part in argv), name

with unittest.mock.patch.object(check, "run", return_value=True) as ran:
    assert check.main([]) == 0
    assert ran.call_count == len(names)

with unittest.mock.patch.object(check, "run", return_value=True) as ran:
    assert check.main(["publish"]) == 0
    assert [c.args[0] for c in ran.call_args_list] == [
        "publish main", "publish alpha", "published tree is fog-free"]

with unittest.mock.patch.object(check, "run", return_value=False):
    assert check.main(["index gate"]) == 1, "a failing gate must fail the run"

assert check.main(["no-such-gate"]) == 2, "an unmatched filter must not report success"

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root / "tools").mkdir()
    (root / "tools" / "test_new_gate.py").write_text("def test(): assert True\n")
    minimal = check.gates(root / "out", root)
    assert "harness self-test" not in {name for name, _ in minimal}
    assert any("test_new_gate.py" in name for name, _ in minimal)

    # Stage 7 / B-023: both supported shapes enter the plan without a hand-edited list.
    orphan = root / "tools" / "test_orphan.py"
    orphan.write_text("def test(): assert True\n")
    unit = root / "feature" / "test_unit.py"
    unit.parent.mkdir()
    unit.write_text("import unittest\nclass Case(unittest.TestCase): pass\n")
    planned = check.test_gates(sys.executable, root)
    assert any(command[-1] == "tools/test_orphan.py" for _name, command in planned)
    assert any("discover" in command and command[command.index("-s") + 1] == "feature"
               for _name, command in planned)

print(f"OK: {len(names)} gates, all named, filtered, and reporting their own failure.")
