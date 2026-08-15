# Deterministic sourcing policy

Supplemental art and domain context must be proactively discovered but approval-gated.

## Cheap evidence first

Look before you extract. A screenshot of two or three pages answers most questions:

```bash
sips -s format png --resampleWidth 1400 file.pdf --out /tmp/p.png   # then read the image
```

Byte-level extraction — parsing content streams, installing packages, hashing every page — is an **escalation the user opts into**, not the default. It is infeasible on small models and usually answers a question nobody asked. Once, `cards.pdf` (9.5 MB) was byte-parsed through a venv, pip installs and a 22 MB XObject decode; a screenshot answered the question, and the user overrode the extracted colours anyway.

Corpus files are hashed once at `init`. That is the only automatic hashing.

## Recommendation record

Each recommendation contains an ID and category, the observed cue, the design question it resolves, preferred authoritative source type, candidate library/archive/standard/dataset/renderer, license and attribution requirement, proposed version or retrieval date, expected tool/token cost, and user disposition.

The agent presents pending recommendations in the project questionnaire. It must not wait for the user to invent obvious categories such as ASCII art, motion curves, iconography, spatial standards, material samples, or mockup compositing.

## Retrieval

After approval:

1. Resolve official documentation or the primary source.
2. Pin a version, commit, edition, or retrieval timestamp.
3. Record rights and attribution before inference.
4. Fetch only the files or concepts needed for the current shot.
5. Hash raw bytes and store them outside the source root.
6. Commit provenance and compact excerpts, not large bodies.
7. Reuse the pinned artifact by hash.

Do not silently substitute a search snippet, generated imitation, unofficial mirror, or model memory for a named source.

## Questionnaire behavior

Phrase recommendations as confirmations:

> The references use monospaced text as illustration. I recommend pinning a licensed ASCII/Unicode art library and testing it as a deterministic decoration source. Approve, reject, or replace?

Do not ask “Do you have any libraries in mind?” when evidence already indicates the category.

