#!/usr/bin/env python3
"""What the user says their references are for.

`observe_corpus` records what a reference IS -- its bytes, its kind, its
hash. It cannot record what the reference is FOR, because intent is not
readable off a filename. That gap is what makes every round expensive: with
nothing declaring which references matter, `validate_art_direction` demands
an accounting for all of them, and a real 135-item corpus produced 8
observations and 127 boilerplate dismissals, rewritten every round before any
design thinking could start.

Tags are authored per FOLDER and stored per CONTENT HASH. The folder is the
unit the user already curated -- an inspiration directory arrives as
`strong color/`, `layout hierarchy/`, `pixel, ascii, compute/`, which is the
user having tagged their own corpus by hand before ever opening this tool.
Eight decisions, not a hundred and thirty-five. Storing the result against
each item's sha256 means renaming or reshuffling those folders later does not
orphan the work, because the hash follows the bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from html import escape as html_escape
from pathlib import Path
from typing import Any, Mapping

from editorial_workflow import (CORPUS_FILE, STORE, WorkflowError, _atomic_json,
                                _read_json, _text)

TAGS_FILE = "corpus-tags.json"
TAGS_INBOX_FILE = "corpus-tags-inbox.jsonl"
# Where the companion writes. Defaulted so SKILL.md spends one line, not two.
DEFAULT_INBOX = ".superpowers/brainstorm/" + TAGS_INBOX_FILE
MAX_NOTE_CHARS = 280

# The design-system foundations, from `bootstrap_harness.FOUNDATIONS`. Repeated
# rather than imported because bootstrap_harness imports THIS module to render
# the article, and a cycle for seven strings is a poor trade.
# `test_corpus_tags` asserts the two stay identical.
ASPECTS = ("core", "palette", "typography", "illustration",
           "composition", "voice", "motion")
ROLES = ("reference", "constraint", "attempt", "derivative")
STANCES = ("pursue", "refine", "avoid")
QUALITIES = ("finished", "sketch")

ROOT_GROUP = "(root)"


def group_of(path: str) -> str:
    """The folder a corpus item was filed under, which is its authored tag."""
    return path.rsplit("/", 1)[0] if "/" in path else ROOT_GROUP


def corpus_groups(corpus: Mapping[str, Any]) -> dict[str, list[str]]:
    """Every folder in the corpus, mapped to the hashes it holds."""
    groups: dict[str, list[str]] = {}
    for item in corpus.get("items") or []:
        if not isinstance(item, Mapping):
            continue
        digest = item.get("sha256")
        if not digest:
            continue
        groups.setdefault(group_of(str(item.get("path") or "")), []).append(str(digest))
    return groups


def _vocabulary(value: Any, allowed: tuple[str, ...], field: str) -> str:
    text = _text(value, field)
    if text not in allowed:
        raise WorkflowError(f"{field} must be one of {', '.join(allowed)}")
    return text


def validate_tags(raw: Any) -> dict[str, Any]:
    """Normalise the tag table, or say exactly which part of it is wrong.

    Closed vocabularies, checked here and nowhere else. The browser posts
    whatever it likes; this is the only thing that decides what a tag may say.
    """
    if not isinstance(raw, Mapping):
        raise WorkflowError("corpus tags must be an object")
    entries = raw.get("tags")
    if not isinstance(entries, Mapping):
        raise WorkflowError("corpus tags.tags must be an object keyed by sha256")
    tags: dict[str, Any] = {}
    for digest, entry in entries.items():
        if not isinstance(digest, str) or len(digest) != 64:
            raise WorkflowError(f"{digest!r} is not a sha256 digest")
        if not isinstance(entry, Mapping):
            raise WorkflowError(f"tags[{digest}] must be an object")
        aspects = entry.get("aspects")
        if not isinstance(aspects, list) or not aspects:
            raise WorkflowError(f"tags[{digest}].aspects must name at least one aspect")
        seen: list[str] = []
        for index, aspect in enumerate(aspects):
            value = _vocabulary(aspect, ASPECTS, f"tags[{digest}].aspects[{index}]")
            if value not in seen:
                seen.append(value)
        note = entry.get("note") or ""
        if not isinstance(note, str):
            raise WorkflowError(f"tags[{digest}].note must be text")
        if len(note) > MAX_NOTE_CHARS:
            raise WorkflowError(
                f"tags[{digest}].note is {len(note)} characters, over the "
                f"{MAX_NOTE_CHARS} limit. A tag is a label, not a critique.")
        role = _vocabulary(entry.get("role", "reference"), ROLES,
                           f"tags[{digest}].role")
        stance = _vocabulary(entry.get("stance"), STANCES,
                             f"tags[{digest}].stance")
        if stance == "refine" and role != "attempt":
            raise WorkflowError(f"tags[{digest}]: refine stance requires attempt role")
        if stance == "refine" and not note.strip():
            raise WorkflowError(f"tags[{digest}]: refine attempt requires a note")
        tags[digest] = {
            "aspects": seen,
            "role": role,
            "stance": stance,
            "quality": _vocabulary(entry.get("quality"), QUALITIES, f"tags[{digest}].quality"),
            "group": _text(entry.get("group"), f"tags[{digest}].group"),
            "note": note.strip(),
            "at": _text(entry.get("at"), f"tags[{digest}].at"),
        }
    return {"version": 1, "tags": tags}


def load_tags(project_root: Path) -> dict[str, Any]:
    """The tags as they stand. An absent file is an untagged project, not an
    error -- every reader here has to work before the user has tagged anything."""
    path = Path(project_root) / STORE / TAGS_FILE
    if not path.exists():
        return {"version": 1, "tags": {}}
    return validate_tags(_read_json(path))


def save_tags(project_root: Path, raw: Any) -> dict[str, Any]:
    value = validate_tags(raw)
    _atomic_json(Path(project_root) / STORE / TAGS_FILE, value)
    return value


def load_corpus(project_root: Path) -> dict[str, Any]:
    path = Path(project_root) / STORE / CORPUS_FILE
    if not path.exists():
        raise WorkflowError(f"this project has no {CORPUS_FILE}; run `observe` first")
    return _read_json(path)


def tag_group(project_root: Path, event: Mapping[str, Any]) -> int:
    """Apply one folder's tag to every item in it. Returns items tagged.

    Last write wins, so re-tagging a folder is how the user changes their mind
    and re-adopting an inbox in order lands on the same state either way. That
    is the whole idempotency story.

    ponytail: no tag history is kept, only current state. Add an append-only
    event log beside this if a tag ever needs auditing, the way
    `editorial-events.jsonl` does it for scope.
    """
    root = Path(project_root)
    groups = corpus_groups(load_corpus(root))
    name = _text(event.get("group"), "group")
    if name not in groups:
        raise WorkflowError(f"unknown corpus folder {name}")
    entry = {
        "aspects": event.get("aspects"), "role": event.get("role", "reference"),
        "stance": event.get("stance"),
        "quality": event.get("quality"), "group": name,
        "note": event.get("note") or "", "at": _text(event.get("at"), "at"),
    }
    current = load_tags(root)
    for digest in groups[name]:
        current["tags"][digest] = entry
    save_tags(root, current)
    return len(groups[name])


def adopt_inbox(project_root: Path, inbox: Path) -> tuple[int, int]:
    """Fold browser-written tags in. The companion validates almost nothing and
    this owns the schema, exactly as `brief_workflow` does for the manifesto."""
    inbox = Path(inbox)
    if not inbox.exists():
        return (0, 0)
    adopted = skipped = 0
    for line in inbox.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
            tag_group(project_root, event)
            adopted += 1
        except (json.JSONDecodeError, WorkflowError, OSError):
            skipped += 1
    return (adopted, skipped)


def missing_evidence(corpus: Mapping[str, Any], tags: Mapping[str, Any],
                     seen: set[str]) -> list[str]:
    """What a direction spec has still not accounted for, given what it saw.

    The unit is the FOLDER, not the file, and that is the whole saving. The
    user grouped 32 references into `pixel, ascii, compute` and said what they
    are for; making the agent write 32 separate dismissals of that one
    statement is the ceremony this module exists to end. One observation
    anywhere inside a tagged folder accounts for the folder.

    Untagged projects keep the old contract exactly -- every item, by id --
    so nothing changes until the user opts in.
    """
    items = [i for i in (corpus.get("items") or []) if isinstance(i, Mapping)]
    tagged = tags.get("tags") or {}
    if not tagged:
        return sorted(str(i.get("id")) for i in items
                      if i.get("id") and str(i.get("id")) not in seen)
    covered: set[str] = set()
    folders: dict[str, list[str]] = {}
    for item in items:
        digest = str(item.get("sha256") or "")
        if digest not in tagged:
            continue
        name = group_of(str(item.get("path") or ""))
        folders.setdefault(name, [])
        if str(item.get("id")) in seen:
            covered.add(name)
    return sorted(name for name in folders if name not in covered)


def digest_rows(project_root: Path) -> list[dict[str, Any]]:
    """One row per aspect the user endorsed, plus what is left untagged.

    The key tokens a round reads instead of the raw corpus. Aggregated here
    rather than described in prose so the numbers cannot drift from the file.
    """
    corpus = load_corpus(project_root)
    tags = load_tags(project_root)["tags"]
    rows: dict[str, dict[str, int]] = {}
    for entry in tags.values():
        for aspect in entry["aspects"]:
            row = rows.setdefault(
                aspect, {"pursue": 0, "refine": 0, "avoid": 0, "sketch": 0})
            row[entry["stance"]] += 1
            if entry["quality"] == "sketch":
                row["sketch"] += 1
    ordered = [{"aspect": a, **rows[a]} for a in ASPECTS if a in rows]
    total = len([i for i in (corpus.get("items") or []) if isinstance(i, Mapping)])
    ordered.append({"aspect": "untagged", "pursue": 0, "refine": 0,
                    "avoid": 0, "sketch": 0,
                    "count": total - len(tags)})
    return ordered


def render_digest(rows: list[dict[str, Any]]) -> str:
    lines = []
    for row in rows:
        if row["aspect"] == "untagged":
            lines.append(f'{"untagged":<13}{row["count"]}')
            continue
        sketch = f' ({row["sketch"]} sketch)' if row["sketch"] else ""
        refine = f'   refine {row["refine"]}' if row["refine"] else ""
        avoid = f'   avoid {row["avoid"]}' if row["avoid"] else ""
        lines.append(
            f'{row["aspect"]:<13}pursue {row["pursue"]}{sketch}{refine}{avoid}')
    return "\n".join(lines) + "\n"


def untagged_groups(project_root: Path) -> list[tuple[str, int]]:
    """Folders with nothing tagged yet, largest first. The work that remains."""
    groups = corpus_groups(load_corpus(project_root))
    tagged = load_tags(project_root)["tags"]
    pending = [(name, len(digests)) for name, digests in groups.items()
               if not any(d in tagged for d in digests)]
    return sorted(pending, key=lambda pair: (-pair[1], pair[0]))


def representative_items(corpus: Mapping[str, Any], group: str,
                         limit: int = 3) -> list[Mapping[str, Any]]:
    """Deterministic first, middle, last image evidence for one folder."""
    items = sorted((item for item in (corpus.get("items") or [])
                    if isinstance(item, Mapping)
                    and item.get("kind") == "image"
                    and group_of(str(item.get("path") or "")) == group
                    and item.get("sha256") and item.get("inspectPath")),
                   key=lambda item: str(item.get("path") or ""))
    if len(items) <= limit:
        return items
    indexes = (0, len(items) // 2, len(items) - 1)
    return [items[index] for index in indexes[:limit]]


def thumbnail_name(item: Mapping[str, Any]) -> str:
    suffix = Path(str(item.get("path") or "")).suffix.lower()
    if suffix not in (".avif", ".gif", ".jpeg", ".jpg", ".png", ".webp"):
        suffix = ".img"
    return f'corpus-{str(item.get("sha256"))[:20]}{suffix}'


def stage_corpus_thumbnails(project_root: Path, content_dir: Path) -> list[Path]:
    """Copy verified representatives beside the served article, never the corpus."""
    try:
        corpus = load_corpus(project_root)
        pending = untagged_groups(project_root)
    except (OSError, WorkflowError):
        return []
    if not pending:
        return []
    content_dir.mkdir(parents=True, exist_ok=True)
    staged = []
    for item in representative_items(corpus, pending[0][0]):
        source = Path(str(item["inspectPath"]))
        try:
            if not source.is_file():
                continue
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            if digest != str(item["sha256"]):
                continue
            target = content_dir / thumbnail_name(item)
            shutil.copy2(source, target)
            staged.append(target)
        except OSError:
            continue
    return staged


TAGS_STYLE = """<style>/* dh-tags */
.dh-tags{margin:0 0 var(--s5);border:1px solid var(--dh-rule);border-radius:14px;
 padding:var(--s3) var(--s4)}
.dh-tags > summary{cursor:pointer;list-style:none;display:flex;align-items:baseline;
 gap:var(--s2);flex-wrap:wrap}
.dh-tags > summary::-webkit-details-marker{display:none}
.dh-tags > summary::before{content:"\\25b8";flex:none;font-size:13px;
 transition:transform .12s;color:color-mix(in srgb, currentColor 55%, transparent)}
.dh-tags[open] > summary::before{transform:rotate(90deg)}
.dh-tags > summary:focus-visible{outline:2px solid var(--dh-accent,#d9482a);outline-offset:3px}
.dh-tags-title{font-size:12px;font-weight:700;letter-spacing:.16em;text-transform:uppercase}
.dh-tags-count{font-size:11px;letter-spacing:0;
 color:color-mix(in srgb, var(--dh-ink,#111) 55%, transparent)}
.dh-tags-body{margin:var(--s3) 0 0;display:grid;gap:var(--s3);max-inline-size:68ch}
.dh-tags-asking{padding:var(--s3);border-radius:10px;
 background:color-mix(in srgb, var(--dh-ink,#111) 5%, transparent)}
.dh-tags-folder{margin:0;font-size:17px;line-height:1.45;font-weight:700}
.dh-tags-n{font-size:11px;
 color:color-mix(in srgb, var(--dh-ink,#111) 55%, transparent)}
.dh-tags-thumbs{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;
 margin-block-start:var(--s2)}
.dh-tags-thumb{display:block;inline-size:100%;aspect-ratio:4/3;object-fit:cover;
 border-radius:8px;border:1px solid var(--dh-rule);background:var(--dh-bg,#fff)}
.dh-tags-set{display:flex;flex-wrap:wrap;gap:6px;margin-block-start:var(--s2);border:0;padding:0}
.dh-tags-set legend{font-size:10px;font-weight:700;letter-spacing:.12em;
 text-transform:uppercase;padding:0;margin-block-end:5px}
.dh-tags-set label{display:inline-flex;align-items:center;gap:5px;font-size:12px;
 padding:5px 10px;border:1px solid var(--dh-rule);border-radius:999px;cursor:pointer}
.dh-tags-set label:has(:checked){background:var(--dh-ink,#111);color:var(--dh-bg,#fff);
 border-color:var(--dh-ink,#111)}
.dh-tags-set input{position:absolute;opacity:0;pointer-events:none}
.dh-tags-set label:has(:focus-visible){outline:2px solid var(--dh-accent,#d9482a);
 outline-offset:2px}
.dh-tags-note{font:inherit;font-size:12px;width:100%;box-sizing:border-box;
 padding:8px 10px;border:1px solid var(--dh-rule);border-radius:8px}
.dh-tags-actions{display:flex;align-items:center;gap:var(--s2);margin-block-start:var(--s3)}
.dh-tags-save{font:inherit;font-size:12px;font-weight:700;cursor:pointer;
 padding:9px 14px;border-radius:8px;border:1px solid var(--dh-ink,#111);
 background:var(--dh-ink,#111);color:var(--dh-bg,#fff)}
.dh-tags-save:hover{opacity:.85}
.dh-tags-save[disabled]{opacity:.45;cursor:default}
.dh-tags-digest{margin:0;font-size:12px;line-height:1.7;white-space:pre-wrap;
 font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
</style>"""


TAGS_SCRIPT = """<script>/* dh-tags */
(function(){
 if(window.__dhTags)return; window.__dhTags=1;
 document.addEventListener('click',function(e){
  var btn=e.target.closest?e.target.closest('[data-tags-save]'):null; if(!btn)return;
  var card=btn.closest('[data-tags-group]'); if(!card)return;
  var aspects=[].slice.call(card.querySelectorAll('[name=aspect]:checked'))
    .map(function(i){return i.value});
  if(!aspects.length)return;
  var one=function(n){var f=card.querySelector('[name='+n+']:checked');return f?f.value:''};
  btn.disabled=true;
  fetch('/corpus',{method:'POST',headers:{'Content-Type':'application/json'},
   body:JSON.stringify({group:card.getAttribute('data-tags-group'),aspects:aspects,
    role:one('role'),stance:one('stance'),quality:one('quality'),
    note:(card.querySelector('[name=note]')||{}).value||'',
    at:new Date().toISOString()})})
   .then(function(r){if(!r.ok)throw new Error('save failed');
    btn.textContent=btn.getAttribute('data-saved-label')||'Saved';})
   .catch(function(){btn.disabled=false});
 });
})();
</script>"""


def _chips(name: str, values: tuple[str, ...], legend: str,
           words: Mapping[str, str], multiple: bool, checked: str = "") -> str:
    kind = "checkbox" if multiple else "radio"
    # Aspects are the design-system foundations and already carry a translated
    # label under their bare key; stance and quality use a `tag-` prefix.
    boxes = "".join(
        f'<label><input type="{kind}" name="{name}" value="{html_escape(v)}"'
        f'{" checked" if v == checked else ""}>'
        f'{html_escape(words.get(v, words.get("tag-" + v, v)))}</label>' for v in values)
    return (f'<fieldset class="dh-tags-set"><legend>{html_escape(legend)}</legend>'
            f"{boxes}</fieldset>")


def render_corpus_tags(project_root: Path, txt: Mapping[str, str] | None = None) -> str:
    """One untagged folder at a time, plus the digest built so far.

    One at a time for the same reason the brief asks one question at a time:
    eight folders on screen at once is a form, and a form gets skimmed. A
    project with no corpus, or one already fully tagged, renders nothing.
    """
    try:
        pending = untagged_groups(project_root)
        rows = digest_rows(project_root)
    except (OSError, WorkflowError):
        return ""
    tagged_any = any(r["aspect"] != "untagged" for r in rows)
    if not pending and not tagged_any:
        return ""
    words = dict(txt or {})
    heading = words.get("tags-title", "Reference tags")
    counted = words.get("tags-count", "{left} folder(s) left").format(left=len(pending))
    body = []
    if tagged_any:
        body.append('<pre class="dh-tags-digest">'
                    + html_escape(render_digest(rows)) + "</pre>")
    if pending:
        name, count = pending[0]
        corpus = load_corpus(project_root)
        thumbs = "".join(
            f'<img class="dh-tags-thumb" src="/files/{html_escape(thumbnail_name(item))}" '
            f'alt="{html_escape(Path(str(item.get("path") or "reference")).name)}" '
            'loading="lazy" decoding="async">'
            for item in representative_items(corpus, name)
        )
        strip = f'<div class="dh-tags-thumbs">{thumbs}</div>' if thumbs else ""
        body.append(
            f'<div class="dh-tags-asking" data-tags-group="{html_escape(name)}">'
            f'<p class="dh-tags-folder">{html_escape(name)}'
            f' <span class="dh-tags-n">{count}</span></p>'
            + strip
            + _chips("aspect", ASPECTS, words.get("tags-aspects", "Useful for"),
                     words, True)
            + _chips("role", ROLES, words.get("tags-role", "Corpus role"),
                     words, False, ROLES[0])
            + _chips("stance", STANCES, words.get("tags-stance", "Stance"),
                     words, False, STANCES[0])
            + _chips("quality", QUALITIES, words.get("tags-quality", "Quality"),
                     words, False, QUALITIES[0])
            + f'<input class="dh-tags-note" name="note" maxlength="{MAX_NOTE_CHARS}" '
              f'placeholder="{html_escape(words.get("tags-note", "What to preserve or fix"))}">'
            + '<div class="dh-tags-actions">'
            f'<button type="button" class="dh-tags-save" data-tags-save'
            f' data-saved-label="{html_escape(words.get("tags-saved", "Saved"))}">'
            f'{html_escape(words.get("tags-save", "Save tag"))}</button></div></div>')
    state = " open" if pending and not tagged_any else ""
    return (TAGS_STYLE + TAGS_SCRIPT
            + f'<details class="dh-tags"{state}>'
            + f'<summary><span class="dh-tags-title">{html_escape(heading)}</span>'
            + f'<span class="dh-tags-count">{html_escape(counted)}</span></summary>'
            + f'<div class="dh-tags-body">{"".join(body)}</div></details>')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    tag = sub.add_parser("tag", help="tag one corpus folder")
    tag.add_argument("--project-root", required=True, type=Path)
    tag.add_argument("--group", required=True, help="folder as it appears in corpus.json")
    tag.add_argument("--aspects", required=True,
                     help="comma-separated, from " + ", ".join(ASPECTS))
    tag.add_argument("--role", default=ROLES[0], choices=ROLES)
    tag.add_argument("--stance", default=STANCES[0], choices=STANCES)
    tag.add_argument("--quality", default=QUALITIES[0], choices=QUALITIES)
    tag.add_argument("--note", default="")
    tag.add_argument("--at", required=True, help="ISO 8601 timestamp")
    adopt = sub.add_parser("adopt", help="fold browser-written tags in")
    adopt.add_argument("--project-root", required=True, type=Path)
    adopt.add_argument("--inbox", type=Path, default=None,
                       help="defaults to " + DEFAULT_INBOX)
    show = sub.add_parser("digest", help="print the key tokens for this corpus")
    show.add_argument("--project-root", required=True, type=Path)
    groups = sub.add_parser("groups", help="list corpus folders and what is untagged")
    groups.add_argument("--project-root", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.command == "tag":
            n = tag_group(args.project_root, {
                "group": args.group,
                "aspects": [a.strip() for a in args.aspects.split(",") if a.strip()],
                "role": args.role, "stance": args.stance, "quality": args.quality,
                "note": args.note, "at": args.at})
            print(f"Tagged {n} item(s) under {args.group}.")
        elif args.command == "adopt":
            inbox = args.inbox or (args.project_root / DEFAULT_INBOX)
            adopted, skipped = adopt_inbox(args.project_root, inbox)
            print(f"Adopted {adopted} tag(s); skipped {skipped} unusable line(s).")
            # The digest is the reason to run adopt at all, so print it here
            # rather than making SKILL.md spend a second command on it.
            sys.stdout.write(render_digest(digest_rows(args.project_root)))
        elif args.command == "digest":
            sys.stdout.write(render_digest(digest_rows(args.project_root)))
        elif args.command == "groups":
            for name, count in untagged_groups(args.project_root):
                print(f"{count:5d}  {name}")
    except (WorkflowError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
