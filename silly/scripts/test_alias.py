#!/usr/bin/env python3
"""What `alias.py` must refuse.

The one that matters is the clobber guard. This tool writes into a folder full
of skills somebody installed on purpose, so the interesting tests are the ones
where it declines to write.

    python3 -m unittest test_alias
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import alias

MANIFEST = """---
name: knowledge
description: Distils sources. In Spanish it answers to enciclopedia.
translations:
  es: enciclopedia
  ja: hyakka
aliases:
  - nerd-mode
also:
  - reads the docs :: An index row can mention this too
---

# Knowledge
"""


class Frontmatter(unittest.TestCase):
    def test_reads_both_nested_shapes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "SKILL.md"
            path.write_text(MANIFEST, encoding="utf-8")
            fields, translations, aliases, also = alias.frontmatter(path)
        self.assertEqual(fields["name"], "knowledge")
        self.assertEqual(translations, {"es": "enciclopedia", "ja": "hyakka"})
        self.assertEqual(aliases, ["nerd-mode"])
        self.assertEqual(also, [("reads the docs", "An index row can mention this too")])

    def test_no_block_yields_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "SKILL.md"
            path.write_text("# no frontmatter\n", encoding="utf-8")
            self.assertEqual(alias.frontmatter(path), ({}, {}, [], []))


class Tree(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        (self.root / "knowledge").mkdir()
        (self.root / "knowledge" / "SKILL.md").write_text(MANIFEST, encoding="utf-8")
        (self.root / "ora").mkdir()
        (self.root / "ora" / "SKILL.md").write_text(
            "---\nname: ora\ndescription: Spanish voice.\n---\n", encoding="utf-8")

    def run_link(self, *extra: str) -> int:
        return alias.main(["link", "--root", str(self.root), *extra])

    def test_manifest_lists_every_declared_name(self):
        rows = alias.manifested(self.root)
        self.assertEqual([(a, c, k) for a, c, k, _ in rows],
                         [("enciclopedia", "knowledge", "es"),
                          ("hyakka", "knowledge", "ja"),
                          ("nerd-mode", "knowledge", "fun")])

    def test_one_language_installs_only_that_language(self):
        self.assertEqual(self.run_link("--lang", "es"), 0)
        self.assertTrue((self.root / "enciclopedia" / "SKILL.md").is_file())
        self.assertFalse((self.root / "hyakka").exists())
        self.assertFalse((self.root / "nerd-mode").exists())

    def test_the_stub_carries_the_new_name_not_the_old_one(self):
        self.run_link("--lang", "es")
        text = (self.root / "enciclopedia" / "SKILL.md").read_text()
        self.assertIn("name: enciclopedia", text)
        self.assertIn("alias_of: knowledge", text)
        self.assertIn("disable-model-invocation: true", text)

    def test_fun_names_are_opt_in_and_separate(self):
        self.assertEqual(self.run_link("--fun"), 0)
        self.assertTrue((self.root / "nerd-mode").exists())
        self.assertFalse((self.root / "enciclopedia").exists())

    def test_asking_for_nothing_is_an_error_not_a_no_op(self):
        self.assertEqual(self.run_link(), 1)

    def test_refuses_to_overwrite_a_real_skill(self):
        (self.root / "enciclopedia").mkdir()
        (self.root / "enciclopedia" / "SKILL.md").write_text(
            "---\nname: enciclopedia\ndescription: someone's own work\n---\n",
            encoding="utf-8")
        self.assertEqual(self.run_link("--lang", "es"), 1)
        self.assertIn("someone's own work",
                      (self.root / "enciclopedia" / "SKILL.md").read_text())

    def test_relinking_its_own_alias_is_fine(self):
        self.run_link("--lang", "es")
        self.assertEqual(self.run_link("--lang", "es"), 0)

    def test_an_alias_never_manifests_aliases_of_its_own(self):
        self.run_link("--lang", "es")
        self.assertEqual(len(alias.manifested(self.root)), 3)

    def test_unlink_removes_only_what_it_wrote(self):
        self.run_link("--lang", "es", )
        self.assertEqual(alias.main(["unlink", "--root", str(self.root)]), 0)
        self.assertFalse((self.root / "enciclopedia").exists())
        self.assertTrue((self.root / "knowledge" / "SKILL.md").is_file())
        self.assertTrue((self.root / "ora" / "SKILL.md").is_file())

    def test_dry_run_writes_nothing(self):
        self.run_link("--lang", "es", "--dry-run")
        self.assertFalse((self.root / "enciclopedia").exists())

    def test_a_missing_root_fails_rather_than_creating_one(self):
        self.assertEqual(
            alias.main(["list", "--root", str(self.root / "nope")]), 1)


if __name__ == "__main__":
    unittest.main()
