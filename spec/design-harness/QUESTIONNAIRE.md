# Design Harness Questionnaire

Answer each recommendation with approve, reject, or replace. The agent proposes likely sources; the user does not need to invent them.

## Project constraints

1. Confirm the intended output, audience, approval authority, and release boundary.
2. Confirm rights for the configured source-root evidence.
3. Confirm which proposed external sources may be fetched and pinned.

## Sourcing recommendations

1. **ascii-library** (`art-direction`): The agent must evaluate whether a pinned, licensed ASCII/Unicode art library fits the evidence; approve, reject, or replace the proposed source.
2. **art-assets** (`art-direction`): Confirm authoritative icon, illustration, texture, or type sources inferred from the visual grammar.

For every approved source, record its primary URL or package, license, pinned version/edition/commit, retrieval method, expected tool cost, and SHA-256.
