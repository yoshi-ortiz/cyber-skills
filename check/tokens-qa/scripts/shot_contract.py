"""Strict, modality-neutral validation for one canonical Shot record."""
from __future__ import annotations

import copy

CURRENT_VERSION = 2
REQUIRED = ("shot_id", "scope", "inputs", "compute", "output",
            "provenance", "user_feedback")
TOP_LEVEL = REQUIRED + ("version", "gates", "findings")
# `admitted_context` is the surfaces a shot actually touched. `shot_view` has
# always read it; this tuple has always refused it, so a valid shot could not
# carry one and `context.status` could only ever say not_observed.
# `invocation` is the run this Shot belongs to. Optional, and it stays
# optional: every record already on disk was written without one, and making it
# required would rewrite history instead of migrating it.
INPUTS = ("prompt_hash", "tools", "corpus_refs", "stack", "request",
          "target_skill", "admitted_context", "invocation")
COMPUTE = ("model", "harness", "started_at", "duration_ms", "tokens", "passes")
FEEDBACK = ("status", "sentiment", "correction", "rank", "evidence", "observed_at")
PROVENANCE = ("corpus", "procedural", "fetched", "inference")
STATUS = ("pending", "accepted", "corrected", "rejected")
GATE_STATUS = ("pass", "fail", "skip")
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


def only(obj: dict, where: str, *allowed: str) -> None:
    extra = sorted(set(obj) - set(allowed))
    if extra:
        raise Invalid(f"{where}.{extra[0]}: unknown field")


def migrate(record: object, where: str = "$") -> dict:
    """The one door into the contract. Callers hand over whatever is on disk and
    get a v2 record back, never a mutated argument."""
    record = copy.deepcopy(require_object(record, where))
    version = record.get("version", 1)
    if version == CURRENT_VERSION:
        return record
    if version != 1:
        raise Invalid(f"{where}.version: unsupported version {version!r}")
    record["version"] = CURRENT_VERSION

    inputs = record.get("inputs")
    if isinstance(inputs, dict) and isinstance(inputs.get("corpus_refs"), list):
        inputs["corpus_refs"] = [ref if isinstance(ref, dict) else {"path": ref}
                                 for ref in inputs["corpus_refs"]]

    output = record.get("output")
    if isinstance(output, dict) and "path" in output:
        artifact = {"role": "deliverable", "path": output.pop("path")}
        for key in ("mime", "bytes"):
            if key in output:
                artifact[key] = output.pop(key)
        output["artifacts"] = [artifact]
    return record


def validate_v2(record: object, where: str = "$") -> dict:
    record = require_object(record, where)
    for key in REQUIRED:
        if key not in record:
            raise Invalid(f"{where}.{key}: required key is absent")
    only(record, where, *TOP_LEVEL)
    if record.get("version") != CURRENT_VERSION:
        raise Invalid(f"{where}.version: expected {CURRENT_VERSION}")
    if record.get("provenance") not in PROVENANCE:
        raise Invalid(f"{where}.provenance: not one of {'/'.join(PROVENANCE)}")
    require_string(record["shot_id"], f"{where}.shot_id")
    require_string(record["scope"], f"{where}.scope")

    inputs = require_object(record["inputs"], f"{where}.inputs")
    only(inputs, f"{where}.inputs", *INPUTS)
    for key in ("prompt_hash", "tools"):
        if key not in inputs:
            raise Invalid(f"{where}.inputs.{key}: required key is absent")
    require_string(inputs["prompt_hash"], f"{where}.inputs.prompt_hash")
    require_string_list(inputs["tools"], f"{where}.inputs.tools")
    refs = inputs.get("corpus_refs", [])
    if not isinstance(refs, list) or any(not isinstance(ref, dict) for ref in refs):
        raise Invalid(f"{where}.inputs.corpus_refs: expected an array of objects")
    for index, ref in enumerate(refs):
        require_string(ref.get("path"), f"{where}.inputs.corpus_refs[{index}].path")
    if "stack" in inputs:
        require_string_list(inputs["stack"], f"{where}.inputs.stack")
    if "admitted_context" in inputs:
        require_string_list(inputs["admitted_context"], f"{where}.inputs.admitted_context")
    if "request" in inputs:
        require_string(inputs["request"], f"{where}.inputs.request")
    if "target_skill" in inputs:
        require_string(inputs["target_skill"], f"{where}.inputs.target_skill")
    if "invocation" in inputs:
        require_string(inputs["invocation"], f"{where}.inputs.invocation")

    compute = require_object(record["compute"], f"{where}.compute")
    only(compute, f"{where}.compute", *COMPUTE)
    for key in ("model", "harness", "started_at", "duration_ms", "tokens"):
        if key not in compute:
            raise Invalid(f"{where}.compute.{key}: required key is absent")
    for key in ("model", "harness", "started_at"):
        require_string(compute[key], f"{where}.compute.{key}")
    require_count(compute["duration_ms"], f"{where}.compute.duration_ms")
    tokens = require_object(compute["tokens"], f"{where}.compute.tokens")
    only(tokens, f"{where}.compute.tokens", "input", "output", "profile")
    for key in ("input", "output", "profile"):
        if key not in tokens:
            raise Invalid(f"{where}.compute.tokens.{key}: required key is absent")
    require_count(tokens["input"], f"{where}.compute.tokens.input", nullable=True)
    require_count(tokens["output"], f"{where}.compute.tokens.output", nullable=True)
    require_string(tokens["profile"], f"{where}.compute.tokens.profile")
    passes = compute.get("passes", [])
    if not isinstance(passes, list) or any(not isinstance(p, dict) for p in passes):
        raise Invalid(f"{where}.compute.passes: expected an array of objects")

    output = require_object(record["output"], f"{where}.output")
    only(output, f"{where}.output", "adapter", "artifacts", "inline")
    require_string(output.get("adapter"), f"{where}.output.adapter")
    if ("artifacts" in output) == ("inline" in output):
        raise Invalid(f"{where}.output: exactly one of `artifacts` and `inline`")
    if "inline" in output:
        require_object(output["inline"], f"{where}.output.inline")
    else:
        artifacts = output["artifacts"]
        if not isinstance(artifacts, list) or not artifacts:
            raise Invalid(f"{where}.output.artifacts: expected a non-empty array")
        for index, artifact in enumerate(artifacts):
            at = f"{where}.output.artifacts[{index}]"
            require_object(artifact, at)
            only(artifact, at, "role", "path", "mime", "bytes", "sha256")
            require_string(artifact.get("role"), f"{at}.role")
            require_string(artifact.get("path"), f"{at}.path")
            if "mime" in artifact:
                require_string(artifact["mime"], f"{at}.mime")
            if "bytes" in artifact:
                require_count(artifact["bytes"], f"{at}.bytes")
            if "sha256" in artifact:
                require_string(artifact["sha256"], f"{at}.sha256")

    feedback = require_object(record["user_feedback"], f"{where}.user_feedback")
    only(feedback, f"{where}.user_feedback", *FEEDBACK)
    if feedback.get("status") not in STATUS:
        raise Invalid(f"{where}.user_feedback.status: not one of {'/'.join(STATUS)}")
    if "sentiment" in feedback and feedback["sentiment"] not in ("positive", "neutral", "negative"):
        raise Invalid(f"{where}.user_feedback.sentiment: not positive/neutral/negative")
    for key in ("correction", "evidence", "observed_at"):
        if key in feedback:
            require_string(feedback[key], f"{where}.user_feedback.{key}")
    if "rank" in feedback and (isinstance(feedback["rank"], bool)
                               or not isinstance(feedback["rank"], (int, float))):
        raise Invalid(f"{where}.user_feedback.rank: expected a number")

    gates = require_object(record.get("gates", {}), f"{where}.gates")
    only(gates, f"{where}.gates", "l1", "l2")
    for key, gate in gates.items():
        at = f"{where}.gates.{key}"
        require_object(gate, at)
        only(gate, at, "status", "name", "reason")
        if gate.get("status") not in GATE_STATUS:
            raise Invalid(f"{at}.status: not one of {'/'.join(GATE_STATUS)}")
        for field in ("name", "reason"):
            if field in gate:
                require_string(gate[field], f"{at}.{field}")

    findings = record.get("findings", [])
    if not isinstance(findings, list):
        raise Invalid(f"{where}.findings: expected an array")
    for finding in findings:
        if not isinstance(finding, dict) or finding.get("id") not in FINDINGS:
            value = finding.get("id") if isinstance(finding, dict) else finding
            raise Invalid(f"{where}.findings: unknown id {value!r}")
    return record


def validate(record: object, where: str = "$") -> dict:
    return validate_v2(migrate(record, where), where)
