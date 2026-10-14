import tempfile
import unittest
from pathlib import Path

from tools.build_risk_level_overrisk_legal_review_packet import build_report, write_json


def eval_case(
    case_id,
    *,
    question,
    category="知识产权",
    risk_types=None,
    actions=None,
    mismatch_type="over_risk",
):
    return {
        "id": case_id,
        "category": category,
        "passed": mismatch_type == "exact_match",
        "retrieval_failure_stage": "PASS",
        "question": question,
        "answer": question,
        "risk_level": "high",
        "risk_types": risk_types or ["商标撤销风险"],
        "recommended_actions": actions or ["保留使用证据"],
        "checks": [
            {
                "name": "expected_risk_level",
                "passed": mismatch_type == "exact_match",
                "details": {
                    "policy": "exact",
                    "actual_level": "high",
                    "expected_level": "medium",
                    "mismatch_type": mismatch_type,
                },
            }
        ],
        "evidence": [
            {
                "source": "中华人民共和国商标法",
                "article_no": 49,
                "citation": "[《中华人民共和国商标法》第四十九条第一款]",
            }
        ],
    }


def expected_case(case_id, *, question, risk_types=None, actions=None, evidence=None):
    return {
        "id": case_id,
        "question": question,
        "expected_risk_level": "medium",
        "expected_risk_types": risk_types or ["商标撤销风险"],
        "expected_actions": actions or ["保留使用证据"],
        "expected_evidence": evidence or [{"source": "中华人民共和国商标法", "article_no": 49}],
        "legal_reasoning": question,
    }


def attribution_row(case_id):
    return {
        "case_id": case_id,
        "primary_attribution": "output_rule_amplification_review",
        "review_routes": ["risk_supplement_rule_review", "answer_wording_overstatement_review"],
        "confidence": "strong_signal",
        "review_reason": "Saved report shows output rule amplification signal.",
        "output_contribution_counts": {"risk_supplement_rules": 1},
    }


class RiskLevelOverriskLegalReviewPacketTest(unittest.TestCase):
    def build_with_rows(self, eval_rows, case_rows, attribution_rows=None):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            eval_path = root / "eval.json"
            cases_path = root / "cases.json"
            attr_path = root / "attr.json"
            write_json(eval_path, {"reports": eval_rows, "total": len(eval_rows), "passed": 0, "failed": len(eval_rows)})
            write_json(cases_path, {"cases": case_rows})
            write_json(attr_path, {"case_rows": attribution_rows or []})
            return build_report(eval_path, attr_path, cases_path, None)

    def test_trademark_non_use_high_is_likely_overstated(self):
        report = self.build_with_rows(
            [
                eval_case(
                    "case_non_use",
                    question="某公司注册商标后连续三年未实际使用，该商标是否存在被撤销风险？",
                )
            ],
            [
                expected_case(
                    "case_non_use",
                    question="某公司注册商标后连续三年未实际使用，该商标是否存在被撤销风险？",
                )
            ],
            [attribution_row("case_non_use")],
        )

        row = report["case_rows"][0]
        self.assertEqual(report["summary"]["status"], "legal_review_packet_ready")
        self.assertEqual(row["legal_reasonableness"], "actual_high_likely_overstated")
        self.assertEqual(row["legal_review_confidence"], "high")
        self.assertEqual(row["manual_review_priority"], 1)
        self.assertFalse(row["rule_change_allowed"])
        self.assertIn("trademark_non_use_is_procedural_cancellation_risk", row["legal_signals"])

    def test_tax_underpayment_signal_is_potentially_defensible(self):
        report = self.build_with_rows(
            [
                eval_case(
                    "case_tax",
                    category="财税",
                    question="企业混合销售未分别核算并统一按低税率纳税，是否存在少缴税款风险？",
                    risk_types=["税务核算风险", "少缴税款风险", "混合销售核算风险", "增值税税率适用错误风险"],
                    actions=["分别核算", "补缴税款", "缴纳滞纳金", "正确适用税率", "完善核算体系"],
                )
            ],
            [
                expected_case(
                    "case_tax",
                    question="企业混合销售未分别核算并统一按低税率纳税，是否存在少缴税款风险？",
                    risk_types=["混合销售核算风险", "税率适用错误风险"],
                    actions=["分别核算不同业务收入", "正确适用税率"],
                    evidence=[
                        {"source": "中华人民共和国增值税法", "article_no": 12},
                        {"source": "中华人民共和国增值税法", "article_no": 13},
                    ],
                )
            ],
            [attribution_row("case_tax")],
        )

        row = report["case_rows"][0]
        self.assertEqual(row["legal_reasonableness"], "actual_high_potentially_defensible")
        self.assertEqual(row["manual_review_priority"], 3)
        self.assertIn("tax_underpayment_or_rate_misapplication_signal", row["legal_signals"])
        self.assertEqual(row["recommended_next_step"], "manual_review_expected_level_before_rule_change")

    def test_no_overrisk_cases_reports_clean_status(self):
        report = self.build_with_rows(
            [
                eval_case(
                    "case_exact",
                    question="普通准确匹配 case",
                    mismatch_type="exact_match",
                )
            ],
            [expected_case("case_exact", question="普通准确匹配 case")],
        )

        self.assertEqual(report["summary"]["status"], "no_overrisk_cases")
        self.assertEqual(report["summary"]["overrisk_case_count"], 0)
        self.assertEqual(report["case_rows"], [])

    def test_attribution_and_expected_refs_are_preserved(self):
        report = self.build_with_rows(
            [
                eval_case(
                    "case_generic",
                    question="某企业将行业通用名称注册为商标并独占使用，是否合法？",
                    risk_types=["商标注册风险", "商标无效风险"],
                )
            ],
            [
                expected_case(
                    "case_generic",
                    question="某企业将行业通用名称注册为商标并独占使用，是否合法？",
                    evidence=[{"source": "中华人民共和国商标法", "article_no": 11}],
                )
            ],
            [attribution_row("case_generic")],
        )

        row = report["case_rows"][0]
        self.assertEqual(row["legal_reasonableness"], "actual_high_likely_overstated")
        self.assertEqual(row["expected_evidence_refs"], [{"source": "中华人民共和国商标法", "article_no": 11}])
        self.assertEqual(row["attribution"]["primary_attribution"], "output_rule_amplification_review")
        self.assertEqual(report["summary"]["rule_change_allowed"], False)


if __name__ == "__main__":
    unittest.main()
