import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_metadata_chunking_fix_design import (
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_ROOT_CAUSE_PATH,
    build_report,
    render_markdown,
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class MetadataChunkingFixDesignTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(DEFAULT_ROOT_CAUSE_PATH, legacy_report_path("metadata_chunking_root_cause_report.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("metadata_chunking_fix_design_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/metadata_chunking_fix_design_v0.4.12.1.md"))

    def test_real_root_cause_builds_fix_design(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.12.1")
        self.assertEqual(report["schema_kind"], "metadata_chunking_fix_design")
        self.assertEqual(report["fix_design_gate"]["status"], "ready_for_fix_design_gate")
        self.assertEqual(report["summary"]["design_target"], "build_article_documents_chunk_boundary_metadata")
        self.assertTrue(report["summary"]["requires_rebuild"])
        self.assertEqual(report["summary"]["stable_id_impact"], "expected")
        self.assertIn("article", report["metadata_contract"]["affected_block_types"])
        self.assertIn("chunk_index", report["metadata_contract"]["required_new_fields"])
        self.assertFalse(report["fix_design_gate"]["implementation_allowed"])

    def test_stable_id_impact_requires_rebuild_and_blocks_payload_patch(self):
        report = build_report()
        stable_id_impact = report["stable_id_impact"]

        self.assertTrue(stable_id_impact["assign_stable_chunk_ids_includes_chunk_index"])
        self.assertTrue(stable_id_impact["chunk_id_change_expected"])
        self.assertTrue(stable_id_impact["qdrant_point_id_change_expected"])
        self.assertTrue(stable_id_impact["rebuild_required"])
        self.assertFalse(stable_id_impact["direct_payload_patch_allowed"])

    def test_root_cause_drift_blocks_design(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            root_cause = copy.deepcopy(load_json(DEFAULT_ROOT_CAUSE_PATH))
            root_cause["summary"]["primary_root_cause"] = "retrieval_main_flow_policy_issue"
            root_path = tmp / "root_cause.json"
            write_json(root_path, root_cause)

            report = build_report(root_path)

        self.assertEqual(report["fix_design_gate"]["status"], "blocked")
        self.assertIn("unexpected_primary_root_cause", report["fix_design_gate"]["blockers"])

    def test_markdown_keeps_design_only_boundary(self):
        markdown = render_markdown(build_report())
        self.assertIn("v0.4.12.1 Metadata/Chunking Fix Design", markdown)
        self.assertIn("does not patch ingestion", markdown)
        self.assertIn("Direct Qdrant payload patching remains disallowed", markdown)


if __name__ == "__main__":
    unittest.main()
