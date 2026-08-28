#!/usr/bin/env python3
"""A runner that quietly skips a gate is worse than no runner."""
import sys
import unittest.mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check

names = [name for name, _ in check.gates(Path("/tmp/unused"))]

# Every documented gate is on the board. The whole point of the file is that
# the two lists it replaces each missed half the other.
for expected in ("contracts", "unit tests", "harness self-test", "index gate",
                 "loanwords", "publish main", "publish alpha"):
    assert expected in names, f"{expected} is not a gate"

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

print(f"OK: {len(names)} gates, all named, filtered, and reporting their own failure.")
