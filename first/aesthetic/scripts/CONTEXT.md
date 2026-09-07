---
purpose: the tools that enforce what SKILL.md would otherwise merely ask for
admits: executable modules and their tests, one concern per module
refuses: prose, fixtures larger than the code under test, vendored dependencies
max_file_bytes: 30000
---

# Scripts

Standard library only. A **command** module answers `--help` and has a
`test_*.py` beside it that runs under `python3 -m unittest`. A **seam** module
carries no CLI, was extracted from a command to keep it under budget, and is
covered through the tests of the command that re-exports it. Demanding a
parser on a data-access seam is ceremony, not coverage.

**Assert on parsed structure, never on a substring of generated output.** A test
that greps a string the generator just built proves the generator meant well and
nothing else. See `../references/verification.md`.

`bootstrap_harness.py` was 216,757 bytes and is now 25,326, re-exporting
thirteen `harness_*` seams. `editorial_workflow.py` was 34,911 and is now the
parser over four seams and a shared store. The deep module is still the ledger;
`init`/`preflight`/`validate` are still scaffolding.

Add to the seam that owns the concern, not to the facade. The facade is a
parser and a re-export block, and it went over budget once by being the easy
place to put things.
