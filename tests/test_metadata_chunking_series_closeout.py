import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_metadata_chunking_series_closeout import (
    DEFAULT_FIX_DESIGN_GATE_PATH,
    DEFAULT_FIX_DESIGN_PATH,
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


class MetadataChunkingSeriesCloseoutTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(DEFAULT_ROOT_CAUSE_PATH, legacy_report_path("metadata_chunking_root_cause_report.json"))
        self.assertEqual(DEFAULT_FIX_DESIGN_PATH, legacy_report_path("metadata_chunking_fix_design_report.json"))
        self.assertEqual(DEFAULT_FIX_DESIGN_GATE_PATH, legacy_report_path("metadata_chunking_fix_design_gate_report.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("metadata_chunking_series_closeout_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/metadata_chunking_series_closeout_v0.4.12.3.md"))

    def test_real_reports_complete_closeout(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.12.3")
        self.assertEqual(report["schema_kind"], "metadata_chunking_series_closeout")
        self.assertEqual(report["summary"]["status"], "completed")
        self.assertEqual(report["summary"]["completed_step_count"], 3)
        self.assertEqual(report["summary"]["primary_root_cause"], "ingestion_article_chunks_missing_boundary_metadata")
        self.assertTrue(report["summary"]["requires_rebuild"])
        self.assertFalse(report["summary"]["implementation_allowed"])
        self.assertIn("v0.4.13.x", report["summary"]["allowed_next_series"])

    def test_gate_failure_blocks_closeout(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            gate = copy.deepcopy(load_json(DEFAULT_FIX_DESIGN_GATE_PATH))
            gate["summary"]["status"] = "failed"
            gate_path = tmp / "gate.json"
            write_json(gate_path, gate)

            report = build_report(DEFAULT_ROOT_CAUSE_PATH, DEFAULT_FIX_DESIGN_PATH, gate_path)

        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("fix_design_gate_not_passed", report["summary"]["blockers"])

    def test_handoff_blocks_main_flow_and_payload_patch(self):
        report = build_report()
        must_not = set(report["handoff"]["must_not_do_next"])

        self.assertIn("do not patch rag_query", must_not)
        self.assertIn("do not patch Qdrant payloads directly", must_not)
        self.assertIn("do not rebuild collection before rebuild dry-run and rollback plan", must_not)

    def test_markdown_mentions_next_series(self):
        markdown = render_markdown(build_report())
        self.assertIn("v0.4.12.3 Metadata/Chunking Series Closeout", markdown)
        self.assertIn("v0.4.13.x ingestion metadata patch", markdown)
        self.assertIn("Must Not Do Next", markdown)


if __name__ == "__main__":
    unittest.main()
