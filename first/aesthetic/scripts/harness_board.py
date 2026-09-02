#!/usr/bin/env python3
"""The companion's lifecycle: is it up, what is it serving, bring it up.

Reading the board URL, probing the socket, choosing the newest screen, starting
the process, and publishing a screen into the slot it serves. The seam is that
this is the only module that owns a running process and a port.
"""

from __future__ import annotations

import http.client
import json
import os
import time
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse

from harness_core import HarnessError, write_json


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
