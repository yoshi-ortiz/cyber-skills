#!/usr/bin/env python3
"""Advisory assessment of user messages. Suggests; never decides, never writes.

A human `--status` is the only thing that settles a Shot. This module reads a
message and, at most once per message, names one field a human might want to
set. Silence is the correct output for anything it does not recognise.
"""
import re
from typing import NamedTuple, Sequence


MESSAGE = None

THRESHOLD = 0.6

MUTE = (
    re.compile(r"\bnot bad\b", re.I),
    re.compile(r"\bnot terrible\b", re.I),
    re.compile(r"\bno complaints?\b", re.I),
)

# Bare `no`, `not`, `bad` and `but` are banned from every pattern here. They are
# what the classifier this replaces matched on, and they read "not bad" as a
# rejection. Only phrases whose whole meaning survives the match get a row.
RULES = (
    (re.compile(r"\bno changes needed\b", re.I), "status", "accepted", 0.9,
     "an explicit statement that nothing is left to do"),
    (re.compile(r"\bship it\b", re.I), "status", "accepted", 0.9,
     "release is the strongest form of acceptance"),
    (re.compile(r"\blooks good\b", re.I), "status", "accepted", 0.85,
     "the whole phrase, because bare good survives any complaint after it"),
    (re.compile(r"\blgtm\b", re.I), "status", "accepted", 0.9,
     "review shorthand with no other reading"),
    (re.compile(r"\bapproved?\b", re.I), "status", "accepted", 0.85,
     "the verdict word itself"),

    (re.compile(r"\bfix\b", re.I), "correction", MESSAGE, 0.8,
     "a request to fix is work outstanding, whatever praise surrounds it"),
    (re.compile(r"\bchange\b", re.I), "correction", MESSAGE, 0.75,
     "names an edit to make"),
    (re.compile(r"\binstead of\b", re.I), "correction", MESSAGE, 0.8,
     "substitution is a correction with the replacement named"),
    (re.compile(r"\bc[aá]mbi", re.I), "correction", MESSAGE, 0.8,
     "Spanish stem for change, accented or not"),
    (re.compile(r"\barregl", re.I), "correction", MESSAGE, 0.8,
     "Spanish stem for fix"),
    (re.compile(r"\bcorr[ií]g", re.I), "correction", MESSAGE, 0.8,
     "Spanish stem for correct, accented or not"),

    (re.compile(r"\buseless\b", re.I), "sentiment", "negative", 0.75,
     "dismissal with no fix attached"),
    (re.compile(r"\bgarbage\b", re.I), "sentiment", "negative", 0.75,
     "dismissal with no fix attached"),
    (re.compile(r"\bbroken\b", re.I), "sentiment", "negative", 0.7,
     "reports a failure without naming the repair"),
    (re.compile(r"doesn'?t work\b", re.I), "sentiment", "negative", 0.7,
     "reports a failure without naming the repair"),
    (re.compile(r"\bno sirve\b", re.I), "sentiment", "negative", 0.7,
     "Spanish, does not work"),
    (re.compile(r"\brot[oa]\b", re.I), "sentiment", "negative", 0.7,
     "Spanish, broken"),

    (re.compile(r"\bmeh\b", re.I), "sentiment", "negative", 0.5,
     "kept and never emitted: meh is mild assent as often as disappointment"),
)


# The hard read, kept apart from RULES above on purpose. RULES answer "which
# field might a human want to set, and how sure are we"; these answer "did the
# user object, and did they have to say it twice". Same words, different
# question, and collapsing them would make one of the two answers wrong.
#
# English keywords, imperfect. A caller may only ever use them together with
# evidence that nothing changed, so a false positive cannot fail a round alone.
FRUSTRATION = ("broken", "fucked", "dafuq", "wtf", "doesn't work", "does not work",
               "garbage", "useless", "terrible", "all wrong", "no sirve", "roto")

# A correction is stronger evidence than frustration: it names an instruction
# the run did not follow. "It's broken" is a symptom; "I asked for X" is a
# requirement still outstanding.
CORRECTION = tuple(re.compile(p, re.I) for p in (
    r"\byou (did ?n[o']?t|didn't|never|forgot|failed to|were supposed)",
    r"\bi (initially |already |actually |just )?(asked|requested|told you|said)\b",
    r"\bnot what i\b",
    r"\bshould (not |n't )?(be|stick|have|follow|take)\b",
    r"\binstead of\b",
))
# Words too common to prove two corrections are the same instruction.
COMMON = {"should", "would", "could", "that", "this", "with", "from", "have",
          "just", "like", "also", "your", "make", "sure", "want", "need",
          "skill", "thing", "only", "does", "what", "when", "then", "they"}


def repeated(corrections: Sequence[str], floor: int = 3) -> list[str]:
    """Corrections that restate an earlier one.

    Whether an instruction was *satisfied* is a judgement no automated read can
    make. That the user had to say it twice is a fact, and it is the same
    evidence: an instruction repeated is an instruction that did not land.
    """
    words = [set(re.findall(r"[a-z]{4,}", c.lower())) - COMMON for c in corrections]
    out = []
    for i, later in enumerate(words):
        if any(len(later & earlier) >= floor for earlier in words[:i]):
            out.append(corrections[i])
    return out


def audit(turns: Sequence[str]) -> dict:
    """Everything this boundary can say about what the user said in one run."""
    corrections = [t for t in turns if any(p.search(t) for p in CORRECTION)]
    return {
        "complaints": [t for t in turns
                       if any(w in t.lower() for w in FRUSTRATION)],
        "corrections": corrections,
        "restated": repeated(corrections),
        "candidates": [c._asdict() for c in assess(turns)],
    }


class FeedbackCandidate(NamedTuple):
    field: str
    value: str
    confidence: float
    reasons: tuple[str, ...]
    evidence: str


def assess(messages: Sequence[str]) -> list[FeedbackCandidate]:
    found = []
    for message in messages:
        if not message.strip() or any(m.search(message) for m in MUTE):
            continue
        for pattern, field, kind, confidence, reason in RULES:
            if not pattern.search(message):
                continue
            if confidence >= THRESHOLD:
                found.append(FeedbackCandidate(
                    field, message if kind is MESSAGE else kind,
                    confidence, (reason,), message))
            break
    return found


BUNDLE = ("shot_id", "scope", "evidence", "findings", "artifacts", "observed_at")


def correction_bundle(shot: dict, evidence: str = "",
                      artifacts: Sequence[str] = ()) -> dict:
    """What an adapter is allowed to see when a Shot is sent back.

    Bounded on purpose. Handing over the whole record is how one rejected
    round turns into a rewrite of the skill that produced it, so this carries
    the correction and the things it names, and nothing else.
    """
    said = shot.get("user_feedback") or {}
    declared = shot.get("output", {}).get("artifacts") or []
    return {
        "shot_id": shot.get("shot_id", ""),
        "scope": shot.get("scope", ""),
        "evidence": evidence or said.get("correction") or said.get("evidence") or "",
        "findings": sorted(f["id"] for f in shot.get("findings") or []
                           if isinstance(f, dict) and f.get("status") == "present"),
        "artifacts": list(artifacts) or [a["path"] for a in declared
                                         if isinstance(a, dict) and a.get("path")],
        "observed_at": said.get("observed_at", ""),
    }
