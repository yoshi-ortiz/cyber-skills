# Bugs

Live incidents. Each entry carries a one-sentence root cause, because a fix
written against a symptom comes back.

Status: `open` (reproduced, not fixed) · `fixed` (shipped with a guard) ·
`unverified` (reported, not yet reproduced) · `not reproducible` (measured
against a real project and absent) · `superseded by <id>` (real, but the
useful form of it lives elsewhere) · `external` (outside this repo).

Fog. Lives on `dev`, never published to `main`.

---

## B-001 · Slideshow reads as cluttered · fixed

**Symptom.** Reported across several sessions. The lightbox looked cramped and
undesigned, and successive spacing fixes appeared to change nothing.

**Root cause.** The lightbox `<dialog>` is appended to `document.body`, outside
`.dh-art` where `--s1..--s6` are declared, so every `var(--sN)` in the lightbox
resolved to nothing and the shell computed `padding:0`. The spacing edits meant
to fix it were themselves the thing being discarded.

**Fix.** Redeclare the scale on `dialog.dh-lb`. Measured before: padding `0px`,
bar margin `0px`, strip margin `0px`. After: `40px`, `24px`, `24px`.

**Guard.** `test_the_lightbox_declares_the_spacing_scale_it_uses`.

---

## B-002 · Comps render corrupted and overlapping · fixed

**Root cause.** Every embedded comp shared one `@scope` root, so two comps
reusing a class name (`.title`, `.mini`) collided and whichever rendered last
won for every comp on the page.

**Fix.** A per-element scope class derived from the element id.

**Guard.** `test_comp_css_scope_is_unique_per_element_not_shared_globally`.

---

## B-003 · Too many proposals for one element · fixed

**Root cause.** The variant cap counted only the current cohort, so a family
grew one round at a time and never tripped it. A real ledger reached seven live
drawings under one `family.tab`.

**Fix.** Count live descendants in the ledger, not just the cohort. The refusal
names what is already standing so the agent can act on it.

**Guard.** `test_variants_accumulated_over_earlier_rounds_still_count`.

---

## B-004 · Status stuck "working" long after a run ended · fixed

**Root cause.** `lastAgent` cleared only on an explicit final `status --idle`
call or a four-hour timeout, and an interrupted run never reached the call.

**Fix.** Timestamp every push, treat a stale `active` as idle, sweep open tabs.

**Guard.** `test_active_status_goes_stale_after_the_configured_window`.

---

## B-005 · Status flipped to "waiting" mid-inference · fixed

**Root cause.** Self-inflicted by B-004. `AGENT_STALE_MS` was three minutes;
status is push-based, so silence is ambiguous between "run stopped" and "one
step is slow", and a single slow step tripped it.

**Fix.** Fifteen minutes, above the longest plausible step and below abandoned.

---

## B-006 · Nothing to do during a long inference · fixed

**Root cause.** Two separate causes, neither the one assumed. Scoring was
already fully live while `data-preparing` was set (no `pointer-events`, no
`disabled`, no `inert`) but the rows were dimmed to 72% so they read as
disabled. Separately, any publish broadcast an unconditional
`window.location.reload()` that destroyed in-progress input, and `publish`
stamps mtime with `os.utime` so even an unchanged republish fired it.

**Fix.** Stop dimming live controls, hash the screen so identical republishes
do not reload, and mirror the brief draft into `sessionStorage`.

---

## B-007 · Bare-SVG previews render with dead space · open

**Symptom.** Some slides show a large empty area around a small drawing.

**Root cause.** 62 elements in `keynote-performance` were recorded as bare
`.svg` previews before the gate that now refuses them. Their artwork carries a
full-bleed background rect with content occupying only part of the canvas. The
lightbox renders exactly what the file contains; this is source art, not layout.

**Next.** Redraw in HTML/CSS and re-`shoot`. Find them with
`bootstrap_harness.py audit-svg --project-root <project>`.

---

## B-008 · Chrome headless unreliable, crash dialog reappears · external

**Symptom.** GPU process crashes mid-render; the macOS crash dialog returns.
Incident family `230C110D-8BAC-4EB8-9110-1936E00089B1`.

**Assessment.** Originates outside this repo, on macOS 26 beta. Several reports
traced to a separate Cursor-driven automation loop rather than to this skill.

**Mitigation shipped.** Chrome now has its own 12s budget instead of sharing
qlmanage's 45s, so a flaky render costs roughly a third as much.

---

## B-009 · Round proposals reported as overlapping · not reproducible

**Symptom.** Reported repeatedly: proposals appear to render over one another.

**Measured, 2026-08-22**, against the real `keynote-performance` ledger (26
elements, 27 rendered rows, served over HTTP at 1280px). Zero overlapping
pairs among rows that actually paint, and nothing covered by another element.

**Why it keeps looking real.** A naive `getBoundingClientRect()` sweep reports
six overlapping pairs, 1050px wide and 10-154px tall. Every one is a phantom.
The backlog is the only folding zone, and its 14 rows sit inside a closed
`<details class="dh-acc">`, whose contents are display-locked under
`content-visibility: hidden`. Locked subtrees still return plausible rects, so
the rows appear to be 154px tall inside a 109px box and to "escape" it. They
never paint. Filtering by
`checkVisibility({contentVisibilityAuto: true})` drops 14 of 27 rows and every
overlap with them.

The earlier `510` figure was the same class of error on the other axis: 510 is
the comp's own internal width, not the page's. A comp is 510px scaled by
0.184 into a ~94px thumbnail.

**Conclusion.** Two investigations have now produced a confident wrong answer
from the wrong measurement, and one of them built and deleted a guard over it.
Do not reopen this on a rect sweep. Settle it with visibility-filtered rects
plus `elementFromPoint`, or with a screenshot of the specific round — and if
the report recurs, get the screenshot first.

---

## B-010 · Long runs produce weak output · superseded by B-017

**Symptom.** The loudest complaint and the least mechanical.

**Contributing causes fixed so far.** Uncapped cohort size, cross-round variant
accumulation, and the shared Chrome/qlmanage timeout.

**Judged, 2026-08-22**, against the delivered artwork in `keynote-performance`
rather than against the ledger's old scores. The output is not generically
weak, and this entry is too vague to act on.

The harness's own probe (`measure_screen.js`) over the rendered article: 27 of
27 elements carry a visible graphic, no dead shots, worst contrast 4.61:1, no
unreadable rules. The 158 sub-9px text nodes it counts are all *inside* comps,
none in the chrome — a comp is 510px scaled by 0.184, so its "5px" type is
27px in the artwork. A scaling artifact, not a legibility defect.

The artwork itself carries a real system: a pink ground, a dot-matrix display
face, a black spine rail with vertical type, punched-binder edge, numbered
tabs. `interior.pairs.stacked-i2.ring-mark` executes it cleanly. It would read
as this subject with the branding removed, and would not fit an unrelated
product unchanged — the two criteria SKILL.md's done gate calls the design bar.

**What is actually wrong** is one nameable craft defect, now filed as B-017.
The user's 1-star scores are justified by that defect, not by a systemic
weakness. Closing the vague form so it stops absorbing every complaint.

---

## B-011 · Round proposals overstep their parent Subject · fixed

**Symptom.** A Direction or Epic proposed for one Subject (the specific
product or page a round is working on) starts reasoning about, or restyling,
elements that belong to a different Subject instead of staying confined to
its own parent product.

**Root cause.** `SKILL.md`'s Done gate already names the failure ("does not
fit an unrelated product unchanged"), but nothing names or checks the
containing boundary itself. Round scope inference has no explicit fence: an
agent inferring what a Direction implies can reach into a sibling Subject's
epics because no step requires resolving to exactly one Subject before
proposing anything.

**Fix.** `check_round_stays_in_scope` in `bootstrap_harness.py` refuses a
cohort spanning more than one parent item, read off the dotted id's first
segment by `parent_item_of`. Called from `render_article` beside
`check_cohort_size`, so it fires for every caller and not only the CLI. No
schema change and no migration: the id convention already carried the object.
Deliberately no `--asks` escape — that flag answers the foundation-span
check, which is about a round that needs explaining, not about a round that
should be two rounds.

**Guard.** `test_scope.py::ARoundMustStayOnOneObject`, plus
`test_adopt.py::test_asks_does_not_buy_a_round_out_of_its_parent_item`
end-to-end. Two existing tests in `test_adopt.py` had to be rewritten: their
fixture cohort spanned three foundations *and* three parent items, so
whichever check ran first was the one being tested. They now use a cohort
under one `folder` parent, which reaches the foundation check with scope
already satisfied.

---

## B-012 · Repo-dev vocabulary leaks into Design-Inference Context · fixed

**Symptom.** An agent zoomed out over the repo picks up software-triage
vocabulary ("root cause," "guard," "budget," "known debt") while doing design
work, with nothing marking which files belong to which context.

**Root cause.** `.audit/aesthetic-output-quality.tsv`, this file, and
`ROADMAP.md` sit at the repo root, outside every directory's
`admits`/`refuses` contract. `.audit/aesthetic-output-quality.tsv` is an
append-only ledger shaped exactly like the skill's own
`editorial-events.jsonl`, so its rows can be mistaken for Scope Events.
`aesthetic/AGENTS.md` sits inside the skill root beside `SKILL.md` (admitted
by `aesthetic/CONTEXT.md` itself) and is kept out of `main` only by
`tools/fog.py`'s fog list — on `dev` it is fully in reach of a
Design-Inference Context session.

**Second root cause, and the reason nothing caught this.** `contracts.py` is
the tool that should have. Its `walk()` skipped hidden directories by testing
`d.name` alone, which is not ancestor-aware: `.git/refs/heads` is named
`heads`, so a repository-root run descended into git's internals and reported
240 directories. Scoped to `aesthetic/` the bug never showed — which is
exactly why the checker was only ever pointed there, and why the repo root
went uncontracted.

**Fix.** `walk()` now tests every part of the path relative to the root, so
`--root .` at the repository root reports 13 directories instead of 240. On
that footing, three contracts were added: a root `CONTEXT.md` declaring the
release package, its skill index, and the two contexts — naming `BUGS.md`,
`ROADMAP.md`, `CHANGELOG.md`, and `.audit/` as Repo-Dev Context, never
Preference Evidence or Golden Rule Evidence — plus `ora/CONTEXT.md` and
`assets/CONTEXT.md`. The root contract ships: the repo is one release package
indexing several skills, so the index is worth carrying to `main`.

**Guard.** `test_contracts.py::HiddenDirectories`, including the inverse case
— a root that is itself hidden must still walk its visible children.
`python3 aesthetic/scripts/contracts.py --root .` is now the whole-repo check.

---

## B-013 · P0 · Long runs overstep Round Scope and burn tokens for weak output · open

**Symptom.** An inference run takes too long, visibly reasons past the
element it was asked about, and still lands on a minimal, generic design —
tokens spent with nothing usable to show for it.

**Root cause.** Three independent gaps compound:

1. `editorial_workflow.py`'s cohort check (`validate_art_direction`,
   [scripts/editorial_workflow.py:299-308](aesthetic/scripts/editorial_workflow.py))
   only enforces size (3–6 unique ids) and, once anything is ranked, that the
   cohort stays inside already-known preference ids. It never checks that a
   cohort's elements share one epic — `validate_editorial_spec`
   ([scripts/editorial_workflow.py:335-366](aesthetic/scripts/editorial_workflow.py))
   maps each element to exactly one epic but has no Subject/parent-item field
   at all, so nothing stops a Direction from spanning unrelated epics. This is
   the code-level version of B-011/R-21 (Round Scope).
2. `golden_rules.py --min-coverage` ([scripts/golden_rules.py:201-218](aesthetic/scripts/golden_rules.py))
   is a single-shot evaluator with no memory between calls. SKILL.md's "Fix a
   rejected spec; never bypass the gate" means the retry loop lives entirely
   in the agent's own behavior — there is no code-enforced retry cap and
   nothing requires a retry to narrow scope rather than re-attempt the same
   over-broad cohort.
3. `MAX_VARIANTS_PER_IDEA = 3` ([scripts/bootstrap_harness.py:3656](aesthetic/scripts/bootstrap_harness.py))
   caps *live* wallpaper per idea, but nothing caps how many epics/elements a
   single round's `direction`/`observe`/`seed` pass may touch before that
   per-idea cap ever applies — a run can spread thin across many parent items
   and still pass every existing check.

**Partial fix shipped.** Gap 1 is closed by `check_round_stays_in_scope`
(B-011): a round can no longer span parent items, which is the breadth that
made these runs long. Gap 3 is unchanged but far less reachable now that a
cohort must sit under one object.

**Still open — gap 2.** There is no code-enforced retry cap. `golden_rules.py`
remains a single-shot evaluator, and "fix a rejected spec; never bypass the
gate" is still SKILL.md prose, so nothing requires a retry to narrow scope
rather than re-attempt the same spec.

**Measured, 2026-08-22.** The harness is not the cost. A full `article` render
over the real 26-element `keynote-performance` ledger takes **0.19s**. Whatever
makes a run long is model inference, not tooling — so the lever is the retry
cap (R-24) and the scope fix already shipped, and there is nothing to optimise
in the pipeline itself. Do not go looking for slow code here.

**Guard.** Scope only: `test_scope.py`. Nothing guards retry cost yet.

---

## B-014 · Status chart accumulates squares instead of grouping by mutation origin · fixed

**Symptom.** The published article's element grid keeps growing across
rounds; near-identical iterations of the same idea each keep their own
permanent square instead of collapsing under the idea they came from.

**Root cause.** `render_feedback_controls`
([scripts/bootstrap_harness.py:1989-2045](aesthetic/scripts/bootstrap_harness.py))
groups every live row by `foundation_of(element)` — palette, typography,
composition, etc. ([scripts/bootstrap_harness.py:186-196](aesthetic/scripts/bootstrap_harness.py))
— or by lifecycle via `GROUP_OF`
([scripts/bootstrap_harness.py:111-117](aesthetic/scripts/bootstrap_harness.py)),
never by mutation lineage. A supersede chain already exists in the data model
— `decide --supersedes` / `supersede` write `state="superseded"` and a
`supersededBy` back-reference
([scripts/bootstrap_harness.py:661-668](aesthetic/scripts/bootstrap_harness.py),
[scripts/bootstrap_harness.py:819-843](aesthetic/scripts/bootstrap_harness.py))
— but `live = [e for e in decisions["elements"] if e["state"] in GROUP_OF]`
still includes `superseded` elements (mapped to the `"rejected"` group), so
every retired mutation keeps rendering as its own card, just reordered to the
bottom ("Discarded last" per `SKILL.md`), forever. `MAX_VARIANTS_PER_IDEA = 3`
([scripts/bootstrap_harness.py:3656](aesthetic/scripts/bootstrap_harness.py))
caps concurrently-*live* variants of one idea but explicitly excludes
already-superseded ones from that count, so the discarded pile is unbounded.

**Fix.** The strip is now built from lineage roots. `lineage_root_of` follows
`incumbent_of` up the id chain to the original idea; each lineage emits one
bar, and `speaks_for` picks which drawing reports it — this round's ask
first, so the asked element keeps its `?` and outline, then the standing
drawing, best execution first. The bar carries `data-variants="N"` and says
so in its `aria-label`, so the history stays reachable through the existing
hover card and slideshow instead of being repeated across the strip.

This is a rendering change only: no ledger migration, no state rewrite, and
a test asserts the ledger is byte-identical before and after. The round zone
has grouped variants under their incumbent since it was written
(`render_article`'s idea-grouping); this applies the same grouping to the
strip that summarises the whole ledger.

**Guard.** `test_article.py::TheChartCountsIdeasNotAttempts` (a three-deep
chain draws one bar; the standing drawing speaks, not the best-scoring
retired attempt) and `test_scope.py::ALineageIsFollowedToItsRoot`.

---

## B-015 · Companion header/bottom bar show a stale or wrong agent identity · fixed

**Symptom.** The companion's header and bottom-bar aids don't reflect which
app is actually running the round; the identity looks hardcoded to "Cursor",
and its link target doesn't match the current session.

**Root cause.** Two separate paths exist and neither is Claude-Code-aware or
per-run-fresh:

1. `agent_context_from_env`
   ([scripts/bootstrap_harness.py:399-405](aesthetic/scripts/bootstrap_harness.py))
   only reads `CURSOR_AGENT_URL`/`AGENT_URL`/`CURSOR_AGENT_NAME`/`AGENT_NAME`/
   `CURSOR_MODEL` — Cursor-specific names, nothing for any other host — and is
   only called from `open_board` ([scripts/bootstrap_harness.py:2272](aesthetic/scripts/bootstrap_harness.py)),
   not from `render_article` at all.
2. `render_article` ([scripts/bootstrap_harness.py:3819-3822](aesthetic/scripts/bootstrap_harness.py))
   resolves identity as `agent_url.strip() or stored_url` /
   `agent_name.strip() or stored_name`, where `stored_url`/`stored_name` come
   from `companion_agent(project_root)` — whatever a previous run persisted
   via `save_companion_agent` into `project.json`
   ([scripts/bootstrap_harness.py:390-397](aesthetic/scripts/bootstrap_harness.py)).
   If `--agent`/`--agent-url` aren't passed fresh on the current `article`
   call (SKILL.md only shows them as a placeholder example, `"<App | Model>"`,
   never a live-detection instruction — [SKILL.md:116](aesthetic/SKILL.md)),
   the header silently keeps showing whatever was saved by an earlier run
   under a different app, indefinitely.

**The deeper cause, found while fixing it.** The URL and the name were
resolved by two independent `or` chains, so they could come from different
runs. That is literally what the real `project.json` held: a
`companionAgentName` of `Claude Code` beside a `companionAgentUrl` of
`cursor://anysphere.cursor-deeplink/prompt`. Neither value was wrong on its
own. The pairing was.

**Fix.** `resolve_agent` takes identity whole from the first source that says
anything, in order: explicit flag, live environment, stored value. Both halves
always come from the same place. `agent_context_from_env` gained an
`AGENT_HOSTS` table so a host that ships no deep link still names itself
(`CLAUDECODE` was invisible to it). `render_article` calls it too, not just
`open_board`.

Fixing this surfaced a latent crash: `save_companion_agent` read `project.json`
without checking it exists, which never fired while only Cursor was detected
and the save path stayed unreached on a bare directory. It now returns instead.

**Guard.** `test_article.py::TheHeaderNamesWhoIsActuallyRunning`, including the
mismatch case and the missing-project case.

---

## B-016 · Manifesto questionnaire and corpus tagging never appear · fixed

**Symptom.** The article never shows the manifesto/brief questionnaire or
any way for the user to tag reference material, even on projects that should
have both.

**Root cause — two distinct gaps:**

1. **Brief (manifesto) is built but never invoked.** `render_brief`
   ([scripts/brief_workflow.py:333-345](aesthetic/scripts/brief_workflow.py))
   returns `""` whenever `load_brief(project_root)` is `None` — i.e., whenever
   `brief start` was never run for this project — and `render_article` treats
   an import failure the same way, silently
   ([scripts/bootstrap_harness.py:3977-3987](aesthetic/scripts/bootstrap_harness.py)).
   `SKILL.md` never once names `brief_workflow.py` or a `brief start` step in
   its Loop; its only "brief" language is the unrelated *preference* brief
   from `editorial_workflow.py preferences` ([SKILL.md:53,58](aesthetic/SKILL.md)).
   The feature is fully implemented and tested (`test_brief_workflow.py`) but
   orphaned from the doctrine that actually drives a run — this is not a
   render bug, it is a wiring gap. Tracked as **R-19**.
2. **Corpus tagging has no user-facing surface at all.** `companion/frame-template.html`,
   `companion/helper.js`, and `companion/server.cjs` contain zero references
   to "corpus" — every corpus concept (`observe`, `seed`, `corpus.json`) is
   CLI/backend-only in `editorial_workflow.py`, driven by the agent reading a
   local folder path, never by the user tagging anything in the browser.
   There is nothing to fix here because nothing was built. Tracked as
   **R-20**.

**Fix.** Both halves shipped. Corpus tagging is `scripts/corpus_tags.py`
(R-20, absorbing R-11 and R-12). The manifesto is wired by `ensure_brief`,
called from `open_board` (R-19): the module was always complete, and nothing
had ever created a brief for `render_brief` to render. `adopt` now folds the
brief inbox in alongside the tag inbox.

The tagging module avoids repeating this bug's own lesson. It is reached
through `bootstrap_harness.py adopt`, a command `SKILL.md` already names, so
it costs zero bytes of an entry point that was sitting at exactly its 7250
budget — and a module nobody invokes is the thing that broke here.

**Guard.** `test_corpus_tags.py`, including
`TheSkillActuallyInvokesIt::test_bootstrap_adopt_folds_in_corpus_tags`, which
fails if the wiring is ever removed.

---

## B-017 · Circular ring type breaks at the lower arc · open

**Symptom.** In `cover.ring.kicker.antetitulo-arco.sin-lavado`, the circular
`ROL · DE · LENGUAJE` ring reads correctly across the top and right, then at
roughly the 7-to-8 o'clock position the glyphs render inverted, in the accent
red rather than the ink, and overlapping each other. That arc reads as damage,
not as type.

**Why it matters.** This is the concrete defect behind the vague B-010. The
element carries a thumb up and a 1-star score — the user is saying the idea is
right and the drawing is not there yet, and they are correct: the direction is
strong, one arc of it is broken. Its sibling `interior.pairs.stacked-i2.ring-mark`
executes the same system cleanly, so the system is not at fault.

**Not yet root-caused.** Likely per-glyph rotation past 180° without the
counter-rotation that keeps letters upright on the lower half of a circle, but
the comp has not been opened and read. Do that before proposing a redraw.

**Guard.** None yet, and a deterministic one may not be possible — this is
craft, judged in the render.

---

## B-018 · Re-rendering the current article is refused as a round · fixed

**Symptom.** `article` with no `--cohort` is refused whenever the project
carries polish debt:

```
error: 10 element(s) carry a thumb up and a low score [...] and this round improves none of them
```

**Root cause.** `check_round_earns_its_place` treats an empty cohort as a round
that proposes nothing while polish work waits. It ends with
`touches_polish = any(... for c in cohort)`, which is vacuously `False` for an
empty cohort, so the refusal fires. The check is right about rounds and wrong
about this case: asking for no elements is not proposing new ideas over
unanswered feedback, it is redrawing the page as it already stands.

**Cost.** There is no way to regenerate the article after a code change without
inventing a cohort. `ROADMAP.md`'s working note already documents a
`render_article` snippet to work around exactly this.

**Fix.** `check_round_earns_its_place` returns early on an empty cohort,
beside the existing `if not polish` guard. The ROADMAP workaround snippet can
go: `article` with no `--cohort` now renders the page as it stands.

**Guard.** `test_article.py::ReRenderingIsNotARound`, which also asserts a
real round still has to answer the polish debt.

---

## B-019 · Chrome profiles are created per run and never removed · not reproducible

**Symptom.** `keynote-performance/design/review/` holds **184 MB** across 12
abandoned `_chrome-profile*` directories. The actual deliverables in that
folder — 15 review PNGs — total about 1 MB, so 99.5% of it is litter, sitting
inside the user's project rather than a temporary directory.

**Root cause.** Each Chrome invocation gets a fresh profile directory beside
the output and nothing removes it afterwards. The suffixes (`-cdp`, `-live`,
`-live2`, `-live3`, `-live4`, `-shoot`, `-space`) show several code paths each
minting their own.

**Suspected link to B-008.** That entry blames macOS 26 beta for GPU crashes
and a returning crash dialog. Twelve cold profiles in one project is also a
plausible contributor: a fresh profile skips warm caches and re-runs
first-launch work on every shoot. Worth re-testing B-008 with a single reused
profile before treating it as purely external.

**Already fixed in code; the 184 MB is residue.** The skill makes exactly one
Chrome invocation, at `bootstrap_harness.py:1594`. It already uses
`tempfile.mkdtemp(prefix="dh-shot-")` and already removes it in a `finally`.
The string `_chrome-profile` appears nowhere in this repository, so the
current code cannot produce those directories. They are leftovers from an
earlier version or from the separate Cursor-driven automation loop B-008
names, dated 2026-08-21 01:41-01:56.

**Action.** Nothing to build. The directories are inside the user's own
project, so reclaiming the space is their call, not a harness change.

---

## B-020 · Harness hid installer security assessments during sync · external

**Symptom.** `kit sync` / `harness.py sync`, 2026-08-29. `npx skills add`
prints Gen, Socket, and Snyk assessments before installation, but the harness
passes `-y`, ignores the table, reports the source as `ok`, and fans the result
out to every agent directory. The captured run assessed 77 skills; 25 were not
clean. Two had Snyk Critical Risk (`switch-project`,
`run-acceptance-tests`), three had Gen High Risk (`shellcheck`,
`ui-ux-pro-max`, `windows-builder`), four carried Socket alerts, and nine had
Snyk High Risk.

**Root cause.** The harness discarded the installer's assessment output, so
operators could not see findings during `sync` or `add`. A first attempted fix
mistakenly made findings and missing assessment tables fatal, which violated
the collection contract: every declared source must still be installed and
propagated. The original report singled out `graphify`; parsing the whole log
showed that premise was false.

**Upstream fix.** `harness-core` runs each installer once against the real
agent environment, streams and captures its output, and reports every non-clean
Gen, Socket, or Snyk row as a security advisory. Findings remain visible but do
not convert a successful installation into a failure or suppress cross-agent
fan-out. Actual installer and fan-out process failures remain fatal. The
upstream audit is repository-and-skill level, not commit attestation.

**Guard.** `test_risky_install_succeeds_and_fans_out` runs the real harness CLI
against a fake risky `npx` result and proves the assessment is reported while
the real install and `sync-skills.sh` both execute successfully. Parser checks
cover ANSI output and names with spaces; absent tables produce no advisory.

## B-021 · Dashboard reports character counts as bytes · open

**Symptom.** `build-context-token-vectors/scripts/vectors.py:177` emits
`"bytes": len(texts[i])` into every per-skill record the dashboard renders.
`texts[i]` is the frontmatter-stripped body as a `str`, so `len()` returns
characters. Every non-ASCII skill is under-reported, and `ora/` is the Spanish
voice skill, so the error lands on a shipped skill rather than a hypothetical
one. The number is labelled `bytes` in the record, in the page, and in the
terminal renderer.

**Root cause.** Size is measured four ways in four places and nothing owns the
definition. `aesthetic/scripts/contracts.py` uses `path.stat().st_size`, raw
disk bytes including the frontmatter it exempts. `tools/token_bench.py` uses
`len(text.encode("utf-8"))` on both the description and the whole file.
`aesthetic/scripts/direction_context.py:149` uses
`-(-len(text.encode("utf-8")) // ratio)`, a ceiling division into token
estimate. `vectors.py` uses `len()` on a `str`. Four things named bytes, four
scopes, and no module holds the one true measure, so a fifth caller will pick a
fifth meaning.

**Fix.** R-54. The corpus module returns the size alongside the record, counted
once as `len(text.encode("utf-8"))`, and every caller reads it rather than
recomputing. Fixing `vectors.py` alone would leave the other three disagreeing.

## B-022 · CLAUDE.md reports a gate count two short of reality · open

**Symptom.** `CLAUDE.md:27` reads "18/19 gates pass; `contracts` is red on
purpose (R-15, four files over the 30 KB budget)." Running
`python3 tools/check.py` on 2026-08-29 prints `18/20 gates pass` and
`failing: contracts, unit tests`. The unit suite reports
`Ran 444 tests` / `FAILED (failures=2, errors=2)`.

**Root cause.** The gate list in `tools/check.py:gates()` grew and the prose in
`CLAUDE.md` did not. Nothing checks the claim, so the file that routes every
Repo-Dev agent tells it the suite is one known-red gate away from green when it
is two, and the second red is undocumented. An agent reading `CLAUDE.md` to
decide whether the tree is clean gets a wrong answer from the file whose whole
job is routing.

**Fix.** Two halves, and only the second is durable. Name the unit failures and
either fix them or record them the way `contracts` is recorded. Then make the
count derivable rather than transcribed: `check.py` already knows its own gate
count, so `CLAUDE.md` should cite the command instead of a number, the same
argument `GOAL.md` makes for a re-runnable benchmark over a number in a
document.

## B-023 · The companion's live test runs in no gate · open

**Symptom.** `build-context-token-vectors/scripts/test_vectors_live.py` exists,
passes when invoked directly, and is executed by nothing. `tools/check.py`
names each `tools/test_*.py` individually in `gates()` and has no entry for it.
The unit gate is `unittest discover -s aesthetic/scripts`, which never descends
into `build-context-token-vectors/`, and the file is script-style
(`if __name__ == "__main__": test()`) rather than unittest, so discovery would
skip it even if pointed there.

**Root cause.** Three test conventions coexist with no rule saying which
applies where. `aesthetic/scripts/test_*.py` are unittest and found by
discovery; `tools/test_*.py` are script-style and found by being listed by
hand; `build-context-token-vectors/scripts/test_vectors_live.py` is
script-style and listed nowhere, which is the intersection that runs never. The
untested behaviour is not incidental: the test covers the tuning companion's
cross-origin refusal (`Origin: https://example.com` must 403), its unknown
parameter path (400), and that invalid input never reaches the `retune` seam.
Those are the security properties of a server bound on loopback.

**Fix.** R-57. Add it to `gates()` in the same shape as the `tools/` tests,
which is the smallest change, and record the convention so the next skill that
ships a test does not land in the same gap.

## B-024 · A saved dashboard offers Retune controls that post into nothing · open

**Symptom.** `build-context-token-vectors/scripts/dashboard.html` decides
whether tuning is available by sniffing the protocol:

```js
const live = location.protocol === "http:" || location.protocol === "https:";
$("applyTune").disabled = !live;
```

A page written with `--out` and then opened over any local static server, which
is the ordinary way to view a saved HTML file, satisfies that test. The Retune
controls render enabled and `POST /tune` into a server that is not there.

**Root cause.** Liveness is a property of the server that rendered the page,
and the page infers it from the client's URL scheme instead of being told. The
server already re-renders the page from in-memory state on every `GET /` under
`--serve`, so it is the one component that knows the answer and the one that
never says so.

**Fix.** `page(data)` takes the liveness flag and writes it into the data blob;
the client reads it rather than sniffing. One parameter, and it removes a
class of confusion rather than one instance of it.

## B-025 · Every `@container` rule in the ranking controls is dead · open

**Symptom.** `first/aesthetic/screen/controls.css` carries three container
queries that shape the scoring card at narrow widths -- `@container dh-row
(max-width: 980px)`, `@container dh-row (max-width: 380px)`, and a bare
`@container (max-width: 780px)`. None of them has ever applied. Measured on the
served companion:

```js
row.closest('.dh-feedback,[data-dh-controls]')   // null
getComputedStyle(row.parentElement).containerType // "normal"
```

**Root cause.** Two independent faults, either one sufficient. First, no
ancestor establishes a container at all: `container-type:inline-size` is
declared only on `.dh-feedback,[data-dh-controls]`, and `embed` lifts the rows
out of that wrapper into the project's own placeholder -- the file's own opening
comment describes this, and adding `[data-dh-controls]` to the selector did not
fix it because the placeholder is not that element either. Second, even with a
container present, `container-name: dh-row` is never set anywhere in the
codebase, so a query written `@container dh-row (...)` could not match a
container that has no name.

The cost is not one layout. It is that every narrow-width repair anybody writes
in this file is inert, verifies as "fixed" against a viewport `@media` rule
elsewhere in the same file that happens to fire at a similar width, and ships.
That has now happened at least twice.

**Fix.** Name the container and give the row a real one. `container: dh-row /
inline-size` on the row's parent is the shape the rules already assume, but the
parent is project markup, so the durable version is for `embed` to emit a
wrapper per row and set the container on it. An element cannot be its own query
container, so putting it on `.dh-fb` is not an option. Until then, prefer rules
that need no query: B-026's two fixes are both query-free for this reason.

## B-026 · The hero comp hand-authors SVG, so its own gate cannot run · open

**Symptom.** `bootstrap_harness.py audit-svg --project-root .` is red:

```
1 recorded preview(s) hand-author <svg>
  landing.hero.flow.foundation	design/landing-flow-hero.html
```

`shoot` refuses the comp for the same reason, so the one graphic in the round
never passes through `check_no_hand_authored_svg`.

**Root cause.** The comp draws its room bosses and signature items as inline
`<svg>`. That is not an accident and not the model inventing coordinates: it is
the user's recorded instruction on `landing.hero.flow.foundation` -- "the
graphic should be css first, and vectors for characters+items sprite sheets."
The sprite sheets half was never built, so the vectors still live in the page.

**Fix.** Extract the characters and items into referenced sprite files and point
at them with `<img src="...">`, which is what the instruction asked for and what
the gate wants. This is not mechanical: the rooms colour their walls with
`color-mix()` over a per-station `--plate-face` custom property, and custom
properties do not cascade into an `<img>`-referenced SVG, so each sprite either
bakes its palette or the theming moves. That is a design decision, and it
belongs to the cartoon round the user has already scheduled ("cartoons drawings
will need their own round"), not to a layout pass.

**2026-09-02.** `deliver.py` now refuses a cohort element whose preview
hand-authors `<svg>`, unless the user has already thumbed or scored it. That
was added after a round of hand-drawn cartoon characters shipped and was
rejected on sight: `shoot` had always refused such a comp, but delivery never
routed through `shoot`, and `audit-svg` printed its three violations and exited
0. `landing.hero.flow.foundation` carries a thumb, so it stays deliverable; any
NEW character work does not. Sprite extraction is therefore on the critical
path for the cartoon round, not optional to it.

## B-027 · The installed skill is a copy, so edits to it are silently lost · open (needs a human)

**Symptom.** `~/.claude/skills/aesthetic` is a symlink, which reads as a live
dev loop, but it points outside the repository:

```
~/.claude/skills/aesthetic -> ../../.agents/skills/aesthetic
```

`.agents/skills/aesthetic` is a full copy of `first/aesthetic`. An agent that
edits the path it is told is "the skill" changes the copy; `git status` in this
repository stays clean, every gate stays green, and the next `kit sync`
overwrites the work. This session lost one CSS fix that way and only found it by
diffing the two trees by hand.

**Root cause.** `c1bef2a "make the dev loop a symlink, not a channel"` made the
symlink, but aimed it at the installed channel copy rather than at
`first/aesthetic` in the working tree. The name says dev loop; the target is
still a channel.

**Fix.** Point `.agents/skills/aesthetic` at `first/aesthetic`, so editing the
skill through the path the agent is given edits the source under version
control. Until then, treat `first/aesthetic` as the only writable copy and sync
outward, never inward.

This one is not an agent's to run. It deletes a directory outside the
repository, so it needs a human who can see what is in there first:

```bash
rm -rf ~/.agents/skills/aesthetic
ln -s ~/Development/cyber-skills/first/aesthetic ~/.agents/skills/aesthetic
```
