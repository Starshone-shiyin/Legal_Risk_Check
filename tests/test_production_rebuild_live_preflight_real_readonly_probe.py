import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.run_production_rebuild_live_preflight_real_readonly_probe import (
    DEFAULT_COLLECTION,
    DEFAULT_OUTPUT_PATH,
    READ_ONLY_EXPOSED_METHODS,
    build_real_qdrant_readonly_probe,
    build_report,
)


FIXED_TIME = "2026-06-05T00:00:00+00:00"


class FakeCount:
    count = 7177


class FakeParams:
    vectors = {"default": {"size": 1024}}
    sparse_vectors = {"bm25": {"index": {"on_disk": False}}}


class FakeConfig:
    params = FakeParams()


class FakeCollectionInfo:
    config = FakeConfig()


class FakePoint:
    payload = {
        "page_content": "sample",
        "metadata": {
            "source": "sample-law",
            "chunk_id": "chunk-1",
            "qdrant_point_id": 1,
        },
    }


class FakeClient:
    def __init__(self, collection_name: str = "legal_knowledge"):
        self.collection_name = collection_name
        self.calls: list[str] = []

    def get_collection(self, collection_name: str):
        self.calls.append(f"get_collection:{collection_name}")
        return FakeCollectionInfo()

    def count(self, collection_name: str, exact: bool = False):
        self.calls.append(f"count:{collection_name}:{exact}")
        return FakeCount()

    def scroll(self, collection_name: str, limit: int, with_payload: bool, with_vectors: bool):
        self.calls.append(f"scroll:{collection_name}:{limit}:{with_payload}:{with_vectors}")
        return [FakePoint()], None


class ProductionRebuildLivePreflightRealReadonlyProbeTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(DEFAULT_COLLECTION, "legal_knowledge")
        self.assertEqual(DEFAULT_OUTPUT_PATH, Path("tests/production_rebuild_live_preflight_real_readonly_probe_report.json"))

    def test_real_readonly_probe_uses_only_read_methods(self):
        client = FakeClient()
        probe = build_real_qdrant_readonly_probe(client)

        result = probe("legal_knowledge")

        self.assertEqual(result["collection_name"], "legal_knowledge")
        self.assertTrue(result["reachable"])
        self.assertEqual(result["points_count"], 7177)
        self.assertEqual(result["exposed_methods"], READ_ONLY_EXPOSED_METHODS)
        self.assertIn("metadata", result["sample_payload_keys"])
        self.assertIn("chunk_id", result["sample_metadata_keys"])
        self.assertEqual(
            client.calls,
            [
                "get_collection:legal_knowledge",
                "count:legal_knowledge:False",
                "scroll:legal_knowledge:1:True:False",
            ],
        )

    def test_build_report_blocks_without_authorization_but_keeps_real_readonly_probe(self):
        report = build_report(
            collection_name="legal_knowledge",
            authorization_status="not_collected",
            backup_or_snapshot_reference=None,
            source_lineage_reference="ingestion-metadata-source-patch-v0.4.13.8",
            client=FakeClient(),
            clock=lambda: FIXED_TIME,
        )

        self.assertEqual(report["version"], "0.4.14.23")
        self.assertEqual(report["schema_kind"], "production_rebuild_live_preflight_real_readonly_probe_report")
        self.assertEqual(report["summary"]["preflight_status"], "blocked")
        self.assertIn("authorization_record_not_accepted", report["summary"]["blockers"])
        self.assertIn("backup_or_snapshot_reference_missing", report["summary"]["blockers"])
        self.assertTrue(report["summary"]["real_qdrant_readonly_probe"])
        self.assertTrue(report["summary"]["qdrant_access_allowed"])
        self.assertFalse(report["summary"]["qdrant_write_allowed"])
        self.assertFalse(report["summary"]["production_rebuild_allowed"])
        self.assertFalse(report["summary"]["authorization_granted"])

    def test_accepted_mock_preflight_still_does_not_grant_write_or_rebuild(self):
        report = build_report(
            collection_name="legal_knowledge",
            authorization_status="accepted",
            authorization_reference="mock-formal-authorization",
            backup_or_snapshot_reference="snapshot://manual-placeholder",
            source_lineage_reference="ingestion-metadata-source-patch-v0.4.13.8",
            client=FakeClient(),
            clock=lambda: FIXED_TIME,
        )

        self.assertEqual(report["summary"]["preflight_status"], "passed")
        self.assertEqual(report["summary"]["blockers"], [])
        self.assertFalse(report["summary"]["qdrant_write_allowed"])
        self.assertFalse(report["summary"]["production_rebuild_allowed"])
        self.assertFalse(report["summary"]["authorization_granted"])

    def test_cli_writes_blocked_report_with_allow_blocked_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "probe.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "tools/run_production_rebuild_live_preflight_real_readonly_probe.py",
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

        self.assertEqual(report["version"], "0.4.14.23")
        self.assertEqual(report["summary"]["preflight_status"], "blocked")
        self.assertFalse(report["summary"]["qdrant_write_allowed"])
        self.assertFalse(report["summary"]["production_rebuild_allowed"])

    def test_source_has_no_write_or_rebuild_calls(self):
        source = Path("tools/run_production_rebuild_live_preflight_real_readonly_probe.py").read_text(encoding="utf-8")

        for forbidden in [
            ".upsert(",
            ".delete(",
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
