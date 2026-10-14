import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.build_production_rebuild_post_rebuild_series_closeout import (
    DEFAULT_EXECUTION_PATH,
    DEFAULT_INITIAL_FULL_RAG_PATH,
    DEFAULT_INITIAL_FULL_RAG_SUMMARY_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_POST_VALIDATION_PATH,
    DEFAULT_QUALITY_SUMMARY_PATH,
    DEFAULT_RETENTION_DELTA_PATH,
    DEFAULT_RETENTION_FULL_RAG_PATH,
    DEFAULT_SMOKE_PATH,
    DEFAULT_SUMMARY_PATH,
    DEFAULT_TIGHTENED_FULL_RAG_PATH,
    DEFAULT_TIGHTENING_DOC_PATH,
    GUARDRAILS,
    build_report,
    render_markdown,
)


SOURCE_ORDER = [
    "execution",
    "post_validation",
    "smoke",
    "quality_summary",
    "initial_full_rag",
    "initial_full_rag_summary",
    "retention_full_rag",
    "retention_delta",
    "tightened_full_rag",
]

DEFAULT_PATHS = {
    "execution": DEFAULT_EXECUTION_PATH,
    "post_validation": DEFAULT_POST_VALIDATION_PATH,
    "smoke": DEFAULT_SMOKE_PATH,
    "quality_summary": DEFAULT_QUALITY_SUMMARY_PATH,
    "initial_full_rag": DEFAULT_INITIAL_FULL_RAG_PATH,
    "initial_full_rag_summary": DEFAULT_INITIAL_FULL_RAG_SUMMARY_PATH,
    "retention_full_rag": DEFAULT_RETENTION_FULL_RAG_PATH,
    "retention_delta": DEFAULT_RETENTION_DELTA_PATH,
    "tightened_full_rag": DEFAULT_TIGHTENED_FULL_RAG_PATH,
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def build_with_paths(paths: dict[str, Path], tightening_doc_path: Path = DEFAULT_TIGHTENING_DOC_PATH) -> dict:
    return build_report(
        execution_path=paths["execution"],
        post_validation_path=paths["post_validation"],
        smoke_path=paths["smoke"],
        quality_summary_path=paths["quality_summary"],
        initial_full_rag_path=paths["initial_full_rag"],
        initial_full_rag_summary_path=paths["initial_full_rag_summary"],
        retention_full_rag_path=paths["retention_full_rag"],
        retention_delta_path=paths["retention_delta"],
        tightened_full_rag_path=paths["tightened_full_rag"],
        tightening_doc_path=tightening_doc_path,
    )


class ProductionRebuildPostRebuildSeriesCloseoutTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(DEFAULT_OUTPUT_PATH, Path("tests/production_rebuild_post_rebuild_series_closeout_report.json"))
        self.assertEqual(DEFAULT_SUMMARY_PATH, Path("docs/production_rebuild_post_rebuild_series_closeout_v0.4.14.35.md"))
        self.assertEqual(DEFAULT_TIGHTENING_DOC_PATH, Path("docs/post_rebuild_alignment_retention_tightening_v0.4.14.34.md"))

    def test_real_inputs_close_series_without_running_new_gate(self):
        report = build_report()
        summary = report["summary"]

        self.assertEqual(report["version"], "0.4.14.35")
        self.assertEqual(report["schema_kind"], "production_rebuild_post_rebuild_series_closeout")
        self.assertEqual(summary["status"], "closed_for_next_real_rag_quality_task")
        self.assertEqual(summary["blockers"], [])
        self.assertTrue(summary["production_rebuild_succeeded"])
        self.assertTrue(summary["post_validation_passed"])
        self.assertEqual(summary["post_rebuild_smoke"], {"passed": 25, "total": 25})
        self.assertEqual(summary["initial_post_rebuild_full_rag"]["passed"], 58)
        self.assertEqual(summary["initial_post_rebuild_full_rag"]["total"], 60)
        self.assertEqual(summary["initial_post_rebuild_full_rag"]["regression_count"], 2)
        self.assertEqual(summary["tightened_full_rag"]["passed"], 60)
        self.assertEqual(summary["tightened_full_rag"]["total"], 60)
        self.assertEqual(summary["tightened_full_rag"]["retrieval_failure_stage_summary"], {"PASS": 60})
        self.assertEqual(summary["allowed_next_step"], "next_real_rag_quality_task_planning")
        self.assertEqual(report["inputs"]["execution"]["status"], "succeeded")

    def test_guardrails_disallow_runtime_and_sensitive_mutations(self):
        self.assertTrue(GUARDRAILS["saved_reports_only"])
        self.assertEqual(GUARDRAILS["qdrant_access"], "disallowed")
        self.assertEqual(GUARDRAILS["qdrant_write"], "disallowed")
        self.assertEqual(GUARDRAILS["rag_query_call"], "disallowed")
        self.assertEqual(GUARDRAILS["llm_access"], "disallowed")
        self.assertEqual(GUARDRAILS["runtime_mutation"], "disallowed")
        self.assertEqual(GUARDRAILS["anchor_mutation"], "disallowed")
        self.assertEqual(GUARDRAILS["prompt_mutation"], "disallowed")
        self.assertEqual(GUARDRAILS["rerank_mutation"], "disallowed")
        self.assertEqual(GUARDRAILS["eval_case_mutation"], "disallowed")
        self.assertEqual(GUARDRAILS["hidden_seed_mutation"], "disallowed")

    def test_missing_source_blocks_closeout(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = {key: Path(tmpdir) / f"{key}.json" for key in SOURCE_ORDER}
            for key in SOURCE_ORDER:
                if key != "tightened_full_rag":
                    write_json(paths[key], load_json(DEFAULT_PATHS[key]))

            report = build_with_paths(paths)

        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("tightened_full_rag_not_60_of_60", report["summary"]["blockers"])
        self.assertEqual(report["summary"]["allowed_next_step"], "resolve_closeout_blockers")

    def test_final_eval_drift_blocks_closeout(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = {key: Path(tmpdir) / f"{key}.json" for key in SOURCE_ORDER}
            for key in SOURCE_ORDER:
                payload = copy.deepcopy(load_json(DEFAULT_PATHS[key]))
                if key == "tightened_full_rag":
                    payload["passed"] = 59
                    payload["retrieval_failure_stage_summary"] = {"PASS": 59, "RERANK_MISS": 1}
                write_json(paths[key], payload)

            report = build_with_paths(paths)

        blockers = report["summary"]["blockers"]
        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("tightened_full_rag_not_60_of_60", blockers)
        self.assertIn("tightened_full_rag_stage_summary_not_all_pass", blockers)

    def test_initial_regression_lineage_is_required(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = {key: Path(tmpdir) / f"{key}.json" for key in SOURCE_ORDER}
            for key in SOURCE_ORDER:
                payload = copy.deepcopy(load_json(DEFAULT_PATHS[key]))
                if key == "initial_full_rag":
                    payload["passed"] = 60
                if key == "initial_full_rag_summary":
                    payload["rag_eval_summary"]["regression_count"] = 0
                write_json(paths[key], payload)

            report = build_with_paths(paths)

        blockers = report["summary"]["blockers"]
        self.assertIn("initial_post_rebuild_full_rag_expected_58_of_60_missing", blockers)
        self.assertIn("initial_post_rebuild_regression_count_not_2", blockers)

    def test_delta_removed_expected_evidence_blocks_closeout(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = {key: Path(tmpdir) / f"{key}.json" for key in SOURCE_ORDER}
            for key in SOURCE_ORDER:
                payload = copy.deepcopy(load_json(DEFAULT_PATHS[key]))
                if key == "retention_delta":
                    payload["evidence_delta_summary"]["removed_expected_evidence_count"] = 1
                write_json(paths[key], payload)

            report = build_with_paths(paths)

        self.assertIn("alignment_retention_delta_removed_expected_evidence", report["summary"]["blockers"])

    def test_markdown_documents_closeout_not_gate(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.14.35 Production Rebuild / Post-Rebuild Series Closeout", markdown)
        self.assertIn("只是 RAG 主链路生产重建后的收口归档", markdown)
        self.assertIn("不是新增 gate", markdown)
        self.assertIn("不连接 Qdrant", markdown)
        self.assertIn("不修改运行时代码", markdown)


if __name__ == "__main__":
    unittest.main()
