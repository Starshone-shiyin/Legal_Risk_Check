import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.check_human_rebuild_authorization_record_draft_scaffold_gate import (
    DEFAULT_DRAFT_SCAFFOLD_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    build_report,
    render_markdown,
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class HumanRebuildAuthorizationRecordDraftScaffoldGateTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(
            DEFAULT_DRAFT_SCAFFOLD_PATH,
            legacy_report_path("human_rebuild_authorization_record_draft_scaffold_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("human_rebuild_authorization_record_draft_scaffold_gate_report.json"),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/human_rebuild_authorization_record_draft_scaffold_gate_v0.4.14.7.md"),
        )

    def test_real_draft_scaffold_passes_gate(self):
        report = build_report()
        summary = report["summary"]

        self.assertEqual(report["version"], "0.4.14.7")
        self.assertEqual(report["schema_kind"], "human_rebuild_authorization_record_draft_scaffold_gate")
        self.assertEqual(summary["status"], "passed")
        self.assertEqual(summary["check_count"], 13)
        self.assertEqual(summary["failed_check_count"], 0)
        self.assertEqual(summary["allowed_next_step"], "human_rebuild_authorization_record_input_workflow_design")
        self.assertFalse(summary["human_values_collected"])
        self.assertFalse(summary["draft_record_created"])
        self.assertFalse(summary["formal_authorization_record_created"])
        self.assertFalse(summary["human_authorization_record_created"])
        self.assertFalse(summary["human_authorization_record_accepted"])
        self.assertFalse(summary["authorization_granted"])
        self.assertFalse(summary["live_preflight_run"])
        self.assertFalse(summary["production_rebuild_executed"])
        self.assertFalse(summary["qdrant_write_allowed"])
        self.assertFalse(summary["rebuild_allowed"])
        self.assertEqual(summary["full_eval"], "not_run")
        self.assertEqual(summary["forbidden_output_key_count"], 0)

    def test_status_or_source_lineage_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "draft_scaffold.json"
            payload = copy.deepcopy(load_json(DEFAULT_DRAFT_SCAFFOLD_PATH))
            payload["version"] = "0.4.14.99"
            payload["summary"]["status"] = "authorized"
            payload["summary"]["allowed_next_step"] = "live_preflight"
            payload["inputs"]["human_rebuild_authorization_record_draft_design_gate"]["version"] = "0.4.14.99"
            payload["inputs"]["human_rebuild_authorization_record_draft_design_gate"]["schema_kind"] = "wrong_schema"
            payload["inputs"]["human_rebuild_authorization_record_draft_design_gate"]["status"] = "failed"
            payload["inputs"]["legacy_report"] = {"version": "0.4.13.18"}
            write_json(path, payload)

            report = build_report(path)

        failed = {row["check_id"] for row in report["failed_checks"]}
        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("draft_scaffold_version", failed)
        self.assertIn("draft_scaffold_status", failed)
        self.assertIn("source_lineage", failed)

    def test_values_or_authorization_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "draft_scaffold.json"
            payload = copy.deepcopy(load_json(DEFAULT_DRAFT_SCAFFOLD_PATH))
            payload["summary"]["human_value_count"] = 1
            payload["summary"]["human_values_collected"] = True
            payload["summary"]["draft_record_created"] = True
            payload["summary"]["formal_authorization_record_created"] = True
            payload["summary"]["authorization_granted"] = True
            payload["summary"]["live_preflight_run"] = True
            payload["summary"]["qdrant_write_allowed"] = True
            payload["summary"]["rebuild_allowed"] = True
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("no_values_or_authorization", {row["check_id"] for row in report["failed_checks"]})

    def test_internal_gate_or_guardrail_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "draft_scaffold.json"
            payload = copy.deepcopy(load_json(DEFAULT_DRAFT_SCAFFOLD_PATH))
            payload["draft_scaffold_gate"]["allowed_use"] = "authorization_record"
            payload["draft_scaffold_gate"]["qdrant_write_allowed"] = True
            payload["guardrails"]["qdrant_write"] = "allowed"
            payload["guardrails"]["collection_rebuild"] = "allowed"
            payload["guardrails"]["prompt_mutation"] = "allowed"
            write_json(path, payload)

            report = build_report(path)

        failed = {row["check_id"] for row in report["failed_checks"]}
        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("internal_gate_locked", failed)
        self.assertIn("guardrails_locked", failed)

    def test_section_contract_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "draft_scaffold.json"
            payload = copy.deepcopy(load_json(DEFAULT_DRAFT_SCAFFOLD_PATH))
            scaffold = payload["draft_scaffold"]
            scaffold["record_status"] = "created"
            scaffold["section_order"] = list(reversed(scaffold["section_order"]))
            scaffold["sections"][0]["field_ids"] = []
            scaffold["sections"][0]["value_collection"] = "collected"
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("section_contract_locked", {row["check_id"] for row in report["failed_checks"]})

    def test_row_blank_contract_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "draft_scaffold.json"
            payload = copy.deepcopy(load_json(DEFAULT_DRAFT_SCAFFOLD_PATH))
            row = payload["draft_scaffold"]["rows"][0]
            row["value_status"] = "collected"
            row["human_value"] = "prod_collection"
            row["normalized_value"] = "prod_collection"
            row["authorization_granted"] = True
            row["qdrant_write_allowed"] = True
            row["guidance"] = ""
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("row_blank_contract_locked", {row["check_id"] for row in report["failed_checks"]})

    def test_future_policy_handoff_or_traceability_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "draft_scaffold.json"
            payload = copy.deepcopy(load_json(DEFAULT_DRAFT_SCAFFOLD_PATH))
            payload["draft_scaffold"]["future_validation_policy"]["operator_approval_effect"] = "approval_now"
            payload["handoff"]["not_allowed_yet"].remove("write Qdrant")
            payload["traceability"]["scaffold_field_count"] = 9
            write_json(path, payload)

            report = build_report(path)

        failed = {row["check_id"] for row in report["failed_checks"]}
        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("future_validation_policy_locked", failed)
        self.assertIn("handoff_boundaries", failed)
        self.assertIn("traceability_counts", failed)

    def test_forbidden_output_key_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "draft_scaffold.json"
            payload = copy.deepcopy(load_json(DEFAULT_DRAFT_SCAFFOLD_PATH))
            payload["draft_scaffold"]["rows"][0]["commands"] = []
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertEqual(report["summary"]["forbidden_output_key_count"], 1)
        self.assertIn("forbidden_output_keys_absent", {row["check_id"] for row in report["failed_checks"]})

    def test_cli_output_matches_builder_shape_and_utf8_markdown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "draft_scaffold_gate.json"
            summary = Path(tmpdir) / "draft_scaffold_gate.md"
            subprocess.run(
                [
                    sys.executable,
                    "tools/check_human_rebuild_authorization_record_draft_scaffold_gate.py",
                    "--draft-scaffold",
                    str(DEFAULT_DRAFT_SCAFFOLD_PATH),
                    "--output",
                    str(output),
                    "--summary",
                    str(summary),
                ],
                check=True,
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
            )

            cli_report = load_json(output)
            cli_summary = summary.read_text(encoding="utf-8")

        expected = copy.deepcopy(build_report())
        expected.pop("generated_at", None)
        cli_report.pop("generated_at", None)
        self.assertEqual(cli_report, expected)
        self.assertIn("本 gate 只检查 v0.4.14.6 空白授权草案 scaffold", cli_summary)
        self.assertIn("不创建或接受正式授权记录", cli_summary)
        self.assertIn("只允许进入 `human_rebuild_authorization_record_input_workflow_design`", cli_summary)

    def test_markdown_documents_gate_boundary(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.14.7 Human Rebuild Authorization Record Draft Scaffold Gate", markdown)
        self.assertIn("不收集人工值", markdown)
        self.assertIn("不创建或接受正式授权记录", markdown)
        self.assertIn("不访问或写入 Qdrant", markdown)
        self.assertIn("仍不代表已经允许填写真实人工值", markdown)


if __name__ == "__main__":
    unittest.main()
