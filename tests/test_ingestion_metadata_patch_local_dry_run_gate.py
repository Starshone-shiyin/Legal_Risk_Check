import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.check_ingestion_metadata_patch_local_dry_run_gate import (
    DEFAULT_LOCAL_DRY_RUN_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    build_report,
    render_markdown,
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class IngestionMetadataPatchLocalDryRunGateTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(DEFAULT_LOCAL_DRY_RUN_PATH, legacy_report_path("ingestion_metadata_patch_local_dry_run_report.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("ingestion_metadata_patch_local_dry_run_gate_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/ingestion_metadata_patch_local_dry_run_gate_v0.4.13.5.md"))

    def test_real_local_dry_run_passes_gate(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.13.5")
        self.assertEqual(report["schema_kind"], "ingestion_metadata_patch_local_dry_run_gate")
        self.assertEqual(report["summary"]["status"], "passed")
        self.assertEqual(report["summary"]["failed_check_count"], 0)
        self.assertEqual(report["summary"]["allowed_next_step"], "actual_ingestion_metadata_patch_design")
        self.assertFalse(report["summary"]["implementation_allowed"])
        self.assertFalse(report["summary"]["qdrant_write_allowed"])
        self.assertFalse(report["summary"]["rebuild_allowed"])

    def test_forbidden_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            dry_run = copy.deepcopy(load_json(DEFAULT_LOCAL_DRY_RUN_PATH))
            dry_run["summary"]["forbidden_drift_count"] = 1
            dry_run["rows"][0]["forbidden_drift"] = ["citation"]
            path = tmp / "dry_run.json"
            write_json(path, dry_run)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("forbidden_drift_zero", {row["check_id"] for row in report["failed_checks"]})

    def test_missing_boundary_metadata_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            dry_run = copy.deepcopy(load_json(DEFAULT_LOCAL_DRY_RUN_PATH))
            dry_run["rows"][0]["post_chunk_index"] = None
            dry_run["rows"][0]["missing_post_boundary_metadata"] = True
            path = tmp / "dry_run.json"
            write_json(path, dry_run)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("boundary_metadata_present", {row["check_id"] for row in report["failed_checks"]})

    def test_missing_id_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            dry_run = copy.deepcopy(load_json(DEFAULT_LOCAL_DRY_RUN_PATH))
            dry_run["rows"][0]["chunk_id_changed"] = False
            path = tmp / "dry_run.json"
            write_json(path, dry_run)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("id_drift_rows", {row["check_id"] for row in report["failed_checks"]})

    def test_qdrant_guardrail_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            dry_run = copy.deepcopy(load_json(DEFAULT_LOCAL_DRY_RUN_PATH))
            dry_run["guardrails"]["qdrant_write"] = "allowed"
            path = tmp / "dry_run.json"
            write_json(path, dry_run)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("qdrant_blocked", {row["check_id"] for row in report["failed_checks"]})

    def test_missing_handoff_boundary_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            dry_run = copy.deepcopy(load_json(DEFAULT_LOCAL_DRY_RUN_PATH))
            dry_run["handoff"]["not_allowed_yet"].remove("write Qdrant")
            path = tmp / "dry_run.json"
            write_json(path, dry_run)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("handoff_boundaries", {row["check_id"] for row in report["failed_checks"]})

    def test_markdown_reports_gate_status(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.13.5 Ingestion Metadata Patch Local Dry-Run Gate", markdown)
        self.assertIn("Allowed next step", markdown)
        self.assertIn("`PASS`", markdown)


if __name__ == "__main__":
    unittest.main()
