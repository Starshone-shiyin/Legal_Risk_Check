import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.check_ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate import (
    DEFAULT_DESIGN_PATH,
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


class IngestionMetadataPatchPostPatchRebuildDryRunDesignGateTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(
            DEFAULT_DESIGN_PATH,
            legacy_report_path("ingestion_metadata_patch_post_patch_rebuild_dry_run_design_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate_report.json"),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate_v0.4.13.10.md"),
        )

    def test_real_design_passes_gate(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.13.10")
        self.assertEqual(report["schema_kind"], "ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate")
        self.assertEqual(report["summary"]["status"], "passed")
        self.assertEqual(report["summary"]["failed_check_count"], 0)
        self.assertEqual(report["summary"]["allowed_next_step"], "post_patch_rebuild_dry_run_runner")
        self.assertFalse(report["summary"]["qdrant_write_allowed"])
        self.assertFalse(report["summary"]["rebuild_allowed"])
        self.assertEqual(report["summary"]["full_eval"], "not_run")

    def test_wrong_source_patch_input_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            design = copy.deepcopy(load_json(DEFAULT_DESIGN_PATH))
            design["inputs"]["source_patch_report"]["status"] = "failed"
            path = tmp / "design.json"
            write_json(path, design)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("source_patch_input", {row["check_id"] for row in report["failed_checks"]})

    def test_runner_creation_permission_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            design = copy.deepcopy(load_json(DEFAULT_DESIGN_PATH))
            design["summary"]["runner_creation_allowed"] = True
            path = tmp / "design.json"
            write_json(path, design)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("summary_permissions_blocked", {row["check_id"] for row in report["failed_checks"]})

    def test_missing_sample_shape_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            design = copy.deepcopy(load_json(DEFAULT_DESIGN_PATH))
            design["dry_run_design"]["sample_strategy"]["required_shapes"] = ["single paragraph article"]
            path = tmp / "design.json"
            write_json(path, design)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("sample_strategy", {row["check_id"] for row in report["failed_checks"]})

    def test_missing_comparison_field_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            design = copy.deepcopy(load_json(DEFAULT_DESIGN_PATH))
            design["dry_run_design"]["comparison_fields"]["must_remain_stable"].remove("citation")
            path = tmp / "design.json"
            write_json(path, design)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("stable_fields", {row["check_id"] for row in report["failed_checks"]})

    def test_output_contract_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            design = copy.deepcopy(load_json(DEFAULT_DESIGN_PATH))
            design["output_contract"]["row_fields"].remove("blocking_conditions")
            path = tmp / "design.json"
            write_json(path, design)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("row_output_contract", {row["check_id"] for row in report["failed_checks"]})

    def test_guardrail_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            design = copy.deepcopy(load_json(DEFAULT_DESIGN_PATH))
            design["guardrails"]["qdrant_write"] = "allowed"
            path = tmp / "design.json"
            write_json(path, design)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("guardrails_locked", {row["check_id"] for row in report["failed_checks"]})

    def test_handoff_boundary_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            design = copy.deepcopy(load_json(DEFAULT_DESIGN_PATH))
            design["handoff"]["not_allowed_yet"].remove("write Qdrant")
            path = tmp / "design.json"
            write_json(path, design)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("handoff_boundaries", {row["check_id"] for row in report["failed_checks"]})

    def test_markdown_reports_non_runtime_boundary(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.13.10 补丁后 rebuild dry-run 设计门禁", markdown)
        self.assertIn("不创建 runner", markdown)
        self.assertIn("不写 Qdrant", markdown)
        self.assertIn("`PASS`", markdown)


if __name__ == "__main__":
    unittest.main()
