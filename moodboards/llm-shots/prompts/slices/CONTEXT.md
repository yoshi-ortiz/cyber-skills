---
purpose: the reusable fragments the prompts are assembled from
admits: plain-text slices and the manifest that orders them
refuses: whole prompts, images, anything not referenced by `../manifest.json`
max_file_bytes: 50000
---

# Slices

One edit to a slice changes every prompt that composes it, which is the point.
A slice no manifest references is dead and belongs deleted, not archived.
