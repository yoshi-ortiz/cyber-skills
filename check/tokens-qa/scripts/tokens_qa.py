#!/usr/bin/env python3
"""Observe one Shot, and say what it cost and what it broke.

Black box on purpose. It reads the declared request, the observable output, the
token counts, and the user's own words. It never reads hidden reasoning, and it
never substitutes a repository scan for evidence -- context it cannot see is
reported `not_observed`, never guessed at.

    python3 tokens_qa.py record <skill> --request req.txt --inline "<output>"
    python3 tokens_qa.py observe .audit/shots/<id>.json
    python3 tokens_qa.py compare .audit/shots/<base>.json .audit/shots/<cand>.json
    python3 tokens_qa.py feedback .audit/shots/<id>.json --status accepted
    python3 tokens_qa.py assess-feedback --evidence turns.json --json

Exit 0 success, 1 hard veto, 2 schema or arguments, 3 I/O, 4 write conflict,
5 adapter or subprocess.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import uuid
from types import SimpleNamespace
from datetime import datetime, timezone
from pathlib import Path

import feedback as advisory
import shot_io
from shot_contract import Invalid, validate
from shot_io import sha256_text as sha256
from shot_view import ORDER, VETOES, metrics, table, totals, verdict, vetoes


class Refused(Exception):
    def __init__(self, message: str, code: int = 2, path: str | None = None):
        super().__init__(message)
        self.code, self.path = code, path


# ponytail: bytes/4. The repo already refuses to pretend precision it does not
# have (tools/token_bench.py says so at length); swap for a real tokenizer only
# when one is installed and the ratio stops being the thing that carries.
def estimate(text: str) -> int:
    return math.ceil(len(text.encode("utf-8")) / 4)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def parse_contexts(specs: list[str]) -> dict[str, tuple[str, ...]]:
    """`["api=src/api/", "ui=src/ui/,web/"]` -> `{"api": (...), "ui": (...)}`.

    The project names its own contexts. This package never learns a folder
    layout: QA.md owns the veto, the caller owns the map. A malformed spec is
    refused rather than dropped, because a context silently missing from the
    map is a derail that silently cannot fire.
    """
    contexts: dict[str, tuple[str, ...]] = {}
    for spec in specs:
        name, sep, prefixes = spec.partition("=")
        if not (sep and name.strip() and prefixes.strip()):
            raise Refused(f"--context {spec!r}: expected NAME=prefix[,prefix]")
        contexts[name.strip()] = tuple(
            p.strip() for p in prefixes.split(",") if p.strip())
    return contexts


def path_matches(path: str, prefixes: tuple[str, ...]) -> bool:
    if ".." in Path(path).parts:
        return False
    return any(Path(path) == Path(prefix) or Path(prefix) in Path(path).parents
               for prefix in prefixes)


def scope_finding(paths: list[str], allowed: tuple[str, ...]) -> list[dict]:
    """`[scope_breach]` when the pass wrote outside its declared scope.

    `scope` is the one bounded task a Shot claims. Nothing compared that claim
    against what the pass actually wrote, so a run could declare a narrow scope,
    edit half the tree, and still report no veto. The caller declares the
    allowed prefixes; declaring none means there is nothing to check, not that
    everything is permitted.
    """
    if not allowed:
        return []
    outside = sorted(p for p in paths if not path_matches(p, allowed))
    if not outside:
        return []
    return [{"id": "scope_breach", "status": "present",
             "evidence": (f"wrote {len(outside)} path(s) outside the declared scope "
                          f"({', '.join(allowed)}): " + ", ".join(outside[:4]))}]


def derail_finding(paths: list[str],
                   contexts: dict[str, tuple[str, ...]]) -> list[dict]:
    """`[context_derail]` when one pass wrote to two declared contexts.

    A path no context claims belongs to none: a shot is not derailed by a
    file nobody said was a boundary.
    """
    hit = {name: sorted(p for p in paths if path_matches(p, prefixes))
           for name, prefixes in contexts.items()}
    hit = {name: found for name, found in hit.items() if found}
    if len(hit) < 2:
        return []
    where = "; ".join(f"{name} ({', '.join(found[:3])})"
                      for name, found in sorted(hit.items()))
    return [{"id": "context_derail", "status": "present",
             "evidence": f"one pass wrote {len(hit)} declared contexts -- {where}"}]


def cmd_record(args):
    if args.output:
        raise Refused('--output was removed. Pass --inline "<text>" for an inline '
                      "payload, or --output-manifest <manifest.json> for artifacts "
                      "on disk.")
    request = Path(args.request).read_text(encoding="utf-8")
    if args.redacted_request:
        if not args.request_ref:
            raise Refused('redacted request requires request-ref')
        request = '[redacted]'
    digests: list[dict] = []
    if args.output_manifest:
        output, size, digests = shot_io.manifest_output(
            args.output_manifest, Path(args.project_root) if args.project_root else None)
    else:
        output, size = shot_io.inline_output(args.inline)
    shot_id = uuid.uuid4().hex
    contexts = parse_contexts(args.context or [])
    changed = [p.strip() for p in (args.changed or "").split(",") if p.strip()]
    scope_paths = tuple(p.strip() for p in (args.within or "").split(",")
                        if p.strip())
    inputs = {"request": request, "target_skill": args.skill,
              "corpus_refs": [], "prompt_hash": sha256(request), "tools": []}
    if args.request_ref:
        inputs['request_ref'] = args.request_ref
    if changed:
        inputs["changed_paths"] = changed
    if args.admitted_context is not None:
        inputs["admitted_context"] = args.admitted_context
    if args.invocation:
        inputs["invocation"] = args.invocation
    telemetry = args.item_id is not None or any(value is not None for value in
        (args.tokens_input, args.tokens_output, args.token_profile))
    record = validate({
        "version": 2, "shot_id": shot_id, "scope": args.scope or args.skill,
        **({"item_id": args.item_id} if args.item_id is not None else {}),
        "inputs": inputs,
        "compute": {"model": args.model, "harness": args.harness,
                    "started_at": now(), "duration_ms": args.duration_ms,
                    "tokens": {"input": args.tokens_input if telemetry else estimate(request),
                               "output": args.tokens_output if telemetry else math.ceil(size / 4),
                               "profile": (args.token_profile or "unknown") if telemetry
                               else "utf8_bytes_div4_ceil_v1"}},
        "output": output, "provenance": "inference",
        **({"gates": shot_io.load(args.gates)} if args.gates else {}),
        "user_feedback": {"status": "pending"},
        "findings": (scope_finding(changed, scope_paths)
                     + derail_finding(changed, contexts)),
    })
    target = shot_io.contained(Path(args.project_root or Path.cwd()),
                               f".audit/shots/{shot_id}.json")
    with shot_io.locked(target.parent):
        shot_io.create_shot(target, record)
    # The table, not the path. `record` used to print where it wrote, so
    # reading the numbers it had just computed took a second command and
    # nobody ran it.
    return 0, {"path": str(target), "shot_id": shot_id, "artifacts": digests,
               "findings": [f["id"] for f in record["findings"]]}, \
        table(metrics(record), None) + f"\n{target}"


def read_pair(base_path: str, cand_path: str | None):
    base = shot_io.read_shot(base_path)
    cand = shot_io.read_shot(cand_path) if cand_path else None
    text = table(metrics(base), metrics(cand) if cand else None)
    selected = cand if cand is not None else base
    return (1 if vetoes(selected) else 0), {"verdict": verdict(selected),
                                        "hard_vetoes": vetoes(selected)}, text


def cmd_gate(args):
    with shot_io.locked(shot_io.contained(Path(args.project_root), '.audit/shots')):
        return gate_result(args)


def gate_result(args):
    shot_io.contained(Path(args.project_root), args.shot)
    record = shot_io.read_shot(args.shot)
    _, history, _ = cmd_history(SimpleNamespace(project_root=args.project_root,
                                               item_id=record.get('item_id')))
    failures = shot_io.verify_artifacts(record, Path(args.project_root), args.allow_historical)
    latest = history.get('latest') or {}
    if latest.get('shot_id') != record['shot_id']:
        failures.append('latest Shot required')
    if args.expected_revision and args.expected_revision != history['revision']:
        failures.append('stale Item revision')
    if history['unresolved_corrections']:
        failures.append('unresolved corrections')
    if history['deleted_shots']:
        failures.append('deleted evidence makes closure unverifiable')
    acceptance = next((e for e in reversed(record.get('feedback_events', []))
                       if 'status' in e['fields']), None)
    if not acceptance or acceptance['fields']['status'] != 'accepted' or acceptance['source_kind'] != 'user':
        failures.append('user acceptance provenance required')
    if not record.get("item_id"):
        failures.append("item_id required")
    if verdict(record) != "accepted":
        failures.append("acceptance required")
    hard = vetoes(record)
    failures.extend(hard)
    if record.get("gates", {}).get("l2", {}).get("status") != "pass":
        failures.append("l2 pass required")
    l2 = record.get('gates', {}).get('l2', {})
    if not all(l2.get(field) for field in ('name', 'observer', 'observed_at', 'artifacts')):
        failures.append('observed L2 provenance required')
    proofs = {str(shot_io.contained(Path(args.project_root), a['path']))
              for a in record['output'].get('artifacts', []) if a['role'] == 'proof'}
    required = set(args.proof or []) | set(l2.get('artifacts', []))
    for proof in required:
        if str(shot_io.contained(Path(args.project_root), proof)) not in proofs:
            failures.append(f'proof coverage missing: {proof}')
    if not any(a["role"] == "proof" for a in record["output"].get("artifacts", [])):
        failures.append("proof artifact required")
    result = {"item_id": record.get("item_id"), "shot_id": record["shot_id"],
              "verdict": verdict(record), "ready": not failures,
              "hard_vetoes": hard, "reasons": failures, 'revision': history['revision']}
    return int(bool(failures)), result, json.dumps(result, separators=(",", ":"))


def cmd_history(args):
    paths = shot_io.shot_paths(Path(args.project_root))
    records = [shot_io.read_shot(path) for path in paths]
    locations = {record["shot_id"]: str(path) for path, record in zip(paths, records)}
    records = [r for r in records if r.get("item_id") == args.item_id]
    records.sort(key=lambda r: (r["compute"]["started_at"], r["shot_id"]))
    profiles = {}
    for record in records:
        tokens = record["compute"]["tokens"]
        bucket = profiles.setdefault(tokens["profile"], {
            "shots": 0, "input": 0, "output": 0,
            "unknown_input": 0, "unknown_output": 0})
        bucket["shots"] += 1
        for key in ("input", "output"):
            if tokens[key] is None:
                bucket["unknown_" + key] += 1
            else:
                bucket[key] += tokens[key]
    for bucket in profiles.values():
        for key in ("input", "output"):
            bucket["known_" + key] = bucket[key]
            if bucket["unknown_" + key]:
                bucket[key] = None
    last = records[-1] if records else None
    unresolved = {}
    resolved = set()
    event_count = 0
    for record in records:
        baseline = record.get('feedback_baseline', record['user_feedback'])
        if baseline.get('correction'):
            identity = record['shot_id'] + ':legacy'
            unresolved[identity] = {'event_id': identity, 'shot_id': record['shot_id'],
                                    'correction': baseline['correction']}
        for event in record.get('feedback_events', []):
            event_count += 1
            for identity in event['resolves']:
                resolved.add(identity)
            if event['fields'].get('correction'):
                unresolved[event['event_id']] = {'event_id': event['event_id'],
                    'shot_id': record['shot_id'], 'correction': event['fields']['correction']}
    deleted = shot_io.deleted_shots(Path(args.project_root), args.item_id)
    result = {"item_id": args.item_id, "shots": len(records), "latest": {
        "shot_id": last["shot_id"], "verdict": verdict(last),
        "path": locations[last["shot_id"]],
        "correction": last["user_feedback"].get("correction")
        , "revision": shot_io.revision(last)
    } if last else None, "totals_by_profile": profiles,
        'feedback_events': event_count, 'unresolved_corrections': [value for key, value in unresolved.items() if key not in resolved],
        'deleted_shots': len(deleted),
        'revision': sha256(''.join(shot_io.revision(record) for record in records + deleted))}
    return 0, result, json.dumps(result, separators=(",", ":"))


def cmd_retention(args):
    root = Path(args.project_root)
    if args.delete:
        with shot_io.locked(shot_io.contained(root, '.audit/shots')):
            return retain(args, root)
    return retain(args, root)


def retain(args, root):
    paths = [p for p in shot_io.shot_paths(root) if shot_io.read_shot(p).get('item_id') == args.item_id]
    revision = sha256(''.join(str(p) + shot_io.revision(shot_io.read_shot(p)) for p in paths))
    result = {'paths': [str(p) for p in paths], 'revision': revision, 'deleted': False}
    if args.delete:
        if not args.expected_revision or args.expected_revision != revision:
            raise Refused('preview revision required; records changed or preview absent', 4)
        shot_io.delete_shots(root, paths)
        result['deleted'] = True
    return 0, result, json.dumps(result)


def cmd_observe(args):
    if args.events:
        record = shot_io.read_shot(args.shot)
        result = {'events': record.get('feedback_events', []),
                  'legacy_feedback': record.get('feedback_baseline', record['user_feedback']),
                  'revision': shot_io.revision(record)}
        return 0, result, json.dumps(result)
    return read_pair(args.shot, args.candidate)


def cmd_compare(args):
    return read_pair(args.baseline, args.candidate)


def cmd_feedback(args):
    path = Path(args.shot)
    with shot_io.locked(path.resolve().parent):
        return write_feedback(args, path)


def write_feedback(args, path):
    record = shot_io.read_shot(path)
    given = {"status": args.status, "correction": args.correction,
             "sentiment": args.sentiment, "rank": args.rank}
    given = {k: v for k, v in given.items() if v is not None}
    if not given and not args.resolve:
        raise Refused("feedback: give at least one of --status, --correction,"
                      " --sentiment, --rank")
    # A v1 file is history. Writing it would migrate it and rewrite the past.
    if shot_io.on_disk_version(path) == 1:
        raise Refused(f"{path}: version 1 is read-only, record a new shot")
    operation = args.operation_id or uuid.uuid4().hex
    event = {'version': 1, 'event_id': record['shot_id'] + ':' + operation,
             'operation_id': operation, 'fields': given, 'source_kind': args.source_kind,
             'observed_at': args.observed_at or now(), 'resolves': args.resolve or []}
    for key in ('source_ref', 'source_text', 'redacted_ref'):
        if getattr(args, key):
            event[key] = getattr(args, key)
    for previous in record.get('feedback_events', []):
        if previous['operation_id'] == operation:
            compare = dict(event)
            if not args.observed_at:
                compare['observed_at'] = previous['observed_at']
            if compare != previous:
                raise Refused('operation ID reused with different feedback', 4)
            return 0, {'event_id': previous['event_id'], 'revision': shot_io.revision(record),
                       'verdict': verdict(record), 'user_feedback': record['user_feedback']}, verdict(record)
    if args.expected_revision and args.expected_revision != shot_io.revision(record):
        raise Refused('stale feedback revision', 4)
    if args.source_kind in ('user', 'fixture') and not args.observed_at:
        raise Refused('observed-at required for sourced feedback')
    record.setdefault('feedback_baseline', dict(record['user_feedback']))
    if args.resolve:
        if args.source_kind != 'user':
            raise Refused('only user-sourced feedback may resolve corrections')
        if path.parent.name != 'shots' or path.parent.parent.name != '.audit' or not record.get('item_id'):
            raise Refused('correction resolution requires an Item-linked project Shot')
        _, history, _ = cmd_history(SimpleNamespace(project_root=path.resolve().parents[2],
                                                   item_id=record['item_id']))
        known = {e['event_id'] for e in history['unresolved_corrections']}
        if set(args.resolve) - known:
            raise Refused('unknown or already resolved correction reference')
    record.setdefault('feedback_events', []).append(event)
    fields = dict(record["user_feedback"])
    latest_correction = next((e['event_id'] for e in reversed(record.get('feedback_events', []))
                              if e['fields'].get('correction')), record['shot_id'] + ':legacy')
    if latest_correction in (args.resolve or []):
        fields.pop('correction', None)
    fields.update(given)
    record["user_feedback"] = fields
    record = validate(record)
    shot_io.replace_shot(path, record)
    return 0, {"verdict": verdict(record), "user_feedback": fields,
               'event_id': event['event_id'], 'revision': shot_io.revision(record)}, verdict(record)


def turns_of(evidence: str) -> list[str]:
    bundle = shot_io.load(evidence)
    turns = bundle.get("turns") if isinstance(bundle, dict) else None
    if not isinstance(turns, list) or any(not isinstance(t, str) for t in turns):
        raise Refused("$.turns: expected an array of strings", path="$.turns")
    return turns


def cmd_assess(args):
    found = [c._asdict() for c in advisory.assess(turns_of(args.evidence))]
    lines = [f"{c['field']} = {c['value']} ({c['confidence']})" for c in found]
    return 0, {"candidates": found}, "\n".join(lines) or "no candidates"


def cmd_audit(args):
    """Everything this boundary can say about one run's turns, in one answer.

    One command rather than two, so a caller never has to run both and
    correlate the halves itself -- which is where a loop starts keeping its own
    copy of the rules.
    """
    found = advisory.audit(turns_of(args.evidence))
    return 0, found, "\n".join(f"{kind}: {len(found[kind])}" for kind in found)


def cmd_correction(args):
    shot = shot_io.read_shot(args.shot)
    bundle = advisory.correction_bundle(shot, args.evidence or "", args.artifact)
    return 0, bundle, json.dumps(bundle, indent=2, sort_keys=True)


def parse(argv):
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", help="emit one JSON envelope")
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="verb", required=True)

    rec = sub.add_parser("record", parents=[common], help="write a Shot record")
    rec.add_argument("skill")
    rec.add_argument("--request", required=True)
    rec.add_argument('--request-ref')
    rec.add_argument('--redacted-request', action='store_true')
    out = rec.add_mutually_exclusive_group(required=True)
    out.add_argument("--output-manifest")
    out.add_argument("--inline")
    # Declared only so it stops being an abbreviation of --output-manifest.
    # Without it argparse expands the removed flag onto the new one and the
    # user's file is parsed as a manifest.
    out.add_argument("--output", help=argparse.SUPPRESS)
    rec.add_argument("--invocation", default="", metavar="RUN_ID",
                     help="the run this Shot belongs to, so the session, the "
                          "table and the feedback join by one identity")
    rec.add_argument("--scope", default="")
    rec.add_argument("--model", default="unknown")
    rec.add_argument("--harness", default="unknown")
    rec.add_argument("--item-id")
    rec.add_argument("--gates", help="JSON L1/L2 observations; does not execute commands")
    rec.add_argument("--project-root")
    rec.add_argument("--admitted-context", nargs="*", default=None)
    rec.add_argument("--tokens-input", type=int)
    rec.add_argument("--tokens-output", type=int)
    rec.add_argument("--token-profile")
    rec.add_argument("--duration-ms", type=int)
    rec.add_argument("--changed", default="",
                     help="comma-separated paths this shot wrote, as the caller "
                          "observed them (absent: context.status not_observed)")
    rec.add_argument("--within", default="", metavar="prefix[,prefix]",
                     help="paths the bounded task was allowed to write; anything "
                          "outside is scope_breach (absent: not checked). Not "
                          "--scope-paths: --scope would silently abbreviate it")
    rec.add_argument("--context", action="append", metavar="NAME=prefix[,prefix]",
                     help="declare one context boundary; repeat for each. Two "
                          "written in one pass is context_derail")
    rec.set_defaults(run=cmd_record)

    obs = sub.add_parser("observe", parents=[common], help="read one Shot")
    obs.add_argument("shot")
    obs.add_argument("candidate", nargs="?")
    obs.add_argument('--events', action='store_true')
    obs.set_defaults(run=cmd_observe)

    cmp_ = sub.add_parser("compare", parents=[common], help="baseline against candidate")
    cmp_.add_argument("baseline")
    cmp_.add_argument("candidate")
    cmp_.set_defaults(run=cmd_compare)

    fb = sub.add_parser("feedback", parents=[common], help="record the user's authority")
    fb.add_argument("shot")
    fb.add_argument("--status", choices=("pending", "accepted", "corrected", "rejected"))
    fb.add_argument("--correction")
    fb.add_argument("--sentiment", choices=("positive", "neutral", "negative"))
    fb.add_argument("--rank", type=float)
    fb.add_argument('--operation-id')
    fb.add_argument('--expected-revision')
    fb.add_argument('--source-kind', choices=('caller', 'user', 'fixture'), default='caller')
    fb.add_argument('--source-ref')
    fb.add_argument('--source-text')
    fb.add_argument('--redacted-ref')
    fb.add_argument('--observed-at')
    fb.add_argument('--resolve', action='append')
    fb.set_defaults(run=cmd_feedback)

    ass = sub.add_parser("assess-feedback", parents=[common], help="advisory candidates")
    ass.add_argument("--evidence", required=True)
    ass.set_defaults(run=cmd_assess)

    aud = sub.add_parser("shot-audit", parents=[common],
                         help="complaints, corrections, restatements, candidates")
    aud.add_argument("--evidence", required=True)
    aud.set_defaults(run=cmd_audit)

    cor = sub.add_parser("correction", parents=[common],
                         help="a bounded bundle an adapter may act on")
    cor.add_argument("shot")
    cor.add_argument("--evidence", default="")
    cor.add_argument("--artifact", action="append", default=[])
    cor.set_defaults(run=cmd_correction)
    gate = sub.add_parser("gate", parents=[common], help="check Item completion evidence")
    gate.add_argument("shot")
    gate.add_argument("--project-root", required=True)
    gate.add_argument('--expected-revision')
    gate.add_argument('--proof', action='append')
    gate.add_argument('--allow-historical', action='store_true',
                      help='accept an exact recorded artifact retained in Git history')
    gate.set_defaults(run=cmd_gate)
    history = sub.add_parser("history", parents=[common], help="summarize Item attempts")
    history.add_argument("--project-root", required=True)
    history.add_argument("--item-id", required=True)
    history.set_defaults(run=cmd_history)
    retention = sub.add_parser('retention', parents=[common], help='preview exact Shot deletion; retains artifacts')
    retention.add_argument('--project-root', required=True)
    retention.add_argument('--item-id', required=True)
    retention.add_argument('--delete', action='store_true')
    retention.add_argument('--expected-revision')
    retention.set_defaults(run=cmd_retention)
    return parser.parse_args(argv)


def json_path(message: str) -> str | None:
    head = message.split(":", 1)[0]
    return head if head.startswith("$") else None


def main(argv: list[str] | None = None) -> int:
    args = parse(argv)
    result, error, path = None, None, None
    try:
        code, result, text = args.run(args)
    except Refused as bad:
        code, error, path = bad.code, str(bad), bad.path
    except Invalid as bad:
        code, error, path = 2, str(bad), json_path(str(bad))
    except FileExistsError as bad:
        code, error = 4, f"{bad.filename}: a shot already claims this id"
    except json.JSONDecodeError as bad:
        code, error = 2, f"not JSON: {bad}"
    except OSError as bad:
        code, error = 3, f"{bad.filename}: {bad.strerror}"
    if args.json:
        print(json.dumps({"ok": code == 0, "code": code, "error": error,
                          "path": path, "result": result}))
    elif error:
        print(f"tokens-qa: {error}", file=sys.stderr)
    else:
        print(text)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
