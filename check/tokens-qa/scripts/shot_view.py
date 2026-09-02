"""What one Shot reads as. The verdict, the metrics, and the two columns."""
from __future__ import annotations

import shutil

# QA.md names exactly four. An unlisted finding never blocks compliance.
VETOES = ("scope_breach", "missing_observation_log", "context_derail",
          "ungrounded_corpus_claim")


def verdict(record: dict) -> str:
    """The user decides. L1 and L2 never rescue or override L3."""
    feedback = record["user_feedback"]
    if feedback["status"] in ("corrected", "rejected"):
        return "failed"
    if feedback.get("correction") or feedback.get("sentiment") == "negative":
        return "failed"
    return "accepted" if feedback["status"] == "accepted" else "pending"


def vetoes(record: dict) -> list[str]:
    return [f["id"] for f in record.get("findings", [])
            if f.get("status") == "present" and f["id"] in VETOES]


def totals(record: dict) -> tuple[int | None, str]:
    tokens = record["compute"]["tokens"]
    given = (tokens.get("input"), tokens.get("output"))
    if any(t is None for t in given):
        return None, tokens.get("profile", "unavailable")
    return sum(given), tokens.get("profile", "unavailable")


def metrics(record: dict) -> dict[str, str]:
    total, profile = totals(record)
    admitted = record["inputs"].get("admitted_context")
    contaminated = any(f.get("status") == "present" and
                       f["id"] in ("context_derail", "context_contamination")
                       for f in record.get("findings", []))
    tokens = record["compute"]["tokens"]
    mark = "~" if profile != "exact" else ""
    return {
        "scope": record["scope"],
        "context.status": ("not_observed" if admitted is None
                           else "contaminated" if contaminated else "observed"),
        "hard_vetoes": ", ".join(vetoes(record)) or "none",
        "feedback.status": record["user_feedback"]["status"],
        "feedback.corrections": "1" if record["user_feedback"].get("correction") else "0",
        "tokens.input": f"{mark}{tokens['input']}" if tokens.get("input") is not None else "unavailable",
        "tokens.output": f"{mark}{tokens['output']}" if tokens.get("output") is not None else "unavailable",
        "tokens.total": f"{mark}{total}" if total is not None else "unavailable",
        "tokens.profile": profile,
        "verdict": verdict(record),
    }


ORDER = ("scope", "context.status", "hard_vetoes", "feedback.status",
         "feedback.corrections", "tokens.input", "tokens.output",
         "tokens.total", "tokens.profile", "verdict")


def table(base: dict[str, str], cand: dict[str, str] | None) -> str:
    """Two semantic columns. Two physical rows per metric, never wrapped."""
    width = min(160, max(80, shutil.get_terminal_size((100, 24)).columns))
    left = (width - 3) // 2
    right = width - 3 - left

    def cell(text: str, room: int) -> str:
        room -= 2
        if len(text) > room:
            text = text[:room - 1] + "…" if room >= 2 else "…"
        return f" {text.ljust(room)} "

    rule = f"+{'-' * left}+{'-' * right}+"
    lines = [rule, f"|{cell('current', left)}|{cell('QA proposal', right)}|", rule]
    for key in ORDER:
        if key not in base and (not cand or key not in cand):
            continue
        top, bottom = f"{key}: {base.get(key, 'pending')}", ""
        prev = f"previous: {key}: {base.get(key, 'pending')}"
        new = f"new: {key}: {cand[key]}" if cand else "pending"
        lines.append(f"|{cell(top, left)}|{cell(prev, right)}|")
        lines.append(f"|{cell(bottom, left)}|{cell(new, right)}|")
        lines.append(rule)
    return "\n".join(lines)
