import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_ingestion_metadata_patch_contract import (
    DEFAULT_FIX_DESIGN_PATH,
    DEFAULT_INGESTION_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_SERIES_CLOSEOUT_PATH,
    build_report,
    render_markdown,
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class IngestionMetadataPatchContractTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(DEFAULT_SERIES_CLOSEOUT_PATH, legacy_report_path("metadata_chunking_series_closeout_report.json"))
        self.assertEqual(DEFAULT_FIX_DESIGN_PATH, legacy_report_path("metadata_chunking_fix_design_report.json"))
        self.assertEqual(DEFAULT_INGESTION_PATH, Path("src/rag/ingestion.py"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("ingestion_metadata_patch_contract_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/ingestion_metadata_patch_contract_v0.4.13.0.md"))

    def test_real_sources_build_contract(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.13.0")
        self.assertEqual(report["schema_kind"], "ingestion_metadata_patch_contract")
        self.assertEqual(report["contract_gate"]["status"], "blocked")
        self.assertIn("article_boundary_metadata_already_present", report["contract_gate"]["blockers"])
        self.assertEqual(report["summary"]["patch_target"], "src/rag/ingestion.py::build_article_documents")
        self.assertTrue(report["summary"]["requires_rebuild"])
        self.assertFalse(report["contract_gate"]["implementation_allowed"])
        self.assertEqual(report["patch_contract"]["allowed_files"], ["src/rag/ingestion.py"])
        self.assertEqual(report["patch_contract"]["allowed_function"], "build_article_documents")
        self.assertIn("src/rag/retriever.py", report["patch_contract"]["forbidden_files"])

    def test_saved_contract_report_keeps_original_pre_patch_gate(self):
        saved = load_json(DEFAULT_OUTPUT_PATH)

        self.assertEqual(saved["contract_gate"]["status"], "ready_for_ingestion_metadata_patch_contract_gate")
        self.assertEqual(saved["contract_gate"]["blockers"], [])

    def test_contract_defines_parent_and_child_chunk_rules(self):
        contract = build_report()["patch_contract"]

        self.assertEqual(contract["parent_article_rule"]["chunk_index"], 1)
        self.assertEqual(contract["parent_article_rule"]["chunk_count"], 1)
        self.assertFalse(contract["parent_article_rule"]["content_change_allowed"])
        self.assertEqual(contract["child_chunk_rule"]["chunk_index"], "1-based emission order within article_parts")
        self.assertEqual(contract["child_chunk_rule"]["chunk_count"], "len(article_parts)")
        self.assertFalse(contract["child_chunk_rule"]["content_change_allowed"])

    def test_closeout_drift_blocks_contract(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            closeout = copy.deepcopy(load_json(DEFAULT_SERIES_CLOSEOUT_PATH))
            closeout["summary"]["status"] = "blocked"
            closeout_path = tmp / "closeout.json"
            write_json(closeout_path, closeout)

            report = build_report(closeout_path, DEFAULT_FIX_DESIGN_PATH, DEFAULT_INGESTION_PATH)

        self.assertEqual(report["contract_gate"]["status"], "blocked")
        self.assertIn("series_closeout_not_completed", report["contract_gate"]["blockers"])

    def test_markdown_keeps_contract_only_boundary(self):
        markdown = render_markdown(build_report())
        self.assertIn("v0.4.13.0 Ingestion Metadata Patch Contract", markdown)
        self.assertIn("does not patch ingestion", markdown)
        self.assertIn("Standard section behavior must remain unchanged", markdown)


if __name__ == "__main__":
    unittest.main()
