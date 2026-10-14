import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.check_evidence_metadata_snapshot_gate import (
    DEFAULT_CONTRACT_PATH,
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


class EvidenceMetadataSnapshotGateTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(DEFAULT_SNAPSHOT_PATH, legacy_report_path("evidence_metadata_snapshot_report.json"))
        self.assertEqual(DEFAULT_CONTRACT_PATH, legacy_report_path("evidence_metadata_snapshot_contract_report.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("evidence_metadata_snapshot_gate_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/evidence_metadata_snapshot_gate_v0.4.11.2.md"))

    def test_real_snapshot_opens_closeout(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.11.2")
        self.assertEqual(report["schema_kind"], "evidence_metadata_snapshot_gate")
        self.assertEqual(report["gate"]["status"], "open_for_v0_4_11_series_closeout")
        self.assertEqual(report["gate"]["allowed_next_step"], "v0_4_11_series_closeout")
        self.assertEqual(report["summary"]["diagnostic_row_count"], 19)
        self.assertEqual(report["summary"]["target_count"], 19)
        self.assertEqual(report["summary"]["failed_check_count"], 0)
        self.assertEqual(report["summary"]["primary_finding"], "chunk_boundary_ambiguity")
        self.assertGreater(report["summary"]["scanned_point_count"], 0)
        self.assertTrue(all(item["status"] == "passed" for item in report["checks"]))

    def test_qdrant_unavailable_snapshot_blocks_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            snapshot = copy.deepcopy(load_json(DEFAULT_SNAPSHOT_PATH))
            snapshot["snapshot_gate"]["status"] = "blocked"
            snapshot["snapshot_gate"]["qdrant_payload_read"] = False
            snapshot["summary"]["qdrant_payload_read"] = False
            snapshot_path = tmp / "snapshot.json"
            write_json(snapshot_path, snapshot)

            report = build_report(snapshot_path, DEFAULT_CONTRACT_PATH)

        self.assertEqual(report["gate"]["status"], "blocked")
        self.assertIn("snapshot_status_allowed", report["gate"]["blockers"])
        self.assertIn("qdrant_payload_read", report["gate"]["blockers"])

    def test_vector_read_drift_blocks_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            snapshot = copy.deepcopy(load_json(DEFAULT_SNAPSHOT_PATH))
            snapshot["snapshot_gate"]["with_vectors"] = True
            snapshot_path = tmp / "snapshot.json"
            write_json(snapshot_path, snapshot)

            report = build_report(snapshot_path, DEFAULT_CONTRACT_PATH)

        self.assertEqual(report["gate"]["status"], "blocked")
        self.assertIn("vectors_disabled", report["gate"]["blockers"])

    def test_row_count_drift_blocks_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            snapshot = copy.deepcopy(load_json(DEFAULT_SNAPSHOT_PATH))
            snapshot["diagnostic_rows"] = snapshot["diagnostic_rows"][:-1]
            snapshot_path = tmp / "snapshot.json"
            write_json(snapshot_path, snapshot)

            report = build_report(snapshot_path, DEFAULT_CONTRACT_PATH)

        self.assertEqual(report["gate"]["status"], "blocked")
        self.assertIn("row_count_matches_contract", report["gate"]["blockers"])

    def test_markdown_records_findings_without_fixing(self):
        markdown = render_markdown(build_report())
        self.assertIn("v0.4.11.2 Evidence Metadata Snapshot Gate", markdown)
        self.assertIn("Metadata findings are preserved", markdown)
        self.assertIn("does not repair metadata or chunks", markdown)


if __name__ == "__main__":
    unittest.main()
