---
purpose: imagery the README shows, and nothing else
admits: cover art and screenshots referenced from README.md
refuses: anything any skill reads at runtime -- a skill's own assets live inside that skill
max_file_bytes: 1200000
---

# README assets

Presentation only. No skill loads anything here, so a file in this directory can
change without any run behaving differently.

A skill that needs an asset at runtime keeps it under its own directory, where
that skill's contract governs it — see `aesthetic/assets/`, which holds
templates emitted into a user's project and is a different thing entirely
despite the matching name.
