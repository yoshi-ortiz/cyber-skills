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
    python3 scripts/vectors.py --serve               # dashboard, and open it
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
import re
import webbrowser
from pathlib import Path

import numpy as np
from evoc import EVoC
from model2vec import StaticModel

TEMPLATE = Path(__file__).resolve().parent / "dashboard.html"

# Ours, from the repository's root CONTEXT.md table. Everything else is
# somebody else's work, which is the point of comparing against it.
LOCAL = ("aesthetic", "genesis", "knowledge", "ora", "silly", "kit",
         "starter-pack", "build-context-token-vectors")

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


def build(root: Path, model_name: str, k: int, params: dict) -> dict:
    names, texts = load(root)
    if not names:
        raise SystemExit(f"no SKILL.md under {root}")
    vectors = embed(texts, model_name)

    model = EVoC(random_state=SEED, **params).fit(vectors)
    coords = project(vectors)
    similarity = vectors @ vectors.T
    np.fill_diagonal(similarity, -1.0)

    strength = np.asarray(getattr(model, "membership_strengths_",
                                  np.ones(len(names))), dtype=float)
    every = layers(model, model.labels_)

    skills = []
    for i, name in enumerate(names):
        order = np.argsort(-similarity[i])[:k]
        skills.append({
            "name": name,
            "local": name in LOCAL,
            "layers": [layer[i] for layer in every],
            "strength": round(float(strength[i]), 3),
            "x": round(float(coords[i][0]), 4),
            "y": round(float(coords[i][1]), 4),
            "bytes": len(texts[i]),
            "peers": [{"name": names[j], "sim": round(float(similarity[i][j]), 3),
                       "local": names[j] in LOCAL} for j in order],
        })

    persistence = np.asarray(getattr(model, "persistence_scores_", []), dtype=float)
    return {
        "skills": skills, "root": str(root), "model": model_name, "seed": SEED,
        "params": params,
        "persistence": [round(float(p), 3) for p in persistence.tolist()],
        "layerStats": [{"clusters": int(max(layer)) + 1,
                        "noise": int(sum(1 for c in layer if c < 0))}
                       for layer in every],
    }


def page(data: dict) -> str:
    blob = json.dumps(data, ensure_ascii=False, sort_keys=True).replace("</", "<\\/")
    return TEMPLATE.read_text(encoding="utf-8").replace("__DATA__", blob)


def render(data: dict) -> str:
    top = data["layerStats"][-1]
    lines = [f"{len(data['skills'])} skills from {data['root']}",
             f"{len(data['layerStats'])} layer(s), coarsest {top['clusters']} "
             f"clusters and {top['noise']} noise, seed {data['seed']}",
             f"{data['model']}  {data['params'] or 'EVoC defaults'}", ""]
    for skill in data["skills"]:
        if not skill["local"]:
            continue
        cluster = skill["layers"][-1]
        tag = f"c{cluster}" if cluster >= 0 else "noise"
        lines.append(f"{skill['name']}  [{tag}]  strength {skill['strength']}")
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
    ap.add_argument("--serve", action="store_true", help="write it and open it")
    for name, (kind, default, help_text) in TUNABLE.items():
        ap.add_argument(f"--{name.replace('_', '-')}", dest=name, type=kind,
                        default=None, help=f"{help_text} (EVoC default {default})")
    args = ap.parse_args()

    # Only what the user actually set. Passing EVoC its own defaults back would
    # make every run look tuned and hide which knob was turned.
    params = {name: getattr(args, name) for name in TUNABLE
              if getattr(args, name) is not None}

    data = build(args.root.expanduser(), args.model, args.k, params)
    out = args.out or (Path("/tmp/context-token-vectors.html") if args.serve else None)
    if out is None:
        print(render(data))
        return 0
    out.write_text(page(data), encoding="utf-8")
    top = data["layerStats"][-1]
    print(f"{len(data['skills'])} skills, {len(data['layerStats'])} layer(s), "
          f"{top['clusters']} clusters, {top['noise']} noise -> {out}")
    if args.serve:
        webbrowser.open(out.resolve().as_uri())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
