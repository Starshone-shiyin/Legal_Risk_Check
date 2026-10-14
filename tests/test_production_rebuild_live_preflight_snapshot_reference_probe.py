import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.run_production_rebuild_live_preflight_snapshot_reference_probe import (
    DEFAULT_COLLECTION,
    DEFAULT_OUTPUT_PATH,
    READ_ONLY_EXPOSED_METHODS,
    build_report,
    build_snapshot_reference,
    build_snapshot_reference_probe,
)


FIXED_TIME = "2026-06-05T00:00:00+00:00"


class FakeSnapshot:
    def __init__(self, name: str, creation_time: str, size: int = 100, checksum: str = "abc"):
        self.name = name
        self.creation_time = creation_time
        self.size = size
        self.checksum = checksum


class FakeClient:
    def __init__(self, snapshots=None, raise_error: Exception | None = None):
        self.snapshots = snapshots if snapshots is not None else []
        self.raise_error = raise_error
        self.calls: list[str] = []

    def list_snapshots(self, collection_name: str):
        self.calls.append(f"list_snapshots:{collection_name}")
        if self.raise_error:
            raise self.raise_error
        return self.snapshots


class ProductionRebuildLivePreflightSnapshotReferenceProbeTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(DEFAULT_COLLECTION, "legal_knowledge")
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            Path("tests/production_rebuild_live_preflight_snapshot_reference_probe_report.json"),
        )

    def test_reference_format_is_collection_scoped(self):
        self.assertEqual(
            build_snapshot_reference("legal_knowledge", "snapshot-1.snapshot"),
            "qdrant-snapshot://collection/legal_knowledge/snapshot-1.snapshot",
        )

    def test_probe_uses_only_list_snapshots_and_selects_latest_snapshot(self):
        client = FakeClient([
            FakeSnapshot("older.snapshot", "2026-06-04T00:00:00Z"),
            FakeSnapshot("newer.snapshot", "2026-06-05T00:00:00Z"),
        ])
        probe = build_snapshot_reference_probe(client)

        result = probe("legal_knowledge")

        self.assertEqual(result["collection_name"], "legal_knowledge")
        self.assertTrue(result["reachable"])
        self.assertEqual(result["snapshot_count"], 2)
        self.assertEqual(result["selected_snapshot"]["name"], "newer.snapshot")
        self.assertEqual(
            result["backup_or_snapshot_reference"],
            "qdrant-snapshot://collection/legal_knowledge/newer.snapshot",
        )
        self.assertEqual(result["exposed_methods"], READ_ONLY_EXPOSED_METHODS)
        self.assertEqual(client.calls, ["list_snapshots:legal_knowledge"])

    def test_report_blocks_when_no_existing_snapshot_reference(self):
        report = build_report(
            collection_name="legal_knowledge",
            client=FakeClient([]),
            clock=lambda: FIXED_TIME,
        )

        self.assertEqual(report["version"], "0.4.14.24")
        self.assertEqual(report["schema_kind"], "production_rebuild_live_preflight_snapshot_reference_probe_report")
        self.assertEqual(report["summary"]["snapshot_reference_status"], "blocked")
        self.assertIn("backup_or_snapshot_reference_missing", report["summary"]["blockers"])
        self.assertFalse(report["summary"]["backup_or_snapshot_reference_present"])
        self.assertFalse(report["summary"]["qdrant_write_allowed"])
        self.assertFalse(report["summary"]["production_rebuild_allowed"])
        self.assertFalse(report["summary"]["authorization_granted"])

    def test_report_passes_reference_probe_but_never_authorizes_rebuild(self):
        report = build_report(
            collection_name="legal_knowledge",
            client=FakeClient([FakeSnapshot("snapshot-a.snapshot", "2026-06-05T00:00:00Z")]),
            clock=lambda: FIXED_TIME,
        )

        self.assertEqual(report["summary"]["snapshot_reference_status"], "passed")
        self.assertEqual(report["summary"]["blockers"], [])
        self.assertTrue(report["summary"]["backup_or_snapshot_reference_present"])
        self.assertEqual(
            report["summary"]["backup_or_snapshot_reference"],
            "qdrant-snapshot://collection/legal_knowledge/snapshot-a.snapshot",
        )
        self.assertFalse(report["summary"]["qdrant_write_allowed"])
        self.assertFalse(report["summary"]["production_rebuild_allowed"])
        self.assertFalse(report["summary"]["authorization_granted"])

    def test_probe_error_is_fail_closed(self):
        report = build_report(
            collection_name="legal_knowledge",
            client=FakeClient(raise_error=RuntimeError("qdrant unavailable")),
            clock=lambda: FIXED_TIME,
        )

        self.assertEqual(report["summary"]["snapshot_reference_status"], "blocked")
        self.assertIn("snapshot_reference_probe_error", report["summary"]["blockers"])
        self.assertIn("backup_or_snapshot_reference_missing", report["summary"]["blockers"])
        self.assertFalse(report["snapshot_probe"]["reachable"])

    def test_cli_writes_blocked_report_with_allow_blocked_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "snapshot_probe.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "tools/run_production_rebuild_live_preflight_snapshot_reference_probe.py",
                    "--collection",
                    "missing_collection_for_test",
                    "--output",
                    str(output),
                    "--allow-blocked-output",
                ],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(output.read_text(encoding="utf-8-sig"))

        self.assertEqual(report["version"], "0.4.14.24")
        self.assertEqual(report["summary"]["snapshot_reference_status"], "blocked")
        self.assertFalse(report["summary"]["qdrant_write_allowed"])
        self.assertFalse(report["summary"]["production_rebuild_allowed"])

    def test_source_has_no_snapshot_write_rebuild_or_rag_calls(self):
        source = Path("tools/run_production_rebuild_live_preflight_snapshot_reference_probe.py").read_text(
            encoding="utf-8"
        )

        for forbidden in [
            ".create_snapshot(",
            ".create_full_snapshot(",
            ".create_shard_snapshot(",
            ".delete_snapshot(",
            ".delete_full_snapshot(",
            ".delete_shard_snapshot(",
            ".recover_snapshot(",
            ".recover_shard_snapshot(",
            ".upsert(",
            ".delete_collection(",
            ".recreate_collection(",
            ".update_collection(",
            ".update_aliases(",
            "rag_query(",
            "OpenAI(",
            "run_eval(",
            "--write",
            "--rebuild",
            "--switch-collection",
        ]:
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
