#!/usr/bin/env python3
"""Which installed skills are actually this one's peers.

`tools/token_bench.py` measures a flow against a reference flow, and the
reference is authored by hand: someone decided `ask-matt` is the peer. This
derives the comparison set instead. Embed every installed `SKILL.md`, cluster
the vectors, and read the neighbours off the corpus.

Position and overlap only. A skill that clusters with nothing has no peer among
the skills installed; whether that is novelty or a diluted `SKILL.md` is a
judgement no clusterer can make, which is why nothing here writes a verdict.

    python3 scripts/vectors.py                       # print it
    python3 scripts/vectors.py --serve               # live dashboard, and open it
    python3 scripts/vectors.py --serve --min-cluster-size 3 --n-neighbors 10

Every EVoC parameter below is a flag, because the useful act is comparing two
settings rather than trusting one. The page carries the settings it was built
with, so a screenshot still says what produced it.

Third-party imports live here and nowhere else in this package. Create the
environment yourself; this installs nothing.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import webbrowser
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Callable

import numpy as np
from evoc import EVoC
from model2vec import StaticModel

TEMPLATE = Path(__file__).resolve().parent / "dashboard.html"

# Ours, from the repository's root CONTEXT.md table. Everything else is
# somebody else's work, which is the point of comparing against it.
LOCAL = ("aesthetic", "genesis", "knowledge", "ora", "silly", "kit",
         "starter-pack", "build-context-token-vectors")

# Display order for the rail. This annotates the corpus after clustering; it
# never feeds back into embeddings or EVoC.
RAIL = (
    ("first", ("first", "genesis", "aesthetic", "knowledge", "ask-matt",
               "prototype", "grill-me", "grill-with-docs", "grilling",
               "brainstorming", "context7-cli", "context7-mcp")),
    ("build", ("build", "build-context-token-vectors", "ponytail", "tdd",
               "code-review", "test-driven-development",
               "verification-before-completion", "semgrep")),
    ("land", ("land", "handoff", "claude-handoff")),
    ("check", ("check", "zoom-out", "graphify")),
    ("kit", ("kit", "starter-pack")),
    ("fix", ("fix", "diagnosing-bugs", "systematic-debugging", "poteto-mode")),
)
RAIL_PHASE = {name: phase for phase, names in RAIL for name in names}

# Declared, not defaulted. EVoC is stochastic, and a comparison set that
# changes between two runs cannot be compared against anything.
SEED = 42
DEFAULT_MODEL = "minishlab/potion-base-8M"

# EVoC's own defaults, restated so `--help` shows them and a changed value is
# visible as changed. Keys are the constructor's argument names.
TUNABLE = {
    "base_min_cluster_size": (int, 5, "points needed to form a cluster"),
    "n_neighbors": (int, 15, "neighbours in the kNN graph"),
    "min_samples": (int, 5, "samples for the density estimate"),
    "noise_level": (float, 0.5, "how readily a point is called noise"),
    "n_epochs": (int, 50, "node embedding optimization epochs"),
    "neighbor_scale": (float, 1.0, "scales the effective neighbour count"),
    "min_similarity_threshold": (float, 0.2, "Jaccard threshold between layers"),
}


@dataclass(frozen=True)
class PreparedCorpus:
    """Expensive, parameter-independent work shared by every tuning run."""

    root: Path
    model: str
    k: int
    names: list[str]
    texts: list[str]
    vectors: np.ndarray
    coords: np.ndarray
    similarity: np.ndarray


def body(text: str) -> str:
    """Frontmatter is metadata; doctrine is what a peer is judged on."""
    return re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.S).strip()


def load(root: Path) -> tuple[list[str], list[str]]:
    names, texts = [], []
    for path in sorted(root.glob("*/SKILL.md")):
        try:
            text = body(path.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
        if text:
            names.append(path.parent.name)
            texts.append(text)
    return names, texts


def embed(texts: list[str], model_name: str) -> np.ndarray:
    """L2-normalised, so a dot product is the cosine similarity."""
    vectors = np.asarray(StaticModel.from_pretrained(model_name).encode(texts),
                         dtype=np.float32)
    return vectors / (np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-12)


def project(vectors: np.ndarray) -> np.ndarray:
    """Two dimensions for a scatter plot, by PCA.

    A reading aid, never the result: clustering runs in full dimensionality,
    and two components of a 256-dimensional space discard most of what
    separated the clusters. Points that look adjacent here may not be, which is
    why every table carries the real numbers.
    """
    centred = vectors - vectors.mean(axis=0)
    coords = centred @ np.linalg.svd(centred, full_matrices=False)[2][:2].T
    span = coords.max(axis=0) - coords.min(axis=0)
    return (coords - coords.min(axis=0)) / np.where(span > 0, span, 1)


def layers(model: EVoC, fallback: np.ndarray) -> list[list[int]]:
    """Every resolution EVoC found, coarsest last.

    The hierarchy is the reason to use this clusterer rather than a flat one,
    so a page that shows only `labels_` is showing one slice of the answer.
    """
    found = [np.asarray(layer, dtype=int).tolist()
             for layer in getattr(model, "cluster_layers_", []) or []]
    return found or [np.asarray(fallback, dtype=int).tolist()]


def prepare(root: Path, model_name: str, k: int) -> PreparedCorpus:
    names, texts = load(root)
    if not names:
        raise SystemExit(f"no SKILL.md under {root}")
    vectors = embed(texts, model_name)
    coords = project(vectors)
    similarity = vectors @ vectors.T
    np.fill_diagonal(similarity, -1.0)
    return PreparedCorpus(root, model_name, k, names, texts, vectors, coords,
                          similarity)


def analyze(corpus: PreparedCorpus, params: dict) -> dict:
    """Fit only the tunable layer against one cached corpus."""
    names, texts = corpus.names, corpus.texts
    model = EVoC(random_state=SEED, **params).fit(corpus.vectors)

    strength = np.asarray(getattr(model, "membership_strengths_",
                                  np.ones(len(names))), dtype=float)
    every = layers(model, model.labels_)

    skills = []
    for i, name in enumerate(names):
        order = np.argsort(-corpus.similarity[i])[:corpus.k]
        skills.append({
            "name": name,
            "local": name in LOCAL,
            "phase": RAIL_PHASE.get(name),
            "layers": [layer[i] for layer in every],
            "strength": round(float(strength[i]), 3),
            "x": round(float(corpus.coords[i][0]), 4),
            "y": round(float(corpus.coords[i][1]), 4),
            "bytes": len(texts[i]),
            "peers": [{"name": names[j],
                       "sim": round(float(corpus.similarity[i][j]), 3),
                       "local": names[j] in LOCAL} for j in order],
        })

    persistence = np.asarray(getattr(model, "persistence_scores_", []), dtype=float)
    return {
        "skills": skills, "root": str(corpus.root), "model": corpus.model,
        "seed": SEED,
        "railOrder": [phase for phase, _ in RAIL],
        "params": params,
        "tunables": {name: {"type": kind.__name__, "default": default,
                             "help": help_text}
                     for name, (kind, default, help_text) in TUNABLE.items()},
        "persistence": [round(float(p), 3) for p in persistence.tolist()],
        "layerStats": [{"clusters": int(max(layer)) + 1,
                        "noise": int(sum(1 for c in layer if c < 0))}
                       for layer in every],
    }


def build(root: Path, model_name: str, k: int, params: dict) -> dict:
    """One-shot adapter retained for terminal and saved-page callers."""
    return analyze(prepare(root, model_name, k), params)


def page(data: dict) -> str:
    blob = json.dumps(data, ensure_ascii=False, sort_keys=True).replace("</", "<\\/")
    return TEMPLATE.read_text(encoding="utf-8").replace("__DATA__", blob)


def validate_params(raw: object) -> dict:
    """One JSON tuning request, normalized to EVoC's declared types."""
    if not isinstance(raw, dict):
        raise ValueError("parameters must be an object")
    unknown = sorted(set(raw) - set(TUNABLE))
    if unknown:
        raise ValueError(f"unknown parameter: {unknown[0]}")
    params = {}
    for name, value in raw.items():
        kind = TUNABLE[name][0]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{name} must be a number")
        if kind is int and not isinstance(value, int):
            raise ValueError(f"{name} must be an integer")
        value = kind(value)
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite")
        if name in {"base_min_cluster_size", "n_neighbors", "min_samples", "n_epochs"} \
                and value < 1:
            raise ValueError(f"{name} must be at least 1")
        if name == "neighbor_scale" and value <= 0:
            raise ValueError("neighbor_scale must be greater than 0")
        if name == "min_similarity_threshold" and not 0 <= value <= 1:
            raise ValueError("min_similarity_threshold must be between 0 and 1")
        params[name] = value
    return params


def companion(initial: dict, retune: Callable[[dict], dict],
              port: int = 8932) -> tuple[HTTPServer, str]:
    """Build the loopback adapter; the caller owns its process lifetime."""
    state = {"data": initial}
    server: HTTPServer

    class Handler(BaseHTTPRequestHandler):
        def send(self, code: int, payload: bytes, kind: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self) -> None:
            if self.path != "/":
                self.send(404, b'{"error":"not found"}', "application/json")
                return
            self.send(200, page(state["data"]).encode("utf-8"),
                      "text/html; charset=utf-8")

        def do_POST(self) -> None:
            if self.path != "/tune":
                self.send(404, b'{"error":"not found"}', "application/json")
                return
            origin = self.headers.get("Origin")
            allowed = {None, url.rstrip("/"),
                       url.replace("127.0.0.1", "localhost").rstrip("/")}
            if origin not in allowed:
                self.send(403, b'{"error":"cross-origin"}', "application/json")
                return
            if not self.headers.get("Content-Type", "").startswith("application/json"):
                self.send(415, b'{"error":"expected application/json"}',
                          "application/json")
                return
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                self.send(400, b'{"error":"invalid content length"}',
                          "application/json")
                return
            if length > 16_384:
                self.send(413, b'{"error":"request too large"}', "application/json")
                return
            try:
                params = validate_params(json.loads(self.rfile.read(length) or b"{}"))
                data = retune(params)
            except (ValueError, json.JSONDecodeError) as exc:
                payload = json.dumps({"error": str(exc)[:500]}).encode()
                self.send(400, payload, "application/json; charset=utf-8")
                return
            state["data"] = data
            payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/").encode()
            self.send(200, payload, "application/json; charset=utf-8")

        def log_message(self, *args: object) -> None:
            pass

    server = HTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{server.server_port}/"
    return server, url


def serve(initial: dict, retune: Callable[[dict], dict], port: int) -> None:
    server, url = companion(initial, retune, port)
    print(f"Live vector tuning at {url}\nCtrl-C to stop.")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        server.server_close()


def render(data: dict) -> str:
    top = data["layerStats"][-1]
    lines = [f"{len(data['skills'])} skills from {data['root']}",
             f"{len(data['layerStats'])} layer(s), coarsest {top['clusters']} "
             f"clusters and {top['noise']} noise, seed {data['seed']}",
             f"{data['model']}  {data['params'] or 'EVoC defaults'}", ""]
    rank = {phase: i for i, phase in enumerate(data["railOrder"])}
    ordered = sorted(data["skills"],
                     key=lambda skill: (rank.get(skill["phase"], len(rank)),
                                        skill["name"]))
    for skill in ordered:
        if not skill["local"]:
            continue
        cluster = skill["layers"][-1]
        tag = f"c{cluster}" if cluster >= 0 else "noise"
        phase = f"/{skill['phase']} " if skill["phase"] else ""
        lines.append(f"{phase}{skill['name']}  [{tag}]  strength {skill['strength']}")
        for peer in skill["peers"]:
            lines.append(f"   {peer['sim']:.3f} {'*' if peer['local'] else ' '} {peer['name']}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", type=Path, default=Path.home() / ".agents/skills")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("-k", type=int, default=8, help="neighbours to report")
    ap.add_argument("--out", type=Path, help="write the dashboard and exit")
    ap.add_argument("--serve", action="store_true",
                    help="serve a live tuning companion and open it")
    ap.add_argument("--port", type=int, default=8932,
                    help="loopback port for --serve (default 8932)")
    for name, (kind, default, help_text) in TUNABLE.items():
        ap.add_argument(f"--{name.replace('_', '-')}", dest=name, type=kind,
                        default=None, help=f"{help_text} (EVoC default {default})")
    args = ap.parse_args()

    # Only what the user actually set. Passing EVoC its own defaults back would
    # make every run look tuned and hide which knob was turned.
    params = {name: getattr(args, name) for name in TUNABLE
              if getattr(args, name) is not None}

    corpus = prepare(args.root.expanduser(), args.model, args.k)
    data = analyze(corpus, params)
    if args.serve:
        if args.out:
            args.out.write_text(page(data), encoding="utf-8")
        serve(data, lambda tuned: analyze(corpus, tuned), args.port)
        return 0
    if args.out is None:
        print(render(data))
        return 0
    args.out.write_text(page(data), encoding="utf-8")
    top = data["layerStats"][-1]
    print(f"{len(data['skills'])} skills, {len(data['layerStats'])} layer(s), "
          f"{top['clusters']} clusters, {top['noise']} noise -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
