---
purpose: one clustering run over installed skills, and the page that reads it
admits: the clustering script and its HTML template
refuses: doctrine, and any import from another skill's scripts
max_file_bytes: 30000
---

# Scripts

`vectors.py` prepares a corpus, then analyzes it. Preparation owns the expensive
stable work: loading, embedding, projection, similarity, and nearest peers.
Analysis owns EVoC and accepts the tunable parameters. The terminal and saved
page are one adapter; `--serve` is a loopback HTTP adapter that holds the
prepared corpus and returns a fresh analysis from `POST /tune`.

`dashboard.html` reads either adapter's data. In a saved page its tuning controls
are disabled. Under `--serve` they replace the in-memory result and redraw;
nothing is persisted. The server pattern is deliberately local rather than an
import from `tools/`, which this package refuses.

These are the only files in this package that import a third-party module; the
dependencies remain in the virtual environment the user creates.
