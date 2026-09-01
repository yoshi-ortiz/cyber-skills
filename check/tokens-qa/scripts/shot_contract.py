"""Strict, modality-neutral validation for one canonical Shot record."""
from __future__ import annotations

REQUIRED = ("shot_id", "scope", "inputs", "compute", "output",
            "provenance", "user_feedback")
TOP_LEVEL = set(REQUIRED) | {"version", "gates", "findings"}
PROVENANCE = ("corpus", "procedural", "fetched", "inference")
STATUS = ("pending", "accepted", "corrected", "rejected")
FINDINGS = ("scope_breach", "missing_observation_log", "context_derail",
            "ungrounded_corpus_claim", "context_contamination")


class Invalid(Exception):
    """The record cannot be read. Fail closed and name the JSON path."""


def require_object(value: object, where: str) -> dict:
    if not isinstance(value, dict):
        raise Invalid(f"{where}: not a JSON object")
    return value


def require_string(value: object, where: str) -> str:
    if not isinstance(value, str) or not value:
        raise Invalid(f"{where}: required non-empty string")
    return value


def require_string_list(value: object, where: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise Invalid(f"{where}: expected an array of strings")
    return value


def require_count(value: object, where: str, *, nullable: bool = False) -> int | None:
    if value is None and nullable:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise Invalid(f"{where}: expected a non-negative integer"
                      + (" or null" if nullable else ""))
    return value


def validate(record: object, where: str = "$") -> dict:
    record = require_object(record, where)
    for key in REQUIRED:
        if key not in record:
            raise Invalid(f"{where}.{key}: required key is absent")
    unknown = set(record) - TOP_LEVEL
    if unknown:
        key = sorted(unknown)[0]
        raise Invalid(f"{where}.{key}: unknown top-level field")
    if record.get("provenance") not in PROVENANCE:
        raise Invalid(f"{where}.provenance: not one of {'/'.join(PROVENANCE)}")
    require_string(record["shot_id"], f"{where}.shot_id")
    require_string(record["scope"], f"{where}.scope")

    inputs = require_object(record["inputs"], f"{where}.inputs")
    for key in ("prompt_hash", "tools"):
        if key not in inputs:
            raise Invalid(f"{where}.inputs.{key}: required key is absent")
    require_string(inputs["prompt_hash"], f"{where}.inputs.prompt_hash")
    require_string_list(inputs["tools"], f"{where}.inputs.tools")
    if "corpus_refs" in inputs:
        require_string_list(inputs["corpus_refs"], f"{where}.inputs.corpus_refs")
    if "stack" in inputs:
        require_string_list(inputs["stack"], f"{where}.inputs.stack")

    compute = require_object(record["compute"], f"{where}.compute")
    output = require_object(record["output"], f"{where}.output")
    for key in ("model", "harness", "started_at", "duration_ms", "tokens"):
        if key not in compute:
            raise Invalid(f"{where}.compute.{key}: required key is absent")
    for key in ("model", "harness", "started_at"):
        require_string(compute[key], f"{where}.compute.{key}")
    require_count(compute["duration_ms"], f"{where}.compute.duration_ms")
    tokens = require_object(compute["tokens"], f"{where}.compute.tokens")
    for key in ("input", "output", "profile"):
        if key not in tokens:
            raise Invalid(f"{where}.compute.tokens.{key}: required key is absent")
    require_count(tokens["input"], f"{where}.compute.tokens.input", nullable=True)
    require_count(tokens["output"], f"{where}.compute.tokens.output", nullable=True)
    require_string(tokens["profile"], f"{where}.compute.tokens.profile")

    require_string(output.get("adapter"), f"{where}.output.adapter")
    if ("path" in output) == ("inline" in output):
        raise Invalid(f"{where}.output: exactly one of `path` and `inline`")
    if "path" in output:
        require_string(output["path"], f"{where}.output.path")
    else:
        require_object(output["inline"], f"{where}.output.inline")
    if "mime" in output:
        require_string(output["mime"], f"{where}.output.mime")
    if "bytes" in output:
        require_count(output["bytes"], f"{where}.output.bytes")

    feedback = require_object(record["user_feedback"], f"{where}.user_feedback")
    if feedback.get("status") not in STATUS:
        raise Invalid(f"{where}.user_feedback.status: not one of {'/'.join(STATUS)}")
    if "sentiment" in feedback and feedback["sentiment"] not in ("positive", "neutral", "negative"):
        raise Invalid(f"{where}.user_feedback.sentiment: not positive/neutral/negative")
    if "correction" in feedback:
        require_string(feedback["correction"], f"{where}.user_feedback.correction")
    if "rank" in feedback and (isinstance(feedback["rank"], bool)
                               or not isinstance(feedback["rank"], (int, float))):
        raise Invalid(f"{where}.user_feedback.rank: expected a number")
    findings = record.get("findings", [])
    if not isinstance(findings, list):
        raise Invalid(f"{where}.findings: expected an array")
    for finding in findings:
        if not isinstance(finding, dict) or finding.get("id") not in FINDINGS:
            value = finding.get("id") if isinstance(finding, dict) else finding
            raise Invalid(f"{where}.findings: unknown id {value!r}")
    return record
