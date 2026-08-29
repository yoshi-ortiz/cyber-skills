---
purpose: one clustering run over installed skills, and the page that reads it
admits: the clustering script and its HTML template
refuses: doctrine, and any import from another skill's scripts
max_file_bytes: 30000
---

# Scripts

`vectors.py` embeds, clusters, and either prints or writes a page.
`dashboard.html` is that page, with its data substituted in at build time --
the same shape as `tools/trace_preview.html`, so a reader who knows one knows
the other.

These are the only files in this package that import a third-party module. That
is the whole reason this skill is alpha.
