import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_metadata_chunking_root_cause_report import (
    DEFAULT_CLOSEOUT_PATH,
    DEFAULT_INGESTION_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_QDRANT_INTEGRITY_PATH,
    DEFAULT_SNAPSHOT_PATH,
    build_report,
    render_markdown,
    static_ingestion_signals,
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class MetadataChunkingRootCauseReportTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(DEFAULT_CLOSEOUT_PATH, legacy_report_path("evidence_metadata_snapshot_series_closeout_report.json"))
        self.assertEqual(DEFAULT_SNAPSHOT_PATH, legacy_report_path("evidence_metadata_snapshot_report.json"))
        self.assertEqual(DEFAULT_QDRANT_INTEGRITY_PATH, legacy_report_path("qdrant_index_integrity_report.json"))
        self.assertEqual(DEFAULT_INGESTION_PATH, Path("src/rag/ingestion.py"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("metadata_chunking_root_cause_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/metadata_chunking_root_cause_v0.4.12.0.md"))

    def test_real_sources_identify_article_chunk_boundary_root_cause(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.12.0")
        self.assertEqual(report["schema_kind"], "metadata_chunking_root_cause_report")
        self.assertEqual(report["root_cause_gate"]["status"], "ready_for_metadata_chunking_fix_design")
        self.assertEqual(report["summary"]["primary_root_cause"], "ingestion_article_chunks_missing_boundary_metadata")
        self.assertEqual(report["summary"]["confidence"], "medium")
        self.assertEqual(report["summary"]["chunk_boundary_ambiguity_count"], 19)
        self.assertTrue(report["summary"]["qdrant_integrity_passed"])
        self.assertFalse(report["summary"]["source_count_mismatch"])
        self.assertTrue(report["static_ingestion_signals"]["standard_section_assigns_chunk_index"])
        self.assertTrue(report["static_ingestion_signals"]["article_function_assigns_chunk_index"])
        self.assertFalse(report["root_cause_gate"]["implementation_allowed"])

    def test_static_ingestion_signals_detect_article_boundary_absence(self):
        source = """
def build_standard_section_documents():
    metadata = {"chunk_index": index, "chunk_count": len(chunks)}

def build_article_documents():
    metadata = {"block_type": "article"}
    metadata = {"block_type": "paragraph"}
    metadata = {"block_type": "item"}
"""
        signals = static_ingestion_signals(source)

        self.assertTrue(signals["standard_section_assigns_chunk_index"])
        self.assertTrue(signals["standard_section_assigns_chunk_count"])
        self.assertTrue(signals["article_function_present"])
        self.assertFalse(signals["article_function_assigns_chunk_index"])
        self.assertIn("paragraph", signals["article_block_types"])

    def test_current_source_detects_article_boundary_presence_after_patch(self):
        source = DEFAULT_INGESTION_PATH.read_text(encoding="utf-8-sig")
        signals = static_ingestion_signals(source)

        self.assertTrue(signals["article_function_assigns_chunk_index"])
        self.assertTrue(signals["article_function_assigns_chunk_count"])

    def test_saved_root_cause_report_keeps_original_pre_patch_conclusion(self):
        saved = load_json(DEFAULT_OUTPUT_PATH)

        self.assertEqual(saved["summary"]["confidence"], "high")
        self.assertFalse(saved["static_ingestion_signals"]["article_function_assigns_chunk_index"])

    def test_closeout_drift_blocks_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            closeout = copy.deepcopy(load_json(DEFAULT_CLOSEOUT_PATH))
            closeout["version"] = "0.4.11.2"
            closeout_path = tmp / "closeout.json"
            write_json(closeout_path, closeout)

            report = build_report(closeout_path, DEFAULT_SNAPSHOT_PATH, DEFAULT_QDRANT_INTEGRITY_PATH, DEFAULT_INGESTION_PATH)

        self.assertEqual(report["root_cause_gate"]["status"], "blocked")
        self.assertIn("closeout_version_mismatch", report["root_cause_gate"]["blockers"])

    def test_markdown_keeps_no_fix_boundary(self):
        markdown = render_markdown(build_report())
        self.assertIn("v0.4.12.0 Metadata/Chunking Root-Cause Report", markdown)
        self.assertIn("does not authorize a fix", markdown)
        self.assertIn("Next step is fix design", markdown)


if __name__ == "__main__":
    unittest.main()
