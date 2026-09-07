#!/usr/bin/env python3
"""The Skill Catalog is one fact seen through several adapters."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import skill_discovery


class SkillCatalogTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def skill(self, relative: str, frontmatter: str, body: str = "") -> Path:
        directory = self.root / relative
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "SKILL.md").write_text(
            f"---\n{frontmatter.strip()}\n---\n\n{body}", encoding="utf-8")
        return directory

    def test_record_owns_identity_family_channel_names_origin_path_and_size(self) -> None:
        self.skill("kit", "name: kit\ndescription: Day zero.", "setup")
        genesis = self.skill(
            "first/genesis",
            """name: genesis
description: Plans work. In Spanish it answers to origen; also called plan.
translations:
  es: origen
aliases:
  - plan
also:
  - first-plan-roadmap :: Update the state""",
            "señal",
        )

        records = {record.name: record for record in skill_discovery.catalog(self.root)}

        self.assertEqual(records["kit"].family, "kit")
        self.assertEqual(records["kit"].channel, "main")
        record = records["genesis"]
        self.assertEqual(record.family, "first")
        self.assertEqual(record.channel, "alpha")
        self.assertEqual(record.translations, (("es", "origen"),))
        self.assertEqual(record.aliases, ("plan",))
        self.assertEqual(record.also, (("first-plan-roadmap", "Update the state"),))
        self.assertEqual(record.names, ("genesis", "origen", "plan"))
        self.assertEqual(record.origin, "yoshi-ortiz/cyber-skills")
        self.assertEqual(record.path, genesis.relative_to(self.root))
        self.assertEqual(record.body, "señal")
        self.assertEqual(record.body_bytes, len("señal".encode("utf-8")))

    def test_alias_stub_is_not_a_canonical_record(self) -> None:
        self.skill("kit", "name: kit\ndescription: Day zero.")
        self.skill("kit/old-kit", "name: old-kit\nalias_of: kit")
        self.assertEqual([record.name for record in skill_discovery.catalog(self.root)],
                         ["kit"])

    def test_duplicate_canonical_names_fail_instead_of_overwriting(self) -> None:
        self.skill("first/shared", "name: shared")
        self.skill("check/shared", "name: shared")
        with self.assertRaisesRegex(ValueError, "duplicate skill name 'shared'"):
            skill_discovery.catalog(self.root)

    def test_path_owner_matches_the_skill_root_not_an_unrelated_component(self) -> None:
        self.skill("first/genesis", "name: genesis")
        records = skill_discovery.catalog(self.root)
        self.assertIsNone(skill_discovery.owner_of(Path("assets/genesis/icon.svg"), records))
        self.assertEqual(
            skill_discovery.owner_of(Path("first/genesis/references/a.md"), records).name,
            "genesis",
        )

    def test_family_exits_form_one_catalog_graph(self) -> None:
        self.skill("build", "name: build\nexits: first, land, fix")
        records = skill_discovery.catalog(self.root)
        self.assertEqual(skill_discovery.rail_graph(records),
                         {"build": ("first", "land", "fix")})
        self.assertTrue(skill_discovery.allows_exit(records, "build", "land"))
        self.assertFalse(skill_discovery.allows_exit(records, "build", "check"))


if __name__ == "__main__":
    unittest.main()
