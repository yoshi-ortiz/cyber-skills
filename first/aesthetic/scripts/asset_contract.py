from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping, Sequence


class AssetError(ValueError):
    pass


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AssetError(f"{label} must be non-empty text")
    return value.strip()


def validate_assets(raw: Any, corpus_ids: set[str],
                    project_root: Path | None = None) -> list[dict[str, Any]]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise AssetError("assets must be a list")
    result = []
    for index, item in enumerate(raw):
        if not isinstance(item, Mapping):
            raise AssetError(f"assets[{index}] must be an object")
        identifier = _text(item.get("id"), f"assets[{index}].id")
        provenance = _text(item.get("provenance"), f"{identifier}.provenance")
        if provenance == "generated-from-memory":
            raise AssetError("generated-from-memory vectors are forbidden")
        if provenance not in {"corpus", "project", "fetched", "procedural", "omitted"}:
            raise AssetError(f"{identifier} has unsupported provenance")
        value: dict[str, Any] = {"id": identifier, "provenance": provenance}
        if provenance == "corpus":
            corpus_item = _text(item.get("corpusItem"), f"{identifier}.corpusItem")
            if corpus_item not in corpus_ids:
                raise AssetError(f"{identifier} names an unknown corpus asset")
            value["corpusItem"] = corpus_item
        elif provenance == "omitted":
            value["reason"] = _text(item.get("reason"), f"{identifier}.reason")
        else:
            relative = _text(item.get("path"), f"{identifier}.path")
            digest = _text(item.get("sha256"), f"{identifier}.sha256").lower()
            if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
                raise AssetError(f"{identifier}.sha256 must be a SHA-256 digest")
            value.update({"path": relative, "sha256": digest})
            if provenance == "fetched":
                url = _text(item.get("sourceUrl"), f"{identifier}.sourceUrl")
                if not url.startswith("https://"):
                    raise AssetError(f"{identifier}.sourceUrl must use https")
                value.update({"sourceUrl": url,
                              "license": _text(item.get("license"), f"{identifier}.license"),
                              "version": _text(item.get("version"), f"{identifier}.version")})
            if provenance == "procedural":
                procedure = item.get("procedure")
                if not isinstance(procedure, Mapping):
                    raise AssetError(f"{identifier}.procedure must be an object")
                value["procedure"] = {
                    "algorithm": _text(procedure.get("algorithm"), f"{identifier}.algorithm"),
                    "seed": _text(str(procedure.get("seed", "")), f"{identifier}.seed"),
                    "parameters": procedure.get("parameters", {}),
                }
            if project_root is not None:
                root = Path(project_root).resolve()
                path = (root / relative).resolve()
                if root not in path.parents or not path.is_file():
                    raise AssetError(f"{identifier} asset file is missing or outside the project")
                if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                    raise AssetError(f"{identifier} asset hash does not match")
        result.append(value)
    if len({item["id"] for item in result}) != len(result):
        raise AssetError("asset ids must be unique")
    return result
