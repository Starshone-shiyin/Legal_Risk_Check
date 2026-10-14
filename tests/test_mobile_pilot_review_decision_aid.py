import json
import tempfile
import unittest
from pathlib import Path

from tools.build_manual_review_export_pipeline_dry_run import build_report as build_dry_run_report
from tools.build_mobile_pilot_review_decision_aid import (
    DEFAULT_CONTRACT_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_ROUND1_SUPPORT_PATH,
    GUARDRAILS,
    build_report,
    render_markdown,
)
from tools._shared.layout import legacy_report_path


FORBIDDEN_OUTPUT_KEYS = {
    "reviewer",
    "reviewed_at",
    "decision",
    "confirmed_root_causes",
    "rejected_root_causes",
    "confirmed_follow_up_actions",
    "proposed_change_targets",
    "fixture_candidate",
    "rationale",
    "notes",
    "reviewer_decision",
    "reviewer_input_template",
    "workbench_items",
    "decision_status",
}


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def round1_case(case_id: str) -> dict:
    return {
        "case_id": case_id,
        "rank": 1,
        "round1_attention_level": "high",
        "case_under_review": {
            "plain_case_brief": "Employee exported customer data; review evidence support.",
            "question": "What risks should be reviewed?",
        },
        "original_llm_output_for_comparison": {
            "risk_types": ["data leakage", "administrative penalty"],
            "recommended_actions": ["notify regulator"],
        },
        "evidence_snapshot": {
            "support_status": "likely_evidence_support_gap_needs_user_confirmation",
            "support_status_label": "Likely evidence gap",
            "counts": {
                "final_evidence": 3,
                "missing_expected_evidence": 1,
                "missing_scenario_core_evidence": 0,
                "lost_before_final_evidence": 1,
            },
            "signals": [
                {"code": "primary_issue_missing_evidence", "label": "Primary issue lacks evidence"},
                {"code": "final_selection_loss", "label": "Final evidence selection loss"},
            ],
            "examples": {
                "missing_expected_evidence": [
                    {"citation": "Article 66", "source": "PIPL", "content_preview": "Liability clause."}
                ],
                "missing_scenario_core_evidence": [],
                "lost_before_final_evidence": [
                    {"citation": "Article 69", "source": "PIPL", "content_preview": "Civil liability."}
                ],
            },
        },
        "round1_review_prompts": [
            "Does Article 66 need to support the liability conclusion?",
            "Should Article 69 be retained in final evidence?",
        ],
    }


def contract() -> dict:
    return {
        "version": "contract-test",
        "field_contract": {
            "allowed_values": {
                "confirmed_root_causes": [
                    "primary_evidence_gap",
                    "final_evidence_selection_policy",
                ],
                "confirmed_follow_up_actions": [
                    "primary_evidence_fixture_candidate_review",
                    "final_evidence_selection_policy_review",
                    "needs_additional_evidence_capture",
                ],
            }
        },
    }


def minimal_schema(case_id: str) -> dict:
    return {
        "version": "schema-test",
        "summary": {"total_decision_records": 1},
        "decision_records": [{"case_id": case_id, "decision_status": "pending"}],
    }


def minimal_contract() -> dict:
    return {"version": "contract-test", "scope": "manual review intake contract"}


def walk_dicts(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_dicts(child)


class MobilePilotReviewDecisionAidTest(unittest.TestCase):
    def test_default_paths_keep_legacy_reports_and_docs_markdown_output(self):
        self.assertEqual(DEFAULT_ROUND1_SUPPORT_PATH, legacy_report_path("pilot_manual_review_round1_support_report.json"))
        self.assertEqual(DEFAULT_CONTRACT_PATH, legacy_report_path("manual_review_visual_workbench_contract_report.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("mobile_pilot_review_decision_aid_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/mobile_pilot_review_decision_aid_v0.4.7.8.20.md"))

    def test_build_report_uses_mobile_advisory_fields_only(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            round1_path = tmp / "round1.json"
            contract_path = tmp / "contract.json"
            write_json(round1_path, {"version": "0.4.7.8.19", "round1_cases": [round1_case("case_a")]})
            write_json(contract_path, contract())

            report = build_report(round1_path, contract_path)

        self.assertEqual(report["version"], "0.4.7.8.20")
        self.assertEqual(report["schema_kind"], "advisory_mobile_pilot_review_decision_aid")
        self.assertEqual(report["guardrails"], GUARDRAILS)
        self.assertTrue(report["advisory_packet_only"])
        self.assertFalse(report["contains_completed_manual_decisions"])
        self.assertEqual(report["summary"]["mobile_cards"], 1)
        self.assertEqual(report["summary"]["user_confirmation_needed_cases"], 1)
        self.assertEqual(report["summary"]["completed_manual_decisions"], 0)
        self.assertEqual(report["summary"]["promotion_candidates"], 0)
        self.assertEqual(report["summary"]["ready_action_candidates"], 0)
        self.assertEqual(report["summary"]["mobile_advisory_tendency_summary"], {"confirm_diagnostic_issue": 1})

        card = report["mobile_cards"][0]
        self.assertEqual(card["case_id"], "case_a")
        self.assertEqual(card["mobile_advisory_tendency"], "confirm_diagnostic_issue")
        self.assertIn("primary_evidence_gap", card["mobile_advisory_root_cause_codes"])
        self.assertIn("primary_evidence_fixture_candidate_review", card["mobile_advisory_follow_up_action_codes"])
        self.assertTrue(card["mobile_user_confirmation_required"])
        self.assertTrue(card["mobile_not_reviewer_decision"])
        self.assertGreaterEqual(len(card["mobile_review_lines"]), 5)

        for node in walk_dicts(report):
            self.assertFalse(FORBIDDEN_OUTPUT_KEYS & set(node.keys()))

    def test_report_can_not_be_imported_as_completed_manual_review(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            round1_path = tmp / "round1.json"
            contract_path = tmp / "contract.json"
            aid_path = tmp / "mobile_aid.json"
            schema_path = tmp / "schema.json"
            intake_contract_path = tmp / "intake_contract.json"
            artifact_dir = tmp / "artifacts"
            write_json(round1_path, {"round1_cases": [round1_case("case_a")]})
            write_json(contract_path, contract())
            write_json(schema_path, minimal_schema("case_a"))
            write_json(intake_contract_path, minimal_contract())
            aid_report = build_report(round1_path, contract_path)
            write_json(aid_path, aid_report)

            dry_run = build_dry_run_report(schema_path, aid_path, intake_contract_path, artifact_dir)
            proposed = json.loads(Path(dry_run["artifacts"]["proposed_schema"]).read_text(encoding="utf-8"))

        self.assertEqual(dry_run["summary"]["imported_rows"], 0)
        self.assertEqual(dry_run["summary"]["promotion_candidates"], 0)
        self.assertEqual(dry_run["summary"]["ready_action_candidates"], 0)
        self.assertEqual(dry_run["summary"]["gate_status"], "blocked")
        self.assertEqual(dry_run["summary"]["pipeline_conclusion"], "blocked_input_rejections_require_review")
        self.assertIn("invalid_json_workbench_export", dry_run["summary"]["dry_run_blockers"])
        self.assertEqual(proposed["decision_records"][0]["decision_status"], "pending")

    def test_markdown_states_confirmation_boundary(self):
        report = {
            "summary": {
                "mobile_cards": 1,
                "user_confirmation_needed_cases": 1,
                "completed_manual_decisions": 0,
                "promotion_candidates": 0,
                "ready_action_candidates": 0,
                "gate_status": "blocked_until_real_human_review_export_passes_dry_run",
            },
            "mobile_cards": [
                {
                    "mobile_card_title": "1. case_a",
                    "mobile_review_lines": ["案由：test", "建议倾向：test"],
                    "mobile_advisory_tendency": "confirm_diagnostic_issue",
                    "mobile_advisory_rationale": "Only a mobile aid.",
                }
            ],
        }

        markdown = render_markdown(report)

        self.assertIn("手机端确认前草稿", markdown)
        self.assertIn("不是人工复核结论", markdown)
        self.assertIn("本报告不写 `reviewer_input_template`", markdown)
        self.assertIn("真正结论必须由用户", markdown)


if __name__ == "__main__":
    unittest.main()
