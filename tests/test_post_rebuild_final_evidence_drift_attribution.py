import tempfile
import unittest
from pathlib import Path

from tools.build_post_rebuild_final_evidence_drift_attribution import (
    DEFAULT_OUTPUT_PATH,
    DEFAULT_SUMMARY_PATH,
    DEFAULT_TARGETED_REPEAT_PATH,
    DRIFT_CANDIDATE_KEYS,
    GUARDRAILS,
    TARGET_CASE_ID,
    build_report,
    render_markdown,
)
from tools.build_post_rebuild_repeat_stability_summary import write_json


def candidate(key: str):
    source, article = key.split("|")
    return {
        "source": source,
        "law_name": source,
        "article_no": int(article),
        "section_no": "",
        "citation": f"[{source}第{article}条]",
        "similarity_score": 0.9,
    }


def case_row(selected_key: str, *, include_both_in_input: bool = True):
    inputs = [candidate("中华人民共和国个人信息保护法|24"), candidate("中华人民共和国个人信息保护法|48")]
    if include_both_in_input:
        inputs.extend(candidate(key) for key in DRIFT_CANDIDATE_KEYS)
    else:
        inputs.append(candidate(selected_key))
    final = [
        candidate("中华人民共和国个人信息保护法|24"),
        candidate("中华人民共和国个人信息保护法|48"),
        candidate(selected_key),
    ]
    return {
        "id": TARGET_CASE_ID,
        "passed": True,
        "retrieval_failure_stage": "PASS",
        "evidence": final,
        "debug_info": {
            "rerank_input_candidates": inputs,
            "final_candidates": final,
            "reranked_candidates": final,
            "sparse_candidates": inputs,
            "union_candidates": inputs,
            "anchor_candidates": inputs[:2],
            "dense_candidates": [],
        },
    }


def repeat_report(selected_keys, *, include_both_in_input=True):
    runs = []
    for index, selected_key in enumerate(selected_keys, start=1):
        runs.append({
            "run": index,
            "reports": [case_row(selected_key, include_both_in_input=include_both_in_input)],
        })
    return {"repeat": len(runs), "runs": runs}


class PostRebuildFinalEvidenceDriftAttributionTest(unittest.TestCase):
    def test_default_paths_and_guardrails(self):
        self.assertEqual(DEFAULT_TARGETED_REPEAT_PATH, Path("tests/targeted_repeat_algorithm_bias_v0.4.15.1_report.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, Path("tests/post_rebuild_final_evidence_drift_attribution_v0.4.15.2_report.json"))
        self.assertEqual(DEFAULT_SUMMARY_PATH, Path("docs/post_rebuild_final_evidence_drift_attribution_v0.4.15.2.md"))
        self.assertTrue(GUARDRAILS["saved_reports_only"])
        self.assertEqual(GUARDRAILS["rag_query_call"], "disallowed")
        self.assertEqual(GUARDRAILS["qdrant_access"], "disallowed")
        self.assertEqual(GUARDRAILS["anchor_mutation"], "disallowed")
        self.assertEqual(GUARDRAILS["eval_case_mutation"], "disallowed")

    def test_both_alternates_present_and_selection_changes_blocks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            targeted_path = root / "targeted.json"
            triage_path = root / "triage.json"
            cases_path = root / "cases.json"
            write_json(targeted_path, repeat_report(DRIFT_CANDIDATE_KEYS))
            write_json(triage_path, {"summary": {"status": "needs_evidence_stability_triage", "blockers": []}})
            write_json(cases_path, {"cases": []})

            report = build_report(targeted_path, triage_path, cases_path)

        self.assertEqual(report["summary"]["status"], "needs_selector_stability_design")
        self.assertEqual(
            report["summary"]["classification"],
            "rerank_top3_boundary_drift_after_core_evidence_locked",
        )
        self.assertIn("both_alternates_present_before_final_selection", report["summary"]["blockers"])
        self.assertFalse(report["summary"]["runtime_fix_authorized"])

    def test_no_selection_change_passes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            targeted_path = root / "targeted.json"
            triage_path = root / "triage.json"
            cases_path = root / "cases.json"
            write_json(targeted_path, repeat_report([DRIFT_CANDIDATE_KEYS[0], DRIFT_CANDIDATE_KEYS[0]]))
            write_json(triage_path, {"summary": {"status": "passed", "blockers": []}})
            write_json(cases_path, {"cases": []})

            report = build_report(targeted_path, triage_path, cases_path)

        self.assertEqual(report["summary"]["status"], "passed")
        self.assertEqual(report["summary"]["blockers"], [])

    def test_real_report_attributes_algorithm_bias_drift(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.15.2")
        self.assertEqual(report["target_case"]["id"], TARGET_CASE_ID)
        self.assertEqual(report["summary"]["status"], "needs_selector_stability_design")
        self.assertEqual(report["selected_alternate_summary"]["selected_alternate_changed"], True)
        self.assertIn("both_alternates_present_before_final_selection", report["summary"]["blockers"])
        self.assertEqual(report["attribution"]["stage_of_first_observed_divergence"], "reranked_candidates_or_final_candidates")
        self.assertFalse(report["attribution"]["raw_cross_encoder_full_order_available"])
        self.assertFalse(report["summary"]["runtime_fix_authorized"])

    def test_markdown_documents_boundary_and_limitation(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.15.2 最终证据漂移归因报告", markdown)
        self.assertIn("## 归因", markdown)
        self.assertIn("核心预期证据", markdown)
        self.assertIn("saved-report attribution", markdown)
        self.assertIn("不是运行时修复", markdown)
        self.assertIn("raw Cross-Encoder", markdown)


if __name__ == "__main__":
    unittest.main()
