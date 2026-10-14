import unittest
from pathlib import Path

from src.rag.complex_case import is_complex_multi_issue_question, plan_complex_case_issues
from tools.run_rag_eval import (
    check_expected_answer_status,
    check_expected_missing_evidence,
    load_cases,
)


COMPLEX_CASES_PATH = Path("tests/complex_case_eval_cases.json")


class ComplexCaseEvalCasesTest(unittest.TestCase):
    def test_complex_case_eval_cases_are_structured_for_specialized_regression(self):
        cases = load_cases(COMPLEX_CASES_PATH)

        self.assertEqual(len(cases), 3)
        for case in cases:
            with self.subTest(case=case["id"]):
                self.assertTrue(is_complex_multi_issue_question(case["question"]))
                self.assertEqual(case["expected_answer_status"], "complex_case_fast_workflow")
                self.assertGreaterEqual(case["k"], 8)
                self.assertTrue(case["expected_missing_evidence_keywords"])
                self.assertTrue(case["expected_answer_keywords"])
                self.assertEqual(case["expected_risk_level"], "high")

    def test_complex_case_planner_exposes_missing_law_gaps(self):
        cases = load_cases(COMPLEX_CASES_PATH)
        expected_gap_terms = {
            "complex_medical_ai_zhizhen_001": ["医疗器械监督管理条例"],
            "complex_credit_ai_xinan_001": ["征信业管理条例"],
            "complex_chip_xintu_001": ["中华人民共和国出口管制法", "BSD 3-Clause", "Apache 2.0"],
        }

        for case in cases:
            with self.subTest(case=case["id"]):
                plans = plan_complex_case_issues(case["question"])
                missing_text = " ".join(
                    missing
                    for plan in plans
                    for missing in plan.get("missing_laws", [])
                )
                for keyword in expected_gap_terms[case["id"]]:
                    self.assertIn(keyword, missing_text)

    def test_new_eval_checks_validate_missing_evidence_and_answer_status(self):
        result = {
            "missing_evidence": ["当前知识库未入库或未覆盖：中华人民共和国出口管制法、BSD 3-Clause 许可证文本"],
            "filters": {"answer_status": "complex_case_fast_workflow"},
        }
        case = {
            "expected_missing_evidence_keywords": ["中华人民共和国出口管制法", "BSD 3-Clause"],
            "expected_answer_status": "complex_case_fast_workflow",
        }

        self.assertTrue(check_expected_missing_evidence(case, result).passed)
        self.assertTrue(check_expected_answer_status(case, result).passed)

    def test_new_eval_checks_report_missing_contract_terms(self):
        result = {
            "missing_evidence": ["当前知识库未入库或未覆盖：中华人民共和国出口管制法"],
            "filters": {"answer_status": "complex_case_fast_workflow"},
        }
        case = {
            "expected_missing_evidence_keywords": ["Apache 2.0"],
            "expected_answer_status": "plain_legal_answer",
        }

        self.assertFalse(check_expected_missing_evidence(case, result).passed)
        self.assertFalse(check_expected_answer_status(case, result).passed)


if __name__ == "__main__":
    unittest.main()
