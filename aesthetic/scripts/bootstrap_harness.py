#!/usr/bin/env python3
"""Bootstrap and validate a portable, read-only-source design harness."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import mimetypes
import os
import re
import time
import shutil
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path


VERSION = 1
PROFILES = {
    "frontend-layout": ["repository", "knowledge", "http", "image", "pdf", "devtools", "playwright", "lighthouse", "storybook"],
    "art-direction": ["repository", "knowledge", "http", "image", "pdf", "licensing"],
    "motion": ["repository", "knowledge", "browser", "playwright", "motion-renderer"],
    "composition": ["repository", "image", "pdf", "browser"],
    "physical-space": ["repository", "image", "pdf", "geometry", "standards"],
    "product-design": ["repository", "knowledge", "image", "pdf", "materials", "standards"],
    "copywriting": ["repository", "knowledge", "http", "copy-evidence"],
    "mockup-layering": ["repository", "image", "pdf", "layer-renderer", "color-management"],
}
RECOMMENDATIONS = {
    "frontend-layout": [
        ("frontend-browser", "Confirm DevTools MCP, Playwright, Lighthouse, responsive screenshot, and Storybook MCP adapters."),
    ],
    "art-direction": [
        ("ascii-library", "The agent must evaluate whether a pinned, licensed ASCII/Unicode art library fits the evidence; approve, reject, or replace the proposed source."),
        ("art-assets", "Confirm authoritative icon, illustration, texture, or type sources inferred from the visual grammar."),
    ],
    "motion": [
        ("motion-source", "Confirm a pinned motion library or primary choreography reference, including reduced-motion behavior."),
    ],
    "composition": [
        ("composition-source", "Confirm the proposed grid, editorial composition, or framing reference source."),
    ],
    "physical-space": [
        ("spatial-source", "Confirm applicable measurement, accessibility, safety, lighting, and material standards."),
    ],
    "product-design": [
        ("product-source", "Confirm applicable ergonomic, material, manufacturing, packaging, and regulatory sources."),
    ],
    "copywriting": [
        ("copy-source", "Confirm audience research, claim evidence, voice references, legal constraints, and localization sources."),
    ],
    "mockup-layering": [
        ("mockup-renderer", "Confirm a deterministic layer renderer and pin its version, color profile, and export settings."),
    ],
}
TEMPLATE_NAMES = ("CONTEXT.md", "CONTRACTS.md", "WORKFLOWS.md")
# OS-generated sidecars mutate whenever a folder is merely browsed. Hashing them
# wires the integrity gate to noise: Finder opening the source root turns every
# later run red while nothing about the evidence changed.
NOISE_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini", ".localized"}
NOISE_DIRS = {".Spotlight-V100", ".fseventsd", ".TemporaryItems", "__MACOSX"}
# A decision is binding until superseded. `stars` is the deterministic standing
# used to rank competing elements; it is set by the user, never by the agent.
# `completed` is a status, not a lock: "this one is finished for now". It does
# not mean approved and does not freeze the element -- iteration continues.
DECISION_STATES = ("proposed", "completed", "approved", "superseded", "rejected")
# Stars rate GRAPHIC EXECUTION ONLY: ugly -> beautiful. Not confidence, not
# priority, not "should we do this".
# ZERO IS A REAL SCORE AND IT IS THE WORST ONE: "this is genuinely bad".
# It is not "no opinion". The difference between "judged terrible" and "never
# looked at" is carried by `scored`, not by the number.
# A zero still does NOT change state -- rating a thing badly is not deleting it.
# Only an explicit verdict moves an element between groups.
STAR_RANGE = (1, 5)
ZERO_STARS = 0
# The two signals answer different questions and must never be collapsed:
#   stars    = how well the thing is DRAWN (ugly -> beautiful). Execution.
#   thumbs   = whether the DIRECTION is worth pursuing. Encouragement.
# So "thumbs up + one star" is not a contradiction, it is the most actionable
# state in the system: good idea, execution not beautiful yet -> improve it,
# never drop it. Collapsing these is what caused ideas to be discarded.
SENTIMENTS = {"like": "encouraged", "dislike": "discouraged"}
# A score never changes an element's state. Removal is always a deliberate act
# (`decide --supersedes` or an explicit reject control), because reading a low
# score as "delete this" already destroyed work the user wanted kept.
SCORE_NEVER_REMOVES = True
# A preview is the graphic the star is actually about.
PREVIEW_SUFFIXES = {".svg", ".html", ".png", ".jpg", ".jpeg", ".webp", ".gif"}
# Who set a rank. The distinction is the whole point: an agent-typed number and
# a user click used to be indistinguishable in the ledger.
# Three lifecycle groups the user reads at a glance. Derived from state, never
# stored separately, so a state change cannot leave the group stale.
GROUPS = (
    ("brainstorming", "Lluvia de ideas", ("proposed",)),
    ("developing", "En desarrollo", ("completed", "approved")),
    ("rejected", "Descartado", ("rejected", "superseded")),
)
GROUP_OF = {state: key for key, _, states in GROUPS for state in states}
SOURCES = ("user", "agent")
AGENT_MAX_STARS = 1


class HarnessError(Exception):
    pass


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def source_entries(source_root: Path) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for path in sorted(source_root.rglob("*"), key=lambda item: item.as_posix()):
        if path.is_symlink():
            raise HarnessError(f"source contains a symlink: {path.relative_to(source_root)}")
        if path.is_dir():
            continue
        relative = path.relative_to(source_root)
        if path.name in NOISE_NAMES or NOISE_DIRS.intersection(relative.parts):
            continue
        if not path.is_file():
            raise HarnessError(f"source contains an unsupported entry: {path.relative_to(source_root)}")
        media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        entries.append({
            "path": path.relative_to(source_root).as_posix(),
            "bytes": path.stat().st_size,
            "mediaType": media_type,
            "sha256": sha256_file(path),
        })
    return entries


def parse_profiles(raw: str) -> list[str]:
    profiles = sorted({item.strip() for item in raw.split(",") if item.strip()})
    unknown = sorted(set(profiles) - set(PROFILES))
    if unknown:
        raise HarnessError(f"unknown profile(s): {', '.join(unknown)}")
    if not profiles:
        raise HarnessError("at least one profile is required")
    return profiles


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def questionnaire(profiles: list[str]) -> str:
    lines = [
        "# Design Harness Questionnaire",
        "",
        "Answer each recommendation with approve, reject, or replace. The agent proposes likely sources; the user does not need to invent them.",
        "",
        "## Project constraints",
        "",
        "1. Confirm the intended output, audience, approval authority, and release boundary.",
        "2. Confirm rights for the configured source-root evidence.",
        "3. Confirm which proposed external sources may be fetched and pinned.",
        "",
        "## Sourcing recommendations",
        "",
    ]
    number = 1
    for profile in profiles:
        for recommendation_id, prompt in RECOMMENDATIONS[profile]:
            lines.append(f"{number}. **{recommendation_id}** (`{profile}`): {prompt}")
            number += 1
    lines.extend([
        "",
        "For every approved source, record its primary URL or package, license, pinned version/edition/commit, retrieval method, expected tool cost, and SHA-256.",
        "",
    ])
    return "\n".join(lines)


def empty_decisions() -> dict[str, object]:
    return {"version": VERSION, "state": "draft", "elements": [], "supersededCount": 0}


def load_decisions(output: Path) -> dict[str, object]:
    path = output / "decisions.json"
    if not path.is_file():
        raise HarnessError("decisions.json is missing; run `init` or re-bootstrap")
    return json.loads(path.read_text(encoding="utf-8"))


def render_decisions_md(decisions: dict[str, object]) -> str:
    live = [e for e in decisions["elements"] if e["state"] in ("approved", "proposed")]
    dead = [e for e in decisions["elements"] if e["state"] in ("superseded", "rejected")]
    lines = [
        "# Design Decisions",
        "",
        "Generated by `bootstrap_harness.py decide`. Do not hand-edit.",
        "",
        "**Binding for any agent resuming this project.** An element listed under",
        "Standing may not be replaced, restyled, or dropped without an explicit",
        "`decide --supersedes` recorded here first. Chat history is not a record.",
        "",
        f"Lifecycle state: `{decisions['state']}`",
        "",
        "## Standing",
        "",
    ]
    if live:
        lines += ["| Element | Verdict | Stars | Evidence |", "| --- | --- | --- | --- |"]
        for e in sorted(live, key=lambda x: (-x["stars"], x["element"])):
            stars = "★" * e["stars"] + "☆" * (STAR_RANGE[1] - e["stars"])
            lines.append(f"| `{e['element']}` | {e['state']} | {stars} | {e['evidence']} |")
    else:
        lines.append("_No decisions recorded yet._")
    if dead:
        lines += ["", "## Superseded", ""]
        for e in sorted(dead, key=lambda x: x["element"]):
            note = f" → `{e['supersededBy']}`" if e.get("supersededBy") else ""
            lines.append(f"- ~~`{e['element']}`~~ ({e['state']}){note} — {e['evidence']}")
    return "\n".join(lines) + "\n"


def record_decision(project_root: Path, element: str, verdict: str, stars: int,
                    evidence: str, supersedes: list[str],
                    preview: dict[str, str] | None = None,
                    source: str = "agent",
                    sentiment: str | None = None,
                    implemented: str | None = None,
                    description: str | None = None) -> dict[str, object]:
    output = project_root.resolve(strict=True) / "spec" / "design-harness"
    if verdict not in DECISION_STATES:
        raise HarnessError(f"verdict must be one of: {', '.join(DECISION_STATES)}")
    if stars != ZERO_STARS and not STAR_RANGE[0] <= stars <= STAR_RANGE[1]:
        raise HarnessError(f"stars must be {STAR_RANGE[0]}-{STAR_RANGE[1]}, "
                           f"or {ZERO_STARS} meaning bad execution")
    if not evidence.strip():
        raise HarnessError("evidence is required: quote the user, do not paraphrase")
    if source not in SOURCES:
        raise HarnessError(f"source must be one of: {', '.join(SOURCES)}")
    if source == "agent" and stars > AGENT_MAX_STARS:
        raise HarnessError(
            f"agent-set rank is capped at {AGENT_MAX_STARS} star. A higher rank must come from a "
            "user click, adopted with `adopt` -- typing the number yourself is the failure this "
            "cap exists to prevent.")
    decisions = load_decisions(output)
    known = {e["element"] for e in decisions["elements"]}
    missing = [s for s in supersedes if s not in known]
    if missing:
        raise HarnessError(f"cannot supersede unknown element(s): {', '.join(missing)}")
    for e in decisions["elements"]:
        if e["element"] in supersedes:
            e["state"] = "superseded"
            e["supersededBy"] = element
            decisions["supersededCount"] += 1
        elif e["element"] == element:
            e["state"], e["stars"], e["evidence"] = verdict, stars, evidence
            e["source"] = source
            e["scored"] = True
            if implemented is not None:
                e["implemented"] = implemented
            if description is not None:
                e["description"] = description
            e.setdefault("implemented", None)
            e.setdefault("description", None)
            if sentiment is not None:
                e["sentiment"] = sentiment
            e.setdefault("sentiment", None)
            if preview is not None:
                e["preview"] = preview
            e.setdefault("preview", None)
            break
    else:
        decisions["elements"].append({
            "element": element, "state": verdict, "stars": stars,
            "evidence": evidence, "supersededBy": None, "preview": preview,
            "source": source, "sentiment": sentiment, "scored": True,
            "implemented": implemented, "description": description,
        })
    if any(e["state"] == "approved" for e in decisions["elements"]):
        decisions["state"] = "approved"
    elif decisions["state"] == "draft":
        decisions["state"] = "proposed"
    write_json(output / "decisions.json", decisions)
    (output / "DECISIONS.md").write_text(render_decisions_md(decisions), encoding="utf-8")
    project_path = output / "project.json"
    project = json.loads(project_path.read_text(encoding="utf-8"))
    project["state"] = decisions["state"]
    write_json(project_path, project)
    return decisions


def describe_element(project_root: Path, element: str,
                     description: str | None, implemented: str | None) -> dict[str, object]:
    """Label an existing element without touching its verdict, rank or source.

    `decide` cannot do this: it demands a verdict and a rank, so relabelling a
    user-ranked row means retyping the user's stars -- the invention the star cap
    exists to prevent.
    """
    output = project_root.resolve(strict=True) / "spec" / "design-harness"
    if description is None and implemented is None:
        raise HarnessError("nothing to set: pass --description and/or --implemented")
    decisions = load_decisions(output)
    for entry in decisions["elements"]:
        if entry["element"] == element:
            break
    else:
        raise HarnessError(f"unknown element: {element}. Record it with `decide` first.")
    if description is not None:
        entry["description"] = description
    if implemented is not None:
        entry["implemented"] = implemented
    write_json(output / "decisions.json", decisions)
    (output / "DECISIONS.md").write_text(render_decisions_md(decisions), encoding="utf-8")
    return entry


def adopt_companion(project_root: Path, ledger_path: Path) -> tuple[int, int]:
    """Fold the companion's durable ledger into the harness ledger.

    The companion records what the user actually clicked and ranked. Without this
    step an agent re-types those decisions by hand, which is where design-element
    ids drift and elements in standing get silently rebuilt.
    """
    if not ledger_path.is_file():
        raise HarnessError(f"companion ledger not found: {ledger_path}")

    def is_star(value: object) -> bool:
        if not isinstance(value, int) or isinstance(value, bool):
            return False
        return value == ZERO_STARS or STAR_RANGE[0] <= value <= STAR_RANGE[1]

    output = project_root.resolve(strict=True) / "spec" / "design-harness"
    existing = {e["element"]: e for e in load_decisions(output)["elements"]}
    accepted: list[tuple[int, int, str, str, int, str, str | None]] = []
    resets: list[tuple[int, int, str]] = []
    skipped = 0
    for index, line in enumerate(ledger_path.read_text(encoding="utf-8").splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            skipped += 1
            continue
        element = event.get("element")
        stars, sentiment = event.get("stars"), event.get("sentiment")
        if event.get("type") == "reset" or event.get("reset") is True:
            # The zero-star control. "This is bad" is a rating the user must be
            # able to give, and the 1-5 strip cannot express it.
            resets.append((int(event.get("timestamp") or 0), index, element))
            continue
        # An interaction carrying no design-element id names a screen-local
        # label, not a binding element. Report it rather than guessing an id.
        if not element or not isinstance(element, str):
            skipped += 1
            continue
        if event.get("verdict") not in (None, "approved", "rejected", "completed"):
            skipped += 1
            continue
        if sentiment is not None and sentiment not in SENTIMENTS:
            skipped += 1
            continue
        if sentiment is None and event.get("verdict") is None and not is_star(stars):
            skipped += 1
            continue
        explicit = event.get("verdict")
        prior = existing.get(element, {})
        if explicit in ("approved", "rejected", "completed"):
            # Only an explicit verdict control moves state. A star never does.
            verdict = explicit
            rank = stars if is_star(stars) else prior.get("stars", 0)
        else:
            # Scores and thumbs leave state alone: an element already standing
            # stays standing, and a new one arrives as `proposed` for review.
            verdict = prior.get("state") or "proposed"
            if verdict in ("superseded", "rejected"):
                verdict = "proposed"
            rank = stars if is_star(stars) else prior.get("stars", 0)
        evidence = str(event.get("text") or "").strip() or (
            f"companion {sentiment}: {rank} star" if sentiment else f"companion rank: {rank} star")
        # Replay order is fixed by (timestamp, file position) so adopting the
        # same ledger twice always yields the same ledger.
        stamp = event.get("timestamp")
        stamp = stamp if isinstance(stamp, (int, float)) and not isinstance(stamp, bool) else 0
        accepted.append((int(stamp), index, element, verdict, rank, evidence[:400], sentiment))

    for _, _, element, verdict, rank, evidence, mood in sorted(accepted, key=lambda row: (row[0], row[1])):
        record_decision(project_root, element, verdict, rank, evidence, [], source="user",
                        sentiment=mood)
    for _, _, element in sorted(resets, key=lambda row: (row[0], row[1])):
        score_zero(project_root, element)
    return len(accepted), skipped


# Every token has a var()-with-fallback, never a bare literal. Two ways to set
# them, both deterministic:
#   1. Pass --bg/--ink/--accent/--font to `controls`; values are baked into an
#      inline style on the wrapper, so the same flags always emit the same
#      bytes.
#   2. Pass none, and nest the output inside a screen that already sets
#      --dh-bg/--dh-ink/--dh-accent/--dh-font on an ancestor (every screen this
#      harness has produced does, since C2/rev13 scope --bg/--acc per card) --
#      the cascade fills the fallback. Either way there is no hardcoded color
#      the harness's own approved palette (`palette.family-from-cards`) can be
#      overridden by.
# Inline so a host stylesheet cannot collapse the one element the user must see.
# The fallback MUST match the grid track in FEEDBACK_STYLE. When it did not, the
# graphic rendered wider than its column and sat on top of the description text.
SHOT_INLINE = ("display:block;flex:0 0 auto;inline-size:var(--dh-shot-w,96px);"
               "block-size:calc(var(--dh-shot-w,96px) * 11 / 8.5);overflow:hidden;"
               "position:relative;border:1px solid currentColor;background:#fff")
SHOT_INNER_INLINE = ("position:absolute;inset-block-start:0;inset-inline-start:0;"
                     "inline-size:850px;block-size:1100px;transform-origin:0 0;"
                     "transform:scale(calc(var(--dh-shot-w,96px) / 850));pointer-events:none")
STYLE_MARKER = "/* dh-controls */"
# Bumped whenever the emitted CSS or markup changes. `embed` bakes both into the
# screen, so a screen embedded by an older skill keeps the older bug forever and
# looks, from the browser, exactly like a fix that did not work. `doctor`
# compares this against the served page and fails on a mismatch.
CONTROLS_VERSION = "11"
VERSION_MARKER = "dh-controls-version"

# Restores the signals a refresh would otherwise throw away.
#
# The served screen is a static snapshot: `embed` bakes each row's stars into
# the HTML, and the companion re-serves that same file on every request. Clicks
# travel out to the durable ledger and nothing ever brings them back, so every
# refresh silently reverted the user's scoring to whatever the agent last
# published -- the single defect behind "the score is not being saved".
#
# The durable ledger stays the source of truth for `adopt`; this only keeps the
# screen from lying to the person clicking it. Capture phase, so it reads each
# control's state before the companion's own handler toggles it.
REHYDRATE_SCRIPT = """<script>/* dh-rehydrate */
(function(){
 if(window.__dhRehydrated)return; window.__dhRehydrated=1;
 var KEY='dh-signals';
 /* Every row carries the ledger revision it was baked from. A re-`embed`
    republishes the ledger's own numbers, so anything cached against an older
    revision is stale by definition and must lose to what the agent just baked.
    Without this gate an overlay would keep resurrecting superseded scores. */
 var first=document.querySelector('.dh-fb[data-dh-rev]');
 var rev=first?first.getAttribute('data-dh-rev'):'';
 var read=function(){try{
   var s=JSON.parse(localStorage.getItem(KEY)||'null');
   if(!s||s.rev!==rev||!s.el)return {rev:rev,el:{}};
   return s;}catch(e){return {rev:rev,el:{}}}};
 var state=read();
 /* localStorage, never sessionStorage: sessionStorage is scoped to ONE tab, so
    two tabs on the same screen drifted into different scores with no way to
    tell which was real. Shared storage survives refresh AND new tabs; the
    channel below is what makes an open tab update the instant another scores. */
 var write=function(){try{localStorage.setItem(KEY,JSON.stringify(state))}catch(e){}};
 var chan=null; try{chan=new BroadcastChannel('dh-signals')}catch(e){}
 function paint(row,s){
  if(typeof s.stars==='number'){
   row.dataset.stars=String(s.stars); row.dataset.scored='yes';
   row.querySelectorAll('[data-rank]').forEach(function(b){
    var n=parseInt(b.dataset.rank,10);
    b.classList.toggle('on', n===0 ? s.stars===0 : (n>0&&n<=s.stars));});
  }
  if('sentiment' in s) row.querySelectorAll('[data-sentiment]').forEach(function(b){
    b.classList.toggle('on', b.dataset.sentiment===s.sentiment);});
  if('verdict' in s) row.querySelectorAll('[data-verdict]').forEach(function(b){
    b.classList.toggle('on', b.dataset.verdict===s.verdict);});
 }
 /* Wait for the rows. `embed` injects this ahead of the markup -- into <head>
    when the screen has one, otherwise at the very top of the file -- so at
    execution time the document holds no rows at all, and an immediate pass
    painted nothing while looking, by every attribute, perfectly correct. */
 function rowFor(el){
  var all=document.querySelectorAll('.dh-fb[data-element]');
  for(var i=0;i<all.length;i++) if(all[i].getAttribute('data-element')===el) return all[i];
  return null;}
 function applyAll(){document.querySelectorAll('.dh-fb[data-element]').forEach(function(row){
  var s=state.el[row.getAttribute('data-element')]; if(s)paint(row,s);});}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',applyAll);
 else applyAll();
 document.addEventListener('click',function(e){
  var row=e.target.closest?e.target.closest('.dh-fb[data-element]'):null; if(!row)return;
  var r=e.target.closest('[data-rank]'),m=e.target.closest('[data-sentiment]'),
      v=e.target.closest('[data-verdict]');
  if(!r&&!m&&!v)return;
  var el=row.getAttribute('data-element');
  var s=state.el[el]||(state.el[el]={});
  if(r)s.stars=parseInt(r.dataset.rank,10);
  if(m)s.sentiment=m.classList.contains('on')?null:m.dataset.sentiment;
  if(v)s.verdict=v.classList.contains('on')?null:v.dataset.verdict;
  write();
  if(chan)try{chan.postMessage({rev:rev,el:el,s:s})}catch(_){}
  /* Repaint after the companion's own handler has run. A companion that lights
     every control whose rank is <= the score lights the zero as well, so a
     5-star row drew "0 1 2 3 4 5" all lit at once. Deferring by one task lets
     this own the final state without the skill depending on any companion. */
  setTimeout(function(){paint(row,s)},0);
 },true);
 /* Instant fan-out to every other open tab. The storage event below is the
    fallback where BroadcastChannel is unavailable; it also covers a tab that
    was closed while another scored and is reopened later. */
 function accept(msg){
  if(!msg||msg.rev!==rev||!msg.el)return;
  state.el[msg.el]=msg.s;
  var row=rowFor(msg.el); if(row)paint(row,msg.s);}
 if(chan)chan.onmessage=function(e){accept(e.data)};
 window.addEventListener('storage',function(e){
  if(e.key!==KEY)return; state=read(); applyAll();});
 /* The channel above only reaches tabs in THIS browser profile -- storage and
    BroadcastChannel are both per profile. Two different browsers, or two
    machines, never see each other that way. The companion socket is the only
    shared point, so subscribe to its fan-out and treat it as authoritative. */
 function fold(ev){
  if(!ev||!ev.element)return;
  var s=state.el[ev.element]||(state.el[ev.element]={});
  if(ev.reset===true||ev.type==='reset')s.stars=0;
  else if(typeof ev.stars==='number')s.stars=ev.stars;
  if('sentiment' in ev)s.sentiment=ev.sentiment;
  if(ev.verdict==='completed'||ev.verdict==='approved')s.verdict='completed';
  else if(ev.verdict==='proposed')s.verdict=null;
  state.el[ev.element]=s; write();
  var row=rowFor(ev.element); if(row)paint(row,s);}
 (function socket(){
  var url=(location.protocol==='https:'?'wss://':'ws://')+location.host+'/';
  var ws; try{ws=new WebSocket(url)}catch(e){return}
  ws.onmessage=function(e){
   var m; try{m=JSON.parse(e.data)}catch(_){return}
   if(m&&m.type==='dh-signal')fold(m.event);};
  /* A dropped socket means silently going stale, which is worse than a visible
     gap -- reconnect, and repaint from shared storage on the way back. */
  ws.onclose=function(){setTimeout(function(){state=read();applyAll();socket()},1500)};
 })();
})();
</script>"""
FEEDBACK_STYLE = """<style>/* dh-controls */
/* Owned by the aesthetic skill. Do not restyle in a project: every local
   patch so far has produced specificity fights and unusable controls.
   `.dh-fb.dh-fb` doubles specificity so a host rule cannot flatten it. */
/* Both wrappers establish the container. `controls --out` emits .dh-feedback,
   but `embed` lifts the rows out of it into the project's own placeholder, so
   on every embedded screen there was no container at all and the responsive
   rule below could never match -- the signals stayed on the row and ran off
   the right edge however narrow the description column got. */
.dh-feedback,[data-dh-controls]{container-type:inline-size;display:flex;
 flex-direction:column;gap:6px}
.dh-offline{display:block;background:#b00020;color:#fff;font:700 12px/1.4 ui-monospace,monospace;
 padding:9px 11px;border-radius:6px}
:root[data-dh-live] .dh-offline{display:none}
/* The description column carries a floor. At minmax(0,1fr) the signals column
   took its full max-content width and squeezed the text to about 80px, where
   `overflow-wrap:anywhere` broke every word mid-syllable -- "cover.sp / ine.righ
   / t" -- and the strip became unreadable while every control still worked. */
.dh-fb.dh-fb{display:grid;grid-template-columns:var(--dh-shot-w,96px) minmax(26ch,1fr) auto;
 gap:16px;align-items:center;padding:13px 15px;border:1px solid rgba(0,0,0,.14);
 border-radius:10px;background:var(--dh-bg,#fff);color:var(--dh-ink,#111);
 font:500 13px/1.45 var(--dh-font,ui-monospace,SFMono-Regular,Menlo,monospace);
 contain:layout style;content-visibility:auto;contain-intrinsic-size:auto 120px}
.dh-fb.dh-fb:hover{border-color:var(--dh-ink,#111)}
.dh-fb .dh-meta{display:flex;flex-direction:column;gap:5px;min-width:0}
/* Five stacked lines of near-identical grey monospace is what made the strip
   tiring to read. Hierarchy now: the id leads, the description is the line you
   actually read, provenance is demoted to a labelled aside, and the state sits
   beside the id instead of adding a fifth line. */
.dh-fb .dh-head{display:flex;align-items:baseline;gap:9px;flex-wrap:wrap;min-width:0}
.dh-fb .dh-id{font-weight:700;font-size:14px;letter-spacing:-.01em;
 overflow-wrap:anywhere;color:var(--dh-ink,#111)}
.dh-fb .dh-state{font-size:9.5px;letter-spacing:.11em;text-transform:uppercase;
 padding:2px 6px;border-radius:3px;white-space:nowrap;
 background:color-mix(in srgb, var(--dh-ink,#111) 8%, transparent);
 color:color-mix(in srgb, var(--dh-ink,#111) 62%, transparent)}
.dh-fb .dh-desc{font-size:13px;line-height:1.5;overflow-wrap:break-word;
 color:color-mix(in srgb, var(--dh-ink,#111) 88%, transparent)}
/* provenance, not prose: smaller, dimmer, with a micro-label instead of a
   run-on bold prefix inside the sentence */
.dh-fb .dh-sub{font-size:11.5px;line-height:1.45;display:flex;gap:7px;
 color:color-mix(in srgb, var(--dh-ink,#111) 58%, transparent)}
.dh-fb .dh-sub b{font-weight:700;font-size:9px;letter-spacing:.1em;
 text-transform:uppercase;flex:none;padding-top:2px;
 color:color-mix(in srgb, var(--dh-ink,#111) 62%, transparent)}
.dh-fb .dh-signals{display:flex;gap:8px;align-items:center}
/* One continuous strip: zero is a first-class score, not a hidden reset. */
.dh-fb .dh-stars{display:flex;align-items:center;gap:0}
.dh-fb .dh-stars > *{min-inline-size:32px;min-block-size:34px;display:grid;place-items:center;
 cursor:pointer;user-select:none;font-size:21px;line-height:1;border:0;background:transparent;
 color:color-mix(in srgb, var(--dh-ink,#111) 26%, transparent);transition:color .12s}
.dh-fb .dh-stars > *.on{color:var(--dh-accent,#d9482a)}
/* Hover previews the RANK, not one glyph. Every star up to the pointer lights,
   and the standing score steps aside for the duration so the preview is the
   only thing being read. Without both halves, hovering the 2nd star of a
   4-star row changed nothing at all, and hovering the 5th lit a gap-toothed
   1,2,3,5 -- which is what "the hover is buggy" was pointing at. */
.dh-fb .dh-stars:hover [data-rank]{color:color-mix(in srgb, var(--dh-ink,#111) 26%, transparent)}
.dh-fb .dh-stars [data-rank]:hover,
.dh-fb .dh-stars [data-rank]:has(~ [data-rank]:hover){color:var(--dh-accent,#d9482a)}
/* The zero lives OUTSIDE the star strip, and stays out of the way until the
   user actually reaches for the bottom of the scale: it surfaces on hovering
   ONE star. It is always visible when it IS the score, so a zero already given
   can never be mistaken for an unrated row.
   While hidden it is also unclickable. That pairing is the whole point -- an
   invisible-but-clickable zero sitting beside the first star is exactly how a
   click aimed at 1 used to score 0, and a mis-hit zero used to wipe the thumb
   and the tick along with it. Never set the opacity without the pointer-events.
   The spacing is padding, not margin: a margin here is dead ground where
   neither control is hovered, and the zero vanished as the pointer crossed it. */
.dh-fb .dh-zero{display:flex;align-items:center;padding-inline-end:13px;
 border-inline-end:1px solid rgba(0,0,0,.18);opacity:0;transition:opacity .12s}
.dh-fb [data-rank="0"]{min-inline-size:30px;min-block-size:34px;display:grid;place-items:center;
 cursor:pointer;user-select:none;border:0;background:transparent;font-size:13px;font-weight:700;
 line-height:1;color:color-mix(in srgb, var(--dh-ink,#111) 40%, transparent);
 transition:color .12s;pointer-events:none}
.dh-fb .dh-zero:has([data-rank="0"].on),.dh-fb .dh-zero:hover,
.dh-fb .dh-zero:has(:focus-visible),
.dh-fb .dh-zero:has(~ .dh-stars [data-rank="1"]:hover){opacity:1}
.dh-fb .dh-zero:has([data-rank="0"].on) [data-rank="0"],
.dh-fb .dh-zero:hover [data-rank="0"],
.dh-fb .dh-zero:has(:focus-visible) [data-rank="0"],
.dh-fb .dh-zero:has(~ .dh-stars [data-rank="1"]:hover) [data-rank="0"]{pointer-events:auto}
.dh-fb [data-rank="0"]:hover,.dh-fb [data-rank="0"].on{color:#b00020}
.dh-fb [data-sentiment],.dh-fb [data-verdict]{min-inline-size:38px;min-block-size:34px;
 display:grid;place-items:center;cursor:pointer;user-select:none;font-size:15px;
 border:1px solid rgba(0,0,0,.22);border-radius:6px;background:transparent;line-height:1}
.dh-fb [data-sentiment]:hover,.dh-fb [data-verdict]:hover{border-color:var(--dh-ink,#111)}
.dh-fb [data-sentiment="like"].on{background:#1c8b4b;border-color:#126435;color:#fff}
.dh-fb [data-sentiment="dislike"].on{background:#b00020;border-color:#8a0019;color:#fff}
/* Approve reads as done: green fill, white tick, unmistakable. */
.dh-fb [data-verdict].on{background:#1c8b4b;border-color:#126435;color:#fff;font-weight:800}
.dh-fb [data-rank]:focus-visible,.dh-fb [data-sentiment]:focus-visible,
.dh-fb [data-verdict]:focus-visible{outline:2px solid var(--dh-accent,#d9482a);outline-offset:2px}
.dh-group{margin:14px 0 2px;display:flex;align-items:center;gap:8px;
 font:700 11px/1 var(--dh-font,ui-monospace,monospace);letter-spacing:.14em;
 text-transform:uppercase;color:var(--dh-ink,#111);opacity:.75}
.dh-group:first-child{margin-top:0}
.dh-group .dh-count{font-weight:600;opacity:.6}
.dh-group::after{content:"";flex:1;height:1px;background:currentColor;opacity:.25}
.dh-group[data-group="rejected"]{color:#b00020;opacity:.85}
.dh-fb[data-group="rejected"]{opacity:.62}
.dh-fb[data-group="rejected"]:hover{opacity:1}
.dh-shot{display:block;inline-size:var(--dh-shot-w,96px);aspect-ratio:8.5/11;overflow:hidden;
 position:relative;border:1px solid rgba(0,0,0,.25);border-radius:4px;background:#fff;contain:strict}
.dh-shot svg{inline-size:100%;block-size:100%;display:block}
.dh-shot img{inline-size:100%;block-size:100%;object-fit:contain;display:block}
.dh-shot-missing{display:grid;place-items:center;text-align:center;padding:6px;
 font-size:9px;opacity:.6;block-size:100%}
@container (max-width: 780px){
 .dh-fb.dh-fb{grid-template-columns:var(--dh-shot-w,96px) minmax(0,1fr)}
 .dh-fb .dh-signals{grid-column:1 / -1;justify-content:flex-start}
}
@media (prefers-reduced-motion:reduce){.dh-fb *{transition:none!important}}
</style>"""

# The stamp rides the stylesheet because that is the one asset `embed` always
# rewrites into the screen. On the wrapper it never survived: `embed` lifts the
# rows out of the generated block and leaves the wrapper behind.
FEEDBACK_STYLE = FEEDBACK_STYLE.replace(
    STYLE_MARKER, f"{STYLE_MARKER}\n/* dh-controls-version: {CONTROLS_VERSION} */", 1)


def preview_reference(project_root: Path, raw: str) -> dict[str, str]:
    """Resolve and hash a preview graphic for a design element.

    Stored as a project-relative path plus a hash, on the same principle as the
    corpus manifest: a preview that silently changed is a preview nobody
    completed.
    """
    project_root = project_root.resolve(strict=True)
    candidate = (project_root / raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
    if not is_within(candidate, project_root):
        raise HarnessError("preview must live inside the project root")
    if not candidate.is_file():
        raise HarnessError(f"preview not found: {raw}")
    if candidate.suffix.lower() not in PREVIEW_SUFFIXES:
        raise HarnessError(f"unsupported preview type '{candidate.suffix}'; use one of "
                           + ", ".join(sorted(PREVIEW_SUFFIXES)))
    return {"path": candidate.relative_to(project_root).as_posix(), "sha256": sha256_file(candidate)}


def render_preview(project_root: Path | None, preview: dict[str, str] | None, element: str) -> str:
    """Inline the graphic for one element, or say plainly that there is none."""
    if not preview:
        return (f'<span class="dh-shot" style="{SHOT_INLINE}">'
                '<span class="dh-shot-missing">sin gráfico<br>--preview</span></span>')
    if project_root is None:
        return (f'<span class="dh-shot" style="{SHOT_INLINE}">'
                f'<span class="dh-shot-missing">{preview["path"]}</span></span>')
    path = (project_root / preview["path"])
    if not path.is_file():
        return (f'<span class="dh-shot" style="{SHOT_INLINE}">'
                f'<span class="dh-shot-missing">gráfico ausente<br>{preview["path"]}</span></span>')
    suffix = path.suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
        media = "image/jpeg" if suffix in {".jpg", ".jpeg"} else f"image/{suffix.lstrip('.')}"
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        body = f'<img alt="" src="data:{media};base64,{encoded}">'
        return f'<span class="dh-shot" style="{SHOT_INLINE}">{body}</span>'
    # svg / html fragment: scaled inside a clipped frame rather than reflowed
    fragment = path.read_text(encoding="utf-8")
    if suffix == ".svg":
        # Force the root <svg> to fill the frame regardless of its own width/height attrs.
        fragment = re.sub(r"<svg\b", '<svg preserveAspectRatio="xMidYMid meet" '
                          'style="width:100%;height:100%;display:block"', fragment, count=1)
        return f'<span class="dh-shot" style="{SHOT_INLINE}">{fragment}</span>'
    return (f'<span class="dh-shot" style="{SHOT_INLINE}">'
            f'<span class="dh-shot-inner" style="{SHOT_INNER_INLINE}">{fragment}</span></span>')


def render_feedback_controls(decisions: dict[str, object], theme: dict[str, str] | None = None,
                             project_root: Path | None = None,
                             pinned: set[str] | None = None) -> str:
    """Emit rank + sentiment controls for every element in standing.

    Generated from the ledger so a screen cannot invent a design-element id.
    Each row carries the graphic being ranked: a star next to a dotted id is a
    guess, not a judgement. Same ledger, theme and previews in, byte-identical
    markup out.
    """
    pinned = pinned or set()
    live = [e for e in decisions["elements"] if e["state"] in GROUP_OF]
    # Fingerprint of what the ledger says right now. Baked onto every row so a
    # browser can tell "these numbers are the ones I already have" from "the
    # agent adopted and re-embedded, throw my cached overlay away".
    ledger_rev = hashlib.sha256("|".join(
        f'{e["element"]}:{e["stars"]}:{e.get("sentiment")}:{e["state"]}:{e.get("scored")}'
        for e in sorted(live, key=lambda e: e["element"])).encode()).hexdigest()[:12]
    theme_vars = {
        "--dh-bg": "bg", "--dh-ink": "ink", "--dh-accent": "accent",
        "--dh-font": "font", "--dh-shot-w": "shot",
    }
    wrapper_style = ""
    if theme:
        declared = "; ".join(f"{prop}: {theme[key]}" for prop, key in theme_vars.items() if theme.get(key))
        if declared:
            wrapper_style = f' style="{declared}"'
    lines = [FEEDBACK_STYLE, REHYDRATE_SCRIPT,
             f'<div class="dh-feedback" data-{VERSION_MARKER}="{CONTROLS_VERSION}"{wrapper_style}>',
             '<strong class="dh-offline">Sin conexión al companion: estos clics NO se guardan. '
             'Abre la URL del companion (http://localhost:PORT/?key=...), no el archivo.</strong>']
    if not live:
        lines.append("<!-- no elements in standing; record one with `decide` first -->")
    group_index = {key: n for n, (key, _, _) in enumerate(GROUPS)}
    def order(item: dict[str, object]) -> tuple:
        # Pinned work from this turn first, then group order, then best
        # execution first, then id so the output stays byte-stable.
        return (0 if item["element"] in pinned else 1,
                group_index[GROUP_OF[item["state"]]],
                -int(item.get("stars") or 0),
                item["element"])
    rendered_group = None
    for entry in sorted(live, key=order):
        is_pinned = entry["element"] in pinned
        group_key = "pinned" if is_pinned else GROUP_OF[entry["state"]]
        if group_key != rendered_group:
            rendered_group = group_key
            label = ("De esta ronda" if is_pinned else
                     next(n for k, n, _ in GROUPS if k == group_key))
            tally = sum(1 for e in live
                        if ("pinned" if e["element"] in pinned else GROUP_OF[e["state"]]) == group_key)
            lines.append(f'<h4 class="dh-group" data-group="{group_key}">{label}<span class="dh-count">{tally}</span></h4>')
        element, stars = entry["element"], entry["stars"]
        lines.append(
            f'<div class="dh-fb" data-element="{element}" data-stars="{stars}" '
            f'data-scored="{"yes" if entry.get("scored") else "no"}" '
            f'data-dh-rev="{ledger_rev}" '
            f'data-group="{GROUP_OF[entry["state"]]}" data-label="{element}">'
        )
        lines.append(render_preview(project_root, entry.get("preview"), element))
        lines.append('<span class="dh-meta">')
        unscored = "" if entry.get("scored") else " &middot; sin puntuar"
        # The state rides beside the id instead of trailing the block as a fifth
        # line of near-identical grey text.
        lines.append(f'<span class="dh-head"><span class="dh-id">{element}</span>'
                     f'<span class="dh-state">{entry["state"]}{unscored}</span></span>')
        what = str(entry.get("description") or "").strip()
        proposed = str(entry.get("evidence") or "").strip()
        built = str(entry.get("implemented") or "").strip()
        if what:
            lines.append(f'<span class="dh-desc">{what}</span>')
        # Evidence that only repeats the id is noise: it printed
        # "Propuesto: palette.role-groups-three" directly under the heading
        # "palette.role-groups-three" on almost every row.
        if proposed and proposed != element:
            lines.append(f'<span class="dh-desc dh-sub"><b>Propuesto</b>{proposed}</span>')
        if built:
            lines.append(f'<span class="dh-desc dh-sub"><b>Implementado</b>{built}</span>')
        lines.append("</span>")
        lines.append('<span class="dh-signals">')
        stars_markup = "".join(
            f'<span data-rank="{n}" role="button" tabindex="0" aria-label="{n} de {STAR_RANGE[1]}: calidad de ejecucion"'
            + (' class="on"' if 0 < n <= stars else "") + ">&#9733;</span>"
            for n in range(STAR_RANGE[0], STAR_RANGE[1] + 1)
        )
        # The zero is a rank, so it rides the rank code path: it scores 0 and
        # touches nothing else. Emitted as `data-reset` it hit a companion
        # handler that also stripped the thumb and the tick -- a score silently
        # erasing two unrelated signals, which is the one thing the contract
        # says a score must never do.
        zero_on = ' class="on"' if entry.get("scored") and stars == ZERO_STARS else ""
        lines.append(
            f'<span class="dh-zero"><span data-rank="0" role="button" tabindex="0" '
            f'title="cero estrellas: pesimo, pero sigue en pie" '
            f'aria-label="cero estrellas para {element}: pesima ejecucion"{zero_on}>0</span></span>'
            f'<span class="dh-stars" role="group" aria-label="ejecucion de {element}">'
            f'{stars_markup}</span>')
        mood = entry.get("sentiment")
        for name, glyph, label in (("like", "&#128077;", "me gusta"), ("dislike", "&#128078;", "no me gusta")):
            on = ' class="on"' if mood == name else ""
            lines.append(f'<span data-sentiment="{name}" role="button" tabindex="0" '
                         f'aria-label="{label} {element}" title="{label}"{on}>{glyph}</span>')
        # A status, not a lock: "this one is done for now". Toggleable, and it never
        # freezes the element -- iteration continues after it is checked.
        done = entry["state"] in ("completed", "approved")
        on = ' class="on"' if done else ""
        lines.append(f'<span data-verdict="completed" role="button" tabindex="0" '
                     f'aria-pressed="{"true" if done else "false"}" '
                     f'aria-label="completado: {element}" title="completado"{on}>'
                     f'<span>&#10003;</span></span>')
        lines.append("</span>")
        lines.append("</div>")
    lines.append("</div>")
    return "\n".join(lines) + "\n"


def record_preflight(project_root: Path, available: list[str], missing: list[str]) -> dict[str, object]:
    """Record which adapters were actually observed, per the compute invariant.

    The agent cannot detect its own MCP wiring from inside this script, so
    availability is asserted explicitly and stored. An adapter that was never
    preflighted stays `available: false` -- absence of evidence is not
    availability.
    """
    output = project_root.resolve(strict=True) / "spec" / "design-harness"
    matrix_path = output / "capability-matrix.json"
    if not matrix_path.is_file():
        raise HarnessError("capability-matrix.json is missing; run `init` first")
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    claimed = {item["category"] for item in matrix.get("requiredCapabilities", [])}
    unknown = sorted((set(available) | set(missing)) - claimed)
    if unknown:
        raise HarnessError("capability not required by the selected profiles: " + ", ".join(unknown))
    both = sorted(set(available) & set(missing))
    if both:
        raise HarnessError("capability marked both available and missing: " + ", ".join(both))
    for item in matrix["requiredCapabilities"]:
        if item["category"] in available:
            item["available"] = True
        elif item["category"] in missing:
            item["available"] = False
    write_json(matrix_path, matrix)
    return matrix


def newest_session_dir(project_root: Path) -> Path:
    root = project_root / ".superpowers" / "brainstorm"
    sessions = [d for d in root.glob("*/") if (d / "content").is_dir()] if root.is_dir() else []
    if not sessions:
        raise HarnessError("no companion session found; start the companion first")
    return max(sessions, key=lambda d: d.stat().st_mtime)


def embed_controls(project_root: Path, screen: Path, theme: dict[str, str] | None = None,
                   pinned: set[str] | None = None) -> int:
    """Fill a screen's `data-dh-controls` placeholders with generated rows.

    Without this, an agent wanting scoring inside a prototype hand-writes the
    markup and silently drops the component graphic -- which is exactly what
    happened. The placeholder names the elements; the harness supplies the row.
    """
    project_root = project_root.resolve(strict=True)
    output = project_root / "spec" / "design-harness"
    html = screen.read_text(encoding="utf-8")
    generated = render_feedback_controls(load_decisions(output), theme, project_root, pinned)
    rows = {m.group(1): m.group(0) for m in re.finditer(
        r'<div class="dh-fb" data-element="([^"]+)".*?\n</div>', generated, re.S)}
    style_match = re.search(r"<style>.*?</style>", generated, re.S)
    style = style_match.group(0) if style_match else ""
    script_match = re.search(r"<script>/\* dh-rehydrate \*/.*?</script>", generated, re.S)
    script = script_match.group(0) if script_match else ""

    # Match the placeholder's OWN closing tag by counting nested divs. The old
    # non-greedy `(.*?)</div>` stopped at the first </div> inside a generated
    # row, so re-running embed duplicated every row and orphaned the remainder.
    placeholders = []
    for opening in re.finditer(r'<div([^>]*?)data-dh-controls="([^"]*)"([^>]*?)>', html):
        depth, cursor = 1, opening.end()
        for tag in re.finditer(r"<(/?)div\b[^>]*>", html[opening.end():]):
            depth += -1 if tag.group(1) else 1
            if depth == 0:
                cursor = opening.end() + tag.end()
                break
        else:
            raise HarnessError("unbalanced <div> around a data-dh-controls placeholder")
        placeholders.append((opening, cursor))
    if not placeholders:
        raise HarnessError(
            'no <div data-dh-controls="element.a,element.b"></div> placeholder in the screen. '
            "Add one where scoring belongs -- never hand-write the rows.")

    filled = 0
    # Right to left so earlier offsets stay valid. Each placeholder's contents
    # are replaced wholesale, which is what makes embed safe to re-run.
    for opening, close_end in reversed(placeholders):
        wanted = [e.strip() for e in opening.group(2).split(",") if e.strip()]
        missing = [e for e in wanted if e not in rows]
        if missing:
            raise HarnessError("placeholder names element(s) not in standing: " + ", ".join(missing))
        body = "\n".join(rows[e] for e in wanted)
        replacement = (f'<div{opening.group(1)}data-dh-controls="{opening.group(2)}"'
                       f'{opening.group(3)}>\n{body}\n</div>')
        html = html[:opening.start()] + replacement + html[close_end:]
        filled += len(wanted)

    # Replace the assets, never skip them. `embed` used to inject the stylesheet
    # only when the screen carried none, so a screen embedded by an older skill
    # kept that older CSS for the rest of its life: fixing a control bug in the
    # skill changed nothing the user could see, and the only symptom was "the
    # fix did not work". Stripping first also keeps `embed` byte-idempotent.
    html = re.sub(r"<style>/\* dh-controls \*/.*?</style>\n?", "", html, flags=re.S)
    html = re.sub(r"<script>/\* dh-rehydrate \*/.*?</script>\n?", "", html, flags=re.S)
    head = "\n".join(part for part in (style, script) if part)
    if head:
        html = (html.replace("</head>", head + "\n</head>", 1)
                if "</head>" in html else head + "\n" + html)
    screen.write_text(html, encoding="utf-8")
    return filled


def publish_screen(project_root: Path, screen: Path, gap_seconds: int = 5) -> Path:
    """Make one screen the served one, deterministically.

    The companion serves only the newest-mtime file. Doing that by hand invites
    both a silent redirect and an mtime race, so the harness does it: the chosen
    screen is stamped a clear margin ahead of every other screen.
    """
    session = newest_session_dir(project_root.resolve(strict=True))
    content = session / "content"
    if screen.resolve().parent != content.resolve():
        raise HarnessError(f"screen must live in the served session: {content}")
    others = [p for p in content.glob("*.html") if p.resolve() != screen.resolve()]
    newest_other = max((p.stat().st_mtime for p in others), default=0.0)
    stamp = max(time.time(), newest_other + gap_seconds)
    os.utime(screen, (stamp, stamp))
    return screen


def score_zero(project_root: Path, element: str) -> None:
    """Score an element zero: the worst rating, deliberately given.

    This is a judgement, not an erasure -- `scored` stays true. A zero says the
    execution is bad; it says nothing about whether the element should exist,
    so state is left exactly where it was.
    """
    output = project_root.resolve(strict=True) / "spec" / "design-harness"
    decisions = load_decisions(output)
    for entry in decisions["elements"]:
        if entry["element"] == element:
            # Encouragement and completion are separate signals with their
            # own controls; a zero touches the execution score only.
            entry["stars"] = ZERO_STARS
            entry["scored"] = True
            break
    write_json(output / "decisions.json", decisions)
    (output / "DECISIONS.md").write_text(render_decisions_md(decisions), encoding="utf-8")


def ledger_stats(decisions: dict[str, object]) -> dict[str, object]:
    """Deterministic aggregates over the ledger. Same ledger, same numbers.

    The headline is `coverage`: what fraction of standing elements carry a
    signal the user actually set. A high star average means nothing if the
    agent typed all of it.
    """
    elements = decisions["elements"]
    live = [e for e in elements if e["state"] in ("approved", "proposed")]
    user = [e for e in live if e.get("source") == "user"]
    ranked = sorted((e["stars"] for e in user))

    def median(values: list[int]) -> float:
        if not values:
            return 0.0
        mid = len(values) // 2
        return float(values[mid]) if len(values) % 2 else (values[mid - 1] + values[mid]) / 2

    histogram = {str(n): sum(1 for e in user if e["stars"] == n)
                 for n in range(STAR_RANGE[0], STAR_RANGE[1] + 1)}
    # A user who liked something but scored it low, or disliked something still
    # standing, is telling you something an average would hide.
    # Good idea, not yet beautiful: improve the drawing, never drop it.
    needs_polish = sorted(e["element"] for e in live
                          if e.get("sentiment") == "like" and e["stars"] <= 2)
    # Well drawn but the direction is discouraged: that is the real contradiction.
    conflicts = sorted(e["element"] for e in live
                       if e.get("sentiment") == "dislike" and e["stars"] >= 4)
    return {
        "standing": len(live),
        "userSet": len(user),
        "agentSet": len(live) - len(user),
        "coverage": round(len(user) / len(live), 3) if live else 0.0,
        "meanStars": round(sum(ranked) / len(ranked), 2) if ranked else 0.0,
        "medianStars": median(ranked),
        "histogram": histogram,
        "likes": sum(1 for e in live if e.get("sentiment") == "like"),
        "dislikes": sum(1 for e in live if e.get("sentiment") == "dislike"),
        "approved": sum(1 for e in elements if e["state"] == "approved"),
        "completed": sum(1 for e in elements if e["state"] == "completed"),
        "rejected": sum(1 for e in elements if e["state"] == "rejected"),
        "superseded": sum(1 for e in elements if e["state"] == "superseded"),
        "unscored": sorted(e["element"] for e in live if e.get("source") != "user"),
        "conflicts": conflicts, "needsPolish": needs_polish,
    }


def init_harness(project_root: Path, source_root: Path, profiles: list[str]) -> Path:
    project_root = project_root.resolve(strict=True)
    source_root = source_root.resolve(strict=True)
    if not project_root.is_dir() or not source_root.is_dir():
        raise HarnessError("project root and source root must be directories")
    output = project_root / "spec" / "design-harness"
    if is_within(output.resolve(), source_root):
        raise HarnessError("generated harness cannot live inside the read-only source root")

    before = source_entries(source_root)
    output.mkdir(parents=True, exist_ok=True)
    template_root = Path(__file__).resolve().parent.parent / "assets" / "spec"
    for name in TEMPLATE_NAMES:
        template = template_root / f"{name}.tmpl"
        if not template.is_file():
            raise HarnessError(f"missing skill template: {template}")
        (output / name).write_bytes(template.read_bytes())

    project = {
        "version": VERSION,
        "sourceRoot": str(source_root),
        "sourcePolicy": "read-only",
        "profiles": profiles,
        "state": "draft",
        "budgets": {"toolCalls": 4, "urls": 2, "newVisuals": 4, "extractedChars": 24000, "outputTokens": 1200},
    }
    capabilities = sorted({capability for profile in profiles for capability in PROFILES[profile]})
    matrix = {
        "version": VERSION,
        "profiles": profiles,
        "requiredCapabilities": [{"category": category, "adapter": None, "available": False} for category in capabilities],
        "promotionChecks": ["source-integrity", "lineage", "user-approval", "domain-conformance"],
    }
    manifest = {"version": VERSION, "algorithm": "sha256", "sourceRoot": str(source_root), "entries": before}
    write_json(output / "project.json", project)
    write_json(output / "capability-matrix.json", matrix)
    write_json(output / "source-manifest.json", manifest)
    (output / "QUESTIONNAIRE.md").write_text(questionnaire(profiles), encoding="utf-8")
    if not (output / "decisions.json").is_file():
        decisions = empty_decisions()
        write_json(output / "decisions.json", decisions)
        (output / "DECISIONS.md").write_text(render_decisions_md(decisions), encoding="utf-8")

    after = source_entries(source_root)
    if before != after:
        raise HarnessError("source root changed during bootstrap")
    return output


def validate_harness(project_root: Path) -> None:
    output = project_root.resolve(strict=True) / "spec" / "design-harness"
    required = [*TEMPLATE_NAMES, "project.json", "capability-matrix.json", "source-manifest.json",
                "QUESTIONNAIRE.md", "decisions.json", "DECISIONS.md"]
    missing = [name for name in required if not (output / name).is_file()]
    if missing:
        raise HarnessError(f"missing generated file(s): {', '.join(missing)}")
    project = json.loads((output / "project.json").read_text(encoding="utf-8"))
    manifest = json.loads((output / "source-manifest.json").read_text(encoding="utf-8"))
    matrix = json.loads((output / "capability-matrix.json").read_text(encoding="utf-8"))
    if project.get("sourcePolicy") != "read-only" or project.get("sourceRoot") != manifest.get("sourceRoot"):
        raise HarnessError("source-root contract is missing or contradictory")
    profiles = project.get("profiles")
    if not isinstance(profiles, list) or any(profile not in PROFILES for profile in profiles):
        raise HarnessError("project contains unknown profiles")
    expected_capabilities = sorted({capability for profile in profiles for capability in PROFILES[profile]})
    actual_capabilities = sorted(item.get("category") for item in matrix.get("requiredCapabilities", []))
    if actual_capabilities != expected_capabilities:
        raise HarnessError("capability matrix does not match selected profiles")
    source_root = Path(project["sourceRoot"]).resolve(strict=True)
    actual_entries = source_entries(source_root)
    corpus_drift: list[str] = []
    if manifest.get("algorithm") != "sha256":
        raise HarnessError("source manifest algorithm is not sha256")
    if manifest.get("entries") != actual_entries:
        was = {e["path"]: e["sha256"] for e in manifest.get("entries", [])}
        now = {e["path"]: e["sha256"] for e in actual_entries}
        corpus_drift = ([f"removed: {p}" for p in sorted(set(was) - set(now))]
                        + [f"added: {p}" for p in sorted(set(now) - set(was))]
                        + [f"changed: {p}" for p in sorted(set(was) & set(now)) if was[p] != now[p]])
    if "read-only" not in (output / "CONTRACTS.md").read_text(encoding="utf-8"):
        raise HarnessError("generated contracts omit the read-only source invariant")

    decisions = load_decisions(output)
    warnings: list[str] = []
    seen: set[str] = set()
    for entry in decisions.get("elements", []):
        element = entry.get("element")
        if not element or element in seen:
            raise HarnessError("decisions.json contains a missing or duplicate element id")
        seen.add(element)
        if entry.get("state") not in DECISION_STATES:
            raise HarnessError(f"decision '{element}' has an unknown state")
        stars_value = entry.get("stars")
        if not isinstance(stars_value, int) or not (
                stars_value == ZERO_STARS or STAR_RANGE[0] <= stars_value <= STAR_RANGE[1]):
            raise HarnessError(f"decision '{element}' has an invalid star rank")
        if not str(entry.get("evidence", "")).strip():
            raise HarnessError(f"decision '{element}' has no user evidence excerpt")
        preview = entry.get("preview")
        if preview is not None:
            if not isinstance(preview, dict) or not preview.get("path") or not preview.get("sha256"):
                raise HarnessError(f"decision '{element}' has a malformed preview reference")
            shot = project_root.resolve(strict=True) / preview["path"]
            if not shot.is_file():
                raise HarnessError(f"decision '{element}' references a missing preview: {preview['path']}")
            if sha256_file(shot) != preview["sha256"]:
                warnings.append(f"preview for '{element}' changed since it was ranked "
                                f"(re-record with `decide --preview` when convenient)")
        target = entry.get("supersededBy")
        if target and target not in {e.get("element") for e in decisions["elements"]}:
            raise HarnessError(f"decision '{element}' is superseded by an unknown element")
    if decisions.get("state") != project.get("state"):
        raise HarnessError("project.json state disagrees with decisions.json state")
    if (output / "DECISIONS.md").read_text(encoding="utf-8") != render_decisions_md(decisions):
        raise HarnessError("DECISIONS.md is stale; regenerate it with `decide`")
    return {"warnings": warnings, "corpusDrift": corpus_drift}


def visible_controls(markup: str, attribute: str) -> dict[str, str]:
    """Map each control carrying `attribute` to the text a browser would draw.

    Counting substrings in generated markup is not verification -- it asserts
    what the generator meant, not what a parser builds. This walks the markup
    the way a browser does, so a control whose glyph got absorbed into a broken
    opening tag comes back empty instead of coming back "present".
    """
    class _Walk(HTMLParser):
        def __init__(self) -> None:
            super().__init__(convert_charrefs=True)
            self.open: list[tuple[str, str | None, list[str]]] = []
            self.found: dict[str, str] = {}

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            keys = dict(attrs)
            # A valueless attribute (`data-reset`) parses to None. That is still
            # a control -- key it by the attribute name, not by "absent".
            key = keys.get(attribute) or attribute if attribute in keys else None
            self.open.append((tag, key, []))

        def handle_data(self, data: str) -> None:
            for frame in self.open:
                frame[2].append(data)

        def handle_endtag(self, tag: str) -> None:
            while self.open:
                name, key, text = self.open.pop()
                if key is not None:
                    self.found.setdefault(key or attribute, "".join(text))
                if name == tag:
                    break

    walk = _Walk()
    walk.feed(markup)
    walk.close()
    while walk.open:                       # unclosed tags at EOF still count
        _, key, text = walk.open.pop()
        if key is not None:
            walk.found.setdefault(key or attribute, "".join(text))
    return walk.found


def self_test() -> None:
    with tempfile.TemporaryDirectory(prefix="design-harness-test-") as temp:
        root = Path(temp)
        project = root / "project"
        source = root / "Oddly Named Evidence 42"
        project.mkdir()
        source.mkdir()
        (source / "reference.txt").write_text("ASCII composition and physical product", encoding="utf-8")
        (source / "frame.png").write_bytes(b"deterministic-image-fixture")
        before = source_entries(source)
        output = init_harness(project, source, ["art-direction", "mockup-layering", "physical-space"])
        validate_harness(project)
        after = source_entries(source)
        if before != after:
            raise HarnessError("self-test source changed")
        questions = (output / "QUESTIONNAIRE.md").read_text(encoding="utf-8")
        for expected in ("ASCII/Unicode", "layer renderer", "measurement"):
            if expected not in questions:
                raise HarnessError(f"self-test questionnaire omitted: {expected}")

        # OS sidecars must never enter the manifest: browsing the source root
        # would otherwise flip validate to red with the evidence untouched.
        (source / ".DS_Store").write_bytes(b"finder-noise-v1")
        validate_harness(project)
        (source / ".DS_Store").write_bytes(b"finder-noise-v2-different-bytes")
        validate_harness(project)

        # A decision must survive as an artifact, carry a star rank, and win
        # over the element it supersedes.
        record_decision(project, "cover.layout.two-column", "approved", 5, "user: 'c2'", [], source="user")
        record_decision(project, "cover.spine.right", "approved", 4, "user: 'place it on the right'", [], source="user")
        record_decision(project, "cover.layout.single-column", "rejected", 1, "user: 'you destructed the two columns'",
                        ["cover.layout.two-column"])
        validate_harness(project)
        ledger = json.loads((output / "decisions.json").read_text(encoding="utf-8"))
        by_id = {e["element"]: e for e in ledger["elements"]}
        if by_id["cover.layout.two-column"]["state"] != "superseded":
            raise HarnessError("self-test: supersede did not retire the prior element")
        if by_id["cover.layout.two-column"]["supersededBy"] != "cover.layout.single-column":
            raise HarnessError("self-test: supersede lost its back-reference")
        if "★★★★☆" not in (output / "DECISIONS.md").read_text(encoding="utf-8"):
            raise HarnessError("self-test: star rank not rendered")
        if ledger["state"] != "approved" or json.loads((output / "project.json").read_text(encoding="utf-8"))["state"] != "approved":
            raise HarnessError("self-test: lifecycle state did not advance past draft")

        # Companion star ranks must adopt into the ledger; events with no
        # design-element id must be skipped rather than guessed at.
        companion = root / "decisions.jsonl"
        companion.write_text("\n".join([
            json.dumps({"type": "rank", "element": "form.paper.white", "stars": 5, "text": "user: form stays white", "timestamp": 30}),
            json.dumps({"type": "click", "choice": "screen-local-slug", "element": None, "stars": None}),
            json.dumps({"type": "rank", "element": "palette.inferred", "stars": 1, "timestamp": 10}),
            json.dumps({"type": "sentiment", "element": "cover.ring.kicker", "sentiment": "like", "timestamp": 20}),
            json.dumps({"type": "sentiment", "element": "cover.background.black", "sentiment": "dislike", "timestamp": 40}),
            json.dumps({"type": "sentiment", "element": "bogus.sentiment", "sentiment": "meh", "timestamp": 50}),
            json.dumps({"type": "rank", "element": "bogus.range", "stars": 9, "timestamp": 60}),
            "not json at all",
        ]) + "\n", encoding="utf-8")
        adopted, skipped = adopt_companion(project, companion)
        if adopted != 4 or skipped != 4:
            raise HarnessError(f"self-test: adopt miscounted ({adopted} adopted, {skipped} skipped)")
        validate_harness(project)
        adopted_ledger = {e["element"]: e for e in json.loads((output / "decisions.json").read_text(encoding="utf-8"))["elements"]}
        if adopted_ledger["form.paper.white"]["stars"] != 5 or adopted_ledger["palette.inferred"]["stars"] != 1:
            raise HarnessError("self-test: adopt lost the star rank")
        if "user: form stays white" not in adopted_ledger["form.paper.white"]["evidence"]:
            raise HarnessError("self-test: adopt dropped the evidence excerpt")
        # sentiment maps deterministically to verdict + default rank
        # A thumb records encouragement; it must NOT move state or invent a rank.
        for element, name in (("cover.ring.kicker", "like"), ("cover.background.black", "dislike")):
            entry = adopted_ledger[element]
            if entry.get("sentiment") != name:
                raise HarnessError(f"self-test: {name} was not recorded as sentiment")
            if entry["state"] == "rejected" and name == "dislike":
                raise HarnessError("self-test: a thumb-down must not reject; only an explicit verdict may")

        # Adopting the same ledger twice must be a no-op on content.
        first = (output / "decisions.json").read_text(encoding="utf-8")
        adopt_companion(project, companion)
        if (output / "decisions.json").read_text(encoding="utf-8") != first:
            raise HarnessError("self-test: adopt is not idempotent")

        # Controls are generated from the ledger and are byte-stable.
        markup = render_feedback_controls(load_decisions(output))
        if markup != render_feedback_controls(load_decisions(output)):
            raise HarnessError("self-test: controls are not deterministic")
        for required in ('data-element="form.paper.white"', 'data-rank="5"',
                         'data-verdict="completed"', 'data-sentiment="like"',
                         'data-sentiment="dislike"', 'data-rank="0"'):
            if required not in markup:
                raise HarnessError(f"self-test: controls omitted {required}")
        # Zero is a rank and must ride the rank path. As `data-reset` it reached a
        # companion handler that cleared the thumb and the tick too, so scoring an
        # element 0 silently destroyed two signals the user had set deliberately.
        if "data-reset" in markup:
            raise HarnessError(
                "self-test: zero emitted as `data-reset` -- that path erases sentiment and verdict")
        # The zero is revealed by hovering ONE star, which is where a user
        # reaching for the bottom of the scale already is. Hiding it is only
        # safe while it is also unclickable, and only honest while a zero
        # already given still shows.
        if 'pointer-events:none' not in re.sub(r"\s+", "", FEEDBACK_STYLE).split(
                '[data-rank="0"]{')[1].split("}")[0]:
            raise HarnessError(
                "self-test: the hidden zero is still clickable -- an invisible control beside "
                "the first star is how a click meant for 1 scores 0")
        if '[data-rank="1"]:hover)' not in FEEDBACK_STYLE:
            raise HarnessError(
                "self-test: nothing reveals the zero -- it must surface when one star is hovered")
        if '.dh-zero:has([data-rank="0"].on)' not in FEEDBACK_STYLE:
            raise HarnessError(
                "self-test: a zero already given would stay hidden -- it must be "
                "distinguishable from an unrated row")
        # The zero must not sit inside the star strip: adjacent and unlabelled, it
        # caught clicks aimed at one star.
        if re.search(r'<span class="dh-stars"[^>]*>\s*<span data-rank="0"', markup):
            raise HarnessError(
                "self-test: the zero sits inside the star strip -- it will catch clicks meant for 1 star")
        # Hovering must preview the whole rank, not a single glyph.
        if ":has(~ [data-rank]:hover)" not in FEEDBACK_STYLE:
            raise HarnessError(
                "self-test: stars do not preview a rank on hover -- hovering lights one glyph, "
                "so the user cannot see what a click would set")
        # A refresh must not throw away what the user clicked.
        if "/* dh-rehydrate */" not in markup:
            raise HarnessError(
                "self-test: controls ship no rehydrator -- a refresh reverts every score")
        # sessionStorage is scoped to one tab, so two tabs on the same screen
        # drift into different scores with no way to tell which is real.
        if re.search(r"sessionStorage\s*\.\s*(get|set)Item", markup):
            raise HarnessError(
                "self-test: signals cached in sessionStorage -- per-tab storage lets two tabs "
                "disagree about the same element")
        if "localStorage" not in markup or "BroadcastChannel" not in markup:
            raise HarnessError(
                "self-test: signals do not sync across tabs -- needs shared storage plus a "
                "channel for instant fan-out")
        if 'data-dh-rev=' not in markup:
            raise HarnessError(
                "self-test: rows carry no ledger revision -- a cached overlay would outlive "
                "the re-embed that superseded it")
        if f"dh-controls-version: {CONTROLS_VERSION}" not in markup:
            raise HarnessError("self-test: controls carry no version stamp -- a stale embed "
                               "cannot be told apart from a fix that did not work")
        # Substring checks above prove the ATTRIBUTES were emitted. They cannot
        # prove a browser will render anything: an unterminated opening tag keeps
        # every `data-rank="n"` intact while swallowing the star glyph into an
        # attribute, so all five controls parse as empty and the user sees a blank
        # strip. Parse it and assert on what a browser would actually show.
        for control, label, minimum in (("data-rank", "star", STAR_RANGE[1]),
                                        ("data-rank", "zero", 1),
                                        ("data-verdict", "verdict", 1)):
            shown = visible_controls(markup, control)
            if len(shown) < minimum:
                raise HarnessError(
                    f"self-test: {label} controls parse as {len(shown)} element(s), expected {minimum}")
            blank = [attr for attr, text in shown.items() if not text.strip()]
            if blank:
                raise HarnessError(
                    f"self-test: {label} control(s) {sorted(blank)} render with no visible content -- "
                    "the markup emits the attribute but a browser draws nothing")
        # A thumb-down keeps the element scoreable; only an explicit reject removes it.
        if 'data-element="cover.background.black"' not in markup:
            raise HarnessError("self-test: a disliked element vanished from scoring")
        record_decision(project, "explicitly.rejected", "rejected", ZERO_STARS, "user clicked reject", [],
                        source="user")
        rejected_markup = render_feedback_controls(load_decisions(output), None, project)
        # Rejected work stays visible in its own group so a rejection can be
        # undone by clicking, instead of by editing JSON.
        if 'data-element="explicitly.rejected"' not in rejected_markup:
            raise HarnessError("self-test: rejected element is unreachable for undo")
        if 'data-group="rejected"' not in rejected_markup:
            raise HarnessError("self-test: rejected group not rendered")
        if "Lluvia de ideas" not in rejected_markup:
            raise HarnessError("self-test: brainstorming group label missing")

        # Every color must be a themeable token, never a literal that would
        # override the corpus palette the ledger already approved.
        style_block = markup.split("</style>")[0]
        for token in ("--dh-bg", "--dh-ink", "--dh-accent", "--dh-font"):
            if token not in style_block:
                raise HarnessError(f"self-test: controls style omits the {token} token")
        # Theme colours must come from tokens. Fixed semantic colours (the green
        # "done" state, the red offline warning) are design constants, not theme.
        for literal in ("color:var(--dh-ink,#111);background:#fff",
                        "background:#111;color:#fff"):
            if literal in style_block.replace(" ", ""):
                raise HarnessError(f"self-test: controls hardcode {literal} outside a var() fallback")

        # A declared theme is baked in, and identical flags emit identical bytes.
        themed = render_feedback_controls(load_decisions(output),
                                          {"bg": "#f9e7b5", "ink": "#111", "accent": "#d9482a", "font": None})
        if "--dh-bg: #f9e7b5" not in themed or "--dh-accent: #d9482a" not in themed:
            raise HarnessError("self-test: declared theme was not applied")
        if "--dh-font" in themed.split("<div")[1].split(">")[0]:
            raise HarnessError("self-test: unset theme key leaked into the wrapper")
        if themed != render_feedback_controls(load_decisions(output),
                                              {"bg": "#f9e7b5", "ink": "#111", "accent": "#d9482a", "font": None}):
            raise HarnessError("self-test: themed controls are not deterministic")

        # The graphic being ranked must ride along with the rank, and must be
        # hash-pinned: a preview that changed is a preview nobody looked at.
        shots = project / "shots"
        shots.mkdir()
        shot = shots / "cover.svg"
        shot.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 85 110"><rect width="85" height="110" fill="#f9e7b5"/></svg>', encoding="utf-8")
        record_decision(project, "cover.layout.two-column", "approved", 5, "user: 'c2'", [],
                        preview_reference(project, "shots/cover.svg"), source="user")
        validate_harness(project)
        with_shot = render_feedback_controls(load_decisions(output), None, project)
        if 'class="dh-shot"' not in with_shot or "#f9e7b5" not in with_shot:
            raise HarnessError("self-test: the ranked element carries no graphic")
        if "sin gr" not in render_feedback_controls(load_decisions(output), None, project):
            raise HarnessError("self-test: elements without a preview must say so, not fake one")
        if with_shot != render_feedback_controls(load_decisions(output), None, project):
            raise HarnessError("self-test: previews broke control determinism")
        # A regenerated preview is normal work: it must be reported, not blocked.
        shot.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 85 110"><rect fill="#000"/></svg>', encoding="utf-8")
        report = validate_harness(project)
        if not any("changed since it was ranked" in w for w in report["warnings"]):
            raise HarnessError("self-test: preview drift must be reported as a warning")
        record_decision(project, "cover.layout.two-column", "approved", 5, "user: 'c2'", [],
                        preview_reference(project, "shots/cover.svg"), source="user")
        validate_harness(project)
        for bad in ("../outside.svg", "shots/nope.svg", "scripts/evil.py"):
            try:
                preview_reference(project, bad)
            except HarnessError:
                continue
            raise HarnessError(f"self-test: preview accepted an unsafe reference: {bad}")

        # The agent must not be able to type a confident rank. This cap is the
        # difference between "user clicked 4" and "agent felt like 4".
        try:
            record_decision(project, "agent.guess", "approved", 4, "agent hunch", [], source="agent")
        except HarnessError:
            pass
        else:
            raise HarnessError("self-test: agent was allowed to set a rank above the cap")
        record_decision(project, "agent.guess", "proposed", 1, "agent inference", [], source="agent")
        ledger_now = {e["element"]: e for e in json.loads((output / "decisions.json").read_text(encoding="utf-8"))["elements"]}
        if ledger_now["agent.guess"]["source"] != "agent":
            raise HarnessError("self-test: provenance not recorded")
        if ledger_now["cover.layout.two-column"]["source"] != "user":
            raise HarnessError("self-test: user provenance lost")

        # Zero is a real score meaning worst execution, and must survive adoption.
        zero_ledger = root / "zero.jsonl"
        zero_ledger.write_text(json.dumps({"element": "kill.me", "stars": 0, "timestamp": 1}) + "\n"
                               + json.dumps({"element": "bless.me", "verdict": "approved", "timestamp": 2}) + "\n",
                               encoding="utf-8")
        adopt_companion(project, zero_ledger)
        z = {e["element"]: e for e in json.loads((output / "decisions.json").read_text(encoding="utf-8"))["elements"]}
        # A score rates execution. It must never remove the element: reading a
        # low score as "delete this" destroyed work the user wanted kept.
        if z["kill.me"]["stars"] != ZERO_STARS:
            raise HarnessError("self-test: zero-star value was not recorded")
        if z["kill.me"]["state"] == "rejected":
            raise HarnessError("self-test: a score removed an element; only an explicit verdict may")
        if z["bless.me"]["state"] != "approved" or z["bless.me"]["source"] != "user":
            raise HarnessError("self-test: explicit approve verdict not adopted")

        # Statistics must be deterministic and must not flatter the ledger:
        # coverage tells you how much is really the user's.
        first_stats = ledger_stats(load_decisions(output))
        if first_stats != ledger_stats(load_decisions(output)):
            raise HarnessError("self-test: stats are not deterministic")
        if not 0.0 <= first_stats["coverage"] <= 1.0:
            raise HarnessError("self-test: coverage out of range")
        if first_stats["userSet"] + first_stats["agentSet"] != first_stats["standing"]:
            raise HarnessError("self-test: user/agent split does not sum to standing")
        record_decision(project, "liked.but.weak", "proposed", 1, "user click", [],
                        source="user", sentiment="like")
        flagged = ledger_stats(load_decisions(output))
        # Good idea, ugly execution: actionable polish, never a contradiction.
        if "liked.but.weak" not in flagged["needsPolish"]:
            raise HarnessError("self-test: like-with-low-stars not surfaced as polish work")
        if "liked.but.weak" in flagged["conflicts"]:
            raise HarnessError("self-test: like-with-low-stars mislabelled as a conflict")
        if flagged["likes"] < 1:
            raise HarnessError("self-test: like not counted")

        # embed must supply the graphic, and must refuse to guess a placement.
        session = project / ".superpowers" / "brainstorm" / "s1" / "content"
        session.mkdir(parents=True)
        screen = session / "proto.html"
        screen.write_text('<html><head></head><body><h1>fichas</h1>'
                          '<div data-dh-controls="cover.layout.two-column"></div>'
                          '</body></html>', encoding="utf-8")
        if embed_controls(project, screen) != 1:
            raise HarnessError("self-test: embed did not fill the placeholder")
        embedded = screen.read_text(encoding="utf-8")
        for needed in ('class="dh-shot"', 'data-rank="0"', 'data-verdict="completed"',
                       'data-sentiment="like"', 'data-sentiment="dislike"',
                       "/* dh-rehydrate */", f"dh-controls-version: {CONTROLS_VERSION}"):
            if needed not in embedded:
                raise HarnessError(f"self-test: embedded row missing {needed}")
        # Re-running embed must be a no-op, not a duplication. The old regex
        # stopped at the first </div> inside a generated row, so a second run
        # doubled every row and left orphaned closing tags that silently ended
        # the wrapper early and killed every descendant style rule.
        once = screen.read_text(encoding="utf-8")
        embed_controls(project, screen)
        twice = screen.read_text(encoding="utf-8")
        if once != twice:
            raise HarnessError("self-test: embed is not idempotent")
        if twice.count('data-element="cover.layout.two-column"') != 1:
            raise HarnessError("self-test: embed duplicated a row on re-run")
        if twice.count("<div") != twice.count("</div"):
            raise HarnessError("self-test: embed left unbalanced <div> tags")

        screen.write_text("<html><body>no placeholder</body></html>", encoding="utf-8")
        try:
            embed_controls(project, screen)
        except HarnessError:
            pass
        else:
            raise HarnessError("self-test: embed accepted a screen with no placeholder")

        # publish must win the newest-mtime race by a clear margin, not a tie.
        screen.write_text('<html><body><div data-dh-controls="cover.layout.two-column"></div></body></html>',
                          encoding="utf-8")
        rival = session / "rival.html"
        rival.write_text("<html><body>rival</body></html>", encoding="utf-8")
        publish_screen(project, screen)
        gap = screen.stat().st_mtime - rival.stat().st_mtime
        if gap < 2:
            raise HarnessError(f"self-test: publish left a {gap:.1f}s race with another screen")

        # Reviewed is a status, not approval, and must not freeze the element.
        record_decision(project, "seen.it", "completed", 3, "user clicked completed", [], source="user")
        seen = {e["element"]: e for e in json.loads((output / "decisions.json").read_text(encoding="utf-8"))["elements"]}
        if seen["seen.it"]["state"] != "completed":
            raise HarnessError("self-test: completed status not recorded")
        if 'data-element="seen.it"' not in render_feedback_controls(load_decisions(output), None, project):
            raise HarnessError("self-test: a completed element must stay scoreable")
        record_decision(project, "seen.it", "proposed", 5, "user kept iterating", [], source="user")
        if json.loads((output / "decisions.json").read_text(encoding="utf-8")) is None:
            raise HarnessError("unreachable")

        # Zero is the worst score, deliberately given -- not an erasure. It must
        # stay `scored`, must not touch encouragement, and must NOT move state:
        # rating a thing badly is not deleting it. That conflation is what
        # silently deleted a user's work once already.
        record_decision(project, "rated.then.zeroed", "approved", 4, "user", [],
                        source="user", sentiment="like")
        score_zero(project, "rated.then.zeroed")
        zeroed = {e["element"]: e for e in json.loads((output / "decisions.json").read_text(encoding="utf-8"))["elements"]}["rated.then.zeroed"]
        if zeroed["stars"] != ZERO_STARS:
            raise HarnessError("self-test: zero was not recorded as a score")
        if not zeroed["scored"]:
            raise HarnessError("self-test: zero must count as judged -- it is the worst rating, not a blank")
        if zeroed["state"] != "approved":
            raise HarnessError("self-test: a zero score moved the element's state; only a verdict may")
        if zeroed.get("sentiment") != "like":
            raise HarnessError("self-test: zero wrongly cleared the encouragement signal")

        # Ordering: this turn on top, then unresolved, best execution first.
        for name, state, stars in (("z.old.approved", "approved", 5), ("a.new.proposed", "proposed", 2),
                                   ("m.mid.proposed", "proposed", 4)):
            record_decision(project, name, state, stars, "fixture", [], source="user")
        ordered = render_feedback_controls(load_decisions(output), None, project, pinned={"z.old.approved"})
        seq = re.findall(r'data-element="([^"]+)"', ordered)
        if seq[0] != "z.old.approved":
            raise HarnessError("self-test: pinned element was not placed first")
        props = [n for n in seq if n in ("a.new.proposed", "m.mid.proposed")]
        if props != ["m.mid.proposed", "a.new.proposed"]:
            raise HarnessError("self-test: proposals not sorted by execution score")

        # validate must refuse a decision-less harness rather than green-light it.
        (output / "decisions.json").unlink()
        try:
            validate_harness(project)
        except HarnessError:
            pass
        else:
            raise HarnessError("self-test: validate green-lit a harness with no decision ledger")


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description=__doc__)
    subcommands = command.add_subparsers(dest="command", required=True)
    init = subcommands.add_parser("init")
    init.add_argument("--project-root", required=True, type=Path)
    init.add_argument("--source-root", required=True, type=Path)
    init.add_argument("--profiles", required=True)
    validate = subcommands.add_parser("validate")
    validate.add_argument("--project-root", required=True, type=Path)
    decide = subcommands.add_parser("decide", help="record a binding design decision")
    decide.add_argument("--project-root", required=True, type=Path)
    decide.add_argument("--element", required=True, help="stable dotted id, e.g. cover.layout.two-column")
    decide.add_argument("--verdict", required=True, choices=DECISION_STATES)
    decide.add_argument("--stars", required=True, type=int, help=f"{STAR_RANGE[0]}-{STAR_RANGE[1]}, set by the user")
    decide.add_argument("--evidence", required=True, help="verbatim user excerpt, not a paraphrase")
    decide.add_argument("--supersedes", default="", help="comma-separated element ids this replaces")
    decide.add_argument("--preview", default="", help="project-relative graphic of the element being ranked")
    decide.add_argument("--description", default="",
                        help="what the component IS, in plain words (shown on the scoring row)")
    decide.add_argument("--implemented", default="",
                        help="what was actually built for it this time")
    decide.add_argument("--source", default="agent", choices=SOURCES,
                        help="agent (capped at 1 star) or user (only via adopt)")
    describe = subcommands.add_parser(
        "describe", help="label an element without touching its verdict or rank")
    describe.add_argument("--project-root", required=True, type=Path)
    describe.add_argument("--element", required=True)
    describe.add_argument("--description", default="",
                          help="what the component IS, in plain words (shown on the scoring row)")
    describe.add_argument("--implemented", default="", help="what was actually built for it")
    adopt = subcommands.add_parser("adopt", help="fold companion star ranks into the ledger")
    adopt.add_argument("--project-root", required=True, type=Path)
    adopt.add_argument("--companion-ledger", required=True, type=Path,
                       help="path to the companion's durable decisions.jsonl")
    controls = subcommands.add_parser("controls", help="emit star + like/dislike controls from the ledger")
    controls.add_argument("--project-root", required=True, type=Path)
    controls.add_argument("--out", type=Path, help="write here instead of stdout")
    controls.add_argument("--shot-width", default="", help="preview frame width, e.g. 132px")
    controls.add_argument("--pin", default="", help="element ids to pin on top (this turn's work)")
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
    subcommands.add_parser("self-test")
    return command


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "init":
            output = init_harness(args.project_root, args.source_root, parse_profiles(args.profiles))
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
            preview = preview_reference(args.project_root, args.preview) if args.preview else None
            decisions = record_decision(args.project_root, args.element, args.verdict,
                                        args.stars, args.evidence, supersedes, preview,
                                        source=args.source,
                                        implemented=args.implemented or None,
                                        description=args.description or None)
            live = [e for e in decisions["elements"] if e["state"] in ("approved", "proposed")]
            print(f"Recorded {args.element} ({args.verdict}, {args.stars}★). "
                  f"{len(live)} element(s) standing, state={decisions['state']}.")
        elif args.command == "describe":
            entry = describe_element(args.project_root, args.element,
                                     args.description or None, args.implemented or None)
            print(f"Labelled {args.element} (still {entry['state']}, {entry['stars']}★, "
                  f"set by {entry.get('source', 'unknown')}).")
        elif args.command == "adopt":
            adopted, skipped = adopt_companion(args.project_root, args.companion_ledger)
            print(f"Adopted {adopted} ranked decision(s); skipped {skipped} "
                  f"interaction(s) with no design-element id or usable signal.")
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
            return subprocess.call([sys.executable, str(script), str(args.project_root)])
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
