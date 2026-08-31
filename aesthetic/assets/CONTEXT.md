---
purpose: templates copied into a user project by `init`
admits: .tmpl files, and directories mirroring the project layout they produce
refuses: anything read at runtime -- templates are emitted once, then owned by the project
max_file_bytes: 8000
---

# Assets

These become files in someone's project. Once emitted they are the user's, not
the skill's, so a template change never retroactively edits a live project.
