"""Tests for the checkable subset of the design golden rules.

Expected values come from references/graphic-design-fundamentals.md, never from
recomputing what the implementation does. Each test cites its source line.
"""
import unittest

import golden_rules as gr


class Measure(unittest.TestCase):
    """Arizona accessible-branding guidance: 45–75 characters per line."""

    def test_sixty_two_characters_is_within_the_optimal_measure(self):
        line = "The quick brown fox jumps over the lazy dog, twice over now."
        self.assertEqual(len(line), 60)          # fixture is what it claims
        self.assertTrue(gr.measure(line).ok)

    def test_thirty_characters_is_too_tight(self):
        result = gr.measure("Short ragged column of text.")
        self.assertFalse(result.ok)
        self.assertIn("45", result.detail)

    def test_ninety_characters_is_too_loose(self):
        long_line = "A" * 90
        result = gr.measure(long_line)
        self.assertFalse(result.ok)
        self.assertIn("75", result.detail)

    def test_the_boundaries_themselves_are_acceptable(self):
        self.assertTrue(gr.measure("A" * 45).ok)
        self.assertTrue(gr.measure("A" * 75).ok)


class ValueContrast(unittest.TestCase):
    """Expected ratios come from WCAG 2.2 success criterion 1.4.3."""

    def test_black_on_white_is_the_maximum_ratio(self):
        self.assertAlmostEqual(gr.contrast_ratio("#000000", "#FFFFFF"), 21.0, places=1)

    def test_white_on_white_has_no_contrast(self):
        self.assertAlmostEqual(gr.contrast_ratio("#FFFFFF", "#FFFFFF"), 1.0, places=1)

    def test_the_wcag_boundary_grey_lands_just_above_four_point_five(self):
        # #767676 on white is WCAG's canonical "just passes AA" example.
        self.assertAlmostEqual(gr.contrast_ratio("#767676", "#FFFFFF"), 4.54, places=1)

    def test_shorthand_and_case_are_accepted(self):
        self.assertAlmostEqual(gr.contrast_ratio("#000", "#fff"), 21.0, places=1)

    def test_body_text_below_four_point_five_fails_the_rule(self):
        self.assertFalse(gr.contrast("#999999", "#FFFFFF").ok)

    def test_body_text_at_or_above_four_point_five_passes(self):
        self.assertTrue(gr.contrast("#767676", "#FFFFFF").ok)

    def test_the_failure_says_what_was_measured(self):
        result = gr.contrast("#CCCCCC", "#FFFFFF")
        self.assertFalse(result.ok)
        self.assertIn("4.5", result.detail)


FULLY_DECLARED = {
    "body": {"sample_line": "A" * 62, "ink": "#111111", "paper": "#FFFFFF"},
    "grid": "modular",
    "gestalt": ["proximity", "similarity"],
    "register": "symbol",
}


class Declaration(unittest.TestCase):
    """A design decision is PINNED when the spec names it, so a rule can decide
    it. Undeclared decisions are FREE -- that is where two runs diverge."""

    def test_a_named_grid_is_pinned(self):
        self.assertTrue(gr.grid("modular").pinned)

    def test_an_unnamed_grid_is_free_not_failing(self):
        result = gr.grid(None)
        self.assertFalse(result.pinned)
        self.assertFalse(result.ok)

    def test_an_invented_grid_type_is_pinned_but_wrong(self):
        # Declared, therefore checkable, therefore deterministic -- and wrong.
        result = gr.grid("vibes")
        self.assertTrue(result.pinned)
        self.assertFalse(result.ok)

    def test_the_three_canonical_grids_are_accepted(self):
        for name in ("manuscript", "column", "modular"):
            self.assertTrue(gr.grid(name).ok, name)

    def test_gestalt_grouping_must_name_a_law(self):
        self.assertTrue(gr.gestalt(["proximity"]).ok)
        self.assertFalse(gr.gestalt([]).pinned)
        self.assertFalse(gr.gestalt(["telepathy"]).ok)

    def test_semiotic_register_must_be_one_of_peirces_three(self):
        for name in ("icon", "index", "symbol"):
            self.assertTrue(gr.register(name).ok, name)
        self.assertFalse(gr.register(None).pinned)
        self.assertFalse(gr.register("logo").ok)


class Coverage(unittest.TestCase):
    """The benchmark. Coverage is the determinism lever: it counts decisions a
    rule can decide, whether or not they pass."""

    def test_a_fully_declared_design_reaches_total_coverage(self):
        report = gr.evaluate(FULLY_DECLARED)
        self.assertEqual(report.coverage, 1.0)
        self.assertEqual(report.free, [])

    def test_an_empty_design_pins_nothing(self):
        report = gr.evaluate({})
        self.assertEqual(report.coverage, 0.0)
        self.assertEqual(len(report.free), report.total)

    def test_coverage_counts_pinned_decisions_not_passing_ones(self):
        # Every decision declared; the contrast is declared and terrible.
        bad = dict(FULLY_DECLARED,
                   body={"sample_line": "A" * 62, "ink": "#EEEEEE", "paper": "#FFFFFF"})
        report = gr.evaluate(bad)
        self.assertEqual(report.coverage, 1.0)       # fully deterministic
        self.assertFalse(report.passing)             # and fully wrong
        self.assertIn("contrast", [c.rule for c in report.failures])

    def test_dropping_one_declaration_lowers_coverage_by_one_slot(self):
        partial = {k: v for k, v in FULLY_DECLARED.items() if k != "register"}
        full = gr.evaluate(FULLY_DECLARED)
        report = gr.evaluate(partial)
        self.assertEqual(report.total, full.total)
        self.assertEqual(len(report.free), 1)
        self.assertEqual([c.rule for c in report.free], ["register"])

    def test_the_report_is_deterministic_for_a_given_design(self):
        self.assertEqual(gr.evaluate(FULLY_DECLARED), gr.evaluate(FULLY_DECLARED))


class Rendering(unittest.TestCase):
    """The benchmark has to be readable in a terminal, and byte-stable."""

    def test_the_rendered_report_names_free_decisions_explicitly(self):
        partial = {k: v for k, v in FULLY_DECLARED.items() if k != "grid"}
        text = gr.render(gr.evaluate(partial))
        self.assertIn("FREE", text)
        self.assertIn("grid", text)

    def test_it_leads_with_coverage(self):
        self.assertIn("coverage", gr.render(gr.evaluate(FULLY_DECLARED)).split("\n")[0])

    def test_rendering_is_byte_stable(self):
        self.assertEqual(gr.render(gr.evaluate(FULLY_DECLARED)),
                         gr.render(gr.evaluate(FULLY_DECLARED)))


class Scaffold(unittest.TestCase):
    """Declaring must be the default path. A blank scaffold names every slot, so
    the agent fills them in rather than inventing the shape per session."""

    def test_the_scaffold_names_every_checkable_slot(self):
        spec = gr.scaffold("cover.ring.kicker")
        self.assertEqual(gr.evaluate(spec).total, len(gr.evaluate(FULLY_DECLARED).checks))
        self.assertIn("element", spec)

    def test_a_blank_scaffold_pins_nothing(self):
        self.assertEqual(gr.evaluate(gr.scaffold("x")).coverage, 0.0)

    def test_the_scaffold_carries_the_legal_values_for_each_choice(self):
        spec = gr.scaffold("x")
        self.assertEqual(spec["choices"]["grid"], list(gr.GRIDS))
        self.assertEqual(spec["choices"]["register"], list(gr.REGISTERS))
        self.assertEqual(spec["choices"]["gestalt"], list(gr.GESTALT_LAWS))

    def test_filling_the_scaffold_reaches_total_coverage(self):
        spec = gr.scaffold("x")
        spec["grid"] = "column"
        spec["gestalt"] = ["closure"]
        spec["register"] = "index"
        spec["body"] = {"sample_line": "A" * 55, "ink": "#000", "paper": "#FFF"}
        self.assertEqual(gr.evaluate(spec).coverage, 1.0)

    def test_choices_are_not_mistaken_for_declarations(self):
        self.assertEqual(gr.evaluate(gr.scaffold("x")).coverage, 0.0)


if __name__ == "__main__":
    unittest.main()
