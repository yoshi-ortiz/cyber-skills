---
name: knowledge
description: Distil external documentation into a local, cited OKF 0.2 knowledge bundle the agent reads instead of re-scraping. Use when researching a dependency, SDK, API, framework, standard, or a competitor's product, and when the user asks to save, cache, capture, or index a reference or a source. Also use before implementing against an unfamiliar or fast-moving library, so the facts in context are fetched and attributed rather than recalled. In Spanish the same skill answers to enciclopedia.
translations:
  es: enciclopedia
---

# Knowledge

A fetched page is worth nothing on the next turn. Distil it once into a
**concept file** in the project, cite where it came from, and every later turn
reads a dense local fact instead of guessing or paying for the fetch again.

The format is **Open Knowledge Format 0.2**: one concept per file, YAML
frontmatter, `index.md` at the door. Spec cached in
[references/okf-0.2.md](references/okf-0.2.md); do not fetch it again.

## Where it lands

`docs/knowledge/` in the **target project**, never in this skill. One directory
per subject when there is more than one, each with its own `index.md`.

## Capture a source

```bash
python3 <skill>/scripts/okf.py new <url> --root docs/knowledge \
    --type Reference --title "Prisma migrate" --by claude/opus-5
```

It fetches, writes the stub with `resource`, `generated`, and `sources` filled
in, and prints the extracted text to stdout. **The extract is not the
deliverable.** Read it, then replace the body with the distilled concept.

Local files work too: pass a path instead of a URL.

## Distil, then verify

1. Read the extract. Keep what this project will act on, drop the marketing,
   the changelog, and the parts about versions you do not use.
2. Write the body: what it is, the shape that matters, the failure modes, the
   exact version this was true for. Rules in
   [references/distilling.md](references/distilling.md).
3. Set `description` to one sentence and `status` to `stable` once the body is
   real. A `draft` in the tree is a stub nobody finished.
4. Add a row to `index.md` naming the concept, its purpose, and its trust
   boundary. A concept the index does not list is a concept nobody finds.
5. Gate it:

```bash
python3 <skill>/scripts/okf.py check --root docs/knowledge
```

Refuses a file with no parseable frontmatter, a file with no `type`, a concept
missing from `index.md`, and an index link that resolves to nothing.

## What a concept file is not

| Not | Because |
| --- | --- |
| A copy of the docs | You already have the URL. The value is what you cut. |
| A summary written from memory | Every claim traces to a `sources` entry, or it is not in the file. |
| Undated | `generated.at` and the version the claim held for, or the file rots silently. |
| A place for project decisions | Those are the project's, not the source's. Keep them out. |

Version pins are load-bearing. A snippet that matches the docs but not the
dependency manifest is a hallucinated compatibility claim: name the version in
the body and check it against the manifest before acting on it.

## Refresh

Re-run `new` with `--force` on the same slug when the upstream moves. Keep the
old `sources` entry, add the new one, and say in the body what changed. A
`stale_after` timestamp is worth setting on anything version-bound.
