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


def primary_foundation(cohort: set[str]) -> str:
    """Which foundation this round is really about -- one topic, not a batch."""
    if not cohort:
        return "core"
    counts: dict[str, int] = {}
    for element in cohort:
        key = foundation_of(element)
        counts[key] = counts.get(key, 0) + 1
    return min(counts, key=lambda k: (-counts[k], FOUNDATION_ORDER.get(k, 99)))


def round_tag_label(cohort: set[str], decisions: dict[str, object],
                      cohort_name: str = "", round_label: str = "") -> str:
    """What the round header names. Slugs like `objeto` become the object name."""
    if round_label.strip():
        return round_label.strip()
    slug = cohort_name.strip().lower().replace("-", " ")
    if slug and slug not in GENERIC_ROUND_SLUGS and len(slug.split()) <= 3:
        return cohort_name.strip()
    by_id = {e["element"]: e for e in decisions["elements"]}
    ordered = sorted(cohort, key=lambda e: (
        0 if by_id.get(e, {}).get("state") == "proposed" else 1, e))
    if not ordered:
        return cohort_name.strip() or "Round"
    entry = by_id.get(ordered[0], {"element": ordered[0]})
    desc = str(entry.get("description") or "")
    for pattern in (r"\b(?:es el|es la|es un|es una)\s+([^,.;]+)",
                    r"\b(?:the|a|an)\s+([^,.;]+)"):
        match = re.search(pattern, desc, re.I)
        if match:
            phrase = match.group(1).strip()
            words = phrase.split()
            if words:
                label = words[0] if len(words) == 1 else " ".join(words[:2])
                return label[0].upper() + label[1:]
    name = display_name(entry)
    words = name.split()
    return " ".join(words[:3]) if len(words) > 4 else name


def foundation_of(element: str) -> str:
    """Which design-system foundation an element id belongs to.

    Reads the id's leading segments, most specific first: `family.mark.dotmatrix`
    files under illustration on `mark` rather than falling through on `family`.
    """
    parts = [p for p in re.split(r"[.\-_]", element.lower()) if p]
    for part in parts:
        if part in FOUNDATION_OF_WORD:
            return FOUNDATION_OF_WORD[part]
    return "core"
SOURCES = ("user", "agent")
AGENT_MAX_STARS = 1

# Every word the scoring strip draws. The strip used to be Spanish literals with
# an English cohort banner bolted on, so one screen spoke two languages and no
# other project could use it without editing this file. The language is a
# property of the project (stored by `init`), not of the harness.
DEFAULT_LANGUAGE = "en"
STRINGS = {
    "en": {
        "offline": "No connection to the companion: these clicks are NOT saved. "
                   "Open the companion URL (http://localhost:PORT/?key=...), not the file.",
        "this-round": "this round", "to-score": "element(s) to score",
        "from-this-round": "From this round",
        "brainstorming": "Brainstorming", "developing": "In progress", "rejected": "Set aside",
        "core": "Core ideas", "palette": "Colour palette", "typography": "Typography",
        "illustration": "Illustration & texture", "composition": "Composition & layout",
        "voice": "Copy & voice", "motion": "Motion",
        "unscored": "not yet scored", "proposed-by": "Proposed", "built": "Built",
        "no-graphic": "no graphic",
        "article-title": "Aesthetic ranking", "brand": "Design Agent",
        "companion-brand": "CYBER YOSHI: SKILLS", "companion-agent": "Cyber Yoshi",
        "companion-kind": "Agent companion",
        "agent-working": "Agent running", "agent-idle": "Agent idle",
        "prep-legend": "New designs are on the way \u2014 keep scoring, your ranks save while I draw.",
        "done-cheer": "Marked as done",
        "credit-what": "Live companion",
        "credit-who": "Inspired from Jesse Vincent \u00b7 github.com/obra \u00b7 Superpowers",
        "project-label": "Project", "designing": "Designing",
        "saved": "Preference saved", "designs": "designs",
        "zone-round": "This round",
        "zone-round-note": "The only section asking for something. Rank what is here.",
        "round-heading": "Design round",
        "toc-jump": "Jump to",
        "zone-fundamentals": "Critical components",
        "zone-fundamentals-note": "Understanding the direction. The ideas, the palette and the "
                                  "type, together \u2014 rank them as a system: the pairings, "
                                  "not only the parts.",
        "zone-backlog": "On development", "zone-backlog-note": "Proposed, not resolved yet.",
        "zone-antipattern": "Rejected",
        "zone-antipattern-note": "Turned down. Kept so they are not proposed again.",
        "specimen-colors": "Palette", "specimen-fonts": "Typefaces",
        "hero-standing": "standing", "hero-ranked": "you ranked",
        "hero-asking": "in better shape", "hero-ongoing": "need your direction",
        "hero-improve": "rejected",
        "temp-caption": "One bar per element, worst execution to best \u2014 click one to jump to "
                        "it. Solid green is done, pale green is well drawn but still open, grey "
                        "is unscored. Bars marked ? are what this round asks.",
        "temp-alt": "Distribution of execution scores, worst to best",
        "hero-lede": "Give your score to the AI element designs below. When you finish "
                     "giving points, go back to your agent chat and give your critique and "
                     "directions \u2014 we'll generate new designs and improvements.",
        "key-done": "done", "key-open": "well drawn, open", "key-weak": "needs work",
        "key-unscored": "unscored", "key-asked": "this round", "key-anti": "set aside",
        "bar-attempts": "{count} drawings of this idea",
        "before": "what stands now", "after": "proposed instead", "brand-new": "new, nothing to beat",
        "empty-zone": "Nothing here yet.", "zone-count": "elements",
        "execution-of": "execution of", "stars-of": "of", "execution-quality": "execution quality",
        "state-proposed": "proposed", "state-approved": "on shape",
        "state-completed": "completed", "state-superseded": "replaced",
        "state-rejected": "set aside",
        "like": "like it", "dislike": "do not like it", "completed": "completed",
        "bookmark": "bookmark this card",
        "brief-title": "Project brief", "brief-count": "{answered} of {total} answered",
        "brief-unanswered": "not answered yet",
        "brief-now": "Now", "brief-more": "{count} more after this",
        "brief-save": "Save answer", "brief-saved": "Saved",
        "brief-placeholder": "Answer in your own words",
        "tags-title": "Reference tags", "tags-count": "{left} folder(s) left",
        "tags-aspects": "Useful for", "tags-stance": "Stance",
        "tags-quality": "Quality", "tags-save": "Save tag", "tags-saved": "Saved",
        "tag-pursue": "pursue", "tag-avoid": "avoid",
        "tag-finished": "finished", "tag-sketch": "rough sketch",
        "zero-title": "zero stars: terrible, but it still stands",
        "zero-label": "zero stars for {element}: terrible execution",
    },
    "es": {
        "offline": "Sin conexión al companion: estos clics NO se guardan. "
                   "Abre la URL del companion (http://localhost:PORT/?key=...), no el archivo.",
        "this-round": "esta ronda", "to-score": "elemento(s) por puntuar",
        "from-this-round": "De esta ronda",
        "brainstorming": "Lluvia de ideas", "developing": "En desarrollo", "rejected": "Descartado",
        "core": "Ideas centrales", "palette": "Paleta de color", "typography": "Tipografía",
        "illustration": "Ilustración y textura", "composition": "Composición y retícula",
        "voice": "Texto y voz", "motion": "Movimiento",
        "unscored": "sin puntuar", "proposed-by": "Propuesto", "built": "Implementado",
        "no-graphic": "sin gráfico",
        "article-title": "Aesthetic ranking", "brand": "Design Agent",
        "companion-brand": "CYBER YOSHI: SKILLS", "companion-agent": "Cyber Yoshi",
        "companion-kind": "Companion del agente",
        "agent-working": "Agente trabajando", "agent-idle": "Agente en pausa",
        "prep-legend": "Están llegando diseños nuevos \u2014 sigue puntuando, tus puntos se guardan mientras dibujo.",
        "done-cheer": "Marcado como listo",
        "credit-what": "Companion en vivo",
        "credit-who": "Inspired from Jesse Vincent \u00b7 github.com/obra \u00b7 Superpowers",
        "project-label": "Proyecto", "designing": "Diseñando",
        "saved": "Preferencia guardada", "designs": "diseños",
        "zone-round": "Esta ronda",
        "zone-round-note": "La única sección que pide algo. Puntúa lo que hay aquí.",
        "round-heading": "Ronda de diseño",
        "toc-jump": "Ir a",
        "zone-fundamentals": "Componentes críticos",
        "zone-fundamentals-note": "Entender la dirección. Las ideas, la paleta y la tipografía, "
                                  "juntas \u2014 púntualas como sistema: los emparejamientos, "
                                  "no solo las piezas.",
        "zone-backlog": "En desarrollo", "zone-backlog-note": "Propuesto, todavía sin resolver.",
        "zone-antipattern": "Descartados",
        "zone-antipattern-note": "Descartado. Queda aquí para no volver a proponerlo.",
        "specimen-colors": "Paleta", "specimen-fonts": "Tipografías",
        "hero-standing": "en pie", "hero-ranked": "puntuados por ti",
        "hero-asking": "van mejor", "hero-ongoing": "esperan tu dirección",
        "hero-improve": "descartados",
        "key-done": "terminado", "key-open": "bien dibujado, abierto", "key-weak": "por mejorar",
        "key-unscored": "sin puntuar", "key-asked": "esta ronda", "key-anti": "descartado",
        "bar-attempts": "{count} dibujos de esta idea",
        "before": "lo que hay ahora", "after": "se propone en su lugar",
        "brand-new": "nuevo, no compite con nada",
        "temp-caption": "Una barra por elemento, de peor a mejor ejecución \u2014 pulsa una para "
                        "ir a ella. Verde sólido es terminado, verde claro es bien dibujado pero "
                        "abierto, gris es sin puntuar. Las marcadas con ? son las de esta ronda.",
        "temp-alt": "Distribución de las notas de ejecución, de peor a mejor",
        "hero-lede": "Puntúa los diseños que la IA propone abajo. Cuando termines de "
                     "dar puntos, vuelve al chat con tu agente y dale tu crítica y tus "
                     "indicaciones \u2014 generaremos nuevos diseños y mejoras.",
        "empty-zone": "Todavía no hay nada aquí.", "zone-count": "elementos",
        "execution-of": "ejecución de", "stars-of": "de", "execution-quality": "calidad de ejecución",
        "state-proposed": "propuesto", "state-approved": "en forma",
        "state-completed": "terminado", "state-superseded": "reemplazado",
        "state-rejected": "descartado",
        "like": "me gusta", "dislike": "no me gusta", "completed": "completado",
        "bookmark": "guardar esta tarjeta",
        "brief-title": "Resumen del proyecto",
        "brief-count": "{answered} de {total} respondidas",
        "brief-unanswered": "sin responder",
        "brief-now": "Ahora", "brief-more": "{count} más después de esta",
        "brief-save": "Guardar respuesta", "brief-saved": "Guardado",
        "brief-placeholder": "Responde con tus propias palabras",
        "tags-title": "Etiquetas de referencia", "tags-count": "faltan {left} carpeta(s)",
        "tags-aspects": "Sirve para", "tags-stance": "Postura",
        "tags-quality": "Calidad", "tags-save": "Guardar etiqueta",
        "tags-saved": "Guardado",
        "tag-pursue": "perseguir", "tag-avoid": "evitar",
        "tag-finished": "terminado", "tag-sketch": "boceto",
        "zero-title": "cero estrellas: pésimo, pero sigue en pie",
        "zero-label": "cero estrellas para {element}: pésima ejecución",
    },
}


def strings_for(language: str | None) -> dict[str, str]:
    """Fall back to English PER KEY, not just per language.

    Falling back only when the whole language was unknown left a gap: adding a
    string and forgetting one translation raised KeyError mid-render, so the
    user's own language was the one that crashed while English stayed fine. An
    untranslated word is a blemish; no page at all is a broken tool.
    """
    chosen = STRINGS.get((language or DEFAULT_LANGUAGE).lower(), {})
    return {**STRINGS[DEFAULT_LANGUAGE], **chosen}


def project_language(project_root: Path | None) -> str:
    if project_root is None:
        return DEFAULT_LANGUAGE
    path = project_root / "spec" / "design-harness" / "project.json"
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("language") or DEFAULT_LANGUAGE
    except (OSError, ValueError):
        return DEFAULT_LANGUAGE


def companion_agent(project_root: Path | None) -> tuple[str, str]:
    """Agent name and deep link stored by `open` for header and bottom bar."""
    if project_root is None:
        return "", ""
    path = project_root / "spec" / "design-harness" / "project.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "", ""
    return (str(data.get("companionAgentUrl") or "").strip(),
            str(data.get("companionAgentName") or "").strip())


def save_companion_agent(project_root: Path, url: str = "", name: str = "") -> None:
    # No project.json means there is no project to remember this against. That
    # used to raise, which nothing noticed while only Cursor was ever detected
    # and the save path stayed unreached on a bare directory.
    path = project_root / "spec" / "design-harness" / "project.json"
    if not path.is_file():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    if url.strip():
        data["companionAgentUrl"] = url.strip()
    if name.strip():
        data["companionAgentName"] = name.strip()
    write_json(path, data)


# Which app is running this. Only Cursor was ever detected, so every other host
# fell through to whatever a previous run had saved and the header confidently
# named the wrong app. A host that ships no deep link still gets to name itself.
AGENT_HOSTS = (("CLAUDECODE", "Claude Code"), ("CURSOR_TRACE_ID", "Cursor"))


def agent_context_from_env() -> tuple[str, str]:
    """Best-effort agent identity when the CLI did not pass one."""
    url = (os.environ.get("CURSOR_AGENT_URL") or os.environ.get("AGENT_URL") or "").strip()
    name = (os.environ.get("CURSOR_AGENT_NAME") or os.environ.get("AGENT_NAME")
            or os.environ.get("CURSOR_MODEL") or "").strip()
    if not name:
        name = next((label for var, label in AGENT_HOSTS if os.environ.get(var)), "")
    return url, name


def ensure_brief(project_root: Path) -> bool:
    """Create the project's brief the first time the companion opens.

    `brief_workflow` has been complete and tested since it was written and has
    never once rendered, because `SKILL.md` names no command that creates a
    brief and `render_brief` returns nothing without one. Starting it here
    costs the entry point no bytes, and `open` already means "get this project
    ready to be looked at".
    """
    if not (project_root / "spec" / "design-harness").is_dir():
        return False
    try:
        import brief_workflow
        if brief_workflow.load_brief(project_root) is not None:
            return False
        brief_workflow.save_brief_spec(project_root, brief_workflow.default_brief(
            time.strftime("%Y-%m-%dT%H:%M:%S%z"), project_language(project_root)))
        return True
    except (ImportError, OSError, ValueError):
        return False


def resolve_agent(url: str, name: str, project_root: Path) -> tuple[str, str]:
    """Agent identity, taken whole from one source.

    Resolving the URL and the name independently is what put `Claude Code`
    beside a `cursor://` deep link in a real `project.json`: the name came from
    one run and the link from another. Sources are tried in order and the first
    that says anything supplies both halves, so the pair always agrees.
    """
    for candidate in ((url.strip(), name.strip()),
                      agent_context_from_env(),
                      companion_agent(project_root)):
        if candidate[0] or candidate[1]:
            return candidate
    return "", ""


def agent_display_parts(name: str, url: str = "") -> tuple[str, str]:
    """Split the session line into app + model for balanced header type."""
    name = (name or "").strip()
    if "|" in name:
        parts = [part.strip() for part in name.split("|") if part.strip()]
        if len(parts) >= 2:
            return parts[0], " ".join(parts[1:])
        if parts:
            return parts[0], ""
    app = (os.environ.get("DH_AGENT_APP") or os.environ.get("CURSOR_AGENT_APP") or "").strip()
    lower = (url or "").lower()
    if not app:
        if lower.startswith("cursor:"):
            app = "Cursor"
        elif "claude.ai" in lower or lower.startswith("claude:"):
            app = "Claude"
    if app and name:
        return app, name
    if app:
        return app, ""
    return name, ""


def agent_display_line(name: str, url: str = "") -> str:
    """Plain fallback label when the brand script cannot split app/model."""
    app, model = agent_display_parts(name, url)
    return " ".join(part for part in (app, model) if part).strip()


def check_asks(asks: str, cohort: set[str], language: str | None = None) -> None:
    """A cohort without a real question is a questionnaire nobody can answer."""
    if not cohort:
        return
    text = asks.strip()
    generics = {STRINGS["en"]["zone-round-note"].casefold(),
                STRINGS["es"]["zone-round-note"].casefold()}
    if language:
        generics.add(strings_for(language)["zone-round-note"].casefold())
    if not text:
        return
    if text.casefold() in generics:
        raise HarnessError(
            "this round has no question. Pass --asks \"<the one thing to judge>\", "
            "not the zone's purpose line. The last PNG and the user's last rank name that move.")


MAX_COHORT_SIZE = 6


def check_cohort_size(cohort: set[str], max_size: int = MAX_COHORT_SIZE) -> None:
    """A round nobody can finish reading is not a round, it's a backlog.

    `SKILL.md` and `loop.md` have said "3-6 element cohort" in prose since
    this file's own history, and every round drifted past it anyway because
    nothing enforced it: the round zone never folds ("the round is the ask
    and must never be hidden"), so a large cohort renders every card open,
    unfoldable, and slower to draw and shoot than the reader can use.
    """
    if len(cohort) <= max_size:
        return
    raise HarnessError(
        f"this round's cohort has {len(cohort)} elements, over the {max_size}-element "
        "limit. Split it into two rounds instead of asking the user to judge all of "
        "them at once -- see SKILL.md's '3-6 element cohort' convention.")
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


def empty_decisions() -> dict[str, object]:
    return {"version": VERSION, "state": "draft", "elements": [], "supersededCount": 0}


def load_decisions(output: Path) -> dict[str, object]:
    path = output / "decisions.json"
    if not path.is_file():
        raise HarnessError("decisions.json is missing; run `init` or re-bootstrap")
    return json.loads(path.read_text(encoding="utf-8"))


def render_decisions_md(decisions: dict[str, object]) -> str:
    live = [e for e in decisions["elements"] if e["state"] in ("approved", "proposed")]
    # `completed` is a status, not a lock, so it gets its own section rather than
    # sitting under Standing -- but it must still be rendered. Omitting it made
    # finished elements invisible to any agent resuming from this file.
    done = [e for e in decisions["elements"] if e["state"] == "completed"]
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
    if done:
        lines += ["", "## Completed", "",
                  "Finished for now. Still binding as a record; iteration may continue.",
                  "", "| Element | Stars | Evidence |", "| --- | --- | --- |"]
        for e in sorted(done, key=lambda x: (-x["stars"], x["element"])):
            stars = "★" * e["stars"] + "☆" * (STAR_RANGE[1] - e["stars"])
            lines.append(f"| `{e['element']}` | {stars} | {e['evidence']} |")
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
                    sentiment: str | None | object = KEEP_SENTIMENT,
                    implemented: str | None = None,
                    description: str | None = None,
                    title: str | None = None,
                    scored: bool | None = None,
                    bookmarked: bool | object = KEEP_BOOKMARK) -> dict[str, object]:
    output = project_root.resolve(strict=True) / "spec" / "design-harness"
    if verdict not in DECISION_STATES:
        raise HarnessError(f"verdict must be one of: {', '.join(DECISION_STATES)}")
    if sentiment is not KEEP_SENTIMENT and sentiment is not None and sentiment not in SENTIMENTS:
        raise HarnessError(f"sentiment must be one of: {', '.join(SENTIMENTS)}, or None to withdraw it")
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
    if source == "agent":
        stars = ZERO_STARS
    rank_was_set = source == "user" if scored is None else bool(scored)
    if source == "agent":
        rank_was_set = False
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
            # `scored` means THE USER ranked it. An agent placeholder is a
            # starting position, not a judgement -- recording it as scored
            # painted a gold star on every brand-new proposal, suppressed
            # the "sin puntuar" marker, and made a round the user had not
            # looked at yet read as one they had already judged badly.
            e["scored"] = rank_was_set
            if implemented is not None:
                e["implemented"] = implemented
            if description is not None:
                e["description"] = description
            if title is not None:
                e["title"] = title
            e.setdefault("implemented", None)
            e.setdefault("description", None)
            if sentiment is not KEEP_SENTIMENT:
                e["sentiment"] = sentiment
            e.setdefault("sentiment", None)
            if bookmarked is not KEEP_BOOKMARK:
                e["bookmarked"] = bool(bookmarked)
            e.setdefault("bookmarked", False)
            if preview is not None:
                e["preview"] = preview
            e.setdefault("preview", None)
            e.setdefault("tokens", None)
            break
    else:
        decisions["elements"].append({
            "element": element, "state": verdict, "stars": stars,
            "evidence": evidence, "supersededBy": None, "preview": preview,
            # Same rule on the create path as on the update path: an agent
            # placeholder is a starting position, never a score.
            "source": source, "scored": rank_was_set,
            "sentiment": None if sentiment is KEEP_SENTIMENT else sentiment, "tokens": None,
            "implemented": implemented, "description": description, "title": title,
            "bookmarked": False if bookmarked is KEEP_BOOKMARK else bool(bookmarked),
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


def parse_tokens(raw: str) -> dict[str, object]:
    """The specimen data a design-system section is made of.

    A "Typography" heading over a scoring row is a list, not a design system:
    the section has to show the faces that were chosen, and a palette section
    has to show the actual colours. The ledger held ids and prose and no hex
    value anywhere, so that section could never be more than a list. Shape:

        {"colors": [{"name": "crema", "value": "#F4E9D2", "role": "paper"}],
         "fonts":  [{"name": "Söhne Mono", "stack": "ui-monospace",
                     "use": "display", "sample": "Aa"}]}
    """
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as err:
        raise HarnessError(f"--tokens is not valid JSON: {err}") from err
    return validate_tokens(value)


def validate_tokens(value: object) -> dict[str, object]:
    """Checked here, not in the CLI: the rules protect the ledger, so they have
    to hold for every caller rather than only for people typing a command."""
    if not isinstance(value, dict):
        raise HarnessError('--tokens must be a JSON object, e.g. {"colors": [...]}')
    for key, items in value.items():
        if key not in ("colors", "fonts"):
            raise HarnessError(f"unknown token group: {key} (expected colors or fonts)")
        if not isinstance(items, list) or not all(isinstance(i, dict) for i in items):
            raise HarnessError(f"{key} must be a list of objects")
    for swatch in value.get("colors", []):
        if not str(swatch.get("value", "")).strip():
            raise HarnessError("every colour token needs a `value` (the hex the design uses)")
    # Either every colour in a set is separately rankable or none is. A set
    # where only the first carries an `element` renders one swatch with a
    # star strip and the rest without -- which reads as a broken page, and
    # is how a three-colour palette came to show scoring under `amarillo`
    # alone. Half-linked is not a state the ledger should be able to hold.
    linked = [bool(str(c.get("element", "")).strip()) for c in value.get("colors", [])]
    if len(linked) > 1 and any(linked) and not all(linked):
        named = [str(c.get("name") or c.get("value"))
                 for c, has in zip(value.get("colors", []), linked) if not has]
        raise HarnessError(
            "these colours carry no `element`, but others in the same set do: "
            + ", ".join(named)
            + ". Give every colour its own element id so each is rankable, or give none of "
            "them one so the set is ranked by its own row. A set where only some are "
            "rankable renders as a palette that half failed to draw.")
    for face in value.get("fonts", []):
        if not str(face.get("name", "")).strip():
            raise HarnessError("every font token needs a `name` (the face that was chosen)")
        for key_name in ("element",):
            if face.get(key_name) is not None and not str(face[key_name]).strip():
                raise HarnessError(f"font `{key_name}` cannot be blank")
        variants = face.get("variants")
        if variants is not None:
            if not isinstance(variants, list) or not all(isinstance(v, dict) for v in variants):
                raise HarnessError("font `variants` must be a list of objects")
            for variant in variants:
                if not str(variant.get("use", "")).strip():
                    raise HarnessError(
                        "every font variant needs a `use` -- a weight nobody can point at a job "
                        "is a specimen, not a system")
    return value


def describe_element(project_root: Path, element: str,
                     description: str | None, implemented: str | None,
                     tokens: dict[str, object] | None = None) -> dict[str, object]:
    """Label an existing element without touching its verdict, rank or source.

    `decide` cannot do this: it demands a verdict and a rank, so relabelling a
    user-ranked row means retyping the user's stars -- the invention the star cap
    exists to prevent.
    """
    output = project_root.resolve(strict=True) / "spec" / "design-harness"
    if description is None and implemented is None and tokens is None:
        raise HarnessError("nothing to set: pass --description, --implemented and/or --tokens")
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
    if tokens is not None:
        entry["tokens"] = validate_tokens(tokens)
    write_json(output / "decisions.json", decisions)
    (output / "DECISIONS.md").write_text(render_decisions_md(decisions), encoding="utf-8")
    return entry


def retire_element(project_root: Path, loser: str, winner: str,
                   evidence: str) -> dict[str, object]:
    """Retire `loser` in favour of `winner`, touching nothing on the winner.

    `decide --supersedes` cannot do this. It records the supersede on the
    WINNER, and the winner is necessarily the element the user just ranked --
    so writing it re-runs the agent path, which is capped at 1 star and stamps
    `source=agent`. Recording a win therefore destroyed the very click that
    decided it: a user's 3-star rank came back as agent 1-star, and `adopt`
    would not restore it because it had already consumed that click. The
    supersede belongs on the loser, where nothing the user set is at stake.
    """
    output = project_root.resolve(strict=True) / "spec" / "design-harness"
    if loser == winner:
        raise HarnessError("an element cannot supersede itself")
    if not evidence.strip():
        raise HarnessError("evidence is required: quote the user, do not paraphrase")
    decisions = load_decisions(output)
    by_id = {e["element"]: e for e in decisions["elements"]}
    for name in (loser, winner):
        if name not in by_id:
            raise HarnessError(f"unknown element: {name}. Record it with `decide` first.")
    entry = by_id[loser]
    if entry["state"] == "superseded" and entry.get("supersededBy") == winner:
        return entry
    entry["state"] = "superseded"
    entry["supersededBy"] = winner
    entry["evidence"] = evidence
    decisions["supersededCount"] += 1
    if any(e["state"] == "approved" for e in decisions["elements"]):
        decisions["state"] = "approved"
    write_json(output / "decisions.json", decisions)
    (output / "DECISIONS.md").write_text(render_decisions_md(decisions), encoding="utf-8")
    project_path = output / "project.json"
    project = json.loads(project_path.read_text(encoding="utf-8"))
    project["state"] = decisions["state"]
    write_json(project_path, project)
    return entry


def ledger_cursor_key(project_root: Path, ledger_path: Path) -> str:
    """Name a companion ledger without baking an absolute path into decisions.json."""
    resolved = ledger_path.resolve()
    root = project_root.resolve(strict=True)
    return str(resolved.relative_to(root)) if is_within(resolved, root) else resolved.name


def adopt_companion(project_root: Path, ledger_path: Path) -> tuple[int, int]:
    """Fold the companion's durable ledger into the harness ledger.

    The companion records what the user actually clicked and ranked. Without this
    step an agent re-types those decisions by hand, which is where design-element
    ids drift and elements in standing get silently rebuilt.

    Only lines added since the last adopt are replayed. Replaying the whole
    ledger every run re-litigates settled history: `decide --source user` writes
    straight to decisions.json and never appears in this file, so an approval
    granted after the user un-ticked a box has no position in the chronological
    replay -- and the older `proposed` click lands back on top of it. That
    silently downgraded seven standing elements in one run.
    """
    if not ledger_path.is_file():
        raise HarnessError(f"companion ledger not found: {ledger_path}")

    def is_star(value: object) -> bool:
        if not isinstance(value, int) or isinstance(value, bool):
            return False
        return value == ZERO_STARS or STAR_RANGE[0] <= value <= STAR_RANGE[1]

    output = project_root.resolve(strict=True) / "spec" / "design-harness"
    decisions = load_decisions(output)
    existing = {e["element"]: dict(e) for e in decisions["elements"]}
    lines = ledger_path.read_text(encoding="utf-8").splitlines()
    key = ledger_cursor_key(project_root, ledger_path)
    cursor = (decisions.get("adoptedLedgers") or {}).get(key) or {}
    start = cursor.get("lines") or 0
    # The mark is only trustworthy if the lines it claims to have consumed are
    # still the same lines. A companion restart writes a fresh ledger at the
    # same path; trusting a stale count there would skip real clicks, so an
    # unrecognised prefix falls back to a full replay.
    if not isinstance(start, int) or not 0 <= start <= len(lines) or \
            ledger_digest(lines[:start]) != cursor.get("digest"):
        start = 0
    accepted: list[tuple[int, int, dict[str, object]]] = []
    resets: list[tuple[int, int, str]] = []
    skipped = 0
    for index, line in enumerate(lines):
        line = line.strip()
        if index < start or not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            skipped += 1
            continue
        element = event.get("element")
        if element == PROBE_ELEMENT:
            skipped += 1
            continue
        stars, sentiment = event.get("stars"), event.get("sentiment")
        has_sentiment = "sentiment" in event
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
        # Companions spell the completed status differently, and un-completing
        # arrives as `proposed`. Both were being skipped: 15 real toggle-offs in
        # one ledger were discarded because `proposed` was not on this list, so
        # un-ticking a box did nothing and the tick came back on the next adopt.
        if event.get("verdict") == "reviewed":
            event["verdict"] = "completed"
        if event.get("verdict") not in (None, "approved", "rejected", "completed", "proposed"):
            skipped += 1
            continue
        if sentiment is not None and sentiment not in SENTIMENTS:
            skipped += 1
            continue
        # `"sentiment": null` present is a WITHDRAWAL and carries signal; the key
        # missing entirely means the event never spoke about the thumb. The
        # rehydrate script has always drawn this line (`if('sentiment' in ev)`)
        # -- adopt did not, so the browser cleared the chip and the ledger kept
        # the like forever.
        if not has_sentiment and "bookmark" not in event and event.get("verdict") is None \
                and not is_star(stars):
            skipped += 1
            continue
        # Replay order is fixed by (timestamp, file position) so adopting the
        # same ledger twice always yields the same ledger.
        stamp = event.get("timestamp")
        stamp = stamp if isinstance(stamp, (int, float)) and not isinstance(stamp, bool) else 0
        accepted.append((int(stamp), index, event))

    # Resolve each event against the ledger AS OF that event, not as of the start
    # of the batch. A rank and a verdict on the same element at the same
    # millisecond (max stars auto-fires a completed toggle) used to be resolved
    # against the same pre-batch snapshot, so the verdict -- carrying no stars of
    # its own -- fell back to the pre-batch rank and overwrote the star just set.
    for _, _, event in sorted(accepted, key=lambda row: (row[0], row[1])):
        element = event["element"]
        stars, sentiment = event.get("stars"), event.get("sentiment")
        has_sentiment = "sentiment" in event
        explicit = event.get("verdict")
        prior = existing.get(element, {})
        if explicit in ("approved", "rejected", "completed", "proposed"):
            # Only an explicit verdict control moves state. A star never does.
            verdict = explicit
        else:
            # Scores and thumbs leave state alone: an element already standing
            # stays standing, and a new one arrives as `proposed` for review.
            verdict = prior.get("state") or "proposed"
        # Only the dedicated rank interaction establishes rank provenance.
        # Older companions omitted `type`, so a numeric non-sentiment event is
        # accepted as a rank for compatibility. A thumb event carrying stars=0
        # is never a rank: that historical UI bug poisoned coverage otherwise.
        establishes_rank = event.get("type") == "rank" or (
            event.get("type") is None and not has_sentiment and is_star(stars))
        rank = stars if establishes_rank and is_star(stars) else prior.get("stars", 0)
        rank_was_set = bool(establishes_rank or prior.get("scored"))
        withdrawn = "sentiment" in event and sentiment is None
        bookmark_only = "bookmark" in event and not has_sentiment and event.get("verdict") is None \
            and not is_star(stars)
        evidence = str(event.get("text") or "").strip() or (
            (f"companion {'bookmarked' if event.get('bookmark') else 'unbookmarked'} it"
             if bookmark_only else
             f"companion {sentiment}: {rank} star" if sentiment else
             (f"companion withdrew the thumb: {rank} star" if withdrawn
              else f"companion rank: {rank} star")))
        record_decision(project_root, element, verdict, rank, evidence[:400], [],
                        source="user", scored=rank_was_set,
                        sentiment=sentiment if "sentiment" in event else KEEP_SENTIMENT,
                        bookmarked=event["bookmark"] if "bookmark" in event else KEEP_BOOKMARK)
        existing[element] = dict(prior, element=element, state=verdict, stars=rank,
                                 source="user", scored=rank_was_set)
    for _, _, element in sorted(resets, key=lambda row: (row[0], row[1])):
        score_zero(project_root, element)
    # Re-read: every record_decision above rewrote the file underneath us.
    decisions = load_decisions(output)
    ledgers = dict(decisions.get("adoptedLedgers") or {})
    ledgers[key] = {"lines": len(lines), "digest": ledger_digest(lines)}
    decisions["adoptedLedgers"] = ledgers
    write_json(output / "decisions.json", decisions)
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


STYLE_MARKER = "/* dh-controls */"
# Bumped whenever the emitted CSS or markup changes. `embed` bakes both into the
# screen, so a screen embedded by an older skill keeps the older bug forever and
# looks, from the browser, exactly like a fix that did not work. `doctor`
# compares this against the served page and fails on a mismatch.
CONTROLS_VERSION = "37"
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
REHYDRATE_SCRIPT = _screen("rehydrate.js")
FEEDBACK_STYLE = _screen("controls.css")

# The stamp rides the stylesheet because that is the one asset `embed` always
# rewrites into the screen. On the wrapper it never survived: `embed` lifts the
# rows out of the generated block and leaves the wrapper behind.
FEEDBACK_STYLE = FEEDBACK_STYLE.replace(
    STYLE_MARKER, f"{STYLE_MARKER}\n/* dh-controls-version: {CONTROLS_VERSION} */", 1)


# Drawing a comp as raw SVG is the one job the model is worst at: it authors a
# coordinate system it never sees. The ledger recorded the cost -- 59 previews
# holding 6352 <rect> and 15 <path>, and 34 of them carrying a near-zero opacity
# somewhere. One session shipped a comp wrapped in a nested `opacity="0.13"` and
# the NEXT session's entire round was spent repairing it, not improving it.
#
# So a preview is drawn in HTML/CSS -- which the model is good at, and which the
# browser lays out instead of the model -- rendered to a small PNG, and gated on
# its own PIXELS before it can be recorded. "Nearly invisible" stops being a
# thing a session can discover one score later.
CHROME_CANDIDATES = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
)
# 8.5x11 at a deliberately cheap resolution. The thumbnail is read at 96px and
# the slideshow at roughly 700px tall, so this is already generous, and every
# preview is base64-inlined into the article -- a 2x render would triple a page
# that is already over a megabyte for nothing the reader can see.
PREVIEW_WIDTH = 510
PREVIEW_RATIO = 11 / 8.5
# Below this fraction of non-background pixels the comp is not "minimal", it is
# absent. Deliberately loose: coverage is a blank-page check and nothing more.
# Measured on real renders, a faded comp and a good one sit only 2.5x apart on
# coverage (1.26% against 3.11%) but 7x apart on contrast (94 against 699), so a
# coverage threshold tight enough to catch fading would start refusing sparse
# comps that are perfectly legible. Contrast is the discriminator; this only
# catches a page with nothing on it at all.
MIN_INK_COVERAGE = 0.005
# And ink that IS there has to be distinguishable from the ground it sits on.
# This is the threshold that actually catches the opacity failure: a comp faded
# to 13% still covers a THIRD of the page in pixels that differ from the ground,
# so coverage alone waves it through -- it is not blank, it is weak. What
# separates it is that its strongest mark reaches only ~60/765 of contrast,
# where a real comp (even a deliberately sparse one) puts something at 650+.
# Coverage answers "is anything there"; contrast answers "can any of it be seen".
MIN_INK_CONTRAST = 180


def find_chrome() -> str:
    for candidate in CHROME_CANDIDATES:
        if Path(candidate).is_file():
            return candidate
    for name in ("chromium", "google-chrome", "google-chrome-stable", "chrome"):
        found = shutil.which(name)
        if found:
            return found
    return ""


def check_no_hand_authored_svg(html: Path) -> None:
    """Refuse a comp that draws its own `<svg>` instead of writing HTML/CSS.

    loop.md has said "never hand-author SVG" since this file's own history: a
    session once carried 59 such previews holding 6352 `<rect>` and 15 `<path>`
    the model invented rather than sourced, 34 of them faded to near-zero
    opacity. That was a prose rule nobody mechanically checked, so it kept
    getting written anyway. A comp needing a real graphic references a fetched
    or project asset with `<img src="...">` -- that never matches this check,
    because the SVG markup lives in the referenced file, not in the comp.
    """
    text = html.read_text(encoding="utf-8", errors="replace")
    if re.search(r"<svg\b", text, re.I):
        raise HarnessError(
            f"{html.name} hand-authors an <svg> element. Comps are drawn in HTML/CSS; "
            "a graphic is reused from the project, fetched from a pinned licensed source "
            "and referenced with <img src=\"...\">, generated deterministically in CSS, "
            "or omitted. See asset-sourcing.md. Remove the inline <svg> and redraw the "
            "comp before shooting it.")


def audit_recorded_svg(project_root: Path) -> list[dict[str, str]]:
    """Find elements ALREADY in the ledger whose recorded preview hand-authors SVG.

    `check_no_hand_authored_svg` only stops a NEW comp from being shot. It has
    no opinion on what a session recorded before that gate existed -- and a
    project that hit this failure for real can carry dozens of them, each one
    an element a designer cannot see rendered because there is no PNG to
    canonicalise, only the raw markup that made it into the article. This
    reads the ledger and reports every one by element id and recorded path, so
    they can be found and redrawn instead of discovered one crash at a time.
    """
    project_root = project_root.resolve(strict=True)
    output = project_root / "spec" / "design-harness"
    decisions_path = output / "decisions.json"
    if not decisions_path.is_file():
        return []
    decisions = json.loads(decisions_path.read_text(encoding="utf-8"))
    hits = []
    for entry in decisions.get("elements", []):
        preview = entry.get("preview")
        if not isinstance(preview, dict):
            continue
        rel = preview.get("path")
        if not rel or not str(rel).lower().endswith((".html", ".svg")):
            continue
        candidate = project_root / rel
        if not candidate.is_file():
            continue
        try:
            text = candidate.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if re.search(r"<svg\b", text, re.I):
            hits.append({"element": entry.get("element", ""), "path": str(rel)})
    return hits


def render_html_preview(html: Path, out: Path, width: int = PREVIEW_WIDTH,
                        timeout: int = 45, chrome_timeout: int = 12) -> str:
    """Rasterise a comp. Returns the renderer used, or raises.

    Chrome is preferred because it honours the CSS the comp was written in.
    `qlmanage` is the fallback that needs nothing installed, but QuickLook fits
    the page into a square thumbnail, so the comp must not depend on its own
    aspect ratio to read.

    Chrome and qlmanage get SEPARATE budgets. A local static-HTML screenshot
    should resolve in well under `chrome_timeout` seconds -- sharing one long
    `timeout` between both legs meant a hung or GPU-flaky Chrome process ate
    the whole budget before falling back, turning one slow shot into the
    worst-case wait for every shot in a round.
    """
    html = html.resolve(strict=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    height = int(round(width * PREVIEW_RATIO))
    chrome = find_chrome()
    if chrome:
        profile = tempfile.mkdtemp(prefix="dh-shot-")
        try:
            result = subprocess.run(
                [chrome, "--headless=new", "--disable-gpu", "--no-first-run",
                 "--no-default-browser-check", "--disable-extensions", "--disable-sync",
                 f"--user-data-dir={profile}", "--hide-scrollbars",
                 "--force-device-scale-factor=1", "--virtual-time-budget=3000",
                 f"--window-size={width},{height}",
                 f"--screenshot={out}", html.as_uri()],
                capture_output=True, timeout=chrome_timeout)
            if out.is_file() and out.stat().st_size:
                return "chrome"
            detail = (result.stderr or b"").decode("utf-8", "replace").strip()[:200]
        except subprocess.TimeoutExpired:
            detail = "timed out"
        finally:
            shutil.rmtree(profile, ignore_errors=True)
    else:
        detail = "no chrome/chromium found"
    if not shutil.which("qlmanage"):
        raise HarnessError(f"could not render {html.name}: {detail}, and qlmanage "
                           "is unavailable. Install Chrome or render the PNG yourself.")
    with tempfile.TemporaryDirectory() as staging:
        # Render LARGER than the target: QuickLook fits the page inside a square
        # and anchors it top-left, so the comp comes back small in a big empty
        # frame. Oversampling means the crop below still has pixels to keep.
        subprocess.run(["qlmanage", "-t", "-s", str(width * 3), "-o", staging, str(html)],
                       capture_output=True, timeout=timeout)
        made = list(Path(staging).glob("*.png"))
        if not made:
            raise HarnessError(f"could not render {html.name}: {detail}, and QuickLook "
                               "produced nothing either.")
        shutil.copyfile(made[0], out)
    trim_to_content(out, width)
    return "qlmanage"


def trim_to_content(png: Path, width: int) -> None:
    """Crop a render down to what was actually drawn, then scale it to width.

    QuickLook returns a SQUARE thumbnail with the page anchored top-left: a
    letter-shaped comp arrived as 171x221 of drawing inside 510x510 of white --
    85% empty. The article then fitted that whole square into a 96px portrait
    frame, so the comp itself rendered about 32px across and read as a blank
    card. Cropping to the content restores the comp's own aspect, and the frame
    fills the way it does for a Chrome render.

    A no-op on Chrome output, whose bounding box is already the whole image.
    """
    try:
        from PIL import Image, ImageChops
    except ImportError:
        return
    target = 1 / PREVIEW_RATIO          # width/height of the page we asked for
    with Image.open(png) as handle:
        image = handle.convert("RGB")
        # The corner pixel is the letterbox on a padded render -- but on a
        # FULL-BLEED one it is the comp's own ground, and cropping to "what
        # differs from it" then eats the design down to its ink. A test caught
        # that shaving 41px off a correct 510x660 render.
        #
        # So crop only when doing so RECOVERS the shape we asked for: the
        # padded square moves from 1.00 toward 0.77, while a full-bleed render
        # is already there and any crop takes it further away.
        ground = image.getpixel((0, 0))
        box = ImageChops.difference(
            image, Image.new("RGB", image.size, ground)).getbbox()
        if box:
            cropped_w, cropped_h = box[2] - box[0], box[3] - box[1]
            if cropped_w and cropped_h:
                before = abs(image.width / image.height - target)
                after = abs(cropped_w / cropped_h - target)
                if after < before:
                    image = image.crop(box)
        if image.width != width and image.width:
            height = max(1, round(image.height * width / image.width))
            image = image.resize((width, height), Image.LANCZOS)
        image.save(png)


def preview_ink(png: Path) -> dict[str, float]:
    """Measure what a rendered comp actually puts on the page.

    Reported as numbers rather than a verdict so the caller can say WHY it is
    refusing, and so a legitimately sparse comp can be argued about against a
    figure instead of an opinion.
    """
    try:
        from PIL import Image
    except ImportError:
        return {}
    with Image.open(png) as handle:
        image = handle.convert("RGB")
        if max(image.size) > 400:  # measuring does not need full resolution
            image.thumbnail((400, 400))
        # `getdata` is deprecated in Pillow 12 and gone in 14; `getpixel` over a
        # thumbnailed image is small enough that the loop costs nothing.
        width, height = image.size
        pixels = [image.getpixel((x, y)) for y in range(height) for x in range(width)]
    if not pixels:
        return {"coverage": 0.0, "contrast": 0.0}
    counts: dict[tuple, int] = {}
    for pixel in pixels:
        counts[pixel] = counts.get(pixel, 0) + 1
    ground = max(counts, key=counts.get)

    def distance(pixel: tuple) -> int:
        return sum(abs(a - b) for a, b in zip(pixel, ground))

    ink = [p for p in pixels if distance(p) > 40]
    return {"coverage": len(ink) / len(pixels),
            "contrast": float(max((distance(p) for p in ink), default=0)),
            "ground": ground}


def check_preview_legible(png: Path) -> None:
    """Refuse a comp the user would be asked to score without being able to see it."""
    ink = preview_ink(png)
    if not ink:  # no Pillow: measuring is unavailable, not failing
        return
    if ink["coverage"] < MIN_INK_COVERAGE:
        raise HarnessError(
            f"{png.name} renders essentially blank -- {ink['coverage'] * 100:.2f}% of the "
            f"page differs from its own ground. This is the `opacity=0.13` failure: the "
            "markup is there and the drawing is not. Open the HTML, fix what is hiding it, "
            "and shoot it again. Do not record a preview the user cannot see.")
    if ink["contrast"] < MIN_INK_CONTRAST:
        raise HarnessError(
            f"{png.name} has ink but no contrast -- the strongest mark is only "
            f"{ink['contrast']:.0f}/765 away from the ground. Nothing on this page can be "
            "read at thumbnail size, so a score would be a score of nothing.")


def preferred_preview_path(project_root: Path, preview_path: Path, element: str) -> Path:
    """Prefer the drawn HTML comp over a raster thumbnail when both exist."""
    if preview_path.suffix.lower() == ".html":
        return preview_path
    for candidate in (
        project_root / "content" / f"{element}.html",
        project_root / "content" / f"{preview_path.stem}.html",
    ):
        if candidate.is_file():
            return candidate
    return preview_path


COMP_SCOPE_CLASS = "dh-comp-scope"


def comp_scope_id(element: str) -> str:
    """A CSS-safe, per-element scope class suffix.

    Two comps that both use `.title` or `.mini` (a common authoring
    convention across similar comps) must not fight over which one's rule
    wins on a page that embeds many comps at once. `@scope` only isolates
    against elements OUTSIDE the scope root -- every comp sharing the same
    root class (`.dh-comp-scope`) is not outside any other comp's scope, so
    their `.title` rules collided globally and the wrong comp's font-size
    (or any other property) could win by source order. Hashing the element
    id keeps the class valid regardless of dots or other characters in it.
    """
    return hashlib.sha256(element.encode("utf-8")).hexdigest()[:12]


def scope_comp_css(css: str, scope_class: str = COMP_SCOPE_CLASS) -> str:
    """Rewrite comp CSS so it cannot restyle the companion frame or leak
    into a different comp embedded elsewhere on the same page.

    Comps are drawn as standalone HTML pages with `body { width: 510px }`.
    Inlined verbatim, every thumbnail overwrites the frame's body and the
    whole page shrinks to one comp width -- exactly the broken layout.
    Rewriting :root/html/body to `.dh-comp-scope` AND wrapping in
    `@scope (.dh-comp-scope)` made host rules miss: a selector inside
    `@scope` is a descendant of the root, so `.dh-comp-scope { background }`
    never matched the host. The drawing went blank (white on the lightbox,
    transparent on the card). `:scope` is the host.

    `scope_class` must be unique PER COMP, not the shared `dh-comp-scope`
    class alone -- see `comp_scope_id`.
    """
    if not css.strip():
        return css
    css = re.sub(r":root\b", ":scope", css)
    css = re.sub(r"(?<![\w-])html(?![\w-])", ":scope", css)
    css = re.sub(r"(?<![\w-])body(?![\w-])", ":scope", css)
    if "@scope" in css:
        return css
    return f"@scope (.{scope_class}) {{\n{css}\n}}\n"


def _css_px(css: str, names: tuple[str, ...]) -> float | None:
    """First declared px size among logical and physical properties."""
    for name in names:
        match = re.search(rf"(?<![\w-]){name}:\s*(\d+(?:\.\d+)?)px", css)
        if match:
            return float(match.group(1))
    return None


def html_comp_fragment(raw: str, element: str = "") -> tuple[str, float, float]:
    """Body + styles from a comp file, and its declared page size.

    `element` seeds a per-comp scope class (see `comp_scope_id`) so that two
    comps embedded on the same page never fight over a shared class name
    like `.title` or `.mini`.
    """
    width, height = 850.0, 1100.0
    if re.search(r"<html", raw, re.I):
        styles = "".join(re.findall(r"<style[^>]*>(.*?)</style>", raw, re.S | re.I))
        body_match = re.search(r"<body[^>]*>(.*)</body>", raw, re.S | re.I)
        body = body_match.group(1) if body_match else raw
        # New comps size the page with inline-size/block-size. Reading only
        # `width`/`min-height` left those at the 850×1100 default, so the
        # slideshow scaled a 510 drawing into the corner of a white stage.
        width = _css_px(styles, ("inline-size", "width")) or width
        height = (_css_px(styles, ("block-size", "min-block-size",
                                   "min-height", "height")) or height)
        scope_class = f"{COMP_SCOPE_CLASS}-{comp_scope_id(element)}" if element else COMP_SCOPE_CLASS
        scoped = scope_comp_css(styles, scope_class)
        return (f"<style>{scoped}</style>"
                f'<div class="{COMP_SCOPE_CLASS} {scope_class}">{body}</div>'), width, height
    return raw, width, height


def preview_inner_style(comp_width: float, comp_height: float) -> str:
    return ("position:absolute;inset-block-start:0;inset-inline-start:0;"
            f"inline-size:{comp_width}px;block-size:{comp_height}px;transform-origin:0 0;"
            f"transform:scale(calc(var(--dh-shot-w,96px) / {comp_width}));pointer-events:none")


def preview_reference(project_root: Path, raw: str, element: str = "") -> dict[str, str]:
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
    # `shoot` writes a PNG so the agent can inspect the rendered pixels. When
    # the matching HTML comp also exists it is the canonical interactive
    # drawing. Store that identity now instead of silently swapping assets only
    # while rendering the article; cards, chart tooltips, slideshow and ledger
    # then all name the same thing.
    if element:
        candidate = preferred_preview_path(project_root, candidate, element)
    if candidate.suffix.lower() == ".svg":
        raise HarnessError(
            f"{candidate.name} is an .svg file recorded directly as a preview -- unchecked "
            "and unrenderable by the pipeline that gates every other comp. Draw it in "
            "HTML/CSS, `shoot` it to a PNG, and `decide --preview` that comp instead.")
    if candidate.suffix.lower() not in PREVIEW_SUFFIXES:
        raise HarnessError(f"unsupported preview type '{candidate.suffix}'; use one of "
                           + ", ".join(sorted(PREVIEW_SUFFIXES)))
    # A rendered comp can be checked; hand-authored SVG cannot be, which is
    # exactly why it is no longer the way to draw one.
    if candidate.suffix.lower() == ".png":
        check_preview_legible(candidate)
    return {"path": candidate.relative_to(project_root).as_posix(), "sha256": sha256_file(candidate)}


def canonicalize_recorded_previews(project_root: Path,
                                   decisions: dict[str, object]) -> int:
    """Migrate raster-era records to their matching interactive comp.

    Old articles swapped this only at render time, so the ledger named one
    asset while the card and slideshow showed another. Persist the resolution
    once; subsequent rendering is literal and every view stays in sync.
    """
    changed = 0
    for entry in decisions["elements"]:
        preview = entry.get("preview")
        if not preview or not preview.get("path"):
            continue
        recorded = project_root / str(preview["path"])
        if not recorded.is_file():
            continue
        canonical = preferred_preview_path(project_root, recorded, str(entry["element"]))
        if canonical == recorded:
            continue
        entry["preview"] = {
            "path": canonical.relative_to(project_root).as_posix(),
            "sha256": sha256_file(canonical),
        }
        changed += 1
    if changed:
        output = project_root / "spec" / "design-harness"
        write_json(output / "decisions.json", decisions)
        (output / "DECISIONS.md").write_text(render_decisions_md(decisions), encoding="utf-8")
    return changed


def render_preview(project_root: Path | None, preview: dict[str, str] | None, element: str,
                   txt: dict[str, str] | None = None) -> str:
    """Inline the graphic for one element, or say plainly that there is none.

    The "no graphic" state carries a stable CLASS as well as its words: doctor
    used to grep for the Spanish text, so translating the strip would have
    quietly disabled the check that every row shows what is being judged.
    """
    txt = txt or strings_for(DEFAULT_LANGUAGE)
    # Every thumbnail names the element it draws. A click can then open that
    # element's slide wherever the thumbnail sits -- in a row, in a folded
    # backlog strip, or beside a specimen. Without the id the folded strips
    # were 95 pictures that led nowhere.
    tag = f'<div class="dh-shot" data-el="{html_escape(element)}" style="{SHOT_INLINE}">'
    if not preview:
        return (f'{tag}<span class="dh-shot-missing" data-dh-no-graphic="1">{txt["no-graphic"]}'
                '<br>--preview</span></div>')
    if project_root is None:
        return f'{tag}<span class="dh-shot-missing">{preview["path"]}</span></div>'

    path = project_root / preview["path"]
    if not path.is_file():
        return (f'{tag}<span class="dh-shot-missing">gráfico ausente<br>'
                f'{preview["path"]}</span></div>')
    suffix = path.suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
        media = "image/jpeg" if suffix in {".jpg", ".jpeg"} else f"image/{suffix.lstrip('.')}"
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        body = f'<img alt="" src="data:{media};base64,{encoded}">'
        return f"{tag}{body}</div>"
    fragment = path.read_text(encoding="utf-8")
    if suffix == ".svg":
        fragment = re.sub(r"<svg\b", '<svg preserveAspectRatio="xMidYMid meet" '
                          'style="width:100%;height:100%;display:block"', fragment, count=1)
        return f"{tag}{fragment}</div>"
    body, comp_width, comp_height = html_comp_fragment(fragment, element)
    return (f'{tag}<div class="dh-shot-inner" data-comp-w="{comp_width}" '
            f'data-comp-h="{comp_height}" style="{preview_inner_style(comp_width, comp_height)}">'
            f'{body}</div></div>')


def display_name(entry: dict[str, object]) -> str:
    """What to call this design in front of a designer.

    The card used to be headed `cover.object.character-drawn.dentro-de-margen.
    sin-colision`. That is a stable id for the ledger and it is unreadable as a
    title -- the reader has to parse a namespace to find out what they are
    looking at. A plain `--title` wins; failing that the id's last meaningful
    segment is humanised, which at least reads as words.
    """
    given = str(entry.get("title") or "").strip()
    if given:
        return given
    # No title set: the description already says what this is, in the user's
    # own language, so its first clause beats a humanised id every time --
    # "el objeto de portada dibujado grande" against "Sin colision".
    described = str(entry.get("description") or "").strip()
    if described:
        clause = re.split(r"[,;:.\u2014]| -- ", described, maxsplit=1)[0].strip()
        if 3 <= len(clause) <= 64:
            return clause[0].upper() + clause[1:]
    parts = [part for part in str(entry["element"]).split(".") if part]
    tail = " ".join(parts[-2:]) if len(parts) > 2 else " ".join(parts)
    tail = tail.replace("-", " ").replace("_", " ").replace(".", " ").strip()
    return (tail[0].upper() + tail[1:]) if tail else str(entry["element"])


def display_names(entries: list[dict[str, object]]) -> dict[str, str]:
    """Names for a whole list, guaranteed distinct.

    A redraw inherits its parent's description, so `cover.object.character-drawn`
    and `...dentro-de-margen.sin-colision` both resolved to "El objeto de portada
    dibujado grande" -- and the round view puts exactly those two side by side as
    before and after. Two identical titles over two different drawings is worse
    than the dotted id was. Collisions take the segment that distinguishes them.
    """
    names: dict[str, str] = {}
    taken: dict[str, str] = {}
    for entry in entries:
        element = str(entry["element"])
        name = display_name(entry)
        if name in taken and taken[name] != element:
            tail = element.split(".")[-1].replace("-", " ").replace("_", " ")
            name = f"{name} — {tail}"
        taken.setdefault(name, element)
        names[element] = name
    return names


def extract_feedback_rows(markup: str) -> dict[str, str]:
    """Pull complete `.dh-fb` rows out of generated controls markup.

    A naive `.*?\\n</div>` stops at the first closing tag inside an inlined
    HTML comp preview, which truncates versus-pair rows and nests the rest of
    the round zone inside a thumbnail.
    """
    rows: dict[str, str] = {}
    for opening in re.finditer(r'<div class="dh-fb" data-element="([^"]+)"[^>]*>', markup):
        element = opening.group(1)
        depth = 1
        end = opening.end()
        for tag in re.finditer(r"<(/?)div\b[^>]*>", markup[opening.end():]):
            depth += -1 if tag.group(1) else 1
            if depth == 0:
                end = opening.end() + tag.end()
                break
        else:
            raise HarnessError(f"unbalanced <div> in feedback row for {element}")
        rows[element] = markup[opening.start():end]
    return rows


def render_feedback_controls(decisions: dict[str, object], theme: dict[str, str] | None = None,
                             project_root: Path | None = None,
                             pinned: set[str] | None = None,
                             language: str | None = None) -> str:
    """Emit rank + sentiment controls for every element in standing.

    Generated from the ledger so a screen cannot invent a design-element id.
    Each row carries the graphic being ranked: a star next to a dotted id is a
    guess, not a judgement. Same ledger, theme and previews in, byte-identical
    markup out.
    """
    pinned = pinned or set()
    txt = strings_for(language or project_language(project_root))
    live = [e for e in decisions["elements"] if e["state"] in GROUP_OF]
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
             f'<div class="dh-feedback" data-{VERSION_MARKER}="{CONTROLS_VERSION}" '
             f'data-saved="{html_escape(txt["saved"])}"{wrapper_style}>',
             f'<strong class="dh-offline">{txt["offline"]}</strong>']
    if not live:
        lines.append("<!-- no elements in standing; record one with `decide` first -->")
    # Grouped by design-system foundation, not by lifecycle. The user asked to
    # see the typography together, the palette together -- that is a design
    # system with a rank against each part. Lifecycle still rides on each row's
    # own state chip, where it belongs.
    def group_of(item: dict[str, object]) -> str:
        return "pinned" if item["element"] in pinned else foundation_of(item["element"])
    def order(item: dict[str, object]) -> tuple:
        # This round first, then the foundations in reading order, then best
        # execution first, then id so the output stays byte-stable.
        return (0 if item["element"] in pinned else 1,
                FOUNDATION_ORDER.get(group_of(item), len(FOUNDATION_ORDER)),
                -int(item.get("stars") or 0),
                item["element"])
    names = display_names(live)
    rendered_group = None
    for entry in sorted(live, key=order):
        group_key = group_of(entry)
        if group_key != rendered_group:
            rendered_group = group_key
            label = txt["from-this-round"] if group_key == "pinned" else txt.get(group_key, group_key)
            tally = sum(1 for e in live if group_of(e) == group_key)
            lines.append(f'<h4 class="dh-group" data-group="{group_key}">{label}<span class="dh-count">{tally}</span></h4>')
        element, stars = entry["element"], entry["stars"]
        # The strip already greys an unscored bar; the ROW painted its
        # stars straight from the number regardless of who put it there.
        user_ranked = entry.get("source") == "user" and bool(entry.get("scored"))
        lines.append(
            f'<div class="dh-fb" data-element="{element}" data-stars="{stars if user_ranked else 0}" '
            f'data-scored="{"yes" if user_ranked else "no"}" '
            f'data-state="{entry["state"]}" '
            f'data-group="{GROUP_OF[entry["state"]]}" data-foundation="{foundation_of(element)}" '
            f'data-label="{element}">'
        )
        lines.append(render_preview(project_root, entry.get("preview"), element, txt))
        lines.append('<span class="dh-meta">')
        # Legacy rows carry scored=True from when an agent placeholder was
        # written as a score, so the marker keys off who ranked it, not off
        # the stale flag -- otherwise old agent rows still read as judged.
        unscored = "" if user_ranked else f' &middot; {txt["unscored"]}'
        # The state rides beside the id instead of trailing the block as a fifth
        # line of near-identical grey text.
        # The NAME leads and the id becomes a tag under it. A designer should
        # not have to read a namespace to learn what they are scoring.
        lines.append(f'<span class="dh-head"><span class="dh-id">'
                     f'{html_escape(names.get(element) or display_name(entry))}</span>'
                     f'<span class="dh-state">{html_escape(txt.get("state-" + str(entry["state"]), str(entry["state"])))}{unscored}</span></span>')
        what = str(entry.get("description") or "").strip()
        if what:
            lines.append(f'<span class="dh-desc">{what}</span>')
        lines.append("</span>")
        lines.append('<span class="dh-signals">')
        # Leads the strip. A bookmark is "keep this where I can find it", which
        # is a decision ABOUT the card rather than a judgement of it, so it sits
        # before the scale instead of trailing the verdict where it read as a
        # fifth opinion. The ribbon is clip-path on a box, not an emoji and not
        # hand-authored SVG -- `check_no_hand_authored_svg` refuses the latter,
        # and asset-sourcing.md allows a deterministic CSS primitive.
        bookmarked = bool(entry.get("bookmarked"))
        on = ' class="on"' if bookmarked else ""
        lines.append(f'<span data-bookmark role="button" tabindex="0" '
                     f'aria-pressed="{"true" if bookmarked else "false"}" '
                     f'aria-label="{txt["bookmark"]}: {element}" title="{txt["bookmark"]}"{on}>'
                     f'<i class="dh-ribbon" aria-hidden="true"></i></span>')
        stars_markup = "".join(
            f'<span data-rank="{n}" role="button" tabindex="0" '
            f'aria-label="{n} {txt["stars-of"]} {STAR_RANGE[1]}: {txt["execution-quality"]}"'
            + (' class="on"' if user_ranked and 0 < n <= stars else "")
            + ">&#9733;</span>"
            for n in range(STAR_RANGE[0], STAR_RANGE[1] + 1)
        )
        # The zero is a rank, so it rides the rank code path: it scores 0 and
        # touches nothing else. Emitted as `data-reset` it hit a companion
        # handler that also stripped the thumb and the tick -- a score silently
        # erasing two unrelated signals, which is the one thing the contract
        # says a score must never do.
        zero_on = ' class="on"' if user_ranked and stars == ZERO_STARS else ""
        lines.append(
            f'<span class="dh-zero"><span data-rank="0" role="button" tabindex="0" '
            f'title="{txt["zero-title"]}" '
            f'aria-label="{txt["zero-label"].format(element=element)}"{zero_on}>0</span></span>'
            # data-stars is mirrored onto the strip so the numeric readout can be
            # pure CSS (attr()) and still track a click: `paint` writes it here
            # as well as on the row.
            f'<span class="dh-stars" role="group" data-stars="{stars if user_ranked else 0}" '
            f'data-scored="{"yes" if user_ranked else "no"}" '
            f'aria-label="{txt["execution-of"]} {element}">'
            f'{stars_markup}</span>')
        mood = entry.get("sentiment")
        for name, glyph, label in (("like", "&#128077;", txt["like"]),
                                   ("dislike", "&#128078;", txt["dislike"])):
            on = ' class="on"' if mood == name else ""
            lines.append(f'<span data-sentiment="{name}" role="button" tabindex="0" '
                         f'aria-label="{label} {element}" title="{label}"{on}>{glyph}</span>')
        # A status, not a lock: "this one is done for now". Toggleable, and it never
        # freezes the element -- iteration continues after it is checked.
        done = entry["state"] in ("completed", "approved")
        on = ' class="on"' if done else ""
        lines.append(f'<span data-verdict="completed" role="button" tabindex="0" '
                     f'aria-pressed="{"true" if done else "false"}" '
                     f'aria-label="{txt["completed"]}: {element}" title="{txt["completed"]}"{on}>'
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


def companion_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "companion"


def read_board_url(project_root: Path) -> str | None:
    """The live companion URL, or None if this project has never started one."""
    root = project_root / ".superpowers" / "brainstorm"
    infos = list(root.glob("*/state/server-info")) if root.is_dir() else []
    if infos:
        newest = max(infos, key=lambda p: p.stat().st_mtime)
        try:
            url = json.loads(newest.read_text(encoding="utf-8")).get("url")
            if isinstance(url, str) and url.startswith("http"):
                return url
        except (ValueError, OSError, AttributeError):
            pass
    last, token = root / ".last-port", root / ".last-token"
    if last.is_file() and token.is_file():
        port = last.read_text(encoding="utf-8").strip()
        key = token.read_text(encoding="utf-8").strip()
        if port.isdigit() and key:
            return f"http://localhost:{port}/?key={key}"
    return None


def board_is_up(url: str) -> bool:
    parsed = urlparse(url)
    host, port = parsed.hostname, parsed.port
    if not host or not port:
        return False
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query
    try:
        conn = http.client.HTTPConnection(host, port, timeout=1.5)
        try:
            conn.request("GET", path)
            response = conn.getresponse()
            response.read()
            return response.status < 500
        finally:
            conn.close()
    except OSError:
        return False


def latest_screen(project_root: Path) -> Path | None:
    root = project_root / ".superpowers" / "brainstorm"
    htmls = list(root.glob("*/content/*.html")) if root.is_dir() else []
    return max(htmls, key=lambda p: p.stat().st_mtime) if htmls else None


def ensure_a_screen(project_root: Path) -> None:
    """If the live session has no HTML, copy the newest screen from an older one."""
    try:
        session = newest_session_dir(project_root)
    except HarnessError:
        return
    content = session / "content"
    if any(content.glob("*.html")):
        return
    source = latest_screen(project_root)
    if source is not None:
        publish_screen(project_root, source)


def start_companion(project_root: Path) -> str:
    script = companion_dir() / "start-server.sh"
    if not script.is_file():
        raise HarnessError("companion/start-server.sh missing; run companion/install.sh")
    proc = subprocess.run(
        [str(script), "--project-dir", str(project_root.resolve()), "--background"],
        capture_output=True, text=True, timeout=25,
        cwd=str(companion_dir()),
    )
    text = f"{proc.stdout or ''}\n{proc.stderr or ''}"
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            data = json.loads(line)
        except ValueError:
            continue
        if isinstance(data.get("url"), str):
            return data["url"]
        if data.get("error"):
            raise HarnessError(str(data["error"]))
    url = read_board_url(project_root)
    if url and board_is_up(url):
        return url
    raise HarnessError((proc.stderr or proc.stdout or "companion did not start").strip())


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


ARTICLE_STYLE = _screen("article.css")


# Stroke icon, not an emoji: emoji ignore `color`, so a bin glyph could never
# take the bar's ink or invert with the active pill.
# The round's own mark: a target, because the round is the one thing being aimed
# at. Stroke, not emoji -- emoji ignore `color` and cannot invert with the zone.
ROUND_ICON = ('<svg class="dh-round-icon" viewBox="0 0 24 24" fill="none" '
              'stroke="currentColor" stroke-width="1.6" aria-hidden="true">'
              '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4.5"/>'
              '<circle cx="12" cy="12" r="1" fill="currentColor"/></svg>')

def _round_icon(path: str) -> str:
    return ('<svg class="dh-round-icon" viewBox="0 0 24 24" fill="none" '
            'stroke="currentColor" stroke-width="1.6" aria-hidden="true">' + path + '</svg>')

ROUND_ICONS = {
    "core": ROUND_ICON,
    "palette": _round_icon('<rect x="4" y="4" width="7" height="7" rx="1"/>'
                           '<rect x="13" y="4" width="7" height="7" rx="1"/>'
                           '<rect x="4" y="13" width="7" height="7" rx="1"/>'
                           '<rect x="13" y="13" width="7" height="7" rx="1"/>'),
    "typography": _round_icon('<path d="M6 18V6h4l4 8 4-8h4v12"/>'),
    "illustration": _round_icon('<path d="M4 20l5-7 4 5 3-4 4 6"/>'
                                '<circle cx="9" cy="8" r="2"/>'),
    "composition": _round_icon('<rect x="4" y="4" width="16" height="16" rx="1"/>'
                               '<path d="M4 10h16M10 4v16"/>'),
    "voice": _round_icon('<path d="M5 8h14M5 12h10M5 16h12"/>'),
    "motion": _round_icon('<path d="M5 12h3l2-4 2 8 2-5 3 1"/>'),
}

TRASH_ICON = ('<svg class="dh-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
              'stroke-width="2" stroke-linecap="round" aria-hidden="true">'
              '<path d="M3 6h18M8 6V4h8v2M6 6l1 14h10l1-14M10 11v6M14 11v6"/></svg>')

TOC_SCRIPT = _screen("toc.js")


# The slideshow. A 96px thumbnail is a reminder of a drawing, not a view of
# one -- so the page was asking for a judgement it never showed enough to make.
#
# The strip here holds NO state of its own. Every control is a proxy: it finds
# the element's real row and clicks its real control, so the ledger keeps one
# write path and the companion's own rehydrator stays the only thing that
# decides what a click means. Duplicating that logic per language is exactly
# how the JS and Python rules drifted apart before.
SHOT_FIT_SCRIPT = _screen("shot-fit.js")

LIGHTBOX_SCRIPT = _screen("lightbox.js")


def _specimens(entries: list[dict[str, object]], txt: dict[str, str],
               rows: dict[str, str] | None = None) -> str:
    """Show the material itself: the colours, the faces. Rendered from tokens the
    project recorded, so the harness invents no value it was not given."""
    colors, fonts = [], []
    for entry in entries:
        tokens = entry.get("tokens") or {}
        # Carry the OWNING element with each token: a token whose id is
        # just its owner's is not separately rankable, and pretending it is
        # was the whole of the palette defect.
        owner = str(entry["element"])
        colors += [(owner, c) for c in (tokens.get("colors") or [])]
        fonts += [(owner, f) for f in (tokens.get("fonts") or [])]
    rows = rows or {}

    def scoreable(token: dict[str, object], owner: str = "",
                  is_set_header: bool = False) -> str:
        """A specimen the user cannot rank is a picture of a decision.

        Point a token at an element id and its own controls ride beside it, so
        a family, a pairing and a single weight are each ranked where they are
        read -- rather than as a dotted id in a list somewhere below.
        """
        linked = str(token.get("element") or "").strip()
        if linked not in rows:
            return ""
        # A control on a set HEADER ranks the set, which is what it looks
        # like. The same control hung on ONE MEMBER of a set claims to rank
        # that member -- so a palette whose first colour happened to carry
        # the family's id showed a star strip under `amarillo` and nothing
        # under `menta` or `rosa`, as if two thirds of the palette had
        # failed to render. A swatch earns controls by having its OWN id.
        if linked == owner and not is_set_header:
            return ""
        row = rows[linked]
        # Only the controls. The full row keeps the id, the state and the
        # evidence further down; repeating all that beside a specimen that
        # already shows the thing would say everything twice. The graphic in
        # particular carries an inline `display:block`, which no class rule of
        # ours can override -- so it is never emitted here rather than hidden.
        head = re.match(r'<div class="dh-fb"[^>]*>', row)
        start = row.find('<span class="dh-signals">')
        if not head or start < 0:
            return ""
        # To the END of the signals block, not the first `</span>` inside it --
        # a non-greedy match here emitted the zero control alone, a 44px stub
        # where the whole strip belonged. The row closes with the signals span
        # followed by its own </div>.
        body = row[start:].rsplit("</div>", 1)[0].rstrip()
        return '<div class="dh-spec-score">' + head.group(0) + body + "</div></div>"

    out = []
    if colors:
        items = "".join(
            f'<li><span class="dh-chip" style="background:{html_escape(str(c["value"]))}"></span>'
            f'<span class="dh-vals"><b>{html_escape(str(c.get("name") or c["value"]))}</b>'
            f'<code>{html_escape(str(c["value"]))}</code>'
            + (f'<span>{html_escape(str(c["role"]))}</span>' if c.get("role") else "")
            + "</span>" + scoreable(c, owner) + "</li>"
            for owner, c in colors)
        out.append(f'<div class="dh-spec"><ul class="dh-swatches">{items}</ul></div>')
    if fonts:
        items = []
        for owner, f in fonts:
            stack = html_escape(str(f.get("stack") or "inherit"))
            # A family, then every weight it is actually used at, each labelled
            # with the job it does. One sample line and a name is a caption: it
            # cannot tell you which weight sets a heading and which sets a
            # caption, which is most of what a type system decides.
            variants = list(f.get("variants") or [])
            if not variants:
                variants = [{"use": f.get("use") or "", "sample": f.get("sample") or ""}]
            rows_out = []
            for v in variants:
                weight = str(v.get("weight") or "").strip()
                style = str(v.get("style") or "").strip()
                size = str(v.get("size") or "").strip()
                sample = html_escape(str(v.get("sample") or f.get("sample") or "Aa Bb Cc 0123"))
                css = f"font-family:{stack}"
                if weight:
                    css += f";font-weight:{html_escape(weight)}"
                if style:
                    css += f";font-style:{html_escape(style)}"
                if size:
                    css += f";font-size:{html_escape(size)}"
                spec = " · ".join(x for x in (weight, style, size) if x)
                rows_out.append(
                    f'<li><span class="dh-sample" style="{css}">{sample}</span>'
                    f'<span class="dh-var-meta">'
                    f'<b>{html_escape(str(v.get("use") or ""))}</b>'
                    + (f'<code>{html_escape(spec)}</code>' if spec else "")
                    + "</span>" + scoreable(v, owner) + "</li>")
            items.append(
                f'<li class="dh-face"><div class="dh-face-head">'
                f'<b>{html_escape(str(f["name"]))}</b>'
                f'<code>{stack}</code>'
                + (f'<span class="dh-face-use">{html_escape(str(f["use"]))}</span>'
                   if f.get("use") else "")
                + scoreable(f, owner, is_set_header=True)
                + f'</div><ul class="dh-variants">{"".join(rows_out)}</ul></li>')
        out.append(f'<div class="dh-spec"><ul class="dh-faces">{"".join(items)}</ul></div>')
    return "".join(out)


# The choices that ARE the direction. They belong together whatever their
# lifecycle state: a type system is judged as a system -- the pairings, the
# scale, the palette against the faces -- and scattering half of it into a
# backlog because it is still `proposed` makes that judgement impossible.
FUNDAMENTAL_FOUNDATIONS = ("core", "palette", "typography")


def zone_of(entry: dict[str, object], cohort: set[str]) -> str:
    """Four zones, and every element is in exactly one.

    A flat list of twenty-eight rows cannot say which are settled, which are
    being asked about now, and which were turned down -- so the user re-reads
    decisions they already made looking for the three that matter.
    """
    if entry["element"] in cohort:
        return "round"
    # A thumb up says the DIRECTION is right, so the element cannot be a wrong
    # direction -- whatever became of this particular drawing. Superseded work
    # that the user still likes is history, not an antipattern, and filing it
    # here told the next agent to stop pursuing an idea the user endorsed.
    if entry.get("sentiment") == "dislike":
        return "antipattern"
    if entry["state"] in ("rejected", "superseded"):
        return "backlog" if entry.get("sentiment") == "like" else "antipattern"
    if foundation_of(entry["element"]) in FUNDAMENTAL_FOUNDATIONS:
        return "fundamentals"
    return "backlog"


def incumbent_of(element: str, known: set[str]) -> str:
    """The element a proposal is competing with, read off its own id.

    `cover.ring.kicker.antetitulo-arco` is a new drawing of
    `cover.ring.kicker` -- the convention the skill already requires. Without
    showing that pair the user is asked to score a drawing against nothing:
    "is this good?" has no answer, where "is this better than what stands?"
    does. Longest matching prefix wins, so a third pass compares against the
    second rather than the original.
    """
    parts = element.split(".")
    for cut in range(len(parts) - 1, 0, -1):
        candidate = ".".join(parts[:cut])
        if candidate in known:
            return candidate
    return ""


def lineage_root_of(element: str, known: set[str]) -> str:
    """The original idea an element descends from, following incumbents up.

    `incumbent_of` answers one step -- what this drawing replaces. A third and
    fourth pass at the same idea form a chain, and the chart needs the whole
    chain to say "these five bars are five attempts at one thing" rather than
    five separate concerns.
    """
    seen = {element}
    current = element
    while True:
        parent = incumbent_of(current, known - {current})
        if not parent or parent in seen:
            return current
        seen.add(parent)
        current = parent


def parent_item_of(element: str) -> str:
    """The item a round's work sits under: the id's first dotted segment.

    `cover.layout.two-column` and `cover.ring.kicker` are both work on the
    cover. `type.heading.serif` is not -- it is a different parent item, and a
    round that proposes both is redesigning two things at once.
    """
    return element.split(".")[0]


def check_round_stays_in_scope(cohort: set[str]) -> None:
    """Refuse a round whose cohort spans more than one parent item.

    A round is one object being worked on. Left unenforced, an inference pass
    reads a whole ledger, reasons across every surface in it, and returns a
    thin proposal for each -- the expensive failure: a long run, wide reasoning
    and minimal drawings, because attention that should have gone into one
    cover went into six unrelated things.

    `check_cohort_size` caps how MANY elements a round may carry and says
    nothing about whether they belong together; the foundation-span check in
    `render_article` asks a related question but can be answered with `--asks`.
    Scope is not a prose problem, so this one has no escape hatch: a round that
    spans two parent items is two rounds.
    """
    if len(cohort) < 2:
        return
    by_item: dict[str, list[str]] = {}
    for element in sorted(cohort):
        by_item.setdefault(parent_item_of(element), []).append(element)
    if len(by_item) == 1:
        return
    spans = "; ".join(f"{item} ({', '.join(members)})"
                      for item, members in sorted(by_item.items()))
    raise HarnessError(
        f"this round spans {len(by_item)} parent items: {spans}. A round is one "
        "object -- a cover, a type system, an illustration set -- so proposing "
        "across two of them oversteps the one being judged and spends the run "
        "on breadth the user did not ask for. Split it into one round per "
        "parent item.")


MAX_VARIANTS_PER_IDEA = 3


def check_round_earns_its_place(decisions: dict[str, object], cohort: set[str]) -> None:
    """Refuse a round that sprays new ideas instead of improving ranked ones.

    `loop.md` says polish liked-but-low-scoring work first, and says it in
    prose, so every session drifted past it. The ledger shows what that cost:
    eighteen elements the user liked and scored 1-2 sat untouched while the
    agent proposed eleven fresh siblings, and the mean score FELL to 1.56. A
    thumb up on a two-star drawing is the clearest instruction the ledger can
    carry -- the idea is right, the drawing is not there yet -- and answering
    it with a brand-new idea throws the instruction away.

    Two refusals, both satisfiable by doing the right thing rather than by
    passing a flag:

    1. A round of nothing but new ids, while liked-and-low work is waiting.
       Redrawing one of them (`<parent>.<slug>`) satisfies this, because the
       redraw's incumbent is the element being polished.
    2. More than `MAX_VARIANTS_PER_IDEA` new drawings of the SAME incumbent
       in one round. Up to that many are allowed and render grouped
       together (see `render_article`'s idea-grouping) -- comparing 2-3
       genuine variants of one idea side by side is the whole point of a
       round. Past that cap it becomes the `anti-slop` wallpaper tell again:
       the user cannot usefully compare a wall of near-identical guesses,
       only pick the least-bad one.
    """
    live = [e for e in decisions["elements"] if e["state"] in ("approved", "proposed")]
    known = {e["element"] for e in decisions["elements"]}
    polish = {e["element"] for e in live
              if e.get("sentiment") == "like" and int(e.get("stars") or 0) <= 2}

    # A cohort member is "new" when the ledger has never seen it. Its incumbent
    # is the standing element it redraws, read off its own dotted id.
    incumbents = {c: incumbent_of(c, known - {c}) for c in cohort}
    # Counted against the LEDGER, not just against this cohort. Counting the
    # cohort alone let an idea accumulate variants one round at a time and
    # never trip the cap: two this round, two the next, and nothing ever saw
    # four at once. A real ledger reached seven live drawings under one
    # `family.tab` that way, which is the "too many for the same element"
    # scope failure -- the round was small every time, the family was not.
    live_ids = {e["element"] for e in live}
    standing = {}
    for inc in {i for i in incumbents.values() if i}:
        prefix = inc + "."
        standing[inc] = len([e for e in live_ids
                             if e.startswith(prefix) and e not in cohort])
    overrun = sorted(
        inc for inc in standing
        if standing[inc] + sum(1 for v in incumbents.values() if v == inc)
        > MAX_VARIANTS_PER_IDEA)
    if overrun:
        detail = ", ".join(
            f"{inc} ({standing[inc]} already standing "
            f"+ {sum(1 for v in incumbents.values() if v == inc)} proposed here)"
            for inc in overrun)
        raise HarnessError(
            "this round would leave more than " + str(MAX_VARIANTS_PER_IDEA)
            + " live drawings of one idea: " + detail
            + ". That stops being a choice and becomes wallpaper -- the user cannot "
            "usefully compare a wall of near-identical guesses. Supersede the ones this "
            "round replaces (`decide --supersedes`) instead of stacking another variant "
            "beside them, or ask about a different element.")

    # Asking about nothing is not a round proposing new ideas over unanswered
    # feedback; it is redrawing the page as it already stands. Refusing it left
    # no way to regenerate the article after a code change without inventing a
    # cohort, which is why a workaround snippet lived in ROADMAP.md.
    if not cohort or not polish:
        return
    touches_polish = any(c in polish or incumbents.get(c) in polish for c in cohort)
    if touches_polish:
        return
    waiting = sorted(polish)
    raise HarnessError(
        f"{len(waiting)} element(s) carry a thumb up and a low score -- the user said the idea is "
        "right and the drawing is not there yet -- and this round improves none of them:\n  "
        + "\n  ".join(waiting[:8])
        + (f"\n  ... and {len(waiting) - 8} more" if len(waiting) > 8 else "")
        + "\nRedraw one as `<that-id>.<slug>` so it is scored against what it replaces, or put the "
          "element itself in the cohort to re-ask. New ideas proposed over unanswered feedback are "
          "why the ledger is growing and the scores are not.")


def check_unique_cohort_previews(decisions: dict[str, object], cohort: set[str]) -> None:
    """A copied drawing with a new id is not another proposal."""
    seen: dict[str, str] = {}
    duplicates: list[tuple[str, str]] = []
    for entry in decisions["elements"]:
        element = str(entry["element"])
        if element not in cohort:
            continue
        preview = entry.get("preview") or {}
        digest = str(preview.get("sha256") or "")
        if not digest:
            continue
        if digest in seen:
            duplicates.append((seen[digest], element))
        else:
            seen[digest] = element
    if duplicates:
        pairs = ", ".join(f"{first} / {second}" for first, second in duplicates)
        raise HarnessError(
            "this round presents the same drawing under different names: " + pairs +
            ". Keep one proposal or draw a materially different alternative.")


ZONES = ("round", "fundamentals", "backlog", "antipattern")
# Only the backlog earns a second level of navigation: it is the long one, and
# the reader arrives at it looking for a particular surface.
# Both long zones earn a second level. Only the backlog had one, so the
# critical components -- the section a designer scrolls hardest through --
# offered no way to reach a surface except by scrolling past every other one.
SUBNAV_ZONES = ("fundamentals", "backlog")
# The long zone folds. The round is the ask and must never be hidden; the
# fundamentals are the system on display; antipatterns are already quiet.
FOLDING_ZONES = ("fundamentals", "backlog", "antipattern")


def project_title(project_root: Path | None) -> str:
    if project_root is None:
        return ""
    path = project_root / "spec" / "design-harness" / "project.json"
    try:
        return str(json.loads(path.read_text(encoding="utf-8")).get("title") or "")
    except (OSError, ValueError):
        return ""


def render_article(project_root: Path, decisions: dict[str, object],
                   cohort: set[str] | None = None, *,
                   cohort_name: str = "", language: str | None = None,
                   title: str = "", asks: str = "",
                   agent_url: str = "", agent_name: str = "",
                   round_label: str = "", agent_working: bool = False) -> str:
    """A design-system article that is also the scoring companion.

    The strip alone answered "what is on the list". It could not answer "what is
    the typography doing", because a heading with one row under it is a list.
    Here each foundation shows its own material first -- the palette as colour,
    the faces as type -- and the scoring row sits against the thing it judges.
    """
    txt = strings_for(language or project_language(project_root))
    agent_url, raw_name = resolve_agent(agent_url, agent_name, project_root)
    agent_app, agent_model = agent_display_parts(raw_name, agent_url)
    agent_name = agent_display_line(raw_name, agent_url)
    cohort = cohort or set()
    check_asks(asks, cohort, language or project_language(project_root))
    check_cohort_size(cohort)
    check_round_stays_in_scope(cohort)
    check_unique_cohort_previews(decisions, cohort)
    # A cohort is one surface or one problem. Three elements drawn from three
    # different foundations, under a name that claims a shared surface, is a
    # batch of errands -- and the page cannot say what it is asking, so the
    # agent ends up explaining the round in prose the user never asked for.
    # Either the domain is evident from the ledger, or it has to be stated.
    #
    # `--asks` answers THIS check, which is about a round that needs explaining.
    # It does not answer `check_round_stays_in_scope` above, which is about a
    # round that should not exist as one round -- no sentence makes two parent
    # items into one object.
    domains = sorted({foundation_of(e) for e in cohort})
    if len(domains) > 2 and not asks.strip():
        raise HarnessError(
            "this cohort spans " + ", ".join(domains) + " -- that is a batch of errands, "
            "not a round. Narrow it to one surface or one problem, or say what they share "
            "with --asks \"<one sentence>\" so the screen can state it.")
    generated = render_feedback_controls(decisions, None, project_root, cohort, language)
    rows = extract_feedback_rows(generated)
    style = re.search(r"<style>/\* dh-controls \*/.*?</style>", generated, re.S)
    script = re.search(r"<script>/\* dh-rehydrate \*/.*?</script>", generated, re.S)
    live = [e for e in decisions["elements"] if e["state"] in GROUP_OF]
    bar_names = display_names(live)
    known_ids = {e["element"] for e in decisions["elements"]}
    stats = ledger_stats(decisions)

    def rank(entry: dict[str, object]) -> tuple:
        # Best execution on top, inside its own foundation. A user scanning for
        # what is working should not have to read every row to find it.
        return (FOUNDATION_ORDER.get(foundation_of(entry["element"]), len(FOUNDATION_ORDER)),
                -int(entry.get("stars") or 0), entry["element"])

    def bar_class(entry: dict[str, object]) -> str:
        # Solid green is reserved for finished work. A high score is not the
        # same claim -- it says this drawing is beautiful, not that the question
        # is closed -- so it reads as a faded green and the eye can still find
        # the handful of things actually done.
        # Turned-down work keeps a red, drained of its urgency: still legible
        # as "rejected", no longer shouting alongside a live 0-star problem.
        if zone_of(entry, cohort) == "antipattern":
            return "dh-tanti"
        if not entry.get("scored"):
            return "dh-tnone"
        if entry["state"] == "completed":
            return "dh-tdone"
        if int(entry.get("stars") or 0) >= 4:
            return "dh-thigh"
        return f'dh-t{entry["stars"]}'

    def bar(entry: dict[str, object], attempts: int = 1) -> str:
        stars = "--" if not entry.get("scored") else entry["stars"]
        asked = entry["element"] in cohort
        # The old tooltip read `family.tab.spine-step.grupo-color -- 1/5 --
        # proposed`: a namespace, a fraction and a lifecycle word. A designer
        # needs to see the DRAWING and its name. The bar now carries the id so
        # the script can build a real preview card, and a click opens the
        # slideshow rather than scrolling to a row.
        name = bar_names.get(entry["element"]) or display_name(entry)
        label = f'{name} — {stars}/{STAR_RANGE[1]}'
        if attempts > 1:
            label = f'{label} — {txt["bar-attempts"].format(count=attempts)}'
        if asked:
            label = f'{txt["zone-round"]}: {label}'
        return (f'<a class="{bar_class(entry)}" href="#dh-el-{html_escape(entry["element"])}"'
                f'{" data-asked=\"1\"" if asked else ""} '
                f'data-el="{html_escape(entry["element"])}" '
                f'data-name="{html_escape(name)}" '
                f'{f"data-variants=\"{attempts}\" " if attempts > 1 else ""}'
                f'data-score="{stars}" '
                # `aria-label`, never `title`: a `title` made the browser draw a
                # SECOND tooltip in the OS font, on top of the key row.
                f'aria-label="{html_escape(label)}">'
                f'<span>{"?" if asked else ""}</span></a>')

    def bar_order(entry: dict[str, object]) -> tuple:
        # Worst to best, with what was set aside after it. The round's own bars
        # stay where their score puts them -- they carry a ? and an outline, so
        # they are findable in place, and a bar's POSITION is what says how the
        # work compares. Hoisting them to the front threw that reading away.
        anti = 1 if zone_of(entry, cohort) == "antipattern" else 0
        return (anti, -int(entry.get("stars") or 0), entry["element"])

    # One bar per IDEA, not per attempt. Every redraw used to keep its own bar
    # forever -- a superseded drawing is still `live` for the strip's purposes
    # -- so the chart grew without bound and said "twenty-eight concerns" when
    # the truth was eight ideas, some of them drawn four times. The round zone
    # has grouped variants under their incumbent since it was written; this is
    # the same grouping, applied to the strip that summarises the whole ledger.
    lineages: dict[str, list[dict[str, object]]] = {}
    for entry in live:
        lineages.setdefault(lineage_root_of(entry["element"], known_ids), []).append(entry)

    def speaks_for(members: list[dict[str, object]]) -> dict[str, object]:
        # This round's ask speaks for its own lineage: it carries the `?` and
        # the outline, and hiding it behind an ancestor would make the one
        # thing being asked about the one thing the strip could not show.
        # Otherwise the standing drawing speaks, best execution first.
        return sorted(members, key=lambda e: (
            0 if e["element"] in cohort else 1,
            0 if e["state"] not in ("superseded", "rejected") else 1,
            -int(e.get("stars") or 0),
            e["element"]))[0]

    attempts: dict[str, int] = {}
    speakers: list[dict[str, object]] = []
    for members in lineages.values():
        speaker = speaks_for(members)
        attempts[speaker["element"]] = len(members)
        speakers.append(speaker)
    ordered_bars = sorted(speakers, key=bar_order)
    bars = "".join(bar(e, attempts.get(e["element"], 1)) for e in ordered_bars)
    asking = len([e for e in live if e["element"] in cohort])
    # Three figures the reader can act on, in the order they matter: what is
    # being asked now, what is still moving, and what is known to need another
    # pass. "Standing" and "you ranked" counted the archive instead -- both read
    # 32 of 32, which is true and tells nobody what to do next.
    # The three figures a designer can act on, matching the words under them.
    # "In better shape" is work they scored well; "need your direction" is work
    # waiting on THEM -- never scored, or liked but still weak. The old figures
    # counted the round and the archive, which told nobody what to do next.
    def user_stars(entry: dict[str, object]) -> int:
        return int(entry.get("stars") or 0) if entry.get("scored") else -1
    better = len([e for e in live if zone_of(e, cohort) != "antipattern"
                  and (user_stars(e) >= 3 or e["state"] in ("approved", "completed"))])
    ongoing = len([e for e in live if zone_of(e, cohort) != "antipattern"
                   and user_stars(e) < 3
                   and (not e.get("scored") or e["element"] in set(stats["needsPolish"]))])
    to_improve = len([e for e in live if zone_of(e, cohort) == "antipattern"])
    # A kebab-case cohort id set at 68px is a machine label wearing a headline's
    # clothes. The hero names the artefact being designed; the round is a line
    # underneath it, which is what it actually is.
    headline = html_escape(title or project_title(project_root) or txt["article-title"])
    agent_state = "active" if agent_working else "idle"
    designing_display = (round_label or cohort_name).strip()
    # The screen is a fragment, so its encoding rode entirely on whoever served
    # it. Opened from disk, or served by anything that omits the header, every
    # accent in a Spanish project rendered as mojibake. Declaring it here makes
    # the artifact say what it is wherever it ends up.
    out = ['<meta charset="utf-8">',
           ARTICLE_STYLE, style.group(0) if style else "", script.group(0) if script else "",
           TOC_SCRIPT, SHOT_FIT_SCRIPT, LIGHTBOX_SCRIPT,
           f'<div class="dh-art" data-saved="{html_escape(txt["saved"])}" '
           f'data-cheer-text="{html_escape(txt["done-cheer"])}" '
           f'data-done-label="{html_escape(txt["completed"])}" '
           f'data-agent-url="{html_escape(agent_url)}" '
           f'data-agent-state="{agent_state}" '
           f'data-lang="{html_escape((language or project_language(project_root)).lower())}" '
           f'data-agent-label="{html_escape(agent_name)}" '
           f'data-agent-app="{html_escape(agent_app)}" '
           f'data-agent-model="{html_escape(agent_model)}" '
           f'data-companion-kind="{html_escape(txt["companion-kind"])}">',
           '<header class="dh-hero">',
           # Read by a graphic designer, not by whoever built the harness: who
           # is asking, what this page is, which project, and what is on the
           # table right now -- in that order, before any number.
           f'<p class="dh-eyebrow">{html_escape(txt["brand"])}</p>',
           f'<h1>{html_escape(txt["article-title"])}</h1>',
           '<div class="dh-hero-meta">',
           f'<span class="dh-label">{html_escape(txt["project-label"])}</span>',
           f'<b class="dh-value">{headline}</b>',
           *([f'<span class="dh-label">{html_escape(txt["designing"])}</span>',
              f'<b class="dh-value">{html_escape(designing_display)}</b>']
             if designing_display else []),
           "</div>",
           f'<p class="dh-lede">{html_escape(txt["hero-lede"])}</p>',
           '<div class="dh-figures">',
           f'<div><b>{better}</b><span>{html_escape(txt["hero-asking"])}</span></div>',
           f'<div><b>{ongoing}</b><span>{html_escape(txt["hero-ongoing"])}</span></div>',
           f'<div><b>{to_improve}</b><span>{html_escape(txt["hero-improve"])}</span></div>',
           "</div>",
           "</header>"]
    # Keep the original article as the only presentation. The small workflow
    # module supplies durable project scope; it must never render a competing
    # website. A missing spec simply means this older project has no burndown.
    # `WorkflowError` subclasses ValueError, so the existing catch already
    # covers a corrupt spec on both.
    #
    # Built here, rendered under the round. The round is what the page is
    # asking for; a five-question form standing above it buried the ask behind
    # homework. Below it the reading order is what stands, rank it, then
    # sharpen the foundations if you want to.
    try:
        import brief_workflow
        brief_markup = brief_workflow.render_brief(project_root, txt)
    except (ImportError, OSError, ValueError):
        brief_markup = ""
    # Reference tags are the other half of what the user tells the agent, so
    # they render beside the brief rather than at opposite ends of the page.
    # Both stay quiet until they have something to ask about.
    try:
        import corpus_tags
        tags_markup = corpus_tags.render_corpus_tags(project_root, txt)
    except (ImportError, OSError, ValueError):
        tags_markup = ""
    try:
        import editorial_workflow
        burndown_markup = editorial_workflow.render_burndown(project_root)
    except (ImportError, OSError, ValueError):
        burndown_markup = ""
    if burndown_markup:
        out.append(burndown_markup)
    shown = [z for z in ZONES
             if z == "round" or any(zone_of(e, cohort) == z for e in live)]
    links = []
    for z in shown:
        tally = len([e for e in live if zone_of(e, cohort) == z])
        icon = TRASH_ICON if z == "antipattern" else ""
        # This round is the one thing being asked for, so it is the only link
        # that looks like a button. The rest are places to go.
        cta = ' data-cta="1"' if z == "round" else ""
        links.append(f'<li><a href="#dh-zone-{z}" data-zone="{z}"{cta}>{icon}'
                     f'{html_escape(txt[f"zone-{z}"])}<em>{tally}</em></a></li>')
    out.append('<nav class="dh-toc" aria-label="' + html_escape(txt["article-title"])
               + '"><p class="dh-toc-title">' + html_escape(txt["article-title"]) + "</p>"
               # Legend, then the chart it explains, then the sections it indexes.
               + '<p class="dh-key">'
               + f'<span><b>?</b>{html_escape(txt["key-asked"])}</span>'
               + '<span class="dh-key-good">'
               + f'<span><i class="dh-tdone"></i>{html_escape(txt["key-done"])}</span>'
               + f'<span><i class="dh-thigh"></i>{html_escape(txt["key-open"])}</span>'
               + "</span>"
               + '<span class="dh-key-bad">'
               + f'<span><i class="dh-t1"></i>{html_escape(txt["key-weak"])}</span>'
               + f'<span><i class="dh-tnone"></i>{html_escape(txt["key-unscored"])}</span>'
               + f'<span><i class="dh-tanti"></i>{html_escape(txt["key-anti"])}</span>'
               + "</span>"
               + "</p>"
               + f'<div class="dh-temp dh-temp-sticky" role="group" '
                 f'aria-label="{html_escape(txt["temp-alt"])}">{bars}</div>'
               + '<ol>' + "".join(links) + "</ol></nav>")
    for zone in ZONES:
        members = sorted((e for e in live if zone_of(e, cohort) == zone), key=rank)
        if not members and zone != "round":
            continue
        note = txt[f"zone-{zone}-note"]
        domain_line = ""
        if zone == "round":
            if asks.strip():
                note = asks.strip()
            topic = primary_foundation(cohort) if cohort else ""
            if topic:
                domain_line = ('<p class="dh-domain">'
                               f'<span>{html_escape(txt.get(topic, topic))}</span>'
                               "</p>")
        # The round is the only section that ASKS, so its own question is the
        # protagonist of the page -- set large and centred rather than filed as
        # a grey note under a heading, which is where nobody read it.
        heading = txt["round-heading"] if zone == "round" else txt[f"zone-{zone}"]
        note_markup = (f'<p class="dh-ask">{html_escape(note)}</p>'
                       if zone == "round"
                       else f'<p class="dh-note">{html_escape(note)}</p>')
        # The round tag names the OBJECT being judged, not a slug like `objeto`.
        tag = (html_escape(round_tag_label(cohort, decisions, cohort_name, round_label))
               if zone == "round" and cohort
               else (html_escape(cohort_name) if zone == "round" and cohort_name
                     else f'{len(members)} {html_escape(txt["designs"])}'))
        icon = (ROUND_ICONS.get(primary_foundation(cohort), ROUND_ICON)
                if zone == "round" and cohort else "")
        preparing = ' data-preparing="1"' if zone == "round" and agent_working else ""
        out += [f'<section class="dh-zone" id="dh-zone-{zone}" data-zone="{zone}"{preparing}>', "<header>",
                icon,
                f'<p class="dh-tag">{tag}</p>',
                f'<h2>{html_escape(heading)}</h2>',
                domain_line,
                note_markup, "</header>"]
        if zone == "round":
            out.append(f'<p class="dh-prep">{html_escape(txt["prep-legend"])}</p>')
        if not members:
            out.append(f'<p class="dh-empty">{html_escape(txt["empty-zone"])}</p>')
        # A second sticky level for the long zone: the reader arrives here
        # hunting a surface, and scrolling twenty rows to find it is the cost
        # the first bar was supposed to remove.
        if zone in SUBNAV_ZONES and members:
            order_seen: list[str] = []
            for entry in members:
                key = foundation_of(entry["element"])
                if key not in order_seen:
                    order_seen.append(key)
            # Three groups, not two. A second sticky bar over a short list is
            # noise -- that judgement stands -- but the critical components now
            # run to seventeen elements across five foundations, and a reader
            # hunting a surface there had no way to reach it except by scrolling
            # past every other one. The threshold is the length, not the zone.
            if len(order_seen) >= 3:
                out.append(
                    f'<nav class="dh-subnav" aria-label="{html_escape(txt["toc-jump"])}"><ol>'
                    + "".join(
                        f'<li><a href="#dh-{zone}-{key}" data-sub="{key}">{html_escape(txt.get(key, key))}'
                        f'<em>{len([e for e in members if foundation_of(e["element"]) == key])}</em>'
                        "</a></li>" for key in order_seen)
                    + "</ol></nav>")
        # Round-zone members that redraw the SAME incumbent render together
        # under one shared "before" instead of each getting its own
        # standalone before/after card. `check_round_earns_its_place` already
        # caps this at MAX_VARIANTS_PER_IDEA, so a group here is always small.
        incumbent_of_member: dict[str, str] = {}
        variant_count: dict[str, int] = {}
        grouped_already: set[str] = set()
        if zone == "round":
            for e in members:
                inc = incumbent_of(e["element"], known_ids)
                if inc and inc in rows:
                    incumbent_of_member[e["element"]] = inc
                    variant_count[inc] = variant_count.get(inc, 0) + 1
        seen_foundation = None
        for entry in members:
            key = foundation_of(entry["element"])
            if key != seen_foundation:
                if seen_foundation is not None and zone in FOLDING_ZONES:
                    out.append("</details>")
                seen_foundation = key
                same = [e for e in members if foundation_of(e["element"]) == key]
                heading = (f'{txt.get(key, key)}<span class="dh-count">{len(same)}</span>')
                if zone in FOLDING_ZONES:
                    # Folded, the group still shows its work: a strip of the
                    # graphics themselves. A collapsed section that shows only
                    # its own name asks the reader to open every one to find
                    # anything, which is worse than the scroll it replaced.
                    thumbs = "".join(
                        render_preview(project_root, e.get("preview"), e["element"], txt)
                        for e in same)
                    out.append(
                        f'<details class="dh-acc" data-group="{key}">'
                        f'<summary class="dh-group" id="dh-{zone}-{key}" data-group="{key}">'
                        f'{heading}<span class="dh-acc-thumbs">{thumbs}</span></summary>')
                else:
                    out.append(f'<h4 class="dh-group" id="dh-{zone}-{key}" data-group="{key}">'
                               f'{heading}</h4>')
                out.append(_specimens(same, txt, rows))
            if entry["element"] in grouped_already:
                continue
            row = rows.get(entry["element"], "")
            row = row.replace('<div class="dh-fb"',
                              f'<div id="dh-el-{entry["element"]}" class="dh-fb"', 1)
            if zone == "round":
                # Paired with what it replaces, or plainly marked as new. Either
                # way the user is never asked to rank a drawing against nothing.
                prior = incumbent_of_member.get(entry["element"], "")
                if prior and variant_count.get(prior, 0) >= 2:
                    # Two or more variants of the SAME idea: one shared
                    # "before", every variant beside it instead of each
                    # getting its own standalone before/after card.
                    variants = [e for e in members
                               if incumbent_of_member.get(e["element"]) == prior]
                    variant_markup = []
                    for variant in variants:
                        vrow = rows.get(variant["element"], "")
                        vrow = vrow.replace('<div class="dh-fb"',
                                            f'<div id="dh-el-{variant["element"]}" class="dh-fb"', 1)
                        suffix = variant["element"][len(prior) + 1:]
                        variant_markup.append(
                            '<div class="dh-idea-variant">'
                            f'<p class="dh-versus-label"><b class="dh-now">{html_escape(suffix)}</b></p>'
                            + vrow + "</div>")
                        grouped_already.add(variant["element"])
                    out.append(
                        '<div class="dh-idea-group">'
                        f'<p class="dh-versus-label"><b>{html_escape(txt["before"])}</b></p>'
                        + rows[prior].replace('<div class="dh-fb"',
                                              '<div class="dh-fb dh-fb-before"', 1)
                        + '<div class="dh-idea-variants">' + "".join(variant_markup) + "</div>"
                        + "</div>")
                    continue
                if prior:
                    out.append(
                        '<div class="dh-versus">'
                        f'<p class="dh-versus-label"><b>{html_escape(txt["before"])}</b></p>'
                        + rows[prior].replace('<div class="dh-fb"',
                                              '<div class="dh-fb dh-fb-before"', 1)
                        + f'<p class="dh-versus-label"><b class="dh-now">{html_escape(txt["after"])}</b></p>'
                        + row + "</div>")
                    continue
                out.append('<div class="dh-versus">'
                           f'<p class="dh-versus-label"><b class="dh-now">'
                           f'{html_escape(txt["brand-new"])}</b></p>' + row + "</div>")
                continue
            out.append(row)
        if seen_foundation is not None and zone in FOLDING_ZONES:
            out.append("</details>")
        out.append("</section>")
        if zone == "round":
            out.extend(m for m in (brief_markup, tags_markup) if m)
    out += [
        '<footer class="dh-credit">'
        f'<b>{html_escape(txt["credit-what"])}</b>'
        f'<span>{html_escape(txt["credit-who"])}</span>'
        "</footer>",
        "</div>",
    ]
    return "\n".join(part for part in out if part) + "\n"


def embed_controls(project_root: Path, screen: Path, theme: dict[str, str] | None = None,
                   pinned: set[str] | None = None, language: str | None = None) -> int:
    """Fill a screen's `data-dh-controls` placeholders with generated rows.

    Without this, an agent wanting scoring inside a prototype hand-writes the
    markup and silently drops the component graphic -- which is exactly what
    happened. The placeholder names the elements; the harness supplies the row.
    """
    project_root = project_root.resolve(strict=True)
    output = project_root / "spec" / "design-harness"
    html = screen.read_text(encoding="utf-8")
    language = language or project_language(project_root)
    txt = strings_for(language)
    generated = render_feedback_controls(load_decisions(output), theme, project_root,
                                         pinned, language)
    rows = extract_feedback_rows(generated)
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
    # A foundation heads its section once per screen, at its first appearance.
    # This screen carries sixteen placeholders, so heading each one in isolation
    # printed "Composition & layout" four times -- a repetition that reads as
    # noise rather than as a design system. Decided in document order here,
    # because the rewrite below has to run backwards.
    headed: set[str] = set()
    heads_at: dict[int, set[str]] = {}
    for position, (opening, _) in enumerate(placeholders):
        names = [e.strip() for e in opening.group(2).split(",") if e.strip()]
        fresh = {foundation_of(n) for n in names} - headed
        heads_at[position] = fresh
        headed |= fresh
    # Right to left so earlier offsets stay valid. Each placeholder's contents
    # are replaced wholesale, which is what makes embed safe to re-run.
    for position, (opening, close_end) in reversed(list(enumerate(placeholders))):
        wanted = [e.strip() for e in opening.group(2).split(",") if e.strip()]
        missing = [e for e in wanted if e not in rows]
        if missing:
            raise HarnessError("placeholder names element(s) not in standing: " + ", ".join(missing))
        # Group the placeholder's own elements by design-system foundation.
        # `embed` lifts bare rows out of the generated wrapper, so the headings
        # rendered there never reached an embedded screen -- the grouping
        # existed and was invisible on the only page the user actually scores.
        # Ordered by foundation, author's order kept inside each one.
        by_id = {e["element"]: e for e in load_decisions(output)["elements"]}
        buckets: dict[str, list[str]] = {}
        for name in wanted:
            buckets.setdefault(foundation_of(name), []).append(name)
        # Best execution on top within each foundation. The author's typing order
        # carried no information, so the strongest work could sit last and the
        # user had to read every row to find what was working.
        for names in buckets.values():
            names.sort(key=lambda n: (-int((by_id.get(n) or {}).get("stars") or 0), n))
        ordered = sorted(buckets.items(),
                         key=lambda kv: FOUNDATION_ORDER.get(kv[0], len(FOUNDATION_ORDER)))
        body = "\n".join(
            (f'<h4 class="dh-group" data-group="{key}">{txt.get(key, key)}'
             f'<span class="dh-count">{len(names)}</span></h4>\n'
             if key in heads_at[position] else "")
            + "\n".join(rows[e] for e in names)
            for key, names in ordered)
        # A round names its cohort so the user knows what is being asked and what
        # is deliberately out of scope. Read it off THIS div: an outer wrapper's
        # attributes never survive into the placeholder embed rewrites.
        attributes = opening.group(1) + opening.group(3)
        cohort = re.search(r'data-dh-cohort="([^"]*)"', attributes)
        if cohort and cohort.group(1).strip():
            banner = (f'<p class="dh-cohort"><b>{txt["this-round"]}</b>'
                      f'<span>{html_escape(cohort.group(1).strip())}</span>'
                      f'{len(wanted)} {txt["to-score"]}</p>\n')
            body = banner + body
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
        # The served session dir changes whenever the companion restarts, so
        # refusing here made a correct screen unpublishable and left the user
        # on a stale page. Move it instead -- which is what everyone did by
        # hand anyway. One fix here covers every caller that names a path.
        content.mkdir(parents=True, exist_ok=True)
        screen = Path(shutil.copy2(screen, content / screen.name))
    try:
        import corpus_tags
        corpus_tags.stage_corpus_thumbnails(project_root, content)
    except (ImportError, OSError):
        pass
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
    user = [e for e in live if e.get("source") == "user" and e.get("scored")]
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
        "unscored": sorted(e["element"] for e in live if not e.get("scored")),
        "conflicts": conflicts, "needsPolish": needs_polish,
    }


def init_harness(project_root: Path, source_root: Path, profiles: list[str],
                 language: str = DEFAULT_LANGUAGE) -> Path:
    project_root = project_root.resolve(strict=True)
    source_root = source_root.resolve(strict=True)
    if not project_root.is_dir() or not source_root.is_dir():
        raise HarnessError("project root and source root must be directories")
    output = project_root / "spec" / "design-harness"
    if is_within(output.resolve(), source_root):
        raise HarnessError("generated harness cannot live inside the read-only source root")
    if output.is_dir() and any(output.iterdir()):
        route = ("run text_to_graphics.py status" if
                 any((output / name).is_file() for name in
                     ("scene-spec.json", "graphics-manifest.json")) else
                 "continue the existing harness")
        raise HarnessError(f"design harness already exists; {route} instead of init")

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
        # UI locale only. Chat language comes from the user's words and the
        # project's published copy, never from this field.
        "language": language,
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
        s_adopt_states = '("approved", "rejected", "completed", "proposed")'
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
        if '.dh-fb[data-stars="0"][data-scored="yes"] .dh-zero' not in FEEDBACK_STYLE:
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
        # The emitted verdict word must be one `adopt` will fold back in. These
        # two drifted apart once already: the UI emitted `completed` while the
        # ledger reader accepted a different set, so the tick could be clicked
        # and never survived the round trip.
        for word in set(re.findall(r'data-verdict="([a-z]+)"', markup)):
            if word not in ("approved", "rejected", "completed"):
                raise HarnessError(
                    f"self-test: controls emit data-verdict=\"{word}\", which `adopt` "
                    "does not accept -- the tick would never reach the ledger")
        # And the toggle-off must survive too, or un-ticking silently reverts.
        if '"proposed"' not in s_adopt_states:
            raise HarnessError(
                "self-test: `adopt` drops the un-complete event -- a cleared tick comes back")
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
            raise HarnessError("self-test: rejected lifecycle group not marked on the row")
        # Headings group by design-system foundation, so the user reads the
        # typography together and the palette together. Lifecycle rides on the
        # row, which is what dims rejected work and drives the state chip.
        if 'class="dh-group" data-group="palette"' not in rejected_markup:
            raise HarnessError("self-test: rows are not grouped by design-system foundation")
        if strings_for("es")["palette"] in rejected_markup:
            raise HarnessError("self-test: default strip is not in the default language")
        spanish = render_feedback_controls(load_decisions(output), None, project, language="es")
        if strings_for("es")["palette"] not in spanish:
            raise HarnessError("self-test: --lang did not translate the group headings")
        if strings_for("en")["proposed-by"] in spanish:
            raise HarnessError("self-test: a translated strip still carries English row labels")
        for element_id, expected in (("palette.family-from-cards", "palette"),
                                     ("type.bracket-numerals", "typography"),
                                     ("cover.layout.two-column", "composition"),
                                     ("family.mark.dotmatrix", "illustration"),
                                     ("something.unmapped", "core")):
            if foundation_of(element_id) != expected:
                raise HarnessError(
                    f"self-test: {element_id} filed under {foundation_of(element_id)}, not {expected}")

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
        shot = shots / "cover.html"
        shot.write_text('<div style="width:85px;height:110px;background:#f9e7b5"></div>', encoding="utf-8")
        record_decision(project, "cover.layout.two-column", "approved", 5, "user: 'c2'", [],
                        preview_reference(project, "shots/cover.html"), source="user")
        validate_harness(project)
        with_shot = render_feedback_controls(load_decisions(output), None, project)
        if 'class="dh-shot"' not in with_shot or "#f9e7b5" not in with_shot:
            raise HarnessError("self-test: the ranked element carries no graphic")
        if "data-dh-no-graphic" not in render_feedback_controls(load_decisions(output), None, project):
            raise HarnessError("self-test: elements without a preview must say so, not fake one")
        if with_shot != render_feedback_controls(load_decisions(output), None, project):
            raise HarnessError("self-test: previews broke control determinism")
        # A regenerated preview is normal work: it must be reported, not blocked.
        shot.write_text('<div style="width:85px;height:110px;background:#000"></div>', encoding="utf-8")
        report = validate_harness(project)
        if not any("changed since it was ranked" in w for w in report["warnings"]):
            raise HarnessError("self-test: preview drift must be reported as a warning")
        record_decision(project, "cover.layout.two-column", "approved", 5, "user: 'c2'", [],
                        preview_reference(project, "shots/cover.html"), source="user")
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
        if ledger_now["agent.guess"]["stars"] != ZERO_STARS:
            raise HarnessError("self-test: agent proposals must store 0 stars until the user ranks")
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
    decide.add_argument("--preview", default="", help="project-relative graphic of the element being ranked")
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
                         help="the one design question this round asks. Required "
                              "when the cohort is set. Do not paste the zone note.")
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
                print(f"{len(hits)} recorded preview(s) hand-author <svg> -- redraw in HTML/CSS "
                     "and `shoot` + `decide --preview` again:")
                for hit in hits:
                    print(f"  {hit['element']}\t{hit['path']}")
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
            adopted, skipped = adopt_companion(args.project_root, args.companion_ledger)
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
