---
name: ora
description: Rewrite a reply in the user's own Spanish. Summarizes the conclusions by default; `full` translates the whole reply, and `on`/`off` hold it for the session. Use when the user asks for an answer in Spanish or asks for it shorter and plainer — "ora", "en español", "resúmelo", "explícamelo simple", "tradúcelo", "más corto", "en cristiano". One reply only unless they said `on`. Do NOT use merely because the user happens to write in Spanish.
---

# Ora

A reply, rewritten in the user's own Spanish.

## Modes

| Invocation | What it does |
| --- | --- |
| `/ora`, or "resúmelo", "en corto" | Keep the conclusions, cut the rest. This reply only. |
| `/ora full`, or "todo", "completo" | Translate the whole reply. This reply only. |
| `/ora on` | Stay on for every reply until told otherwise. |
| `/ora off` | Stop. Back to normal replies. |

One reply is the default, and `on` is the only thing that changes it. Once
`on`, keep going until `off`, "stop ora", "modo normal" or the session ends;
do not quietly drop it after a long reply or a topic change.

In `full`, translate rather than summarize. Every section, caveat and number in
the reply survives.

A user writing to you in Spanish is not a request for Ora. Answer them in
Spanish normally. Ora is for when they ask you to compress or convert.

## Match their Spanish, do not average it

"Latin American Spanish" is not a register any person writes in. Read the
user's own messages and mirror the variety they actually use.

| Markers in their writing | Follow with |
| --- | --- |
| ahorita, platicar, mande, padre, chido, órale | Mexican |
| vos, che, laburo, quilombo, boludo | Rioplatense |
| parcero, chévere, berraco, bacano | Colombian |
| pana, chamo, vaina, burda | Venezuelan and Caribbean |

Match their pronoun too: `tú`, `vos` or `usted`, whichever they use on you.

When their messages give you nothing to go on, write neutral Spanish with no
regional slang at all. Neutral is a real choice and always safe.

Never mix markers from two countries in one reply. A "chévere" next to an
"ahorita" is the tell that nobody real wrote it, and it is the most common way
this skill fails.

## Summary mode

1. **Catch the point.** Keep the real conclusions. Cut process chatter, hedges
   and digressions. Done when you can say it in one short sentence.
2. **Say it plainly.** Everyday words. Comic tone is welcome; never hide the
   truth behind the joke. Done when a non-expert gets it on the first read.
3. **Dress it.** Section headers, one idea per bullet. Done when it is
   scannable in about ten seconds.

## Every bullet opens with the action, in bold, alone

Bold names the action taken, verb first, nothing else. Not the subject, not the
full sentence, just what was done: **Bajé las etiquetas.**, not **Etiquetas.**
or **Bajé las etiquetas debajo de la ronda, junto al brief.**

The detail goes on its own line under it, inside the same bullet. That split
is what makes the scan work: the bold line alone tells the whole story of what
happened, and the line under it is there for whoever wants the rest.

```markdown
## ✅ Se hizo
- **Bajé las etiquetas.**
  Ahora están debajo de la ronda, junto al brief.
- **Arreglé Ora.**
  Ya no se queda pegada. Una invocación, una respuesta.

## ⏭️ Qué hacer
- **Nada urgente.**
  Todo verificado contra tu proyecto real.

## 😅 Ojo
- **Revisa las dos copias.**
  Estaban desincronizadas y pueden separarse otra vez.
```

A whole sentence in bold is a headline, not an action, and it defeats the
scan. Skip empty sections.

## Link the files you name

A file is a link, written relative to the working directory, so the user can
open it from the reply: `[SKILL.md](kit/spanish/ora/SKILL.md)`, or
`[bootstrap_harness.py:1594](first/aesthetic/scripts/bootstrap_harness.py:1594)` when
the line matters. Name it once per bullet and link that mention.

Paths inside code fences stay bare. A command is meant to be copied, not
clicked, and a markdown link inside a fence copies as broken text.

## Rules

- Code, paths, commands and error strings stay exact. English inside fences is
  fine.
- Emoji budget: 1 to 3 per section, as markers, not confetti.
- Never invent a fact to land a joke.
- Bad news stays bad news. A light tone never softens a real failure into a
  shrug, and never buries a warning the user has to act on.

## Example

**Before:**

> The authentication middleware was comparing token expiry with a strict
> less-than operator, which caused valid tokens at the exact expiry boundary to
> be rejected. We should change the comparison to less-than-or-equal and add a
> regression test.

**After, summary mode:**

```markdown
## ✅ Se hizo
- **Encontré el bug.**
  [auth.ts](src/middleware/auth.ts) botaba tokens válidos justo al vencimiento: usaba `<` en vez de `<=`. 😅

## ⏭️ Qué hacer
- **Cambia el operador** a `<=`.
- **Mete un test** para que no vuelva a pasar.
```
