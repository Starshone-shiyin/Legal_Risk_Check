import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.run_ingestion_metadata_patch_local_dry_run import (
    DEFAULT_DRY_RUN_DESIGN_GATE_PATH,
    DEFAULT_DRY_RUN_DESIGN_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    SAMPLE_SCENARIOS,
    build_report,
    render_markdown,
    run_sample,
    simulate_boundary_metadata_patch,
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class IngestionMetadataPatchLocalDryRunTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(DEFAULT_DRY_RUN_DESIGN_PATH, legacy_report_path("ingestion_metadata_patch_dry_run_design_report.json"))
        self.assertEqual(
            DEFAULT_DRY_RUN_DESIGN_GATE_PATH,
            legacy_report_path("ingestion_metadata_patch_dry_run_design_gate_report.json"),
        )
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("ingestion_metadata_patch_local_dry_run_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/ingestion_metadata_patch_local_dry_run_v0.4.13.4.md"))

    def test_real_inputs_pass_local_dry_run(self):
        report = build_report()
        summary = report["summary"]

        self.assertEqual(report["version"], "0.4.13.4")
        self.assertEqual(report["schema_kind"], "ingestion_metadata_patch_local_dry_run")
        self.assertEqual(summary["status"], "passed")
        self.assertEqual(summary["sample_count"], 3)
        self.assertEqual(summary["forbidden_drift_count"], 0)
        self.assertEqual(summary["blocking_condition_count"], 0)
        self.assertEqual(summary["metadata_drift_count"], 0)
        self.assertEqual(summary["chunk_id_drift_count"], 0)
        self.assertEqual(summary["qdrant_point_id_drift_count"], 0)
        self.assertEqual(summary["allowed_next_step"], "ingestion_metadata_patch_local_dry_run_gate")
        self.assertFalse(summary["implementation_allowed"])
        self.assertFalse(summary["qdrant_write_allowed"])

    def test_sample_block_shapes_match_design(self):
        results = {sample["scenario_id"]: run_sample(sample) for sample in SAMPLE_SCENARIOS}

        self.assertEqual(results["single_paragraph_article"]["post_block_counts"], {"article": 1, "paragraph": 1, "item": 0})
        self.assertEqual(results["multi_paragraph_article"]["post_block_counts"], {"article": 1, "paragraph": 2, "item": 0})
        self.assertEqual(results["paragraph_with_items"]["post_block_counts"], {"article": 1, "paragraph": 0, "item": 2})
        self.assertTrue(all(not result["blockers"] for result in results.values()))

    def test_simulation_only_adds_boundary_metadata(self):
        sample = SAMPLE_SCENARIOS[0]
        from tools.run_ingestion_metadata_patch_local_dry_run import build_current_documents

        original_docs = build_current_documents(sample)
        patched_docs = simulate_boundary_metadata_patch(original_docs)

        self.assertEqual(original_docs[0].metadata["chunk_index"], 1)
        self.assertEqual(original_docs[0].metadata["chunk_count"], 1)
        self.assertEqual(patched_docs[0].metadata["chunk_index"], 1)
        self.assertEqual(patched_docs[0].metadata["chunk_count"], 1)
        self.assertEqual(patched_docs[1].metadata["chunk_index"], 1)
        self.assertEqual(patched_docs[1].metadata["chunk_count"], 1)
        self.assertEqual(original_docs[0].page_content, patched_docs[0].page_content)
        self.assertEqual(original_docs[0].metadata["citation"], patched_docs[0].metadata["citation"])

    def test_saved_pre_patch_report_keeps_original_drift_conclusion(self):
        saved = load_json(DEFAULT_OUTPUT_PATH)
        summary = saved["summary"]

        self.assertGreater(summary["metadata_drift_count"], 0)
        self.assertGreater(summary["chunk_id_drift_count"], 0)
        self.assertGreater(summary["qdrant_point_id_drift_count"], 0)

    def test_failed_prerequisite_blocks_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            gate = copy.deepcopy(load_json(DEFAULT_DRY_RUN_DESIGN_GATE_PATH))
            gate["summary"]["status"] = "failed"
            gate_path = tmp / "gate.json"
            write_json(gate_path, gate)

            report = build_report(DEFAULT_DRY_RUN_DESIGN_PATH, gate_path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("dry_run_design_gate_not_passed", report["blockers"])
        self.assertEqual(report["summary"]["allowed_next_step"], "blocked")

    def test_rows_keep_content_and_citation_stable(self):
        report = build_report()

        self.assertTrue(report["rows"])
        self.assertTrue(all(not row["content_changed"] for row in report["rows"]))
        self.assertTrue(all(not row["citation_changed"] for row in report["rows"]))
        self.assertTrue(all(not row["forbidden_drift"] for row in report["rows"]))
        self.assertTrue(all(not row["missing_post_boundary_metadata"] for row in report["rows"]))

    def test_markdown_keeps_local_only_boundary(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.13.4 Ingestion Metadata Patch Local Dry-Run", markdown)
        self.assertIn("does not patch ingestion", markdown)
        self.assertIn("Allowed next step", markdown)


if __name__ == "__main__":
    unittest.main()
