#!/usr/bin/env python3
"""Art direction: the evidence a round is allowed to argue from.

A seam because this is the only place that decides what counts as grounding,
whether that is corpus observations or declared premises, and it must be able to
change its mind about that without disturbing editorial scope, theme, or the
corpus reader that merely lists what is on disk."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from asset_contract import AssetError, validate_assets
from direction_context import load_decisions, validate_brief_constraints
from harness_store import (
    ART_DIRECTION_FILE, CORPUS_FILE, KNOWN_BASES, STORE, VAGUE_LABEL, WorkflowError,
    _atomic_json, _read_json, _text,
)


def preference_state(entry: Mapping[str, Any]) -> str:
    sentiment = entry.get("sentiment")
    ranked = entry.get("source") == "user" and entry.get("scored") is True
    stars = int(entry.get("stars") or 0)
    if ranked and sentiment == "like":
        return "anchor" if stars >= 3 else "polish"
    if ranked and sentiment == "dislike":
        return "conflict" if stars >= 3 else "discard"
    if sentiment == "like":
        return "direction-like"
    if sentiment == "dislike":
        return "direction-dislike"
    if ranked:
        return "strong-execution" if stars >= 3 else "weak-execution"
    return "explore"


def preference_brief(decisions: Mapping[str, Any]) -> dict[str, Any]:
    elements = []
    user_ranked = 0
    for entry in sorted(decisions.get("elements", []), key=lambda item: str(item.get("element", ""))):
        if not isinstance(entry, Mapping) or not isinstance(entry.get("element"), str):
            continue
        ranked = entry.get("source") == "user" and entry.get("scored") is True
        user_ranked += int(ranked)
        item = {
            "element": entry["element"],
            "preferenceState": preference_state(entry),
            "rank": int(entry.get("stars") or 0) if ranked else None,
            "sentiment": entry.get("sentiment") if entry.get("sentiment") in {"like", "dislike"} else None,
            "lifecycle": entry.get("state") or "proposed",
            "rankProvenance": entry.get("source") if ranked else None,
            "preview": entry.get("preview"),
            "evidence": entry.get("evidence") or "",
        }
        elements.append(item)
    total = len([item for item in decisions.get("elements", []) if isinstance(item, Mapping)])
    return {
        "version": 1,
        "coverage": {"userRanked": user_ranked, "elements": total,
                     "fraction": user_ranked / total if total else 0},
        "elements": elements,
    }


def validate_art_direction(raw: Any, corpus: Mapping[str, Any],
                           preferences: Mapping[str, Any],
                           accountable: Any = None,
                           brief: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Validate direction evidence; accountable may group tagged references."""
    if not isinstance(raw, Mapping):
        raise WorkflowError("art direction must be an object")

    def prohibit(value: Any, path: str = "root") -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                if str(key).lower() in {"average", "reward", "overallscore", "totalscore"}:
                    raise WorkflowError(f"{path}.{key}: averages and reward scores are forbidden")
                prohibit(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                prohibit(child, f"{path}[{index}]")
    prohibit(raw)

    normalized_constraints = validate_brief_constraints(
        raw.get("briefConstraints", []), brief, WorkflowError)

    corpus_ids = {item.get("id") for item in corpus.get("items", []) if isinstance(item, Mapping)}
    try:
        assets = validate_assets(raw.get("assets"), corpus_ids)
    except AssetError as exc:
        raise WorkflowError(str(exc)) from exc
    preference_ids = {item.get("element") for item in preferences.get("elements", [])
                      if isinstance(item, Mapping)}
    # A project with no reference folder still gets to direct the work. It
    # argues from declared premises instead, and the grounding says which.
    seeded = not corpus_ids
    premises = raw.get("premises", [])
    if not isinstance(premises, list):
        raise WorkflowError("premises must be a list")
    if premises and not seeded:
        raise WorkflowError("premises are inference; a real corpus must be cited as observations")
    normalized_premises = []
    if seeded:
        if not premises:
            raise WorkflowError("a seeded corpus needs premises: declare what you are directing from")
        for index, premise in enumerate(premises):
            if not isinstance(premise, Mapping):
                raise WorkflowError(f"premises[{index}] must be an object")
            basis = _text(premise.get("basis"), f"premises[{index}].basis")
            if basis not in KNOWN_BASES:
                raise WorkflowError(f"unknown premise basis {basis}")
            claim = _text(premise.get("claim"), f"premises[{index}].claim")
            if VAGUE_LABEL.search(claim):
                raise WorkflowError("premise claim must name an observable relationship")
            counter = premise.get("counterevidence")
            if not isinstance(counter, list) or not counter:
                raise WorkflowError("premise must state counterevidence")
            normalized_premises.append({"basis": basis, "claim": claim,
                                        "counterevidence": [str(item) for item in counter]})

    observations = raw.get("observations", [])
    if not isinstance(observations, list):
        raise WorkflowError("observations must be a list")
    if seeded and observations:
        raise WorkflowError("a seeded corpus has nothing to observe; use premises")
    if not seeded and not observations:
        raise WorkflowError("art direction needs corpus observations")
    seen_corpus: set[str] = set()
    normalized_observations = []
    for index, observation in enumerate(observations):
        if not isinstance(observation, Mapping):
            raise WorkflowError(f"observations[{index}] must be an object")
        corpus_id = _text(observation.get("corpusItem"), f"observations[{index}].corpusItem")
        if corpus_id not in corpus_ids:
            raise WorkflowError(f"unknown corpus item {corpus_id}")
        seen_corpus.add(corpus_id)
        normalized_observations.append({
            "corpusItem": corpus_id,
            "locator": _text(observation.get("locator"), f"observations[{index}].locator"),
            "observation": _text(observation.get("observation"), f"observations[{index}].observation"),
        })
    omissions = raw.get("omissions", [])
    if not isinstance(omissions, list):
        raise WorkflowError("omissions must be a list")
    normalized_omissions = []
    for index, omission in enumerate(omissions):
        if not isinstance(omission, Mapping):
            raise WorkflowError(f"omissions[{index}] must be an object")
        corpus_id = _text(omission.get("corpusItem"), f"omissions[{index}].corpusItem")
        if corpus_id not in corpus_ids:
            raise WorkflowError(f"unknown corpus item {corpus_id}")
        if corpus_id in seen_corpus:
            raise WorkflowError(f"corpus item {corpus_id} is both observed and omitted")
        seen_corpus.add(corpus_id)
        normalized_omissions.append({"corpusItem": corpus_id,
                                     "reason": _text(omission.get("reason"), "omission.reason")})
    # Untagged projects account for every item, as they always have. Once the
    # user has tagged their reference folders, the folder is the unit: one
    # observation inside it accounts for it. A 135-item corpus was costing 127
    # boilerplate omissions per round, rewritten every time.
    missing = (sorted(str(item) for item in corpus_ids - seen_corpus)
               if accountable is None else accountable(seen_corpus))
    if missing:
        raise WorkflowError("unaccounted corpus items: " + ", ".join(missing))

    patterns = raw.get("preferencePatterns")
    if not isinstance(patterns, list):
        raise WorkflowError("preferencePatterns must be a list")
    normalized_patterns = []
    vague = VAGUE_LABEL
    for index, pattern in enumerate(patterns):
        if not isinstance(pattern, Mapping):
            raise WorkflowError(f"preferencePatterns[{index}] must be an object")
        claim = _text(pattern.get("claim"), f"preferencePatterns[{index}].claim")
        if vague.search(claim):
            raise WorkflowError("preference claim must name an observable relationship")
        support = pattern.get("support")
        counter = pattern.get("counterevidence")
        if not isinstance(support, list) or not support:
            raise WorkflowError("preference pattern needs supporting element ids")
        if not isinstance(counter, list):
            raise WorkflowError("preference pattern counterevidence must be a list")
        unknown = [item for item in support + counter if item not in preference_ids]
        if unknown:
            raise WorkflowError("unknown preference element " + str(unknown[0]))
        n = pattern.get("n")
        coverage = pattern.get("coverage")
        confidence = pattern.get("confidence")
        if not isinstance(n, int) or isinstance(n, bool) or n < len(set(support + counter)):
            raise WorkflowError("preference pattern n is inconsistent")
        if not isinstance(coverage, (int, float)) or isinstance(coverage, bool) or not 0 <= coverage <= 1:
            raise WorkflowError("preference pattern coverage must be 0..1")
        if confidence not in {"low", "medium", "high"}:
            raise WorkflowError("preference pattern confidence must be low, medium, or high")
        normalized_patterns.append({"claim": claim, "support": support,
                                    "counterevidence": counter, "n": n,
                                    "coverage": coverage, "confidence": confidence})

    hypotheses = raw.get("hypotheses")
    if not isinstance(hypotheses, list) or not 1 <= len(hypotheses) <= 4:
        raise WorkflowError("art direction needs one to four hypotheses")
    system_keys = ("palette", "typography", "grid", "hierarchy", "imagery", "voice", "motion")
    normalized_hypotheses = []
    ids: set[str] = set()
    signatures: set[str] = set()
    for index, hypothesis in enumerate(hypotheses):
        if not isinstance(hypothesis, Mapping):
            raise WorkflowError(f"hypotheses[{index}] must be an object")
        identifier = _text(hypothesis.get("id"), f"hypotheses[{index}].id")
        signature = _text(hypothesis.get("signatureMove"), f"{identifier}.signatureMove")
        if identifier in ids or signature.lower() in signatures:
            raise WorkflowError("hypotheses need unique ids and signature moves")
        ids.add(identifier); signatures.add(signature.lower())
        system = hypothesis.get("visualSystem")
        if not isinstance(system, Mapping):
            raise WorkflowError(f"{identifier}.visualSystem must be an object")
        normalized_hypotheses.append({
            "id": identifier, "thesis": _text(hypothesis.get("thesis"), f"{identifier}.thesis"),
            "signatureMove": signature,
            "visualSystem": {key: _text(system.get(key), f"{identifier}.{key}") for key in system_keys},
        })

    comparison = raw.get("comparison")
    if not isinstance(comparison, list) or len(comparison) != len(ids):
        raise WorkflowError("comparison needs one row per hypothesis")
    dimensions = ("corpusFit", "preferenceFit", "subjectSpecificity", "coherence", "executionLeverage")
    user_ranked = int(preferences.get("coverage", {}).get("userRanked") or 0)
    compared: set[str] = set()
    normalized_comparison = []
    for row in comparison:
        if not isinstance(row, Mapping) or row.get("hypothesis") not in ids:
            raise WorkflowError("comparison names an unknown hypothesis")
        identifier = str(row["hypothesis"])
        if identifier in compared:
            raise WorkflowError("comparison repeats a hypothesis")
        compared.add(identifier)
        values = {}
        for dimension in dimensions:
            value = row.get(dimension)
            missing_evidence = ((dimension == "corpusFit" and seeded) or
                                (dimension == "preferenceFit" and not user_ranked))
            if missing_evidence:
                if value is not None:
                    raise WorkflowError(
                        f"{identifier}.{dimension} must be null without supporting evidence")
                values[dimension] = None
                continue
            if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 5:
                raise WorkflowError(f"{identifier}.{dimension} must be 1..5")
            values[dimension] = value
        normalized_comparison.append({"hypothesis": identifier, **values,
                                      "tradeoff": _text(row.get("tradeoff"), f"{identifier}.tradeoff")})
    selected = _text(raw.get("selected"), "selected")
    if selected not in ids:
        raise WorkflowError("selected must name a hypothesis")
    cohort = raw.get("cohort")
    if not isinstance(cohort, list) or not 3 <= len(cohort) <= 6 or len(set(cohort)) != len(cohort):
        raise WorkflowError("cohort must contain three to six unique elements")
    # With nothing ranked yet the cohort is necessarily new work. Once the user
    # has ranked anything, the cohort must stay inside that set so a round
    # cannot quietly drift off the elements under judgement.
    if preference_ids:
        unknown_cohort = [item for item in cohort if item not in preference_ids]
        if unknown_cohort:
            raise WorkflowError("unknown cohort element " + str(unknown_cohort[0]))
    return {
        "version": 1, "observations": normalized_observations, "omissions": normalized_omissions,
        "premises": normalized_premises, "grounding": "inference" if seeded else "corpus",
        "preferencePatterns": normalized_patterns, "hypotheses": normalized_hypotheses,
        "comparison": normalized_comparison, "selected": selected,
        "selectionRationale": _text(raw.get("selectionRationale"), "selectionRationale"),
        "cohort": cohort, "assets": assets,
        "briefConstraints": normalized_constraints,
    }


def save_art_direction(project_root: Path, raw: Any) -> dict[str, Any]:
    root = Path(project_root)
    if any((root / STORE / name).is_file()
           for name in ("scene-spec.json", "graphics-manifest.json")):
        raise WorkflowError(
            "graphics project detected; run text_to_graphics.py status instead of direction")
    corpus = _read_json(root / STORE / CORPUS_FILE)
    # Nothing ranked yet is a normal first round, not a missing artifact.
    preferences = preference_brief(load_decisions(root))
    # Imported here, not at module scope: `corpus_tags` imports this module.
    from corpus_tags import load_tags, missing_evidence
    from brief_workflow import load_brief
    tags = load_tags(root)
    value = validate_art_direction(
        raw, corpus, preferences,
        lambda seen: missing_evidence(corpus, tags, seen),
        load_brief(root))
    try:
        validate_assets(value["assets"], {item.get("id") for item in corpus["items"]}, root)
    except AssetError as exc:
        raise WorkflowError(str(exc)) from exc
    _atomic_json(root / STORE / ART_DIRECTION_FILE, value)
    return value
