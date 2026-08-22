# Bugs

Live incidents. Each entry carries a one-sentence root cause, because a fix
written against a symptom comes back.

Status: `open` (reproduced, not fixed) · `fixed` (shipped with a guard) ·
`unverified` (reported, not yet reproduced) · `external` (outside this repo).

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

## B-009 · Round proposals reported as overlapping · unverified

**Symptom.** Reported repeatedly: proposals appear to render over one another.

**Investigation.** Measured the suspected comp directly:
`bodyScrollW == bodyClientW == 510`, all three cards inside the sheet. No
overflow. An overflow gate was built against this hypothesis and then deleted,
because the hypothesis was disproven and the gate would have added a second
Chrome render per comp against the loudest complaint about slow runs.

**Next.** Needs a screenshot of the specific round that overlaps.

---

## B-010 · Long runs produce weak output · open

**Symptom.** The loudest complaint and the least mechanical.

**Contributing causes fixed so far.** Uncapped cohort size, cross-round variant
accumulation, and the shared Chrome/qlmanage timeout.

**Next.** What remains is a craft question about the design loop. Judge it
against a fresh round now that the rendering defects above are gone, rather
than assuming it is still true.
