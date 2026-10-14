import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_human_rebuild_authorization_worksheet import (
    DEFAULT_DESIGN_GATE_PATH,
    DEFAULT_DESIGN_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    FIELD_ORDER,
    build_report,
    render_markdown,
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class HumanRebuildAuthorizationWorksheetTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(DEFAULT_DESIGN_PATH, legacy_report_path("rebuild_authorization_design_report.json"))
        self.assertEqual(DEFAULT_DESIGN_GATE_PATH, legacy_report_path("rebuild_authorization_design_gate_report.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("human_rebuild_authorization_worksheet_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/human_rebuild_authorization_worksheet_v0.4.13.15.md"))

    def test_real_inputs_build_blank_worksheet(self):
        report = build_report()
        gate = report["worksheet_gate"]
        summary = report["summary"]

        self.assertEqual(report["version"], "0.4.13.15")
        self.assertEqual(report["schema_kind"], "human_rebuild_authorization_worksheet")
        self.assertEqual(gate["status"], "ready_for_human_rebuild_authorization_review")
        self.assertEqual(gate["allowed_use"], "human_authorization_discussion_only")
        self.assertFalse(gate["human_authorization_record_created"])
        self.assertFalse(gate["authorization_granted"])
        self.assertFalse(gate["qdrant_write_allowed"])
        self.assertFalse(gate["rebuild_allowed"])
        self.assertFalse(gate["captures_formal_authorization_outcome"])
        self.assertEqual(gate["blockers"], [])
        self.assertEqual(summary["allowed_next_step"], "human_rebuild_authorization_worksheet_gate")
        self.assertEqual(summary["collected_value_count"], 0)
        self.assertFalse(summary["human_values_collected"])

    def test_worksheet_rows_match_required_field_order_and_labels(self):
        report = build_report()
        rows = report["authorization_worksheet_rows"]

        self.assertEqual(len(rows), 10)
        self.assertEqual([row["source_required_field"] for row in rows], FIELD_ORDER)
        for row in rows:
            self.assertTrue(row["required"])
            self.assertTrue(row["human_review_required"])
            self.assertEqual(row["human_value_status"], "not_collected")
            self.assertFalse(row["authorization_granted"])
            self.assertFalse(row["rebuild_allowed"])
            self.assertFalse(row["qdrant_write_allowed"])
            labels = row["field_labels"]
            self.assertTrue(any(label["requirement"] == "required" for label in labels))
            self.assertTrue(any(label["requirement"] == "optional" for label in labels))

    def test_operator_approval_row_is_not_current_approval(self):
        report = build_report()
        row = next(row for row in report["authorization_worksheet_rows"] if row["source_required_field"] == "operator_approval")
        labels = {label["field"]: label["requirement"] for label in row["field_labels"]}

        self.assertIn("approver_name", labels)
        self.assertIn("approved_at", labels)
        self.assertIn("explicit_yes_no_authorization", labels)
        self.assertFalse(row["authorization_granted"])
        self.assertFalse(row["captures_formal_authorization_outcome"])

    def test_abort_conditions_are_present_as_required_labels(self):
        report = build_report()
        row = next(
            row for row in report["authorization_worksheet_rows"]
            if row["source_required_field"] == "abort_conditions_acknowledgement"
        )
        required = {label["field"] for label in row["field_labels"] if label["requirement"] == "required"}

        self.assertIn("missing_backup_or_snapshot", required)
        self.assertIn("target_collection_unclear_or_unexpected", required)
        self.assertIn("operator_approval_missing", required)
        self.assertIn("post_rebuild_validation_plan_missing", required)

    def test_failed_gate_blocks_worksheet(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            design = tmp / "design.json"
            gate = tmp / "gate.json"
            write_json(design, load_json(DEFAULT_DESIGN_PATH))
            gate_payload = copy.deepcopy(load_json(DEFAULT_DESIGN_GATE_PATH))
            gate_payload["summary"]["status"] = "failed"
            write_json(gate, gate_payload)

            report = build_report(design, gate)

        self.assertEqual(report["worksheet_gate"]["status"], "blocked")
        self.assertIn("gate_not_passed", report["worksheet_gate"]["blockers"])

    def test_missing_required_field_blocks_worksheet(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            design = tmp / "design.json"
            gate = tmp / "gate.json"
            design_payload = copy.deepcopy(load_json(DEFAULT_DESIGN_PATH))
            design_payload["authorization_design"]["required_confirmation_fields"].remove("backup_plan")
            write_json(design, design_payload)
            write_json(gate, load_json(DEFAULT_DESIGN_GATE_PATH))

            report = build_report(design, gate)

        self.assertEqual(report["worksheet_gate"]["status"], "blocked")
        self.assertIn("design_required_field_drift", report["worksheet_gate"]["blockers"])

    def test_rebuild_permission_drift_blocks_worksheet(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            design = tmp / "design.json"
            gate = tmp / "gate.json"
            write_json(design, load_json(DEFAULT_DESIGN_PATH))
            gate_payload = copy.deepcopy(load_json(DEFAULT_DESIGN_GATE_PATH))
            gate_payload["summary"]["rebuild_allowed"] = True
            write_json(gate, gate_payload)

            report = build_report(design, gate)

        self.assertEqual(report["worksheet_gate"]["status"], "blocked")
        self.assertIn("gate_rebuild_not_blocked", report["worksheet_gate"]["blockers"])

    def test_markdown_is_worksheet_only(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.13.15 Human Rebuild Authorization Worksheet", markdown)
        self.assertIn("没有创建授权记录", markdown)
        self.assertIn("没有授予生产 rebuild 权限", markdown)
        self.assertIn("仍不代表已经允许生产 Qdrant rebuild", markdown)
        for forbidden in ["authorized_actions", "ready_to_apply", "commands", "rebuild_steps"]:
            self.assertNotIn(forbidden, markdown)


if __name__ == "__main__":
    unittest.main()
