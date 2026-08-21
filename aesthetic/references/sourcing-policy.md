# Deterministic sourcing policy

Supplemental art and domain context is proactively discovered, narrowly fetched,
licensed, and pinned. See [asset-sourcing.md](asset-sourcing.md) for the strict
graphic-resolution order.

## Cheap evidence first

Inspect representative pages and images before expensive extraction. Corpus
files are hashed at intake; parsing every embedded object or installing a new
tool requires a real design question that the cheaper view cannot answer.

## Recommendation record

Each source recommendation names its category, observed cue, design question,
primary source, license/attribution, version or retrieval date, expected cost,
and disposition. Raise obvious categories such as iconography, pixel type,
ASCII/Unicode, motion curves, spatial standards, or compositing sources without
asking the user to invent a library name.

## Retrieval

1. Resolve official documentation or the primary repository.
2. Confirm license and attribution before inference.
3. Pin a version, commit, edition, or retrieval date.
4. Fetch only the current cohort's required artifact.
5. Hash and store it outside the immutable corpus.
6. Record transformations and reuse the pinned bytes.

Never substitute a search snippet, unofficial mirror, remembered vector path,
generated imitation, or model memory for a resolved source.
