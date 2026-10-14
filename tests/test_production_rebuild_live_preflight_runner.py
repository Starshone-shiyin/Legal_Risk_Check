import ast
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.run_production_rebuild_live_preflight import (
    DEFAULT_COLLECTION,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_SCAFFOLD_REPORT_PATH,
    READ_ONLY_EXPOSED_METHODS,
    build_authorization_context,
    build_real_qdrant_readonly_probe,
    build_live_preflight_report,
    build_scaffold_status_report,
    load_authorization_record,
    write_json,
)


FIXED_TIME = "2026-06-05T00:00:00+00:00"


def accepted_authorization() -> dict:
    return {
        "authorization_status": "accepted",
        "authorization_reference": "mock-only-formal-authorization",
        "record_id": "mock-only",
    }


def fake_probe(collection_name: str) -> dict:
    return {
        "collection_name": collection_name,
        "reachable": True,
        "exposed_methods": ["get_collection", "scroll"],
    }


def base_kwargs() -> dict:
    return {
        "authorization_record": accepted_authorization(),
        "target_collection": "legal_knowledge_rebuild_candidate",
        "backup_or_snapshot_reference": "snapshot://mock-only",
        "source_lineage_reference": "ingestion-metadata-patch-v0.4.13.8",
        "qdrant_readonly_probe": fake_probe,
        "clock": lambda: FIXED_TIME,
    }


class ProductionRebuildLivePreflightRunnerTest(unittest.TestCase):
    def test_default_paths_and_no_live_probe(self):
        self.assertEqual(DEFAULT_COLLECTION, "legal_knowledge")
        self.assertEqual(DEFAULT_OUTPUT_PATH, Path("tests/production_rebuild_live_preflight_report.json"))
        self.assertEqual(
            DEFAULT_SCAFFOLD_REPORT_PATH,
            Path("tests/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_report.json"),
        )

        report = build_live_preflight_report(
            authorization_record=accepted_authorization(),
            target_collection="legal_knowledge_rebuild_candidate",
            backup_or_snapshot_reference="snapshot://mock-only",
            source_lineage_reference="ingestion-metadata-patch-v0.4.13.8",
            clock=lambda: FIXED_TIME,
        )

        self.assertEqual(report["summary"]["preflight_status"], "blocked")
        self.assertIn("readonly_probe_missing", report["summary"]["blockers"])
        self.assertFalse(report["summary"]["live_preflight_run_allowed"])
        self.assertFalse(report["summary"]["qdrant_write_allowed"])
        self.assertFalse(report["summary"]["production_rebuild_allowed"])
        self.assertFalse(report["summary"]["authorization_granted"])

    def test_successful_fake_readonly_probe_does_not_grant_write_or_rebuild(self):
        report = build_live_preflight_report(**base_kwargs())

        self.assertEqual(report["version"], "0.4.14.29")
        self.assertEqual(report["schema_kind"], "production_rebuild_live_preflight_report")
        self.assertEqual(report["generated_at"], FIXED_TIME)
        self.assertEqual(report["summary"]["preflight_status"], "passed")
        self.assertEqual(report["summary"]["blockers"], [])
        self.assertTrue(report["summary"]["qdrant_access_allowed"])
        self.assertFalse(report["summary"]["live_preflight_run_allowed"])
        self.assertFalse(report["summary"]["qdrant_write_allowed"])
        self.assertFalse(report["summary"]["production_rebuild_allowed"])
        self.assertFalse(report["summary"]["authorization_granted"])
        self.assertTrue(report["summary"]["formal_authorization_accepted"])
        self.assertEqual(report["summary"]["full_eval"], "not_run")

    def test_authorization_record_context_can_drive_passed_preflight_without_rebuild_permission(self):
        authorization_record = {
            "authorization_status": "accepted",
            "authorization_reference": "formal-record-2026-06-05",
            "target_collection": "legal_knowledge_rebuild_candidate",
            "backup_or_snapshot_reference": "snapshot://formal-record",
            "source_lineage_reference": "ingestion-metadata-patch-v0.4.13.8",
        }
        context, target, backup, lineage = build_authorization_context(
            authorization_record=authorization_record,
            cli_authorization_status=None,
            cli_authorization_reference=None,
            cli_target_collection=None,
            cli_backup_or_snapshot_reference=None,
            cli_source_lineage_reference=None,
        )

        report = build_live_preflight_report(
            authorization_record=context,
            target_collection=target,
            backup_or_snapshot_reference=backup,
            source_lineage_reference=lineage,
            qdrant_readonly_probe=fake_probe,
            clock=lambda: FIXED_TIME,
        )

        self.assertEqual(report["summary"]["preflight_status"], "passed")
        self.assertEqual(report["summary"]["blockers"], [])
        self.assertTrue(report["summary"]["formal_authorization_accepted"])
        self.assertFalse(report["summary"]["authorization_granted"])
        self.assertFalse(report["summary"]["qdrant_write_allowed"])
        self.assertFalse(report["summary"]["production_rebuild_allowed"])

    def test_authorization_record_cli_conflict_fails_closed(self):
        context, target, backup, lineage = build_authorization_context(
            authorization_record={
                "authorization_status": "accepted",
                "authorization_reference": "formal-record",
                "target_collection": "legal_knowledge",
                "backup_or_snapshot_reference": "snapshot://record",
                "source_lineage_reference": "ingestion-metadata-patch-v0.4.13.8",
            },
            cli_authorization_status="accepted",
            cli_authorization_reference="formal-record",
            cli_target_collection="other_collection",
            cli_backup_or_snapshot_reference="snapshot://record",
            cli_source_lineage_reference="ingestion-metadata-patch-v0.4.13.8",
        )

        report = build_live_preflight_report(
            authorization_record=context,
            target_collection=target,
            backup_or_snapshot_reference=backup,
            source_lineage_reference=lineage,
            qdrant_readonly_probe=fake_probe,
            clock=lambda: FIXED_TIME,
        )

        self.assertEqual(report["summary"]["preflight_status"], "blocked")
        self.assertIn("authorization_record_target_collection_mismatch", report["summary"]["blockers"])
        self.assertFalse(report["summary"]["production_rebuild_allowed"])

    def test_authorization_record_with_execution_fields_fails_closed(self):
        context, target, backup, lineage = build_authorization_context(
            authorization_record={
                "authorization_status": "accepted",
                "authorization_reference": "formal-record",
                "target_collection": "legal_knowledge_rebuild_candidate",
                "backup_or_snapshot_reference": "snapshot://record",
                "source_lineage_reference": "ingestion-metadata-patch-v0.4.13.8",
                "commands": ["rebuild now"],
                "authorized_actions": ["production_rebuild"],
            },
            cli_authorization_status=None,
            cli_authorization_reference=None,
            cli_target_collection=None,
            cli_backup_or_snapshot_reference=None,
            cli_source_lineage_reference=None,
        )

        report = build_live_preflight_report(
            authorization_record=context,
            target_collection=target,
            backup_or_snapshot_reference=backup,
            source_lineage_reference=lineage,
            qdrant_readonly_probe=fake_probe,
            clock=lambda: FIXED_TIME,
        )

        self.assertEqual(report["summary"]["preflight_status"], "blocked")
        self.assertIn("authorization_record_forbidden_execution_fields", report["summary"]["blockers"])
        self.assertFalse(report["summary"]["production_rebuild_allowed"])

    def test_authorization_record_loader_rejects_non_object_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "authorization.json"
            path.write_text("[]", encoding="utf-8")

            with self.assertRaises(ValueError):
                load_authorization_record(path)

    def test_missing_authorization_fails_closed(self):
        kwargs = base_kwargs()
        kwargs["authorization_record"] = {}

        report = build_live_preflight_report(**kwargs)

        self.assertEqual(report["summary"]["preflight_status"], "blocked")
        self.assertIn("authorization_record_not_accepted", report["summary"]["blockers"])
        self.assertFalse(report["summary"]["production_rebuild_allowed"])

    def test_accepted_authorization_without_reference_fails_closed(self):
        kwargs = base_kwargs()
        kwargs["authorization_record"] = {"authorization_status": "accepted"}

        report = build_live_preflight_report(**kwargs)

        self.assertEqual(report["summary"]["preflight_status"], "blocked")
        self.assertIn("authorization_record_not_accepted", report["summary"]["blockers"])
        self.assertFalse(report["summary"]["formal_authorization_accepted"])

    def test_target_collection_mismatch_fails_closed(self):
        kwargs = base_kwargs()
        kwargs["qdrant_readonly_probe"] = lambda _collection: {
            "collection_name": "other_collection",
            "exposed_methods": ["get_collection"],
        }

        report = build_live_preflight_report(**kwargs)

        self.assertEqual(report["summary"]["preflight_status"], "blocked")
        self.assertIn("target_collection_mismatch", report["summary"]["blockers"])
        self.assertFalse(report["summary"]["qdrant_write_allowed"])

    def test_fake_probe_error_fails_closed(self):
        def failing_probe(_collection: str) -> dict:
            raise RuntimeError("mock probe failed")

        kwargs = base_kwargs()
        kwargs["qdrant_readonly_probe"] = failing_probe

        report = build_live_preflight_report(**kwargs)

        self.assertEqual(report["summary"]["preflight_status"], "blocked")
        self.assertIn("readonly_probe_error", report["summary"]["blockers"])
        self.assertFalse(report["summary"]["production_rebuild_allowed"])

    def test_forbidden_write_method_exposure_fails_closed(self):
        kwargs = base_kwargs()
        kwargs["qdrant_readonly_probe"] = lambda collection: {
            "collection_name": collection,
            "exposed_methods": ["get_collection", "upsert"],
        }

        report = build_live_preflight_report(**kwargs)

        self.assertEqual(report["summary"]["preflight_status"], "blocked")
        self.assertIn("forbidden_write_methods_exposed", report["summary"]["blockers"])
        self.assertFalse(report["summary"]["qdrant_write_allowed"])

    def test_missing_backup_or_source_lineage_fails_closed(self):
        kwargs = base_kwargs()
        kwargs["backup_or_snapshot_reference"] = ""
        kwargs["source_lineage_reference"] = None

        report = build_live_preflight_report(**kwargs)

        self.assertEqual(report["summary"]["preflight_status"], "blocked")
        self.assertIn("backup_or_snapshot_reference_missing", report["summary"]["blockers"])
        self.assertIn("source_lineage_reference_missing", report["summary"]["blockers"])

    def test_scaffold_status_report_documents_non_execution_boundary(self):
        report = build_scaffold_status_report(clock=lambda: FIXED_TIME)
        summary = report["summary"]

        self.assertEqual(report["version"], "0.4.14.21")
        self.assertEqual(
            report["schema_kind"],
            "production_rebuild_live_preflight_runner_minimal_implementation_scaffold",
        )
        self.assertEqual(summary["status"], "ready_for_minimal_scaffold_gate")
        self.assertEqual(
            summary["allowed_next_step"],
            "production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate",
        )
        self.assertTrue(summary["runner_file_created"])
        self.assertTrue(summary["runner_test_file_created"])
        self.assertFalse(summary["runner_report_created"])
        self.assertFalse(summary["live_preflight_run_allowed"])
        self.assertFalse(summary["qdrant_write_allowed"])
        self.assertFalse(summary["production_rebuild_allowed"])

    def test_cli_writes_only_scaffold_status_to_requested_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "scaffold_report.json"
            subprocess.run(
                [
                    sys.executable,
                    "tools/run_production_rebuild_live_preflight.py",
                    "--scaffold-report-output",
                    str(output),
                ],
                check=True,
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
            )

            report = json.loads(output.read_text(encoding="utf-8-sig"))

        self.assertEqual(report["version"], "0.4.14.21")
        self.assertEqual(report["summary"]["status"], "ready_for_minimal_scaffold_gate")

    def test_cli_reads_authorization_record_but_still_only_writes_readonly_preflight(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            authorization_path = root / "authorization.json"
            output = root / "preflight.json"
            write_json(
                authorization_path,
                {
                    "authorization_status": "accepted",
                    "authorization_reference": "formal-record-cli",
                    "target_collection": "missing_collection_for_test",
                    "backup_or_snapshot_reference": "snapshot://formal-record",
                    "source_lineage_reference": "ingestion-metadata-patch-v0.4.13.8",
                },
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "tools/run_production_rebuild_live_preflight.py",
                    "--run-readonly-live-preflight",
                    "--authorization-record",
                    str(authorization_path),
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

        self.assertEqual(report["version"], "0.4.14.29")
        self.assertEqual(report["inputs"]["target_collection"], "missing_collection_for_test")
        self.assertFalse(report["summary"]["qdrant_write_allowed"])
        self.assertFalse(report["summary"]["production_rebuild_allowed"])

    def test_write_json_is_available_for_explicit_temp_outputs_only(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "report.json"
            write_json(path, build_live_preflight_report(**base_kwargs()))
            report = json.loads(path.read_text(encoding="utf-8-sig"))

        self.assertEqual(report["summary"]["preflight_status"], "passed")

    def test_real_readonly_probe_uses_only_read_methods(self):
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
            payload = {"page_content": "sample", "metadata": {"chunk_id": "chunk-1", "qdrant_point_id": 1}}

        class FakeClient:
            def __init__(self):
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

            def upsert(self, *args, **kwargs):
                raise AssertionError("readonly probe must not call upsert")

            def delete(self, *args, **kwargs):
                raise AssertionError("readonly probe must not call delete")

            def update_aliases(self, *args, **kwargs):
                raise AssertionError("readonly probe must not call update_aliases")

        client = FakeClient()
        result = build_real_qdrant_readonly_probe(client)("legal_knowledge")

        self.assertEqual(result["collection_name"], "legal_knowledge")
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

    def test_source_has_no_write_rebuild_rag_llm_or_eval_calls(self):
        source = Path("tools/run_production_rebuild_live_preflight.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = set()
        for node in tree.body:
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            if isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)

        forbidden_imports = {"qdrant_client", "openai", "src.rag.retriever", "src.rag.ingestion", "run_rag_eval"}
        self.assertTrue(forbidden_imports.isdisjoint(imports))
        self.assertNotIn("src.core.vectorstore", imports)
        for forbidden_call in [
            "rag_query(",
            "OpenAI(",
            "run_eval(",
            ".upsert(",
            ".delete_collection(",
            ".recreate_collection(",
            ".update_aliases(",
            "--rebuild",
            "--switch-collection",
            "--write",
        ]:
            self.assertNotIn(forbidden_call, source)


if __name__ == "__main__":
    unittest.main()
