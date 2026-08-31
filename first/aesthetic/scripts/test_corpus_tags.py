"""Tests for corpus tags: what the user says their references are for.

The bug these exist against is measurable. A real 135-item corpus produced 8
observations and 127 boilerplate omissions in `art-direction.json`, rewritten
every round, because nothing recorded which references the user actually
cared about.
"""
import json
import hashlib
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

import bootstrap_harness as bh
import corpus_tags as ct
from editorial_workflow import STORE, WorkflowError


def project(root: Path, *paths: str) -> Path:
    """A corpus of files whose sha256 is derived from the path, so a test can
    predict a digest without hashing bytes it never wrote."""
    store = root / STORE
    store.mkdir(parents=True, exist_ok=True)
    items = [{"id": f"image-{i}", "path": p, "kind": "image",
              "sha256": f"{i:064x}", "bytes": 1}
             for i, p in enumerate(paths)]
    (store / "corpus.json").write_text(
        json.dumps({"version": 1, "root": "/x", "modalities": ["image"],
                    "items": items}), encoding="utf-8")
    return root


def tag(root: Path, group: str, aspects: list[str], **kw) -> int:
    return ct.tag_group(root, {"group": group, "aspects": aspects,
                               "stance": kw.get("stance", "pursue"),
                               "quality": kw.get("quality", "finished"),
                               "note": kw.get("note", ""),
                               "at": "2026-08-22T00:00:00-06:00"})


class TheVocabularyMatchesTheDesignSystem(unittest.TestCase):
    """ASPECTS is copied from bootstrap_harness rather than imported, to avoid
    a cycle. That copy is only safe while something checks it."""

    def test_aspects_are_exactly_the_foundations(self):
        self.assertEqual(ct.ASPECTS, tuple(key for key, _ in bh.FOUNDATIONS))


class AFolderIsTheUnitOfTagging(unittest.TestCase):
    def test_a_folder_tag_reaches_every_item_inside_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(Path(tmp), "strong color/a.jpg", "strong color/b.jpg",
                           "manuals/c.jpg")
            self.assertEqual(tag(root, "strong color", ["palette"]), 2)
            self.assertEqual(len(ct.load_tags(root)["tags"]), 2)

    def test_a_file_at_the_corpus_root_still_has_a_group(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(Path(tmp), "loose.jpg")
            self.assertEqual(tag(root, ct.ROOT_GROUP, ["core"]), 1)

    def test_an_unknown_folder_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(Path(tmp), "manuals/c.jpg")
            with self.assertRaises(WorkflowError):
                tag(root, "not a folder", ["core"])

    def test_tags_are_stored_against_the_hash_not_the_path(self):
        # Renaming the folder must not orphan the tag: the key follows bytes.
        with tempfile.TemporaryDirectory() as tmp:
            root = project(Path(tmp), "strong color/a.jpg")
            tag(root, "strong color", ["palette"])
            stored = ct.load_tags(root)["tags"]
            self.assertEqual(list(stored), [f"{0:064x}"])

    def test_retagging_a_folder_replaces_the_earlier_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(Path(tmp), "manuals/c.jpg")
            tag(root, "manuals", ["palette"])
            tag(root, "manuals", ["voice"], stance="avoid")
            entry = list(ct.load_tags(root)["tags"].values())[0]
            self.assertEqual(entry["aspects"], ["voice"])
            self.assertEqual(entry["stance"], "avoid")


class TheSchemaIsOwnedHere(unittest.TestCase):
    """The companion validates almost nothing; this is the only gate."""

    def test_an_unknown_aspect_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(Path(tmp), "manuals/c.jpg")
            with self.assertRaises(WorkflowError):
                tag(root, "manuals", ["vibes"])

    def test_an_unknown_stance_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(Path(tmp), "manuals/c.jpg")
            with self.assertRaises(WorkflowError):
                tag(root, "manuals", ["core"], stance="maybe")

    def test_refine_is_a_distinct_attempt_stance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(Path(tmp), "attempts/candidate.png")
            ct.tag_group(root, {
                "group": "attempts", "aspects": ["composition"],
                "stance": "refine", "role": "attempt", "quality": "finished",
                "note": "keep room scale; repair the road", "at": "2026-08-31T00:00:00Z",
            })
            entry = next(iter(ct.load_tags(root)["tags"].values()))
            self.assertEqual((entry["stance"], entry["role"]), ("refine", "attempt"))

    def test_refine_is_refused_for_a_reference_role(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(Path(tmp), "references/candidate.png")
            with self.assertRaisesRegex(WorkflowError, "refine.*attempt"):
                ct.tag_group(root, {
                    "group": "references", "aspects": ["composition"],
                    "stance": "refine", "role": "reference", "quality": "finished",
                    "note": "repair it", "at": "2026-08-31T00:00:00Z",
                })

    def test_an_unknown_role_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(Path(tmp), "references/candidate.png")
            with self.assertRaisesRegex(WorkflowError, "role must be one of"):
                ct.tag_group(root, {
                    "group": "references", "aspects": ["composition"],
                    "stance": "pursue", "role": "vibes", "quality": "finished",
                    "note": "", "at": "2026-08-31T00:00:00Z",
                })

    def test_a_tag_with_no_aspect_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(Path(tmp), "manuals/c.jpg")
            with self.assertRaises(WorkflowError):
                tag(root, "manuals", [])

    def test_a_note_longer_than_the_limit_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(Path(tmp), "manuals/c.jpg")
            with self.assertRaises(WorkflowError):
                tag(root, "manuals", ["core"], note="x" * (ct.MAX_NOTE_CHARS + 1))

    def test_a_duplicate_aspect_collapses(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(Path(tmp), "manuals/c.jpg")
            tag(root, "manuals", ["core", "core", "voice"])
            entry = list(ct.load_tags(root)["tags"].values())[0]
            self.assertEqual(entry["aspects"], ["core", "voice"])

    def test_an_untagged_project_loads_as_empty_not_as_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(ct.load_tags(Path(tmp))["tags"], {})


class TaggingRetiresTheOmissionCeremony(unittest.TestCase):
    """The point of the whole module. `validate_art_direction` demanded an
    accounting for every corpus item, so 135 references cost 127 boilerplate
    dismissals per round. The unit is now the folder the user curated."""

    def test_an_untagged_project_still_accounts_for_every_item(self):
        # Existing projects must not change behaviour until the user opts in.
        with tempfile.TemporaryDirectory() as tmp:
            root = project(Path(tmp), "a/1.jpg", "a/2.jpg", "b/3.jpg")
            missing = ct.missing_evidence(ct.load_corpus(root), ct.load_tags(root), set())
            self.assertEqual(missing, ["image-0", "image-1", "image-2"])

    def test_an_untagged_project_credits_what_it_saw(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(Path(tmp), "a/1.jpg", "a/2.jpg")
            missing = ct.missing_evidence(ct.load_corpus(root), ct.load_tags(root),
                                          {"image-0"})
            self.assertEqual(missing, ["image-1"])

    def test_one_observation_accounts_for_its_whole_folder(self):
        # 32 references the user grouped and labelled once must not cost 32
        # separate dismissals.
        with tempfile.TemporaryDirectory() as tmp:
            root = project(Path(tmp), "a/1.jpg", "a/2.jpg", "a/3.jpg")
            tag(root, "a", ["palette"])
            missing = ct.missing_evidence(ct.load_corpus(root), ct.load_tags(root),
                                          {"image-0"})
            self.assertEqual(missing, [])

    def test_an_untouched_tagged_folder_is_still_refused(self):
        # The gate's real purpose survives: a folder the user pointed at
        # cannot be silently ignored.
        with tempfile.TemporaryDirectory() as tmp:
            root = project(Path(tmp), "a/1.jpg", "b/2.jpg")
            tag(root, "a", ["palette"])
            tag(root, "b", ["voice"])
            missing = ct.missing_evidence(ct.load_corpus(root), ct.load_tags(root),
                                          {"image-0"})
            self.assertEqual(missing, ["b"])

    def test_untagged_folders_stop_demanding_anything(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(Path(tmp), "a/1.jpg", "junk/2.jpg", "junk/3.jpg")
            tag(root, "a", ["palette"])
            missing = ct.missing_evidence(ct.load_corpus(root), ct.load_tags(root),
                                          {"image-0"})
            self.assertEqual(missing, [])

    def test_tagging_more_folders_never_costs_more_than_one_each(self):
        # The earlier item-keyed version made tagging MORE folders restore the
        # full burden, which inverted the incentive to curate.
        with tempfile.TemporaryDirectory() as tmp:
            root = project(Path(tmp), *[f"f{i}/{j}.jpg" for i in range(8)
                                        for j in range(20)])
            for i in range(8):
                tag(root, f"f{i}", ["palette"])
            missing = ct.missing_evidence(ct.load_corpus(root), ct.load_tags(root), set())
            self.assertEqual(len(missing), 8)


class TheDigestIsTheKeyTokens(unittest.TestCase):
    def test_aspects_are_counted_by_stance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(Path(tmp), "a/1.jpg", "b/2.jpg")
            tag(root, "a", ["palette"])
            tag(root, "b", ["palette"], stance="avoid")
            row = next(r for r in ct.digest_rows(root) if r["aspect"] == "palette")
            self.assertEqual((row["pursue"], row["avoid"]), (1, 1))

    def test_refine_attempts_are_counted_separately(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(Path(tmp), "attempts/one.png")
            ct.tag_group(root, {
                "group": "attempts", "aspects": ["composition"],
                "stance": "refine", "role": "attempt", "quality": "finished",
                "note": "keep scale", "at": "2026-08-31T00:00:00Z",
            })
            row = next(r for r in ct.digest_rows(root) if r["aspect"] == "composition")
            self.assertEqual((row["pursue"], row["refine"], row["avoid"]), (0, 1, 0))

    def test_sketches_are_counted_separately_from_finished_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(Path(tmp), "a/1.jpg")
            tag(root, "a", ["composition"], quality="sketch")
            row = next(r for r in ct.digest_rows(root) if r["aspect"] == "composition")
            self.assertEqual((row["pursue"], row["sketch"]), (1, 1))

    def test_the_untagged_remainder_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(Path(tmp), "a/1.jpg", "b/2.jpg", "b/3.jpg")
            tag(root, "a", ["core"])
            row = next(r for r in ct.digest_rows(root) if r["aspect"] == "untagged")
            self.assertEqual(row["count"], 2)

    def test_rows_follow_the_foundation_reading_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(Path(tmp), "a/1.jpg", "b/2.jpg")
            tag(root, "a", ["voice"])
            tag(root, "b", ["palette"])
            names = [r["aspect"] for r in ct.digest_rows(root)]
            self.assertLess(names.index("palette"), names.index("voice"))


class TheBrowserQueueIsAdoptedNotTrusted(unittest.TestCase):
    def test_adopting_an_inbox_applies_its_tags(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(Path(tmp), "a/1.jpg")
            inbox = root / "inbox.jsonl"
            inbox.write_text(json.dumps(
                {"group": "a", "aspects": ["palette"], "stance": "pursue",
                 "quality": "finished", "at": "2026-08-22T00:00:00-06:00"}) + "\n",
                encoding="utf-8")
            self.assertEqual(ct.adopt_inbox(root, inbox), (1, 0))
            self.assertEqual(len(ct.load_tags(root)["tags"]), 1)

    def test_a_malformed_line_is_skipped_not_fatal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(Path(tmp), "a/1.jpg")
            inbox = root / "inbox.jsonl"
            inbox.write_text('not json\n{"group":"nope","aspects":["core"]}\n',
                             encoding="utf-8")
            self.assertEqual(ct.adopt_inbox(root, inbox), (0, 2))

    def test_a_missing_inbox_is_not_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(Path(tmp), "a/1.jpg")
            self.assertEqual(ct.adopt_inbox(root, root / "absent.jsonl"), (0, 0))

    def test_readopting_the_same_inbox_lands_on_the_same_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(Path(tmp), "a/1.jpg")
            inbox = root / "inbox.jsonl"
            inbox.write_text(json.dumps(
                {"group": "a", "aspects": ["palette"], "stance": "pursue",
                 "quality": "finished", "at": "2026-08-22T00:00:00-06:00"}) + "\n",
                encoding="utf-8")
            ct.adopt_inbox(root, inbox)
            first = ct.load_tags(root)
            ct.adopt_inbox(root, inbox)
            self.assertEqual(ct.load_tags(root), first)


class TheModuleRendersOrStaysQuiet(unittest.TestCase):
    def test_a_project_with_no_corpus_renders_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(ct.render_corpus_tags(Path(tmp)), "")

    def test_a_fully_tagged_corpus_stops_asking(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(Path(tmp), "a/1.jpg")
            tag(root, "a", ["palette"])
            self.assertEqual(ct.untagged_groups(root), [])

    def test_the_largest_untagged_folder_is_asked_about_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(Path(tmp), "small/1.jpg", "big/2.jpg", "big/3.jpg")
            self.assertEqual(ct.untagged_groups(root)[0], ("big", 2))

    def test_only_one_folder_is_put_in_front_of_the_user(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(Path(tmp), "a/1.jpg", "b/2.jpg", "c/3.jpg")
            markup = ct.render_corpus_tags(root)
            self.assertEqual(markup.count("data-tags-group="), 1)
            self.assertIn('name="role"', markup)
            self.assertIn('value="refine"', markup)
            self.assertIn('name="note"', markup)

    def test_every_aspect_is_offered_as_a_choice(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(Path(tmp), "a/1.jpg")
            markup = ct.render_corpus_tags(root)
            for aspect in ct.ASPECTS:
                self.assertIn(f'value="{aspect}"', markup)

    def test_the_folder_question_shows_three_representative_thumbnails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = root / STORE
            source = root / "references"
            store.mkdir(parents=True)
            source.mkdir()
            items = []
            for index in range(5):
                path = source / f"{index}.jpg"
                payload = f"image-{index}".encode()
                path.write_bytes(payload)
                items.append({
                    "id": f"image-{index}", "path": f"covers/{index}.jpg",
                    "kind": "image", "mediaType": "image/jpeg",
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "inspectPath": str(path), "bytes": len(payload),
                })
            (store / "corpus.json").write_text(json.dumps({
                "version": 1, "root": str(source), "modalities": ["image"],
                "items": items,
            }), encoding="utf-8")

            markup = ct.render_corpus_tags(root)

            self.assertEqual(markup.count('class="dh-tags-thumb"'), 3)
            self.assertIn("/files/corpus-", markup)
            self.assertNotIn(str(source), markup)

    def test_publish_stages_only_hash_verified_corpus_thumbnails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = root / STORE
            source = root / "references"
            target = root / "content"
            store.mkdir(parents=True)
            source.mkdir()
            good = source / "good.jpg"
            bad = source / "bad.jpg"
            good.write_bytes(b"good")
            bad.write_bytes(b"tampered")
            (store / "corpus.json").write_text(json.dumps({
                "version": 1, "items": [
                    {"path": "covers/good.jpg", "kind": "image",
                     "mediaType": "image/jpeg", "inspectPath": str(good),
                     "sha256": hashlib.sha256(b"good").hexdigest()},
                    {"path": "covers/bad.jpg", "kind": "image",
                     "mediaType": "image/jpeg", "inspectPath": str(bad),
                     "sha256": hashlib.sha256(b"original").hexdigest()},
                ],
            }), encoding="utf-8")

            staged = ct.stage_corpus_thumbnails(root, target)

            self.assertEqual(len(staged), 1)
            self.assertEqual(staged[0].read_bytes(), b"good")


if __name__ == "__main__":
    unittest.main()


class TheSkillActuallyInvokesIt(unittest.TestCase):
    """B-016: `brief_workflow.py` is fully built, fully tested, and never
    appears, because `SKILL.md` never names it. A module the doctrine does not
    invoke is a module that does not exist.

    Tags are reached through `bootstrap_harness adopt`, which SKILL.md already
    names, so the entry cost stays zero. That only holds while adopt really
    folds them in, which is what this asserts.
    """

    def test_bootstrap_adopt_folds_in_corpus_tags(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = project(Path(tmp), "strong color/a.jpg")
            inbox = root / ct.DEFAULT_INBOX
            inbox.parent.mkdir(parents=True, exist_ok=True)
            inbox.write_text(json.dumps(
                {"group": "strong color", "aspects": ["palette"],
                 "stance": "pursue", "quality": "finished",
                 "at": "2026-08-22T00:00:00-06:00"}) + "\n", encoding="utf-8")
            store = root / "spec" / "design-harness"
            bh.write_json(store / "decisions.json", bh.empty_decisions())
            bh.write_json(store / "project.json",
                          {"version": bh.VERSION, "state": "draft"})
            (root / "ledger.jsonl").write_text("", encoding="utf-8")
            argv = ["bootstrap_harness.py", "adopt", "--project-root", str(root),
                    "--companion-ledger", str(root / "ledger.jsonl")]
            with unittest.mock.patch.object(sys, "argv", argv):
                bh.main()
            self.assertEqual(len(ct.load_tags(root)["tags"]), 1)
