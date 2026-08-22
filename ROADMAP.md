# Roadmap

Persisting bugs and unbuilt work in the `aesthetic` skill, recorded as identified
so a complaint that keeps coming back can be answered with a status instead of a
fresh investigation.

Status values: `fixed` (shipped with a regression test), `open` (reproduced, root
cause known, not fixed), `unverified` (reported, not yet reproduced), `deferred`
(understood and deliberately not built yet).

## How to verify anything here

The published article is a **static file**. Restarting the companion server does
not regenerate it, so a CSS or render change is invisible until an `article` +
`publish` round writes a fresh one. To check a render change without a real round:

```bash
cd aesthetic/scripts && python3 -c "
import sys; sys.path.insert(0,'.')
import bootstrap_harness as bh
from pathlib import Path
root = Path('<project>')
d = bh.load_decisions(root/'spec'/'design-harness')
bh.canonicalize_recorded_previews(root, d)
Path('/tmp/check.html').write_text(
    bh.render_article(root, d, set(), '', 'es', None, None, '', '', '', '', '', False),
    encoding='utf-8')"
```

This trap has cost two sessions. A screenshot of the live URL after a code change
shows the OLD article and looks like the fix did nothing.

## Fixed

| # | Bug | Root cause | Guard |
| --- | --- | --- | --- |
| 1 | Slideshow "ugly and cluttered" across several sessions | The lightbox `<dialog>` is appended to `document.body`, outside `.dh-art` where `--s1..--s6` are declared, so **every** `var(--sN)` in the lightbox resolved to nothing. The shell computed `padding:0` and every zone gap collapsed. Spacing edits aimed at this were themselves being discarded. | `test_the_lightbox_declares_the_spacing_scale_it_uses` |
| 2 | Comps corrupted, overlapping, misaligned | All embedded comps shared one `@scope` root, so two comps reusing a class name (`.title`, `.mini`) collided; last one rendered won for every comp on the page. | `test_comp_css_scope_is_unique_per_element_not_shared_globally` |
| 3 | Too many proposals for one element | The variant cap counted only the current cohort, so a family grew one round at a time and never tripped it. A real ledger reached 7 live drawings under one `family.tab`. | `test_variants_accumulated_over_earlier_rounds_still_count` |
| 4 | Status stuck "working" for hours after a run ended | `lastAgent` was only cleared by an explicit final `status --idle` call or a 4-hour timeout. An interrupted run never reached the final call. | `test_active_status_goes_stale_after_the_configured_window` |
| 5 | Status flipped to "waiting" mid-inference | Self-inflicted by the fix for #4. `AGENT_STALE_MS` was 3 minutes; a single slow step exceeded it and the bar told the user their turn had come while the agent was still working. Now 15 minutes, above the longest plausible step. | same as #4 |
| 6 | Rounds unbounded in size | The documented "3-6 element cohort" was prose only; nothing capped `len(cohort)` and the round zone never folds. | `test_render_article_refuses_a_cohort_past_the_limit` |

## Open

**Bare-SVG previews render with dead space.** 62 elements in `keynote-performance`
were recorded as bare `.svg` previews before the gate that now refuses them. Their
artwork carries a full-bleed background rect with content occupying only part of the
canvas, so the slide shows a large empty area. This is source art, not a layout bug;
the lightbox is rendering exactly what the file contains. Fix is to redraw them in
HTML/CSS and re-`shoot`. Find them with:

```bash
python3 aesthetic/scripts/bootstrap_harness.py audit-svg --project-root <project>
```

**Chrome headless is unreliable on macOS 26 beta.** GPU process crashes mid-render
and the OS crash dialog reappears. The harness already falls back to `qlmanage`, and
the Chrome attempt now has its own 12s budget instead of sharing the 45s one, so a
flaky render costs less. The crash dialog itself originates outside this repo. Reports
observed under this incident family: `230C110D-8BAC-4EB8-9110-1936E00089B1`. Several
were traced to a separate Cursor-driven browser automation loop, not to this skill.

**Round proposals reported as overlapping.** Reported repeatedly. Measured the
suspected comp directly (`bodyScrollW == bodyClientW == 510`, all three cards inside
the sheet) and found no overflow, so the earlier hypothesis is disproven and no gate
was added for it. Needs a screenshot of the specific overlapping round to locate.

## Deferred

These are understood and deliberately not built. They are features, not fixes, and
each is large enough that a rushed version would be worse than none.

**Project brief as a manifesto.** A deliverables-focused intake the user writes as a
project manifesto, living in its own collapsible article section, revisitable at any
time, with append-only change history. Should mirror the editorial burndown's
`editorial.json` + `editorial-events.jsonl` pattern. Must not disturb `loop.md`'s
existing "infer rather than interview, ask once" doctrine, which governs the
per-round design question and is a different surface.

**Deterministic corpus tagging.** `observe_corpus` currently tags items only
`image`/`text` by file extension. Wanted: a stable per-item classification of *why*
a reference was added, keyed by content hash so it is computed once and never
silently re-inferred. "Deterministic" has to mean stable storage and schema; the
classification pass itself needs inference, since intent cannot be read off a
filename.

**Aspect-scoped corpus valuation.** A low-quality draft should be creditable for one
compositional aspect only (its colour, its layout, its text). `validate_art_direction`
is currently strictly binary: every corpus item is either fully observed or fully
omitted. Needs a third, aspect-scoped state.

**Asynchronous brief, ranking and inference.** The largest item. Today the brief does
not exist and ranking is only useful once an article is published, so a long inference
leaves the user with nothing to do. The goal is that all three are live at once and
the UI reassures the user that work is progressing rather than leaving them staring at
a status dot. This depends on the brief existing first.

**Long runs producing weak output.** The loudest complaint and the least mechanical.
Contributing causes fixed so far are the uncapped cohort, the cross-round variant
accumulation, and the shared Chrome/qlmanage timeout. What remains is a craft
question about the design loop itself, and should be judged against a fresh round
now that the rendering defects above are gone, rather than assumed to still be true.
