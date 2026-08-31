#!/usr/bin/env python3
"""Build and validate the compact project context used by art direction.

`inference_context` is the evidence: what the user said, what they ranked, what
they tagged. Everything below it is the deterministic program that spends that
evidence. `candidates` tags each piece with the four dimensions that must never
collapse into one weight -- priority, workflow role, semantic context, loading
tier -- and `compile_pass` counts it under a named tokenizer profile, packs it
in priority order inside one inference pass budget, and returns a trace naming
why every chunk was admitted or omitted.

Two properties are load-bearing. The same project and profile compile to the
same bytes. And a user correction cannot be displaced by anything below it: a
correction that does not fit raises rather than being dropped quietly.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping


STORE = Path("spec/design-harness")
SKILL_ROOT = Path(__file__).resolve().parent.parent

# The admission order. The index in this tuple IS the priority, so ordering is
# a sort key rather than a chain of comparisons.
PRIORITIES = ("correction", "criterion", "evidence", "instruction", "doctrine")

# Which brief answer is which kind of evidence. The brief already asks the five
# questions; nothing here parses prose to decide what the user meant.
BRIEF_PRIORITY = {
    "fixed": "correction", "out-of-scope": "correction", "done": "criterion",
    "ships": "evidence", "audience": "evidence",
}

TIERS = {"correction": "always", "criterion": "always", "instruction": "always",
         "evidence": "invocation", "doctrine": "conditional"}

# One bounded act inside an attempt, and what it may spend. Declared here so a
# budget is a reviewed number rather than whatever fit on the day.
PASS_BUDGETS = {"intent": 2000, "constraint": 2000, "retrieval": 6000,
                "proposal": 9000, "generation": 12000, "implementation": 9000,
                "verification": 4000}

# An expensive pass waits for the cheapest artifact that would have caught the
# mistake. `golden-rules` is that artifact here: it costs one subprocess.
PROOF_GATE = {"generation": "golden-rules"}

# Estimated profiles, as bytes per token. An exact count comes from a real
# target tokenizer named `hf:<id>`; there is no ratio that can stand in for one.
BYTES_PER_TOKEN = {"bytes/4": 4}
DEFAULT_PROFILE = "bytes/4"
EXACT_PREFIX = "hf:"

# Doctrine, in the order SKILL.md tells an agent to read it. Alphabetical order
# spent a proposal budget on `commands.md` and dropped `golden-rules.md`, which
# is the exact failure this module exists to stop. Anything unnamed follows.
DOCTRINE_ORDER = ("user-communication.md", "golden-rules.md", "loop.md",
                  "interpret-art.md", "anti-slop.md", "sentiment-analysis.md",
                  "graphic-design-fundamentals.md", "editorial-workflow.md",
                  "asset-sourcing.md", "verification.md")

ATTEMPTS_FILE = "inference-attempts.jsonl"
OUTCOMES = ("accepted", "mixed", "rejected")


class DirectionContextError(ValueError):
    pass


def answered_brief(brief: Mapping[str, Any] | None) -> list[dict[str, str]]:
    if not isinstance(brief, Mapping):
        return []
    return [
        {"id": str(item["id"]), "answer": str(item["answer"]).strip()}
        for item in brief.get("answers", [])
        if isinstance(item, Mapping) and item.get("id")
        and str(item.get("answer") or "").strip()
    ]


def load_decisions(project_root: Path) -> Mapping[str, Any]:
    path = Path(project_root) / STORE / "decisions.json"
    if not path.exists():
        return {"elements": []}
    return json.loads(path.read_text(encoding="utf-8"))


def validate_brief_constraints(
        raw: Any, brief: Mapping[str, Any] | None,
        error_type: type[Exception] = DirectionContextError) -> list[dict[str, str]]:
    if not isinstance(raw, list):
        raise error_type("briefConstraints must be a list")
    normalized = []
    for index, item in enumerate(raw):
        if not isinstance(item, Mapping):
            raise error_type(f"briefConstraints[{index}] must be an object")
        values = {}
        for key in ("id", "answer", "impact"):
            value = item.get(key)
            if not isinstance(value, str) or not value.strip():
                raise error_type(
                    f"briefConstraints[{index}].{key} must be non-empty text")
            values[key] = value.strip()
        normalized.append(values)
    snapshot = [{"id": item["id"], "answer": item["answer"]} for item in normalized]
    if snapshot != answered_brief(brief):
        raise error_type(
            "briefConstraints must reproduce every current answered brief item in order")
    return normalized


def inference_context(project_root: Path) -> dict[str, Any]:
    """Current user constraints, feedback, and reference intent; no doctrine."""
    from brief_workflow import load_brief
    from corpus_tags import digest_rows
    from editorial_workflow import WorkflowError, preference_brief

    root = Path(project_root)
    try:
        reference_tags = digest_rows(root)
    except (OSError, WorkflowError):
        reference_tags = []
    return {
        "version": 1,
        "briefConstraints": answered_brief(load_brief(root)),
        "preferences": preference_brief(load_decisions(root)),
        "referenceTags": reference_tags,
    }


def count(text: str, profile: str = DEFAULT_PROFILE) -> tuple[int, bool]:
    """Token cost under one profile, and whether that count is exact.

    A byte ratio is an estimate and says so. One tokenizer never stands in for
    every model, so an exact count names the target tokenizer or is refused.
    """
    if profile.startswith(EXACT_PREFIX):
        return _exact(text, profile[len(EXACT_PREFIX):]), True
    if profile not in BYTES_PER_TOKEN:
        raise DirectionContextError(
            f"unknown tokenizer profile {profile!r}; "
            f"estimated: {', '.join(sorted(BYTES_PER_TOKEN))}, "
            f"exact: {EXACT_PREFIX}<tokenizer id>")
    ratio = BYTES_PER_TOKEN[profile]
    return -(-len(text.encode("utf-8")) // ratio), False


def _exact(text: str, name: str) -> int:
    try:
        from tokenizers import Tokenizer
    except ImportError as exc:
        raise DirectionContextError(
            f"{EXACT_PREFIX}{name} needs the `tokenizers` package, which this "
            f"skill does not ship. Use {DEFAULT_PROFILE} for a count that "
            f"declares itself an estimate.") from exc
    return len(Tokenizer.from_pretrained(name).encode(text).ids)


def _chunk(key: str, priority: str, role: str, text: str, channel: str) -> dict[str, Any]:
    """One candidate, carrying the four dimensions that stay independent."""
    return {"key": key, "priority": priority, "role": role,
            "context": "Design-Inference", "tier": TIERS[priority],
            "channel": channel, "text": text.strip()}


def _doctrine_rank(name: str) -> int:
    return DOCTRINE_ORDER.index(name) if name in DOCTRINE_ORDER else len(DOCTRINE_ORDER)


def candidates(project_root: Path, skill_root: Path = SKILL_ROOT) -> list[dict[str, Any]]:
    """Every piece of context eligible for this project, in admission order.

    The sources are enumerated, never discovered by walking the project. A
    Repo-Dev rail document sitting beside the design work has no route in,
    which is the contamination guard the skill states in prose.
    """
    evidence = inference_context(project_root)
    rows: list[dict[str, Any]] = []

    for item in evidence["briefConstraints"]:
        rows.append(_chunk(f"brief:{item['id']}",
                           BRIEF_PRIORITY.get(item["id"], "evidence"), "evidence",
                           f"{item['id']}: {item['answer']}", "dev-only"))

    for element in evidence["preferences"]["elements"]:
        note = str(element.get("evidence") or "").strip()
        if element.get("sentiment") == "dislike":
            rows.append(_chunk(f"correction:{element['element']}", "correction",
                               "evidence",
                               f"{element['element']}: rejected by the user. {note}",
                               "dev-only"))
        elif element.get("rank"):
            rows.append(_chunk(f"preference:{element['element']}", "evidence",
                               "evidence",
                               f"{element['element']}: ranked {element['rank']}. {note}",
                               "dev-only"))

    for row in evidence["referenceTags"]:
        if row["aspect"] == "untagged":
            body = f"untagged references: {row.get('count', 0)}"
        else:
            body = (f"{row['aspect']}: pursue {row['pursue']}, "
                    f"avoid {row['avoid']}, sketch {row['sketch']}")
        rows.append(_chunk(f"corpus:{row['aspect']}", "evidence", "evidence",
                           body, "dev-only"))

    skill = Path(skill_root) / "SKILL.md"
    if skill.is_file():
        rows.append(_chunk("skill:SKILL.md", "instruction", "instruction",
                           skill.read_text(encoding="utf-8"), "alpha"))

    for path in sorted((Path(skill_root) / "references").glob("*.md")):
        if path.name == "CONTEXT.md":
            continue
        rows.append(_chunk(f"doctrine:references/{path.name}", "doctrine", "reference",
                           path.read_text(encoding="utf-8"), "alpha")
                    | {"rank": _doctrine_rank(path.name)})

    rows.sort(key=lambda row: (PRIORITIES.index(row["priority"]),
                               row.get("rank", 0), row["key"]))
    return rows


def compile_pass(project_root: Path, pass_name: str,
                 profile: str = DEFAULT_PROFILE, budget: int | None = None,
                 proof: tuple[str, ...] = (), force: bool = False,
                 skill_root: Path = SKILL_ROOT) -> dict[str, Any]:
    """Pack one inference pass, and explain every decision that packed it."""
    if pass_name not in PASS_BUDGETS:
        raise DirectionContextError(
            f"unknown inference pass {pass_name!r}; "
            f"one of {', '.join(sorted(PASS_BUDGETS))}")
    required = PROOF_GATE.get(pass_name)
    state = ("not required" if not required else
             "passed" if required in proof else
             "forced" if force else "blocked")
    if state == "blocked":
        raise DirectionContextError(
            f"{pass_name} is gated on {required}; run it and pass "
            f"--proof {required}, or --force to ask for the expensive pass directly")

    limit = PASS_BUDGETS[pass_name] if budget is None else int(budget)
    used, admitted, trace = 0, [], []
    for chunk in candidates(project_root, skill_root):
        tokens, exact = count(chunk["text"], profile)
        fits = used + tokens <= limit
        if fits:
            used += tokens
            admitted.append(chunk["text"])
        elif chunk["priority"] in ("correction", "criterion"):
            raise DirectionContextError(
                f"{chunk['key']} is a {chunk['priority']} costing {tokens} tokens "
                f"and does not fit the {limit} token {pass_name} budget. Raise the "
                f"budget; a correction is never dropped to make room.")
        trace.append({k: chunk[k] for k in
                      ("key", "priority", "role", "context", "tier", "channel")}
                     | {"tokens": tokens, "exact": exact, "admitted": fits,
                        "reason": "admitted in priority order" if fits else
                        f"omitted: optional {chunk['priority']}, {pass_name} budget full"})

    return {"version": 1, "pass": pass_name,
            "profile": {"name": profile, "exact": profile.startswith(EXACT_PREFIX)},
            "budget": limit, "used": used,
            "proofGate": {"requires": required, "state": state},
            "chunks": trace,
            # ponytail: whole chunks only. Truncating a doctrine file mid-clause
            # spends budget on half an argument; omit it and say so instead.
            "bundle": "\n\n".join(admitted) + "\n" if admitted else ""}


def render_trace(trace: Mapping[str, Any]) -> str:
    """The pass trace as a maintainer reads it: budget, spend, and reasons."""
    kind = "exact" if trace["profile"]["exact"] else "estimated"
    lines = [f"{trace['pass']}  {trace['used']}/{trace['budget']} tokens "
             f"({trace['profile']['name']}, {kind})",
             f"proof gate: {trace['proofGate']['state']}",
             ""]
    for row in trace["chunks"]:
        mark = "+" if row["admitted"] else "-"
        lines.append(f"  {mark} {row['key']:<44}{row['tokens']:>7}  "
                     f"{row['priority']:<12}{row['reason']}")
    return "\n".join(lines) + "\n"


def record_attempt(project_root: Path, attempt: Mapping[str, Any]) -> Path:
    """Append one reviewed outcome. Local and dev-only; never published."""
    if attempt.get("outcome") not in OUTCOMES:
        raise DirectionContextError(f"outcome must be one of {', '.join(OUTCOMES)}")
    path = Path(project_root) / STORE / ATTEMPTS_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(attempt, ensure_ascii=False, sort_keys=True) + "\n")
    return path


def _dump(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--pass", dest="pass_name", choices=sorted(PASS_BUDGETS),
                        help="compile this inference pass instead of dumping evidence")
    parser.add_argument("--profile", default=DEFAULT_PROFILE,
                        help=f"tokenizer profile (default {DEFAULT_PROFILE}, estimated)")
    parser.add_argument("--budget", type=int, help="override the declared pass budget")
    parser.add_argument("--proof", action="append", default=[],
                        help="a proof that has passed; repeat for several")
    parser.add_argument("--force", action="store_true",
                        help="run a gated pass anyway, on explicit request")
    parser.add_argument("--trace", type=Path, help="write the compiler trace as JSON")
    args = parser.parse_args()

    try:
        return _run(args)
    except DirectionContextError as refusal:
        print(refusal, file=sys.stderr)
        return 2


def _run(args) -> int:
    if not args.pass_name:
        text = _dump(inference_context(args.project_root))
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(text, encoding="utf-8")
        print(text, end="")
        return 0

    trace = compile_pass(args.project_root, args.pass_name, args.profile,
                         args.budget, tuple(args.proof), args.force)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(trace["bundle"], encoding="utf-8")
    if args.trace:
        args.trace.parent.mkdir(parents=True, exist_ok=True)
        args.trace.write_text(_dump(trace), encoding="utf-8")
    print(render_trace(trace), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
