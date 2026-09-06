---
purpose: the deterministic half of genesis -- state evaluation, topology checks, and action gating
admits: executable modules and their unit tests, one concern per module
refuses: doctrine and architectural philosophy, which stay in SKILL.md and references/
max_file_bytes: 30000
---

# Genesis scripts

Standard library only, `--help` on every entry point, a `test_*.py` beside each
module that runs under `python3 -m unittest`.

`compass.py` owns roadmap parsing, structural validation and Item selection.
Its standalone result is shared with Repo Context, which adds Shot observations
and verified closure. `genesis_flow.py` retains the legacy topology audit;
its next action is a topology recommendation, not Item closure authority.

`SKILL.md` is canonical. The state-machine table there names the files a
project keeps state in, and this module reads that table rather than listing
the paths a second time -- a second list is a lifecycle that drifts. Ordering
stays here, because which gap to close first is behaviour and the table has no
order to read. A path this module names that the doctrine dropped fails
`test_genesis_flow.py`, so drift is a red test rather than a check that
silently never fires.
