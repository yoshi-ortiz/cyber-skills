#!/usr/bin/env python3
"""Publish a round and hand back what the reply must lead with.

The four calls that end every round -- `article`, `publish`, `review_delivery`,
`status --idle` -- always run together, in that order, and the failure this
prevents is dropping the last two. A screen that was written but not published
is a URL showing "Waiting for the agent to push a screen...", and a publish
with no review images is a link the user cannot act on. Both used to be one
forgotten line of prose away, because the order lived only in `SKILL.md`.

It lives here instead, so the order is a thing that runs rather than a thing an
agent is asked to remember.

    python3 deliver.py --project-root . --out design/aesthetic-ranking.html \
        --cohort "hero.a,hero.b" --round-label "hero" \
        --asks "How strong is this proposal?" \
        --assessments /tmp/proposal-assessments.json \
        --idle-text "Revisa los nuevos diseños"

Prints one JSON object: url, key, ask, and every absolute review image path.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
KEY = re.compile(r"[?&]key=([0-9a-f]+)")

# Resolved from this file, never from the cwd: `deliver.py` is called with a
# --project-root that is not necessarily the repo it lives in.
REPO_ROOT = HERE.parents[2]
TOKENS_QA = REPO_ROOT / "check" / "tokens-qa" / "scripts" / "tokens_qa.py"


class DeliveryError(Exception):
    """A step refused. The round is not delivered and the reply has no URL."""


def step(argv: list[str], project_root: Path) -> str:
    done = subprocess.run([sys.executable, *argv, "--project-root", str(project_root)],
                          capture_output=True, text=True)
    if done.returncode != 0:
        name = Path(argv[0]).stem
        raise DeliveryError(f"{name} {argv[1] if len(argv) > 1 else ''}: "
                            f"{(done.stderr or done.stdout).strip()}")
    return done.stdout.strip()


def deliver(project_root: Path, out: str, cohort: str, round_label: str, asks: str,
            assessments: str | None, idle_text: str, agent: str = "",
            agent_url: str = "") -> dict:
    # Review images are the half a user can act on. No assessments means the
    # caller has nothing to show, which is a refusal, not a quiet skip.
    #
    # Checked FIRST, before anything is written or served. It used to sit after
    # `article` and `publish`, so the refusal arrived having already replaced
    # the live screen -- the round was published, and only then declared
    # undeliverable. A precondition that needs no subprocess belongs before the
    # steps that mutate what the user is looking at.
    if not assessments:
        raise DeliveryError("no --assessments: a published round with no review "
                            "images is a link the user cannot act on")

    harness = str(HERE / "bootstrap_harness.py")
    article = [harness, "article", "--out", out, "--cohort", cohort,
               "--round-label", round_label, "--asks", asks]
    if agent:
        article += ["--agent", agent]
    if agent_url:
        article += ["--agent-url", agent_url]
    step(article, project_root)

    step([harness, "publish", "--screen", out], project_root)

    # The URL comes from `open`, not from `publish`.
    #
    # `publish` prints one line -- "Serving <name>. Any screen written after
    # this steals the route" -- and has never printed a URL at all. Scanning
    # its stdout for a line starting with "http" therefore found nothing on
    # every run, and the guard below it turned that into a hard failure. So
    # this script, whose entire reason to exist is that `article`, `publish`,
    # `review_delivery` and `status --idle` must run TOGETHER, aborted after
    # step two of four -- every time it was called. The round was published
    # with no review images and no idle status, which is precisely the
    # "a link the user cannot act on" failure the module docstring describes.
    #
    # `open` is the verb that owns the URL, and it is idempotent: it starts the
    # companion only if it is not already up, and prints the URL either way.
    url = step([harness, "open"], project_root).strip()
    if not url.startswith("http"):
        raise DeliveryError(f"open returned no URL: {url!r}")

    images = step([str(HERE / "review_delivery.py"), "--cohort", cohort,
                   "--assessments", assessments], project_root)

    step([harness, "status", "--idle", "--text", idle_text], project_root)

    found = KEY.search(url)
    return {"url": url, "key": found.group(1) if found else "",
            "ask": asks, "images": json.loads(images) if images else []}


def record_shot(payload: dict, round_label: str, asks: str) -> None:
    """Write the delivered round to the Shot ledger, so QA has something to read."""
    images = payload.get("images") or {}
    declared = images.get("images", []) if isinstance(images, dict) else []
    artifacts = [{"path": item["image_path"], "role": "deliverable",
                  "mime": "image/png"}
                 for item in declared if isinstance(item, dict) and item.get("image_path")]
    if not artifacts:
        return
    with tempfile.TemporaryDirectory(prefix="deliver-shot-") as staging:
        stage = Path(staging)
        request = stage / "request.txt"
        request.write_text(asks, encoding="utf-8")
        manifest = stage / "manifest.json"
        manifest.write_text(json.dumps({"adapter": "graphic",
                                        "artifacts": artifacts}),
                            encoding="utf-8")
        done = subprocess.run(
            [sys.executable, str(TOKENS_QA), "record", "first/aesthetic",
             "--request", str(request), "--output-manifest", str(manifest),
             "--scope", round_label],
            cwd=str(REPO_ROOT), capture_output=True, text=True)
    if done.returncode != 0:
        raise DeliveryError((done.stderr or done.stdout).strip())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--out", required=True, help="screen to write, then publish")
    parser.add_argument("--cohort", required=True)
    parser.add_argument("--round-label", required=True)
    parser.add_argument("--asks", required=True)
    parser.add_argument("--assessments", help="proposal assessments JSON")
    parser.add_argument("--idle-text", required=True,
                        help="user-language review request for the idle status")
    parser.add_argument("--agent", default="")
    parser.add_argument("--agent-url", default="")
    args = parser.parse_args(argv)
    try:
        payload = deliver(args.project_root.resolve(), args.out, args.cohort,
                          args.round_label, args.asks, args.assessments,
                          args.idle_text, args.agent, args.agent_url)
    except DeliveryError as refused:
        print(f"deliver: {refused}", file=sys.stderr)
        return 1
    json.dump(payload, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    # Recording happens HERE, not inside `deliver`, and it cannot fail the
    # round. `deliver` already shells four subprocesses that each get to
    # refuse; a fifth that could turn a delivered round into a failed one buys
    # nothing, because by this line the screen is live and the payload is
    # printed. An unrecorded round is a gap in QA, not a broken delivery.
    try:
        record_shot(payload, args.round_label, args.asks)
    except Exception as unrecorded:
        print(f"deliver: round delivered but not recorded: {unrecorded}",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
