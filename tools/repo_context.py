#!/usr/bin/env python3
"""Query bounded Repo-Dev facts without loading the rail's whole history."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import subprocess
from pathlib import Path

from item_contract import item_contract
from repo_queries import (bugs, exact_bug, exact_roadmap_item, item_context,
                          latest_bug, module_context, roadmap_rows,
                          roadmap_state, summary)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "first/genesis/scripts"))
import compass

QA = ROOT / "check/tokens-qa/scripts/tokens_qa.py"


def shot_query(root: Path, verb: str, *args: str) -> tuple[int, dict]:
    """The observer owns feedback and proof; this adapter owns the Item join."""
    done = subprocess.run([sys.executable, str(QA), verb, *args,
                           "--project-root", str(root), "--json"],
                          capture_output=True, text=True, timeout=30)
    envelope = json.loads(done.stdout)
    if done.returncode not in (0, 1):
        raise ValueError(envelope.get("error") or done.stderr or "Shot query failed")
    return done.returncode, envelope.get("result") or {}


def next_feature(root: Path, item: str = "", workstream: str = "default") -> dict:
    errors = check_compass(root)
    if errors:
        raise ValueError("; ".join(errors))
    selected = compass.select(root, item=item, workstream=workstream)
    selected.update(version=1, reasons=[], acceptance_criteria=None, exclusions=None,
                    read_paths=None, write_paths=None, proof_requirements=None,
                    latest_shot=None, effective_feedback=None,
                    budget={'cap': None, 'status': 'unknown'})
    identity = selected.get("item_id")
    if not identity:
        selected['reasons'] = ['no-ready-item']
        return selected
    _, history = shot_query(root, "history", "--item-id", identity)
    selected["observations"] = history
    selected['unresolved_corrections'] = history.get('unresolved_corrections', [])
    selected['evidence_revision'] = history.get('revision')
    latest = history.get('latest')
    selected['latest_shot'] = latest
    if latest:
        selected['effective_feedback'] = {'status': latest['verdict'],
                                          'correction': latest.get('correction')}
    row = exact_roadmap_item(root, identity)
    contract = {}
    if row.get('contract'):
        contract, reasons = item_contract(root, row)
        selected.update(contract)
        selected['reasons'] = reasons
        if reasons:
            selected['next_action'] = 'bound-task'
            return selected
        selected['scope'] = ', '.join(contract['write_paths'])
        selected['proof'] = ', '.join(contract['proof_requirements'])
    selected['closure_revision'] = closure_revision(root, contract, history)
    if not row.get('contract') and (not selected.get("scope") or not selected.get("proof")):
        selected["next_action"] = "bound-task"
        selected['reasons'] = ['Scope and Proof required']
        return selected
    if latest:
        if latest["verdict"] == "failed":
            selected["next_action"] = "apply-correction"
        elif latest["verdict"] == "pending":
            selected["next_action"] = "await-feedback"
        else:
            proof_args = [flag for proof in selected.get('proof_requirements') or [] for flag in ('--proof', proof)]
            code, gate = shot_query(root, "gate", latest["path"],
                                    '--expected-revision', history['revision'], *proof_args)
            selected['reasons'].extend(gate.get('reasons', []))
            selected["next_action"] = "close-item" if code == 0 else "verify-proof"
    budget = selected.get("budget_tokens")
    selected['budget'] = {'cap': budget if budget != '' else None, 'status': 'uncapped'}
    if budget is not None and budget != '':
        profiles = history.get("totals_by_profile", {})
        if history.get('deleted_shots') or len(profiles) > 1 or any(b["input"] is None or b["output"] is None for b in profiles.values()):
            selected['budget']['status'] = 'unknown'
        else:
            used = sum(b['input'] + b['output'] for b in profiles.values())
            selected['budget'].update(used=used, remaining=max(0, int(budget) - used),
                                      status='exhausted' if used >= int(budget) else 'available')
        if selected['next_action'] in {'continue-task', 'advance-task', 'apply-correction'}:
            action = {'unknown': 'resolve-budget', 'exhausted': 'budget-exhausted'}.get(selected['budget']['status'])
            if action:
                selected['next_action'] = action
                selected['reasons'].append(action)
    if not selected['reasons']:
        selected['reasons'] = [selected['next_action']]
    return selected


def check_compass(root: Path) -> list[str]:
    errors = compass.check(root)
    if errors:
        return errors
    rows = roadmap_rows(root)
    for row in rows:
        if not row.get("workstream") or row["state"] != "DONE":
            continue
        identity, shot = row["id"], row.get("shot", "")
        if not shot:
            errors.append(f"{identity}: DONE requires a Shot path")
            continue
        path = (root / shot).resolve()
        if not path.is_relative_to(root.resolve() / ".audit/shots"):
            errors.append(f"{identity}: Shot must belong to this project's .audit/shots")
            continue
        contract, missing = item_contract(root, row) if row.get('contract') else ({}, [])
        if missing:
            errors.extend(f'{identity}: {reason}' for reason in missing)
            continue
        proof_args = [flag for proof in contract.get('proof_requirements') or [] for flag in ('--proof', proof)]
        code, result = shot_query(root, "gate", str(path), '--allow-historical', *proof_args)
        _, history = shot_query(root, "history", "--item-id", identity)
        latest = history.get("latest") or {}
        if code or result.get("item_id") != identity or latest.get("shot_id") != result.get("shot_id"):
            errors.append(f"{identity}: latest Shot must be accepted with matching proof and no veto")
    return errors


def closure_revision(root: Path, contract: dict, history: dict) -> str:
    return hashlib.sha256(((root / 'ROADMAP.md').read_text() +
        contract.get('contract_revision', '') + history['revision']).encode()).hexdigest()


def close_item(root: Path, identity: str, expected_shot: str, expected_revision: str) -> dict:
    row = exact_roadmap_item(root, identity)
    contract, missing = item_contract(root, row) if row.get('contract') else ({}, [])
    _, history = shot_query(root, 'history', '--item-id', identity)
    revision = closure_revision(root, contract, history)
    latest = history.get('latest') or {}
    reasons = compass.check(root) + missing
    if latest.get('shot_id') != expected_shot or revision != expected_revision:
        reasons.append('stale closure revision')
    if latest:
        proof_args = [flag for proof in contract.get('proof_requirements') or [] for flag in ('--proof', proof)]
        _, gate = shot_query(root, 'gate', latest['path'], '--expected-revision', history['revision'], *proof_args)
        reasons.extend(gate['reasons'])
    else:
        reasons.append('Shot required')
    return {'item_id': identity, 'latest_shot': latest.get('shot_id'), 'revision': revision,
            'ready': not reasons, 'reasons': reasons}


def _print_human(result: object) -> None:
    if isinstance(result, list):
        for row in result:
            print(f"{row.get('id')}  {row.get('state', '')}  {row.get('item', '')}".rstrip())
    elif isinstance(result, dict):
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    else:
        print(result)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--json", action="store_true")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("summary")
    next_cmd = commands.add_parser("next")
    next_cmd.add_argument("--item", default="")
    next_cmd.add_argument("--workstream", default="default")
    commands.add_parser("check")
    close = commands.add_parser('close', help='read-only closure check; revalidate returned revision before writing DONE')
    close.add_argument('--item', required=True)
    close.add_argument('--expected-shot', required=True)
    close.add_argument('--expected-revision', required=True)
    state = commands.add_parser("state")
    state.add_argument("state")
    item = commands.add_parser("item")
    item.add_argument("id")
    bug = commands.add_parser("bug")
    bug.add_argument("id", nargs="?")
    bug.add_argument("--latest", action="store_true")
    module = commands.add_parser("module")
    module.add_argument("query")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "next":
            result = next_feature(root, args.item, args.workstream)
        elif args.command == 'close':
            result = close_item(root, args.item, args.expected_shot, args.expected_revision)
            print(json.dumps(result, sort_keys=True))
            return 0 if result['ready'] else 1
        elif args.command == "check":
            errors = check_compass(root)
            print(json.dumps({"ok": not errors, "errors": errors}))
            return 1 if errors else 0
        elif args.command == "summary":
            result = summary(root)
        elif args.command == "state":
            result = roadmap_state(root, args.state)
        elif args.command == "item":
            result = item_context(root, args.id)
        elif args.command == "bug":
            result = latest_bug(root) if args.latest else exact_bug(root, args.id)
        else:
            result = module_context(root, args.query)
    except (LookupError, ValueError, OSError, subprocess.SubprocessError) as error:
        print(f"repo-context: {error}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        _print_human(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
