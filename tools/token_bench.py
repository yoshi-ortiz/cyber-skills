#!/usr/bin/env python3
"""Deterministic token-weight benchmark for a skill flow.

Two numbers decide whether a command surface is affordable, and they are not
the same number. `context` is the `description` text a model-invoked skill puts
in front of the model every session. A user-invoked skill declares
`disable-model-invocation: true`, so its description costs zero model context.
`path` is the `SKILL.md` bodies one end-to-end walk actually loads. A design can
be cheap on one and ruinous on the other, which is why a single "size" figure
has never answered the question.

Deterministic means re-runnable: same tree, same numbers, no estimate that
lives only in a document. Compare a flow against a reference flow -- the point
of the exercise is the ratio, not the absolute byte count.

    python3 tools/token_bench.py --root ~/.agents/skills \\
        --flow ask-matt=ask-matt,grill-with-docs,grilling,to-spec,implement,tdd

Bytes, not tokens: the ratio is what carries, and dividing by a constant would
imply a precision no tokenizer-free count has. Roughly 4 bytes per token for
English prose if a token figure is wanted.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

# A stub carries a name and a pointer and no doctrine. The threshold is read
# off the reference implementation rather than chosen: ask-matt's own stubs
# are `grill-with-docs` at 245 bytes and `implement` at 433, and its smallest
# real skill is `handoff` at 879. Anything under this is pointing, not saying.
STUB_MAX_BYTES = 600


def frontmatter_description(text: str) -> str:
    """The declared `description:` value.

    Handles the quoted one-liner and the unquoted run-on both, because the
    installed corpus contains both and undercounting the multi-line form is
    how a survey concludes the tax is smaller than it is.
    """
    block = re.match(r"\s*---\s*\n(.*?)\n---", text, re.S)
    if not block:
        return ""
    found = re.search(r"^description:\s*(.*?)(?=^[a-zA-Z_-]+:|\Z)",
                      block.group(1), re.S | re.M)
    return found.group(1).strip().strip('"') if found else ""


def model_invoked(text: str) -> bool:
    block = re.match(r"\s*---\s*\n(.*?)\n---", text, re.S)
    return not (block and re.search(
        r"^disable-model-invocation:\s*true\s*$", block.group(1), re.M))


def measure(root: Path, names: list[str]) -> list[dict]:
    rows = []
    for name in names:
        path = root / name / "SKILL.md"
        if not path.is_file():
            rows.append({"name": name, "missing": True,
                         "always": 0, "path": 0, "stub": False})
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        total = len(text.encode("utf-8"))
        always = (len(frontmatter_description(text).encode("utf-8"))
                  if model_invoked(text) else 0)
        rows.append({"name": name, "missing": False, "always": always,
                     "path": total, "stub": total <= STUB_MAX_BYTES,
                     "model_invoked": model_invoked(text)})
    return rows


def render(label: str, rows: list[dict]) -> str:
    out = [f"{label}", "-" * len(label)]
    out.append(f"  {'skill':<34}{'context':>9}{'on path':>10}  kind")
    for r in rows:
        if r["missing"]:
            out.append(f"  {r['name']:<34}{'--':>9}{'--':>10}  NOT INSTALLED")
            continue
        kind = ("model " if r["model_invoked"] else "user ") + \
               ("stub" if r["stub"] else "doctrine")
        out.append(f"  {r['name']:<34}{r['always']:>9}{r['path']:>10}  {kind}")
    live = [r for r in rows if not r["missing"]]
    stubs = sum(1 for r in live if r["stub"])
    always = sum(r["always"] for r in live)
    walk = sum(r["path"] for r in live)
    out.append(f"  {'':<34}{'-'*9}{'-'*10}")
    out.append(f"  {'TOTAL':<34}{always:>9}{walk:>10}  "
               f"{len(live)} skills, {stubs} stub")
    out.append(f"  {'':<34}{'':>9}{'':>10}  "
               f"context is paid every session; on-path only when walked")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--root", type=Path, default=Path.home() / ".agents/skills",
                        help="skills directory to measure (default ~/.agents/skills)")
    parser.add_argument("--flow", action="append", default=[], metavar="NAME=a,b,c",
                        help="a named flow; repeat to compare flows")
    args = parser.parse_args(argv)

    if not args.flow:
        parser.error("at least one --flow is required")

    root = args.root.expanduser()
    if not root.is_dir():
        print(f"no such skills root: {root}")
        return 1

    results = []
    for spec in args.flow:
        label, _, members = spec.partition("=")
        if not members:
            parser.error(f"--flow needs NAME=a,b,c, got {spec!r}")
        rows = measure(root, [m.strip() for m in members.split(",") if m.strip()])
        results.append((label, rows))
        print(render(label, rows))
        print()

    if len(results) > 1:
        print("comparison")
        print("----------")
        base_label, base_rows = results[0]
        base = [sum(r[k] for r in base_rows if not r["missing"])
                for k in ("always", "path")]
        for label, rows in results:
            live = [r for r in rows if not r["missing"]]
            a, p = sum(r["always"] for r in live), sum(r["path"] for r in live)
            ratio = "" if label == base_label else (
                f"   {a / base[0]:.2f}x context, {p / base[1]:.2f}x path"
                if base[0] and base[1] else "")
            print(f"  {label:<20}{a:>8} context{p:>10} path{ratio}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
