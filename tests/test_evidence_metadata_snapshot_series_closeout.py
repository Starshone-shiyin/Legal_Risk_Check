import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_evidence_metadata_snapshot_series_closeout import (
    DEFAULT_CONTRACT_PATH,
    DEFAULT_GATE_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_SNAPSHOT_PATH,
    build_report,
    render_markdown,
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class EvidenceMetadataSnapshotSeriesCloseoutTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(DEFAULT_CONTRACT_PATH, legacy_report_path("evidence_metadata_snapshot_contract_report.json"))
        self.assertEqual(DEFAULT_SNAPSHOT_PATH, legacy_report_path("evidence_metadata_snapshot_report.json"))
        self.assertEqual(DEFAULT_GATE_PATH, legacy_report_path("evidence_metadata_snapshot_gate_report.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("evidence_metadata_snapshot_series_closeout_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/evidence_metadata_snapshot_series_closeout_v0.4.11.3.md"))

    def test_real_sources_close_series(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.11.3")
        self.assertEqual(report["schema_kind"], "evidence_metadata_snapshot_series_closeout")
        self.assertEqual(report["closeout_gate"]["status"], "v0_4_11_series_closed_for_evidence_metadata_snapshot")
        self.assertEqual(report["closeout_gate"]["allowed_next_step"], "v0.4.12.x metadata_chunking_root_cause_fix_design")
        self.assertEqual(report["summary"]["completed_step_count"], 3)
        self.assertEqual(report["summary"]["target_count"], 19)
        self.assertEqual(report["summary"]["diagnostic_row_count"], 19)
        self.assertEqual(report["summary"]["primary_finding"], "chunk_boundary_ambiguity")
        self.assertGreater(report["summary"]["scanned_point_count"], 0)
        self.assertFalse(report["closeout_gate"]["implementation_allowed"])
        self.assertFalse(report["closeout_gate"]["retrieval_logic_change_allowed"])
        self.assertEqual(report["closeout_gate"]["blockers"], [])

    def test_gate_drift_blocks_closeout(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            gate = copy.deepcopy(load_json(DEFAULT_GATE_PATH))
            gate["gate"]["status"] = "blocked"
            gate_path = tmp / "gate.json"
            write_json(gate_path, gate)

            report = build_report(DEFAULT_CONTRACT_PATH, DEFAULT_SNAPSHOT_PATH, gate_path)

        self.assertEqual(report["closeout_gate"]["status"], "blocked")
        self.assertIn("snapshot_gate_not_open", report["closeout_gate"]["blockers"])

    def test_missing_qdrant_read_blocks_closeout(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            snapshot = copy.deepcopy(load_json(DEFAULT_SNAPSHOT_PATH))
            snapshot["summary"]["qdrant_payload_read"] = False
            snapshot_path = tmp / "snapshot.json"
            write_json(snapshot_path, snapshot)

            report = build_report(DEFAULT_CONTRACT_PATH, snapshot_path, DEFAULT_GATE_PATH)

        self.assertEqual(report["closeout_gate"]["status"], "blocked")
        self.assertIn("qdrant_payload_not_read", report["closeout_gate"]["blockers"])

    def test_markdown_keeps_fix_boundary(self):
        markdown = render_markdown(build_report())
        self.assertIn("v0.4.11.3 Evidence Metadata Snapshot Series Closeout", markdown)
        self.assertIn("did not fix it", markdown)
        self.assertIn("v0.4.12.x should design root-cause", markdown)


if __name__ == "__main__":
    unittest.main()
