#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import re
import tempfile
from html import escape as html_escape
from pathlib import Path
from typing import Any, Mapping, Sequence

from asset_contract import AssetError, validate_assets
from burndown_view import BURNDOWN_STYLE
from direction_context import load_decisions, validate_brief_constraints
from harness_store import (
    ART_DIRECTION_FILE, CORPUS_FILE, DECISIONS_FILE, EDITORIAL_FILE, EVENTS_FILE,
    KNOWN_BASES, STORE, THEME_FILE, VAGUE_LABEL, WorkflowError,
    _atomic_json, _atomic_text, _read_json, _text,
)
from art_direction import (
    preference_brief, preference_state, save_art_direction, validate_art_direction,
)
from corpus_store import (
    IMAGE_SUFFIXES, TEXT_SUFFIXES, _kind, observe_corpus, seed_corpus, seed_corpus_value,
)
from editorial_scope import (
    EVENT_STATES, _validate_event, append_scope_event, editorial_burndown,
    load_scope_events, project_burndown, render_burndown, save_editorial_spec,
    validate_editorial_spec,
)
from theme_store import (
    DEFAULT_THEME, _rgb, _theme_spec, contrast, save_theme, selected_theme,
    set_follow_art_direction, validate_theme_elements,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    observe = commands.add_parser("observe")
    observe.add_argument("--project-root", type=Path, required=True)
    observe.add_argument("--source-root", type=Path, required=True)
    seed = commands.add_parser("seed")
    seed.add_argument("--project-root", type=Path, required=True)
    seed.add_argument("--profile", required=True)
    seed.add_argument("--subject", required=True)
    preferences = commands.add_parser("preferences")
    preferences.add_argument("--project-root", type=Path, required=True)
    preferences.add_argument("--out", type=Path)
    direction = commands.add_parser("direction")
    direction.add_argument("--project-root", type=Path, required=True)
    direction.add_argument("--spec", type=Path, required=True)
    scope = commands.add_parser("scope")
    scope.add_argument("--project-root", type=Path, required=True)
    scope.add_argument("--spec", type=Path, required=True)
    advance = commands.add_parser("advance")
    advance.add_argument("--project-root", type=Path, required=True)
    advance.add_argument("--event", type=Path, required=True)
    status = commands.add_parser("status")
    status.add_argument("--project-root", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "observe":
            result = observe_corpus(args.project_root, args.source_root)
        elif args.command == "seed":
            result = seed_corpus(args.project_root, args.profile, args.subject)
        elif args.command == "preferences":
            result = preference_brief(load_decisions(args.project_root))
            if args.out:
                _atomic_json(args.out, result)
        elif args.command == "direction":
            result = save_art_direction(args.project_root, _read_json(args.spec))
        elif args.command == "scope":
            result = save_editorial_spec(args.project_root, _read_json(args.spec))
        elif args.command == "advance":
            result = {"changed": append_scope_event(args.project_root, _read_json(args.event))}
        else:
            result = project_burndown(args.project_root) or {"points": []}
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    except WorkflowError as exc:
        _parser().error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
