import ast
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design import (
    DEFAULT_IMPLEMENTATION_DESIGN_GATE_PATH,
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


class ProductionRebuildLivePreflightRunnerMinimalImplementationScaffoldDesignTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(
            DEFAULT_IMPLEMENTATION_DESIGN_GATE_PATH,
            legacy_report_path("production_rebuild_live_preflight_runner_minimal_implementation_design_gate_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path(
                "production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_report.json"
            ),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_v0.4.14.19.md"),
        )

    def test_real_gate_opens_scaffold_design_gate_only(self):
        report = build_report()
        summary = report["summary"]
        design = report["scaffold_design"]

        self.assertEqual(report["version"], "0.4.14.19")
        self.assertEqual(
            report["schema_kind"],
            "production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design",
        )
        self.assertEqual(summary["status"], "ready_for_minimal_implementation_scaffold_design_gate")
        self.assertEqual(
            summary["allowed_next_step"],
            "production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate",
        )
        self.assertEqual(summary["blockers"], [])
        self.assertEqual(summary["scaffold_file_count"], 3)
        self.assertEqual(summary["placeholder_test_count"], 6)
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
        self.assertTrue(all(item["created_now"] is False for item in design["files"]))
        self.assertIn(
            "tests/production_rebuild_live_preflight_report.json",
            {item["path"] for item in design["files"]},
        )

    def test_gate_status_or_next_step_drift_blocks_design(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "gate.json"
            payload = copy.deepcopy(load_json(DEFAULT_IMPLEMENTATION_DESIGN_GATE_PATH))
            payload["summary"]["status"] = "failed"
            payload["summary"]["allowed_next_step"] = "production_rebuild_live_preflight_runner"
            write_json(path, payload)

            report = build_report(implementation_design_gate_path=path)

        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("implementation_design_gate_status_mismatch", report["summary"]["blockers"])
        self.assertIn("implementation_design_gate_next_step_mismatch", report["summary"]["blockers"])

    def test_gate_permission_drift_blocks_design(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "gate.json"
            payload = copy.deepcopy(load_json(DEFAULT_IMPLEMENTATION_DESIGN_GATE_PATH))
            payload["summary"]["runner_file_created"] = True
            payload["summary"]["qdrant_access_allowed"] = True
            payload["summary"]["failure_count"] = 1
            payload["summary"]["failed_checks"] = ["future_files_contract"]
            write_json(path, payload)

            report = build_report(implementation_design_gate_path=path)

        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("implementation_design_gate_runner_file_created_mismatch", report["summary"]["blockers"])
        self.assertIn("implementation_design_gate_qdrant_access_allowed_mismatch", report["summary"]["blockers"])
        self.assertIn("implementation_design_gate_failure_drift", report["summary"]["blockers"])

    def test_forbidden_output_key_drift_blocks_design(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "gate.json"
            payload = copy.deepcopy(load_json(DEFAULT_IMPLEMENTATION_DESIGN_GATE_PATH))
            payload["commands"] = []
            payload["nested"] = {"execution_commands": []}
            write_json(path, payload)

            report = build_report(implementation_design_gate_path=path)

        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("implementation_design_gate_forbidden_output_key_present", report["summary"]["blockers"])

    def test_forbidden_output_key_detector_is_generic(self):
        payload = {"nested": [{"commands": []}, {"authorized_actions": ["x"]}]}

        self.assertEqual(forbidden_output_keys(payload), ["authorized_actions", "commands"])
        self.assertEqual(forbidden_output_keys(build_report()), [])

    def test_cli_output_matches_builder_shape_and_utf8_markdown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "design.json"
            summary = Path(tmpdir) / "design.md"
            subprocess.run(
                [
                    sys.executable,
                    "tools/build_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design.py",
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
        self.assertIn("只设计未来 runner scaffold", cli_summary)
        self.assertIn("不创建 runner 文件", cli_summary)
        self.assertIn("scaffold_design_gate", cli_summary)

    def test_source_has_no_runtime_service_imports_or_calls(self):
        source = Path(
            "tools/build_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design.py"
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
        self.assertNotIn("--qdrant-url", source)

    def test_markdown_documents_design_boundary(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.14.19 Production Rebuild Live Preflight Runner Minimal Implementation Scaffold Design", markdown)
        self.assertIn("不创建 runner 文件", markdown)
        self.assertIn("不运行 live preflight", markdown)
        self.assertIn("不访问或写入 Qdrant", markdown)
        self.assertIn("scaffold_design_gate", markdown)


if __name__ == "__main__":
    unittest.main()
