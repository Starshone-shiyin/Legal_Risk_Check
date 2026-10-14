import copy
import tempfile
import unittest
from pathlib import Path

from tools.build_post_rebuild_repeat_stability_summary import (
    DEFAULT_BASELINE_REPORT_PATH,
    DEFAULT_CASES_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_REPEAT_REPORT_PATH,
    DEFAULT_SUMMARY_PATH,
    GUARDRAILS,
    build_report,
    render_markdown,
    write_json,
)


def case_row(case_id: str, *, passed: bool = True, failed_checks=None, labels=None, evidence_article=1, answer="答案包含赔偿"):
    failed_checks = failed_checks or []
    labels = labels or ["PURE_LLM_PASS"]
    checks = [
        {"name": "expected_evidence", "passed": True, "message": "ok"},
        {"name": "expected_answer_keywords", "passed": "expected_answer_keywords" not in failed_checks, "message": "ok"},
    ]
    return {
        "id": case_id,
        "category": "unit",
        "retrieval_failure_stage": "PASS",
        "contribution_labels": labels,
        "passed": passed,
        "question": "问题",
        "checks": checks,
        "answer": answer,
        "evidence": [
            {
                "rank": 1,
                "source": "中华人民共和国民法典",
                "law_name": "中华人民共和国民法典",
                "article_no": evidence_article,
                "section_no": "",
                "citation": f"[《中华人民共和国民法典》第{evidence_article}条]",
            }
        ],
    }


def run_report(run_no: int, rows):
    return {
        "run": run_no,
        "total": len(rows),
        "passed": sum(1 for row in rows if row["passed"]),
        "failed": sum(1 for row in rows if not row["passed"]),
        "retrieval_failure_stage_summary": {"PASS": len(rows)},
        "contribution_summary": {
            "label_counts": {"PURE_LLM_PASS": len(rows)},
            "dense_fallback_passed": 0,
        },
        "reports": rows,
    }


def repeat_report(runs, unstable=None, label_variation=None):
    return {
        "repeat": len(runs),
        "stability_summary": {
            "runs": len(runs),
            "all_runs_full_pass": all(run["passed"] == run["total"] for run in runs),
            "pass_counts": [run["passed"] for run in runs],
            "total_counts": [run["total"] for run in runs],
            "unstable_cases": unstable or [],
            "label_variation_cases": label_variation or [],
        },
        "runs": runs,
    }


class PostRebuildRepeatStabilitySummaryTest(unittest.TestCase):
    def test_default_paths_and_guardrails(self):
        self.assertEqual(DEFAULT_REPEAT_REPORT_PATH, Path("tests/post_rebuild_repeat_full_rag_eval_v0.4.15.0_report.json"))
        self.assertEqual(DEFAULT_BASELINE_REPORT_PATH, Path("tests/post_rebuild_rag_eval_after_alignment_retention_tightened_report.json"))
        self.assertEqual(DEFAULT_CASES_PATH, Path("tests/rag_eval_cases.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, Path("tests/post_rebuild_repeat_stability_summary_v0.4.15.0_report.json"))
        self.assertEqual(DEFAULT_SUMMARY_PATH, Path("docs/post_rebuild_repeat_stability_summary_v0.4.15.0.md"))
        self.assertTrue(GUARDRAILS["saved_reports_only"])
        self.assertEqual(GUARDRAILS["rag_query_call"], "disallowed")
        self.assertEqual(GUARDRAILS["qdrant_access"], "disallowed")
        self.assertEqual(GUARDRAILS["anchor_mutation"], "disallowed")
        self.assertEqual(GUARDRAILS["rerank_mutation"], "disallowed")
        self.assertEqual(GUARDRAILS["eval_case_mutation"], "disallowed")

    def test_clean_repeat_passes_with_label_variation_as_observation(self):
        baseline = run_report(1, [case_row("a"), case_row("b")])
        runs = [
            run_report(1, [case_row("a"), case_row("b", labels=["ANCHOR_PASS"])]),
            run_report(2, [case_row("a"), case_row("b", labels=["PURE_LLM_PASS"])]),
            run_report(3, [case_row("a"), case_row("b", labels=["PURE_LLM_PASS"])]),
        ]
        repeat = repeat_report(
            runs,
            label_variation=[{"id": "b", "contribution_labels": [["ANCHOR_PASS"], ["PURE_LLM_PASS"], ["PURE_LLM_PASS"]]}],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            repeat_path = root / "repeat.json"
            baseline_path = root / "baseline.json"
            write_json(repeat_path, repeat)
            write_json(baseline_path, baseline)
            report = build_report(repeat_path, baseline_path, root / "missing_cases.json")

        self.assertEqual(report["summary"]["status"], "passed")
        self.assertEqual(report["summary"]["blockers"], [])
        self.assertEqual(report["repeat_summary"]["label_variation_case_count"], 1)
        self.assertEqual(report["label_variation_cases"][0]["blocking"], False)

    def test_repeat_59_of_60_style_failure_is_needs_triage(self):
        baseline = run_report(1, [case_row("risk")])
        runs = [
            run_report(1, [case_row("risk")]),
            run_report(2, [case_row("risk")]),
            run_report(3, [case_row("risk", passed=False, failed_checks=["expected_answer_keywords"], labels=[], answer="答案未写目标词")]),
        ]
        repeat = repeat_report(
            runs,
            unstable=[{
                "id": "risk",
                "passed": [True, True, False],
                "retrieval_failure_stage": ["PASS", "PASS", "PASS"],
                "failed_checks": [[], [], ["expected_answer_keywords"]],
                "contribution_labels": [["PURE_LLM_PASS"], ["PURE_LLM_PASS"], []],
            }],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            repeat_path = root / "repeat.json"
            baseline_path = root / "baseline.json"
            write_json(repeat_path, repeat)
            write_json(baseline_path, baseline)
            report = build_report(repeat_path, baseline_path, root / "missing_cases.json")

        self.assertEqual(report["summary"]["status"], "needs_triage")
        self.assertIn("repeat_not_all_runs_full_pass", report["summary"]["blockers"])
        self.assertIn("repeat_unstable_cases_present", report["summary"]["blockers"])
        self.assertIn("baseline_pass_status_drift", report["summary"]["blockers"])
        self.assertIn("baseline_failed_check_drift", report["summary"]["blockers"])
        self.assertEqual(report["unstable_cases"][0]["classification"], "answer_or_check_instability_with_stable_retrieval")
        self.assertEqual(report["high_risk_manual_review_list"][0]["id"], "risk")

    def test_evidence_identity_drift_blocks_even_when_passed(self):
        baseline = run_report(1, [case_row("a", evidence_article=1)])
        runs = [
            run_report(1, [case_row("a", evidence_article=1)]),
            run_report(2, [case_row("a", evidence_article=2)]),
            run_report(3, [case_row("a", evidence_article=1)]),
        ]
        repeat = repeat_report(runs)

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            repeat_path = root / "repeat.json"
            baseline_path = root / "baseline.json"
            write_json(repeat_path, repeat)
            write_json(baseline_path, baseline)
            report = build_report(repeat_path, baseline_path, root / "missing_cases.json")

        self.assertEqual(report["summary"]["status"], "needs_triage")
        self.assertIn("repeat_evidence_identity_drift", report["summary"]["blockers"])
        self.assertEqual(report["evidence_identity_drift_summary"]["changed_case_count"], 1)

    def test_citation_display_drift_does_not_count_as_evidence_identity_drift(self):
        row_a = case_row("a", evidence_article=58)
        row_b = case_row("a", evidence_article=58)
        row_b["evidence"][0]["citation"] = "[《中华人民共和国民法典》第五十八条第一款]"
        baseline = run_report(1, [row_a])
        repeat = repeat_report([
            run_report(1, [row_a]),
            run_report(2, [row_b]),
            run_report(3, [copy.deepcopy(row_a)]),
        ])

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            repeat_path = root / "repeat.json"
            baseline_path = root / "baseline.json"
            write_json(repeat_path, repeat)
            write_json(baseline_path, baseline)
            report = build_report(repeat_path, baseline_path, root / "missing_cases.json")

        self.assertEqual(report["summary"]["status"], "passed")
        self.assertEqual(report["evidence_identity_drift_summary"]["changed_case_count"], 0)

    def test_case_set_and_dense_fallback_drift_block(self):
        baseline = run_report(1, [case_row("a"), case_row("missing")])
        run = run_report(1, [case_row("a"), case_row("new")])
        run["contribution_summary"]["dense_fallback_passed"] = 1
        repeat = repeat_report([run, copy.deepcopy(run), copy.deepcopy(run)])

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            repeat_path = root / "repeat.json"
            baseline_path = root / "baseline.json"
            write_json(repeat_path, repeat)
            write_json(baseline_path, baseline)
            report = build_report(repeat_path, baseline_path, root / "missing_cases.json")

        self.assertIn("baseline_case_set_drift", report["summary"]["blockers"])
        self.assertIn("dense_fallback_used_in_repeat", report["summary"]["blockers"])
        self.assertEqual(report["baseline_comparison"]["missing_cases"], ["missing"])
        self.assertEqual(report["baseline_comparison"]["new_cases"], ["new"])

    def test_real_repeat_report_captures_current_post_rebuild_instability(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.15.0")
        self.assertEqual(report["schema_kind"], "post_rebuild_repeat_stability_summary")
        self.assertEqual(report["repeat_summary"]["pass_counts"], [60, 60, 59])
        self.assertEqual(report["repeat_summary"]["unstable_case_count"], 1)
        self.assertEqual(report["unstable_cases"][0]["id"], "risk_tort_product_liability_001")
        self.assertEqual(report["unstable_cases"][0]["classification"], "answer_or_check_instability_with_stable_retrieval")
        self.assertIn("repeat_not_all_runs_full_pass", report["summary"]["blockers"])
        self.assertIn("triage_repeat_output_instability_before_runtime_change", report["summary"]["recommended_next_step"])

    def test_markdown_documents_boundary(self):
        report = build_report()
        markdown = render_markdown(report)

        self.assertIn("v0.4.15.0 Post-Rebuild Repeat Stability Summary", markdown)
        self.assertIn("RAG 质量稳定性诊断", markdown)
        self.assertIn("不是样本修补工具", markdown)
        self.assertIn("不修改 anchor", markdown)


if __name__ == "__main__":
    unittest.main()
