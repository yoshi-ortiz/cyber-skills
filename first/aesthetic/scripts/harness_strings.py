#!/usr/bin/env python3
"""Every word the companion says, and the identity it says them as.

The scoring strip used to be Spanish literals with an English banner bolted on.
Keeping the copy in one table, keyed by the language `init` stored on the
project, is what lets a second project use the harness without editing it. The
agent identity lives here too because it is the one other thing a screen prints
that is neither ledger data nor markup.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from harness_core import write_json


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
