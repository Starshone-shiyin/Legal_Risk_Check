import tempfile
import unittest
from pathlib import Path

from tools.build_rag_expected_level_review_packet import build_report, write_json


def check(name, passed=True, details=None):
    return {"name": name, "passed": passed, "details": details}


def report(case_id, *, passed=False, stage="PASS", failed_check="expected_risk_level"):
    checks = [
        check("expected_evidence"),
        check("expected_answer_keywords"),
        check("min_confidence_score"),
        check("expected_risk_types"),
        check(
            "expected_risk_level",
            passed=failed_check != "expected_risk_level",
            details={"actual_level": "high", "expected_level": "medium", "mismatch_type": "over_risk"},
        ),
        check("expected_actions"),
    ]
    if failed_check and failed_check != "expected_risk_level":
        checks.append(check(failed_check, passed=False))
    return {
        "id": case_id,
        "passed": passed,
        "retrieval_failure_stage": stage,
        "question": "question",
        "answer": "answer",
        "checks": checks,
        "evidence": [{"source": "Law", "article_no": 7, "citation": "[Law Article 7]"}],
        "retrieval_diagnostics": {
            "layers": {
                "dense": {"satisfied": stage == "PASS", "matched_count": 1, "expected_count": 1},
                "union": {"satisfied": stage == "PASS", "matched_count": 1, "expected_count": 1},
                "final": {"satisfied": stage == "PASS", "matched_count": 1, "expected_count": 1},
            }
        },
    }


def case(case_id):
    return {
        "id": case_id,
        "expected_risk_level": "medium",
        "risk_level_reason": "fact strength supports medium",
        "legal_reasoning": "Article 6 reasoning",
        "expected_evidence": [{"source": "Law", "article_no": 7}],
        "expected_risk_types": ["type"],
        "expected_actions": ["action"],
    }


class RagExpectedLevelReviewPacketTest(unittest.TestCase):
    def build_with(self, runs, cases):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repeat_path = root / "repeat.json"
            cases_path = root / "cases.json"
            write_json(repeat_path, {"repeat": len(runs), "runs": [{"reports": run} for run in runs]})
            write_json(cases_path, {"cases": cases})
            return build_report(repeat_path, cases_path)

    def test_expected_level_only_failure_is_classified_without_runtime_patch(self):
        result = self.build_with(
            [[report("case_a")], [report("case_a")], [report("case_a")]],
            [case("case_a")],
        )

        row = result["case_rows"][0]
        self.assertEqual(result["summary"]["status"], "expected_level_review_packet_ready")
        self.assertEqual(row["review_classification"], "expected_level_fact_strength_review")
        self.assertTrue(row["all_retrieval_pass"])
        self.assertTrue(row["all_non_level_checks_pass"])
        self.assertFalse(row["runtime_patch_allowed"])
        self.assertEqual(result["summary"]["runtime_patch_recommendation"], "not_recommended_by_this_packet")

    def test_retrieval_failure_is_not_collapsed_into_expected_level_review(self):
        result = self.build_with(
            [[report("case_a", stage="EVIDENCE_MISSING")]],
            [case("case_a")],
        )

        self.assertEqual(result["summary"]["status"], "retrieval_review_required")
        self.assertEqual(result["case_rows"][0]["review_classification"], "retrieval_or_evidence_chain_review")

    def test_additional_failed_check_routes_to_output_or_eval_contract_review(self):
        result = self.build_with(
            [[report("case_a", failed_check="expected_actions")]],
            [case("case_a")],
        )

        self.assertEqual(result["case_rows"][0]["review_classification"], "output_or_eval_contract_review")


if __name__ == "__main__":
    unittest.main()
