import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.check_human_rebuild_authorization_record_scaffold_gate import (
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_SCAFFOLD_PATH,
    build_report,
    render_markdown,
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class HumanRebuildAuthorizationRecordScaffoldGateTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(DEFAULT_SCAFFOLD_PATH, legacy_report_path("human_rebuild_authorization_record_scaffold_report.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("human_rebuild_authorization_record_scaffold_gate_report.json"))
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/human_rebuild_authorization_record_scaffold_gate_v0.4.14.3.md"),
        )

    def test_real_scaffold_passes_gate(self):
        report = build_report()
        summary = report["summary"]

        self.assertEqual(report["version"], "0.4.14.3")
        self.assertEqual(report["schema_kind"], "human_rebuild_authorization_record_scaffold_gate")
        self.assertEqual(summary["status"], "passed")
        self.assertEqual(summary["check_count"], 13)
        self.assertEqual(summary["failed_check_count"], 0)
        self.assertEqual(summary["allowed_next_step"], "human_rebuild_authorization_record_draft_design")
        self.assertFalse(summary["human_values_collected"])
        self.assertFalse(summary["formal_authorization_record_created"])
        self.assertFalse(summary["human_authorization_record_created"])
        self.assertFalse(summary["human_authorization_record_accepted"])
        self.assertFalse(summary["authorization_granted"])
        self.assertFalse(summary["live_preflight_run"])
        self.assertFalse(summary["production_rebuild_executed"])
        self.assertFalse(summary["qdrant_write_allowed"])
        self.assertFalse(summary["rebuild_allowed"])
        self.assertEqual(summary["full_eval"], "not_run")

    def test_status_or_source_lineage_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scaffold.json"
            payload = copy.deepcopy(load_json(DEFAULT_SCAFFOLD_PATH))
            payload["version"] = "0.4.14.99"
            payload["summary"]["status"] = "authorized"
            payload["summary"]["allowed_next_step"] = "live_preflight"
            payload["inputs"]["production_rebuild_execution_design_gate"]["version"] = "0.4.14.99"
            payload["inputs"]["production_rebuild_execution_design_gate"]["schema_kind"] = "wrong_schema"
            payload["inputs"]["production_rebuild_execution_design_gate"]["status"] = "failed"
            payload["inputs"]["legacy_report"] = {"version": "0.4.13.18"}
            write_json(path, payload)

            report = build_report(path)

        failed = {row["check_id"] for row in report["failed_checks"]}
        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("scaffold_version", failed)
        self.assertIn("scaffold_status", failed)
        self.assertIn("source_lineage", failed)

    def test_values_or_authorization_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scaffold.json"
            payload = copy.deepcopy(load_json(DEFAULT_SCAFFOLD_PATH))
            payload["summary"]["human_value_count"] = 1
            payload["summary"]["human_values_collected"] = True
            payload["summary"]["formal_authorization_record_created"] = True
            payload["summary"]["authorization_granted"] = True
            payload["summary"]["live_preflight_run"] = True
            payload["summary"]["qdrant_write_allowed"] = True
            payload["summary"]["rebuild_allowed"] = True
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("no_values_or_authorization", {row["check_id"] for row in report["failed_checks"]})

    def test_guardrail_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scaffold.json"
            payload = copy.deepcopy(load_json(DEFAULT_SCAFFOLD_PATH))
            payload["guardrails"]["qdrant_write"] = "allowed"
            payload["guardrails"]["collection_rebuild"] = "allowed"
            payload["guardrails"]["prompt_mutation"] = "allowed"
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("guardrails_locked", {row["check_id"] for row in report["failed_checks"]})

    def test_row_blank_contract_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scaffold.json"
            payload = copy.deepcopy(load_json(DEFAULT_SCAFFOLD_PATH))
            row = payload["authorization_record_scaffold_rows"][0]
            row["human_value_status"] = "collected"
            row["empty_authorization_value"] = "prod_collection"
            row["authorization_granted"] = True
            row["qdrant_write_allowed"] = True
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("row_blank_contract", {row["check_id"] for row in report["failed_checks"]})

    def test_input_contract_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scaffold.json"
            payload = copy.deepcopy(load_json(DEFAULT_SCAFFOLD_PATH))
            payload["input_contract"]["required_authorization_fields"].remove("backup_plan")
            payload["input_contract"]["required_record_contracts"].append("silent_extra_record")
            payload["input_contract"]["required_preflight_checks"] = list(reversed(
                payload["input_contract"]["required_preflight_checks"]
            ))
            payload["input_contract"]["required_abort_conditions"] = list(reversed(
                payload["input_contract"]["required_abort_conditions"]
            ))
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("input_contract", {row["check_id"] for row in report["failed_checks"]})

    def test_packet_or_handoff_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scaffold.json"
            payload = copy.deepcopy(load_json(DEFAULT_SCAFFOLD_PATH))
            payload["authorization_record_packet"]["record_creation_status"] = "created"
            payload["authorization_record_packet"]["formal_authorization_value_status"] = "collected"
            payload["next_version_handoff"]["not_allowed_yet"].remove("write Qdrant")
            write_json(path, payload)

            report = build_report(path)

        failed = {row["check_id"] for row in report["failed_checks"]}
        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("authorization_packet_blank", failed)
        self.assertIn("handoff_boundaries", failed)

    def test_assertion_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scaffold.json"
            payload = copy.deepcopy(load_json(DEFAULT_SCAFFOLD_PATH))
            payload["assertions"][1]["passed"] = False
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("assertions_present", {row["check_id"] for row in report["failed_checks"]})

    def test_markdown_documents_gate_boundary(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.14.3 Human Rebuild Authorization Record Scaffold Gate", markdown)
        self.assertIn("不收集人工值", markdown)
        self.assertIn("不创建或接受正式授权记录", markdown)
        self.assertIn("不访问或写入 Qdrant", markdown)
        self.assertIn("仍不代表已经允许填写正式授权", markdown)


if __name__ == "__main__":
    unittest.main()
