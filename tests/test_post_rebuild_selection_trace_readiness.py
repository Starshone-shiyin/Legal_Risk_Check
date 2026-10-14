import tempfile
import unittest
from pathlib import Path

from tools.build_post_rebuild_selection_trace_readiness import (
    DEFAULT_OUTPUT_PATH,
    DEFAULT_SUMMARY_PATH,
    GUARDRAILS,
    VERSION,
    build_report,
    main,
    render_markdown,
)


class PostRebuildSelectionTraceReadinessTest(unittest.TestCase):
    def test_default_paths_and_guardrails(self):
        self.assertEqual(VERSION, "0.4.15.3")
        self.assertEqual(DEFAULT_OUTPUT_PATH, Path("tests/post_rebuild_selection_trace_readiness_v0.4.15.3_report.json"))
        self.assertEqual(DEFAULT_SUMMARY_PATH, Path("docs/post_rebuild_selection_trace_readiness_v0.4.15.3.md"))
        self.assertTrue(GUARDRAILS["synthetic_documents_only"])
        self.assertEqual(GUARDRAILS["rag_query_call"], "disallowed")
        self.assertEqual(GUARDRAILS["qdrant_access"], "disallowed")
        self.assertEqual(GUARDRAILS["rerank_score_mutation"], "disallowed")
        self.assertEqual(GUARDRAILS["selector_behavior_mutation"], "disallowed")

    def test_report_confirms_trace_fields_and_behavior_boundary(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.15.3")
        self.assertEqual(report["summary"]["status"], "passed")
        self.assertFalse(report["summary"]["runtime_behavior_change"])
        self.assertEqual(report["synthetic_sample"]["selected_chunk_ids"], ["a24", "a48", "b20"])
        self.assertEqual(
            [item["chunk_id"] for item in report["synthetic_sample"]["selection_trace"]["not_selected"]],
            ["a24-sibling"],
        )
        self.assertIn("rerank_full_score_order", report["trace_fields"]["debug_info_fields"])
        self.assertIn("final_evidence_selection_trace", report["trace_fields"]["debug_info_fields"])

    def test_markdown_documents_observability_not_runtime_fix(self):
        markdown = render_markdown(build_report())

        self.assertIn("Selection Trace Readiness", markdown)
        self.assertIn("RAG 主链路可观测性补丁", markdown)
        self.assertIn("不是 rerank 调参", markdown)
        self.assertIn("rerank_full_score_order", markdown)
        self.assertIn("final_evidence_selection_trace", markdown)

    def test_main_writes_report_and_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "report.json"
            summary = Path(tmpdir) / "summary.md"
            import sys

            old_argv = sys.argv
            try:
                sys.argv = [
                    "build_post_rebuild_selection_trace_readiness.py",
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
            self.assertIn("Selection Trace Readiness", summary.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
