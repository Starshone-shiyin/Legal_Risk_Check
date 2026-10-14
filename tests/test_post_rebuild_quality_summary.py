import json
import tempfile
import unittest
from pathlib import Path

from tools.build_post_rebuild_quality_summary import build_summary_report


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class PostRebuildQualitySummaryTest(unittest.TestCase):
    def test_passes_when_smoke_has_no_regressions_and_validation_passed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            baseline = root / "baseline.json"
            post = root / "post.json"
            validation = root / "validation.json"
            write_json(baseline, {"total": 2, "passed": 2, "reports": [{"id": "a", "passed": True}, {"id": "b", "passed": True}]})
            write_json(
                post,
                {
                    "total": 2,
                    "passed": 2,
                    "failed": 0,
                    "reports": [
                        {"id": "a", "passed": True, "layers": {"rag": {"contribution_labels": ["ANCHOR_PASS"]}}},
                        {"id": "b", "passed": True, "layers": {"rag": {"contribution_labels": ["PURE_LLM_PASS"]}}},
                    ],
                },
            )
            write_json(
                validation,
                {
                    "summary": {"status": "passed", "blockers": []},
                    "validation": {"points_count": 10, "scanned_points": 10, "observed_chunk_fields": {"article": 1}, "missing_chunk_fields": {}},
                },
            )

            report = build_summary_report(post_rebuild_smoke_path=post, baseline_smoke_path=baseline, post_validation_path=validation)

        self.assertEqual(report["version"], "0.4.14.30")
        self.assertEqual(report["summary"]["status"], "passed")
        self.assertEqual(report["smoke_summary"]["regressed_cases"], [])
        self.assertEqual(report["smoke_summary"]["contribution_label_counts"]["ANCHOR_PASS"], 1)

    def test_fails_when_baseline_passing_case_regresses(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            baseline = root / "baseline.json"
            post = root / "post.json"
            validation = root / "validation.json"
            write_json(baseline, {"total": 1, "passed": 1, "reports": [{"id": "a", "passed": True}]})
            write_json(post, {"total": 1, "passed": 0, "failed": 1, "reports": [{"id": "a", "passed": False}]})
            write_json(validation, {"summary": {"status": "passed", "blockers": []}, "validation": {}})

            report = build_summary_report(post_rebuild_smoke_path=post, baseline_smoke_path=baseline, post_validation_path=validation)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("baseline_smoke_regressions", report["summary"]["blockers"])
        self.assertEqual(report["smoke_summary"]["regressed_cases"], ["a"])


if __name__ == "__main__":
    unittest.main()
