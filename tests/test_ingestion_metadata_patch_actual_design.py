import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_ingestion_metadata_patch_actual_design import (
    DEFAULT_CONTRACT_PATH,
    DEFAULT_LOCAL_DRY_RUN_GATE_PATH,
    DEFAULT_LOCAL_DRY_RUN_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    build_report,
    render_markdown,
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class IngestionMetadataPatchActualDesignTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(DEFAULT_CONTRACT_PATH, legacy_report_path("ingestion_metadata_patch_contract_report.json"))
        self.assertEqual(DEFAULT_LOCAL_DRY_RUN_PATH, legacy_report_path("ingestion_metadata_patch_local_dry_run_report.json"))
        self.assertEqual(
            DEFAULT_LOCAL_DRY_RUN_GATE_PATH,
            legacy_report_path("ingestion_metadata_patch_local_dry_run_gate_report.json"),
        )
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("ingestion_metadata_patch_actual_design_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/ingestion_metadata_patch_actual_design_v0.4.13.6.md"))

    def test_real_inputs_build_design(self):
        report = build_report()
        summary = report["summary"]

        self.assertEqual(report["version"], "0.4.13.6")
        self.assertEqual(report["schema_kind"], "ingestion_metadata_patch_actual_design")
        self.assertEqual(summary["status"], "ready_for_actual_ingestion_metadata_patch_design_gate")
        self.assertEqual(summary["allowed_next_step"], "actual_ingestion_metadata_patch_design_gate")
        self.assertEqual(summary["patch_target"], "src/rag/ingestion.py::build_article_documents")
        self.assertFalse(summary["implementation_allowed"])
        self.assertFalse(summary["qdrant_write_allowed"])
        self.assertFalse(summary["rebuild_allowed"])

    def test_patch_design_keeps_single_file_and_function_scope(self):
        design = build_report()["patch_design"]

        self.assertEqual(design["allowed_file"], "src/rag/ingestion.py")
        self.assertEqual(design["allowed_function"], "build_article_documents")
        self.assertIn("src/rag/retriever.py", design["forbidden_files"])
        self.assertIn("assign_stable_chunk_ids", design["forbidden_functions"])
        self.assertEqual(design["parent_article_rule"]["chunk_index"], 1)
        self.assertEqual(design["parent_article_rule"]["chunk_count"], 1)
        self.assertEqual(design["child_chunk_rule"]["chunk_count"], "len(article_parts)")

    def test_post_patch_plan_does_not_reuse_pre_patch_drift_as_expectation(self):
        plan = build_report()["post_patch_validation_plan"]

        self.assertTrue(any("pre-patch drift runner" in item for item in plan))
        self.assertTrue(any("direct metadata assertions" in item for item in plan))

    def test_gate_failure_blocks_design(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            gate = copy.deepcopy(load_json(DEFAULT_LOCAL_DRY_RUN_GATE_PATH))
            gate["summary"]["status"] = "failed"
            gate_path = tmp / "gate.json"
            write_json(gate_path, gate)

            report = build_report(DEFAULT_CONTRACT_PATH, DEFAULT_LOCAL_DRY_RUN_PATH, gate_path)

        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("local_dry_run_gate_not_passed", report["summary"]["blockers"])

    def test_unexpected_next_step_blocks_design(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            gate = copy.deepcopy(load_json(DEFAULT_LOCAL_DRY_RUN_GATE_PATH))
            gate["summary"]["allowed_next_step"] = "patch_now"
            gate_path = tmp / "gate.json"
            write_json(gate_path, gate)

            report = build_report(DEFAULT_CONTRACT_PATH, DEFAULT_LOCAL_DRY_RUN_PATH, gate_path)

        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("unexpected_gate_next_step", report["summary"]["blockers"])

    def test_markdown_keeps_design_only_boundary(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.13.6 Ingestion Metadata Patch Actual Design", markdown)
        self.assertIn("does not modify ingestion", markdown)
        self.assertIn("Still Not Allowed", markdown)


if __name__ == "__main__":
    unittest.main()
