"""Checks for the domain-neutral support-evidence contract."""

from __future__ import annotations

import copy
import unittest

import support_contract as contract


def passing_manifest() -> dict[str, object]:
    requirements = []
    for requirement in contract.REQUIREMENTS:
        layers = contract.LAYERS if requirement in contract.EXTERNAL_REQUIREMENTS else {"fixture"}
        kind = "official-api" if requirement in contract.EXTERNAL_REQUIREMENTS else "local"
        requirements.append({
            "id": requirement,
            "status": "PASS",
            "interfaces": [{"kind": kind, "name": "fixture", "version": "1"}],
            "evidence": [
                {"layer": layer, "passed": True, "artifact": f"evidence/{requirement}-{layer}.json"}
                for layer in sorted(layers)
            ],
        })
    return {
        "version": 1,
        "project": {"domain": "example", "stack": "web", "selectedOutputs": ["app"]},
        "requirements": requirements,
        "controls": {
            "preview": True,
            "approval": True,
            "idempotency": True,
            "receipt": True,
            "rollback": "delete-or-compensate",
            "provenance": True,
        },
    }


class SupportContractTest(unittest.TestCase):
    def test_complete_evidence_passes(self) -> None:
        contract.validate(passing_manifest())

    def test_every_requirement_must_pass(self) -> None:
        manifest = passing_manifest()
        manifest["requirements"][0]["status"] = "BLOCKED"
        with self.assertRaisesRegex(contract.ContractError, "DES-01 is not PASS"):
            contract.validate(manifest)

    def test_external_support_needs_all_three_test_layers(self) -> None:
        manifest = passing_manifest()
        manifest["requirements"][0]["evidence"] = [
            {"layer": "fixture", "passed": True, "artifact": "fixture.json"}
        ]
        with self.assertRaisesRegex(contract.ContractError, "canary, credentialed"):
            contract.validate(manifest)

    def test_compatible_automation_explains_the_fallback(self) -> None:
        manifest = passing_manifest()
        manifest["requirements"][0]["interfaces"] = [{
            "kind": "compatible-automation", "name": "desktop", "version": "1"
        }]
        with self.assertRaisesRegex(contract.ContractError, "fallbackReason"):
            contract.validate(manifest)

    def test_interface_fallbacks_follow_the_official_first_ladder(self) -> None:
        manifest = passing_manifest()
        manifest["requirements"][0]["interfaces"] = [
            {"kind": "compatible-automation", "name": "desktop", "version": "1",
             "fallbackReason": "official interface cannot perform this operation"},
            {"kind": "official-api", "name": "platform", "version": "1"},
        ]
        with self.assertRaisesRegex(contract.ContractError, "fallback order"):
            contract.validate(manifest)


if __name__ == "__main__":
    unittest.main()
