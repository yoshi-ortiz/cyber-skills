---
name: silly
description: Installs second names for the skills you already have, so a command can be typed in your own language or in a name you simply like better. Use when the user asks for commands in another language, says comandos-en-espanol, comandos en espanol, silly, fun names, alias, or asks why a skill answers to two names. Also use when a skill declares a translations or aliases block and the user wants those names live.
disable-model-invocation: true
also:
  - comandos en espanol :: Add commands in Spanish
---

# Silly

A skill answers to the name in its `SKILL.md` and to nothing else. So
`/enciclopedia` does not work because `knowledge` exists in Spanish somewhere;
it works because a file says `name: enciclopedia`.

This installs those files. **Only the name is translated**, never the skill.
The alias is one file pointing at the real thing, so there is no second copy to
drift.

## Install the names

```bash
python3 <skill>/scripts/alias.py list --root ~/.cursor/skills
python3 <skill>/scripts/alias.py link --root ~/.cursor/skills --lang es
```

`--root` is the assistant's own skills folder: `~/.cursor/skills`,
`~/.claude/skills`, or whatever that app uses. Run it once per folder.

| Want | Run |
| --- | --- |
| See what is declared and what is live | `list` |
| Spanish command names | `link --lang es` |
| The playful names | `link --fun` |
| Both, in one pass | `link --lang es --fun` |
| Undo all of it | `unlink` |

`--dry-run` on `link` and `unlink` prints without touching anything.

Then **tell the user to start a new chat.** Assistants read their skills at
session start, so nothing installed mid-conversation exists yet.

## What it will not do

It refuses to write over a directory it did not create. An alias is worth less
than any real skill that happens to share its name, so a collision stops the
run rather than resolving it. Its own stubs are safe to rewrite, and `unlink`
removes only those.

Nothing is installed by default. A package that shipped four languages to
everyone would charge every reader for three they cannot use.

## Declaring a name on a skill

Both blocks are optional and live in the skill's own `SKILL.md` frontmatter.

```yaml
---
name: knowledge
description: ... In Spanish the same skill answers to enciclopedia.
translations:
  es: enciclopedia
aliases:
  - nerd-mode
---
```

| Block | Holds | Rule |
| --- | --- | --- |
| `translations` | Language code to name | One name per language. The name must be lower case, and it must appear in the skill's own `description`, or saying it triggers nothing. |
| `aliases` | A list of playful names | Same rule. A name nobody can trigger is decoration. |

The description rule is not a style preference. The assistant chooses a skill
by reading descriptions, so a name absent from every description is a name it
has never heard of, alias file or not.

## Currently declared

| Skill | Language | Name |
| --- | --- | --- |
| `knowledge` | Spanish | `enciclopedia` |

Run `list` against a real folder rather than trusting this table. It is the
manifests that are authoritative, and this one is written by hand.
