#!/usr/bin/env python3
"""One real round, recorded as a Shot and read back as a table.

R-68 asks for the actual skill path -- real run, real companion artifact, real
delivery, real Shot, real table -- rather than a canned fixture or a pass that
is only an exit code. So this runs the round for real and then records what it
produced, correlated by one run identity.

Deliberately not wired into `tools/check.py`. The Cook gate there already times
out starting the local server, and hanging a second, longer proof off it would
confuse one diagnosis with another.
"""
from __future__ import annotations

import json
import argparse
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from errors import CookError

TOKENS_QA = (Path(__file__).resolve().parents[1]
             / "check" / "tokens-qa" / "scripts" / "tokens_qa.py")
SKILL = "first/aesthetic"


def tokens_qa(project_root: Path, *argv: str) -> subprocess.CompletedProcess:
    """The published CLI, from inside the scratch tree so `.audit/` lands there.

    Cook never imports this package. It asks, the same way a user would, and a
    non-zero exit is reported rather than interpreted.
    """
    return subprocess.run([sys.executable, str(TOKENS_QA), *argv],
                          capture_output=True, text=True, cwd=project_root,
                          timeout=60)


def record(project_root: Path, run_id: str, screen: str, asked: str) -> dict:
    """Write the Shot for this round, with the screen as its deliverable."""
    with tempfile.TemporaryDirectory() as scratch:
        request = Path(scratch) / "request.txt"
        request.write_text(asked, encoding="utf-8")
        manifest = Path(scratch) / "manifest.json"
        manifest.write_text(json.dumps({"adapter": "document", "artifacts": [
            {"role": "deliverable", "path": screen, "mime": "text/html"}]}),
            encoding="utf-8")
        done = tokens_qa(project_root, "record", SKILL,
                         "--request", str(request),
                         "--output-manifest", str(manifest),
                         "--invocation", run_id, "--harness", "cook", '--project-root', str(project_root),
                         '--token-profile', 'unknown', "--json")
    if done.returncode != 0:
        raise CookError(
            f"tokens-qa record exited {done.returncode}: "
            f"{(done.stderr or done.stdout).strip()}")
    return json.loads(done.stdout)["result"]


def prove(project_root: Path, round_runner) -> dict:
    """Run the round, record it, and read the table back.

    `round_runner` is passed in rather than imported so this module does not
    depend on the runner that depends on it. It also means the run identity is
    stamped here, before the round starts, which is what makes the window real
    rather than reconstructed afterwards.
    """
    run_id = "aesthetic@" + datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")
    result = round_runner(project_root)
    screens = result.get("screens") or []
    if not screens:
        raise CookError(
            "the round published no screen, so there is no deliverable to "
            "record. A Shot whose output is nothing proves nothing.")

    shot = record(project_root, run_id, screens[0],
                  "Cook Food Product round: publish one rankable proposal and "
                  "prove a designer can see and score it.")
    table = tokens_qa(project_root, "observe", shot["path"])
    return {**result, "run_id": run_id, "shot": shot["path"],
            "shot_id": shot["shot_id"], "table": table.stdout.strip(),
            # The round's own verdict still decides. Recording a Shot for a
            # broken round is evidence, not a pass.
            "passed": result.get("passed", False)}


def main(argv=None):
    parser = argparse.ArgumentParser(description='Record one code/document proof through Tokens QA.')
    parser.add_argument('--project-root', type=Path, required=True)
    parser.add_argument('--item-id', required=True)
    parser.add_argument('--invocation', required=True)
    parser.add_argument('--request', required=True)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--proof', required=True)
    parser.add_argument('--token-profile', default='unknown')
    parser.add_argument('--tokens-input', type=int)
    parser.add_argument('--tokens-output', type=int)
    parser.add_argument('--check', nargs=argparse.REMAINDER, required=True)
    args = parser.parse_args(argv)
    try:
        root = args.project_root.resolve(strict=True)
        proof = (root / args.proof).resolve()
        if not proof.is_relative_to(root) or proof.exists() or not args.check:
            raise CookError('proof must be a new project-contained file; check argv required')
        # The command is explicit caller input, never read from stored Shot evidence.
        check = subprocess.run(args.check, cwd=root, capture_output=True, text=True, timeout=60)
        with proof.open('x', encoding='utf-8') as output:
            output.write(check.stdout + check.stderr)
        with tempfile.TemporaryDirectory() as temporary:
            gates = Path(temporary) / 'gates.json'
            gates.write_text(json.dumps({'l2': {'status': 'pass' if check.returncode == 0 else 'fail',
                'name': json.dumps(args.check), 'observer': 'cook/prove.py',
                'observed_at': datetime.now(timezone.utc).isoformat(), 'artifacts': [str(proof)]}}))
            command = ['record', 'code/document', '--project-root', str(root),
                       '--item-id', args.item_id, '--invocation', args.invocation,
                       '--request', args.request, '--output-manifest', args.manifest,
                       '--gates', str(gates), '--harness', 'cook/prove.py',
                       '--token-profile', args.token_profile, '--json']
            for name in ('tokens_input', 'tokens_output'):
                if getattr(args, name) is not None:
                    command += ['--' + name.replace('_', '-'), str(getattr(args, name))]
            done = tokens_qa(root, *command)
        if done.returncode:
            raise CookError(done.stderr or done.stdout)
        result = json.loads(done.stdout)['result']
        print(json.dumps({**result, 'check_passed': check.returncode == 0}))
        return int(check.returncode != 0)
    except (CookError, OSError, subprocess.SubprocessError) as error:
        print(json.dumps({'error': str(error)}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
