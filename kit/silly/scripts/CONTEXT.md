---
purpose: the one tool that writes, lists, and removes alias stubs
admits: executable modules and their tests, one concern per module
refuses: anything that edits a real skill; this tool only ever adds and removes its own files
max_file_bytes: 30000
---

# Scripts

Standard library only, `--help` on every entry point, a `test_*.py` beside each
module that runs under `python3 -m unittest`.

`alias.py` runs against a folder full of somebody's installed skills, so most
of its tests are about the writes it declines to make. The `alias_of` key in a
stub's frontmatter is what makes removal safe: `unlink` deletes a directory
only when that key names the skill it points at.
