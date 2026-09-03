#!/usr/bin/env python3
"""What advisory assessment must never get wrong.

The keyword classifier this replaces read "not bad" as a rejection and "no
changes needed, ship it" as a rejection too. Every row of the adversarial
table below is a message that classifier got backwards.
"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import feedback as fb


ADVERSARIAL = [
    ("not bad", None),
    ("no changes needed, ship it", ("status", "accepted")),
    ("good but fix the thumbnail", ("correction", "good but fix the thumbnail")),
    ("la miniatura no sirve; cambiala",
     ("correction", "la miniatura no sirve; cambiala")),
    ("output is useless", ("sentiment", "negative")),
]


def one(message):
    got = fb.assess([message])
    return got[0] if got else None


class Adversarial(unittest.TestCase):
    def test_every_row_of_the_table_lands_where_it_must(self):
        for message, expected in ADVERSARIAL:
            with self.subTest(message):
                got = one(message)
                if expected is None:
                    self.assertIsNone(got)
                else:
                    self.assertIsNotNone(got)
                    self.assertEqual((got.field, got.value), expected)

    def test_praise_carrying_a_correction_is_a_correction_not_a_verdict(self):
        got = one("good but fix the thumbnail")
        self.assertEqual(got.field, "correction")
        self.assertNotEqual(got.value, "negative")

    def test_bare_good_is_not_acceptance_but_looks_good_is(self):
        self.assertIsNone(one("good"))
        self.assertEqual(one("looks good").value, "accepted")

    def test_correction_outranks_negative_in_the_same_message(self):
        got = one("la miniatura no sirve; cambiala")
        self.assertEqual(got.field, "correction")


class Muting(unittest.TestCase):
    def test_muted_phrases_emit_nothing_at_all(self):
        for message in ("not bad", "not terrible", "no complaints",
                        "no complaint from me"):
            with self.subTest(message):
                self.assertEqual(fb.assess([message]), [])

    def test_a_mute_wins_even_when_a_rule_would_also_match(self):
        self.assertEqual(fb.assess(["not bad, ship it"]), [])


class Patterns(unittest.TestCase):
    def test_no_pattern_contains_a_bare_ambiguous_token(self):
        sources = [p.pattern for p in fb.MUTE]
        sources += [row[0].pattern for row in fb.RULES]
        for token in ("no", "not", "bad", "but"):
            bare = r"\b%s\b" % token
            for source in sources:
                with self.subTest(token=token, pattern=source):
                    self.assertNotEqual(source, bare)

    def test_bare_tokens_alone_classify_as_nothing(self):
        for message in ("no", "not", "bad", "but"):
            with self.subTest(message):
                self.assertEqual(fb.assess([message]), [])

    def test_a_row_under_the_threshold_is_documented_but_silent(self):
        weak = [row for row in fb.RULES if row[3] < fb.THRESHOLD]
        self.assertTrue(weak)
        for row in weak:
            with self.subTest(row[0].pattern):
                self.assertTrue(row[4])

    def test_every_row_carries_a_reason(self):
        for row in fb.RULES:
            with self.subTest(row[0].pattern):
                self.assertTrue(row[4].strip())


class Spanish(unittest.TestCase):
    def test_accented_and_unaccented_stems_both_correct(self):
        for message in ("cambiala por favor", "cámbiala por favor",
                        "arregla el borde", "corrige el texto",
                        "corrígelo por favor"):
            with self.subTest(message):
                got = one(message)
                self.assertIsNotNone(got)
                self.assertEqual(got.field, "correction")
                self.assertEqual(got.value, message)

    def test_spanish_negatives_are_negative_when_nothing_asks_for_a_fix(self):
        for message in ("no sirve", "está roto"):
            with self.subTest(message):
                self.assertEqual(one(message).value, "negative")


class Shape(unittest.TestCase):
    def test_empty_and_whitespace_messages_yield_nothing(self):
        self.assertEqual(fb.assess(["", "   ", "\n\t"]), [])

    def test_a_message_matching_nothing_yields_nothing(self):
        self.assertEqual(fb.assess(["the render took four seconds"]), [])

    def test_no_messages_at_all_yields_nothing(self):
        self.assertEqual(fb.assess([]), [])

    def test_at_most_one_candidate_per_message(self):
        messages = [m for m, _ in ADVERSARIAL] * 2
        self.assertLessEqual(len(fb.assess(messages)), len(messages))

    def test_candidates_come_back_in_input_order(self):
        messages = ["ship it", "fix the crop", "garbage"]
        self.assertEqual([c.field for c in fb.assess(messages)],
                         ["status", "correction", "sentiment"])

    def test_evidence_is_always_the_exact_original_message(self):
        messages = ["  Ship It  ", "FIX the crop", "totally Useless"]
        got = fb.assess(messages)
        self.assertEqual([c.evidence for c in got], messages)

    def test_reasons_are_a_non_empty_tuple_and_confidence_clears_threshold(self):
        for candidate in fb.assess([m for m, _ in ADVERSARIAL]):
            with self.subTest(candidate.evidence):
                self.assertIsInstance(candidate.reasons, tuple)
                self.assertTrue(candidate.reasons)
                self.assertGreaterEqual(candidate.confidence, fb.THRESHOLD)

    def test_assess_writes_nothing_and_needs_no_package(self):
        source = Path(fb.__file__).read_text(encoding="utf-8")
        for banned in ("open(", "write_text", "Path(", "import tokens_qa",
                       "import shot_contract"):
            with self.subTest(banned):
                self.assertNotIn(banned, source)


class CorrectionBundleIsBounded(unittest.TestCase):
    """Handing an adapter the whole record is how one rejected round becomes a
    rewrite of the skill that produced it."""

    shot = {
        "shot_id": "abc", "scope": "render one hero",
        "secret": "must not travel",
        "inputs": {"request": "a long private request", "prompt_hash": "sha256:x"},
        "output": {"adapter": "graphic",
                   "artifacts": [{"role": "deliverable", "path": "shots/hero.png"}]},
        "findings": [{"id": "scope_breach", "status": "present"},
                     {"id": "context_derail", "status": "absent"}],
        "user_feedback": {"status": "corrected", "correction": "fix the thumbnail",
                          "observed_at": "2026-09-01T00:00:00Z"},
    }

    def test_the_bundle_carries_exactly_the_declared_keys(self):
        self.assertEqual(set(fb.correction_bundle(self.shot)), set(fb.BUNDLE))

    def test_nothing_outside_the_bundle_travels(self):
        blob = json.dumps(fb.correction_bundle(self.shot))
        self.assertNotIn("must not travel", blob)
        self.assertNotIn("a long private request", blob)

    def test_only_findings_marked_present_are_carried(self):
        self.assertEqual(fb.correction_bundle(self.shot)["findings"], ["scope_breach"])

    def test_declared_artifacts_are_used_when_none_are_named(self):
        self.assertEqual(fb.correction_bundle(self.shot)["artifacts"],
                         ["shots/hero.png"])

    def test_named_artifacts_win_over_declared_ones(self):
        got = fb.correction_bundle(self.shot, artifacts=["design/thumb.png"])
        self.assertEqual(got["artifacts"], ["design/thumb.png"])

    def test_explicit_evidence_wins_over_the_recorded_correction(self):
        got = fb.correction_bundle(self.shot, evidence="the crop is wrong")
        self.assertEqual(got["evidence"], "the crop is wrong")

    def test_a_record_with_no_feedback_yields_empty_strings_not_a_crash(self):
        got = fb.correction_bundle({"shot_id": "x", "scope": "y"})
        self.assertEqual(got["evidence"], "")
        self.assertEqual(got["artifacts"], [])


class ACorrectionIsStrongerThanAComplaint(unittest.TestCase):
    """"It's broken" is a symptom. "I asked for X" is still outstanding.

    These moved here from cook, which used to keep its own copy of the rules
    beside a call asking this package for the same judgement.
    """

    def test_an_unmet_instruction_is_a_correction(self):
        for text in ("i initially requested to take over the design website",
                     "you did not create a css layout"):
            self.assertTrue(any(p.search(text) for p in fb.CORRECTION), text)

    def test_plain_praise_is_not_a_correction(self):
        self.assertFalse(any(p.search("that screenshot looks great")
                             for p in fb.CORRECTION))

    def test_an_instruction_restated_is_one_that_did_not_land(self):
        texts = ["i initially requested to take over the claude design website",
                 "you did not follow instructions about the claude design website"]
        self.assertEqual(fb.repeated(texts), [texts[1]])

    def test_two_unrelated_corrections_are_not_a_restatement(self):
        self.assertEqual(fb.repeated(["i asked for a css layout on the rails",
                                      "you did not translate the companion copy"]), [])

    def test_frustration_alone_is_a_complaint_not_a_correction(self):
        got = fb.audit(["this is broken"])
        self.assertEqual(got["complaints"], ["this is broken"])
        self.assertEqual(got["corrections"], [])


if __name__ == "__main__":
    unittest.main()
