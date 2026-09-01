---
purpose: one observer, one test, standard library only
admits: the Shot contract and its v1 migration, path-first record IO and hashing, verdict and token arithmetic, the renderer, advisory feedback assessment, and the tests for each
refuses: dependencies, a runner framework, authority derived from inference
max_file_bytes: 30000
---

# Scripts

The verbs are `record`, `observe`, `feedback`, `assess-feedback`, and `compare`.
They compose by file path rather than by import.

`shot_contract.py` is the only schema. `shot_io.py` owns every filesystem and
hashing concern, so nothing else opens a Shot. `feedback.py` suggests and never
decides, which is why it is pure and imports nothing from this package.
