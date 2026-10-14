import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.check_human_rebuild_authorization_worksheet_gate import (
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_WORKSHEET_PATH,
    FIELD_ORDER,
    build_report,
    render_markdown,
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class HumanRebuildAuthorizationWorksheetGateTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(DEFAULT_WORKSHEET_PATH, legacy_report_path("human_rebuild_authorization_worksheet_report.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("human_rebuild_authorization_worksheet_gate_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/human_rebuild_authorization_worksheet_gate_v0.4.13.16.md"))

    def test_real_worksheet_passes_gate(self):
        report = build_report()
        summary = report["summary"]

        self.assertEqual(report["version"], "0.4.13.16")
        self.assertEqual(report["schema_kind"], "human_rebuild_authorization_worksheet_gate")
        self.assertEqual(summary["status"], "passed")
        self.assertEqual(summary["failed_check_count"], 0)
        self.assertEqual(summary["allowed_next_step"], "rebuild_runbook_preflight_contract")
        self.assertFalse(summary["human_values_collected"])
        self.assertFalse(summary["authorization_granted"])
        self.assertFalse(summary["qdrant_write_allowed"])
        self.assertFalse(summary["rebuild_allowed"])

    def test_row_order_and_no_value_contract(self):
        worksheet = load_json(DEFAULT_WORKSHEET_PATH)
        self.assertEqual([row["source_required_field"] for row in worksheet["authorization_worksheet_rows"]], FIELD_ORDER)
        report = build_report()
        self.assertNotIn("row_contract", {row["check_id"] for row in report["failed_checks"]})

    def test_collected_value_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "worksheet.json"
            payload = copy.deepcopy(load_json(DEFAULT_WORKSHEET_PATH))
            payload["summary"]["collected_value_count"] = 1
            payload["summary"]["human_values_collected"] = True
            payload["authorization_worksheet_rows"][0]["human_value_status"] = "collected"
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("no_values_or_authorization", {row["check_id"] for row in report["failed_checks"]})
        self.assertIn("row_contract", {row["check_id"] for row in report["failed_checks"]})

    def test_authorization_or_rebuild_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "worksheet.json"
            payload = copy.deepcopy(load_json(DEFAULT_WORKSHEET_PATH))
            payload["worksheet_gate"]["authorization_granted"] = True
            payload["worksheet_gate"]["rebuild_allowed"] = True
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("no_values_or_authorization", {row["check_id"] for row in report["failed_checks"]})

    def test_missing_optional_label_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "worksheet.json"
            payload = copy.deepcopy(load_json(DEFAULT_WORKSHEET_PATH))
            payload["authorization_worksheet_rows"][0]["field_labels"] = [
                label for label in payload["authorization_worksheet_rows"][0]["field_labels"]
                if label["requirement"] != "optional"
            ]
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("row_contract", {row["check_id"] for row in report["failed_checks"]})

    def test_markdown_documents_gate_boundary(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.13.16 Human Rebuild Authorization Worksheet Gate", markdown)
        self.assertIn("不收集人工值", markdown)
        self.assertIn("不创建授权记录", markdown)
        self.assertIn("仍不代表已经允许生产 Qdrant rebuild", markdown)


if __name__ == "__main__":
    unittest.main()
