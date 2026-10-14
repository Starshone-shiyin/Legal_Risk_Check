import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.check_production_rebuild_post_validation import build_post_validation_report


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class ProductionRebuildPostValidationTest(unittest.TestCase):
    def test_passes_when_execution_succeeded_and_chunk_fields_observed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            execution_path = Path(tmpdir) / "execution.json"
            write_json(
                execution_path,
                {
                    "summary": {"execution_status": "succeeded"},
                    "after_snapshot": {"points_count": 7177},
                },
            )

            with patch(
                "tools.check_production_rebuild_post_validation.validate_payload_metadata",
                return_value={
                    "points_count": 7177,
                    "scanned_points": 500,
                    "observed_chunk_fields": {"article": 10, "paragraph": 20, "item": 5},
                    "missing_chunk_fields": {},
                },
            ):
                report = build_post_validation_report(execution_report_path=execution_path)

        self.assertEqual(report["version"], "0.4.14.29")
        self.assertEqual(report["summary"]["status"], "passed")
        self.assertEqual(report["summary"]["blockers"], [])

    def test_blocks_when_chunk_fields_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            execution_path = Path(tmpdir) / "execution.json"
            write_json(
                execution_path,
                {
                    "summary": {"execution_status": "succeeded"},
                    "after_snapshot": {"points_count": 7177},
                },
            )

            with patch(
                "tools.check_production_rebuild_post_validation.validate_payload_metadata",
                return_value={
                    "points_count": 7177,
                    "scanned_points": 500,
                    "observed_chunk_fields": {"article": 10},
                    "missing_chunk_fields": {"paragraph": 1},
                },
            ):
                report = build_post_validation_report(execution_report_path=execution_path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("chunk_fields_missing_in_scanned_structured_blocks", report["summary"]["blockers"])


if __name__ == "__main__":
    unittest.main()
