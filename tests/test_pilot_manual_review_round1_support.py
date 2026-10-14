import json
import tempfile
import unittest
from pathlib import Path

from tools.build_manual_review_export_pipeline_dry_run import build_report as build_dry_run_report
from tools.build_pilot_manual_review_round1_support import (
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_PILOT_BATCH_PATH,
    DEFAULT_PILOT_REVIEW_ASSIST_PATH,
    GUARDRAILS,
    build_report,
    render_markdown,
)
from tools._shared.layout import legacy_report_path


FORBIDDEN_OUTPUT_KEYS = {
    "reviewer_decision",
    "reviewer_input_template",
    "workbench_items",
    "decision_status",
}


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def evidence(citation: str, functional_type: str = "operative_rule") -> dict:
    return {
        "source": "Test Law",
        "article_no": "1",
        "citation": citation,
        "functional_type": functional_type,
        "content_preview": f"{citation} excerpt.",
    }


def pilot_case(case_id: str) -> dict:
    return {
        "case_id": case_id,
        "rank": 1,
        "risk_level": "high",
        "expected_domains": ["data compliance"],
        "case_topic": "Employee exported customer data.",
        "question": "What risks should the company review?",
        "original_llm_output_excerpt": "The company may face administrative and civil liability.",
        "risk_types_from_original_output": ["data leakage", "administrative penalty"],
        "recommended_actions_from_original_output": ["notify regulator", "remediate"],
        "why_selected": ["high risk", "missing expected evidence"],
    }


def assist_case(case_id: str) -> dict:
    return {
        "case_id": case_id,
        "rank": 1,
        "risk_level": "high",
        "expected_domains": ["data compliance"],
        "case_topic": "Employee exported customer data.",
        "question": "What risks should the company review?",
        "plain_case_brief": "Review whether the evidence supports liability and notification duties.",
        "original_llm_claims": {
            "excerpt": "The company may face administrative and civil liability.",
            "risk_types": ["data leakage", "administrative penalty"],
            "recommended_actions": ["notify regulator", "remediate"],
            "source": "test",
        },
        "evidence_support_assessment": {
            "support_status": "likely_evidence_support_gap_needs_user_confirmation",
            "support_status_label": "Likely evidence gap; user confirmation required",
            "counts": {
                "final_evidence": 3,
                "missing_expected_evidence": 1,
                "missing_scenario_core_evidence": 1,
                "lost_before_final_evidence": 1,
            },
            "detected_assist_signals": [
                {"code": "primary_issue_missing_evidence", "label": "Primary issue lacks evidence"},
                {"code": "final_selection_loss", "label": "Evidence lost before final chain"},
            ],
            "plain_assessment": "Final evidence may miss liability support.",
            "final_evidence_examples": [evidence("Article 1")],
            "missing_expected_evidence_examples": [evidence("Article 66", "liability")],
            "missing_scenario_core_evidence_examples": [evidence("Article 57", "procedural")],
            "lost_before_final_evidence_examples": [evidence("Article 69", "liability")],
        },
        "advisory_review_assist": {
            "advisory_tendency": "likely_review_issue_confirmable_but_user_must_decide",
            "advisory_tendency_label": "Likely confirmable, but user must decide",
            "advisory_rationale": ["This is a reading aid only."],
            "focus_questions_for_user": ["Does Article 66 need to support the liability conclusion?"],
            "user_confirmation_required": True,
            "not_a_reviewer_decision": True,
        },
        "source_signals": {
            "why_selected": ["high risk", "missing expected evidence"],
        },
    }


def minimal_schema(case_id: str) -> dict:
    return {
        "version": "schema-test",
        "summary": {"total_decision_records": 1},
        "decision_records": [{"case_id": case_id, "decision_status": "pending"}],
    }


def minimal_contract() -> dict:
    return {
        "version": "contract-test",
        "scope": "manual review intake contract",
        "guardrails": {"overwrite_original_schema": "disallowed"},
    }


def walk_dicts(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_dicts(child)


class PilotManualReviewRound1SupportTest(unittest.TestCase):
    def test_default_paths_keep_legacy_reports_and_docs_markdown_output(self):
        self.assertEqual(DEFAULT_PILOT_BATCH_PATH, legacy_report_path("manual_review_pilot_batch_report.json"))
        self.assertEqual(
            DEFAULT_PILOT_REVIEW_ASSIST_PATH,
            legacy_report_path("manual_review_pilot_case_review_assist_report.json"),
        )
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("pilot_manual_review_round1_support_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/pilot_manual_review_round1_support_v0.4.7.8.19.md"))

    def test_build_report_is_advisory_support_only(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            pilot_path = tmp / "pilot.json"
            assist_path = tmp / "assist.json"
            write_json(pilot_path, {"version": "0.4.7.8.15", "pilot_cases": [pilot_case("case_a")]})
            write_json(
                assist_path,
                {
                    "version": "0.4.7.8.17",
                    "schema_kind": "advisory_pilot_case_review_assist",
                    "advisory_packet_only": True,
                    "contains_completed_manual_decisions": False,
                    "assisted_cases": [assist_case("case_a")],
                },
            )

            report = build_report(pilot_path, assist_path)

        self.assertEqual(report["version"], "0.4.7.8.19")
        self.assertEqual(report["schema_kind"], "advisory_pilot_manual_review_round1_support")
        self.assertEqual(report["guardrails"], GUARDRAILS)
        self.assertTrue(report["advisory_packet_only"])
        self.assertFalse(report["contains_completed_manual_decisions"])
        self.assertEqual(report["summary"]["round1_support_cases"], 1)
        self.assertEqual(report["summary"]["needs_user_confirmation_cases"], 1)
        self.assertEqual(report["summary"]["completed_manual_decisions"], 0)
        self.assertEqual(report["summary"]["promotion_candidates"], 0)
        self.assertEqual(report["summary"]["ready_action_candidates"], 0)
        self.assertEqual(report["summary"]["attention_level_summary"], {"high": 1})
        self.assertEqual(report["summary"]["signal_summary"]["primary_issue_missing_evidence"], 1)

        case = report["round1_cases"][0]
        self.assertEqual(case["case_id"], "case_a")
        self.assertTrue(case["non_binding_assist_view"]["not_a_reviewer_decision"])
        self.assertTrue(case["non_binding_assist_view"]["must_be_confirmed_by_user"])
        self.assertTrue(case["original_llm_output_for_comparison"]["not_a_current_generation"])
        self.assertIn("缺失的预期条文是否属于本案主争点必须证据？", case["round1_review_prompts"])
        self.assertEqual(case["safe_output_boundary"]["completed_decision_written"], False)
        self.assertEqual(
            {option["option_code"] for option in case["decision_options_explained"]},
            {
                "confirm_diagnostic_issue",
                "confirm_scope_adjustment_needed",
                "reject_diagnostic_issue",
                "insufficient_information",
                "defer",
            },
        )

        for node in walk_dicts(report):
            self.assertFalse(FORBIDDEN_OUTPUT_KEYS & set(node.keys()))
            if node is not report["summary"]:
                self.assertNotIn("promotion_candidates", node)
                self.assertNotIn("ready_action_candidates", node)

    def test_report_can_not_be_imported_as_completed_manual_review(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            pilot_path = tmp / "pilot.json"
            assist_path = tmp / "assist.json"
            support_path = tmp / "round1.json"
            schema_path = tmp / "schema.json"
            contract_path = tmp / "contract.json"
            artifact_dir = tmp / "artifacts"
            write_json(pilot_path, {"pilot_cases": [pilot_case("case_a")]})
            write_json(assist_path, {"assisted_cases": [assist_case("case_a")]})
            write_json(schema_path, minimal_schema("case_a"))
            write_json(contract_path, minimal_contract())
            support_report = build_report(pilot_path, assist_path)
            write_json(support_path, support_report)

            dry_run = build_dry_run_report(schema_path, support_path, contract_path, artifact_dir)
            proposed = json.loads(Path(dry_run["artifacts"]["proposed_schema"]).read_text(encoding="utf-8"))

        self.assertEqual(dry_run["summary"]["imported_rows"], 0)
        self.assertEqual(dry_run["summary"]["promotion_candidates"], 0)
        self.assertEqual(dry_run["summary"]["ready_action_candidates"], 0)
        self.assertEqual(dry_run["summary"]["gate_status"], "blocked")
        self.assertEqual(dry_run["summary"]["pipeline_conclusion"], "blocked_input_rejections_require_review")
        self.assertIn("invalid_json_workbench_export", dry_run["summary"]["dry_run_blockers"])
        self.assertEqual(proposed["decision_records"][0]["decision_status"], "pending")
        self.assertNotIn("reviewer_decision", proposed["decision_records"][0])

    def test_markdown_states_human_review_boundary(self):
        report = {
            "summary": {
                "round1_support_cases": 1,
                "needs_user_confirmation_cases": 1,
                "completed_manual_decisions": 0,
                "promotion_candidates": 0,
                "ready_action_candidates": 0,
                "gate_status": "blocked_until_real_human_review_export_passes_dry_run",
            },
            "round1_cases": [
                {
                    "rank": 1,
                    "case_id": "case_a",
                    "round1_attention_level": "high",
                    "case_under_review": {
                        "plain_case_brief": "Review whether evidence supports liability.",
                    },
                    "original_llm_output_for_comparison": {
                        "risk_types": ["data leakage"],
                        "recommended_actions": ["notify regulator"],
                    },
                    "evidence_snapshot": {
                        "support_status_label": "Likely evidence gap",
                        "signals": [{"label": "Primary issue lacks evidence"}],
                        "examples": {
                            "missing_expected_evidence": [evidence("Article 66")],
                            "missing_scenario_core_evidence": [],
                            "lost_before_final_evidence": [],
                        },
                    },
                    "non_binding_assist_view": {
                        "advisory_tendency_label": "Likely confirmable",
                    },
                    "round1_review_prompts": ["Does Article 66 support liability?"],
                    "decision_options_explained": [
                        {
                            "option_code": "confirm_diagnostic_issue",
                            "plain_label": "确认诊断成立",
                            "when_to_use": "Evidence gap is confirmed.",
                        }
                    ],
                }
            ],
        }

        markdown = render_markdown(report)

        self.assertIn("不是人工复核结论", markdown)
        self.assertIn("不会写入可导入的人工复核字段", markdown)
        self.assertIn("本报告不写 `reviewer_input_template`", markdown)
        self.assertIn("本报告不生成 `reviewer_decision`", markdown)
        self.assertIn("真正治理动作必须等待人工", markdown)


if __name__ == "__main__":
    unittest.main()
