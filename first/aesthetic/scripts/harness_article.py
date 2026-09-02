#!/usr/bin/env python3
"""The design-system article, which is also the scoring companion.

One page assembled from the ledger: the round, the fundamentals, the backlog,
the antipatterns, and the controls that make each of them clickable. The seam
is assembly -- every part it uses is generated somewhere else, and this decides
only what appears, in what zone, in what order.
"""

from __future__ import annotations

import json
import re
from html import escape as html_escape
from pathlib import Path

from harness_core import FOUNDATION_ORDER, GROUP_OF, HarnessError, STAR_RANGE
from harness_strings import (agent_display_line, agent_display_parts,
                             project_language, resolve_agent, strings_for)
from harness_ledger import display_name, display_names, ledger_stats
from harness_round import (FOLDING_ZONES, SUBNAV_ZONES, ZONES, check_asks,
                           check_cohort_size, check_round_stays_in_scope,
                           check_unique_cohort_previews, foundation_of,
                           incumbent_of, lineage_root_of, primary_foundation,
                           round_tag_label, zone_of)
from harness_comp import render_preview
from harness_controls import extract_feedback_rows, render_feedback_controls
from harness_specimens import (ARTICLE_STYLE, LIGHTBOX_SCRIPT, ROUND_ICON,
                               ROUND_ICONS, SHOT_FIT_SCRIPT, TOC_SCRIPT,
                               TRASH_ICON, _specimens)


def project_title(project_root: Path | None) -> str:
    if project_root is None:
        return ""
    path = project_root / "spec" / "design-harness" / "project.json"
    try:
        return str(json.loads(path.read_text(encoding="utf-8")).get("title") or "")
    except (OSError, ValueError):
        return ""


def render_article(project_root: Path, decisions: dict[str, object],
                   cohort: set[str] | None = None, *,
                   cohort_name: str = "", language: str | None = None,
                   title: str = "", asks: str = "",
                   agent_url: str = "", agent_name: str = "",
                   round_label: str = "", agent_working: bool = False) -> str:
    """A design-system article that is also the scoring companion.

    The strip alone answered "what is on the list". It could not answer "what is
    the typography doing", because a heading with one row under it is a list.
    Here each foundation shows its own material first -- the palette as colour,
    the faces as type -- and the scoring row sits against the thing it judges.
    """
    txt = strings_for(language or project_language(project_root))
    agent_url, raw_name = resolve_agent(agent_url, agent_name, project_root)
    agent_app, agent_model = agent_display_parts(raw_name, agent_url)
    agent_name = agent_display_line(raw_name, agent_url)
    cohort = cohort or set()
    check_asks(asks, cohort, language or project_language(project_root))
    check_cohort_size(cohort)
    check_round_stays_in_scope(cohort)
    check_unique_cohort_previews(decisions, cohort)
    # A cohort is one surface or one problem. Three elements drawn from three
    # different foundations, under a name that claims a shared surface, is a
    # batch of errands -- and the page cannot say what it is asking, so the
    # agent ends up explaining the round in prose the user never asked for.
    # Either the domain is evident from the ledger, or it has to be stated.
    #
    # `--asks` answers THIS check, which is about a round that needs explaining.
    # It does not answer `check_round_stays_in_scope` above, which is about a
    # round that should not exist as one round -- no sentence makes two parent
    # items into one object.
    domains = sorted({foundation_of(e) for e in cohort})
    if len(domains) > 2 and not asks.strip():
        raise HarnessError(
            "this cohort spans " + ", ".join(domains) + " -- that is a batch of errands, "
            "not a round. Narrow it to one surface or one problem, or say what they share "
            "with --asks \"<one sentence>\" so the screen can state it.")
    generated = render_feedback_controls(decisions, None, project_root, cohort, language)
    rows = extract_feedback_rows(generated)
    style = re.search(r"<style>/\* dh-controls \*/.*?</style>", generated, re.S)
    script = re.search(r"<script>/\* dh-rehydrate \*/.*?</script>", generated, re.S)
    live = [e for e in decisions["elements"] if e["state"] in GROUP_OF]
    bar_names = display_names(live)
    known_ids = {e["element"] for e in decisions["elements"]}
    stats = ledger_stats(decisions)

    def rank(entry: dict[str, object]) -> tuple:
        # Best execution on top, inside its own foundation. A user scanning for
        # what is working should not have to read every row to find it.
        return (FOUNDATION_ORDER.get(foundation_of(entry["element"]), len(FOUNDATION_ORDER)),
                -int(entry.get("stars") or 0), entry["element"])

    def bar_class(entry: dict[str, object]) -> str:
        # Solid green is reserved for finished work. A high score is not the
        # same claim -- it says this drawing is beautiful, not that the question
        # is closed -- so it reads as a faded green and the eye can still find
        # the handful of things actually done.
        # Turned-down work keeps a red, drained of its urgency: still legible
        # as "rejected", no longer shouting alongside a live 0-star problem.
        if zone_of(entry, cohort) == "antipattern":
            return "dh-tanti"
        if not entry.get("scored"):
            return "dh-tnone"
        if entry["state"] == "completed":
            return "dh-tdone"
        if int(entry.get("stars") or 0) >= 4:
            return "dh-thigh"
        return f'dh-t{entry["stars"]}'

    def bar(entry: dict[str, object], attempts: int = 1) -> str:
        stars = "--" if not entry.get("scored") else entry["stars"]
        asked = entry["element"] in cohort
        # The old tooltip read `family.tab.spine-step.grupo-color -- 1/5 --
        # proposed`: a namespace, a fraction and a lifecycle word. A designer
        # needs to see the DRAWING and its name. The bar now carries the id so
        # the script can build a real preview card, and a click opens the
        # slideshow rather than scrolling to a row.
        name = bar_names.get(entry["element"]) or display_name(entry)
        label = f'{name} — {stars}/{STAR_RANGE[1]}'
        if attempts > 1:
            label = f'{label} — {txt["bar-attempts"].format(count=attempts)}'
        if asked:
            label = f'{txt["zone-round"]}: {label}'
        return (f'<a class="{bar_class(entry)}" href="#dh-el-{html_escape(entry["element"])}"'
                f'{" data-asked=\"1\"" if asked else ""} '
                f'data-el="{html_escape(entry["element"])}" '
                f'data-name="{html_escape(name)}" '
                f'{f"data-variants=\"{attempts}\" " if attempts > 1 else ""}'
                f'data-score="{stars}" '
                # `aria-label`, never `title`: a `title` made the browser draw a
                # SECOND tooltip in the OS font, on top of the key row.
                f'aria-label="{html_escape(label)}">'
                f'<span>{"?" if asked else ""}</span></a>')

    def bar_order(entry: dict[str, object]) -> tuple:
        # Worst to best, with what was set aside after it. The round's own bars
        # stay where their score puts them -- they carry a ? and an outline, so
        # they are findable in place, and a bar's POSITION is what says how the
        # work compares. Hoisting them to the front threw that reading away.
        anti = 1 if zone_of(entry, cohort) == "antipattern" else 0
        return (anti, -int(entry.get("stars") or 0), entry["element"])

    # One bar per IDEA, not per attempt. Every redraw used to keep its own bar
    # forever -- a superseded drawing is still `live` for the strip's purposes
    # -- so the chart grew without bound and said "twenty-eight concerns" when
    # the truth was eight ideas, some of them drawn four times. The round zone
    # has grouped variants under their incumbent since it was written; this is
    # the same grouping, applied to the strip that summarises the whole ledger.
    lineages: dict[str, list[dict[str, object]]] = {}
    for entry in live:
        lineages.setdefault(lineage_root_of(entry["element"], known_ids), []).append(entry)

    def speaks_for(members: list[dict[str, object]]) -> dict[str, object]:
        # This round's ask speaks for its own lineage: it carries the `?` and
        # the outline, and hiding it behind an ancestor would make the one
        # thing being asked about the one thing the strip could not show.
        # Otherwise the standing drawing speaks, best execution first.
        return sorted(members, key=lambda e: (
            0 if e["element"] in cohort else 1,
            0 if e["state"] not in ("superseded", "rejected") else 1,
            -int(e.get("stars") or 0),
            e["element"]))[0]

    attempts: dict[str, int] = {}
    speakers: list[dict[str, object]] = []
    for members in lineages.values():
        speaker = speaks_for(members)
        attempts[speaker["element"]] = len(members)
        speakers.append(speaker)
    ordered_bars = sorted(speakers, key=bar_order)
    bars = "".join(bar(e, attempts.get(e["element"], 1)) for e in ordered_bars)
    asking = len([e for e in live if e["element"] in cohort])
    # Three figures the reader can act on, in the order they matter: what is
    # being asked now, what is still moving, and what is known to need another
    # pass. "Standing" and "you ranked" counted the archive instead -- both read
    # 32 of 32, which is true and tells nobody what to do next.
    # The three figures a designer can act on, matching the words under them.
    # "In better shape" is work they scored well; "need your direction" is work
    # waiting on THEM -- never scored, or liked but still weak. The old figures
    # counted the round and the archive, which told nobody what to do next.
    def user_stars(entry: dict[str, object]) -> int:
        return int(entry.get("stars") or 0) if entry.get("scored") else -1
    better = len([e for e in live if zone_of(e, cohort) != "antipattern"
                  and (user_stars(e) >= 3 or e["state"] in ("approved", "completed"))])
    ongoing = len([e for e in live if zone_of(e, cohort) != "antipattern"
                   and user_stars(e) < 3
                   and (not e.get("scored") or e["element"] in set(stats["needsPolish"]))])
    to_improve = len([e for e in live if zone_of(e, cohort) == "antipattern"])
    # A kebab-case cohort id set at 68px is a machine label wearing a headline's
    # clothes. The hero names the artefact being designed; the round is a line
    # underneath it, which is what it actually is.
    headline = html_escape(title or project_title(project_root) or txt["article-title"])
    agent_state = "active" if agent_working else "idle"
    designing_display = (round_label or cohort_name).strip()
    # The screen is a fragment, so its encoding rode entirely on whoever served
    # it. Opened from disk, or served by anything that omits the header, every
    # accent in a Spanish project rendered as mojibake. Declaring it here makes
    # the artifact say what it is wherever it ends up.
    out = ['<meta charset="utf-8">',
           ARTICLE_STYLE, style.group(0) if style else "", script.group(0) if script else "",
           TOC_SCRIPT, SHOT_FIT_SCRIPT, LIGHTBOX_SCRIPT,
           f'<div class="dh-art" data-saved="{html_escape(txt["saved"])}" '
           f'data-cheer-text="{html_escape(txt["done-cheer"])}" '
           f'data-done-label="{html_escape(txt["completed"])}" '
           f'data-agent-url="{html_escape(agent_url)}" '
           f'data-agent-state="{agent_state}" '
           f'data-lang="{html_escape((language or project_language(project_root)).lower())}" '
           f'data-agent-label="{html_escape(agent_name)}" '
           f'data-agent-app="{html_escape(agent_app)}" '
           f'data-agent-model="{html_escape(agent_model)}" '
           f'data-companion-kind="{html_escape(txt["companion-kind"])}">',
           '<header class="dh-hero">',
           # Read by a graphic designer, not by whoever built the harness: who
           # is asking, what this page is, which project, and what is on the
           # table right now -- in that order, before any number.
           f'<p class="dh-eyebrow">{html_escape(txt["brand"])}</p>',
           f'<h1>{html_escape(txt["article-title"])}</h1>',
           '<div class="dh-hero-meta">',
           f'<span class="dh-label">{html_escape(txt["project-label"])}</span>',
           f'<b class="dh-value">{headline}</b>',
           *([f'<span class="dh-label">{html_escape(txt["designing"])}</span>',
              f'<b class="dh-value">{html_escape(designing_display)}</b>']
             if designing_display else []),
           "</div>",
           f'<p class="dh-lede">{html_escape(txt["hero-lede"])}</p>',
           '<div class="dh-figures">',
           f'<div><b>{better}</b><span>{html_escape(txt["hero-asking"])}</span></div>',
           f'<div><b>{ongoing}</b><span>{html_escape(txt["hero-ongoing"])}</span></div>',
           f'<div><b>{to_improve}</b><span>{html_escape(txt["hero-improve"])}</span></div>',
           "</div>",
           "</header>"]
    # Keep the original article as the only presentation. The small workflow
    # module supplies durable project scope; it must never render a competing
    # website. A missing spec simply means this older project has no burndown.
    # `WorkflowError` subclasses ValueError, so the existing catch already
    # covers a corrupt spec on both.
    #
    # Built here, rendered under the round. The round is what the page is
    # asking for; a five-question form standing above it buried the ask behind
    # homework. Below it the reading order is what stands, rank it, then
    # sharpen the foundations if you want to.
    try:
        import brief_workflow
        brief_markup = brief_workflow.render_brief(project_root, txt)
    except (ImportError, OSError, ValueError):
        brief_markup = ""
    # Reference tags are the other half of what the user tells the agent, so
    # they render beside the brief rather than at opposite ends of the page.
    # Both stay quiet until they have something to ask about.
    try:
        import corpus_tags
        tags_markup = corpus_tags.render_corpus_tags(project_root, txt)
    except (ImportError, OSError, ValueError):
        tags_markup = ""
    try:
        import editorial_workflow
        burndown_markup = editorial_workflow.render_burndown(project_root)
    except (ImportError, OSError, ValueError):
        burndown_markup = ""
    if burndown_markup:
        out.append(burndown_markup)
    shown = [z for z in ZONES
             if z == "round" or any(zone_of(e, cohort) == z for e in live)]
    links = []
    for z in shown:
        tally = len([e for e in live if zone_of(e, cohort) == z])
        icon = TRASH_ICON if z == "antipattern" else ""
        # This round is the one thing being asked for, so it is the only link
        # that looks like a button. The rest are places to go.
        cta = ' data-cta="1"' if z == "round" else ""
        links.append(f'<li><a href="#dh-zone-{z}" data-zone="{z}"{cta}>{icon}'
                     f'{html_escape(txt[f"zone-{z}"])}<em>{tally}</em></a></li>')
    out.append('<nav class="dh-toc" aria-label="' + html_escape(txt["article-title"])
               + '"><p class="dh-toc-title">' + html_escape(txt["article-title"]) + "</p>"
               # Legend, then the chart it explains, then the sections it indexes.
               + '<p class="dh-key">'
               + f'<span><b>?</b>{html_escape(txt["key-asked"])}</span>'
               + '<span class="dh-key-good">'
               + f'<span><i class="dh-tdone"></i>{html_escape(txt["key-done"])}</span>'
               + f'<span><i class="dh-thigh"></i>{html_escape(txt["key-open"])}</span>'
               + "</span>"
               + '<span class="dh-key-bad">'
               + f'<span><i class="dh-t1"></i>{html_escape(txt["key-weak"])}</span>'
               + f'<span><i class="dh-tnone"></i>{html_escape(txt["key-unscored"])}</span>'
               + f'<span><i class="dh-tanti"></i>{html_escape(txt["key-anti"])}</span>'
               + "</span>"
               + "</p>"
               + f'<div class="dh-temp dh-temp-sticky" role="group" '
                 f'aria-label="{html_escape(txt["temp-alt"])}">{bars}</div>'
               + '<ol>' + "".join(links) + "</ol></nav>")
    for zone in ZONES:
        members = sorted((e for e in live if zone_of(e, cohort) == zone), key=rank)
        if not members and zone != "round":
            continue
        note = txt[f"zone-{zone}-note"]
        domain_line = ""
        if zone == "round":
            if asks.strip():
                note = asks.strip()
            topic = primary_foundation(cohort) if cohort else ""
            if topic:
                domain_line = ('<p class="dh-domain">'
                               f'<span>{html_escape(txt.get(topic, topic))}</span>'
                               "</p>")
        # The round is the only section that ASKS, so its own question is the
        # protagonist of the page -- set large and centred rather than filed as
        # a grey note under a heading, which is where nobody read it.
        heading = txt["round-heading"] if zone == "round" else txt[f"zone-{zone}"]
        note_markup = (f'<p class="dh-ask">{html_escape(note)}</p>'
                       if zone == "round"
                       else f'<p class="dh-note">{html_escape(note)}</p>')
        # The round tag names the OBJECT being judged, not a slug like `objeto`.
        tag = (html_escape(round_tag_label(cohort, decisions, cohort_name, round_label))
               if zone == "round" and cohort
               else (html_escape(cohort_name) if zone == "round" and cohort_name
                     else f'{len(members)} {html_escape(txt["designs"])}'))
        icon = (ROUND_ICONS.get(primary_foundation(cohort), ROUND_ICON)
                if zone == "round" and cohort else "")
        preparing = ' data-preparing="1"' if zone == "round" and agent_working else ""
        out += [f'<section class="dh-zone" id="dh-zone-{zone}" data-zone="{zone}"{preparing}>', "<header>",
                icon,
                f'<p class="dh-tag">{tag}</p>',
                f'<h2>{html_escape(heading)}</h2>',
                domain_line,
                note_markup, "</header>"]
        if zone == "round":
            out.append(f'<p class="dh-prep">{html_escape(txt["prep-legend"])}</p>')
        if not members:
            out.append(f'<p class="dh-empty">{html_escape(txt["empty-zone"])}</p>')
        # A second sticky level for the long zone: the reader arrives here
        # hunting a surface, and scrolling twenty rows to find it is the cost
        # the first bar was supposed to remove.
        if zone in SUBNAV_ZONES and members:
            order_seen: list[str] = []
            for entry in members:
                key = foundation_of(entry["element"])
                if key not in order_seen:
                    order_seen.append(key)
            # Three groups, not two. A second sticky bar over a short list is
            # noise -- that judgement stands -- but the critical components now
            # run to seventeen elements across five foundations, and a reader
            # hunting a surface there had no way to reach it except by scrolling
            # past every other one. The threshold is the length, not the zone.
            if len(order_seen) >= 3:
                out.append(
                    f'<nav class="dh-subnav" aria-label="{html_escape(txt["toc-jump"])}"><ol>'
                    + "".join(
                        f'<li><a href="#dh-{zone}-{key}" data-sub="{key}">{html_escape(txt.get(key, key))}'
                        f'<em>{len([e for e in members if foundation_of(e["element"]) == key])}</em>'
                        "</a></li>" for key in order_seen)
                    + "</ol></nav>")
        # Round-zone members that redraw the SAME incumbent render together
        # under one shared "before" instead of each getting its own
        # standalone before/after card. `check_round_earns_its_place` already
        # caps this at MAX_VARIANTS_PER_IDEA, so a group here is always small.
        incumbent_of_member: dict[str, str] = {}
        variant_count: dict[str, int] = {}
        grouped_already: set[str] = set()
        if zone == "round":
            for e in members:
                inc = incumbent_of(e["element"], known_ids)
                if inc and inc in rows:
                    incumbent_of_member[e["element"]] = inc
                    variant_count[inc] = variant_count.get(inc, 0) + 1
        seen_foundation = None
        for entry in members:
            key = foundation_of(entry["element"])
            if key != seen_foundation:
                if seen_foundation is not None and zone in FOLDING_ZONES:
                    out.append("</details>")
                seen_foundation = key
                same = [e for e in members if foundation_of(e["element"]) == key]
                heading = (f'{txt.get(key, key)}<span class="dh-count">{len(same)}</span>')
                if zone in FOLDING_ZONES:
                    # Folded, the group still shows its work: a strip of the
                    # graphics themselves. A collapsed section that shows only
                    # its own name asks the reader to open every one to find
                    # anything, which is worse than the scroll it replaced.
                    thumbs = "".join(
                        render_preview(project_root, e.get("preview"), e["element"], txt)
                        for e in same)
                    out.append(
                        f'<details class="dh-acc" data-group="{key}">'
                        f'<summary class="dh-group" id="dh-{zone}-{key}" data-group="{key}">'
                        f'{heading}<span class="dh-acc-thumbs">{thumbs}</span></summary>')
                else:
                    out.append(f'<h4 class="dh-group" id="dh-{zone}-{key}" data-group="{key}">'
                               f'{heading}</h4>')
                out.append(_specimens(same, txt, rows))
            if entry["element"] in grouped_already:
                continue
            row = rows.get(entry["element"], "")
            row = row.replace('<div class="dh-fb"',
                              f'<div id="dh-el-{entry["element"]}" class="dh-fb"', 1)
            if zone == "round":
                # Paired with what it replaces, or plainly marked as new. Either
                # way the user is never asked to rank a drawing against nothing.
                prior = incumbent_of_member.get(entry["element"], "")
                if prior and variant_count.get(prior, 0) >= 2:
                    # Two or more variants of the SAME idea: one shared
                    # "before", every variant beside it instead of each
                    # getting its own standalone before/after card.
                    variants = [e for e in members
                               if incumbent_of_member.get(e["element"]) == prior]
                    variant_markup = []
                    for variant in variants:
                        vrow = rows.get(variant["element"], "")
                        vrow = vrow.replace('<div class="dh-fb"',
                                            f'<div id="dh-el-{variant["element"]}" class="dh-fb"', 1)
                        suffix = variant["element"][len(prior) + 1:]
                        variant_markup.append(
                            '<div class="dh-idea-variant">'
                            f'<p class="dh-versus-label"><b class="dh-now">{html_escape(suffix)}</b></p>'
                            + vrow + "</div>")
                        grouped_already.add(variant["element"])
                    out.append(
                        '<div class="dh-idea-group">'
                        f'<p class="dh-versus-label"><b>{html_escape(txt["before"])}</b></p>'
                        + rows[prior].replace('<div class="dh-fb"',
                                              '<div class="dh-fb dh-fb-before"', 1)
                        + '<div class="dh-idea-variants">' + "".join(variant_markup) + "</div>"
                        + "</div>")
                    continue
                if prior:
                    out.append(
                        '<div class="dh-versus">'
                        f'<p class="dh-versus-label"><b>{html_escape(txt["before"])}</b></p>'
                        + rows[prior].replace('<div class="dh-fb"',
                                              '<div class="dh-fb dh-fb-before"', 1)
                        + f'<p class="dh-versus-label"><b class="dh-now">{html_escape(txt["after"])}</b></p>'
                        + row + "</div>")
                    continue
                out.append('<div class="dh-versus">'
                           f'<p class="dh-versus-label"><b class="dh-now">'
                           f'{html_escape(txt["brand-new"])}</b></p>' + row + "</div>")
                continue
            out.append(row)
        if seen_foundation is not None and zone in FOLDING_ZONES:
            out.append("</details>")
        out.append("</section>")
        if zone == "round":
            out.extend(m for m in (brief_markup, tags_markup) if m)
    out += [
        '<footer class="dh-credit">'
        f'<b>{html_escape(txt["credit-what"])}</b>'
        f'<span>{html_escape(txt["credit-who"])}</span>'
        "</footer>",
        "</div>",
    ]
    return "\n".join(part for part in out if part) + "\n"
