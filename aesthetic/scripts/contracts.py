#!/usr/bin/env python3
"""Directory context contracts.

Every directory carries a CONTEXT.md declaring what it is for, what belongs in
it, what does not, and what it costs. This checker validates one directory
against its own contract and nothing else -- that is what makes the workflow
incremental: change a directory, check that directory, move on.

The bloat this catches is the bloat that already happened once: SKILL.md grew
to 3,200 tokens because nothing declared a budget for it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

CONTRACT_FILE = "CONTEXT.md"
REQUIRED_FIELDS = ("purpose", "admits", "refuses")


@dataclass(frozen=True)
class Report:
    """One directory, judged against its own contract."""
    directory: Path
    purpose: str = ""
    violations: tuple[str, ...] = field(default_factory=tuple)

    @property
    def ok(self) -> bool:
        return not self.violations


def parse_contract(text: str) -> dict[str, str]:
    """Read the leading `---` block as flat `key: value` pairs.

    Deliberately not YAML: a contract that needs a parser dependency is a
    contract nobody writes.
    """
    match = re.match(r"\s*---\s*\n(.*?)\n---", text, re.S)
    if not match:
        return {}
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line and not line.lstrip().startswith("#"):
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    return fields


def check(directory: Path) -> Report:
    """Validate one directory. Never descends -- see `walk`."""
    directory = Path(directory)
    contract_path = directory / CONTRACT_FILE
    if not contract_path.is_file():
        return Report(directory, violations=(
            f"{directory.name or '.'}: no {CONTRACT_FILE} -- "
            "a directory with no declared purpose accumulates whatever lands in it",))

    fields = parse_contract(contract_path.read_text(encoding="utf-8"))
    violations: list[str] = []
    for required in REQUIRED_FIELDS:
        if not fields.get(required):
            violations.append(f"{CONTRACT_FILE} does not declare `{required}`")

    budget = fields.get("max_file_bytes")
    if budget and budget.isdigit():
        limit = int(budget)
        # The contract is exempt from its own budget: it describes the payload,
        # it is not part of it.
        for path in sorted(p for p in directory.iterdir()
                           if p.is_file() and p.name != CONTRACT_FILE):
            size = path.stat().st_size
            if size > limit:
                violations.append(
                    f"{path.name} is {size} bytes, over the {limit} byte budget")

    return Report(directory, fields.get("purpose", ""), tuple(violations))


def walk(root: Path) -> list[Report]:
    """Check `root` and every directory beneath it, one report each, in a fixed
    order so output is comparable between runs."""
    root = Path(root)
    directories = [root] + sorted(
        d for d in root.rglob("*")
        if d.is_dir() and not d.name.startswith((".", "__")))
    return [check(d) for d in directories]


def render(reports: list[Report], root: Path | None = None) -> str:
    """Directories are named by path relative to the first report, so a nested
    `assets/spec` is not mistaken for a top-level `spec`."""
    base = Path(root) if root else (reports[0].directory if reports else Path("."))
    lines = []
    for report in reports:
        try:
            relative = report.directory.relative_to(base)
        except ValueError:
            relative = report.directory
        name = str(relative) if str(relative) != "." else "."
        if report.ok:
            lines.append(f"ok    {name}/  -- {report.purpose}")
        else:
            lines.append(f"FAIL  {name}/")
            lines.extend(f"        {v}" for v in report.violations)
    failed = sum(1 for r in reports if not r.ok)
    lines.append("")
    lines.append(f"{len(reports) - failed}/{len(reports)} directories honour their contract")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    import argparse, sys
    parser = argparse.ArgumentParser(description="check directory context contracts")
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    reports = walk(args.root)
    sys.stdout.write(render(reports))
    return 1 if any(not r.ok for r in reports) else 0


if __name__ == "__main__":
    raise SystemExit(main())
