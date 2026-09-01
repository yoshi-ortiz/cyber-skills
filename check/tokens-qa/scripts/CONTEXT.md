---
purpose: one observer, one test, standard library only
admits: the Shot validator, verdict, token arithmetic and renderer, plus its test
refuses: dependencies, a runner framework, adapters for a second output type
max_file_bytes: 30000
---

# Scripts

One file. The verbs are `record`, `observe`, `feedback`, and they compose by
file path rather than by import.
