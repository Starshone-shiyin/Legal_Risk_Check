import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.check_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate import (
    DEFAULT_FORBIDDEN_REPORT_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_RUNNER_PATH,
    DEFAULT_SCAFFOLD_REPORT_PATH,
    DEFAULT_TEST_PATH,
    build_report,
    render_markdown,
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def without_generated_at(payload: dict) -> dict:
    clone = copy.deepcopy(payload)
    clone.pop("generated_at", None)
    return clone


class ProductionRebuildLivePreflightRunnerMinimalImplementationScaffoldGateTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(
            DEFAULT_SCAFFOLD_REPORT_PATH,
            legacy_report_path("production_rebuild_live_preflight_runner_minimal_implementation_scaffold_report.json"),
        )
        self.assertEqual(DEFAULT_RUNNER_PATH, Path("tools/run_production_rebuild_live_preflight.py"))
        self.assertEqual(DEFAULT_TEST_PATH, Path("tests/test_production_rebuild_live_preflight_runner.py"))
        self.assertEqual(DEFAULT_FORBIDDEN_REPORT_PATH, Path("tests/production_rebuild_live_preflight_report.json"))
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate_report.json"),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate_v0.4.14.22.md"),
        )

    def test_real_scaffold_passes_gate_with_historical_scaffold_traceability(self):
        report = build_report()
        summary = report["summary"]

        self.assertEqual(report["version"], "0.4.14.22")
        self.assertEqual(
            report["schema_kind"],
            "production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate",
        )
        self.assertEqual(summary["status"], "passed")
        self.assertEqual(
            summary["allowed_next_step"],
            "historical_scaffold_gate_retained_for_traceability",
        )
        self.assertEqual(summary["check_count"], 13)
        self.assertEqual(summary["failure_count"], 0)
        self.assertEqual(summary["failed_checks"], [])
        self.assertTrue(summary["runner_file_created"])
        self.assertTrue(summary["runner_test_file_created"])
        self.assertTrue(summary["runner_report_created"])
        self.assertFalse(summary["live_preflight_run_allowed"])
        self.assertFalse(summary["qdrant_write_allowed"])
        self.assertFalse(summary["production_rebuild_allowed"])
        self.assertFalse(summary["authorization_granted"])

    def test_scaffold_report_status_or_permission_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scaffold.json"
            payload = copy.deepcopy(load_json(DEFAULT_SCAFFOLD_REPORT_PATH))
            payload["summary"]["status"] = "blocked"
            payload["summary"]["qdrant_write_allowed"] = True
            payload["guardrails"]["qdrant_write"] = "allowed"
            write_json(path, payload)

            report = build_report(scaffold_report_path=path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("scaffold_status", report["summary"]["failed_checks"])
        self.assertIn("scaffold_permissions_locked", report["summary"]["failed_checks"])
        self.assertIn("scaffold_guardrails_locked", report["summary"]["failed_checks"])

    def test_missing_runner_or_default_report_creation_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_runner = Path(tmpdir) / "missing_runner.py"
            forbidden_report = Path(tmpdir) / "production_rebuild_live_preflight_report.json"
            forbidden_report.write_text("{}", encoding="utf-8")

            report = build_report(runner_path=missing_runner, forbidden_report_path=forbidden_report)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("created_files_present", report["summary"]["failed_checks"])
        self.assertIn("historical_scaffold_report_declared_no_live_output", report["summary"]["failed_checks"])

    def test_forbidden_runner_import_or_text_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = Path(tmpdir) / "runner.py"
            runner.write_text(
                "from qdrant_client import QdrantClient\n"
                "def build_live_preflight_report():\n"
                "    return QdrantClient()\n",
                encoding="utf-8",
            )

            report = build_report(runner_path=runner)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("runner_imports_locked", report["summary"]["failed_checks"])
        self.assertIn("runner_forbidden_text_absent", report["summary"]["failed_checks"])
        self.assertIn("runner_core_contract_present", report["summary"]["failed_checks"])

    def test_mock_test_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = Path(tmpdir) / "test_runner.py"
            test_path.write_text("def test_placeholder():\n    pass\n", encoding="utf-8")

            report = build_report(test_path=test_path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("mock_only_tests_present", report["summary"]["failed_checks"])

    def test_cli_output_matches_builder_shape_and_utf8_markdown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "gate.json"
            summary = Path(tmpdir) / "gate.md"
            subprocess.run(
                [
                    sys.executable,
                    "tools/check_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate.py",
                    "--output",
                    str(output),
                    "--summary",
                    str(summary),
                ],
                check=True,
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
            )

            cli_report = load_json(output)
            cli_summary = summary.read_text(encoding="utf-8")

        self.assertEqual(without_generated_at(cli_report), without_generated_at(build_report()))
        self.assertIn("只 gate v0.4.14.21 最小 runner scaffold", cli_summary)
        self.assertIn("不访问或写入 Qdrant", cli_summary)
        self.assertIn("不执行 production rebuild", cli_summary)

    def test_markdown_documents_gate_boundary(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.14.22 Production Rebuild Live Preflight Runner Minimal Implementation Scaffold Gate", markdown)
        self.assertIn("不运行 live preflight", markdown)
        self.assertIn("不访问或写入 Qdrant", markdown)
        self.assertIn("不能直接运行 live preflight", markdown)


if __name__ == "__main__":
    unittest.main()
