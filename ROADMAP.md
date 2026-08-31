# Roadmap

The burndown. One row per item, each in exactly one state, so "what is left"
is answerable without reading prose.

States: `TODO` · `IN-PROGRESS` · `BLOCKED` · `DONE`

Bugs live in [BUGS.md](BUGS.md) with their root causes. Shipped changes live in
[CHANGELOG.md](CHANGELOG.md). This file is what remains.

Fog. Lives on `dev`, never published to `main`.

## Now

| id | State | Item | Notes |
| --- | --- | --- | --- |
| R-01 | `DONE` | Lightbox spacing scale revived | B-001 |
| R-02 | `DONE` | Per-comp CSS scoping | B-002 |
| R-03 | `DONE` | Variant cap counts the ledger | B-003 |
| R-04 | `DONE` | Status staleness, both directions | B-004, B-005 |
| R-05 | `DONE` | Round stays live during inference | B-006 |
| R-06 | `DONE` | Project brief, one question at a time | |
| R-07 | `DONE` | Brief write path (`POST /brief`) | |
| R-08 | `DONE` | Bookmark as a fourth signal | |
| R-09 | `DONE` | Publication guardrails, `dev` / `main` split | |
| R-10 | `DONE` | Repo docs: README, BUGS, CHANGELOG, this file | |

## Next

| id | State | Item | Why it is not done |
| --- | --- | --- | --- |
| R-11 | `DONE` | Deterministic corpus tagging | Shipped in `corpus_tags.py`. Tags are stored keyed by sha256, so reorganizing or renaming an inspiration folder never orphans them. Intent still cannot be read off a filename, which is why the user authors it rather than the harness inferring it. |
| R-12 | `DONE` | Aspect-scoped corpus valuation | A tag names one or more `aspects` from the design-system foundations plus a `quality` of `finished` or `sketch`, so a rough draft is creditable for its colour alone. Replaces the old binary observed-or-omitted. |
| R-13 | `TODO` | Redraw the 62 bare-SVG previews | B-007. Mechanical but large; each needs redrawing in HTML/CSS and re-shooting. |
| R-14 | `DONE` | Judge design quality afresh | Done 2026-08-22 against `keynote-performance`. Output is not generically weak: the system is coherent and subject-specific, 27/27 shots visible, contrast 4.61:1, zero unreadable rules. B-010 closed as too vague; the real defect is B-017. Pipeline measured at 0.19s, so run cost is inference, not tooling. |
| R-26 | `TODO` | Fix the broken circular ring type | B-017. The lower arc of `cover.ring.kicker.antetitulo-arco` renders inverted, red, and overlapping. Read the comp before proposing a redraw — likely per-glyph rotation past 180° without counter-rotation. |
| R-27 | `DONE` | Let an empty cohort re-render the article | B-018. One early return in `check_round_earns_its_place`. The ROADMAP workaround snippet below is now unnecessary. |
| R-28 | `DONE` | Stop leaving Chrome profiles in the user's project | B-019. Nothing to build. The one Chrome call already uses `tempfile.mkdtemp` and removes it in a `finally`; `_chrome-profile` appears nowhere in the repo. The 184 MB is residue from an earlier version or another tool, inside the user's project, so clearing it is their call. |
| R-29 | `DONE` | Give the article a `<meta charset="utf-8">` | Verified against the exact server config that produced mojibake earlier: `text/html` with no charset now renders Spanish accents correctly. |
| R-15 | `TODO` | Split `bootstrap_harness.py` | 210KB against a 30KB budget, 7x over — was 297KB until the 1,447 lines of CSS/JS moved out to `aesthetic/screen/` and `render_article` shed its two dead parameters. Still over; the rest is Python. Recorded as accepted debt in `aesthetic/scripts/CONTEXT.md` and `AGENTS.md`: split before adding to it, do not widen the budget to silence the check. **R-21, R-22, and R-20 added ~5.5KB to it without splitting first** — a knowing violation of that rule, taken because splitting is this item and the fixes were scoped to the round-scope and chart bugs. The rule stands; the next addition should pay it. |
| R-52 | `TODO` | Agreed tokenization, visualized and gated | [Promoted contract](docs/SPEC/AGREED_TOKENIZATION.md). The token-level lens already exists in `tools/trace_preview.py` and renders every chunk as the chips a BPE actually produces; the default lens is now `Xenova/gpt-4o`. What is missing is the durable half. Three gaps, in order. **One**, the click log lives at `spec/design-harness/context-tags-inbox.jsonl`, which is fog on both channels *and untracked*, so a `check.py` gate reading it is structurally red on every clean checkout and in the detached worktree gates run in. **Two**, `validate_tag` records `at, key, signal, value, pass, tokenizer, exactTokens` and no content hash, so an agreement survives an edit to the text it agreed with and asserts nothing. **Three**, `--review` reports and edits nothing, so no verdict is ever written down. Fix is one shape: `--review` emits a tracked-but-fog verdict file pinning sha256 per chunk, and the gate refuses a verdict whose text has moved. Passes with no verdict are not failures, so the gate ships green and earns coverage instead of asserting it. Landing this amends `CLAUDE.md`'s "signal density gets no checker": what gains a checker is agreement and staleness, never density. Measured while specifying this: `Xenova/gpt-4` 8,013 tokens and `Xenova/gpt-4o` 8,006 on the same `proposal` bundle, both fragmenting `bur|nd|own`, `multim|odal`, `templ|ated`, `crit|ique` identically -- the lens is structural, and the fragmentation belongs to the vocabulary rather than the tokenizer. |
| R-53 | `TODO` | Advisory clustering over the corpus | [Promoted contract](docs/SPEC/ADVISORY_CLUSTERING.md). Supplies the advisory ranker R-50 names as remaining, using [EVoC](https://evoc.readthedocs.io/en/latest/) -- node embedding related to UMAP plus density clustering related to HDBSCAN, returning `-1` for noise, `membership_strengths_`, and `cluster_layers_` finest to coarsest. Two callers, corpus first: CLIP-class vectors over `corpus.json` propose candidate groups against the folders the user authored by hand, and sentence vectors over compiled chunks propose **semantic group** and **contamination risk**. Neither can propose **context utility**, which needs accepted-result outcomes the attempt record holds, so the three signals stay independent. Three constraints decide the shape. **One**, EVoC is stochastic by default and a rerun returns different labels without `random_state`, which the compiler's byte-for-byte replay cannot tolerate -- the seed is contractual, not tuning. **Two**, proposals key by sha256 following `corpus_tags.py`, so a folder rename never orphans them. **Three**, `numpy`, `scipy`, `scikit-learn`, `numba` and a separate embedding model cannot sit under `aesthetic/scripts/` or `tools/`, and the `trace_preview.py` escape hatch of pushing a heavy dependency into a browser does not transfer, because Numba compiles Python. Where the boundary goes instead is the open part, in GOAL.md. Nothing here writes a tag, a declaration, a budget, or a publication decision. |
| R-18 | `TODO` | Companion live-check, every run | `bootstrap_harness.py open` can restore the last page, but nothing in `SKILL.md` gates the rest of a run on the companion actually being reachable first. Needs a hard precondition: verify the companion is live before any other Loop step, not just an `open` call that may go unchecked. |
| R-19 | `DONE` | Wire the manifesto brief into the Loop | B-016. `ensure_brief` in `open_board` creates the brief the first time the companion opens, and `adopt` folds its inbox in. Zero SKILL.md bytes, which mattered at 7250/7250. The module was always complete; nothing had ever created a brief for it to render. The existing one-question-at-a-time textarea is the deliverable; a rich-text editor did not earn its place. |
| R-20 | `DONE` | Corpus relational tagging, embedded in the article | B-016. Tags are authored per reference FOLDER, because the user already curated their inspiration into named folders — 8 decisions on the real project, not 135. `POST /corpus` queues, `corpus_tags.py` owns the schema, and `adopt` prints the key-token digest. Measured on `keynote-performance`: records the agent must write per round fell from 135 to 5. |
| R-21 | `DONE` | Enforce Round Scope against parent items | B-011. `check_round_stays_in_scope` refuses a cohort spanning two parent items, read off the dotted id. No escape hatch: `--asks` answers the foundation-span check, not this one. |
| R-22 | `DONE` | Group the status chart by mutation lineage | B-014. `lineage_root_of` collapses a supersede chain to one bar carrying `data-variants`; the round zone's existing idea-grouping now reaches the strip. |
| R-24 | `TODO` | Cap retry cost when the golden-rule gate rejects a spec | B-013's remaining gap. `golden_rules.py` is single-shot with no memory between calls, so "fix a rejected spec; never bypass the gate" is prose only — nothing requires a retry to narrow scope instead of re-attempting the same spec. Judge against a real run now that R-21 caps breadth, rather than assuming the original symptom survived it. |
| R-25 | `TODO` | Explicit Subject field in `editorial.json` | The durable model behind R-21. The dotted-id prefix is the enforced guard and needs no migration; an explicit `subject` on `validate_editorial_spec`, cross-checked in `validate_art_direction`'s cohort gate, would say the same thing without relying on a naming convention. Not urgent while the convention holds. |
| R-30 | `DONE` | Bring `server.cjs` under budget | 37,195 bytes against 40,000. Deleting duplicated browser-rendering behavior held better than splitting the file; the parser and companion tests cover the resulting path. |
| R-23 | `DONE` | Give the companion header a live agent identity | B-015. `resolve_agent` takes URL and name whole from one source, which is the actual defect: a real `project.json` paired the name `Claude Code` with a `cursor://` link. `AGENT_HOSTS` lets a host with no deep link name itself. |

## Corpus and benchmark

Added 2026-08-29 from an architecture review benchmarked against
`mattpocock/skills` at HEAD. Ordered by dependency: R-54 carries R-55 and R-57.

| id | State | Item | Notes |
| --- | --- | --- | --- |
| R-54 | `TODO` | One module owns the skill corpus | B-021. "Enumerate installed skills and read their frontmatter" is written five times for frontmatter and four times for the walk. The literal `re.match(r"\s*---\s*\n(.*?)\n---", text, re.S)` appears verbatim in `tools/token_bench.py` (twice), `silly/scripts/alias.py`, and `aesthetic/scripts/contracts.py`; `knowledge/scripts/okf.py` uses a different tail and returns `None` instead of `{}`; `build-context-token-vectors/scripts/vectors.py:97` strips it with a fifth variant requiring no leading whitespace, so it agrees with the others only on well-formed files. The seam is not hypothetical and never was: `tools/index_gate.py` and `tools/manifest_gate.py` already `from alias import ...` across a skill directory to borrow one implementation, while `token_bench.py` in the same directory reimplements it. Six adapters, no interface. Only item here that fixes a defect rather than reducing friction, and R-55 and R-57 both sit on it. Open question is placement, the same one R-53 records: a module every skill reads cannot live under any one skill, and `tools/` is fog. |
| R-55 | `TODO` | Flows become repo data, and the benchmark gains a release mode | `tools/token_bench.py` takes its comparison set from `--flow name=a,b,c` on the command line. Nothing constructs, stores, or validates a flow, so the published tables in GOAL.md are reproducible only by copy-pasting prose into a shell. No `ask-matt` file is ever read: the name is a string in a docstring at `token_bench.py:17`, in the `RAIL` tuple at `vectors.py:50`, and in prose. Re-run 2026-08-29 against a freshly synced reference: 870 B context / 36,267 B path for `ask-matt`, 1,855 / 37,405 for the rail, 2.13x and 1.03x, identical to the recorded table, so the reference has not moved since it last did. Two halves. Flows move into repo data so the bare command reproduces every published number and a gate can refuse a stale table. Then a release mode, because the interface cannot answer "how does our release weigh against theirs" at all: producing that comparison needed a throwaway script. Measured there, shipped skills only: 29 against 8, mean `SKILL.md` 4,379 B against 4,321 B which is parity, mean description 161 B against 353 B which is **2.19x** and independently confirms the flow benchmark's 2.13x over a different population, stub rate 14% against 0%. GOAL.md Finding 3 already named the stub scheme as the reference's own; nothing has adopted it. |
| R-56 | `TODO` | Decide the companion seam: shared, or gated identical | `tools/trace_preview.py` and `build-context-token-vectors/scripts/vectors.py` hold the same implementation twice: `TEMPLATE.read_text().replace("__DATA__", blob)`, the `</` to `<\/` escaping, a `BaseHTTPRequestHandler` bound on `127.0.0.1` with `log_message` silenced, and a declared-schema validator over a JSON POST body. Ports 8931 and 8932 are the only difference that matters. Two adapters make the seam real, but doctrine forbids crossing it in both directions and says so outright: `build-context-token-vectors/scripts/CONTEXT.md` states the server pattern is "deliberately local rather than an import from `tools/`, which this package refuses", and `tools/CONTEXT.md` refuses skill logic the other way. The two contracts jointly forbid the shared module, which is a decision this item reopens rather than ignores. What forces the reopening is that the duplication is total rather than partial, and the `</` escaping is a security detail that must not drift between two copies. Either outcome is acceptable and both amend a contract: share it, or keep the copy and gate the two as identical. |
| R-57 | `TODO` | Narrow the vectors interface | B-023. `vectors.py` is 374 lines behind fourteen public functions and seven generated CLI knobs, owning corpus loading, embedding, SVD projection, cosine peers, EVoC clustering, a loopback HTTP server, terminal rendering, and the CLI. Interface nearly as complex as the implementation, which is what shallow means. `build()` is dead: `main()` calls `prepare()` and `analyze()` directly and nothing in the repo calls it. Three things leave rather than being reorganized: corpus loading to R-54, serving to R-56, the size measure to B-021. Embedding and clustering stay as internal seams the module's own tests cross, which is what makes swapping EVoC or the static model stop touching the CLI. Ships with the B-023 gate wiring, because narrowing an interface whose tests never run is not verifiable. |
| R-58 | `TODO` | Give the burndown an interface | Measured 2026-08-29 against `CLAUDE.md`'s own routing table. Mode A, work the burndown, reads `CLAUDE.md` + `ROADMAP.md` + `BUGS.md` + `CHANGELOG.md` + `UBIQUITOUS_LANGUAGE.md` = **73,000 B, roughly 18,250 tokens** on entry. Mode B is 52,421 B. For scale, the rail's entire six-skill walk is 37,405 B and `ask-matt`'s nine-skill walk is 36,267 B: entering Repo-Dev costs twice a full walk before any work starts. That is the Max failure GOAL.md names, in the repo's own routing table. Two doctrine statements are each true and jointly wrong: `CONTEXT.md` exempts these files from a byte budget because they are "append-only history ... which no running skill ever loads", and no *skill* does load them, but `CLAUDE.md` routes an *agent* to read all five. The reference release answers this structurally rather than by trimming, keeping 292 KB of human prose in `docs/`, one file per skill, outside the tree an agent walks. Shape here is a query surface over the burndown rather than five whole files: what is `IN-PROGRESS`, what is R-43, what broke last. Speculative until the split between agent-read and human-read state is decided, which is a GOAL.md question. |

## Main workflow goal

One rail from setup through production feedback, with irreversible work moving
right and operational evidence returning to planning.

| Family | SDLC phase | Place in the loop |
| --- | --- | --- |
| `kit` | **Day 0**, outside the loop | Nothing re-enters it per feature, which is why it is an on-ramp rather than a prefix. |
| `first` | **Plan** | Frames the problem, gathers evidence, selects direction, and records the approved contract before code. |
| `build` | **Code · Build · Test** | Three stages, one family: they share a blast radius — code and tests, nothing beyond them. |
| `land` | **Release · Deploy** | Split from `build` for the loop's own reason: a failed test costs a rerun; a failed deploy costs users. |
| `check` | **Monitor**, plus the Monitor → Plan edge | A return arc, not a stage, so it has no ordering position. It reads production and progress evidence back into `first`. |
| `fix` | **Operate**, incident response | The other return arc: it enters from outside, restores safe operation, and merges back into the earliest affected family. |

### Rail

The workflow rail. Goal and reasoning in [GOAL.md](GOAL.md); this is the
burndown for it. Ordered by what unblocks what.

| id | State | Item | Notes |
| --- | --- | --- | --- |
| R-31 | `DONE` | Write the goal down | `GOAL.md`, fogged. Names the three failure modes, both token-weight axes, and the six-family command surface. |
| R-32 | `DONE` | Settle the naming scheme | Bare on-ramps (`/kit`, `/fix`) plus four phase prefixes (`first-`, `build-`, `land-`, `check-`). Fifteen command names resolving to six skills, the flat names shipped as `alias_of` stubs. The prefix routes without a router command. |
| R-33 | `DONE` | Extend `max_file_bytes` to every skill directory | Stale on discovery via `/zoom-out`, 2026-08-28: every `CONTEXT.md` under `kit/`, `genesis/`, `knowledge/`, `ora/`, `silly/`, `starter-pack/`, `aesthetic/`, and every nested `scripts/`/`references/`/`agents/` already declares one -- 22 of 22 directories that carry a `CONTEXT.md`. The repo root correctly declares none, by its own contract: it holds append-only history no running skill loads, and a budget there would only get ratcheted, not enforced. |
| R-34 | `TODO` | Write `check` | Read-only, small weight, always safe mid-session. Two names resolve to it: `check-progress-goals` and `check-release-ontology`. No router command: the `check-` prefix does the routing that `/rail` would have. The rail itself is **not** here, see R-36. |
| R-35 | `TODO` | Ship the five `first-*` names as stubs over `genesis` and `aesthetic` | `genesis` already owns the burndown files, spec promotion, and the interview, so four of the five are `alias_of: genesis` plus mode rows for `idea-sketch` and `work-style`; `first-aesthetic` is `alias_of: aesthetic`. Do not write a second planning skill. |
| R-36 | `TODO` | Write `build`, `land`, and `fix` | `build` is a router over `ponytail` and `tdd` (`clean-code`, `qa-tests`, `pre-release`). `land` owns the burndown state machine (`asap-burndown`, `deployed-release`). `fix` is a bare on-ramp over `diagnosing-bugs`, bare because breakage arrives from outside the sequence, and it owns **the rail**: `fix-context-derail` plus the `rail` alias. `repair` stays owned by `kit`; the planned `fix` aliases are `rail` and `unstick`. Repairing a derailed context is a write and the same reflex as repairing code; `check` only reads and reports. |
| R-37 | `TODO` | Add `design` and `español` modes to `kit` | Its mode table already exists and already covers ten verbs. Two rows, no new skill. `kit [roadmap/domain rail]` is **not** one of them: that is R-41. |
| R-38 | `TODO` | Declare `phase` in frontmatter | Blocked on G-2: one field against six families, load-bearing for only `genesis` and `aesthetic`, whose names differ from their phase. Declare without enforcement and let the next skill decide whether a checker is worth it. `weight` was dropped as unworkable: families are cut by phase and their sections differ in cost, so one number per skill would be false for four of six. |
| R-43 | `TODO` | Index `collection.yaml`, and add the sources it is missing | Name the top skills and the leader words inline. Blocked on a real gap first: only `ponytail` is a manifest entry. `ask-matt` arrives incidentally through the bare `mattpocock/skills` line, and **`poteto` is in no manifest at all** — nor are `poteto-mode` and `zoom-out`, both of which this scheme drives. A leader word that is not a source cannot be indexed, and a clean install produces a rail with holes in it. |
| R-45 | `TODO` | Teach `alias.py` two more stub kinds | Today `stub()` emits one shape: "another name for X, read its SKILL.md". Anchor aliases need "read X/SKILL.md **§ Section**" and ghost-argument aliases need "read X/SKILL.md and run it with `asap`". One line each in `stub()`, plus a field to carry the section or the argument. The gate already insists a declared name is unique and reachable, so nothing else changes. |
| R-46 | `TODO` | An approve-features gate | Step 2 of the summary workflow, between `first-idea-sketch` and `build`. Nothing in the scheme owns it: sketching produces options and building consumes a decision, and the moment the decision is taken is unrecorded. Likely a `first` section, not a name of its own. |
| R-47 | `TODO` | A legibility gate on what `build` hands back | "Powerful clean code **for blind no coders**" is an acceptance criterion in the workflow and nothing checks it. A green test run is not evidence the deliverable is readable by the person who cannot read the code. Decide what would be. |
| R-44 | `TODO` | Two prompt files, not skills | `check-user-metrics` and `check-production-health` ask about a deployed product, not about building one, and nothing routes to them. Pasteable text costs zero description tax. |
| R-48 | `DONE` | Audit invocation context cost | `token_bench.py` had counted user-invoked descriptions as always loaded. It now assigns context cost only to model-invoked skills and reports invocation kind. The earlier 1.45x finding was invalid; description length remains a signal-density concern, not an always-on tax for user-invoked skills. |
| R-49 | `TODO` | Keep the rail routerless, and say why in `SPEC.md` | Same benchmark: `ask-matt/SKILL.md` is 11,491 bytes, **35% of its own flow**, loaded before any work to answer "what should I run". The prefix scheme buys that back on every walk. Record it as a constraint rather than an accident, or a future session will helpfully add the router back. |
| R-50 | `IN-PROGRESS` | Build the deterministic inference context compiler | [Promoted contract](docs/SPEC/INFERENCE_CONTEXT_COMPILER.md). Vertical slice landed in `aesthetic/scripts/direction_context.py`: tagged candidates, one estimated tokenizer profile, priority admission, pass budgets, the `generation` proof gate, a JSON trace that replays byte for byte, and a local attempt record. Both channels now drop the design workspace and the attempt store. `tools/trace_preview.py` renders one trace as a page that tokenizes it with Transformers.js and tags every token by the priority of its chunk; on this repository's `proposal` pass `Xenova/gpt-4` charges 8,013 tokens against an 8,818 `bytes/4` estimate. `--serve` runs it as a review session on loopback: three independent controls per chunk (context utility, semantic group, contamination risk), one appended line per change carrying the exact token cost, replayed into the page on refresh, and `--review` reading them back as advice that edits nothing. The page, its dependency, its network access, and the reviewed tags are dev-only, and `server.cjs` is untouched. `.claude/skills/check-transformers-neural-network/` starts it in one command and is itself fog. Remaining: declarations for every indexed skill, an exact tokenizer profile inside the Python compiler, held-out measurement of tokens per accepted result, and the advisory ranker. Index every skill package by invocation path and workflow context; compile tokenizer-profiled, pass-budgeted context with user corrections first and a cheap-proof gate before expensive inference. The neural ranker is dev-only and advisory. Prove improvement by tokens per accepted result without losing required context, and keep every dataset, checkpoint, cache, and preview out of both published channels. |
| R-51 | `IN-PROGRESS` | Port harness-core to one tested Python file | `pony.harness.sh` was 463 lines of bash needing `yq` on the PATH before it could answer `--help`, with no tests and a second installer for Windows. `harness.py` is 305 lines, standard library only, and `collection.toml` reads through `tomllib` with no dependency at all. Both emit byte-identical `npx skills add` commands for all 22 sources; 10 tests cover the manifest, the selection, the install specs, MCP fan-out, and append-without-losing-comments. The checkout is `~/.harness-core`, matching the repo it clones. Remaining: port `scripts/sync-skills.sh` and `onboard.sh` for real Windows parity, then delete the bash. Lives in harness-core, not here; `kit/SKILL.md` is the only file in this repo that names it. |
| R-39 | `DONE` | Close the SDLC loop | The Main workflow goal now maps `first`/`build`/`land` to Plan through Deploy, `check` to Monitor and the Monitor → Plan edge, and `fix` to Operate and incident response. `kit` remains Day 0 outside the feature loop. Implementation remains in R-34 and R-36; the topology is settled. |
| R-40 | `TODO` | Measure the host's actual enabled collection | The earlier 15,300-token estimate counted user-invoked descriptions that Claude does not expose to the model. Inventory enabled, model-invoked skills per host before pruning anything; installed file count alone is not context load. |
| R-41 | `TODO` | Write the rail down as a `CLAUDE.md` import | Four proposed commands (`FIRST-take-note`, `FIX-context-derail`, `kit [domain rail]`, `FIRST-work-style`) are one state file. Clearing context fog by running a command is backwards: the fog is the absence of a file that should have loaded at session start. Fixed, known bytes, zero commands. |
| R-42 | `TODO` | Move the measurements off the command surface | `CHECK-tokens-rail` becomes a `statusLine`; `DO-burndown` becomes a stop hook. Both are free and continuous where a command is expensive and forgettable, and this is what "asynchronous and nonblocking" means concretely. Neither `hooks` nor `statusLine` is configured on this machine today. |
| R-59 | `DONE` | Make the graphics loop a skill, not a handoff document | The loop's ordering and recovery rules lived in a pasted markdown file. `graphics_flow.py` computes one next action from the artifacts on disk and `text_to_graphics.py status` prints it with its reason, so the prompt flow is a tested table rather than prose. The module now names no room: positions and palettes moved to the scene spec and manifest, and a second fixture proves it. `compile` reads the corpus tags and the inventory it always claimed to read. AVGE stays the procedural adapter; `iso_svg.py` is rung 2b for when no MCP is authorized. |

### Design workflow epics

The domain-neutral skill workflow in
[`aesthetic/references/platform-support.md`](aesthetic/references/platform-support.md),
ordered as a burndown. Requirement ids are primary-owned by exactly one epic;
an epic is `DONE` only when its mapped entries pass `support_contract.py` with
real evidence. A missing credential or compatible interface is `BLOCKED`, not
done by documentation.

| id | State | Family | Epic | Exit evidence |
| --- | --- | --- | --- | --- |
| E-01 | `DONE` | `kit` | Support contract | `DES-01` through `DES-17`, the official-first fallback ladder, three test layers, and publication controls are specified and enforced by `support_contract.py`; focused and full aesthetic unit tests pass. |
| E-02 | `TODO` | `first` | Project brief and canonical design contract | `DES-09`: a non-coder can establish domain, stack, scope, selected outputs, and versioned deterministic `DESIGN.md` blocks from clean indexed repo context. |
| E-03 | `TODO` | `first` | Inspiration and component discovery | `DES-01`–`DES-04`: Pinterest, Dribbble, Instagram, and repo-native UI-library adapters retain rights and provenance and pass fixture, credentialed, and canary checks where external. |
| E-04 | `TODO` | `first` | Editable design workspaces | `DES-05`–`DES-07`: Figma, product-specific Adobe, and Canva operations pass through official interfaces first, with every fallback labeled and evidenced. |
| E-05 | `TODO` | `build` | Blind operator control and time travel | `DES-08`: plain-language preview, compare, restore, and undo work without requiring Git vocabulary; mutations remain attributable and recoverable. |
| E-06 | `TODO` | `build` | Sketch-to-production implementation | `DES-10`–`DES-12`: project-native architecture turns sketches into semantic, responsive, accessible production components rather than pixel replicas. |
| E-07 | `TODO` | `build` | Product screenshot TDD | `DES-13`: interaction, accessibility, viewport, overflow, screenshot baseline, and human visual review evidence is retained against an exact revision. |
| E-08 | `TODO` | `land` | Observable deployment | `DES-14`: project-scoped static or full-stack IaC deploys with health, logs, metrics, dashboard, canary, and rollback evidence. |
| E-09 | `TODO` | `land` | Relevant deliverables and publication | `DES-15`–`DES-17`: only selected documents, social/data files, editable mockups, and app outputs are built; each passes its format checks, and external publishing records approval, idempotency, receipt, and recovery. |

The cross-cutting `check` phase reads this table and the support manifest. The
`fix` phase returns the first failing epic to `TODO` or `BLOCKED`; neither phase
creates PASS evidence by assertion.

## Someday

| id | State | Item | Notes |
| --- | --- | --- | --- |
| R-16 | `TODO` | Enforce the ubiquitous language | `UBIQUITOUS_LANGUAGE.md` defines 30 terms with banned synonyms and nothing verifies it. A checker would make the document load-bearing. |
| R-17 | `TODO` | Automate the verification loop | Four commands, all manual, no CI. Fine while one person runs them; a trap the moment two people do. |
| R-60 | `TODO` | Build the superpowers companion agent app | Self-built companion for this repo, not vendored from brainstorming-skill. HTML interactions that change values (inputs, sliders, toggles, selects) must sync to file data durably: one append per value change, replay on refresh, ledger outside session dirs. `trace_preview.py` and `vectors.py` already do this for tokenizer review tags; this generalizes it to arbitrary form state. Lives under `.superpowers/` and satisfies `references/companion-contract.md`. Blocked on R-56 for the serving seam. |

## Working notes

**The published article is a static file.** Restarting the companion does not
regenerate it, so a render change is invisible until an `article` + `publish`
round writes a fresh one. Screenshotting the live URL after a code change shows
the *old* article and makes any fix look like it did nothing. This has cost two
sessions. Since R-27, `article` with no `--cohort` re-renders the page as it
stands, so that is the check:

```bash
python3 aesthetic/scripts/bootstrap_harness.py article \
  --project-root <project> --out /tmp/check.html
```

**The installed copy does not sync itself.** Propagate `aesthetic/` to
`~/.claude/skills/aesthetic` before running a real round against it.
