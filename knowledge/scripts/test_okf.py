#!/usr/bin/env python3
"""What `okf.py` must refuse.

The capture path is exercised against a local file rather than a URL: the
fetch is `urlopen`, which is the standard library's problem, and everything
this script decides -- slug, frontmatter, clobber refusal -- happens either
side of it.

    python3 -m unittest test_okf
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import okf


class Frontmatter(unittest.TestCase):
    def test_reads_top_level_pairs(self):
        fields = okf.frontmatter("---\ntype: Reference\ntitle: A\n---\n\nbody\n")
        self.assertEqual(fields, {"type": "Reference", "title": "A"})

    def test_skips_nested_keys(self):
        fields = okf.frontmatter("---\ntype: R\ngenerated:\n  by: x/1\n---\n")
        self.assertEqual(fields, {"type": "R", "generated": ""})
        self.assertNotIn("by", fields)

    def test_no_block_is_not_an_empty_block(self):
        self.assertIsNone(okf.frontmatter("# Just a heading\n"))


class Text(unittest.TestCase):
    def test_drops_script_and_tags_and_unescapes(self):
        text = okf.to_text("<p>a &amp; b</p><script>var x = 1;</script>")
        self.assertEqual(text, "a & b")

    def test_plain_text_passes_through(self):
        self.assertEqual(okf.to_text("already text"), "already text")


class Slug(unittest.TestCase):
    def test_collapses_punctuation(self):
        self.assertEqual(okf.slugify("Prisma  Migrate: v6!"), "prisma-migrate-v6")

    def test_never_empty(self):
        self.assertEqual(okf.slugify("!!!"), "concept")


class Capture(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.source = self.tmp / "source.html"
        self.source.write_text("<h1>Title</h1><p>fact</p>", encoding="utf-8")
        self.root = self.tmp / "knowledge"

    def run_new(self, *extra: str) -> int:
        return okf.main(["new", str(self.source), "--root", str(self.root),
                         "--title", "Thing", *extra])

    def test_writes_a_draft_stub_with_provenance(self):
        self.assertEqual(self.run_new("--by", "human:me"), 0)
        text = (self.root / "thing.md").read_text(encoding="utf-8")
        self.assertIn("type: Reference", text)
        self.assertIn("status: draft", text)
        self.assertIn("by: human:me", text)
        self.assertIn(f"resource: {self.source}", text)

    def test_refuses_to_clobber_without_force(self):
        self.run_new()
        (self.root / "thing.md").write_text("distilled\n", encoding="utf-8")
        self.assertEqual(self.run_new(), 1)
        self.assertEqual((self.root / "thing.md").read_text(), "distilled\n")
        self.assertEqual(self.run_new("--force"), 0)

    def test_missing_source_fails_rather_than_writing(self):
        self.assertEqual(
            okf.main(["new", "http://localhost:1/nope", "--root", str(self.root)]), 1)
        self.assertFalse(any(self.root.glob("*.md")) if self.root.exists() else False)


class Check(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())

    def write(self, name: str, text: str):
        (self.root / name).write_text(text, encoding="utf-8")

    def test_conforming_bundle_passes(self):
        self.write("a.md", "---\ntype: Reference\n---\n\nbody\n")
        self.write("index.md", "# Index\n\n- [A](a.md)\n")
        self.assertEqual(okf.main(["check", "--root", str(self.root)]), 0)

    def test_empty_type_fails(self):
        self.write("a.md", "---\ntype:\n---\n")
        self.write("index.md", "- [A](a.md)\n")
        self.assertEqual(okf.main(["check", "--root", str(self.root)]), 1)

    def test_missing_frontmatter_fails(self):
        self.write("a.md", "# A\n")
        self.write("index.md", "- [A](a.md)\n")
        self.assertEqual(okf.main(["check", "--root", str(self.root)]), 1)

    def test_unindexed_concept_fails(self):
        self.write("a.md", "---\ntype: Reference\n---\n")
        self.write("index.md", "# Index\n")
        self.assertEqual(okf.main(["check", "--root", str(self.root)]), 1)

    def test_broken_index_link_fails(self):
        self.write("a.md", "---\ntype: Reference\n---\n")
        self.write("index.md", "- [A](a.md)\n- [B](b.md)\n")
        self.assertEqual(okf.main(["check", "--root", str(self.root)]), 1)

    def test_index_and_log_need_no_frontmatter(self):
        self.write("a.md", "---\ntype: Reference\n---\n")
        self.write("index.md", "- [A](a.md)\n")
        self.write("log.md", "# Log\n")
        self.assertEqual(okf.main(["check", "--root", str(self.root)]), 0)

    def test_empty_directory_needs_no_index(self):
        self.assertEqual(okf.main(["check", "--root", str(self.root)]), 0)


if __name__ == "__main__":
    unittest.main()


class Ignore(unittest.TestCase):
    """A bundle that shares its directory with something else it does not own."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        (self.root / "a.md").write_text("---\ntype: Reference\n---\n", encoding="utf-8")
        (self.root / "index.md").write_text("- [A](a.md)\n", encoding="utf-8")
        (self.root / "CONTEXT.md").write_text("# not a concept\n", encoding="utf-8")

    def test_a_foreign_file_fails_by_default(self):
        self.assertEqual(okf.main(["check", "--root", str(self.root)]), 1)

    def test_ignoring_it_passes(self):
        self.assertEqual(okf.main(
            ["check", "--root", str(self.root), "--ignore", "CONTEXT.md"]), 0)

    def test_an_ignored_link_is_not_a_broken_link(self):
        (self.root / "index.md").write_text("- [A](a.md)\n- [C](CONTEXT.md)\n",
                                            encoding="utf-8")
        self.assertEqual(okf.main(
            ["check", "--root", str(self.root), "--ignore", "CONTEXT.md"]), 0)
