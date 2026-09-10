---
name: tokens-ontology
description: Index project context with pgvector, retrieve relevant source slices, and escalate to an EVoC exploration manifest when repository structure remains unclear.
disable-model-invocation: true
phase: check
---

# Tokens Ontology

Find the context needed for the current goal. Start with a bounded repository
manifest and exact pgvector retrieval. Build an EVoC exploration manifest only
when retrieval leaves ownership, overlap or module groupings unclear, or the
user explicitly requests repository exploration.

## Bind and index

1. State the active goal, repository root, included paths and the question the
   index must answer. Read existing directory contracts and context declarations.
   Choose source and documentation paths relevant to that question. Done when
   the admission scope is explicit; a repository root is not automatic permission
   to send all its content to an external service.
2. Run `manifest` below. Review its chunks and skipped-path reasons before
   embedding. The scanner uses Git's tracked/unignored inventory when available,
   otherwise walks only explicit includes. It excludes symlinks, common generated
   directories, sensitive filenames, unsupported types and oversized files.
   These filters are not a secret detector; inspect the selected content.
   Done when the source slices and their hashes match the intended scope.
3. Embed locally with one approved model2vec model directory. Index the resulting
   artifact into the intended PostgreSQL database with pgvector installed.
   `index` creates the extension and `tokens_context` table if absent and upserts
   this snapshot transactionally. It preserves other snapshots. Use standard
   `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER` and credential configuration.
   Done when the command returns an index identity and expected chunk count.
4. Search for the actual task question. Show a simple context index with path,
   line range, relevance distance and why the result matters. Read the source
   before making an implementation claim. Done when relevant owners and missing
   evidence are identified; similarity alone does not establish ownership.

## Run

From this skill's directory, with Python available:

```sh
python3 scripts/ontology.py manifest --root /path/to/project --include src --include docs --out /tmp/context-manifest.json
python3 scripts/ontology.py embed --manifest /tmp/context-manifest.json --model /path/to/local/model2vec-model --out /tmp/context-embedded.json
python3 scripts/ontology.py index --manifest /tmp/context-embedded.json
python3 scripts/ontology.py search --manifest /tmp/context-embedded.json --query 'Where is request authorization enforced?' --limit 5
```

The manifest command uses Python's standard library and optional Git. Embedding
requires `model2vec`; indexing/search require `psycopg[binary]` and a PostgreSQL
server with pgvector; exploration requires `evoc`, `numpy` and `matplotlib`.
Install applicable dependencies in an isolated environment. Fetch current
official documentation for the selected versions before setup. The CLI accepts
local model files so repository text stays local during embedding.

Outputs use exclusive creation: choose a fresh filename for each new artifact.
Changed source hashes or model files require rebuilding rather than silently
querying stale context. Existing snapshots remain until explicitly removed.
The exact cosine query is scoped by index identity; approximate vector indexes
are unnecessary until measurements justify them.

```text
Context index (illustrative layout; populate from actual search results)
+-------------------+---------+----------+--------------------------+
| Path              | Lines   | Distance | Relevance to current goal|
+-------------------+---------+----------+--------------------------+
| <source path>     | <range> | <value>  | <evidence-backed reason> |
+-------------------+---------+----------+--------------------------+
```

## Escalate to EVoC

Name the unresolved exploration question, then reuse the embedded snapshot:

```sh
python3 scripts/ontology.py explore --manifest /tmp/context-embedded.json --seed 42 --out /tmp/evoc-manifest.json
```

The manifest records the source snapshot, model identity, seed, cluster labels,
source ranges and hierarchy layers. Small corpora stay on retrieval. Inspect
representative source slices from candidate groups to form a repo map. Record
verified owners separately from inferred similarities. Noise means unassigned
at the chosen settings, not dead code, novelty or poor quality. EVoC groups
embeddings; validate dependencies through actual references and callers.

Done when the map answers the exploration question or names the remaining
uncertainty. Feed only the relevant paths and findings back to the active Item
and Tokens QA's session compass. Keep clustering artifacts out of product source
and avoid loading the full manifest into every subsequent prompt.

## Evidence and limits

With no database, report the file manifest as prepared and database indexing as
unverified. With missing model or EVoC dependencies, give the exact pending step;
a manifest alone is not a semantic search or clustering result.

Implementation references: [pgvector](https://github.com/pgvector/pgvector),
[psycopg transactions](https://www.psycopg.org/psycopg3/docs/basic/transactions.html),
and [EVoC](https://github.com/tutteinstitute/evoc). Recheck installed versions
before changing their interfaces.
