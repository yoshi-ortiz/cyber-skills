#!/usr/bin/env python3
"""Validate evidence that every design-workflow requirement is supported."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REQUIREMENTS = tuple(f"DES-{number:02d}" for number in range(1, 18))
INTERFACES = {
    "official-api",
    "official-mcp",
    "official-sdk",
    "official-script",
    "compatible-automation",
    "local",
}
INTERFACE_ORDER = (
    "official-api",
    "official-mcp",
    "official-sdk",
    "official-script",
    "compatible-automation",
    "local",
)
LAYERS = {"fixture", "credentialed", "canary"}
EXTERNAL_REQUIREMENTS = {
    "DES-01", "DES-02", "DES-03", "DES-05", "DES-06", "DES-07", "DES-16"
}


class ContractError(ValueError):
    pass


def _nonempty(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{label} must be a non-empty string")
    return value


def validate(manifest: object) -> None:
    if not isinstance(manifest, dict) or manifest.get("version") != 1:
        raise ContractError("manifest version must be 1")
    project = manifest.get("project")
    if not isinstance(project, dict):
        raise ContractError("project must be an object")
    _nonempty(project.get("domain"), "project.domain")
    _nonempty(project.get("stack"), "project.stack")
    selected = project.get("selectedOutputs")
    if not isinstance(selected, list) or not selected:
        raise ContractError("project.selectedOutputs must select at least one output")
    if any(not isinstance(item, str) or not item.strip() for item in selected):
        raise ContractError("project.selectedOutputs contains an invalid output")

    requirements = manifest.get("requirements")
    if not isinstance(requirements, list):
        raise ContractError("requirements must be an array")
    ids = [item.get("id") for item in requirements if isinstance(item, dict)]
    if len(ids) != len(requirements) or len(ids) != len(set(ids)):
        raise ContractError("requirement ids must be present and unique")
    missing = sorted(set(REQUIREMENTS) - set(ids))
    extra = sorted(set(ids) - set(REQUIREMENTS))
    if missing or extra:
        raise ContractError(f"requirement ids differ: missing={missing}, extra={extra}")

    for item in requirements:
        requirement = item["id"]
        if item.get("status") != "PASS":
            raise ContractError(f"{requirement} is not PASS")
        interfaces = item.get("interfaces")
        if not isinstance(interfaces, list) or not interfaces:
            raise ContractError(f"{requirement}.interfaces must not be empty")
        for position, interface in enumerate(interfaces):
            label = f"{requirement}.interfaces[{position}]"
            if not isinstance(interface, dict) or interface.get("kind") not in INTERFACES:
                raise ContractError(f"{label}.kind is invalid")
            _nonempty(interface.get("name"), f"{label}.name")
            _nonempty(interface.get("version"), f"{label}.version")
            if interface["kind"] == "compatible-automation":
                _nonempty(interface.get("fallbackReason"), f"{label}.fallbackReason")
        ranks = [INTERFACE_ORDER.index(interface["kind"]) for interface in interfaces]
        if ranks != sorted(ranks):
            raise ContractError(f"{requirement}.interfaces violates the fallback order")
        if requirement in EXTERNAL_REQUIREMENTS and all(
                interface["kind"] == "local" for interface in interfaces):
            raise ContractError(f"{requirement} has no external platform interface")

        evidence = item.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            raise ContractError(f"{requirement}.evidence must not be empty")
        passed_layers: set[str] = set()
        for position, check in enumerate(evidence):
            label = f"{requirement}.evidence[{position}]"
            if not isinstance(check, dict) or check.get("layer") not in LAYERS:
                raise ContractError(f"{label}.layer is invalid")
            if check.get("passed") is not True:
                raise ContractError(f"{label} did not pass")
            _nonempty(check.get("artifact"), f"{label}.artifact")
            passed_layers.add(check["layer"])
        required_layers = LAYERS if requirement in EXTERNAL_REQUIREMENTS else {"fixture"}
        absent = sorted(required_layers - passed_layers)
        if absent:
            raise ContractError(f"{requirement} lacks evidence layers: {', '.join(absent)}")

    controls = manifest.get("controls")
    if not isinstance(controls, dict):
        raise ContractError("controls must be an object")
    for control in ("preview", "approval", "idempotency", "receipt", "provenance"):
        if controls.get(control) is not True:
            raise ContractError(f"controls.{control} must be true")
    _nonempty(controls.get("rollback"), "controls.rollback")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args(argv)
    try:
        validate(json.loads(args.manifest.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, ContractError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"PASS: {len(REQUIREMENTS)} design requirements have support evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
