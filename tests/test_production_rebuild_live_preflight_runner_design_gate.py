import ast
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.check_production_rebuild_live_preflight_runner_design_gate import (
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


class ProductionRebuildLivePreflightRunnerDesignGateTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(
            DEFAULT_DESIGN_PATH,
            legacy_report_path("production_rebuild_live_preflight_runner_design_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("production_rebuild_live_preflight_runner_design_gate_report.json"),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/production_rebuild_live_preflight_runner_design_gate_v0.4.14.16.md"),
        )

    def test_real_design_passes_and_opens_minimal_implementation_design_only(self):
        report = build_report()
        summary = report["summary"]

        self.assertEqual(report["version"], "0.4.14.16")
        self.assertEqual(report["schema_kind"], "production_rebuild_live_preflight_runner_design_gate")
        self.assertEqual(summary["status"], "passed")
        self.assertEqual(
            summary["allowed_next_step"],
            "production_rebuild_live_preflight_runner_minimal_implementation_design",
        )
        self.assertEqual(summary["check_count"], 15)
        self.assertEqual(summary["failure_count"], 0)
        self.assertEqual(summary["failed_checks"], [])
        self.assertFalse(summary["runner_created"])
        self.assertFalse(summary["runner_executed"])
        self.assertFalse(summary["live_preflight_run_allowed"])
        self.assertFalse(summary["qdrant_write_allowed"])
        self.assertFalse(summary["production_rebuild_allowed"])
        self.assertFalse(summary["authorization_granted"])
        self.assertEqual(summary["full_eval"], "not_run")

    def test_design_status_or_lineage_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "design.json"
            payload = copy.deepcopy(load_json(DEFAULT_DESIGN_PATH))
            payload["summary"]["status"] = "blocked"
            payload["inputs"]["readiness_cutoff"]["version"] = "0.4.14.13"
            write_json(path, payload)

            report = build_report(design_path=path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("design_status", report["summary"]["failed_checks"])
        self.assertIn("lineage_cutoff_only", report["summary"]["failed_checks"])

    def test_contract_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "design.json"
            payload = copy.deepcopy(load_json(DEFAULT_DESIGN_PATH))
            payload["future_runner_contract"]["future_inputs"].pop()
            payload["future_runner_contract"]["preflight_checks"].append("extra_check")
            payload["future_runner_contract"]["output_fields"].remove("qdrant_write_allowed")
            payload["future_runner_contract"]["blocking_conditions"].remove("maintenance_window_inactive")
            write_json(path, payload)

            report = build_report(design_path=path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("future_inputs_contract", report["summary"]["failed_checks"])
        self.assertIn("preflight_checks_contract", report["summary"]["failed_checks"])
        self.assertIn("output_fields_contract", report["summary"]["failed_checks"])
        self.assertIn("blocking_conditions_contract", report["summary"]["failed_checks"])

    def test_permission_or_scaffold_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "design.json"
            payload = copy.deepcopy(load_json(DEFAULT_DESIGN_PATH))
            payload["summary"]["runner_created"] = True
            payload["summary"]["qdrant_write_allowed"] = True
            payload["guardrails"]["qdrant_write"] = "allowed"
            payload["scaffold_cutoff_policy"]["continue_input_or_importer_scaffold_chain"] = True
            write_json(path, payload)

            report = build_report(design_path=path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("summary_permissions_locked", report["summary"]["failed_checks"])
        self.assertIn("guardrails_locked", report["summary"]["failed_checks"])
        self.assertIn("scaffold_cutoff_policy", report["summary"]["failed_checks"])

    def test_forbidden_output_key_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "design.json"
            payload = copy.deepcopy(load_json(DEFAULT_DESIGN_PATH))
            payload["commands"] = []
            payload["nested"] = {"rebuild_steps": []}
            write_json(path, payload)

            report = build_report(design_path=path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("forbidden_output_keys_absent", report["summary"]["failed_checks"])

    def test_forbidden_output_key_detector_is_generic(self):
        payload = {"nested": [{"commands": []}, {"authorized_actions": ["x"]}]}

        self.assertEqual(forbidden_output_keys(payload), ["authorized_actions", "commands"])
        self.assertEqual(forbidden_output_keys(build_report()), [])

    def test_cli_output_matches_builder_shape_and_utf8_markdown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "gate.json"
            summary = Path(tmpdir) / "gate.md"
            subprocess.run(
                [
                    sys.executable,
                    "tools/check_production_rebuild_live_preflight_runner_design_gate.py",
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
        self.assertIn("只 gate v0.4.14.15", cli_summary)
        self.assertIn("不访问或写入 Qdrant", cli_summary)
        self.assertIn("minimal_implementation_design", cli_summary)

    def test_source_has_no_runtime_service_imports_or_calls(self):
        source = Path("tools/check_production_rebuild_live_preflight_runner_design_gate.py").read_text(encoding="utf-8")
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

        self.assertIn("v0.4.14.16 Production Rebuild Live Preflight Runner Design Gate", markdown)
        self.assertIn("不创建 runner", markdown)
        self.assertIn("不运行 live preflight", markdown)
        self.assertIn("不访问或写入 Qdrant", markdown)
        self.assertIn("minimal_implementation_design", markdown)


if __name__ == "__main__":
    unittest.main()
