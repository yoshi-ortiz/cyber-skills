---
purpose: skill entry point -- installing the second names other skills declare
admits: SKILL.md, and directories that carry their own contract
refuses: any name of its own; a skill's alias is declared on that skill, never here
max_file_bytes: 7250
---

# Silly

One job: make a declared second name typable. The declaration lives on the
skill it renames, which is what keeps this from becoming a registry that has to
be edited every time another skill gains a name.

It writes into an **installed** skills folder, never into this repository and
never into a published tree. Shipping the aliases would install every language
on every machine, and the whole argument for the manifest is that a reader pays
only for the names they can read.

The alias is a stub rather than a symlink, and that is not a shortcut. A
symlinked directory still contains a `SKILL.md` naming the original skill, so
the assistant registers the old command twice and the new name never appears.
Only a file that declares the new name creates the new command.

It ships in the same package as [aesthetic/](../aesthetic/) and shares nothing
with it.
