import json
import tempfile
import unittest
from pathlib import Path

from tools.build_manual_review_export_pipeline_dry_run import build_report as build_dry_run_report
from tools.build_manual_review_pilot_case_review_assist import (
    GUARDRAILS,
    SUPPORTED_SIGNALS,
    build_report,
    render_markdown,
)


FORBIDDEN_OUTPUT_KEYS = {
    "reviewer_decision",
    "reviewer_input_template",
    "workbench_items",
}


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def evidence(citation: str, functional_type: str = "operative_rule") -> dict:
    return {
        "source": "测试法律",
        "article_no": "1",
        "citation": citation,
        "functional_type": functional_type,
        "content_preview": f"{citation} 的测试摘录。",
    }


def pilot_case(
    case_id: str,
    missing_expected: int = 1,
    missing_core: int = 0,
    lost: int = 1,
    issue_codes: list[str] | None = None,
    functional_typing: int = 0,
) -> dict:
    issue_codes = issue_codes or ["answer_evidence_disconnect", "final_primary_gap"]
    return {
        "case_id": case_id,
        "rank": 1,
        "risk_level": "high",
        "expected_domains": ["数据合规"],
        "case_topic": "测试案由：个人信息处理证据链复核",
        "question": f"{case_id} 是否存在证据链支撑不足？",
        "original_llm_output_excerpt": "原 LLM 输出主张存在行政处罚风险，并建议补充整改动作。",
        "risk_types_from_original_output": ["行政处罚风险", "个人信息处理风险"],
        "recommended_actions_from_original_output": ["补充告知", "完善权限控制"],
        "why_selected": ["高风险", "证据链缺口明显"],
        "evidence_issue_summary": {
            "plain_summary": ["最终证据缺少主要条文。"],
            "evidence_context_counts": {
                "missing_final_expected": missing_expected,
                "missing_scenario_core": missing_core,
                "lost_evidence": lost,
                "final_evidence": 3,
            },
            "detected_issues": [{"code": code, "plain_label": code} for code in issue_codes],
            "issue_family_counts": {"functional_typing": functional_typing},
        },
        "evidence_to_check": {
            "final_evidence": [evidence("测试法律第一条")],
            "missing_expected_evidence": [evidence("测试法律第六十六条", "liability")]
            if missing_expected
            else [],
            "missing_scenario_core_evidence": [evidence("测试法律第三十条", "procedural_rule")]
            if missing_core
            else [],
            "lost_before_final_evidence": [evidence("测试法律第六十九条", "liability")] if lost else [],
        },
        "prescreen_advice": {
            "category": "likely_confirm_diagnostic_issue",
            "category_label": "建议优先确认诊断成立",
            "prescreen_suggested_advisory_decision": "confirm_diagnostic_issue",
            "confidence": "high",
            "score": 80,
            "user_decision_reasons": ["高风险 case 需要人工确认。"],
            "not_a_reviewer_decision": True,
        },
        "ai_suggestion": {
            "present": True,
            "advisory_only": True,
            "human_confirmation_required": True,
            "advisory_decision": "confirm_diagnostic_issue",
            "advisory_root_causes": [{"code": "primary_evidence_gap", "plain_label": "主要证据缺口"}],
            "advisory_follow_up_actions": [
                {"code": "primary_evidence_fixture_candidate_review", "plain_label": "复核 grounding 是否沉淀回归样本"}
            ],
            "not_a_reviewer_decision": True,
        },
    }


def workbench_item(case_id: str) -> dict:
    return {
        "case_id": case_id,
        "issue_types": ["metadata_or_chunking_review_candidate"],
        "suggested_review_questions": ["请确认最终证据是否覆盖主争点。"],
        "evidence_context": {
            "final_evidence": [evidence("测试法律第一条")],
            "missing_final_expected": [evidence("测试法律第六十六条", "liability")],
            "missing_scenario_core": [],
            "lost_evidence": [evidence("测试法律第六十九条", "liability")],
        },
        "evidence_context_counts": {
            "missing_final_expected": 1,
            "missing_scenario_core": 0,
            "lost_evidence": 1,
            "final_evidence": 3,
        },
        "reviewer_input_template": {"decision": "should_not_be_copied"},
    }


def minimal_schema(case_ids: list[str]) -> dict:
    return {
        "version": "schema-test",
        "summary": {"total_decision_records": len(case_ids)},
        "decision_records": [{"case_id": case_id, "decision_status": "pending"} for case_id in case_ids],
    }


def minimal_contract() -> dict:
    return {
        "version": "contract-test",
        "scope": "manual review intake contract",
        "guardrails": {"overwrite_original_schema": "disallowed"},
    }


def walk_values(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_values(child)


def assert_no_completed_decision_structures(testcase: unittest.TestCase, report: dict):
    for node in walk_values(report):
        testcase.assertFalse(FORBIDDEN_OUTPUT_KEYS & set(node.keys()))
        testcase.assertNotEqual(node.get("decision_status"), "completed")
        if node is not report.get("summary"):
            testcase.assertNotIn("promotion_candidates", node)
            testcase.assertNotIn("ready_action_candidates", node)


class ManualReviewPilotCaseReviewAssistTest(unittest.TestCase):
    def test_build_report_is_advisory_only_and_detects_generic_signals(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            pilot_path = tmp / "pilot.json"
            workbench_path = tmp / "workbench.json"
            rag_path = tmp / "rag.json"
            cases = [
                pilot_case(
                    "synthetic_gap",
                    missing_expected=1,
                    missing_core=1,
                    lost=1,
                    issue_codes=["answer_evidence_disconnect", "definition_core_candidate"],
                    functional_typing=1,
                ),
                pilot_case(
                    "synthetic_defer",
                    missing_expected=0,
                    missing_core=0,
                    lost=0,
                    issue_codes=[],
                    functional_typing=0,
                ),
            ]
            write_json(pilot_path, {"version": "pilot-test", "pilot_cases": cases})
            write_json(workbench_path, {"version": "workbench-test", "workbench_items": [workbench_item("synthetic_gap")]})
            write_json(
                rag_path,
                {
                    "reports": [
                        {
                            "id": "synthetic_gap",
                            "answer": "原始答案完整文本。",
                            "risk_types": ["测试风险"],
                            "recommended_actions": ["测试动作"],
                        }
                    ]
                },
            )

            report = build_report(pilot_path, workbench_path, rag_path)

        self.assertEqual(report["version"], "0.4.7.8.17")
        self.assertEqual(report["schema_kind"], "advisory_pilot_case_review_assist")
        self.assertEqual(report["guardrails"], GUARDRAILS)
        self.assertTrue(report["advisory_packet_only"])
        self.assertFalse(report["contains_completed_manual_decisions"])
        self.assertEqual(report["summary"]["assisted_cases"], 2)
        self.assertEqual(report["summary"]["completed_manual_decisions"], 0)
        self.assertEqual(report["summary"]["promotion_candidates"], 0)
        self.assertEqual(report["summary"]["ready_action_candidates"], 0)
        self.assertEqual(report["summary"]["high_attention_manual_review_cases"], 1)
        self.assertIn("primary_issue_missing_evidence", report["summary"]["signal_summary"])
        self.assertIn("definition_substitution_review", report["summary"]["signal_summary"])
        self.assertIn("retrieval_stability_review", report["summary"]["signal_summary"])
        self.assertIn("数据合规", report["summary"]["per_domain_summary"])

        gap_case = next(case for case in report["assisted_cases"] if case["case_id"] == "synthetic_gap")
        signal_codes = {
            signal["code"]
            for signal in gap_case["evidence_support_assessment"]["detected_assist_signals"]
        }
        self.assertEqual(
            gap_case["evidence_support_assessment"]["support_status"],
            "likely_evidence_support_gap_needs_user_confirmation",
        )
        self.assertIn("证据支撑缺口", gap_case["evidence_support_assessment"]["support_status_label"])
        self.assertTrue(
            {
                "primary_issue_missing_evidence",
                "scenario_core_gap",
                "final_selection_loss",
                "answer_evidence_disconnect",
                "definition_substitution_review",
                "retrieval_stability_review",
            }
            <= signal_codes
        )
        self.assertTrue(gap_case["advisory_review_assist"]["user_confirmation_required"])
        self.assertTrue(gap_case["advisory_review_assist"]["not_a_reviewer_decision"])
        self.assertIn("必须由人工决定", gap_case["advisory_review_assist"]["advisory_tendency_label"])
        self.assertEqual(
            gap_case["advisory_review_assist"]["safe_output_boundary"],
            {
                "manual_import_payload_written": False,
                "completed_decision_written": False,
                "promotion_or_ready_action_written": False,
                "user_must_fill_visual_workbench": True,
            },
        )
        self.assertEqual(gap_case["source_signals"]["ai_reference"]["advisory_decision"], "confirm_diagnostic_issue")
        self.assertIn("证据支撑", gap_case["source_signals"]["ai_reference"]["advisory_follow_up_actions"][0])
        self.assertNotIn("grounding", gap_case["source_signals"]["ai_reference"]["advisory_follow_up_actions"][0])
        self.assertNotIn("decision", gap_case["source_signals"]["ai_reference"])
        assert_no_completed_decision_structures(self, report)

    def test_report_can_not_be_imported_as_completed_manual_review(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            pilot_path = tmp / "pilot.json"
            workbench_path = tmp / "workbench.json"
            rag_path = tmp / "rag.json"
            assist_path = tmp / "assist.json"
            schema_path = tmp / "schema.json"
            contract_path = tmp / "contract.json"
            artifact_dir = tmp / "artifacts"
            case_ids = ["synthetic_gap", "synthetic_other", "synthetic_third"]
            write_json(
                pilot_path,
                {
                    "version": "pilot-test",
                    "pilot_cases": [
                        pilot_case(case_ids[0]),
                        pilot_case(case_ids[1]),
                        pilot_case(case_ids[2]),
                    ],
                },
            )
            write_json(workbench_path, {"version": "workbench-test", "workbench_items": []})
            write_json(rag_path, {"reports": []})
            write_json(schema_path, minimal_schema(case_ids))
            write_json(contract_path, minimal_contract())
            assist_report = build_report(pilot_path, workbench_path, rag_path)
            write_json(assist_path, assist_report)

            dry_run = build_dry_run_report(schema_path, assist_path, contract_path, artifact_dir)

        self.assertEqual(dry_run["summary"]["imported_rows"], 0)
        self.assertEqual(dry_run["summary"]["promotion_candidates"], 0)
        self.assertEqual(dry_run["summary"]["ready_action_candidates"], 0)
        self.assertEqual(dry_run["summary"]["gate_status"], "blocked")
        self.assertEqual(dry_run["summary"]["pipeline_conclusion"], "blocked_input_rejections_require_review")

    def test_markdown_plainly_states_advisory_boundary(self):
        report = {
            "supported_signals": SUPPORTED_SIGNALS,
            "summary": {
                "assisted_cases": 1,
                "needs_user_confirmation_cases": 1,
                "high_attention_manual_review_cases": 1,
                "completed_manual_decisions": 0,
                "promotion_candidates": 0,
                "ready_action_candidates": 0,
                "gate_status": "blocked_until_real_human_review_export_passes_dry_run",
            },
            "assisted_cases": [
                {
                    "rank": 1,
                    "case_id": "synthetic_gap",
                    "plain_case_brief": "案由线索是测试。",
                    "advisory_review_assist": {
                        "advisory_tendency": "review_issue_plausible_needs_user_confirmation",
                        "advisory_tendency_label": "诊断问题有一定依据，需要人工确认",
                        "focus_questions_for_user": ["最终 evidence_chain 是否足够？"],
                    },
                    "evidence_support_assessment": {
                        "plain_assessment": "最终证据链存在需要人工确认的证据支撑缺口。",
                        "detected_assist_signals": [{"label": "主争点缺证据"}],
                        "missing_expected_evidence_examples": [evidence("测试法律第六十六条")],
                        "missing_scenario_core_evidence_examples": [],
                        "lost_before_final_evidence_examples": [],
                    },
                    "original_llm_claims": {
                        "risk_types": ["行政处罚风险"],
                        "recommended_actions": ["补充告知"],
                    },
                }
            ],
        }

        markdown = render_markdown(report)

        self.assertIn("不是人工复核结论", markdown)
        self.assertIn("不会写入 `reviewer_input_template`", markdown)
        self.assertIn("只作参考，仍需人工确认", markdown)
        self.assertIn("诊断问题有一定依据，需要人工确认", markdown)
        self.assertIn("不接入 `rag_query`", markdown)
        self.assertIn("真实治理动作必须等人工", markdown)


if __name__ == "__main__":
    unittest.main()
