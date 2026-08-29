#!/usr/bin/env python3
"""Read one compiler trace beside an exact browser tokenization of it.

The trace is deterministic and standard library only. It counts under a byte
ratio, which is an estimate and says so. The only way to see what a target
model actually charges is to run that model's tokenizer, and the cheapest place
to run one is a browser: Transformers.js loads a tokenizer from a CDN with no
install, no Python dependency, and nothing vendored into this repository.

So the exact count lives here, in a page, and never in the compiler. Nothing on
this page changes a declaration, a budget, or an admission. It shows the
deterministic decision, the exact cost beside it, and every token tagged with
the priority of the chunk it came from. Reading it may change what a maintainer
declares next. Nothing here declares anything itself.

    python3 tools/trace_preview.py --project-root . --pass proposal \\
        --out /tmp/trace.html

This directory is fog on both channels, so the page ships nowhere.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "aesthetic" / "scripts"))

CDN = "https://cdn.jsdelivr.net/npm/@huggingface/transformers@4.2.0"
DEFAULT_TOKENIZER = "Xenova/gpt-4o"

INBOX = Path("spec/design-harness/context-tags-inbox.jsonl")

# Three signals, and none of them implies another. This is the same rule the
# companion contract puts on stars, thumbs, and the completed tick: a chunk can
# be expensive and essential, or cheap and a derail, and one score for all three
# would make those indistinguishable. One line per click, one signal per line.
SIGNALS = {
    "utility": ("essential", "useful", "wasted"),
    "group": ("Design-Inference", "Repo-Dev", "mixed"),
    "contamination": ("none", "possible", "derail"),
}

TEMPLATE = Path(__file__).resolve().parent / "trace_preview.html"


def page(trace: dict, texts: dict[str, str], tokenizer: str) -> str:
    """The trace and the text it admitted, as one self-contained page."""
    data = {"trace": trace, "texts": texts, "cdn": CDN, "tokenizer": tokenizer}
    # `</` inside a script element ends it, whatever the JSON says. Doctrine is
    # markdown written by people and will eventually contain one.
    blob = json.dumps(data, ensure_ascii=False, sort_keys=True).replace("</", "<\\/")
    return TEMPLATE.read_text(encoding="utf-8").replace("__DATA__", blob)


def build(project_root: Path, pass_name: str, tokenizer: str = DEFAULT_TOKENIZER,
          budget: int | None = None, proof: tuple[str, ...] = (),
          force: bool = False) -> str:
    import direction_context as dc

    trace = dc.compile_pass(project_root, pass_name, dc.DEFAULT_PROFILE,
                            budget, proof, force)
    texts = {chunk["key"]: chunk["text"]
             for chunk in dc.candidates(project_root)}
    return page(trace, texts, tokenizer)


def validate_tag(raw: object) -> dict:
    """One reviewed judgement, or the reason it is not one.

    The vocabulary lives here and nowhere else. Checking it in the page too
    would put the same rules in two languages and let them drift.
    """
    if not isinstance(raw, dict):
        raise ValueError("a tag must be an object")
    key = str(raw.get("key") or "").strip()
    signal = str(raw.get("signal") or "").strip()
    value = str(raw.get("value") or "").strip()
    if not key:
        raise ValueError("key is required")
    if signal not in SIGNALS:
        raise ValueError(f"signal must be one of {', '.join(sorted(SIGNALS))}")
    if value not in SIGNALS[signal]:
        raise ValueError(f"{signal} must be one of {', '.join(SIGNALS[signal])}")
    tag = {"at": str(raw.get("at") or "")[:40], "key": key[:200],
           "signal": signal, "value": value,
           "pass": str(raw.get("pass") or "")[:40],
           "tokenizer": str(raw.get("tokenizer") or "")[:120]}
    exact = raw.get("exactTokens")
    if isinstance(exact, int) and exact >= 0:
        tag["exactTokens"] = exact
    return tag


def append_tag(project_root: Path, tag: dict) -> Path:
    """Append one line. Never batched, never deduplicated: replay order is this
    file's job, and collapsing two clicks loses the fact that there were two."""
    path = Path(project_root) / INBOX
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(tag, ensure_ascii=False, sort_keys=True) + "\n")
    return path


def adopt(project_root: Path) -> dict[str, dict[str, str]]:
    """Where every chunk stands now: latest value per key and signal.

    Append-only history for audit, latest state for the next action. A refresh
    that showed the agent's last publish instead of what the user clicked is the
    failure the companion contract names, so the page reads this on load.
    """
    path = Path(project_root) / INBOX
    state: dict[str, dict[str, str]] = {}
    if not path.exists():
        return state
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            tag = validate_tag(json.loads(line))
        except (ValueError, json.JSONDecodeError):
            continue
        state.setdefault(tag["key"], {})[tag["signal"]] = tag["value"]
    return state


def review(trace: dict, state: dict[str, dict[str, str]]) -> str:
    """What the review says, as advice. Nothing here edits a declaration."""
    lines, wasted, derail = [], 0, []
    for chunk in trace["chunks"]:
        tags = state.get(chunk["key"], {})
        if not tags:
            continue
        marks = " ".join(f"{s}={tags[s]}" for s in sorted(tags))
        lines.append(f"  {chunk['key']:<44}{chunk['tokens']:>7}  {marks}")
        if tags.get("utility") == "wasted" and chunk["admitted"]:
            wasted += chunk["tokens"]
        if tags.get("contamination") == "derail":
            derail.append(chunk["key"])
    if not lines:
        return "No reviewed tags yet.\n"
    out = [f"{len(lines)} reviewed chunk(s) in {trace['pass']}", ""] + lines + [""]
    if wasted:
        out.append(f"{wasted} admitted tokens are tagged wasted. Reordering "
                   f"DOCTRINE_ORDER or lowering the budget would reclaim them.")
    if derail:
        out.append(f"tagged a contamination derail: {', '.join(derail)}. "
                   f"Consider whether the source belongs in this semantic context.")
    out.append("Advice only. Edit the declarations yourself; nothing here does.")
    return "\n".join(out) + "\n"


def serve(project_root: Path, html: str, port: int = 8931) -> None:
    """A companion surface for one maintainer, on loopback only."""
    from http.server import BaseHTTPRequestHandler, HTTPServer

    body = html.encode("utf-8")

    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: int, payload: bytes, kind: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def _same_origin(self) -> bool:
            # A page on any other site can POST to localhost. The companion
            # blocks that on its socket; this blocks it on the route.
            origin = self.headers.get("Origin")
            return origin in (None, f"http://127.0.0.1:{port}", f"http://localhost:{port}")

        def do_GET(self) -> None:
            if self.path.startswith("/tags"):
                self._send(200, json.dumps(adopt(project_root)).encode(),
                           "application/json; charset=utf-8")
            else:
                self._send(200, body, "text/html; charset=utf-8")

        def do_POST(self) -> None:
            if not self._same_origin():
                self._send(403, b'{"error":"cross-origin"}', "application/json")
                return
            length = int(self.headers.get("Content-Length") or 0)
            try:
                tag = validate_tag(json.loads(self.rfile.read(length) or b"{}"))
            except (ValueError, json.JSONDecodeError) as exc:
                self._send(400, json.dumps({"error": str(exc)}).encode(),
                           "application/json; charset=utf-8")
                return
            append_tag(project_root, tag)
            self._send(200, b'{"ok":true}', "application/json; charset=utf-8")

        def log_message(self, *args: object) -> None:
            pass

    server = HTTPServer(("127.0.0.1", port), Handler)
    print(f"http://127.0.0.1:{port}/\n"
          f"Every click appends one line to {INBOX}. Ctrl-C to stop, then\n"
          f"  python3 tools/trace_preview.py --project-root . --pass <pass> --review")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--pass", dest="pass_name", required=True)
    parser.add_argument("--out", type=Path, help="write the page and exit")
    parser.add_argument("--serve", action="store_true",
                        help="serve the page and collect reviewed tags")
    parser.add_argument("--port", type=int, default=8931)
    parser.add_argument("--review", action="store_true",
                        help="print what the reviewed tags say, and change nothing")
    parser.add_argument("--tokenizer", default=DEFAULT_TOKENIZER,
                        help=f"a Hugging Face tokenizer repo (default {DEFAULT_TOKENIZER})")
    parser.add_argument("--budget", type=int)
    parser.add_argument("--proof", action="append", default=[])
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    import direction_context as dc

    try:
        return run(parser, args, dc)
    except dc.DirectionContextError as refusal:
        print(refusal, file=sys.stderr)
        return 2


def run(parser, args, dc) -> int:
    if args.review:
        trace = dc.compile_pass(args.project_root, args.pass_name,
                                dc.DEFAULT_PROFILE, args.budget,
                                tuple(args.proof), args.force)
        print(review(trace, adopt(args.project_root)), end="")
        return 0

    html = build(args.project_root, args.pass_name, args.tokenizer,
                 args.budget, tuple(args.proof), args.force)
    if args.serve:
        serve(args.project_root, html, args.port)
        return 0
    if not args.out:
        parser.error("one of --out, --serve, or --review is required")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html, encoding="utf-8")
    print(f"{args.out}\n"
          f"Open it and press Count to tokenize with {args.tokenizer}. "
          f"Offline, the deterministic trace still reads in full.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
