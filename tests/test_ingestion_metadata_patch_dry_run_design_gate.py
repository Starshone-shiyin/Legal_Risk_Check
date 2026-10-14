import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.check_ingestion_metadata_patch_dry_run_design_gate import (
    DEFAULT_DRY_RUN_DESIGN_PATH,
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


class IngestionMetadataPatchDryRunDesignGateTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(DEFAULT_DRY_RUN_DESIGN_PATH, legacy_report_path("ingestion_metadata_patch_dry_run_design_report.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("ingestion_metadata_patch_dry_run_design_gate_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/ingestion_metadata_patch_dry_run_design_gate_v0.4.13.3.md"))

    def test_real_design_passes_gate(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.13.3")
        self.assertEqual(report["schema_kind"], "ingestion_metadata_patch_dry_run_design_gate")
        self.assertEqual(report["summary"]["status"], "passed")
        self.assertEqual(report["summary"]["failed_check_count"], 0)
        self.assertEqual(report["summary"]["allowed_next_step"], "ingestion_metadata_patch_local_dry_run_runner")
        self.assertFalse(report["summary"]["implementation_allowed"])
        self.assertFalse(report["summary"]["qdrant_write_allowed"])

    def test_missing_forbidden_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            design = copy.deepcopy(load_json(DEFAULT_DRY_RUN_DESIGN_PATH))
            design["dry_run_design"]["forbidden_metadata_drift"].remove("citation")
            design_path = tmp / "design.json"
            write_json(design_path, design)

            report = build_report(design_path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("forbidden_drift", {row["check_id"] for row in report["failed_checks"]})

    def test_qdrant_input_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            design = copy.deepcopy(load_json(DEFAULT_DRY_RUN_DESIGN_PATH))
            design["dry_run_design"]["forbidden_inputs"].remove("Qdrant collection scroll")
            design_path = tmp / "design.json"
            write_json(design_path, design)

            report = build_report(design_path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("forbidden_inputs", {row["check_id"] for row in report["failed_checks"]})

    def test_missing_blocking_condition_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            design = copy.deepcopy(load_json(DEFAULT_DRY_RUN_DESIGN_PATH))
            design["output_contract"]["blocking_conditions"].remove("any content_changed row")
            design_path = tmp / "design.json"
            write_json(design_path, design)

            report = build_report(design_path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("blocking_conditions", {row["check_id"] for row in report["failed_checks"]})

    def test_full_eval_substitute_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            design = copy.deepcopy(load_json(DEFAULT_DRY_RUN_DESIGN_PATH))
            design["handoff"]["not_allowed_yet"].remove("run full eval as a substitute for dry-run")
            design_path = tmp / "design.json"
            write_json(design_path, design)

            report = build_report(design_path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("full_eval_not_substitute", {row["check_id"] for row in report["failed_checks"]})

    def test_markdown_reports_gate_status(self):
        markdown = render_markdown(build_report())
        self.assertIn("v0.4.13.3 Ingestion Metadata Patch Dry-Run Design Gate", markdown)
        self.assertIn("Allowed next step", markdown)
        self.assertIn("`PASS`", markdown)


if __name__ == "__main__":
    unittest.main()
