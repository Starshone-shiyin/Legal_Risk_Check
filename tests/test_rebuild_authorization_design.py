import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_rebuild_authorization_design import (
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_RUNNER_GATE_REPORT_PATH,
    DEFAULT_RUNNER_REPORT_PATH,
    build_report,
    render_markdown,
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class RebuildAuthorizationDesignTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(
            DEFAULT_RUNNER_REPORT_PATH,
            legacy_report_path("ingestion_metadata_patch_post_patch_rebuild_dry_run_report.json"),
        )
        self.assertEqual(
            DEFAULT_RUNNER_GATE_REPORT_PATH,
            legacy_report_path("ingestion_metadata_patch_post_patch_rebuild_dry_run_gate_report.json"),
        )
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("rebuild_authorization_design_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/rebuild_authorization_design_v0.4.13.13.md"))

    def test_real_inputs_build_ready_design(self):
        report = build_report()
        summary = report["summary"]
        design = report["authorization_design"]

        self.assertEqual(report["version"], "0.4.13.13")
        self.assertEqual(report["schema_kind"], "rebuild_authorization_design")
        self.assertEqual(summary["status"], "ready_for_rebuild_authorization_design_gate")
        self.assertEqual(summary["allowed_next_step"], "rebuild_authorization_design_gate")
        self.assertTrue(summary["human_authorization_required"])
        self.assertFalse(summary["authorization_granted"])
        self.assertFalse(summary["qdrant_write_allowed"])
        self.assertFalse(summary["rebuild_allowed"])
        self.assertFalse(summary["rag_query_allowed"])
        self.assertFalse(summary["embedding_or_llm_allowed"])
        self.assertEqual(summary["full_eval"], "not_run")
        self.assertEqual(summary["blockers"], [])
        self.assertEqual(design["future_authorization_record_status"], "not_created_in_this_version")

    def test_required_human_confirmation_fields_are_present(self):
        report = build_report()
        fields = set(report["authorization_design"]["required_confirmation_fields"])

        self.assertTrue(
            {
                "target_collection",
                "rebuild_scope",
                "source_version",
                "expected_id_drift_acknowledgement",
                "backup_plan",
                "rollback_plan",
                "operator_approval",
                "maintenance_window",
                "post_rebuild_validation_plan",
                "abort_conditions_acknowledgement",
            }.issubset(fields)
        )

    def test_runner_gate_drift_blocks_design(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            runner = tmp / "runner.json"
            gate = tmp / "gate.json"
            write_json(runner, load_json(DEFAULT_RUNNER_REPORT_PATH))
            gate_payload = copy.deepcopy(load_json(DEFAULT_RUNNER_GATE_REPORT_PATH))
            gate_payload["summary"]["allowed_next_step"] = "rebuild_now"
            write_json(gate, gate_payload)

            report = build_report(runner, gate)

        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("runner_gate_next_step_mismatch", report["summary"]["blockers"])

    def test_runner_summary_drift_blocks_design(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            runner = tmp / "runner.json"
            gate = tmp / "gate.json"
            runner_payload = copy.deepcopy(load_json(DEFAULT_RUNNER_REPORT_PATH))
            runner_payload["summary"]["forbidden_drift_count"] = 1
            write_json(runner, runner_payload)
            write_json(gate, load_json(DEFAULT_RUNNER_GATE_REPORT_PATH))

            report = build_report(runner, gate)

        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("runner_forbidden_drift_present", report["summary"]["blockers"])

    def test_handoff_keeps_operational_rebuild_blocked(self):
        report = build_report()
        handoff_blocks = set(report["handoff"]["not_allowed_yet"])

        self.assertIn("write Qdrant", handoff_blocks)
        self.assertIn("rebuild collection", handoff_blocks)
        self.assertIn("run rebuild preflight against a live collection", handoff_blocks)
        self.assertIn("create or accept human authorization record", handoff_blocks)

    def test_markdown_documents_design_only_boundary(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.13.13 Rebuild Authorization Design", markdown)
        self.assertIn("不访问 Qdrant", markdown)
        self.assertIn("不创建授权记录", markdown)
        self.assertIn("仍不代表已经允许生产 Qdrant rebuild", markdown)


if __name__ == "__main__":
    unittest.main()
