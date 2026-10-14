import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.check_production_rebuild_formal_authorization_gate import (
    ACCEPTED_AUTHORIZATION_STATUS,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_REAL_READONLY_PREFLIGHT_PATH,
    DEFAULT_SNAPSHOT_CAPTURE_PATH,
    build_report,
)


FIXED_TIME = "2026-06-05T00:00:00+00:00"


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def snapshot_capture_report(
    status: str = "passed",
    reference: str | None = "qdrant-snapshot://collection/legal_knowledge/a.snapshot",
):
    return {
        "summary": {
            "snapshot_capture_status": status,
            "backup_or_snapshot_reference": reference,
            "backup_or_snapshot_reference_present": bool(reference),
        }
    }


def real_readonly_preflight_report(blockers=None, snapshot_reference_present: bool = True):
    return {
        "inputs": {
            "backup_or_snapshot_reference_present": snapshot_reference_present,
        },
        "summary": {
            "preflight_status": "blocked" if blockers else "passed",
            "blockers": ["authorization_record_not_accepted"] if blockers is None else blockers,
        },
    }


class ProductionRebuildFormalAuthorizationGateTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(
            DEFAULT_SNAPSHOT_CAPTURE_PATH,
            Path("tests/production_rebuild_live_preflight_snapshot_create_reference_capture_report.json"),
        )
        self.assertEqual(
            DEFAULT_REAL_READONLY_PREFLIGHT_PATH,
            Path("tests/production_rebuild_live_preflight_real_readonly_probe_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            Path("tests/production_rebuild_formal_authorization_gate_report.json"),
        )

    def test_current_saved_reports_block_only_on_formal_authorization(self):
        report = build_report(clock=lambda: FIXED_TIME)

        self.assertEqual(report["version"], "0.4.14.26")
        self.assertEqual(report["schema_kind"], "production_rebuild_formal_authorization_gate_report")
        self.assertEqual(report["summary"]["authorization_gate_status"], "blocked")
        self.assertEqual(report["summary"]["blockers"], ["authorization_record_not_accepted"])
        self.assertTrue(report["summary"]["backup_or_snapshot_reference_present"])
        self.assertFalse(report["summary"]["formal_authorization_accepted"])
        self.assertFalse(report["summary"]["production_rebuild_allowed"])
        self.assertEqual(
            report["authorization_gate"]["allowed_next_step"],
            "collect_formal_production_rebuild_authorization",
        )

    def test_accepts_only_explicit_status_and_reference(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            snapshot_path = Path(tmpdir) / "snapshot.json"
            preflight_path = Path(tmpdir) / "preflight.json"
            write_json(snapshot_path, snapshot_capture_report())
            write_json(preflight_path, real_readonly_preflight_report())

            report = build_report(
                snapshot_capture_path=snapshot_path,
                real_readonly_preflight_path=preflight_path,
                authorization_status=ACCEPTED_AUTHORIZATION_STATUS,
                authorization_reference="user-accepted-production-rebuild-2026-06-05",
                clock=lambda: FIXED_TIME,
            )

        self.assertEqual(report["summary"]["authorization_gate_status"], "passed")
        self.assertEqual(report["summary"]["blockers"], [])
        self.assertTrue(report["authorization_gate"]["formal_authorization_accepted"])
        self.assertFalse(report["summary"]["production_rebuild_allowed"])
        self.assertEqual(
            report["authorization_gate"]["allowed_next_step"],
            "run_fail_closed_live_preflight_with_accepted_authorization",
        )

    def test_missing_authorization_reference_is_blocked_even_when_status_accepted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            snapshot_path = Path(tmpdir) / "snapshot.json"
            preflight_path = Path(tmpdir) / "preflight.json"
            write_json(snapshot_path, snapshot_capture_report())
            write_json(preflight_path, real_readonly_preflight_report())

            report = build_report(
                snapshot_capture_path=snapshot_path,
                real_readonly_preflight_path=preflight_path,
                authorization_status=ACCEPTED_AUTHORIZATION_STATUS,
                authorization_reference=" ",
                clock=lambda: FIXED_TIME,
            )

        self.assertEqual(report["summary"]["authorization_gate_status"], "blocked")
        self.assertIn("authorization_record_not_accepted", report["summary"]["blockers"])

    def test_snapshot_missing_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            snapshot_path = Path(tmpdir) / "snapshot.json"
            preflight_path = Path(tmpdir) / "preflight.json"
            write_json(snapshot_path, snapshot_capture_report(reference=None))
            write_json(preflight_path, real_readonly_preflight_report())

            report = build_report(
                snapshot_capture_path=snapshot_path,
                real_readonly_preflight_path=preflight_path,
                authorization_status=ACCEPTED_AUTHORIZATION_STATUS,
                authorization_reference="user-accepted-production-rebuild-2026-06-05",
                clock=lambda: FIXED_TIME,
            )

        self.assertEqual(report["summary"]["authorization_gate_status"], "blocked")
        self.assertIn("backup_or_snapshot_reference_missing", report["summary"]["blockers"])

    def test_unexpected_preflight_blockers_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            snapshot_path = Path(tmpdir) / "snapshot.json"
            preflight_path = Path(tmpdir) / "preflight.json"
            write_json(snapshot_path, snapshot_capture_report())
            write_json(preflight_path, real_readonly_preflight_report(blockers=["qdrant_unreachable"]))

            report = build_report(
                snapshot_capture_path=snapshot_path,
                real_readonly_preflight_path=preflight_path,
                authorization_status=ACCEPTED_AUTHORIZATION_STATUS,
                authorization_reference="user-accepted-production-rebuild-2026-06-05",
                clock=lambda: FIXED_TIME,
            )

        self.assertEqual(report["summary"]["authorization_gate_status"], "blocked")
        self.assertIn("real_readonly_preflight_unexpected_blockers", report["summary"]["blockers"])

    def test_cli_allows_blocked_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "gate.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "tools/check_production_rebuild_formal_authorization_gate.py",
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

        self.assertEqual(report["version"], "0.4.14.26")
        self.assertEqual(report["summary"]["authorization_gate_status"], "blocked")

    def test_source_has_no_qdrant_rag_llm_eval_or_rebuild_execution_calls(self):
        source = Path("tools/check_production_rebuild_formal_authorization_gate.py").read_text(encoding="utf-8")

        for forbidden in [
            "get_qdrant_client",
            "qdrant_client",
            ".create_snapshot(",
            ".list_snapshots(",
            ".recover_snapshot(",
            ".delete_snapshot(",
            ".upsert(",
            ".create_collection(",
            ".delete_collection(",
            ".recreate_collection(",
            ".update_aliases(",
            "rag_query(",
            "OpenAI(",
            "run_eval(",
            "subprocess.run",
            "--write",
            "--rebuild",
            "--switch-collection",
        ]:
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
