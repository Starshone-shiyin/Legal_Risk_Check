import tempfile
import unittest
from pathlib import Path

from tools.analyze_legal_functional_typing_errors import (
    analyze_alignment_report,
    analyze_audit_report,
    analyze_fixture_report,
    build_report,
    prioritize_actions,
)


class LegalFunctionalTypingErrorAnalysisTest(unittest.TestCase):
    def test_fixture_failures_become_p0_action(self):
        fixture = {
            "passed": False,
            "summary": {
                "total_cases": 1,
                "failed_cases": 1,
                "failures_by_expected_type": {"principle": ["case_a"]},
            },
            "cases": [
                {
                    "id": "case_a",
                    "passed": False,
                    "expected_functional_type": "principle",
                    "actual_functional_type": "operative_rule",
                    "matched_rule": "rule:operative_rule",
                    "matched_terms": ["应当"],
                }
            ],
        }
        audit = {"summary": {}, "documents": []}
        alignment = {"summary": {}, "cases": []}

        actions = prioritize_actions(
            analyze_fixture_report(fixture),
            analyze_audit_report(audit),
            analyze_alignment_report(alignment),
        )

        self.assertEqual(actions[0]["priority"], "P0")
        self.assertIn("golden fixture failures", actions[0]["action"])

    def test_high_unclassified_document_becomes_p1_action(self):
        fixture = {"passed": True, "summary": {"failed_cases": 0}, "cases": []}
        audit = {
            "summary": {
                "total_documents": 1,
                "review_documents": 1,
                "total_chunks": 10,
                "unclassified_ratio": 0.5,
                "operative_support_ratio": 0.2,
            },
            "documents": [
                {
                    "source": "Tax Law",
                    "domain": "tax",
                    "document_type": "法律法规",
                    "total_chunks": 10,
                    "unclassified_ratio": 0.5,
                    "operative_support_ratio": 0.2,
                    "operative_support_chunks": 2,
                    "functional_type_counts": {"unclassified": 5, "operative_rule": 2},
                    "review_reasons": ["More than 35% of chunks are unclassified."],
                }
            ],
        }
        alignment = {"summary": {}, "cases": []}

        actions = prioritize_actions(
            analyze_fixture_report(fixture),
            analyze_audit_report(audit),
            analyze_alignment_report(alignment),
        )

        self.assertEqual(actions[0]["priority"], "P1")
        self.assertIn("unclassified", actions[0]["action"])

    def test_alignment_issues_are_summarized(self):
        alignment = {
            "summary": {
                "total_cases": 2,
                "review_cases": 2,
                "issue_type_summary": {
                    "missing_primary_evidence": 1,
                    "answer_evidence_disconnect": 1,
                },
                "high_risk_manual_review": [{"case_id": "case_a"}],
            },
            "cases": [
                {
                    "case_id": "case_a",
                    "detected_issues": ["missing_primary_evidence"],
                    "expected_domains": ["数据合规"],
                    "review_reasons": ["missing"],
                },
                {
                    "case_id": "case_b",
                    "detected_issues": ["answer_evidence_disconnect"],
                    "expected_domains": ["财税"],
                    "review_reasons": ["unsupported"],
                },
            ],
        }

        analysis = analyze_alignment_report(alignment)

        self.assertEqual(len(analysis["missing_primary_cases"]), 1)
        self.assertEqual(len(analysis["unsupported_output_cases"]), 1)
        self.assertEqual(analysis["high_risk_manual_review_count"], 1)

    def test_build_report_from_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            fixture = tmp / "fixture.json"
            audit = tmp / "audit.json"
            alignment = tmp / "alignment.json"
            fixture.write_text(
                '{"passed":true,"summary":{"total_cases":1,"failed_cases":0},"cases":[]}',
                encoding="utf-8",
            )
            audit.write_text(
                '{"summary":{"total_documents":1,"review_documents":0,"total_chunks":1,'
                '"unclassified_ratio":0.0,"operative_support_ratio":1.0},'
                '"documents":[]}',
                encoding="utf-8",
            )
            alignment.write_text(
                '{"summary":{"total_cases":1,"review_cases":0,"issue_type_summary":{},'
                '"high_risk_manual_review":[]},"cases":[]}',
                encoding="utf-8",
            )

            report = build_report(fixture, audit, alignment)

        self.assertEqual(report["version"], "0.4.7.2.3")
        self.assertEqual(report["summary"]["fixture_failed_cases"], 0)
        self.assertEqual(report["summary"]["alignment_review_cases"], 0)


if __name__ == "__main__":
    unittest.main()
