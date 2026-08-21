#!/usr/bin/env python3
"""The checkable subset of the design golden rules.

Source doctrine: references/graphic-design-fundamentals.md. Only rules that can be decided by
machine live here -- a rule that needs taste belongs in references/golden-rules.md
and is enforced by the agent reading it, not by this module.

The point of the split is the benchmark: a decision pinned by a checkable rule
is a decision that does not vary between runs. Everything left FREE is where
output diverges.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

MEASURE_RANGE = (45, 75)          # Arizona accessible-branding guidance
BODY_CONTRAST_MIN = 4.5           # WCAG 2.2 success criterion 1.4.3


GRIDS = ("manuscript", "column", "modular")            # declared skill vocabulary
GESTALT_LAWS = ("proximity", "similarity", "closure",
                "continuity", "figure-ground")          # declared skill vocabulary
REGISTERS = ("icon", "index", "symbol")                 # declared skill vocabulary


@dataclass(frozen=True)
class Check:
    """One rule applied to one value.

    `pinned` is the benchmark's unit, and it is not `ok`. A decision the spec
    declares is one a rule can decide, so it comes out the same on every run --
    even when the rule says it is wrong. A decision left undeclared is free to
    vary, and that variance is what makes output unrepeatable.
    """
    rule: str
    ok: bool
    detail: str
    pinned: bool = True


def _undeclared(rule: str) -> Check:
    return Check(rule, False, "not declared -- free to vary between runs", pinned=False)


def _one_of(rule: str, value: object, allowed: tuple[str, ...]) -> Check:
    if value is None or value == "":
        return _undeclared(rule)
    if value not in allowed:
        return Check(rule, False, f"{value!r} is not one of {', '.join(allowed)}")
    return Check(rule, True, str(value))


def grid(kind: str | None) -> Check:
    """Which grid framework carries the layout. Naming it is the point."""
    return _one_of("grid", kind, GRIDS)


def register(mark: str | None) -> Check:
    """Peirce's triad. A mark that cannot say which one it is has no intent."""
    return _one_of("register", mark, REGISTERS)


def gestalt(laws: list[str] | None) -> Check:
    """Which law does the grouping. Undeclared grouping is accidental grouping."""
    if not laws:
        return _undeclared("gestalt")
    unknown = [l for l in laws if l not in GESTALT_LAWS]
    if unknown:
        return Check("gestalt", False, f"unknown law(s): {', '.join(unknown)}")
    return Check("gestalt", True, ", ".join(laws))


def _luminance(hex_colour: str) -> float:
    """Relative luminance, sRGB. The gamma expansion is not optional -- a naive
    average of the channels gets mid-greys wrong by a factor of two."""
    raw = hex_colour.lstrip("#")
    if len(raw) == 3:
        raw = "".join(c * 2 for c in raw)
    if len(raw) != 6:
        raise ValueError(f"not a hex colour: {hex_colour!r}")
    channels = []
    for offset in (0, 2, 4):
        value = int(raw[offset:offset + 2], 16) / 255
        channels.append(value / 12.92 if value <= 0.03928
                        else ((value + 0.055) / 1.055) ** 2.4)
    red, green, blue = channels
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(foreground: str, background: str) -> float:
    """Value contrast between two colours, 1.0 (none) to 21.0 (black on white)."""
    a, b = _luminance(foreground), _luminance(background)
    lighter, darker = max(a, b), min(a, b)
    return (lighter + 0.05) / (darker + 0.05)


def contrast(foreground: str | None, background: str | None) -> Check:
    """Body text must clear the legibility threshold, not merely look nice."""
    if not foreground or not background:
        return _undeclared("contrast")
    ratio = contrast_ratio(foreground, background)
    ok = ratio >= BODY_CONTRAST_MIN
    return Check("contrast", ok,
                 f"{ratio:.2f}:1 against a {BODY_CONTRAST_MIN} minimum")


def measure(line: str | None) -> Check:
    """Characters per line of body text. Outside 45-75 the eye loses the return."""
    if not line:
        return _undeclared("measure")
    low, high = MEASURE_RANGE
    n = len(line)
    if n < low:
        return Check("measure", False, f"{n} characters per line; below the {low} minimum")
    if n > high:
        return Check("measure", False, f"{n} characters per line; above the {high} maximum")
    return Check("measure", True, f"{n} characters per line")


@dataclass(frozen=True)
class Report:
    """What a design spec pins, and what it leaves to improvisation."""
    checks: tuple[Check, ...]

    @property
    def total(self) -> int:
        return len(self.checks)

    @property
    def pinned(self) -> tuple[Check, ...]:
        return tuple(c for c in self.checks if c.pinned)

    @property
    def free(self) -> list[Check]:
        return [c for c in self.checks if not c.pinned]

    @property
    def failures(self) -> list[Check]:
        return [c for c in self.checks if c.pinned and not c.ok]

    @property
    def coverage(self) -> float:
        """The determinism metric: what fraction of decisions a rule can decide."""
        return len(self.pinned) / self.total if self.total else 0.0

    @property
    def passing(self) -> bool:
        """The quality metric. Independent of coverage, deliberately."""
        return not self.failures


def scaffold(element: str) -> dict:
    """Return a blank spec naming every slot a checkable rule can decide."""
    return {
        "element": element,
        "body": {"sample_line": None, "ink": None, "paper": None},
        "grid": None,
        "gestalt": [],
        "register": None,
        "choices": {
            "grid": list(GRIDS),
            "gestalt": list(GESTALT_LAWS),
            "register": list(REGISTERS),
            "measure": f"{MEASURE_RANGE[0]}-{MEASURE_RANGE[1]} characters per line",
            "contrast": f"body text at or above {BODY_CONTRAST_MIN}:1",
        },
    }


def render(report: Report) -> str:
    """One screen. Coverage first, because it is the metric being moved."""
    pinned = len(report.pinned)
    lines = [f"golden-rule coverage   {pinned}/{report.total}  "
             f"({report.coverage * 100:.0f}%)"]
    for check in report.checks:
        state = "FREE" if not check.pinned else ("PIN " if check.ok else "FAIL")
        arrow = "   <- improvised" if not check.pinned else ""
        lines.append(f"  {check.rule:<10} {state}  {check.detail}{arrow}")
    if report.free:
        lines.append("")
        lines.append(f"unconstrained decisions: {len(report.free)} "
                     f"-> these are where runs diverge")
    return "\n".join(lines) + "\n"


def evaluate(design: dict) -> Report:
    """Apply every checkable rule to a design spec. Order is fixed, so the
    report for a given spec is byte-stable."""
    body = design.get("body") or {}
    return Report((
        measure(body.get("sample_line")),
        contrast(body.get("ink"), body.get("paper")),
        grid(design.get("grid")),
        gestalt(design.get("gestalt")),
        register(design.get("register")),
    ))


def main(argv: list[str] | None = None) -> int:
    import argparse, json, sys
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--design", type=Path,
                        help="JSON design spec to score against the golden rules")
    parser.add_argument("--scaffold", metavar="ELEMENT",
                        help="print a blank spec naming every checkable slot, and exit")
    parser.add_argument("--min-coverage", type=float, default=0.0,
                        help="exit 1 when coverage falls below this (0-1)")
    args = parser.parse_args(argv)
    if args.scaffold:
        sys.stdout.write(json.dumps(scaffold(args.scaffold), indent=2) + "\n")
        return 0
    if not args.design:
        parser.error("pass --design <spec.json> or --scaffold <element>")
    report = evaluate(json.loads(args.design.read_text(encoding="utf-8")))
    sys.stdout.write(render(report))
    return 1 if report.coverage < args.min_coverage else 0


if __name__ == "__main__":
    raise SystemExit(main())
