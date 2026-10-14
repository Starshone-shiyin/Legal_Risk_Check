import tempfile
import unittest
from pathlib import Path

from tools.build_manual_review_prescreen_report import (
    CATEGORY_CONFIRM,
    CATEGORY_INFRA,
    GUARDRAILS,
    SUGGEST_CONFIRM,
    build_report,
    render_markdown,
)


def write_json(path: Path, payload: str):
    path.write_text(payload, encoding="utf-8")


class ManualReviewPrescreenReportTest(unittest.TestCase):
    def test_content_grounding_gap_becomes_high_confidence_confirm_suggestion(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            workbench = tmp / "workbench.json"
            alignment = tmp / "alignment.json"
            coverage = tmp / "coverage.json"
            rag_report = tmp / "rag_eval_report.json"
            rag_cases = tmp / "rag_eval_cases.json"

            write_json(
                workbench,
                """
                {
                  "version": "wb",
                  "workbench_items": [{
                    "rank": 1,
                    "case_id": "case_gap",
                    "priority_score": 12,
                    "risk_level": "high",
                    "expected_domains": ["数据合规"],
                    "issue_types": ["final_primary_gap", "primary_evidence_lost"],
                    "suggested_root_causes": ["primary_evidence_gap"],
                    "suggested_follow_up_actions": ["primary_evidence_fixture_candidate_review"],
                    "evidence_context_counts": {
                      "missing_final_expected": 1,
                      "missing_scenario_core": 0,
                      "lost_evidence": 1,
                      "final_evidence": 2
                    }
                  }]
                }
                """,
            )
            write_json(
                alignment,
                """
                {"version":"alignment","cases":[{
                  "case_id":"case_gap",
                  "alignment_status":"review",
                  "detected_issues":["missing_primary_evidence"],
                  "review_reasons":["One primary issue lacks evidence."]
                }]}
                """,
            )
            write_json(
                coverage,
                """
                {"version":"coverage","cases":[{
                  "case_id":"case_gap",
                  "coverage_status":"review",
                  "detected_issues":["final_primary_gap"],
                  "review_reasons":["Final evidence_chain does not cover expected statutes."],
                  "final_evidence":[{"source":"Law A","article_no":1,"content_preview":"general"}]
                }]}
                """,
            )
            write_json(
                rag_report,
                """
                {"reports":[{
                  "id":"case_gap",
                  "question":"是否缺少主要证据？",
                  "answer":"原回答",
                  "passed":true,
                  "evidence":[{"source":"Law A","article_no":1,"content":"general"}]
                }]}
                """,
            )
            write_json(
                rag_cases,
                '{"cases":[{"id":"case_gap","question":"是否缺少主要证据？","notes":"fixture"}]}',
            )

            report = build_report(workbench, alignment, coverage, rag_report, rag_cases)

        case = report["cases"][0]
        self.assertEqual(case["prescreen_category"], CATEGORY_CONFIRM)
        self.assertEqual(case["prescreen_suggested_decision"], SUGGEST_CONFIRM)
        self.assertEqual(case["prescreen_confidence"], "high")
        self.assertTrue(case["needs_user_decision"])
        self.assertEqual(report["summary"]["total_cases"], 1)
        self.assertEqual(report["summary"]["high_confidence_cases"], 1)
        self.assertEqual(report["guardrails"], GUARDRAILS)
        self.assertNotIn("reviewer_decision", case)

    def test_infrastructure_only_case_is_not_presented_as_legal_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            workbench = tmp / "workbench.json"
            empty_cases = tmp / "empty_cases.json"
            rag_report = tmp / "rag_eval_report.json"
            rag_cases = tmp / "rag_eval_cases.json"

            write_json(
                workbench,
                """
                {
                  "version": "wb",
                  "workbench_items": [{
                    "rank": 2,
                    "case_id": "case_infra",
                    "priority_score": 2,
                    "risk_level": "medium",
                    "expected_domains": ["财税"],
                    "issue_types": [
                      "base_retrieval_review_needed",
                      "dense_retrieval_gap",
                      "anchor_rescue_pattern"
                    ],
                    "suggested_root_causes": [
                      "metadata_chunking_or_query_coverage",
                      "anchor_dependency_governance"
                    ],
                    "evidence_context_counts": {
                      "missing_final_expected": 0,
                      "missing_scenario_core": 0,
                      "lost_evidence": 0,
                      "final_evidence": 0
                    }
                  }]
                }
                """,
            )
            write_json(empty_cases, '{"cases":[]}')
            write_json(rag_report, '{"reports":[{"id":"case_infra","question":"检索是否稳定？","passed":true}]}')
            write_json(rag_cases, '{"cases":[{"id":"case_infra","question":"检索是否稳定？"}]}')

            report = build_report(workbench, empty_cases, empty_cases, rag_report, rag_cases)

        case = report["cases"][0]
        self.assertEqual(case["prescreen_category"], CATEGORY_INFRA)
        self.assertIn("不等于原答案法律结论一定错误", case["plain_language_guidance"])
        self.assertTrue(case["needs_user_decision"])

    def test_markdown_contains_non_cs_review_guidance(self):
        report = {
            "summary": {
                "total_cases": 1,
                "needs_user_decision": 1,
                "high_confidence_cases": 0,
                "medium_confidence_cases": 1,
                "low_confidence_cases": 0,
                "category_summary": {CATEGORY_INFRA: 1},
            },
            "high_risk_user_decision_list": [],
            "cases": [
                {
                    "case_id": "case_a",
                    "risk_level": "medium",
                    "prescreen_category_label": "检索基建稳定性复核",
                    "prescreen_confidence": "medium",
                    "question": "问题",
                    "reason_summary": ["基础检索层存在缺口。"],
                }
            ],
        }

        markdown = render_markdown(report)

        self.assertIn("离线预筛建议", markdown)
        self.assertIn("不是最终人工复核结论", markdown)
        self.assertIn("不要理解成原答案一定错误", markdown)


if __name__ == "__main__":
    unittest.main()
