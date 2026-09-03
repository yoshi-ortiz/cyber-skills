#!/usr/bin/env python3
"""Bootstrap and validate a portable, read-only-source design harness."""

from __future__ import annotations

import argparse
import base64
import hashlib
import http.client
import json
import mimetypes
import os
import re
import time
import shutil
import subprocess
import sys
import tempfile
from html import escape as html_escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


# The import block above is kept whole even where this file no longer uses a
# name: `import bootstrap_harness` is the interface fourteen callers already
# hold, and dropping an import would take a name off it.
#
# Same reason for the star imports. The work behind the verbs moved into the
# modules below; every name the split moved out must still resolve from here,
# and naming them one at a time is a list that goes stale on the next move.

from harness_core import *  # noqa: F401,F403
from harness_strings import *  # noqa: F401,F403
from harness_ledger import *  # noqa: F401,F403
from harness_round import *  # noqa: F401,F403
from harness_preview import *  # noqa: F401,F403
from harness_comp import *  # noqa: F401,F403
from harness_controls import *  # noqa: F401,F403
from harness_board import *  # noqa: F401,F403
from harness_specimens import *  # noqa: F401,F403
from harness_article import *  # noqa: F401,F403
from harness_adoption import *  # noqa: F401,F403
from harness_init import *  # noqa: F401,F403
from harness_self_test import *  # noqa: F401,F403


# Stays here, not in harness_board with the rest of the lifecycle:
# test_article patches `board_is_up` and `start_companion` on THIS module,
# and a patch only reaches the caller that reads the name from here.
def open_board(project_root: Path, status: str = "",
               agent_url: str = "", agent_name: str = "") -> str:
    """Bring the companion up and return its URL. Stdout of the verb is this string."""
    project_root = project_root.resolve()
    agent_url, agent_name = resolve_agent(agent_url, agent_name, project_root)
    if agent_url or agent_name:
        save_companion_agent(project_root, agent_url, agent_name)
    ensure_brief(project_root)
    url = read_board_url(project_root)
    if not url or not board_is_up(url):
        url = start_companion(project_root)
    ensure_a_screen(project_root)
    if status.strip():
        try:
            from companion_doctor import push_status
            push_status(project_root, status)
        except Exception:
            pass
    return url


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description=__doc__)
    subcommands = command.add_subparsers(dest="command", required=True)
    opened = subcommands.add_parser(
        "open", help="start the companion if needed and print its URL")
    opened.add_argument("--project-root", required=True, type=Path)
    opened.add_argument("--status", default="",
                        help="what you are doing, in the user's language")
    opened.add_argument("--agent", default="", help="agent name for header and bottom bar")
    opened.add_argument("--agent-url", default="", help="deep link back to the agent chat")
    init = subcommands.add_parser("init")
    init.add_argument("--project-root", required=True, type=Path)
    init.add_argument("--source-root", required=True, type=Path)
    init.add_argument("--profiles", required=True)
    init.add_argument("--language", default=DEFAULT_LANGUAGE,
                      choices=sorted(STRINGS),
                      help="scoring-strip UI locale only (never chat language)")
    validate = subcommands.add_parser("validate")
    validate.add_argument("--project-root", required=True, type=Path)
    decide = subcommands.add_parser("decide", help="record a binding design decision")
    decide.add_argument("--project-root", required=True, type=Path)
    decide.add_argument("--element", required=True, help="stable dotted id, e.g. cover.layout.two-column")
    decide.add_argument("--verdict", required=True, choices=DECISION_STATES)
    decide.add_argument("--stars", required=True, type=int,
                        help=f"{ZERO_STARS} for agent proposals (blank until the user ranks); "
                             f"{STAR_RANGE[0]}-{STAR_RANGE[1]} when the user set the rank")
    decide.add_argument("--evidence", required=True, help="verbatim user excerpt, not a paraphrase")
    decide.add_argument("--supersedes", default="", help="comma-separated element ids this replaces")
    decide.add_argument("--preview", default="", help=(
        "the HTML comp of the element being ranked. That comp is canonical: the "
        "article inlines it and `review_delivery.py` refuses anything else. A "
        "PNG from `shoot` is for your own eyes and is accepted only when no comp "
        "exists -- record one and delivery rejects the round"))
    decide.add_argument("--title", default="",
                        help="what to CALL this design in plain words, e.g. "
                             "'Pestaña de rol coloreada'. The dotted id stays the "
                             "stable key; this is what the designer reads.")
    decide.add_argument("--description", default="",
                        help="what the component IS, in plain words (shown on the scoring row)")
    decide.add_argument("--implemented", default="",
                        help="what was actually built for it this time")
    decide.add_argument("--source", default="agent", choices=SOURCES,
                        help="agent (proposals store 0★ until the user ranks) or user (only via adopt)")
    describe = subcommands.add_parser(
        "describe", help="label an element without touching its verdict or rank")
    describe.add_argument("--project-root", required=True, type=Path)
    describe.add_argument("--element", required=True)
    describe.add_argument("--description", default="",
                          help="what the component IS, in plain words (shown on the scoring row)")
    describe.add_argument("--implemented", default="", help="what was actually built for it")
    describe.add_argument("--tokens", default="",
                          help='specimen data, JSON: {"colors":[{"name":..,"value":"#hex","role":..}],'
                               ' "fonts":[{"name":..,"stack":..,"use":..,"sample":..}]}')
    retire = subcommands.add_parser(
        "supersede", help="retire the losing element, leaving the winner's user rank intact")
    retire.add_argument("--project-root", required=True, type=Path)
    retire.add_argument("--element", required=True, help="the element being retired (the loser)")
    retire.add_argument("--by", required=True, dest="winner",
                        help="the element that beat it (left completely untouched)")
    retire.add_argument("--evidence", required=True, help="quote the user, do not paraphrase")
    adopt = subcommands.add_parser("adopt", help="fold companion star ranks into the ledger")
    adopt.add_argument("--project-root", required=True, type=Path)
    adopt.add_argument("--companion-ledger", required=True, type=Path,
                       help="path to the companion's durable decisions.jsonl")
    shoot = subcommands.add_parser(
        "shoot", help="render an HTML comp to a small PNG preview, and refuse it if it is blank")
    shoot.add_argument("--html", required=True, type=Path, help="the comp, drawn in HTML/CSS")
    shoot.add_argument("--out", required=True, type=Path, help="PNG to write, e.g. shots/<element>.png")
    shoot.add_argument("--width", type=int, default=PREVIEW_WIDTH)

    article = subcommands.add_parser(
        "article", help="generate the design-system article that is also the scoring companion")
    article.add_argument("--project-root", required=True, type=Path)
    article.add_argument("--out", required=True, type=Path, help="screen to write (then `publish` it)")
    article.add_argument("--cohort", default="", help="element ids this round asks about")
    article.add_argument("--cohort-name", default="", help="what to call this round, e.g. cover-furniture")
    article.add_argument("--round-label", default="",
                         help="object name for the round header, e.g. Micrófono. "
                              "Inferred from the cohort when omitted.")
    article.add_argument("--agent", default="",
                         help="App and model for the companion header, e.g. "
                              "'Cursor | Composer' or 'Composer' with a cursor:// URL. "
                              "The pipe is input only — the header renders them as "
                              "two weights with no separator. Empty hides the model line "
                              "rather than inventing one.")
    article.add_argument("--agent-url", default="",
                         help="deep link back to the agent's desktop app. Left empty "
                              "the header and the bottom bar render as plain text "
                              "rather than guessing a URL scheme.")
    article.add_argument("--working", action="store_true",
                         help="green pulsing dot while the agent is drawing; omit when waiting "
                              "on the user (idle text + orange dot)")
    article.add_argument("--asks", default="",
                         help="the one design question this round asks, in "
                              "project.json.language when that is set -- the screen is "
                              "one language throughout, controls and authored copy "
                              "alike. Required when the cohort is set. Do not paste "
                              "the zone note.")
    article.add_argument("--title", default="",
                         help="the artefact being designed, in the user's own words "
                              "(stored in project.json and reused)")
    article.add_argument("--lang", default="", choices=["", *sorted(STRINGS)])
    controls = subcommands.add_parser("controls", help="emit star + like/dislike controls from the ledger")
    controls.add_argument("--project-root", required=True, type=Path)
    controls.add_argument("--out", type=Path, help="write here instead of stdout")
    controls.add_argument("--shot-width", default="", help="preview frame width, e.g. 132px")
    controls.add_argument("--pin", default="", help="element ids to pin on top (this turn's work)")
    controls.add_argument("--lang", default="", choices=["", *sorted(STRINGS)],
                          help="override the project's stored language")
    controls.add_argument("--bg", default="", help="background color; declare the corpus palette, don't guess it")
    controls.add_argument("--ink", default="", help="text/border color")
    controls.add_argument("--accent", default="", help="accent color, e.g. the approved family accent")
    controls.add_argument("--font", default="", help="font-family stack")
    preflight = subcommands.add_parser("preflight", help="record observed adapter availability")
    preflight.add_argument("--project-root", required=True, type=Path)
    preflight.add_argument("--available", default="", help="comma-separated capabilities you verified")
    preflight.add_argument("--missing", default="", help="comma-separated capabilities you confirmed absent")
    doctor = subcommands.add_parser("doctor", help="health-check the whole feedback path end to end")
    doctor.add_argument("--project-root", required=True, type=Path)
    doctor.add_argument("--quiet", action="store_true",
                        help="print the companion URL only; for a design run, not a diagnosis dump")
    status_cmd = subcommands.add_parser(
        "status", help="update the companion bottom bar without publishing a new round")
    status_cmd.add_argument("--project-root", required=True, type=Path)
    status_cmd.add_argument("--text", default="",
                            help="what you are doing, in the user's language")
    status_cmd.add_argument("--idle", action="store_true",
                            help="waiting on ranks; clears the working state")
    embed = subcommands.add_parser("embed", help="fill data-dh-controls placeholders with generated rows")
    embed.add_argument("--project-root", required=True, type=Path)
    embed.add_argument("--screen", required=True, type=Path)
    for token in ("bg", "ink", "accent", "font"):
        embed.add_argument(f"--{token}", default="")
    embed.add_argument("--shot-width", default="")
    embed.add_argument("--pin", default="", help="element ids to pin on top (this turn's work)")
    publish = subcommands.add_parser("publish", help="make a screen the one the companion serves")
    publish.add_argument("--project-root", required=True, type=Path)
    publish.add_argument("--screen", required=True, type=Path)
    stats = subcommands.add_parser("stats", help="deterministic statistics over the ledger")
    stats.add_argument("--project-root", required=True, type=Path)
    stats.add_argument("--json", action="store_true", help="machine-readable output")
    audit_svg = subcommands.add_parser(
        "audit-svg", help="list ledger elements whose recorded preview hand-authors <svg>")
    audit_svg.add_argument("--project-root", required=True, type=Path)
    subcommands.add_parser("self-test")
    return command


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "open":
            print(open_board(args.project_root, args.status, args.agent_url, args.agent))
        elif args.command == "init":
            output = init_harness(args.project_root, args.source_root,
                              parse_profiles(args.profiles), args.language)
            print(output)
        elif args.command == "validate":
            report = validate_harness(args.project_root) or {}
            drift, warns = report.get("corpusDrift", []), report.get("warnings", [])
            print("Ledger is coherent." if not warns else "Ledger is coherent, with notes:")
            for w in warns:
                print(f"  note: {w}")
            if drift:
                print(f"Corpus drift ({len(drift)} file(s)) -- unrelated to the ledger, triage separately:")
                for d in drift[:10]:
                    print(f"  {d}")
            else:
                print("Corpus unchanged.")
        elif args.command == "decide":
            supersedes = [item.strip() for item in args.supersedes.split(",") if item.strip()]
            preview = (preview_reference(args.project_root, args.preview, args.element)
                       if args.preview else None)
            decisions = record_decision(args.project_root, args.element, args.verdict,
                                        args.stars, args.evidence, supersedes, preview,
                                        source=args.source,
                                        implemented=args.implemented or None,
                                        description=args.description or None,
                                        title=args.title or None)
            stored = next(e for e in decisions["elements"] if e["element"] == args.element)
            live = [e for e in decisions["elements"] if e["state"] in ("approved", "proposed")]
            print(f"Recorded {args.element} ({args.verdict}, {stored['stars']}★). "
                  f"{len(live)} element(s) standing, state={decisions['state']}.")
        elif args.command == "describe":
            entry = describe_element(args.project_root, args.element,
                                     args.description or None, args.implemented or None,
                                     parse_tokens(args.tokens) if args.tokens else None)
            print(f"Labelled {args.element} (still {entry['state']}, {entry['stars']}★, "
                  f"set by {entry.get('source', 'unknown')}).")
        elif args.command == "supersede":
            entry = retire_element(args.project_root, args.element, args.winner, args.evidence)
            print(f"Retired {args.element} in favour of {args.winner}. "
                  f"{args.winner} was not written -- its rank and source are untouched.")
        elif args.command == "audit-svg":
            hits = audit_recorded_svg(args.project_root)
            if not hits:
                print("No recorded preview hand-authors <svg>.")
            else:
                # Non-zero, because a check that cannot fail is a comment. This
                # printed three violations and exited 0 while the round that
                # carried them shipped.
                print(f"{len(hits)} recorded preview(s) hand-author <svg> -- redraw in HTML/CSS "
                     "and `shoot` + `decide --preview` again:", file=sys.stderr)
                for hit in hits:
                    print(f"  {hit['element']}\t{hit['path']}", file=sys.stderr)
                return 1
        elif args.command == "shoot":
            check_no_hand_authored_svg(args.html)
            renderer = render_html_preview(args.html, args.out, args.width)
            check_preview_legible(args.out)
            ink = preview_ink(args.out)
            size = args.out.stat().st_size
            print(f"Wrote {args.out} via {renderer} ({size // 1024}KB, "
                  + (f"{ink['coverage'] * 100:.1f}% ink" if ink else "ink unmeasured")
                  + "). Record it with `decide --preview`.")
        elif args.command == "article":
            root = args.project_root.resolve(strict=True)
            # Drain before building. A round assembled over an undrained queue
            # silently overwrites the ranks and the brief answer the user
            # already gave, and asks them the same question again.
            drain_companion(root)
            cohort = {e.strip() for e in args.cohort.split(",") if e.strip()}
            decisions = load_decisions(root / "spec" / "design-harness")
            canonicalize_recorded_previews(root, decisions)
            known = {e["element"] for e in decisions["elements"]}
            unknown = sorted(cohort - known)
            if unknown:
                raise HarnessError("cohort names element(s) not in the ledger: " + ", ".join(unknown))
            check_round_earns_its_place(decisions, cohort)
            if args.title:
                # Remembered, so the next run does not have to be told again --
                # and so a forgotten flag cannot silently rename the artefact.
                path = root / "spec" / "design-harness" / "project.json"
                stored = json.loads(path.read_text(encoding="utf-8"))
                stored["title"] = args.title
                write_json(path, stored)
            if args.agent_url.strip() or args.agent.strip():
                save_companion_agent(root, args.agent_url, args.agent)
            markup = render_article(root, decisions, cohort, cohort_name=args.cohort_name,
                                    language=args.lang or None, title=args.title,
                                    asks=args.asks, agent_url=args.agent_url,
                                    agent_name=args.agent, round_label=args.round_label,
                                    agent_working=args.working)
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(markup, encoding="utf-8")
            print(f"Wrote {args.out.name}: {len(cohort)} element(s) in this round's cohort. "
                  f"Run `publish` to serve it.")
        elif args.command == "adopt":
            adopted, skipped = drain_companion(args.project_root, args.companion_ledger)
            print(f"Adopted {adopted} ranked decision(s); skipped {skipped} "
                  f"interaction(s) with no design-element id or usable signal.")
            # Everything else the user typed arrives on the same trip. Folding
            # these in here rather than as extra SKILL.md commands keeps the
            # entry cost at zero: `adopt` already means "read what the user
            # told us", and the companion writes all of it to one directory.
            try:
                import brief_workflow
                said, _ = brief_workflow.adopt_brief_inbox(
                    args.project_root,
                    args.project_root / ".superpowers" / "brainstorm"
                    / brief_workflow.BRIEF_INBOX_FILE)
                if said:
                    print(f"Adopted {said} brief answer(s).")
            except (ImportError, OSError, ValueError):
                pass
            try:
                import corpus_tags
                tags_in, _ = corpus_tags.adopt_inbox(
                    args.project_root, args.project_root / corpus_tags.DEFAULT_INBOX)
                rows = corpus_tags.digest_rows(args.project_root)
                if tags_in or any(r["aspect"] != "untagged" for r in rows):
                    print(f"Adopted {tags_in} corpus tag(s).")
                    sys.stdout.write(corpus_tags.render_digest(rows))
            except (ImportError, OSError, ValueError):
                pass
        elif args.command == "preflight":
            split = lambda raw: [i.strip() for i in raw.split(",") if i.strip()]
            matrix = record_preflight(args.project_root, split(args.available), split(args.missing))
            ready = [i["category"] for i in matrix["requiredCapabilities"] if i["available"]]
            blocked = [i["category"] for i in matrix["requiredCapabilities"] if not i["available"]]
            print(f"Available: {', '.join(ready) or 'none'}")
            print(f"Not preflighted or missing: {', '.join(blocked) or 'none'}")
        elif args.command == "embed":
            theme = {t: getattr(args, t) for t in ("bg", "ink", "accent", "font") if getattr(args, t)}
            if args.shot_width:
                theme["shot"] = args.shot_width
            count = embed_controls(args.project_root, args.screen, theme or None,
                                   {i.strip() for i in args.pin.split(",") if i.strip()})
            print(f"Embedded {count} generated row(s) into {args.screen.name}. "
                  f"Run `publish` to make it the served screen.")
        elif args.command == "publish":
            published = publish_screen(args.project_root, args.screen)
            print(f"Serving {published.name}. Any screen written after this steals the route -- "
                  f"re-run `publish` if you write another.")
        elif args.command == "stats":
            output = args.project_root.resolve(strict=True) / "spec" / "design-harness"
            report = ledger_stats(load_decisions(output))
            if args.json:
                print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
            else:
                bars = "  ".join(f"{n}:{report['histogram'][n]}" for n in sorted(report["histogram"]))
                print(f"standing {report['standing']}  "
                      f"user-set {report['userSet']}  agent-set {report['agentSet']}  "
                      f"coverage {report['coverage']:.0%}")
                print(f"stars    mean {report['meanStars']}  median {report['medianStars']}  [{bars}]")
                print(f"signals  {report['likes']} like  {report['dislikes']} dislike  "
                      f"{report['completed']} completed  {report['approved']} approved  "
                      f"{report['rejected']} rejected  "
                      f"{report['superseded']} superseded")
                if report["needsPolish"]:
                    print(f"polish   {len(report['needsPolish'])} (good idea, execution not there yet): "
                          + ", ".join(report["needsPolish"][:5]))
                if report["conflicts"]:
                    print(f"conflict {len(report['conflicts'])}: " + ", ".join(report["conflicts"][:5]))
                if report["unscored"]:
                    print(f"unscored {len(report['unscored'])}: " + ", ".join(report["unscored"][:5]))
        elif args.command == "doctor":
            script = Path(__file__).resolve().parent / "companion_doctor.py"
            cmd = [sys.executable, str(script), str(args.project_root)]
            if args.quiet:
                cmd.append("--quiet")
            return subprocess.call(cmd)
        elif args.command == "status":
            from companion_doctor import push_status
            push_status(args.project_root, args.text, idle=args.idle)
            print("status idle" if args.idle or not args.text.strip() else "status updated")
        elif args.command == "controls":
            output = args.project_root.resolve(strict=True) / "spec" / "design-harness"
            theme = {"bg": args.bg, "ink": args.ink, "accent": args.accent,
                     "font": args.font, "shot": args.shot_width}
            pins = {i.strip() for i in args.pin.split(",") if i.strip()}
            markup = render_feedback_controls(load_decisions(output), theme,
                                              args.project_root.resolve(strict=True), pins)
            if args.out:
                args.out.write_text(markup, encoding="utf-8")
                print(f"Wrote feedback controls to {args.out}")
            else:
                print(markup, end="")
        else:
            self_test()
            print("Self-test passed.")
        return 0
    except (HarnessError, OSError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
