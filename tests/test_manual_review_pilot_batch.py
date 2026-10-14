import json
import tempfile
import unittest
from pathlib import Path

from tools.build_manual_review_pilot_batch import (
    GUARDRAILS,
    MAX_PILOT_CASES,
    MIN_PILOT_CASES,
    build_report,
    render_markdown,
)
from tools.build_manual_review_export_pipeline_dry_run import build_report as build_dry_run_report


FORBIDDEN_REPORT_KEYS = {
    "reviewer_decision",
    "reviewer_input_template",
}


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def prescreen_case(
    case_id: str,
    score: int,
    priority: int,
    domain: str = "数据合规",
    confidence: str = "high",
    risk_level: str = "high",
    missing_final: int = 1,
    lost: int = 1,
) -> dict:
    return {
        "case_id": case_id,
        "rank": priority,
        "risk_level": risk_level,
        "priority_score": priority,
        "expected_domains": [domain],
        "question": f"{case_id} 的问题是什么？",
        "original_llm_output_excerpt": f"{case_id} 的原始回答摘录。",
        "risk_types": ["个人信息处理风险"],
        "recommended_actions": ["补充核验证据"],
        "prescreen_category": "likely_confirm_diagnostic_issue",
        "prescreen_category_label": "建议优先确认诊断成立",
        "prescreen_suggested_decision": "confirm_diagnostic_issue",
        "prescreen_confidence": confidence,
        "prescreen_score": score,
        "needs_user_decision": True,
        "user_decision_reasons": ["需要人工确认证据链是否足够。"],
        "plain_language_guidance": "先核对案由和证据链，再判断诊断是否成立。",
        "reason_summary": ["最终证据链缺少主要条文。"],
        "issue_family_counts": {"content_grounding": 1},
        "detected_issue_types": ["final_primary_gap", "answer_evidence_disconnect"],
        "evidence_context_counts": {
            "missing_final_expected": missing_final,
            "missing_scenario_core": 0,
            "lost_evidence": lost,
            "final_evidence": 3,
        },
    }


def workbench_item(case_id: str) -> dict:
    return {
        "case_id": case_id,
        "evidence_context": {
            "final_evidence": [
                {
                    "source": "中华人民共和国个人信息保护法",
                    "article_no": 51,
                    "citation": "[《中华人民共和国个人信息保护法》第五十一条]",
                    "functional_type": "operative_rule",
                    "content_preview": "个人信息处理者应当采取必要措施。",
                }
            ],
            "missing_final_expected": [
                {
                    "source": "中华人民共和国个人信息保护法",
                    "article_no": 66,
                    "citation": "[《中华人民共和国个人信息保护法》第六十六条]",
                    "functional_type": "liability",
                    "content_preview": "违法处理个人信息的法律责任。",
                }
            ],
            "lost_evidence": [],
        },
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
        testcase.assertFalse(FORBIDDEN_REPORT_KEYS & set(node.keys()))
        testcase.assertNotEqual(node.get("decision_status"), "completed")
        testcase.assertNotIn("promotion_candidates", node if node is not report.get("summary") else {})
        testcase.assertNotIn("ready_action_candidates", node if node is not report.get("summary") else {})


class ManualReviewPilotBatchTest(unittest.TestCase):
    def test_build_report_selects_small_human_confirmation_batch(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            prescreen = tmp / "prescreen.json"
            workbench = tmp / "workbench.json"
            ai_suggestion = tmp / "ai.json"
            cases = [
                prescreen_case("case_a", 80, 10, "数据合规"),
                prescreen_case("case_b", 70, 9, "市场秩序"),
                prescreen_case("case_c", 65, 8, "数据合规"),
                prescreen_case("case_d", 50, 7, "财税"),
                prescreen_case("case_e", 45, 6, "民商事"),
                prescreen_case("case_f", 10, 1, "知识产权", confidence="medium", risk_level="medium", missing_final=0, lost=0),
            ]
            write_json(prescreen, {"version": "prescreen-test", "cases": cases})
            write_json(workbench, {"version": "workbench-test", "workbench_items": [workbench_item(case["case_id"]) for case in cases]})
            write_json(
                ai_suggestion,
                {
                    "version": "ai-test",
                    "human_confirmation_required": True,
                    "reviewer_input_template_written": False,
                    "workbench_items": [
                        {
                            "case_id": "case_a",
                            "ai_review_suggestion": {
                                "decision": "confirm_diagnostic_issue",
                                "confirmed_root_causes": ["primary_evidence_gap"],
                                "confirmed_follow_up_actions": ["primary_evidence_fixture_candidate_review"],
                                "fixture_candidate": True,
                                "rationale": "AI suggestion only.",
                                "human_confirmation_required": True,
                            },
                        }
                    ],
                },
            )

            report = build_report(prescreen, workbench, ai_suggestion, limit=5)

        self.assertEqual(report["version"], "0.4.7.8.15")
        self.assertEqual(report["schema_kind"], "advisory_pilot_packet")
        self.assertFalse(report["contains_completed_manual_decisions"])
        self.assertTrue(report["advisory_packet_only"])
        self.assertEqual(report["guardrails"], GUARDRAILS)
        self.assertGreaterEqual(len(report["pilot_cases"]), MIN_PILOT_CASES)
        self.assertLessEqual(len(report["pilot_cases"]), MAX_PILOT_CASES)
        self.assertEqual(report["summary"]["completed_manual_decisions"], 0)
        self.assertEqual(report["summary"]["promotion_candidates"], 0)
        self.assertEqual(report["summary"]["ready_action_candidates"], 0)
        self.assertIn("no_case_id_hardcoding", report["selection_policy"])
        selected_ids = {case["case_id"] for case in report["pilot_cases"]}
        self.assertTrue(selected_ids <= {case["case_id"] for case in cases})
        self.assertIn("case_a", selected_ids)
        for case in report["pilot_cases"]:
            self.assertTrue(case["reviewer_decision_needed"]["human_confirmation_required"])
            self.assertTrue(case["prescreen_advice"]["not_a_reviewer_decision"])
            if case["ai_suggestion"]["present"]:
                self.assertTrue(case["ai_suggestion"]["not_a_reviewer_decision"])
                self.assertIn("advisory_decision", case["ai_suggestion"])
                self.assertNotIn("decision", case["ai_suggestion"])
            self.assertIn("prescreen_suggested_advisory_decision", case["prescreen_advice"])
            self.assertNotIn("suggested_decision", case["prescreen_advice"])
            self.assertIn("reviewer_input_template", case["fields_not_written"])
            self.assertIn("decision_status=completed", case["fields_not_written"])
        assert_no_completed_decision_structures(self, report)

    def test_ai_suggestion_stays_advisory_and_not_completed_decision(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            prescreen = tmp / "prescreen.json"
            workbench = tmp / "workbench.json"
            ai_suggestion = tmp / "ai.json"
            cases = [
                prescreen_case("case_ai", 80, 10),
                prescreen_case("case_b", 70, 9),
                prescreen_case("case_c", 60, 8),
            ]
            write_json(prescreen, {"cases": cases})
            write_json(workbench, {"workbench_items": [workbench_item(case["case_id"]) for case in cases]})
            write_json(
                ai_suggestion,
                {
                    "workbench_items": [
                        {
                            "case_id": "case_ai",
                            "ai_review_suggestion": {
                                "decision": "confirm_diagnostic_issue",
                                "confirmed_root_causes": ["metadata_chunking_or_query_coverage"],
                                "confirmed_follow_up_actions": ["metadata_chunking_or_query_coverage_review"],
                                "rationale": "This is not a reviewer decision.",
                            },
                        }
                    ]
                },
            )

            report = build_report(prescreen, workbench, ai_suggestion, limit=3)

        ai_case = next(case for case in report["pilot_cases"] if case["case_id"] == "case_ai")
        self.assertTrue(ai_case["ai_suggestion"]["present"])
        self.assertTrue(ai_case["ai_suggestion"]["advisory_only"])
        self.assertTrue(ai_case["ai_suggestion"]["human_confirmation_required"])
        self.assertTrue(ai_case["ai_suggestion"]["not_a_reviewer_decision"])
        self.assertEqual(ai_case["ai_suggestion"]["advisory_decision"], "confirm_diagnostic_issue")
        self.assertIn("advisory_root_causes", ai_case["ai_suggestion"])
        self.assertIn("advisory_follow_up_actions", ai_case["ai_suggestion"])
        self.assertIn("advisory_fixture_candidate", ai_case["ai_suggestion"])
        self.assertNotIn("confirmed_root_causes", ai_case["ai_suggestion"])
        self.assertNotIn("confirmed_follow_up_actions", ai_case["ai_suggestion"])
        self.assertNotIn("fixture_candidate", ai_case["ai_suggestion"])
        self.assertNotIn("decision", ai_case["ai_suggestion"])
        self.assertEqual(report["summary"]["advisory_ai_suggestion_cases"], 1)
        self.assertEqual(report["summary"]["human_confirmation_required_cases"], 3)
        assert_no_completed_decision_structures(self, report)

    def test_pilot_packet_is_blocked_if_used_as_dry_run_workbench_input(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            prescreen = tmp / "prescreen.json"
            workbench = tmp / "workbench.json"
            ai_suggestion = tmp / "ai.json"
            packet_path = tmp / "pilot_packet.json"
            schema = tmp / "schema.json"
            contract = tmp / "contract.json"
            artifact_dir = tmp / "artifacts"
            cases = [
                prescreen_case("case_a", 80, 10),
                prescreen_case("case_b", 70, 9),
                prescreen_case("case_c", 60, 8),
            ]
            write_json(prescreen, {"cases": cases})
            write_json(workbench, {"workbench_items": [workbench_item(case["case_id"]) for case in cases]})
            write_json(ai_suggestion, {"workbench_items": []})
            packet = build_report(prescreen, workbench, ai_suggestion, limit=3)
            write_json(packet_path, packet)
            write_json(
                schema,
                {
                    "version": "schema-test",
                    "decision_records": [
                        {"case_id": case["case_id"], "decision_status": "pending"}
                        for case in cases
                    ],
                },
            )
            write_json(contract, {"version": "contract-test", "guardrails": {}})

            dry_run = build_dry_run_report(schema, packet_path, contract, artifact_dir)

        self.assertEqual(dry_run["summary"]["pipeline_conclusion"], "blocked_input_rejections_require_review")
        self.assertEqual(dry_run["summary"]["imported_rows"], 0)
        self.assertEqual(dry_run["summary"]["promotion_candidates"], 0)
        self.assertEqual(dry_run["summary"]["ready_action_candidates"], 0)
        self.assertEqual(dry_run["summary"]["gate_status"], "blocked")
        self.assertIn("no_imported_review_rows", dry_run["summary"]["gate_blockers"])

    def test_selection_works_with_synthetic_case_ids_without_real_id_dependency(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            prescreen = tmp / "prescreen.json"
            workbench = tmp / "workbench.json"
            ai_suggestion = tmp / "ai.json"
            cases = [
                prescreen_case("synthetic_alpha", 80, 10),
                prescreen_case("synthetic_beta", 70, 9),
                prescreen_case("synthetic_gamma", 60, 8),
                prescreen_case("synthetic_delta", 50, 7),
            ]
            write_json(prescreen, {"cases": cases})
            write_json(workbench, {"workbench_items": [workbench_item(case["case_id"]) for case in cases]})
            write_json(ai_suggestion, {"workbench_items": []})

            report = build_report(prescreen, workbench, ai_suggestion, limit=3)

        selected_ids = [case["case_id"] for case in report["pilot_cases"]]
        self.assertEqual(selected_ids, ["synthetic_alpha", "synthetic_beta", "synthetic_gamma"])
        self.assertTrue(report["selection_policy"]["no_case_id_hardcoding"])

    def test_markdown_states_pilot_batch_is_not_manual_conclusion(self):
        report = {
            "summary": {
                "source_total_cases": 3,
                "pilot_case_count": 3,
                "human_confirmation_required_cases": 3,
                "advisory_ai_suggestion_cases": 1,
                "completed_manual_decisions": 0,
                "promotion_candidates": 0,
                "ready_action_candidates": 0,
                "gate_status": "blocked_until_real_human_review_export_passes_dry_run",
            },
            "pilot_cases": [
                {
                    "case_id": "case_a",
                    "risk_level": "high",
                    "case_topic": "员工数据导出风险",
                    "question": "问题",
                    "why_selected": ["高风险 case。"],
                    "original_llm_output_excerpt": "原回答",
                    "prescreen_advice": {
                        "confidence": "high",
                        "category_label": "建议优先确认诊断成立",
                        "score": 80,
                    },
                    "evidence_issue_summary": {
                        "plain_summary": ["最终证据缺少主要条文。"],
                        "evidence_context_counts": {
                            "missing_final_expected": 1,
                            "missing_scenario_core": 0,
                            "lost_evidence": 0,
                        },
                    },
                    "evidence_to_check": {
                        "final_evidence": [],
                        "missing_expected_evidence": [],
                        "lost_before_final_evidence": [],
                    },
                    "ai_suggestion": {"present": False},
                }
            ],
        }

        markdown = render_markdown(report)

        self.assertIn("不是人工复核结论", markdown)
        self.assertIn("AI suggestion 只作为参考", markdown)
        self.assertIn("判断标准与填写口径", markdown)
        self.assertIn("ready action candidates：0", markdown)
        self.assertIn("不修改 hidden seed", markdown)
        self.assertIn("只有真实人工填写并导出后", markdown)


if __name__ == "__main__":
    unittest.main()
