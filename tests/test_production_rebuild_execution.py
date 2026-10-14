import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.run_production_rebuild_execution import (
    DEFAULT_OUTPUT_PATH,
    VERSION,
    build_execution_record,
    run_rebuild_command,
    validate_execution_inputs,
)


FIXED_TIME = "2026-06-05T00:00:00+00:00"


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def authorization_record() -> dict:
    return {
        "version": "0.4.14.28",
        "schema_kind": "production_rebuild_authorization_record",
        "authorization_status": "accepted",
        "authorization_reference": "formal-authorization",
        "target_collection": "legal_knowledge",
        "backup_or_snapshot_reference": "snapshot://legal_knowledge",
        "source_lineage_reference": "ingestion-metadata-source-patch-v0.4.13.8",
    }


def preflight_report() -> dict:
    return {
        "version": "0.4.14.28",
        "schema_kind": "production_rebuild_live_preflight_report",
        "summary": {
            "preflight_status": "passed",
            "blockers": [],
            "formal_authorization_accepted": True,
        },
    }


def fake_snapshot(collection_name: str) -> dict:
    return {
        "collection_name": collection_name,
        "reachable": True,
        "points_count": 123,
        "sample_metadata_keys": ["chunk_index", "chunk_count", "source"],
    }


class ProductionRebuildExecutionTest(unittest.TestCase):
    def test_default_output_and_version(self):
        self.assertEqual(DEFAULT_OUTPUT_PATH, Path("tests/production_rebuild_execution_report.json"))
        self.assertEqual(VERSION, "0.4.14.29")

    def test_validate_execution_inputs_requires_authorized_passed_preflight(self):
        blockers = validate_execution_inputs(authorization_record(), preflight_report())
        self.assertEqual(blockers, [])

        bad_preflight = preflight_report()
        bad_preflight["summary"]["blockers"] = ["still_blocked"]
        blockers = validate_execution_inputs(authorization_record(), bad_preflight)
        self.assertIn("preflight_blockers_present", blockers)

    def test_dry_run_only_does_not_execute_rebuild(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            auth_path = root / "auth.json"
            preflight_path = root / "preflight.json"
            manifest_path = root / "knowledge_manifest.json"
            write_json(auth_path, authorization_record())
            write_json(preflight_path, preflight_report())
            write_json(manifest_path, {"documents": []})

            current = Path.cwd()
            try:
                import os

                os.chdir(root)
                report = build_execution_record(
                    authorization_record_path=auth_path,
                    preflight_report_path=preflight_path,
                    execute=False,
                    collection_snapshot=fake_snapshot,
                    command_runner=lambda **_: (_ for _ in ()).throw(AssertionError("should not run")),
                    clock=lambda: FIXED_TIME,
                )
            finally:
                os.chdir(current)

        self.assertEqual(report["summary"]["execution_status"], "dry_run_only")
        self.assertFalse(report["summary"]["qdrant_write_executed"])
        self.assertIsNone(report["command_result"])

    def test_execute_uses_existing_rag_admin_rebuild_command_and_records_snapshots(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            auth_path = root / "auth.json"
            preflight_path = root / "preflight.json"
            manifest_path = root / "knowledge_manifest.json"
            write_json(auth_path, authorization_record())
            write_json(preflight_path, preflight_report())
            write_json(manifest_path, {"documents": [{"source": "A", "file_path": "a.txt"}]})
            (root / "a.txt").write_text("demo", encoding="utf-8")

            calls = []

            def fake_runner(command, **kwargs):
                calls.append((command, kwargs))
                return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

            current = Path.cwd()
            try:
                import os

                os.chdir(root)
                report = build_execution_record(
                    authorization_record_path=auth_path,
                    preflight_report_path=preflight_path,
                    execute=True,
                    collection_snapshot=fake_snapshot,
                    command_runner=fake_runner,
                    clock=lambda: FIXED_TIME,
                )
            finally:
                os.chdir(current)

        self.assertEqual(report["summary"]["execution_status"], "succeeded")
        self.assertTrue(report["summary"]["qdrant_write_executed"])
        self.assertEqual(report["before_snapshot"]["points_count"], 123)
        self.assertEqual(report["after_snapshot"]["points_count"], 123)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0][-2:], ["rag_admin.py", "--rebuild"])
        self.assertEqual(calls[0][1]["input"], "y\n")
        self.assertEqual(calls[0][1]["encoding"], "utf-8")

    def test_run_rebuild_command_captures_output_tail(self):
        def fake_runner(command, **kwargs):
            return subprocess.CompletedProcess(command, 0, stdout="x" * 13000, stderr="err")

        result = run_rebuild_command(command_runner=fake_runner)

        self.assertEqual(result["returncode"], 0)
        self.assertEqual(len(result["stdout_tail"]), 12000)
        self.assertEqual(result["stderr_tail"], "err")


if __name__ == "__main__":
    unittest.main()
