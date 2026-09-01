"""Every byte a Shot touches. Hashing, reading, and writing, and nothing else.

The observer decides; this module only moves bytes safely. An artifact is
hashed as bytes, never decoded, so a PNG or a video is as recordable as a
Markdown file.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

from shot_contract import Invalid, require_string, validate

INLINE_MAX = 65536
CHUNK = 1 << 16


def sha256_file(path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(CHUNK), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def load(path) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_shot(path) -> dict:
    return validate(load(path))


def on_disk_version(path) -> int:
    record = load(path)
    return record.get("version", 1) if isinstance(record, dict) else 1


def dump(record: dict) -> str:
    return json.dumps(record, indent=2, sort_keys=True) + "\n"


def create_shot(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "x", encoding="utf-8") as handle:
        handle.write(dump(record))


def replace_shot(path: Path, record: dict) -> None:
    handle, temporary = tempfile.mkstemp(dir=str(path.parent))
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(dump(record))
        os.replace(temporary, path)
    except BaseException:
        if os.path.exists(temporary):
            os.unlink(temporary)
        raise


def inline_output(text: str) -> tuple[dict, int]:
    size = len(text.encode("utf-8"))
    if size > INLINE_MAX:
        raise Invalid(f"$.output.inline: {size} bytes over the {INLINE_MAX} limit")
    return {"adapter": "text", "inline": {"text": text}}, size


def manifest_output(path) -> tuple[dict, int, list[dict]]:
    """`bytes` is the real file size and the digest is over the real bytes,
    streamed so a binary or oversized artifact is never decoded or held whole."""
    declared = load(path)
    if not isinstance(declared, dict):
        raise Invalid("$: manifest is not a JSON object")
    artifacts, digests, size = [], [], 0
    for index, item in enumerate(declared.get("artifacts") or []):
        at = f"$.output.artifacts[{index}]"
        if not isinstance(item, dict):
            raise Invalid(f"{at}: not a JSON object")
        source = Path(require_string(item.get("path"), f"{at}.path"))
        entry = {"role": item.get("role") or "deliverable", "path": str(source),
                 "bytes": source.stat().st_size}
        if item.get("mime"):
            entry["mime"] = item["mime"]
        entry["sha256"] = sha256_file(source)
        size += entry["bytes"]
        artifacts.append(entry)
        digests.append({"path": entry["path"], "sha256": entry["sha256"]})
    if not artifacts:
        raise Invalid("$.output.artifacts: expected a non-empty array")
    adapter = declared.get("adapter") or "file"
    return {"adapter": adapter, "artifacts": artifacts}, size, digests
