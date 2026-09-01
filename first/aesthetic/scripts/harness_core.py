#!/usr/bin/env python3
"""The vocabulary every other harness module spells its work in.

The states a decision may hold, the star range, the sentinels that mean "leave
this field alone", the foundations an element name is sorted into, and the few
pure helpers (hashing, canonical JSON, containment) that have no opinion about
any of it. It is a seam because it is the only module nothing else in the
harness may depend on in reverse: everything imports from here, and this
imports from nobody.
"""

from __future__ import annotations

import hashlib
import json
import mimetypes
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
# Taking a thumb back is a signal in its own right -- "I no longer stand behind
# this direction" -- and the companion says so with an explicit `sentiment:
# null`. It needs a value distinct from that null, because `None` was carrying
# both meanings at once ("leave the thumb alone" and "remove the thumb") and a
# single argument cannot mean both: withdrawals lost, every time. One real
# ledger held 18 of them, one element un-liked twelve times, while `stats` went
# on counting every withdrawn like.
KEEP_SENTIMENT = object()
# Same "not passed here" sentinel, for a field with no natural falsy default:
# `bookmarked=False` must still be distinguishable from "the caller has no
# opinion, leave whatever is already recorded alone".
KEEP_BOOKMARK = object()
# A score never changes an element's state. Removal is always a deliberate act
# (`decide --supersedes` or an explicit reject control), because reading a low
# score as "delete this" already destroyed work the user wanted kept.
SCORE_NEVER_REMOVES = True
# A preview is the graphic the star is actually about.
PREVIEW_SUFFIXES = {".html", ".png", ".jpg", ".jpeg", ".webp", ".gif"}
# Who set a rank. The distinction is the whole point: an agent-typed number and
# a user click used to be indistinguishable in the ledger.
# Three lifecycle groups the user reads at a glance. Derived from state, never
# stored separately, so a state change cannot leave the group stale.
GROUPS = (
    ("brainstorming", "brainstorming", ("proposed",)),
    ("developing", "developing", ("completed", "approved")),
    ("rejected", "rejected", ("rejected", "superseded")),
)
GROUP_OF = {state: key for key, _, states in GROUPS for state in states}

# The foundations of a design system, in the order one is read: what the thing
# IS, then its colour, its lettering, its imagery, how it is laid out, how it
# speaks, how it moves. Rows grouped this way are a design system with a rank
# against each part; grouped only by lifecycle they are a to-do list, and the
# user could not see whether the typography as a whole was working.
#
# Derived from the element id's own prefix -- zero configuration, nothing new to
# maintain, and an id that says `palette.` files itself under colour. An
# unrecognised prefix falls to `core`, never to a crash.
FOUNDATIONS = (
    ("core", ("core", "idea", "concept", "identity", "signature", "thesis", "brand")),
    ("palette", ("palette", "color", "colour", "tone", "hue")),
    ("typography", ("type", "typo", "typography", "font", "lettering", "numerals")),
    ("illustration", ("art", "artsource", "illustration", "image", "imagery",
                      "texture", "photo", "icon", "mark", "drawing")),
    ("composition", ("layout", "grid", "composition", "form", "format", "page",
                     "pages", "spread", "cover", "interior", "spine", "margin")),
    ("voice", ("copy", "voice", "language", "roles", "label", "microcopy")),
    ("motion", ("motion", "anim", "animation", "transition")),
)
FOUNDATION_OF_WORD = {word: key for key, words in FOUNDATIONS for word in words}
FOUNDATION_ORDER = {key: n for n, (key, _) in enumerate(FOUNDATIONS)}
GENERIC_ROUND_SLUGS = frozenset({
    "objeto", "object", "cover", "round", "ronda", "redraw", "furniture", "tab",
})


SOURCES = ("user", "agent")
AGENT_MAX_STARS = 1

# companion_doctor sends a click on this synthetic element to prove the socket
# reaches the ledger, then strips its rows back out. An `adopt` racing that
# cleanup used to fold the probe in as a real element, and adopt never removes.
PROBE_ELEMENT = "__doctor_probe__"


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


def ledger_digest(lines: list[str]) -> str:
    """Fingerprint the ledger prefix an adopt has already consumed."""
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


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


SCREEN_DIR = Path(__file__).resolve().parent.parent / "screen"


def _screen(name: str) -> str:
    """The browser assets, wrapped in the tag that carries them into the page.

    They live as real .css/.js files so an editor, a formatter, and
    `node --check` can read them; holding them as Python string literals is what
    grew this module past ten times its byte budget.
    """
    body = (SCREEN_DIR / name).read_text(encoding="utf-8")
    tag = "style" if name.endswith(".css") else "script"
    return f"<{tag}>{body}</{tag}>"
