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
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def cmd_record(args):
    if args.output:
        raise Refused('--output was removed. Pass --inline "<text>" for an inline '
                      "payload, or --output-manifest <manifest.json> for artifacts "
                      "on disk.")
    request = Path(args.request).read_text(encoding="utf-8")
    digests: list[dict] = []
    if args.output_manifest:
        output, size, digests = shot_io.manifest_output(args.output_manifest)
    else:
        output, size = shot_io.inline_output(args.inline)
    shot_id = uuid.uuid4().hex
    record = validate({
        "version": 2, "shot_id": shot_id, "scope": args.scope or args.skill,
        "inputs": {"request": request, "target_skill": args.skill,
                   "corpus_refs": [], "prompt_hash": sha256(request), "tools": []},
        "compute": {"model": args.model, "harness": args.harness,
                    "started_at": now(), "duration_ms": 0,
                    "tokens": {"input": estimate(request),
                               "output": math.ceil(size / 4),
                               "profile": "utf8_bytes_div4_ceil_v1"}},
        "output": output, "provenance": "inference",
        "user_feedback": {"status": "pending"}, "findings": [],
    })
    target = Path.cwd() / ".audit" / "shots" / f"{shot_id}.json"
    shot_io.create_shot(target, record)
    return 0, {"path": str(target), "shot_id": shot_id, "artifacts": digests}, str(target)


def read_pair(base_path: str, cand_path: str | None):
    base = shot_io.read_shot(base_path)
    cand = shot_io.read_shot(cand_path) if cand_path else None
    text = table(metrics(base), metrics(cand) if cand else None)
    return (1 if vetoes(base) else 0), {"verdict": verdict(base),
                                        "hard_vetoes": vetoes(base)}, text


def cmd_observe(args):
    return read_pair(args.shot, args.candidate)


def cmd_compare(args):
    return read_pair(args.baseline, args.candidate)


def cmd_feedback(args):
    path = Path(args.shot)
    record = shot_io.read_shot(path)
    given = {"status": args.status, "correction": args.correction,
             "sentiment": args.sentiment, "rank": args.rank}
    given = {k: v for k, v in given.items() if v is not None}
    if not given:
        raise Refused("feedback: give at least one of --status, --correction,"
                      " --sentiment, --rank")
    # A v1 file is history. Writing it would migrate it and rewrite the past.
    if shot_io.on_disk_version(path) == 1:
        raise Refused(f"{path}: version 1 is read-only, record a new shot")
    fields = dict(record["user_feedback"])
    fields.update(given)
    record["user_feedback"] = fields
    record = validate(record)
    shot_io.replace_shot(path, record)
    return 0, {"verdict": verdict(record), "user_feedback": fields}, verdict(record)


def cmd_assess(args):
    bundle = shot_io.load(args.evidence)
    turns = bundle.get("turns") if isinstance(bundle, dict) else None
    if not isinstance(turns, list) or any(not isinstance(t, str) for t in turns):
        raise Refused("$.turns: expected an array of strings", path="$.turns")
    found = [c._asdict() for c in advisory.assess(turns)]
    lines = [f"{c['field']} = {c['value']} ({c['confidence']})" for c in found]
    return 0, {"candidates": found}, "\n".join(lines) or "no candidates"


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
    out = rec.add_mutually_exclusive_group(required=True)
    out.add_argument("--output-manifest")
    out.add_argument("--inline")
    # Declared only so it stops being an abbreviation of --output-manifest.
    # Without it argparse expands the removed flag onto the new one and the
    # user's file is parsed as a manifest.
    out.add_argument("--output", help=argparse.SUPPRESS)
    rec.add_argument("--scope", default="")
    rec.add_argument("--model", default="unknown")
    rec.add_argument("--harness", default="unknown")
    rec.set_defaults(run=cmd_record)

    obs = sub.add_parser("observe", parents=[common], help="read one Shot")
    obs.add_argument("shot")
    obs.add_argument("candidate", nargs="?")
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
    fb.set_defaults(run=cmd_feedback)

    ass = sub.add_parser("assess-feedback", parents=[common], help="advisory candidates")
    ass.add_argument("--evidence", required=True)
    ass.set_defaults(run=cmd_assess)

    cor = sub.add_parser("correction", parents=[common],
                         help="a bounded bundle an adapter may act on")
    cor.add_argument("shot")
    cor.add_argument("--evidence", default="")
    cor.add_argument("--artifact", action="append", default=[])
    cor.set_defaults(run=cmd_correction)
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
