import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.check_production_rebuild_execution_design_gate import (
    DEFAULT_DESIGN_PATH,
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


class ProductionRebuildExecutionDesignGateTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(DEFAULT_DESIGN_PATH, legacy_report_path("production_rebuild_execution_design_report.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("production_rebuild_execution_design_gate_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/production_rebuild_execution_design_gate_v0.4.14.1.md"))

    def test_real_design_passes_gate(self):
        report = build_report()
        summary = report["summary"]

        self.assertEqual(report["version"], "0.4.14.1")
        self.assertEqual(report["schema_kind"], "production_rebuild_execution_design_gate")
        self.assertEqual(summary["status"], "passed")
        self.assertEqual(summary["check_count"], 16)
        self.assertEqual(summary["failed_check_count"], 0)
        self.assertEqual(summary["allowed_next_step"], "human_rebuild_authorization_record_scaffold")
        self.assertFalse(summary["authorization_record_created"])
        self.assertFalse(summary["authorization_granted"])
        self.assertFalse(summary["live_preflight_run"])
        self.assertFalse(summary["production_rebuild_executed"])
        self.assertFalse(summary["qdrant_write_allowed"])
        self.assertFalse(summary["rebuild_allowed"])
        self.assertEqual(summary["full_eval"], "not_run")

    def test_authorization_or_execution_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "design.json"
            payload = copy.deepcopy(load_json(DEFAULT_DESIGN_PATH))
            payload["summary"]["authorization_granted"] = True
            payload["summary"]["live_preflight_run"] = True
            payload["summary"]["production_rebuild_executed"] = True
            payload["summary"]["rebuild_allowed"] = True
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("no_authorization_or_execution", {row["check_id"] for row in report["failed_checks"]})

    def test_closeout_lineage_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "design.json"
            payload = copy.deepcopy(load_json(DEFAULT_DESIGN_PATH))
            payload["inputs"]["planning_closeout"]["version"] = "0.4.13.99"
            payload["inputs"]["planning_closeout"]["status"] = "production_rebuild_ready"
            payload["inputs"]["authorization_design"] = {"version": "0.4.13.13"}
            payload["execution_design"]["source_of_truth"] = "legacy authorization reports"
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("closeout_lineage", {row["check_id"] for row in report["failed_checks"]})

    def test_guardrail_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "design.json"
            payload = copy.deepcopy(load_json(DEFAULT_DESIGN_PATH))
            payload["guardrails"]["qdrant_write"] = "allowed"
            payload["guardrails"]["collection_rebuild"] = "allowed"
            payload["guardrails"]["prompt_mutation"] = "allowed"
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("guardrails_locked", {row["check_id"] for row in report["failed_checks"]})

    def test_missing_record_contract_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "design.json"
            payload = copy.deepcopy(load_json(DEFAULT_DESIGN_PATH))
            del payload["execution_design"]["record_contracts"]["post_rebuild_validation_record"]
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("record_contracts_present", {row["check_id"] for row in report["failed_checks"]})

    def test_extra_record_contract_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "design.json"
            payload = copy.deepcopy(load_json(DEFAULT_DESIGN_PATH))
            payload["execution_design"]["record_contracts"]["silent_extra_record"] = {"fields": []}
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("record_contracts_present", {row["check_id"] for row in report["failed_checks"]})

    def test_preflight_check_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "design.json"
            payload = copy.deepcopy(load_json(DEFAULT_DESIGN_PATH))
            payload["execution_design"]["record_contracts"]["preflight_record"]["checks"].remove(
                "target_collection_confirmed"
            )
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("preflight_record_contract", {row["check_id"] for row in report["failed_checks"]})

    def test_extra_preflight_check_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "design.json"
            payload = copy.deepcopy(load_json(DEFAULT_DESIGN_PATH))
            payload["execution_design"]["record_contracts"]["preflight_record"]["checks"].append(
                "silent_extra_preflight_check"
            )
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("preflight_record_contract", {row["check_id"] for row in report["failed_checks"]})

    def test_rebuild_record_creation_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "design.json"
            payload = copy.deepcopy(load_json(DEFAULT_DESIGN_PATH))
            payload["execution_design"]["record_contracts"]["rebuild_execution_record"]["must_not_be_created_in_this_version"] = False
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("rebuild_record_not_created", {row["check_id"] for row in report["failed_checks"]})

    def test_decision_policy_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "design.json"
            payload = copy.deepcopy(load_json(DEFAULT_DESIGN_PATH))
            payload["execution_design"]["record_contracts"]["abort_or_acceptance_decision_record"]["automatic_acceptance_allowed"] = True
            payload["execution_design"]["decision_policy"]["main_flow_change"] = "authorized"
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("abort_or_acceptance_policy", {row["check_id"] for row in report["failed_checks"]})

    def test_abort_condition_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "design.json"
            payload = copy.deepcopy(load_json(DEFAULT_DESIGN_PATH))
            payload["execution_design"]["blocking_conditions"].append("silent_extra_abort_condition")
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

        self.assertIn("v0.4.14.1 Production Rebuild Execution Design Gate", markdown)
        self.assertIn("不创建或接受人工授权记录", markdown)
        self.assertIn("不运行 live preflight", markdown)
        self.assertIn("不访问或写入 Qdrant", markdown)
        self.assertIn("不代表已经允许 live preflight", markdown)


if __name__ == "__main__":
    unittest.main()
