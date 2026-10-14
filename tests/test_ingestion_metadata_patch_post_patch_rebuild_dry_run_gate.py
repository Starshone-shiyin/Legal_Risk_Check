import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.check_ingestion_metadata_patch_post_patch_rebuild_dry_run_gate import (
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_RUNNER_REPORT_PATH,
    build_report,
    render_markdown,
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class IngestionMetadataPatchPostPatchRebuildDryRunGateTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(
            DEFAULT_RUNNER_REPORT_PATH,
            legacy_report_path("ingestion_metadata_patch_post_patch_rebuild_dry_run_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("ingestion_metadata_patch_post_patch_rebuild_dry_run_gate_report.json"),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/ingestion_metadata_patch_post_patch_rebuild_dry_run_gate_v0.4.13.12.md"),
        )

    def test_real_runner_report_passes_gate(self):
        report = build_report()
        summary = report["summary"]

        self.assertEqual(report["version"], "0.4.13.12")
        self.assertEqual(report["schema_kind"], "ingestion_metadata_patch_post_patch_rebuild_dry_run_gate")
        self.assertEqual(summary["status"], "passed")
        self.assertEqual(summary["failed_check_count"], 0)
        self.assertEqual(summary["allowed_next_step"], "rebuild_authorization_design")
        self.assertFalse(summary["runner_rerun_allowed"])
        self.assertFalse(summary["qdrant_write_allowed"])
        self.assertFalse(summary["rebuild_allowed"])
        self.assertFalse(summary["rag_query_allowed"])
        self.assertFalse(summary["embedding_or_llm_allowed"])
        self.assertEqual(summary["full_eval"], "not_run")

    def test_summary_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "runner.json"
            payload = copy.deepcopy(load_json(DEFAULT_RUNNER_REPORT_PATH))
            payload["summary"]["row_count"] = 8
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("summary_contract", {row["check_id"] for row in report["failed_checks"]})

    def test_guardrail_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "runner.json"
            payload = copy.deepcopy(load_json(DEFAULT_RUNNER_REPORT_PATH))
            payload["guardrails"]["qdrant_write"] = "allowed"
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("guardrails_locked", {row["check_id"] for row in report["failed_checks"]})

    def test_sample_shape_or_dependency_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "runner.json"
            payload = copy.deepcopy(load_json(DEFAULT_RUNNER_REPORT_PATH))
            payload["sample_strategy"]["required_shapes"] = ["single paragraph article"]
            payload["sample_strategy"]["hidden_seed_dependency"] = "allowed"
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("sample_contract", {row["check_id"] for row in report["failed_checks"]})

    def test_row_boundary_or_drift_missing_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "runner.json"
            payload = copy.deepcopy(load_json(DEFAULT_RUNNER_REPORT_PATH))
            payload["rows"][0]["chunk_index"] = None
            payload["rows"][0]["detected_drifts"].remove("expected_chunk_count_added")
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("row_contract", {row["check_id"] for row in report["failed_checks"]})

    def test_lineage_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "runner.json"
            payload = copy.deepcopy(load_json(DEFAULT_RUNNER_REPORT_PATH))
            payload["inputs"]["post_patch_rebuild_dry_run_design_gate"]["status"] = "failed"
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("lineage", {row["check_id"] for row in report["failed_checks"]})

    def test_handoff_boundary_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "runner.json"
            payload = copy.deepcopy(load_json(DEFAULT_RUNNER_REPORT_PATH))
            payload["handoff"]["not_allowed_yet"].remove("write Qdrant")
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("handoff_boundaries", {row["check_id"] for row in report["failed_checks"]})

    def test_markdown_reports_non_runtime_boundary(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.13.12 Post-Patch Rebuild Dry-Run Runner Gate", markdown)
        self.assertIn("只读取 v0.4.13.11 saved report", markdown)
        self.assertIn("不访问 Qdrant", markdown)
        self.assertIn("不重跑 runner", markdown)
        self.assertIn("不代表已经允许生产 rebuild", markdown)


if __name__ == "__main__":
    unittest.main()
