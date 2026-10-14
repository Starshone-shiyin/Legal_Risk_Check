import json
import tempfile
import unittest
from pathlib import Path

from tools.build_manual_review_visual_workbench_contract import (
    GUARDRAILS,
    build_report,
)


def write_json(path: Path, data: dict):
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


class ManualReviewVisualWorkbenchContractTest(unittest.TestCase):
    def test_contract_is_ready_when_required_sources_exist(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            workbench = tmp / "workbench.json"
            intake = tmp / "intake.json"
            closeout = tmp / "closeout.json"
            write_json(
                workbench,
                {
                    "version": "0.4.7.6.0",
                    "summary": {
                        "total_workbench_items": 2,
                        "pending_items": 2,
                        "high_priority_items": 1,
                    },
                    "workbench_items": [],
                },
            )
            write_json(
                intake,
                {
                    "contract": {
                        "version": "0.4.7.7.0",
                        "field_policy": {
                            "read_only_context_fields": ["case_id", "risk_level"],
                            "importable_reviewer_fields": ["reviewer", "decision"],
                            "required_for_completed": ["reviewer", "decision"],
                            "list_fields": [],
                            "boolean_fields": [],
                            "list_delimiter": "|",
                        },
                        "allowed_values": {"decision": ["defer"]},
                        "write_policy": {"main_flow_mutation": "disallowed"},
                    }
                },
            )
            write_json(closeout, {"summary": {"gate_status": "blocked", "blockers": ["x"]}})

            report = build_report(
                workbench_path=workbench,
                intake_contract_path=intake,
                progress_report_path=tmp / "missing_progress.json",
                governance_report_path=tmp / "missing_governance.json",
                import_report_path=tmp / "missing_import.json",
                diff_report_path=tmp / "missing_diff.json",
                validation_report_path=tmp / "missing_validation.json",
                promotion_report_path=tmp / "missing_promotion.json",
                closeout_report_path=closeout,
            )

        self.assertEqual(report["version"], "0.4.7.8.0")
        self.assertTrue(report["summary"]["visual_contract_ready"])
        self.assertEqual(report["summary"]["workbench_items"], 2)
        self.assertEqual(report["summary"]["gate_status"], "blocked")
        self.assertIn("case_detail", report["visual_model"]["layout"]["main_grid"])

    def test_contract_keeps_importable_fields_out_of_read_only_fields(self):
        report = build_report()
        field_contract = report["field_contract"]

        self.assertEqual(field_contract["readonly_importable_overlap"], [])
        self.assertIn("case_id", field_contract["read_only_context_fields"])
        self.assertIn("decision", field_contract["importable_reviewer_fields"])

    def test_guardrails_disallow_main_flow_and_policy_mutation(self):
        self.assertEqual(GUARDRAILS["rag_query_integration"], "disallowed")
        self.assertEqual(GUARDRAILS["anchor_mutation"], "disallowed")
        self.assertEqual(GUARDRAILS["rerank_mutation"], "disallowed")
        self.assertEqual(GUARDRAILS["prompt_mutation"], "disallowed")
        self.assertEqual(GUARDRAILS["eval_case_mutation"], "disallowed")

    def test_export_policy_uses_existing_validation_tools(self):
        report = build_report()
        policy = report["export_policy"]

        self.assertTrue(policy["browser_export_only"])
        self.assertIn("filled_workbench_csv", policy["allowed_exports"])
        self.assertIn("tools/import_manual_review_workbench.py", policy["allowed_next_tools"])
        self.assertIn("src/rag/retriever.py", policy["disallowed_writes"])


if __name__ == "__main__":
    unittest.main()
