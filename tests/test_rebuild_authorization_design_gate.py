import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.check_rebuild_authorization_design_gate import (
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


class RebuildAuthorizationDesignGateTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(DEFAULT_DESIGN_PATH, legacy_report_path("rebuild_authorization_design_report.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("rebuild_authorization_design_gate_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/rebuild_authorization_design_gate_v0.4.13.14.md"))

    def test_real_design_passes_gate(self):
        report = build_report()
        summary = report["summary"]

        self.assertEqual(report["version"], "0.4.13.14")
        self.assertEqual(report["schema_kind"], "rebuild_authorization_design_gate")
        self.assertEqual(summary["status"], "passed")
        self.assertEqual(summary["failed_check_count"], 0)
        self.assertEqual(summary["allowed_next_step"], "human_rebuild_authorization_worksheet")
        self.assertFalse(summary["human_authorization_record_created"])
        self.assertFalse(summary["authorization_granted"])
        self.assertFalse(summary["qdrant_write_allowed"])
        self.assertFalse(summary["rebuild_allowed"])
        self.assertEqual(summary["full_eval"], "not_run")

    def test_authorization_or_rebuild_permission_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "design.json"
            payload = copy.deepcopy(load_json(DEFAULT_DESIGN_PATH))
            payload["summary"]["authorization_granted"] = True
            payload["summary"]["rebuild_allowed"] = True
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("no_authorization_or_rebuild", {row["check_id"] for row in report["failed_checks"]})

    def test_lineage_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "design.json"
            payload = copy.deepcopy(load_json(DEFAULT_DESIGN_PATH))
            payload["inputs"]["post_patch_rebuild_dry_run_runner_gate"]["allowed_next_step"] = "rebuild_now"
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("lineage", {row["check_id"] for row in report["failed_checks"]})

    def test_future_authorization_record_status_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "design.json"
            payload = copy.deepcopy(load_json(DEFAULT_DESIGN_PATH))
            payload["authorization_design"]["future_authorization_record_status"] = "created"
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("required_fields", {row["check_id"] for row in report["failed_checks"]})

    def test_missing_required_field_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "design.json"
            payload = copy.deepcopy(load_json(DEFAULT_DESIGN_PATH))
            payload["authorization_design"]["required_confirmation_fields"].remove("backup_plan")
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("required_fields", {row["check_id"] for row in report["failed_checks"]})

    def test_missing_abort_condition_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "design.json"
            payload = copy.deepcopy(load_json(DEFAULT_DESIGN_PATH))
            payload["authorization_design"]["abort_conditions"].remove("operator_approval_missing")
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("abort_conditions", {row["check_id"] for row in report["failed_checks"]})

    def test_handoff_boundary_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "design.json"
            payload = copy.deepcopy(load_json(DEFAULT_DESIGN_PATH))
            payload["handoff"]["not_allowed_yet"].remove("write Qdrant")
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("handoff_boundaries", {row["check_id"] for row in report["failed_checks"]})

    def test_markdown_documents_gate_boundary(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.13.14 Rebuild Authorization Design Gate", markdown)
        self.assertIn("不创建人工授权记录", markdown)
        self.assertIn("不访问 Qdrant", markdown)
        self.assertIn("仍不代表已经允许生产 Qdrant rebuild", markdown)
        return
        self.assertIn("不创建人工授权记录", markdown)
        self.assertIn("不访问 Qdrant", markdown)
        self.assertIn("仍不代表已经允许生产 Qdrant rebuild", markdown)


if __name__ == "__main__":
    unittest.main()
