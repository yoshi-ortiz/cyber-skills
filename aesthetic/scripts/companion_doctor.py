#!/usr/bin/env python3
"""Health-check the whole feedback path, end to end, in one command.

The feedback path is a six-link chain and every link fails silently. This
sends a real probe click through a real socket and confirms it lands in the
ledger. Anything less is narration.

Exit 0 only when a click would actually be recorded.
"""

from __future__ import annotations

import base64
import hashlib
import http.client
import json
import os
import re
import secrets
import socket
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bootstrap_harness import visible_controls  # noqa: E402  (sibling script)

PROBE = "__doctor_probe__"


def fail(msg: str) -> None:
    print(f"FAIL  {msg}")


def ok(msg: str) -> None:
    print(f"ok    {msg}")


def newest_session(project: Path) -> Path | None:
    root = project / ".superpowers" / "brainstorm"
    sessions = [d for d in root.glob("*/") if (d / "state" / "server-info").is_file()] if root.is_dir() else []
    return max(sessions, key=lambda d: d.stat().st_mtime, default=None)


def ws_send(host: str, port: int, key: str, payload: dict) -> bool:
    """Minimal RFC6455 client. Frames of any length, masked, one message."""
    nonce = base64.b64encode(secrets.token_bytes(16)).decode()
    req = (
        f"GET /?key={key} HTTP/1.1\r\nHost: {host}:{port}\r\n"
        f"Upgrade: websocket\r\nConnection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {nonce}\r\nSec-WebSocket-Version: 13\r\n"
        f"Cookie: brainstorm-key-{port}={key}\r\n\r\n"
    )
    with socket.create_connection((host, port), timeout=5) as sock:
        sock.sendall(req.encode())
        head = sock.recv(4096).decode("latin-1", "replace")
        if "101" not in head.split("\r\n")[0]:
            return False
        body = json.dumps(payload).encode()
        mask = secrets.token_bytes(4)
        n = len(body)
        if n < 126:
            frame = bytes([0x81, 0x80 | n])
        elif n < 65536:
            frame = bytes([0x81, 0x80 | 126]) + struct.pack(">H", n)
        else:
            frame = bytes([0x81, 0x80 | 127]) + struct.pack(">Q", n)
        sock.sendall(frame + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(body)))
        sock.settimeout(1.5)
        try:
            sock.recv(64)
        except OSError:
            pass
    return True


def main() -> int:
    project = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    session = newest_session(project)
    if session is None:
        fail("no companion session found; start the companion first")
        return 1
    info = json.loads((session / "state" / "server-info").read_text())
    host, port, key = "127.0.0.1", info["port"], info["url"].split("key=")[-1]
    bad = 0

    # 1 — is the server actually alive right now, not "alive when I last looked"
    try:
        conn = http.client.HTTPConnection(host, port, timeout=4)
        conn.request("GET", f"/?key={key}")
        boot = conn.getresponse()
        cookie = "; ".join(c.split(";")[0] for c in boot.getheader("set-cookie", "").split(", ") if c)
        boot.read()
        conn.close()
        ok(f"server answering on :{port}")
    except OSError as err:
        fail(f"server not answering on :{port} ({err.__class__.__name__}) -- restart it")
        return 1

    # 2 — what is the user actually looking at? newest mtime wins, always
    content = session / "content"
    screens = sorted(content.glob("*.html"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not screens:
        fail("no screens in the served session")
        return 1
    served = screens[0]
    ok(f"serving: {served.name}")
    if len(screens) > 1:
        runner_up = screens[1]
        gap = served.stat().st_mtime - runner_up.stat().st_mtime
        if gap < 2:
            fail(f"{runner_up.name} is within {gap:.1f}s of the served screen -- which one loads is a race")
            bad += 1

    # 3..5 — the served screen must actually be scoreable, with the graphic.
    # Fetch it over HTTP: the file on disk is not what the user gets. The server
    # injects helper.js and caches it at boot, so a correct file can still be
    # served with a stale helper that swallows every click.
    try:
        conn = http.client.HTTPConnection(host, port, timeout=4)
        conn.request("GET", "/", headers={"Cookie": cookie} if cookie else {})
        response = conn.getresponse()
        html = response.read().decode("utf-8", "replace")
        conn.close()
    except OSError as err:
        fail(f"could not fetch the served page ({err.__class__.__name__})")
        return 1
    if "data-dh-live" not in html:
        fail("served page carries a stale helper (no live flag) -- restart the companion "
             "so it re-reads helper.js, or clicks will be silently dropped")
        bad += 1
    else:
        ok("served page is wired (live flag injected)")
    if served.read_text(errors="replace").count("data-element=") > html.count("data-element="):
        fail(f"{served.name} on disk has more scoring rows than the served page -- stale route")
        bad += 1
    checks = {
        "scoring rows present (data-element)": "data-element=" in html,
        "star controls present (data-rank)": "data-rank=" in html,
        "completed toggle present (data-verdict)": "data-verdict=" in html,
        "component graphic present (dh-shot)": "dh-shot" in html,
    }
    for label, passed in checks.items():
        (ok if passed else fail)(label)
        bad += 0 if passed else 1
    # The checks above only prove the attributes reached the page. A control
    # whose glyph got absorbed into a malformed opening tag keeps every
    # attribute and still draws nothing, so parse the served page and require
    # the controls to carry visible content.
    for attribute, label in (("data-rank", "star"), ("data-reset", "reset"),
                             ("data-verdict", "completed")):
        shown = visible_controls(html, attribute)
        blank = sorted(key for key, text in shown.items() if not text.strip())
        if not shown:
            fail(f"{label} controls do not parse as elements on the served page")
            bad += 1
        elif blank:
            fail(f"{label} control(s) {blank} render blank -- attribute present, nothing drawn")
            bad += 1
        else:
            ok(f"{label} controls draw visible content ({len(shown)} on the page)")
    # Presence is not enough: every scoring row must carry its own graphic.
    # A hand-rolled row block passes a global "dh-shot appears somewhere" check
    # while showing the user nothing to judge.
    rows = html.count("data-element=")
    shots = html.count('class="dh-shot"')
    if rows and shots < rows:
        fail(f"{rows - shots} of {rows} scoring row(s) have no component graphic "
             f"-- regenerate with `controls`, never hand-roll rows")
        bad += 1
    else:
        ok(f"every scoring row carries its graphic ({rows} rows)")
    if "data-sentiment=" in html and "data-verdict=" not in html:
        fail("rows use the retired like/dislike vocabulary instead of approve/reject")
        bad += 1
    # Markup present is not markup visible. Every failure in this project's
    # history passed a string count while rendering nothing: a stylesheet that
    # never injected, a host rule with higher specificity, artwork scaled to a
    # corner. Sizing must ride on the element itself.
    sized = len(re.findall(r'class="dh-shot"[^>]*style="[^"]*inline-size', html))
    if rows and sized < rows:
        fail(f"{rows - sized} of {rows} graphic(s) rely on a stylesheet for their size -- "
             f"a host rule or a missing <style> makes them invisible. Re-run `embed`.")
        bad += 1
    else:
        ok("graphics carry their own sizing (cannot be collapsed by host CSS)")
    art = len(re.findall(r'class="dh-shot"[^>]*>\s*<svg', html))
    if rows and art < rows:
        fail(f"{rows - art} row(s) have a frame but no artwork inside it")
        bad += 1
    # Usable, not merely present. doctor was green five times on a UI the user
    # then rejected, because it only ever asked "does the markup exist".
    if 'min-inline-size:34px' not in html and "min-inline-size:38px" not in html:
        fail("controls declare no minimum hit target -- they will be hard to click")
        bad += 1
    else:
        ok("controls declare a usable hit target")
    if "data-reset" not in html:
        fail("no zero-star control -- the worst execution rating cannot be expressed")
        bad += 1
    if 'data-verdict="approved"' in html and 'data-verdict="completed"' not in html:
        fail("verdict control still says approved -- it is a completed status, not approval")
        bad += 1
    stale = [c for c in ('data-rank="0"',) if c in html]
    if stale:
        fail(f"screen carries retired controls ({', '.join(stale)}) -- re-run `embed`")
        bad += 1
    if 'class="dh-desc"' not in html and rows:
        fail("rows show ids with no description of what is being scored -- "
             "record --evidence and --implemented, then re-run `embed`")
        bad += 1
    else:
        ok("rows describe what is being scored")
    if "sin gr" in html:
        fail(f"{html.count('sin gr')} element(s) render with no graphic to judge")
        bad += 1

    # 6 — the only check that matters: does a real click reach the ledger?
    ledger = project / ".superpowers" / "brainstorm" / "decisions.jsonl"
    before = ledger.read_text().count("\n") if ledger.is_file() else 0
    sent = ws_send(host, port, key, {"type": "rank", "element": PROBE, "choice": PROBE, "stars": 3})
    if not sent:
        fail("websocket handshake rejected -- clicks cannot reach the ledger")
        return 1 if bad else 1
    after = ledger.read_text().count("\n") if ledger.is_file() else 0
    if after > before:
        ok("round trip: a click reaches the durable ledger")
        keep = [l for l in ledger.read_text().splitlines() if PROBE not in l]
        ledger.write_text("\n".join(keep) + ("\n" if keep else ""))
    else:
        fail("round trip: click did NOT reach the ledger -- feedback is being dropped")
        bad += 1

    print(f"\n{'FEEDBACK PATH BROKEN' if bad else 'feedback path healthy'} ({bad} problem(s))")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
