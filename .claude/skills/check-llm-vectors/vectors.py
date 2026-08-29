#!/usr/bin/env python3
"""Cluster every installed SKILL.md, and name each local skill's real peers.

The comparison set in `token_bench.py` is hand-authored: someone decided
`ask-matt` is the reference. This derives it instead. Embed each skill, cluster,
and the nearest neighbours are the skills a benchmark should actually run
against.

Position and overlap only. Nothing here judges quality.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
from evoc import EVoC
from model2vec import StaticModel

# Ours, from the repo's CONTEXT.md table. Everything else is someone else's.
LOCAL = {"aesthetic", "genesis", "knowledge", "ora", "silly", "kit",
         "starter-pack", "check-transformers-neural-network"}
SEED = 42


def body(text: str) -> str:
    """Frontmatter is metadata; the doctrine is what a peer is judged on."""
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


def neighbours(vectors: np.ndarray, names: list[str], target: int, k: int) -> list[tuple[str, float]]:
    """Cosine similarity, vectors already L2-normalised."""
    sims = vectors @ vectors[target]
    order = np.argsort(-sims)
    return [(names[i], float(sims[i])) for i in order if i != target][:k]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", type=Path, default=Path.home() / ".agents/skills")
    ap.add_argument("--model", default="minishlab/potion-base-8M")
    ap.add_argument("-k", type=int, default=5)
    args = ap.parse_args()

    names, texts = load(args.root)
    if not names:
        print(f"no SKILL.md under {args.root}", file=sys.stderr)
        return 1
    print(f"{len(names)} skills from {args.root}\n")

    model = StaticModel.from_pretrained(args.model)
    vectors = np.asarray(model.encode(texts), dtype=np.float32)
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-12

    # random_state is contractual, not tuning: EVoC is stochastic without it.
    labels = EVoC(random_state=SEED).fit_predict(vectors)
    clustered = int((labels >= 0).sum())
    print(f"{labels.max() + 1} clusters, {len(names) - clustered} noise "
          f"({clustered / len(names):.0%} clustered), seed {SEED}\n")

    print("=" * 72)
    print("LOCAL SKILLS: cluster, and who they actually sit next to")
    print("=" * 72)
    for i, name in enumerate(names):
        if name not in LOCAL:
            continue
        tag = f"c{labels[i]}" if labels[i] >= 0 else "noise"
        print(f"\n{name}  [{tag}]")
        for peer, sim in neighbours(vectors, names, i, args.k):
            mark = "*" if peer in LOCAL else " "
            print(f"   {sim:.3f} {mark} {peer}")

    print("\n" + "=" * 72)
    print("CLUSTERS CONTAINING A LOCAL SKILL")
    print("=" * 72)
    for c in sorted({labels[i] for i, n in enumerate(names)
                     if n in LOCAL and labels[i] >= 0}):
        members = [names[i] for i in range(len(names)) if labels[i] == c]
        print(f"\nc{c}  ({len(members)})")
        print("   " + ", ".join(members))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
