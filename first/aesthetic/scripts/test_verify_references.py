import json
import tempfile
import unittest
from pathlib import Path

import verify_references


class ReferenceBundleTests(unittest.TestCase):
    def test_okf_bundle_and_cached_provenance(self):
        receipt_path = verify_references.REFERENCES / "source-receipts.json"
        receipts = json.loads(receipt_path.read_text()) if receipt_path.exists() else None
        self.assertEqual([], verify_references.validate_bundle(receipts))

    def test_online_check_is_bounded_before_network(self):
        with self.assertRaises(ValueError):
            verify_references.fetch_sources(timeout=0.1, max_sources=1)

    def test_missing_receipt_is_not_silently_accepted(self):
        errors = verify_references.validate_bundle({"sources": {}})
        self.assertTrue(any("missing source receipt" in error for error in errors))

    def test_frontmatter_parser_keeps_academic_role(self):
        frontmatter = """sources:
  - id: example
    resource: https://example.com/
    academic_role: university curriculum
"""
        self.assertEqual(
            "university curriculum",
            verify_references.parse_sources(frontmatter)[0]["academic_role"],
        )


if __name__ == "__main__":
    unittest.main()
