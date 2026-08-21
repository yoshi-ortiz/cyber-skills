#!/usr/bin/env python3
"""Verify the portable OKF reference bundle and its Golden Rule provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCES = ROOT / "references"
GOLDEN = {
    "graphic-design-fundamentals.md",
    "aesthetics-philosophy.md",
    "art-history.md",
}
CURRICULUM_ROLES = {"university curriculum", "art-institute curriculum"}
SUBSTANTIVE_ROLES = {
    "official standard",
    "university guidance",
    "scholarly reference",
    "museum chronology",
    "university course",
    "primary source",
}
RESERVED = {"index.md", "log.md"}
REQUIRED = {"type", "title", "description", "status", "generated"}
LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
CITE_RE = re.compile(r"\[\^([A-Za-z0-9._-]+)\](?!:)")
CITE_DEF_RE = re.compile(r"^\[\^([A-Za-z0-9._-]+)\]:", re.MULTILINE)


def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        return "", text
    end = text.find("\n---\n", 4)
    if end < 0:
        return "", text
    return text[4:end], text[end + 5 :]


def frontmatter_keys(frontmatter: str) -> set[str]:
    return {
        match.group(1)
        for line in frontmatter.splitlines()
        if (match := re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):(?:\s|$)", line))
    }


def parse_sources(frontmatter: str) -> list[dict[str, str]]:
    sources: list[dict[str, str]] = []
    in_sources = False
    current: dict[str, str] | None = None
    for line in frontmatter.splitlines():
        if line == "sources:":
            in_sources = True
            continue
        if in_sources and line and not line.startswith(" "):
            break
        if not in_sources:
            continue
        item = re.match(r"^  - ([a-z_]+):\s*(.+)$", line)
        field = re.match(r"^    ([a-z_]+):\s*(.+)$", line)
        if item:
            current = {item.group(1): item.group(2).strip(" '\"")}
            sources.append(current)
        elif field and current is not None:
            current[field.group(1)] = field.group(2).strip(" '\"")
    return sources


def markdown_files() -> list[Path]:
    return sorted(REFERENCES.glob("*.md"))


def validate_bundle(receipts: dict | None = None) -> list[str]:
    errors: list[str] = []
    index_text = (REFERENCES / "index.md").read_text()
    index_front, _ = split_frontmatter(index_text)
    if 'okf_version: "0.2"' not in index_front:
        errors.append("references/index.md must declare okf_version 0.2")

    indexed_targets = {target.split("#", 1)[0] for target in LINK_RE.findall(index_text)}
    concepts = {path.name for path in markdown_files() if path.name not in RESERVED}
    missing_index = sorted(concepts - indexed_targets)
    if missing_index:
        errors.append("unindexed concepts: " + ", ".join(missing_index))

    all_sources: dict[str, dict[str, str]] = {}
    for path in markdown_files():
        text = path.read_text()
        front, body = split_frontmatter(text)
        if path.name not in RESERVED:
            missing = REQUIRED - frontmatter_keys(front)
            if missing:
                errors.append(f"{path.name}: missing frontmatter {sorted(missing)}")
            generated = re.search(
                r"^generated:\n  by:\s*([^\n]+)\n  at:\s*([^\n]+)$",
                front,
                re.MULTILINE,
            )
            if not generated:
                errors.append(f"{path.name}: generated provenance must include by and at")
            else:
                actor, at = generated.groups()
                if "/" not in actor and not actor.startswith(("human:", "process:")):
                    errors.append(f"{path.name}: invalid generated actor {actor}")
                try:
                    datetime.fromisoformat(at)
                except ValueError:
                    errors.append(f"{path.name}: generated.at is not ISO 8601")
        for target in LINK_RE.findall(body):
            target = target.split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            if not (path.parent / target).resolve().exists():
                errors.append(f"{path.name}: broken link {target}")

        sources = parse_sources(front)
        for source in sources:
            if not source.get("resource"):
                errors.append(f"{path.name}: source entry missing required resource")
        if path.name in GOLDEN:
            roles = {source.get("academic_role", "") for source in sources}
            if not roles & CURRICULUM_ROLES:
                errors.append(f"{path.name}: missing university/art-institute curriculum evidence")
            if not roles & SUBSTANTIVE_ROLES:
                errors.append(f"{path.name}: missing substantive evidence")
            source_ids = {source.get("id", "") for source in sources}
            citations = set(CITE_RE.findall(body))
            definitions = set(CITE_DEF_RE.findall(body))
            if citations - source_ids:
                errors.append(f"{path.name}: citations without source metadata {sorted(citations - source_ids)}")
            if citations - definitions:
                errors.append(f"{path.name}: citations without definitions {sorted(citations - definitions)}")
            if source_ids - citations:
                errors.append(f"{path.name}: source metadata not cited {sorted(source_ids - citations)}")
        for source in sources:
            resource = source.get("resource", "")
            if resource.startswith("https://"):
                source_id = source.get("id", "")
                if source_id in all_sources and all_sources[source_id] != source:
                    errors.append(f"duplicate source id with different metadata: {source_id}")
                all_sources[source_id] = source

    leaks = re.compile(r"(?:Knowledge/|/Users/|~/.agents/)")
    for path in [*markdown_files(), ROOT / "AGENTS.md", ROOT / "agents" / "CONTEXT.md"]:
        if leaks.search(path.read_text()):
            errors.append(f"{path.relative_to(ROOT)}: personal or external knowledge path leak")

    if receipts is not None:
        received = receipts.get("sources", {})
        try:
            datetime.fromisoformat(receipts["checkedAt"])
        except (KeyError, TypeError, ValueError):
            errors.append("source receipt has no ISO 8601 checkedAt")
        for source_id, source in sorted(all_sources.items()):
            receipt = received.get(source_id)
            if not receipt:
                errors.append(f"missing source receipt: {source_id}")
                continue
            if receipt.get("resource") != source["resource"]:
                errors.append(f"stale source receipt locator: {source_id}")
            if not receipt.get("ok"):
                errors.append(f"failed source receipt: {source_id}")
            status = receipt.get("status")
            if not isinstance(status, int) or not 200 <= status < 400:
                errors.append(f"invalid source receipt status: {source_id}")
            if not receipt.get("contentType") or not receipt.get("sha256Prefix"):
                errors.append(f"incomplete source receipt evidence: {source_id}")
    return errors


def fetch_sources(timeout: float, max_sources: int) -> dict:
    sources: dict[str, dict[str, str]] = {}
    for path in sorted(REFERENCES / name for name in GOLDEN):
        front, _ = split_frontmatter(path.read_text())
        for source in parse_sources(front):
            if source.get("resource", "").startswith("https://"):
                sources[source["id"]] = source
    if len(sources) > max_sources:
        raise ValueError(f"refusing {len(sources)} requests; --max-sources is {max_sources}")

    results: dict[str, dict] = {}
    for source_id, source in sorted(sources.items()):
        request = urllib.request.Request(
            source["resource"],
            headers={"User-Agent": "aesthetic-reference-verifier/1.0"},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read(1_000_000)
                status = response.status
                results[source_id] = {
                    "resource": source["resource"],
                    "ok": 200 <= status < 400,
                    "status": status,
                    "finalUrl": response.url,
                    "contentType": response.headers.get_content_type(),
                    "sha256Prefix": hashlib.sha256(body).hexdigest()[:16],
                }
        except (urllib.error.URLError, TimeoutError) as exc:
            results[source_id] = {
                "resource": source["resource"],
                "ok": False,
                "error": str(exc),
            }
    return {
        "version": 1,
        "checkedAt": datetime.now(timezone.utc).isoformat(),
        "meaning": "Reachability receipt only; not a truth or quality certificate.",
        "sources": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--online", action="store_true", help="perform bounded source checks")
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--max-sources", type=int, default=8)
    parser.add_argument("--receipt", type=Path, default=REFERENCES / "source-receipts.json")
    args = parser.parse_args()

    if args.online:
        result = fetch_sources(args.timeout, args.max_sources)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if all(item["ok"] for item in result["sources"].values()) else 1

    receipts = json.loads(args.receipt.read_text()) if args.receipt.exists() else None
    errors = validate_bundle(receipts)
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors), file=sys.stderr)
        return 1
    print(f"OK: {len(markdown_files())} reference documents; OKF 0.2 and provenance checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
