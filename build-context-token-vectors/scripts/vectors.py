#!/usr/bin/env python3
"""Which installed skills are actually this one's peers.

`tools/token_bench.py` measures a flow against a reference flow, and the
reference is authored by hand: someone decided `ask-matt` is the peer. This
derives the comparison set instead. Embed every installed `SKILL.md`, cluster
the vectors, and read the neighbours off the corpus.

Position and overlap only. A skill that clusters with nothing has no peer among
the skills installed; whether that is novelty or a diluted `SKILL.md` is a
judgement no clusterer can make, which is why nothing here writes a verdict.

    python3 scripts/vectors.py                      # print it
    python3 scripts/vectors.py --out /tmp/v.html    # write the dashboard
    python3 scripts/vectors.py --serve              # and open it

Third-party imports live here and nowhere else in this package. Create the
environment yourself; this installs nothing.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
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

    The plot is a reading aid and never the result: the clustering happens in
    full dimensionality, and two components of a 256-dimensional space discard
    most of what separated the clusters. Points that look adjacent here may not
    be, which is why the neighbour table carries the real numbers.
    """
    centred = vectors - vectors.mean(axis=0)
    coords = centred @ np.linalg.svd(centred, full_matrices=False)[2][:2].T
    span = coords.max(axis=0) - coords.min(axis=0)
    return (coords - coords.min(axis=0)) / np.where(span > 0, span, 1)


def build(root: Path, model_name: str, k: int) -> dict:
    names, texts = load(root)
    if not names:
        raise SystemExit(f"no SKILL.md under {root}")
    vectors = embed(texts, model_name)
    labels = EVoC(random_state=SEED).fit_predict(vectors)
    coords = project(vectors)
    similarity = vectors @ vectors.T
    np.fill_diagonal(similarity, -1.0)

    skills = []
    for i, name in enumerate(names):
        order = np.argsort(-similarity[i])[:k]
        skills.append({
            "name": name,
            "local": name in LOCAL,
            "cluster": int(labels[i]),
            "x": round(float(coords[i][0]), 4),
            "y": round(float(coords[i][1]), 4),
            "bytes": len(texts[i]),
            "peers": [{"name": names[j], "sim": round(float(similarity[i][j]), 3),
                       "local": names[j] in LOCAL} for j in order],
        })
    return {"skills": skills, "root": str(root), "model": model_name,
            "seed": SEED, "clusters": int(labels.max()) + 1,
            "noise": int((labels < 0).sum())}


def page(data: dict) -> str:
    blob = json.dumps(data, ensure_ascii=False, sort_keys=True).replace("</", "<\\/")
    return TEMPLATE.read_text(encoding="utf-8").replace("__DATA__", blob)


def render(data: dict) -> str:
    lines = [f"{len(data['skills'])} skills from {data['root']}",
             f"{data['clusters']} clusters, {data['noise']} noise, "
             f"seed {data['seed']}, {data['model']}", ""]
    for skill in data["skills"]:
        if not skill["local"]:
            continue
        tag = f"c{skill['cluster']}" if skill["cluster"] >= 0 else "noise"
        lines.append(f"{skill['name']}  [{tag}]")
        for peer in skill["peers"]:
            lines.append(f"   {peer['sim']:.3f} {'*' if peer['local'] else ' '} {peer['name']}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", type=Path, default=Path.home() / ".agents/skills")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("-k", type=int, default=6, help="neighbours to report")
    ap.add_argument("--out", type=Path, help="write the dashboard and exit")
    ap.add_argument("--serve", action="store_true", help="write it and open it")
    args = ap.parse_args()

    data = build(args.root.expanduser(), args.model, args.k)
    out = args.out or (Path("/tmp/context-token-vectors.html") if args.serve else None)
    if out is None:
        print(render(data))
        return 0
    out.write_text(page(data), encoding="utf-8")
    print(f"{len(data['skills'])} skills, {data['clusters']} clusters, "
          f"{data['noise']} noise -> {out}")
    if args.serve:
        webbrowser.open(out.resolve().as_uri())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
