"""Tests for Round Scope: how far a round is allowed to reach.

Split out of `test_rounds.py`, which is at its directory's byte budget --
`test_article.py` was split off it for the same reason. Scope is its own
concern anyway: `test_rounds.py` asks whether a round earns its place and fits
in one sitting, and this file asks whether it stayed on one object.

The failure these guard against is the expensive one. Nothing stopped a cohort
from spanning two unrelated parent items, so an inference pass would read the
whole ledger, reason across every surface in it, and return one thin drawing
for each -- a long run, wide reasoning, minimal output, because attention that
should have gone into one cover went into six unrelated things.
"""
import unittest

import bootstrap_harness as bh


class TheParentItemIsReadOffTheId(unittest.TestCase):
    """The dotted id already carries the object. No new field, no migration."""

    def test_the_parent_item_is_the_first_segment(self):
        self.assertEqual(bh.parent_item_of("cover.ring.kicker.antetitulo"), "cover")

    def test_an_id_with_no_dots_is_its_own_parent_item(self):
        self.assertEqual(bh.parent_item_of("cover"), "cover")


class ARoundMustStayOnOneObject(unittest.TestCase):

    def test_a_cohort_under_one_parent_item_is_allowed(self):
        bh.check_round_stays_in_scope({"cover.layout.two-column",
                                       "cover.ring.kicker",
                                       "cover.mark.dotmatrix"})

    def test_a_cohort_spanning_two_parent_items_is_refused(self):
        with self.assertRaises(bh.HarnessError) as caught:
            bh.check_round_stays_in_scope({"cover.layout.two-column",
                                           "type.heading.serif"})
        message = str(caught.exception)
        self.assertIn("cover", message)
        self.assertIn("type", message)

    def test_the_refusal_names_every_item_the_round_spans(self):
        with self.assertRaises(bh.HarnessError) as caught:
            bh.check_round_stays_in_scope({"cover.layout.a", "type.heading.b",
                                           "palette.warm.c"})
        self.assertIn("3 parent items", str(caught.exception))

    def test_a_parent_item_and_its_own_children_are_one_item(self):
        # Re-asking the parent beside a redraw of it is the same object.
        bh.check_round_stays_in_scope({"cover", "cover.layout.two-column"})

    def test_a_single_element_round_is_always_in_scope(self):
        bh.check_round_stays_in_scope({"anything.at.all"})

    def test_an_empty_cohort_is_fine(self):
        bh.check_round_stays_in_scope(set())

    def test_scope_has_no_escape_hatch(self):
        # `--asks` answers the foundation-span check in `render_article`: it
        # explains a round that needs explaining. It must not answer this one,
        # because no sentence turns two objects into one round. The end-to-end
        # proof that `--asks` cannot buy a way past this lives in
        # `test_adopt.test_asks_does_not_buy_a_round_out_of_its_parent_item`.
        with self.assertRaises(bh.HarnessError):
            bh.check_round_stays_in_scope({"cover.layout.a", "type.heading.b"})


class ALineageIsFollowedToItsRoot(unittest.TestCase):
    """`incumbent_of` answers one step. The chart needs the whole chain, so it
    can say "these five bars are five attempts at one idea"."""

    def test_an_element_with_no_ancestor_is_its_own_root(self):
        self.assertEqual(bh.lineage_root_of("cover.ring", {"cover.ring"}),
                         "cover.ring")

    def test_a_chain_resolves_to_the_original_idea(self):
        known = {"cover.ring", "cover.ring.v2", "cover.ring.v2.v3"}
        self.assertEqual(bh.lineage_root_of("cover.ring.v2.v3", known), "cover.ring")

    def test_an_unrecorded_ancestor_does_not_break_the_chain(self):
        # `cover.ring.v2` was never written to the ledger; the walk still
        # reaches the root it can see rather than stopping or looping.
        known = {"cover.ring", "cover.ring.v2.v3"}
        self.assertEqual(bh.lineage_root_of("cover.ring.v2.v3", known), "cover.ring")

    def test_unrelated_ideas_have_different_roots(self):
        known = {"cover.ring", "palette.warm"}
        self.assertNotEqual(bh.lineage_root_of("cover.ring", known),
                            bh.lineage_root_of("palette.warm", known))


if __name__ == "__main__":
    unittest.main()
