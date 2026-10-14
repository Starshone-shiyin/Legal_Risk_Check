import ast
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_production_rebuild_readiness_cutoff import (
    DEFAULT_AUTH_DESIGN_PATH,
    DEFAULT_AUTH_GATE_PATH,
    DEFAULT_DRY_RUN_GATE_PATH,
    DEFAULT_DRY_RUN_PATH,
    DEFAULT_EXECUTION_DESIGN_GATE_PATH,
    DEFAULT_EXECUTION_DESIGN_PATH,
    DEFAULT_FORM_SCAFFOLD_GATE_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_PLANNING_CLOSEOUT_PATH,
    DEFAULT_PROJECT_HEALTH_PATH,
    DEFAULT_RUNBOOK_PATH,
    DEFAULT_SOURCE_PATCH_PATH,
    DEFAULT_WORKSHEET_GATE_PATH,
    DEFAULT_WORKSHEET_PATH,
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


class ProductionRebuildReadinessCutoffTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(DEFAULT_SOURCE_PATCH_PATH, legacy_report_path("ingestion_metadata_source_patch_report.json"))
        self.assertEqual(
            DEFAULT_DRY_RUN_PATH,
            legacy_report_path("ingestion_metadata_patch_post_patch_rebuild_dry_run_report.json"),
        )
        self.assertEqual(
            DEFAULT_DRY_RUN_GATE_PATH,
            legacy_report_path("ingestion_metadata_patch_post_patch_rebuild_dry_run_gate_report.json"),
        )
        self.assertEqual(DEFAULT_AUTH_DESIGN_PATH, legacy_report_path("rebuild_authorization_design_report.json"))
        self.assertEqual(DEFAULT_AUTH_GATE_PATH, legacy_report_path("rebuild_authorization_design_gate_report.json"))
        self.assertEqual(DEFAULT_WORKSHEET_PATH, legacy_report_path("human_rebuild_authorization_worksheet_report.json"))
        self.assertEqual(
            DEFAULT_WORKSHEET_GATE_PATH,
            legacy_report_path("human_rebuild_authorization_worksheet_gate_report.json"),
        )
        self.assertEqual(DEFAULT_RUNBOOK_PATH, legacy_report_path("rebuild_runbook_preflight_contract_report.json"))
        self.assertEqual(
            DEFAULT_PLANNING_CLOSEOUT_PATH,
            legacy_report_path("ingestion_metadata_rebuild_planning_series_closeout_report.json"),
        )
        self.assertEqual(DEFAULT_EXECUTION_DESIGN_PATH, legacy_report_path("production_rebuild_execution_design_report.json"))
        self.assertEqual(
            DEFAULT_EXECUTION_DESIGN_GATE_PATH,
            legacy_report_path("production_rebuild_execution_design_gate_report.json"),
        )
        self.assertEqual(
            DEFAULT_FORM_SCAFFOLD_GATE_PATH,
            legacy_report_path("human_rebuild_authorization_record_input_form_scaffold_gate_report.json"),
        )
        self.assertEqual(DEFAULT_PROJECT_HEALTH_PATH, legacy_report_path("project_health_check_report.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("production_rebuild_readiness_cutoff_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/production_rebuild_readiness_cutoff_v0.4.14.14.md"))

    def test_real_saved_reports_cut_off_scaffold_and_open_preflight_design_only(self):
        report = build_report()
        summary = report["summary"]
        execution = report["execution_readiness"]
        cutoff = report["engineering_cutoff_decision"]

        self.assertEqual(report["version"], "0.4.14.14")
        self.assertEqual(report["schema_kind"], "production_rebuild_readiness_cutoff")
        self.assertEqual(summary["status"], "ready_for_live_preflight_runner_design_cutoff")
        self.assertEqual(summary["allowed_next_step"], "production_rebuild_live_preflight_runner_design")
        self.assertTrue(summary["stop_scaffold_expansion"])
        self.assertEqual(summary["source_report_count"], 13)
        self.assertEqual(summary["missing_ready_flags"], [])
        self.assertEqual(summary["blockers"], [])
        self.assertFalse(summary["live_preflight_run_allowed"])
        self.assertFalse(summary["qdrant_write_allowed"])
        self.assertFalse(summary["production_rebuild_allowed"])
        self.assertFalse(summary["authorization_granted"])
        self.assertEqual(summary["full_eval"], "not_run")
        self.assertEqual(cutoff["status"], "stop_input_scaffold_expansion")
        self.assertFalse(cutoff["further_input_or_importer_scaffold_versions_recommended"])
        self.assertTrue(execution["live_preflight_runner_design_ready"])
        self.assertFalse(execution["live_preflight_run_allowed_now"])
        self.assertFalse(execution["production_rebuild_allowed_now"])
        self.assertFalse(execution["qdrant_write_allowed_now"])
        self.assertTrue(execution["formal_authorization_required_before_execution"])
        self.assertIn("formal_human_authorization_record_not_created_or_accepted", execution["execution_blockers"])

    def test_readiness_flags_lock_source_patch_and_dry_run_evidence(self):
        flags = build_report()["readiness_flags"]

        self.assertTrue(flags["source_patch_completed"])
        self.assertTrue(flags["post_patch_dry_run_passed"])
        self.assertTrue(flags["expected_id_drift_accounted"])
        self.assertTrue(flags["forbidden_drift_absent"])
        self.assertTrue(flags["authorization_chain_gated"])
        self.assertTrue(flags["execution_design_gated"])
        self.assertTrue(flags["input_scaffold_chain_gated"])
        self.assertTrue(flags["project_health_passed"])

    def test_source_patch_or_dry_run_drift_blocks_cutoff(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            source_patch = copy.deepcopy(load_json(DEFAULT_SOURCE_PATCH_PATH))
            dry_run = copy.deepcopy(load_json(DEFAULT_DRY_RUN_PATH))
            source_patch_path = tmp / "source_patch.json"
            dry_run_path = tmp / "dry_run.json"
            source_patch["summary"]["implementation_completed"] = False
            dry_run["summary"]["expected_id_drift_rows"] = 0
            dry_run["summary"]["forbidden_drift_count"] = 1
            write_json(source_patch_path, source_patch)
            write_json(dry_run_path, dry_run)

            report = build_report(source_patch_path=source_patch_path, dry_run_path=dry_run_path)

        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("source_patch_completed", report["summary"]["missing_ready_flags"])
        self.assertIn("expected_id_drift_accounted", report["summary"]["missing_ready_flags"])
        self.assertIn("forbidden_drift_absent", report["summary"]["missing_ready_flags"])

    def test_authorization_or_execution_gate_drift_blocks_cutoff(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            auth_gate = copy.deepcopy(load_json(DEFAULT_AUTH_GATE_PATH))
            execution_gate = copy.deepcopy(load_json(DEFAULT_EXECUTION_DESIGN_GATE_PATH))
            form_gate = copy.deepcopy(load_json(DEFAULT_FORM_SCAFFOLD_GATE_PATH))
            auth_gate_path = tmp / "auth_gate.json"
            execution_gate_path = tmp / "execution_gate.json"
            form_gate_path = tmp / "form_gate.json"
            auth_gate["summary"]["status"] = "failed"
            execution_gate["summary"]["status"] = "failed"
            form_gate["summary"]["status"] = "failed"
            form_gate["summary"]["authorization_granted"] = True
            write_json(auth_gate_path, auth_gate)
            write_json(execution_gate_path, execution_gate)
            write_json(form_gate_path, form_gate)

            report = build_report(
                auth_gate_path=auth_gate_path,
                execution_design_gate_path=execution_gate_path,
                form_scaffold_gate_path=form_gate_path,
            )

        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("authorization_gate_status_mismatch", report["summary"]["blockers"])
        self.assertIn("execution_design_gate_status_mismatch", report["summary"]["blockers"])
        self.assertIn("input_form_scaffold_gate_status_mismatch", report["summary"]["blockers"])
        self.assertIn("input_form_scaffold_gate_authorization_granted_mismatch", report["summary"]["blockers"])
        self.assertIn("authorization_chain_gated", report["summary"]["missing_ready_flags"])
        self.assertIn("execution_design_gated", report["summary"]["missing_ready_flags"])
        self.assertIn("input_scaffold_chain_gated", report["summary"]["missing_ready_flags"])

    def test_project_health_drift_blocks_cutoff(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "project_health.json"
            payload = copy.deepcopy(load_json(DEFAULT_PROJECT_HEALTH_PATH))
            payload["summary"]["status"] = "failed"
            payload["summary"]["failed_checks"] = 1
            write_json(path, payload)

            report = build_report(project_health_path=path)

        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("project_health_status_mismatch", report["summary"]["blockers"])
        self.assertIn("project_health_passed", report["summary"]["missing_ready_flags"])

    def test_project_health_version_drift_blocks_cutoff(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "project_health.json"
            payload = copy.deepcopy(load_json(DEFAULT_PROJECT_HEALTH_PATH))
            payload["version"] = "0.4.14.13"
            write_json(path, payload)

            report = build_report(project_health_path=path)

        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("project_health_version_mismatch", report["summary"]["blockers"])

    def test_forbidden_output_key_drift_blocks_cutoff(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "form_gate.json"
            payload = copy.deepcopy(load_json(DEFAULT_FORM_SCAFFOLD_GATE_PATH))
            payload["commands"] = []
            payload["nested"] = {"authorized_actions": ["write Qdrant"]}
            write_json(path, payload)

            report = build_report(form_scaffold_gate_path=path)

        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("input_form_scaffold_gate_forbidden_output_key_present", report["summary"]["blockers"])

    def test_forbidden_output_key_detector_is_generic(self):
        payload = {"nested": [{"commands": []}, {"authorized_actions": ["write Qdrant"]}]}

        self.assertEqual(forbidden_output_keys(payload), ["authorized_actions", "commands"])
        self.assertEqual(forbidden_output_keys(build_report()), [])

    def test_cli_output_matches_builder_shape_and_utf8_markdown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "cutoff.json"
            summary = Path(tmpdir) / "cutoff.md"
            subprocess.run(
                [
                    sys.executable,
                    "tools/build_production_rebuild_readiness_cutoff.py",
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
        self.assertIn("收口判断", cli_summary)
        self.assertIn("停止继续堆 input/importer scaffold 报告", cli_summary)
        self.assertIn("不代表已经允许 live preflight", cli_summary)

    def test_source_has_no_runtime_service_imports_or_calls(self):
        source = Path("tools/build_production_rebuild_readiness_cutoff.py").read_text(encoding="utf-8")
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

    def test_markdown_documents_cutoff_boundary(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.14.14 Production Rebuild Readiness Cutoff", markdown)
        self.assertIn("不再继续扩 input/importer scaffold", markdown)
        self.assertIn("不访问或写入 Qdrant", markdown)
        self.assertIn("不执行 rebuild", markdown)
        self.assertIn("production_rebuild_live_preflight_runner_design", markdown)


if __name__ == "__main__":
    unittest.main()
