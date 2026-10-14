import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.run_production_rebuild_live_preflight_snapshot_create_reference_capture import (
    AUTHORIZED_STATUS,
    DEFAULT_COLLECTION,
    DEFAULT_OUTPUT_PATH,
    build_authorized_snapshot_capture,
    build_report,
)


FIXED_TIME = "2026-06-05T00:00:00+00:00"


class FakeSnapshot:
    def __init__(self, name: str, creation_time: str, size: int = 100, checksum: str = "abc"):
        self.name = name
        self.creation_time = creation_time
        self.size = size
        self.checksum = checksum


class FakeClient:
    _DEFAULT = object()

    def __init__(self, created=_DEFAULT, listed=None, raise_on_create: Exception | None = None):
        self.created = (
            FakeSnapshot("created.snapshot", "2026-06-05T00:00:00Z")
            if created is self._DEFAULT
            else created
        )
        self.listed = listed if listed is not None else [self.created]
        self.raise_on_create = raise_on_create
        self.calls: list[str] = []

    def create_snapshot(self, collection_name: str, wait: bool = True):
        self.calls.append(f"create_snapshot:{collection_name}:{wait}")
        if self.raise_on_create:
            raise self.raise_on_create
        return self.created

    def list_snapshots(self, collection_name: str):
        self.calls.append(f"list_snapshots:{collection_name}")
        return self.listed


class ProductionRebuildAuthorizedSnapshotCaptureTest(unittest.TestCase):
    def test_default_paths_and_authorization_status(self):
        self.assertEqual(DEFAULT_COLLECTION, "legal_knowledge")
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            Path("tests/production_rebuild_live_preflight_snapshot_create_reference_capture_report.json"),
        )
        self.assertEqual(AUTHORIZED_STATUS, "user_explicitly_authorized_snapshot_creation")

    def test_blocks_without_explicit_authorization_and_does_not_call_client(self):
        client = FakeClient()

        result = build_authorized_snapshot_capture(
            collection_name="legal_knowledge",
            authorization_status="not_collected",
            authorization_reference="missing",
            client=client,
        )

        self.assertEqual(result["status"], "blocked")
        self.assertIn("snapshot_creation_not_explicitly_authorized", result["blockers"])
        self.assertIsNone(result["backup_or_snapshot_reference"])
        self.assertEqual(client.calls, [])

    def test_blocks_wrong_collection_before_client_mutation(self):
        client = FakeClient()

        result = build_authorized_snapshot_capture(
            collection_name="other_collection",
            authorization_status=AUTHORIZED_STATUS,
            authorization_reference="user:2026-06-05:create-legal_knowledge-snapshot",
            client=client,
        )

        self.assertEqual(result["status"], "blocked")
        self.assertIn("target_collection_not_locked_to_legal_knowledge", result["blockers"])
        self.assertIsNone(result["backup_or_snapshot_reference"])
        self.assertEqual(client.calls, [])

    def test_authorized_capture_creates_snapshot_and_captures_reference(self):
        client = FakeClient(
            created=FakeSnapshot("snapshot-a.snapshot", "2026-06-05T00:00:00Z"),
            listed=[
                FakeSnapshot("older.snapshot", "2026-06-04T00:00:00Z"),
                FakeSnapshot("snapshot-a.snapshot", "2026-06-05T00:00:00Z"),
            ],
        )

        result = build_authorized_snapshot_capture(
            collection_name="legal_knowledge",
            authorization_status=AUTHORIZED_STATUS,
            authorization_reference="user:2026-06-05:create-legal_knowledge-snapshot",
            client=client,
        )

        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["blockers"], [])
        self.assertEqual(result["created_snapshot"]["name"], "snapshot-a.snapshot")
        self.assertEqual(result["snapshot_count_after_create"], 2)
        self.assertEqual(result["snapshot_count_before_create"], 2)
        self.assertEqual(
            result["backup_or_snapshot_reference"],
            "qdrant-snapshot://collection/legal_knowledge/snapshot-a.snapshot",
        )
        self.assertEqual(
            client.calls,
            [
                "list_snapshots:legal_knowledge",
                "create_snapshot:legal_knowledge:True",
                "list_snapshots:legal_knowledge",
            ],
        )

    def test_build_report_passes_reference_but_never_authorizes_rebuild(self):
        report = build_report(
            collection_name="legal_knowledge",
            authorization_status=AUTHORIZED_STATUS,
            authorization_reference="user:2026-06-05:create-legal_knowledge-snapshot",
            client=FakeClient(created=FakeSnapshot("snapshot-a.snapshot", "2026-06-05T00:00:00Z")),
            clock=lambda: FIXED_TIME,
        )

        self.assertEqual(report["version"], "0.4.14.25")
        self.assertEqual(report["schema_kind"], "production_rebuild_live_preflight_snapshot_create_reference_capture_report")
        self.assertEqual(report["summary"]["snapshot_capture_status"], "passed")
        self.assertTrue(report["summary"]["snapshot_created"])
        self.assertTrue(report["summary"]["backup_or_snapshot_reference_present"])
        self.assertTrue(report["summary"]["qdrant_snapshot_create_allowed"])
        self.assertFalse(report["summary"]["qdrant_point_write_allowed"])
        self.assertFalse(report["summary"]["production_rebuild_allowed"])
        self.assertFalse(report["summary"]["authorization_granted_for_rebuild"])

    def test_none_snapshot_return_is_fail_closed(self):
        report = build_report(
            collection_name="legal_knowledge",
            authorization_status=AUTHORIZED_STATUS,
            authorization_reference="user:2026-06-05:create-legal_knowledge-snapshot",
            client=FakeClient(created=None, listed=[]),
            clock=lambda: FIXED_TIME,
        )

        self.assertEqual(report["summary"]["snapshot_capture_status"], "blocked")
        self.assertIn("created_snapshot_reference_missing", report["summary"]["blockers"])
        self.assertFalse(report["summary"]["backup_or_snapshot_reference_present"])

    def test_create_error_is_fail_closed(self):
        report = build_report(
            collection_name="legal_knowledge",
            authorization_status=AUTHORIZED_STATUS,
            authorization_reference="user:2026-06-05:create-legal_knowledge-snapshot",
            client=FakeClient(raise_on_create=RuntimeError("qdrant failed")),
            clock=lambda: FIXED_TIME,
        )

        self.assertEqual(report["summary"]["snapshot_capture_status"], "blocked")
        self.assertIn("snapshot_creation_or_capture_error", report["summary"]["blockers"])
        self.assertFalse(report["summary"]["backup_or_snapshot_reference_present"])
        self.assertFalse(report["summary"]["production_rebuild_allowed"])

    def test_cli_blocks_without_explicit_authorization(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "capture.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "tools/run_production_rebuild_live_preflight_snapshot_create_reference_capture.py",
                    "--collection",
                    "legal_knowledge",
                    "--authorization-status",
                    "not_collected",
                    "--authorization-reference",
                    "missing",
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

        self.assertEqual(report["version"], "0.4.14.25")
        self.assertEqual(report["summary"]["snapshot_capture_status"], "blocked")
        self.assertFalse(report["summary"]["backup_or_snapshot_reference_present"])

    def test_cli_missing_authorization_ack_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "capture.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "tools/run_production_rebuild_live_preflight_snapshot_create_reference_capture.py",
                    "--collection",
                    "legal_knowledge",
                    "--authorization-status",
                    AUTHORIZED_STATUS,
                    "--authorization-reference",
                    "user:2026-06-05:create-legal_knowledge-snapshot",
                    "--output",
                    str(output),
                ],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 1)
            report = json.loads(output.read_text(encoding="utf-8-sig"))

        self.assertIn("snapshot_creation_not_explicitly_authorized", report["summary"]["blockers"])

    def test_source_has_no_delete_recover_point_write_rebuild_or_rag_calls(self):
        source = Path("tools/run_production_rebuild_live_preflight_snapshot_create_reference_capture.py").read_text(
            encoding="utf-8"
        )

        for forbidden in [
            ".delete_snapshot(",
            ".delete_full_snapshot(",
            ".delete_shard_snapshot(",
            ".recover_snapshot(",
            ".recover_shard_snapshot(",
            ".upsert(",
            ".delete_collection(",
            ".create_collection(",
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
