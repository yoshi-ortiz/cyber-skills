#!/usr/bin/env python3
"""Tests for the corpus measurer.

Every PNG here is built byte by byte in the test, so a failure means the
decoder is wrong rather than that a fixture drifted.
"""
from __future__ import annotations

import json
import struct
import sys
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from corpus_measure import (MeasureError, decode_png, measure_bytes,  # noqa: E402
                            measure_corpus, palette_of)


def png(pixels: list[list[tuple[int, ...]]], colour: int = 2,
        filters: list[int] | None = None) -> bytes:
    """Encode rows of RGB or RGBA tuples as a PNG, one filter type per row."""
    height = len(pixels)
    width = len(pixels[0])
    sample = 3 if colour == 2 else 4
    kinds = filters or [0] * height
    raw = bytearray()
    previous = bytearray(width * sample)
    for row, kind in zip(pixels, kinds):
        line = bytearray()
        for pixel in row:
            line += bytes(pixel)
        encoded = bytearray(line)
        if kind == 1:
            for index in reversed(range(sample, len(line))):
                encoded[index] = (line[index] - line[index - sample]) & 0xFF
        elif kind == 2:
            for index in range(len(line)):
                encoded[index] = (line[index] - previous[index]) & 0xFF
        elif kind not in (0,):
            raise ValueError("test encoder writes filters 0, 1 and 2 only")
        raw += bytes([kind]) + encoded
        previous = line

    def chunk(kind: bytes, body: bytes) -> bytes:
        return (struct.pack(">I", len(body)) + kind + body
                + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF))

    header = struct.pack(">IIBBBBB", width, height, 8, colour, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
            + chunk(b"IDAT", zlib.compress(bytes(raw))) + chunk(b"IEND", b""))


RED = (220, 40, 40)
BLUE = (30, 60, 200)
INK = (10, 10, 10)


class DecodePng(unittest.TestCase):
    def test_reads_every_pixel_of_an_unfiltered_image(self):
        image = decode_png(png([[RED, BLUE], [BLUE, RED]]))
        self.assertEqual((image["width"], image["height"]), (2, 2))
        self.assertEqual(image["pixels"], [RED, BLUE, BLUE, RED])

    def test_undoes_sub_and_up_filters(self):
        rows = [[RED, BLUE, RED], [BLUE, RED, BLUE], [RED, RED, BLUE]]
        plain = decode_png(png(rows))["pixels"]
        filtered = decode_png(png(rows, filters=[0, 1, 2]))["pixels"]
        self.assertEqual(filtered, plain)

    def test_composites_transparency_over_white(self):
        """A transparent margin must not be counted as black.

        Left uncomposited, every screenshot with an alpha channel would report
        the same fake ink colour.
        """
        image = decode_png(png([[(0, 0, 0, 0), (0, 0, 0, 255)]], colour=6))
        self.assertEqual(image["pixels"], [(255, 255, 255), (0, 0, 0)])

    def test_refuses_what_it_cannot_read_rather_than_guessing(self):
        for label, data in (
            ("not a png", b"\xff\xd8\xff\xe0 jpeg"),
            ("truncated", png([[RED]])[:20]),
        ):
            with self.subTest(label), self.assertRaises(MeasureError):
                decode_png(data)


class PaletteOf(unittest.TestCase):
    def test_ranks_fills_by_coverage(self):
        pixels = [RED] * 70 + [BLUE] * 30
        palette = palette_of(pixels)
        self.assertEqual([entry["hex"] for entry in palette], ["#dc2828", "#1e3cc8"])
        self.assertAlmostEqual(palette[0]["coverage"], 0.70)
        self.assertAlmostEqual(palette[1]["coverage"], 0.30)

    def test_merges_antialiasing_into_the_fill_it_came_from(self):
        """Edge pixels are a consequence of two flats meeting, not a decision."""
        halo = [(RED[0] + shift, RED[1] + shift, RED[2]) for shift in range(1, 9)]
        palette = palette_of([RED] * 60 + halo * 2 + [BLUE] * 24)
        self.assertEqual([entry["hex"] for entry in palette], ["#dc2828", "#1e3cc8"])
        self.assertAlmostEqual(palette[0]["coverage"], 0.76)

    def test_drops_flecks_below_the_coverage_floor(self):
        palette = palette_of([RED] * 999 + [BLUE])
        self.assertEqual([entry["hex"] for entry in palette], ["#dc2828"])

    def test_empty_input_measures_as_nothing(self):
        self.assertEqual(palette_of([]), [])


class MeasureBytes(unittest.TestCase):
    def test_reports_paper_ink_and_contour_share(self):
        rows = [[(250, 248, 240)] * 8 for _ in range(9)] + [[INK] * 8]
        measured = measure_bytes(png(rows))
        self.assertEqual(measured["paper"], "#faf8f0")
        self.assertEqual(measured["ink"], "#0a0a0a")
        self.assertAlmostEqual(measured["inkShare"], 0.1)
        self.assertEqual(measured["aspect"], round(8 / 10, 3))

    def test_ink_is_absent_when_nothing_is_dark(self):
        """None means measured and not found. It never means 'assume black'."""
        measured = measure_bytes(png([[(250, 248, 240)] * 4, [(200, 210, 220)] * 4]))
        self.assertIsNone(measured["ink"])

    def test_same_bytes_measure_the_same_twice(self):
        data = png([[RED, BLUE], [INK, RED]])
        self.assertEqual(measure_bytes(data), measure_bytes(data))


class MeasureCorpus(unittest.TestCase):
    def setUp(self):
        import tempfile

        self.root = Path(tempfile.mkdtemp())

    def test_records_the_files_it_could_not_read_instead_of_dropping_them(self):
        good = self.root / "good.png"
        good.write_bytes(png([[RED] * 4, [INK] * 4]))
        bad = self.root / "bad.jpg"
        bad.write_bytes(b"\xff\xd8\xff\xe0 not a png")
        result = measure_corpus(self.root, [
            {"sha256": "aaa", "path": "good.png", "inspectPath": str(good)},
            {"sha256": "bbb", "path": "bad.jpg", "inspectPath": str(bad)},
        ])
        self.assertEqual(list(result["images"]), ["aaa"])
        self.assertEqual(result["images"]["aaa"]["path"], "good.png")
        self.assertEqual([entry["path"] for entry in result["unmeasured"]], ["bad.jpg"])
        self.assertEqual(result["unmeasured"][0]["sha256"], "bbb")

    def test_a_missing_file_is_unmeasured_not_a_crash(self):
        result = measure_corpus(self.root, [
            {"sha256": "ccc", "path": "gone.png",
             "inspectPath": str(self.root / "gone.png")}])
        self.assertEqual(result["images"], {})
        self.assertEqual(len(result["unmeasured"]), 1)


class PaletteAudit(unittest.TestCase):
    """A comp is HTML, never passes the prompt compiler, and was unchecked."""

    def setUp(self):
        import tempfile

        from corpus_measure import measure_corpus

        self.root = Path(tempfile.mkdtemp())
        store = self.root / "spec" / "design-harness"
        store.mkdir(parents=True)
        image = self.root / "ref.png"
        image.write_bytes(png([[RED] * 6, [BLUE] * 6, [(250, 250, 250)] * 6]))
        digest = "d" * 64
        (store / "corpus.json").write_text(json.dumps({"version": 1, "items": [
            {"sha256": digest, "path": "ref.png", "kind": "image",
             "inspectPath": str(image)}]}), encoding="utf-8")
        (store / "corpus-tags.json").write_text(json.dumps({"version": 1, "tags": {
            digest: {"aspects": ["illustration"], "stance": "pursue",
                     "role": "reference"}}}), encoding="utf-8")
        (store / "corpus-derived.json").write_text(json.dumps(measure_corpus(
            self.root, [{"sha256": digest, "path": "ref.png",
                         "inspectPath": str(image)}])), encoding="utf-8")

    def _audit(self, markup: str):
        from graphics_corpus import palette_audit

        design = self.root / "comp.html"
        design.write_text(markup, encoding="utf-8")
        return palette_audit(self.root, design)

    def test_a_comp_drawn_from_the_corpus_scores_full_fit(self):
        result = self._audit("<style>a{color:#dc2828}b{color:#1e3cc8}</style>")
        self.assertEqual(result["fit"], 1.0)
        self.assertEqual(result["unevidenced"], [])

    def test_an_invented_colour_is_named_with_its_distance(self):
        result = self._audit("<style>a{color:#7b3ff2}</style>")
        self.assertEqual(result["fit"], 0.0)
        self.assertEqual(result["unevidenced"][0]["declared"], "#7b3ff2")
        self.assertGreater(result["unevidenced"][0]["distance"], 40)

    def test_shorthand_hex_is_read_the_same_as_longhand(self):
        self.assertEqual(self._audit("<i style='color:#FFF'>")["declared"],
                         ["#ffffff"])

    def test_no_measurement_yields_no_verdict_rather_than_a_pass(self):
        """Missing evidence is not a neutral score. It is the absence of one."""
        (self.root / "spec" / "design-harness" / "corpus-derived.json").unlink()
        self.assertIsNone(self._audit("<style>a{color:#7b3ff2}</style>")["fit"])


if __name__ == "__main__":
    unittest.main()
