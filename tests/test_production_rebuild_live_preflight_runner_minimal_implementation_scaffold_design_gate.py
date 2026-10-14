import ast
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.check_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate import (
    DEFAULT_DESIGN_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    build_report,
    forbidden_output_keys,
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


class ProductionRebuildLivePreflightRunnerMinimalImplementationScaffoldDesignGateTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(
            DEFAULT_DESIGN_PATH,
            legacy_report_path(
                "production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_report.json"
            ),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path(
                "production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate_report.json"
            ),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path(
                "docs/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate_v0.4.14.20.md"
            ),
        )

    def test_real_design_passes_and_opens_minimal_scaffold_only(self):
        report = build_report()
        summary = report["summary"]

        self.assertEqual(report["version"], "0.4.14.20")
        self.assertEqual(
            report["schema_kind"],
            "production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate",
        )
        self.assertEqual(summary["status"], "passed")
        self.assertEqual(
            summary["allowed_next_step"],
            "production_rebuild_live_preflight_runner_minimal_implementation_scaffold",
        )
        self.assertEqual(summary["check_count"], 14)
        self.assertEqual(summary["failure_count"], 0)
        self.assertEqual(summary["failed_checks"], [])
        self.assertFalse(summary["runner_file_created"])
        self.assertFalse(summary["runner_test_file_created"])
        self.assertFalse(summary["runner_report_created"])
        self.assertFalse(summary["runner_created"])
        self.assertFalse(summary["runner_executed"])
        self.assertFalse(summary["live_preflight_run_allowed"])
        self.assertFalse(summary["qdrant_access_allowed"])
        self.assertFalse(summary["qdrant_write_allowed"])
        self.assertFalse(summary["production_rebuild_allowed"])
        self.assertFalse(summary["authorization_granted"])
        self.assertEqual(summary["full_eval"], "not_run")
        self.assertFalse(summary["runner_file_created"])
        self.assertFalse(summary["runner_test_file_created"])
        self.assertIn(
            "tests/production_rebuild_live_preflight_report.json",
            {item["path"] for item in load_json(DEFAULT_DESIGN_PATH)["scaffold_design"]["files"]},
        )

    def test_status_lineage_or_blocker_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "design.json"
            payload = copy.deepcopy(load_json(DEFAULT_DESIGN_PATH))
            payload["summary"]["status"] = "blocked"
            payload["summary"]["blockers"] = ["unexpected"]
            payload["inputs"]["implementation_design_gate"]["version"] = "0.4.14.17"
            write_json(path, payload)

            report = build_report(design_path=path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("design_status", report["summary"]["failed_checks"])
        self.assertIn("design_blockers_empty", report["summary"]["failed_checks"])
        self.assertIn("lineage_implementation_design_gate_only", report["summary"]["failed_checks"])

    def test_scaffold_contract_or_file_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "design.json"
            payload = copy.deepcopy(load_json(DEFAULT_DESIGN_PATH))
            payload["scaffold_design"]["files"][0]["created_now"] = True
            payload["scaffold_design"]["contract"]["no_write_methods_exposed"] = False
            payload["scaffold_design"]["placeholder_tests"].pop()
            payload["scaffold_design"]["forbidden_scaffold_content"].remove("real endpoint default")
            write_json(path, payload)

            report = build_report(design_path=path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("scaffold_files_contract", report["summary"]["failed_checks"])
        self.assertIn("scaffold_contract_locked", report["summary"]["failed_checks"])
        self.assertIn("placeholder_tests_locked", report["summary"]["failed_checks"])
        self.assertIn("forbidden_scaffold_content_locked", report["summary"]["failed_checks"])

    def test_permission_or_guardrail_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "design.json"
            payload = copy.deepcopy(load_json(DEFAULT_DESIGN_PATH))
            payload["summary"]["runner_file_created"] = True
            payload["summary"]["qdrant_write_allowed"] = True
            payload["guardrails"]["qdrant_write"] = "allowed"
            write_json(path, payload)

            report = build_report(design_path=path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("summary_permissions_locked", report["summary"]["failed_checks"])
        self.assertIn("guardrails_locked", report["summary"]["failed_checks"])

    def test_forbidden_output_key_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "design.json"
            payload = copy.deepcopy(load_json(DEFAULT_DESIGN_PATH))
            payload["commands"] = []
            payload["nested"] = {"ready_to_apply": True}
            write_json(path, payload)

            report = build_report(design_path=path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("forbidden_output_keys_absent", report["summary"]["failed_checks"])

    def test_forbidden_output_key_detector_is_generic(self):
        payload = {"nested": [{"commands": []}, {"qdrant_operation_log": []}]}

        self.assertEqual(forbidden_output_keys(payload), ["commands", "qdrant_operation_log"])
        self.assertEqual(forbidden_output_keys(build_report()), [])

    def test_cli_output_matches_builder_shape_and_utf8_markdown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "gate.json"
            summary = Path(tmpdir) / "gate.md"
            subprocess.run(
                [
                    sys.executable,
                    "tools/check_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate.py",
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
        self.assertIn("只 gate v0.4.14.19 scaffold design", cli_summary)
        self.assertIn("不创建 runner 文件", cli_summary)
        self.assertIn("不访问或写入 Qdrant", cli_summary)

    def test_source_has_no_runtime_service_imports_or_calls(self):
        source = Path(
            "tools/check_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate.py"
        ).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            if isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)

        forbidden_imports = {"qdrant_client", "openai", "src.rag.retriever", "src.rag.ingestion", "run_rag_eval"}
        self.assertTrue(forbidden_imports.isdisjoint(imports))
        for forbidden_call in ["rag_query(", "QdrantClient(", "OpenAI(", "run_eval("]:
            self.assertNotIn(forbidden_call, source)

    def test_markdown_documents_gate_boundary(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.14.20 Production Rebuild Live Preflight Runner Minimal Implementation Scaffold Design Gate", markdown)
        self.assertIn("不创建 runner 文件", markdown)
        self.assertIn("不运行 live preflight", markdown)
        self.assertIn("不访问或写入 Qdrant", markdown)
        self.assertIn("minimal_implementation_scaffold", markdown)


if __name__ == "__main__":
    unittest.main()
