# Spec: the command surface

The contract. What each family is, what it does, what answers to it, and what
it drives. Treat this as fixed for the duration of a build: a spec that changes
while you build against it is a conversation, not a contract.

Why this shape, and what it cost to arrive at, is in [GOAL.md](GOAL.md).
What is still unbuilt is the prototype backlog there, not here. **Nothing in
this file is speculative.** A row lands here when its shape is settled; until
then it is a prototype.

Fog. Lives on `dev`, never published to `main`.

## The shape

```
BARE -- on-ramps, entered from outside the sequence
  /kit          set the machine up
  /fix          something is broken

PREFIXED -- the sequence, prefix is the phase
  /first-*      before code exists
  /build-*      code and tests
  /land-*       release, irreversible
  /check-*      read-only, safe mid-session
```

The prefix is load-bearing ergonomics: typing `/first-` narrows to planning
before you have decided which planning, so the namespace does the routing a
router command would otherwise have to do. `/fix` and `/kit` carry no prefix
because both are entered from outside the sequence, and the shape of the name
is how you tell which kind of command you are looking at.

## Three kinds of alias

A flat name is not a skill. It is one of three things, and the kind decides
what the stub file contains.

| Kind | Mark | The stub says | Costs |
| --- | --- | --- | --- |
| **Whole** | `≡` | "Another name for **kit**. Read `kit/SKILL.md`." | One description line |
| **Anchor** | `→§` | "Read `build/SKILL.md` **§ Clean code** and follow it." | One description line |
| **Ghost argument** | `⇢` | "Read `land/SKILL.md` and run it with `asap`." | One description line |

An **anchor** points a name at a step *inside* a skill, so the doctrine is
written once and each name is a bookmark into it. A **ghost argument** bakes
the argument into the name, so the thing you would have had to remember to type
autocompletes instead.

**Doctrine lives in the six skills, never in a stub.** A stub that starts
explaining what its skill does is a second copy that will drift, which is why
`starter-pack/SKILL.md` says only "read the other file" in 617 bytes.

`silly/scripts/alias.py` generates the whole kind today. Anchor and ghost
argument are one line each in its `stub()` function, plus a field to carry the
section or the argument. R-45.

## The families

| Core family | Core tasks (`SKILL.md` sections) | Aliases and arguments | Drives, and where it comes from |
| --- | --- | --- | --- |
| **`kit`**<br>*ships* | § Install<br>§ Sync<br>§ Fix | `starter-pack` ≡<br>`install` `setup` `init` `start` ⇢ install<br>`sync` `update` `upgrade` ⇢ sync<br>`doctor` `repair` `troubleshoot` `conflict` ⇢ fix<br>`kit design` ⇢ design<br>`kit español` ⇢ es | The whole manifest. `harness` reads `collection.yaml` and installs every source in it. |
| **`first`**<br>*= `genesis`, ships* | § Interview before you architect<br>§ Promote to a spec<br>§ Fetch what you do not know<br>§ Source before you write<br>§ Update the state | `first-plan-roadmap` →§ Update the state<br>`first-take-note` →§ Interview<br>`first-idea-sketch` ⇢ sketch<br>`first-work-style` ⇢ style<br>`first-aesthetic` ≡ `aesthetic`<br>`plan` `genesis` ≡ | `ask-matt`, `prototype`, `grilling` — `mattpocock/skills` *(coding, bare)*<br>`brainstorming` — `obra/superpowers` *(coding, bare)*<br>`aesthetic`, `knowledge` — `yoshi-ortiz/cyber-skills` *(design)* |
| **`build`**<br>*new* | § Clean code<br>§ QA tests<br>§ Pre-release | `build-clean-code` →§ Clean code<br>`build-qa-tests` →§ QA tests<br>`build-pre-release` →§ Pre-release<br>`to` `make` ≡ | `ponytail` — `DietrichGebert/ponytail` *(coding)*<br>`tdd`, `code-review` — `mattpocock/skills`<br>`test-driven-development`, `verification-before-completion` — `obra/superpowers`<br>`semgrep` — `semgrep/skills` *(security)* |
| **`land`**<br>*new* | § Burndown<br>§ Release | `land-asap-burndown` ⇢ asap<br>`land-deployed-release` ⇢ deploy *(final goal)*<br>`do` `ship` `burndown` ≡ | Nothing external. The burndown state machine is the one genuinely new thing in this scheme; `ROADMAP.md` and `BUGS.md` are its store. |
| **`check`**<br>*new* | § Progress<br>§ Ontology | `check-progress-goals` →§ Progress<br>`check-release-ontology` →§ Ontology<br>`check` ≡ | `zoom-out` — `pstack` *(R-43)*<br>`graphify` — `safishamsi/graphify` *(research)* |
| **`fix`**<br>*new, bare* | § Fix the code<br>§ Fix the rail | `fix` bare<br>`fix-context-derail` →§ Fix the rail<br>`rail` `repair` `unstick` ≡ | `diagnosing-bugs` — `mattpocock/skills`<br>`systematic-debugging` — `obra/superpowers`<br>`poteto-mode` — `pstack` *(R-43)* |

**The rail lives in `fix`, not `check`.** `check` reads state and reports;
repairing a derailed context is a write, and it is the same reflex as repairing
broken code: something is wrong, restore it. Splitting the two across families
is what left `/FIX` with no home in the first draft.

## What a family owes

Every one of the six, before it is done:

| Obligation | Why |
| --- | --- |
| A `CONTEXT.md` declaring `purpose`, `admits`, `refuses`, `max_file_bytes` | `contracts.py` enforces it, and the byte cap **is** the worst-case session load |
| A `SKILL.md` whose sections are the anchor targets above | Anchors point at section names, so renaming a section breaks a command |
| A deliberate invocation choice | Keep model invocation only when the agent must discover the skill cold or another skill drives it; otherwise declare `disable-model-invocation: true` and spend human cognitive load instead of model context |
| `phase` in frontmatter | Load-bearing only where skill name and phase diverge (`genesis`, `aesthetic`). Declared without a gate until R-38. There is no `weight` field: the byte cap already is the worst case, and a family's sections differ in cost. |
| A row in the README index and every translation it offers | `tools/index_gate.py` refuses otherwise |
| Its second names present in its own `description` | The gate refuses a name the assistant has never heard of |

## Verify

```bash
python3 aesthetic/scripts/contracts.py --root .
python3 tools/index_gate.py
python3 tools/publish.py --out /tmp/published --check
python3 silly/scripts/alias.py list --root ~/.claude/skills
```
