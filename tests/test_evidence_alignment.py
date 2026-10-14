import tempfile
import unittest
from pathlib import Path

from tools.check_evidence_alignment import (
    DEFAULT_HIDDEN_REPORT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_RAG_REPORT_PATH,
    ISSUE_ANSWER_EVIDENCE_DISCONNECT,
    ISSUE_DEFINITION_ONLY,
    ISSUE_DOMAIN_CONTAMINATION,
    ISSUE_INSUFFICIENT_EVIDENCE_COVERAGE,
    ISSUE_MISSING_PRIMARY_EVIDENCE,
    STATUS_PASS,
    STATUS_REVIEW,
    build_alignment_report,
    evaluate_case,
)


class EvidenceAlignmentTest(unittest.TestCase):
    def test_default_paths_remain_legacy_tests_reports(self):
        self.assertEqual(DEFAULT_RAG_REPORT_PATH, Path("tests/rag_eval_report.json"))
        self.assertEqual(DEFAULT_HIDDEN_REPORT_PATH, Path("tests/hidden_eval_report.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, Path("tests/evidence_alignment_report.json"))

    def test_domain_contamination_uses_expected_domain_and_evidence_category(self):
        result = evaluate_case(
            {
                "id": "case_domain",
                "evidence": [
                    {
                        "source": "Company Law",
                        "category": "公司治理",
                        "article_no": 57,
                    }
                ],
            },
            {"domain": "数据合规", "core_articles": []},
        )

        self.assertEqual(result["alignment_status"], STATUS_REVIEW)
        self.assertIn(ISSUE_DOMAIN_CONTAMINATION, result["detected_issues"])
        self.assertEqual(result["domain_contamination"][0]["domain"], "公司治理")

    def test_primary_issue_coverage_flags_missing_and_insufficient_coverage(self):
        result = evaluate_case(
            {
                "id": "case_primary",
                "evidence": [
                    {"source": "Law A", "category": "数据合规", "article_no": 1},
                ],
            },
            {
                "domain": "数据合规",
                "core_articles": [
                    {"source": "Law A", "article_no": 1},
                    {"source": "Law A", "article_no": 2},
                    {"source": "Law A", "article_no": 3},
                ],
            },
        )

        self.assertIn(ISSUE_MISSING_PRIMARY_EVIDENCE, result["detected_issues"])
        self.assertIn(ISSUE_INSUFFICIENT_EVIDENCE_COVERAGE, result["detected_issues"])
        self.assertEqual(result["primary_issue_coverage"]["matched"], 1)
        self.assertEqual(result["primary_issue_coverage"]["expected"], 3)

    def test_definition_only_flags_missing_operative_support(self):
        result = evaluate_case(
            {
                "id": "case_definition",
                "evidence": [
                    {
                        "source": "个人信息保护法",
                        "category": "数据合规",
                        "article_no": 28,
                        "content": "本法所称敏感个人信息，是指一旦泄露或者非法使用，容易导致自然人人格尊严受到侵害的个人信息。",
                    }
                ],
            },
            {"domain": "数据合规", "core_articles": []},
        )

        self.assertIn(ISSUE_DEFINITION_ONLY, result["detected_issues"])
        self.assertEqual(result["functional_type_counts"]["definition"], 1)

    def test_answer_evidence_disconnect_uses_risk_outputs_without_case_ids(self):
        result = evaluate_case(
            {
                "id": "case_disconnect",
                "risk_types": ["unsupported risk type"],
                "recommended_actions": ["unsupported remediation"],
                "evidence": [
                    {
                        "source": "Law A",
                        "category": "数据合规",
                        "article_no": 1,
                        "content": "general unrelated evidence",
                    }
                ],
            },
            {"domain": "数据合规", "core_articles": []},
        )

        self.assertIn(ISSUE_ANSWER_EVIDENCE_DISCONNECT, result["detected_issues"])
        self.assertEqual(len(result["unsupported_outputs"]), 2)

    def test_clean_case_passes_when_domain_primary_and_output_align(self):
        result = evaluate_case(
            {
                "id": "case_pass",
                "risk_types": ["supported risk"],
                "recommended_actions": ["supported action"],
                "evidence": [
                    {
                        "source": "Law A",
                        "category": "数据合规",
                        "article_no": 1,
                        "content": "supported risk and supported action",
                    }
                ],
            },
            {
                "domain": "数据合规",
                "core_articles": [{"source": "Law A", "article_no": 1}],
            },
        )

        self.assertEqual(result["alignment_status"], STATUS_PASS)
        self.assertEqual(result["detected_issues"], [])

    def test_build_alignment_report_skips_missing_hidden_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            rag_report = tmp / "rag_eval_report.json"
            registry = tmp / "scenario_registry.json"
            hidden_report = tmp / "missing_hidden.json"
            rag_report.write_text(
                '{"reports":[{"id":"case_pass","evidence":[{"source":"Law A","category":"数据合规","article_no":1}]}]}',
                encoding="utf-8",
            )
            registry.write_text('{"scenarios":[]}', encoding="utf-8")

            report = build_alignment_report(
                rag_report_path=rag_report,
                hidden_report_path=hidden_report,
                scenario_registry_path=registry,
            )

        self.assertEqual(report["summary"]["total_cases"], 1)
        self.assertIn(str(hidden_report), report["inputs"]["skipped_inputs"])


if __name__ == "__main__":
    unittest.main()
