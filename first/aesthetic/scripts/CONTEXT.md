---
purpose: the tools that enforce what SKILL.md would otherwise merely ask for
admits: executable modules and their tests, one concern per module
refuses: prose, fixtures larger than the code under test, vendored dependencies
max_file_bytes: 30000
---

# Scripts

Standard library only. Every module answers `--help`, and every module has a
`test_*.py` beside it that runs under `python3 -m unittest`.

**Assert on parsed structure, never on a substring of generated output.** A test
that greps a string the generator just built proves the generator meant well and
nothing else. See `../references/verification.md`.

`bootstrap_harness.py` is over budget and known to be. Its CSS and JS now live in
`../screen/`, which took 1,447 lines and 87 KB off it, and what remains is Python
behind a 13-verb interface. The deep module inside it is the ledger;
`init`/`preflight`/`validate` are scaffolding. Split it before adding to it.
