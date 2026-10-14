import unittest
import tempfile
from pathlib import Path

from tools.build_manual_review_ai_suggestion_prefill import build_safe_suggestion
from tools.import_manual_review_workbench import import_rows, read_json_rows


class ManualReviewAiSuggestionPrefillTest(unittest.TestCase):
    def test_build_safe_suggestion_does_not_emit_reviewer_template(self):
        report = build_safe_suggestion(
            {
                "version": "source-v2",
                "guardrails": {"human_confirmation_required": True},
                "workbench_items": [
                    {
                        "case_id": "case_a",
                        "prefill_scope": "draft",
                        "prescreen_confidence": "high",
                        "reviewer_input_template": {
                            "reviewer": "Codex辅助预填（待人工确认）",
                            "reviewed_at": "2026-05-12",
                            "decision": "confirm_diagnostic_issue",
                            "confirmed_root_causes": ["primary_evidence_gap"],
                            "confirmed_follow_up_actions": ["primary_evidence_fixture_candidate_review"],
                            "fixture_candidate": True,
                            "rationale": "AI辅助预填，需人工最终确认。",
                        },
                    }
                ],
            }
        )

        self.assertEqual(report["version"], "0.4.7.8.13")
        self.assertTrue(report["human_confirmation_required"])
        self.assertFalse(report["reviewer_input_template_written"])
        self.assertEqual(report["summary"]["suggestion_items"], 1)
        item = report["workbench_items"][0]
        self.assertNotIn("reviewer_input_template", item)
        self.assertEqual(item["case_id"], "case_a")
        suggestion = item["ai_review_suggestion"]
        self.assertTrue(suggestion["ai_suggestion"])
        self.assertTrue(suggestion["human_confirmation_required"])
        self.assertEqual(suggestion["decision"], "confirm_diagnostic_issue")
        self.assertEqual(suggestion["source_reviewer_label"], "Codex辅助预填（待人工确认）")

    def test_safe_suggestion_is_rejected_by_importer(self):
        report = build_safe_suggestion(
            {
                "workbench_items": [
                    {
                        "case_id": "case_a",
                        "reviewer_input_template": {
                            "reviewer": "Codex辅助预填（待人工确认）",
                            "decision": "confirm_diagnostic_issue",
                            "rationale": "AI辅助预填，需人工最终确认。",
                        },
                    }
                ],
            }
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "safe_suggestion.json"
            path.write_text(__import__("json").dumps(report, ensure_ascii=False), encoding="utf-8")
            rows = read_json_rows(path)

        decision_schema = {
            "version": "schema",
            "decision_records": [{"case_id": "case_a", "decision_status": "pending"}],
        }
        proposed, import_report = import_rows(decision_schema, rows)

        self.assertEqual(import_report["summary"]["imported_rows"], 0)
        self.assertEqual(import_report["summary"]["rejected_rows"], 1)
        self.assertEqual(import_report["summary"]["invalid_json_workbench_export"], 1)
        self.assertEqual(proposed["decision_records"][0]["decision_status"], "pending")


if __name__ == "__main__":
    unittest.main()
