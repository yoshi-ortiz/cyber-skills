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
from pathlib import Path

HERE = Path(__file__).resolve().parent
KEY = re.compile(r"[?&]key=([0-9a-f]+)")


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
    harness = str(HERE / "bootstrap_harness.py")
    article = [harness, "article", "--out", out, "--cohort", cohort,
               "--round-label", round_label, "--asks", asks]
    if agent:
        article += ["--agent", agent]
    if agent_url:
        article += ["--agent-url", agent_url]
    step(article, project_root)

    published = step([harness, "publish", "--screen", out], project_root)
    url = next((line for line in published.splitlines() if line.startswith("http")),
               published)
    if not url.startswith("http"):
        raise DeliveryError(f"publish returned no URL: {published!r}")

    # Review images are the half a user can act on. No assessments means the
    # caller has nothing to show, which is a refusal, not a quiet skip.
    if not assessments:
        raise DeliveryError("no --assessments: a published round with no review "
                            "images is a link the user cannot act on")
    images = step([str(HERE / "review_delivery.py"), "--cohort", cohort,
                   "--assessments", assessments], project_root)

    step([harness, "status", "--idle", "--text", idle_text], project_root)

    found = KEY.search(url)
    return {"url": url, "key": found.group(1) if found else "",
            "ask": asks, "images": json.loads(images) if images else []}


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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
