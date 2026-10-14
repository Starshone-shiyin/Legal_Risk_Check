import tempfile
import unittest
from pathlib import Path

from tools.build_post_rebuild_selection_trace_attribution import (
    DEFAULT_OUTPUT_PATH,
    DEFAULT_SUMMARY_PATH,
    DEFAULT_TRACE_REPEAT_PATH,
    DRIFT_CANDIDATE_KEYS,
    GUARDRAILS,
    TARGET_CASE_ID,
    build_report,
    main,
    render_markdown,
    write_json,
)


def trace_item(key: str, *, rerank_rank: int, final_rank: int | None = None, score: float = 0.9):
    source, article = key.split("|")
    item = {
        "source": source,
        "law_name": source,
        "article_no": int(article),
        "score": score,
        "input_rank": rerank_rank,
        "rerank_rank": rerank_rank,
        "chunk_id": f"{source}-{article}",
    }
    if final_rank is not None:
        item["final_rank"] = final_rank
    return item


def synthetic_case(selected_key: str, other_key: str):
    core = [
        "中华人民共和国个人信息保护法|24",
        "中华人民共和国个人信息保护法|48",
    ]
    selected_trace = [
        trace_item(core[0], rerank_rank=1, final_rank=1, score=0.98),
        trace_item(core[1], rerank_rank=2, final_rank=2, score=0.91),
        trace_item(selected_key, rerank_rank=6, final_rank=3, score=0.90),
    ]
    not_selected_trace = [trace_item(other_key, rerank_rank=7, score=0.89)]
    return {
        "id": TARGET_CASE_ID,
        "passed": True,
        "retrieval_failure_stage": "PASS",
        "evidence": selected_trace,
        "debug_info": {
            "rerank_full_score_order": selected_trace + not_selected_trace,
            "final_evidence_selection_trace": {
                "mode": "cross_encoder",
                "selected": selected_trace,
                "not_selected": not_selected_trace,
            },
        },
    }


def synthetic_repeat_report():
    first, second = DRIFT_CANDIDATE_KEYS
    return {
        "repeat": 2,
        "runs": [
            {"run": 1, "reports": [synthetic_case(first, second)]},
            {"run": 2, "reports": [synthetic_case(second, first)]},
        ],
    }


class PostRebuildSelectionTraceAttributionTest(unittest.TestCase):
    def test_default_paths_and_guardrails(self):
        self.assertEqual(DEFAULT_TRACE_REPEAT_PATH, Path("tests/targeted_repeat_algorithm_bias_trace_v0.4.15.4_report.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, Path("tests/post_rebuild_selection_trace_attribution_v0.4.15.4_report.json"))
        self.assertEqual(DEFAULT_SUMMARY_PATH, Path("docs/post_rebuild_selection_trace_attribution_v0.4.15.4.md"))
        self.assertTrue(GUARDRAILS["saved_reports_only"])
        self.assertEqual(GUARDRAILS["rag_query_call"], "disallowed")
        self.assertEqual(GUARDRAILS["qdrant_access"], "disallowed")
        self.assertEqual(GUARDRAILS["rerank_score_mutation"], "disallowed")
        self.assertEqual(GUARDRAILS["selector_behavior_mutation"], "disallowed")

    def test_synthetic_report_attributes_drift_to_full_order_boundary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "repeat.json"
            write_json(path, synthetic_repeat_report())

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "needs_near_tie_stability_design")
        self.assertEqual(
            report["summary"]["classification"],
            "raw_rerank_order_boundary_drift_not_selector_replacement",
        )
        self.assertTrue(report["summary"]["all_selected_alternates_match_trace"])
        self.assertTrue(report["summary"]["selected_alternate_is_earlier_full_order_candidate"])
        self.assertFalse(report["summary"]["runtime_fix_authorized"])

    def test_real_trace_report_attributes_algorithm_bias_drift(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.15.4")
        self.assertEqual(report["target_case"]["id"], TARGET_CASE_ID)
        self.assertEqual(report["summary"]["status"], "needs_near_tie_stability_design")
        self.assertEqual(report["summary"]["selected_alternate_counts"], {
            "中华人民共和国个人信息保护法|56": 2,
            "中华人民共和国网络安全法|20": 3,
        })
        self.assertTrue(report["summary"]["all_selected_alternates_match_trace"])
        self.assertTrue(report["summary"]["selected_alternate_is_earlier_full_order_candidate"])

    def test_markdown_documents_trace_boundary(self):
        markdown = render_markdown(build_report())

        self.assertIn("Selection Trace Attribution", markdown)
        self.assertIn("raw rerank stable order", markdown)
        self.assertIn("不是 selector replacement", markdown)
        self.assertIn("不修改 hidden seed", markdown)

    def test_main_writes_report_and_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "report.json"
            summary = Path(tmpdir) / "summary.md"
            import sys

            old_argv = sys.argv
            try:
                sys.argv = [
                    "build_post_rebuild_selection_trace_attribution.py",
                    "--trace-repeat",
                    str(DEFAULT_TRACE_REPEAT_PATH),
                    "--output",
                    str(output),
                    "--summary",
                    str(summary),
                ]
                exit_code = main()
            finally:
                sys.argv = old_argv

            self.assertEqual(exit_code, 0)
            self.assertTrue(output.exists())
            self.assertTrue(summary.exists())


if __name__ == "__main__":
    unittest.main()
