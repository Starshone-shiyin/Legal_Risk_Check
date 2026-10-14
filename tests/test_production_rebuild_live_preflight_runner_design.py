import ast
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_production_rebuild_live_preflight_runner_design import (
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_READINESS_CUTOFF_PATH,
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


class ProductionRebuildLivePreflightRunnerDesignTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(
            DEFAULT_READINESS_CUTOFF_PATH,
            legacy_report_path("production_rebuild_readiness_cutoff_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("production_rebuild_live_preflight_runner_design_report.json"),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/production_rebuild_live_preflight_runner_design_v0.4.14.15.md"),
        )

    def test_real_cutoff_opens_design_gate_only(self):
        report = build_report()
        summary = report["summary"]
        contract = report["future_runner_contract"]

        self.assertEqual(report["version"], "0.4.14.15")
        self.assertEqual(report["schema_kind"], "production_rebuild_live_preflight_runner_design")
        self.assertEqual(summary["status"], "ready_for_live_preflight_runner_design_gate")
        self.assertEqual(summary["allowed_next_step"], "production_rebuild_live_preflight_runner_design_gate")
        self.assertEqual(summary["blockers"], [])
        self.assertFalse(summary["runner_created"])
        self.assertFalse(summary["runner_executed"])
        self.assertFalse(summary["live_preflight_run_allowed"])
        self.assertFalse(summary["qdrant_write_allowed"])
        self.assertFalse(summary["production_rebuild_allowed"])
        self.assertFalse(summary["authorization_granted"])
        self.assertEqual(summary["full_eval"], "not_run")
        self.assertEqual(summary["future_input_count"], 6)
        self.assertEqual(summary["preflight_check_count"], 8)
        self.assertEqual(summary["blocking_condition_count"], 8)
        self.assertTrue(contract["must_run_read_only_before_any_write"])
        self.assertTrue(contract["must_require_formal_authorization_before_execution"])
        self.assertTrue(contract["must_fail_closed_on_unknown_status"])
        self.assertFalse(report["scaffold_cutoff_policy"]["continue_input_or_importer_scaffold_chain"])

    def test_cutoff_status_or_next_step_drift_blocks_design(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "cutoff.json"
            payload = copy.deepcopy(load_json(DEFAULT_READINESS_CUTOFF_PATH))
            payload["summary"]["status"] = "blocked"
            payload["summary"]["allowed_next_step"] = "human_rebuild_authorization_record_input_importer_design"
            write_json(path, payload)

            report = build_report(readiness_cutoff_path=path)

        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("readiness_cutoff_status_mismatch", report["summary"]["blockers"])
        self.assertIn("readiness_cutoff_next_step_mismatch", report["summary"]["blockers"])

    def test_cutoff_permission_drift_blocks_design(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "cutoff.json"
            payload = copy.deepcopy(load_json(DEFAULT_READINESS_CUTOFF_PATH))
            payload["summary"]["qdrant_write_allowed"] = True
            payload["summary"]["production_rebuild_allowed"] = True
            payload["summary"]["authorization_granted"] = True
            payload["summary"]["stop_scaffold_expansion"] = False
            write_json(path, payload)

            report = build_report(readiness_cutoff_path=path)

        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("readiness_cutoff_qdrant_write_allowed_mismatch", report["summary"]["blockers"])
        self.assertIn("readiness_cutoff_production_rebuild_allowed_mismatch", report["summary"]["blockers"])
        self.assertIn("readiness_cutoff_authorization_granted_mismatch", report["summary"]["blockers"])
        self.assertIn("readiness_cutoff_stop_scaffold_expansion_mismatch", report["summary"]["blockers"])

    def test_forbidden_output_key_drift_blocks_design(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "cutoff.json"
            payload = copy.deepcopy(load_json(DEFAULT_READINESS_CUTOFF_PATH))
            payload["commands"] = ["do not do this"]
            payload["nested"] = {"authorized_actions": ["write Qdrant"]}
            write_json(path, payload)

            report = build_report(readiness_cutoff_path=path)

        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("readiness_cutoff_forbidden_output_key_present", report["summary"]["blockers"])

    def test_forbidden_output_key_detector_is_generic(self):
        payload = {"nested": [{"commands": []}, {"ready_to_apply": True}]}

        self.assertEqual(forbidden_output_keys(payload), ["commands", "ready_to_apply"])
        self.assertEqual(forbidden_output_keys(build_report()), [])

    def test_cli_output_matches_builder_shape_and_utf8_markdown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "design.json"
            summary = Path(tmpdir) / "design.md"
            subprocess.run(
                [
                    sys.executable,
                    "tools/build_production_rebuild_live_preflight_runner_design.py",
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
        self.assertIn("最小契约", cli_summary)
        self.assertIn("不访问或写入 Qdrant", cli_summary)
        self.assertIn("production_rebuild_live_preflight_runner_design_gate", cli_summary)

    def test_source_has_no_runtime_service_imports_or_calls(self):
        source = Path("tools/build_production_rebuild_live_preflight_runner_design.py").read_text(encoding="utf-8")
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

    def test_markdown_documents_design_boundary(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.14.15 Production Rebuild Live Preflight Runner Design", markdown)
        self.assertIn("不创建 runner", markdown)
        self.assertIn("不运行 live preflight", markdown)
        self.assertIn("不访问或写入 Qdrant", markdown)
        self.assertIn("live preflight runner design gate", markdown)


if __name__ == "__main__":
    unittest.main()
