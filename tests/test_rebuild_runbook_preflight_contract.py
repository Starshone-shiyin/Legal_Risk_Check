import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_rebuild_runbook_preflight_contract import (
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_WORKSHEET_GATE_PATH,
    DEFAULT_WORKSHEET_PATH,
    PREFLIGHT_CHECKS,
    RUNBOOK_PHASES,
    build_report,
    render_markdown,
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class RebuildRunbookPreflightContractTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(DEFAULT_WORKSHEET_GATE_PATH, legacy_report_path("human_rebuild_authorization_worksheet_gate_report.json"))
        self.assertEqual(DEFAULT_WORKSHEET_PATH, legacy_report_path("human_rebuild_authorization_worksheet_report.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("rebuild_runbook_preflight_contract_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/rebuild_runbook_preflight_contract_v0.4.13.17.md"))

    def test_real_inputs_build_contract(self):
        report = build_report()
        summary = report["summary"]
        contract = report["future_runbook_contract"]

        self.assertEqual(report["version"], "0.4.13.17")
        self.assertEqual(report["schema_kind"], "rebuild_runbook_preflight_contract")
        self.assertEqual(summary["status"], "ready_for_series_closeout")
        self.assertEqual(summary["allowed_next_step"], "v0.4.13_series_closeout")
        self.assertFalse(summary["live_preflight_run"])
        self.assertFalse(summary["authorization_granted"])
        self.assertFalse(summary["qdrant_write_allowed"])
        self.assertFalse(summary["rebuild_allowed"])
        self.assertEqual(contract["phase_order"], RUNBOOK_PHASES)
        self.assertEqual(contract["preflight_checks"], PREFLIGHT_CHECKS)

    def test_failed_worksheet_gate_blocks_contract(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            gate = tmp / "gate.json"
            worksheet = tmp / "worksheet.json"
            gate_payload = copy.deepcopy(load_json(DEFAULT_WORKSHEET_GATE_PATH))
            gate_payload["summary"]["status"] = "failed"
            write_json(gate, gate_payload)
            write_json(worksheet, load_json(DEFAULT_WORKSHEET_PATH))

            report = build_report(gate, worksheet)

        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("worksheet_gate_not_passed", report["summary"]["blockers"])

    def test_rebuild_permission_drift_blocks_contract(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            gate = tmp / "gate.json"
            worksheet = tmp / "worksheet.json"
            gate_payload = copy.deepcopy(load_json(DEFAULT_WORKSHEET_GATE_PATH))
            gate_payload["summary"]["rebuild_allowed"] = True
            write_json(gate, gate_payload)
            write_json(worksheet, load_json(DEFAULT_WORKSHEET_PATH))

            report = build_report(gate, worksheet)

        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("worksheet_gate_rebuild_not_blocked", report["summary"]["blockers"])

    def test_markdown_documents_contract_boundary(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.13.17 Rebuild Runbook / Preflight Contract", markdown)
        self.assertIn("不运行 live preflight", markdown)
        self.assertIn("不访问 Qdrant", markdown)
        self.assertIn("仍不代表已经允许生产 Qdrant rebuild", markdown)


if __name__ == "__main__":
    unittest.main()
