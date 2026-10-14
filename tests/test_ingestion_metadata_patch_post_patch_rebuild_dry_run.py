import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.run_ingestion_metadata_patch_post_patch_rebuild_dry_run import (
    DEFAULT_DESIGN_GATE_PATH,
    DEFAULT_DESIGN_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_SOURCE_PATCH_REPORT_PATH,
    build_report,
    compare_documents,
    render_markdown,
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class IngestionMetadataPatchPostPatchRebuildDryRunTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(
            DEFAULT_SOURCE_PATCH_REPORT_PATH,
            legacy_report_path("ingestion_metadata_source_patch_report.json"),
        )
        self.assertEqual(
            DEFAULT_DESIGN_PATH,
            legacy_report_path("ingestion_metadata_patch_post_patch_rebuild_dry_run_design_report.json"),
        )
        self.assertEqual(
            DEFAULT_DESIGN_GATE_PATH,
            legacy_report_path("ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("ingestion_metadata_patch_post_patch_rebuild_dry_run_report.json"),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/ingestion_metadata_patch_post_patch_rebuild_dry_run_v0.4.13.11.md"),
        )

    def test_real_inputs_build_passed_runner_report(self):
        report = build_report()
        summary = report["summary"]

        self.assertEqual(report["version"], "0.4.13.11")
        self.assertEqual(report["schema_kind"], "ingestion_metadata_patch_post_patch_rebuild_dry_run")
        self.assertEqual(summary["status"], "passed")
        self.assertEqual(summary["sample_count"], 3)
        self.assertGreaterEqual(summary["row_count"], 8)
        self.assertEqual(summary["metadata_presence_rows"], summary["row_count"])
        self.assertEqual(summary["expected_id_drift_rows"], summary["row_count"])
        self.assertEqual(summary["forbidden_drift_count"], 0)
        self.assertEqual(summary["blocking_condition_count"], 0)
        self.assertEqual(summary["allowed_next_step"], "post_patch_rebuild_dry_run_runner_gate")
        self.assertFalse(summary["qdrant_write_allowed"])
        self.assertFalse(summary["rebuild_allowed"])
        self.assertEqual(summary["full_eval"], "not_run")

    def test_samples_cover_required_shapes_and_rows(self):
        report = build_report()
        shapes = {sample["shape"] for sample in report["sample_results"]}
        rows = report["rows"]

        self.assertEqual(
            shapes,
            {
                "single paragraph article",
                "paragraph plus item article",
                "multi-paragraph article",
            },
        )
        self.assertTrue(all(row["chunk_index"] is not None for row in rows))
        self.assertTrue(all(row["chunk_count"] is not None for row in rows))
        self.assertTrue(all(row["chunk_id_drift"] for row in rows))
        self.assertTrue(all(row["qdrant_point_id_drift"] for row in rows))
        self.assertTrue(all(row["content_stable"] for row in rows))
        self.assertTrue(all(row["citation_stable"] for row in rows))
        self.assertTrue(all(row["block_metadata_stable"] for row in rows))
        self.assertTrue(all(not row["blocking_conditions"] for row in rows))

    def test_design_gate_failure_blocks_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            source = tmp / "source.json"
            design = tmp / "design.json"
            gate = tmp / "gate.json"
            source_payload = load_json(DEFAULT_SOURCE_PATCH_REPORT_PATH)
            design_payload = load_json(DEFAULT_DESIGN_PATH)
            gate_payload = copy.deepcopy(load_json(DEFAULT_DESIGN_GATE_PATH))
            gate_payload["summary"]["status"] = "failed"
            write_json(source, source_payload)
            write_json(design, design_payload)
            write_json(gate, gate_payload)

            report = build_report(source, design, gate)

        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("design_gate_report_not_passed", report["blockers"])

    def test_source_patch_next_step_drift_blocks_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            source = tmp / "source.json"
            design = tmp / "design.json"
            gate = tmp / "gate.json"
            source_payload = copy.deepcopy(load_json(DEFAULT_SOURCE_PATCH_REPORT_PATH))
            source_payload["summary"]["allowed_next_step"] = "rebuild_now"
            write_json(source, source_payload)
            write_json(design, load_json(DEFAULT_DESIGN_PATH))
            write_json(gate, load_json(DEFAULT_DESIGN_GATE_PATH))

            report = build_report(source, design, gate)

        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("source_patch_report_next_step_mismatch", report["blockers"])

    def test_compare_documents_blocks_forbidden_content_drift(self):
        class FakeDoc:
            def __init__(self, content, metadata):
                self.page_content = content
                self.metadata = metadata

        before = FakeDoc(
            "before",
            {
                "block_type": "paragraph",
                "citation": "c",
                "paragraph_no": 1,
                "item_no": None,
                "item_label": "",
                "parent_article_id": "p",
                "chunk_id": "old",
                "qdrant_point_id": 1,
            },
        )
        after = FakeDoc(
            "after",
            {
                "block_type": "paragraph",
                "citation": "c",
                "paragraph_no": 1,
                "item_no": None,
                "item_label": "",
                "parent_article_id": "p",
                "chunk_index": 1,
                "chunk_count": 1,
                "chunk_id": "new",
                "qdrant_point_id": 2,
            },
        )

        rows, blockers = compare_documents("sample", [before], [after])

        self.assertIn("forbidden_content_or_citation_drift", rows[0]["blocking_conditions"])
        self.assertIn("sample:1:forbidden_content_or_citation_drift", blockers)

    def test_markdown_documents_non_runtime_boundaries(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.13.11 Post-Patch Rebuild Dry-Run Runner", markdown)
        self.assertIn("不写 Qdrant", markdown)
        self.assertIn("不 rebuild collection", markdown)
        self.assertIn("不调用 RAG/embedding/LLM", markdown)
        self.assertIn("不运行 full eval", markdown)


if __name__ == "__main__":
    unittest.main()
