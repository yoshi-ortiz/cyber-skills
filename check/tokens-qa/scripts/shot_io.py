"""Every byte a Shot touches. Hashing, reading, and writing, and nothing else.

The observer decides; this module only moves bytes safely. An artifact is
hashed as bytes, never decoded, so a PNG or a video is as recordable as a
Markdown file.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import fcntl
from contextlib import contextmanager
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
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w", encoding="utf-8") as handle:
        handle.write(dump(record))


@contextmanager
def locked(path: Path):
    """Serialize local evidence writers; atomic replacement keeps readers intact."""
    # ponytail: one local lock per evidence directory; split only after measured contention.
    if path.name == 'shots' and path.parent.name == '.audit':
        path = path.parent
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    with os.fdopen(os.open(path / '.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600), 'r+') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def revision(record: dict) -> str:
    return sha256_text(dump(record))


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


def contained(root: Path, path, where: str = "$") -> Path:
    root = root.resolve(strict=True)
    target = (root / path).resolve()
    if not target.is_relative_to(root):
        raise Invalid(f"{where}: path escapes project root")
    return target


def shot_paths(root: Path):
    directory = contained(root, ".audit/shots")
    if not directory.exists():
        return []
    return [contained(root, path) for path in sorted(directory.glob("*.json"))]


def deleted_shots(root: Path, item_id: str) -> list[dict]:
    directory = contained(root, '.audit/deleted')
    return [record for path in sorted(directory.glob('*.json'))
            if (record := load(contained(root, path))).get('item_id') == item_id]


def delete_shots(root: Path, paths: list[Path]):
    for path in paths:
        record = read_shot(path)
        tombstone = {'shot_id': record['shot_id'], 'item_id': record.get('item_id'), 'status': 'deleted'}
        target = contained(root, '.audit/deleted/' + hashlib.sha256(record['shot_id'].encode()).hexdigest() + '.json')
        if not target.exists():
            create_shot(target, tombstone)
        path.unlink()


def _committed_digest(root: Path, source: Path, wanted: str) -> bool:
    """Whether Git retains this exact historical artifact version."""
    relative = source.relative_to(root.resolve()).as_posix()
    commits = subprocess.run(
        ["git", "-C", str(root), "log", "--all", "--format=%H", "--", relative],
        capture_output=True, text=True, check=False,
    )
    if commits.returncode:
        return False
    for commit in commits.stdout.splitlines():
        blob = subprocess.run(
            ["git", "-C", str(root), "show", f"{commit}:{relative}"],
            capture_output=True, check=False,
        )
        if blob.returncode == 0 and "sha256:" + hashlib.sha256(blob.stdout).hexdigest() == wanted:
            return True
    return False


def verify_artifacts(record: dict, root: Path, allow_historical: bool = False) -> list[str]:
    failures = []
    for index, artifact in enumerate(record["output"].get("artifacts", [])):
        source = contained(root, artifact["path"], f"$.output.artifacts[{index}].path")
        wanted = artifact.get("sha256")
        if not source.is_file():
            if allow_historical and _committed_digest(root, source, wanted):
                continue
            failures.append(f'artifact[{index}]: missing proof or output')
            continue
        digest = sha256_file(source)
        if wanted != digest and not (allow_historical and _committed_digest(root, source, wanted)):
            failures.append(f"artifact[{index}]: hash mismatch or absent")
    return failures


def manifest_output(path, root: Path | None = None) -> tuple[dict, int, list[dict]]:
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
        if root is not None:
            source = contained(root, source, f"{at}.path")
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
