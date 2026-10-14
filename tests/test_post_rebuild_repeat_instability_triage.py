import copy
import tempfile
import unittest
from pathlib import Path

from tools.build_post_rebuild_repeat_instability_triage import (
    DEFAULT_ALGORITHM_REPEAT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_PRODUCT_REPEAT_PATH,
    DEFAULT_SUMMARY_PATH,
    GUARDRAILS,
    build_report,
    render_markdown,
)
from tools.build_post_rebuild_repeat_stability_summary import write_json


def case_row(case_id, *, passed=True, labels=None, article=24, answer="答案包含赔偿"):
    return {
        "id": case_id,
        "retrieval_failure_stage": "PASS",
        "contribution_labels": labels or ["PURE_LLM_PASS"],
        "passed": passed,
        "checks": [
            {"name": "expected_answer_keywords", "passed": passed, "message": "ok"},
        ],
        "answer": answer,
        "evidence": [
            {
                "source": "中华人民共和国个人信息保护法",
                "law_name": "中华人民共和国个人信息保护法",
                "article_no": article,
                "section_no": "",
                "citation": f"[《中华人民共和国个人信息保护法》第{article}条]",
            }
        ],
    }


def repeat_report(case_id, rows):
    runs = []
    for index, row in enumerate(rows, start=1):
        runs.append({
            "run": index,
            "total": 1,
            "passed": 1 if row["passed"] else 0,
            "failed": 0 if row["passed"] else 1,
            "retrieval_failure_stage_summary": {"PASS": 1},
            "contribution_summary": {"label_counts": {}, "dense_fallback_passed": 0},
            "reports": [row],
        })
    return {
        "repeat": len(runs),
        "stability_summary": {
            "runs": len(runs),
            "all_runs_full_pass": all(row["passed"] for row in rows),
            "pass_counts": [run["passed"] for run in runs],
            "total_counts": [1 for _ in runs],
            "unstable_cases": [],
            "label_variation_cases": [],
        },
        "runs": runs,
    }


def minimal_previous_summary():
    return {
        "summary": {"status": "needs_triage", "blockers": ["repeat_not_all_runs_full_pass"]},
    }


def minimal_previous_repeat():
    return {
        "stability_summary": {"pass_counts": [60, 60, 59]},
    }


class PostRebuildRepeatInstabilityTriageTest(unittest.TestCase):
    def test_default_paths_and_guardrails(self):
        self.assertEqual(DEFAULT_PRODUCT_REPEAT_PATH, Path("tests/targeted_repeat_product_liability_v0.4.15.1_report.json"))
        self.assertEqual(DEFAULT_ALGORITHM_REPEAT_PATH, Path("tests/targeted_repeat_algorithm_bias_v0.4.15.1_report.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, Path("tests/post_rebuild_repeat_instability_triage_v0.4.15.1_report.json"))
        self.assertEqual(DEFAULT_SUMMARY_PATH, Path("docs/post_rebuild_repeat_instability_triage_v0.4.15.1.md"))
        self.assertTrue(GUARDRAILS["saved_reports_only"])
        self.assertEqual(GUARDRAILS["rag_query_call"], "disallowed")
        self.assertEqual(GUARDRAILS["qdrant_access"], "disallowed")
        self.assertEqual(GUARDRAILS["anchor_mutation"], "disallowed")
        self.assertEqual(GUARDRAILS["eval_case_mutation"], "disallowed")

    def test_output_wording_variation_without_failure_is_nonblocking(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            product = repeat_report(
                "risk_tort_product_liability_001",
                [
                    case_row("risk_tort_product_liability_001", article=1203, answer="答案一，包含赔偿"),
                    case_row("risk_tort_product_liability_001", article=1203, answer="答案二，也包含赔偿"),
                ],
            )
            algorithm = repeat_report(
                "risk_algorithm_bias_001",
                [
                    case_row("risk_algorithm_bias_001", article=24),
                    case_row("risk_algorithm_bias_001", article=24),
                ],
            )
            paths = {
                "product": root / "product.json",
                "algorithm": root / "algorithm.json",
                "previous": root / "previous.json",
                "summary": root / "summary.json",
                "baseline": root / "baseline.json",
                "cases": root / "cases.json",
            }
            write_json(paths["product"], product)
            write_json(paths["algorithm"], algorithm)
            write_json(paths["previous"], minimal_previous_repeat())
            write_json(paths["summary"], minimal_previous_summary())
            write_json(paths["baseline"], {"passed": 60, "total": 60})
            write_json(paths["cases"], {"cases": []})

            report = build_report(
                product_repeat_path=paths["product"],
                algorithm_repeat_path=paths["algorithm"],
                previous_repeat_path=paths["previous"],
                previous_summary_path=paths["summary"],
                baseline_path=paths["baseline"],
                cases_path=paths["cases"],
            )

        product_triage = next(item for item in report["case_triage"] if item["id"] == "risk_tort_product_liability_001")
        self.assertEqual(product_triage["classification"], "output_wording_variation_without_current_check_failure")
        self.assertFalse(product_triage["blocking"])

    def test_final_evidence_identity_drift_is_blocking_even_when_all_runs_pass(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            product = repeat_report(
                "risk_tort_product_liability_001",
                [case_row("risk_tort_product_liability_001", article=1203), case_row("risk_tort_product_liability_001", article=1203)],
            )
            algorithm = repeat_report(
                "risk_algorithm_bias_001",
                [case_row("risk_algorithm_bias_001", article=24), case_row("risk_algorithm_bias_001", article=56)],
            )
            paths = {key: root / f"{key}.json" for key in ["product", "algorithm", "previous", "summary", "baseline", "cases"]}
            write_json(paths["product"], product)
            write_json(paths["algorithm"], algorithm)
            write_json(paths["previous"], minimal_previous_repeat())
            write_json(paths["summary"], minimal_previous_summary())
            write_json(paths["baseline"], {"passed": 60, "total": 60})
            write_json(paths["cases"], {"cases": []})

            report = build_report(
                product_repeat_path=paths["product"],
                algorithm_repeat_path=paths["algorithm"],
                previous_repeat_path=paths["previous"],
                previous_summary_path=paths["summary"],
                baseline_path=paths["baseline"],
                cases_path=paths["cases"],
            )

        algorithm_triage = next(item for item in report["case_triage"] if item["id"] == "risk_algorithm_bias_001")
        self.assertEqual(algorithm_triage["classification"], "final_evidence_identity_drift_reproduced")
        self.assertTrue(algorithm_triage["blocking"])
        self.assertEqual(report["summary"]["status"], "needs_evidence_stability_triage")
        self.assertIn("targeted_final_evidence_identity_drift_reproduced", report["summary"]["blockers"])

    def test_real_targeted_reports_capture_current_triage(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.15.1")
        self.assertEqual(report["schema_kind"], "post_rebuild_repeat_instability_triage")
        product = next(item for item in report["case_triage"] if item["id"] == "risk_tort_product_liability_001")
        algorithm = next(item for item in report["case_triage"] if item["id"] == "risk_algorithm_bias_001")
        self.assertEqual(product["classification"], "output_wording_variation_without_current_check_failure")
        self.assertFalse(product["blocking"])
        self.assertEqual(algorithm["classification"], "final_evidence_identity_drift_reproduced")
        self.assertTrue(algorithm["blocking"])
        self.assertEqual(report["summary"]["recommended_next_step"], "triage_final_evidence_identity_drift_before_runtime_change")

    def test_markdown_documents_boundary(self):
        report = build_report()
        markdown = render_markdown(report)

        self.assertIn("v0.4.15.1 Post-Rebuild Repeat Instability Triage", markdown)
        self.assertIn("saved-report triage", markdown)
        self.assertIn("not a runtime fix authorization", markdown)
        self.assertIn("does not modify hidden seeds", markdown)


if __name__ == "__main__":
    unittest.main()
