import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.run_project_health_check import (
    advisory_boundary_checks,
    artifact_index_check,
    build_report,
    encoding_hygiene_report_check,
    layout_compatibility_check,
    layout_helper_pilot_checks,
    LAYOUT_HELPER_PILOT_DEFAULTS,
    dry_run_artifact_contract_check,
    offline_pattern_checks,
    report_presence_checks,
    SCAFFOLD_ALLOWED_FILES,
    scaffold_directory_checks,
    scaffold_purity_check,
    test_index_consistency_report_check,
    tool_index_check,
    tool_index_consistency_report_check,
    artifact_index_consistency_report_check,
    layout_migration_readiness_report_check,
    maintenance_closeout_report_check,
    VERSION,
)


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class ProjectHealthCheckTest(unittest.TestCase):
    def test_advisory_boundary_rejects_importable_manual_review_keys(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "advisory.json"
            write_json(
                path,
                {
                    "advisory_packet_only": True,
                    "contains_completed_manual_decisions": False,
                    "summary": {"completed_manual_decisions": 0},
                    "cards": [{"reviewer_input_template": {"decision": "confirm_diagnostic_issue"}}],
                },
            )

            result = advisory_boundary_checks([path])[0]

        self.assertEqual(result["status"], "failed")
        self.assertIn("contains_importable_or_completed_review_keys", result["errors"])
        self.assertEqual(result["matched_forbidden_keys"]["reviewer_input_template"], 1)
        self.assertEqual(result["matched_forbidden_keys"]["decision"], 1)

    def test_offline_pattern_scan_blocks_rag_or_backend_calls(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "tool.py"
            path.write_text("def run():\n    return rag_query('x')\n", encoding="utf-8")

            result = offline_pattern_checks([path])[0]

        self.assertEqual(result["status"], "failed")
        self.assertIn("rag_query(", result["matches"])

    def test_report_presence_requires_json_object(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "report.json"
            path.write_text("[]", encoding="utf-8")

            result = report_presence_checks([path])[0]

        self.assertEqual(result["status"], "failed")
        self.assertTrue(result["present"])

    def test_scaffold_directory_checks_require_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            directory_path = root / "ready"
            file_path = root / "file_marker"
            missing_path = root / "missing"
            directory_path.mkdir()
            file_path.write_text("not a directory", encoding="utf-8")

            results = scaffold_directory_checks([directory_path, file_path, missing_path])

        self.assertEqual(results[0]["status"], "passed")
        self.assertTrue(results[0]["present"])
        self.assertTrue(results[0]["is_directory"])
        self.assertEqual(results[1]["status"], "failed")
        self.assertTrue(results[1]["present"])
        self.assertFalse(results[1]["is_directory"])
        self.assertEqual(results[2]["status"], "failed")
        self.assertFalse(results[2]["present"])
        self.assertFalse(results[2]["is_directory"])

    def test_scaffold_purity_rejects_unexpected_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            scaffold_root = root / "reports" / "eval"
            allowed_file = scaffold_root / ".gitkeep"
            unexpected_file = scaffold_root / "migrated_report.json"
            allowed_file.parent.mkdir(parents=True)
            allowed_file.write_text("", encoding="utf-8")
            unexpected_file.write_text("{}", encoding="utf-8")

            result = scaffold_purity_check([scaffold_root], {allowed_file})

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["missing_roots"], [])
        self.assertIn(str(unexpected_file), result["unexpected_files"])

    def test_artifact_index_check_requires_key_anchors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "project_artifact_index.md"
            path.write_text("tests/rag_eval_report.json\nreports/eval\n", encoding="utf-8")

            result = artifact_index_check(
                path,
                [
                    "tests/rag_eval_report.json",
                    "tests/evidence_alignment_report.json",
                    "reports/eval",
                ],
            )

        self.assertEqual(result["status"], "failed")
        self.assertTrue(result["present"])
        self.assertEqual(result["missing_anchors"], ["tests/evidence_alignment_report.json"])

    def test_tool_index_check_requires_key_entrypoint_and_boundary_anchors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "project_tool_index.md"
            path.write_text("tools/*.py\ntools/run_rag_eval.py\nfull eval\n", encoding="utf-8")

            result = tool_index_check(
                path,
                [
                    "tools/*.py",
                    "tools/run_rag_eval.py",
                    "tools/check_evidence_alignment.py",
                    "Qdrant",
                    "LLM",
                    "full eval",
                ],
            )

        self.assertEqual(result["status"], "failed")
        self.assertTrue(result["present"])
        self.assertEqual(result["missing_anchors"], ["tools/check_evidence_alignment.py", "Qdrant", "LLM"])

    def test_layout_compatibility_keeps_legacy_paths_authoritative(self):
        result = layout_compatibility_check([
            ("tests/rag_eval_report.json", "eval"),
            ("tests/manual_review_prescreen_report.json", "manual_review"),
        ])

        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["contract"]["legacy_report_paths_authoritative"], True)
        self.assertEqual(result["contract"]["automatic_migration"], False)
        self.assertEqual(result["resolutions"][0]["selected_source"], "legacy_tests")
        self.assertEqual(Path(result["resolutions"][0]["selected_path"]), Path("tests/rag_eval_report.json"))
        self.assertEqual(
            Path(result["resolutions"][1]["future_path"]),
            Path("reports/manual_review/manual_review_prescreen_report.json"),
        )

    def test_layout_helper_pilot_defaults_remain_legacy_tests_paths(self):
        results = layout_helper_pilot_checks(LAYOUT_HELPER_PILOT_DEFAULTS)

        self.assertTrue(results)
        self.assertTrue(all(result["status"] == "passed" for result in results))
        self.assertTrue(all(result["uses_layout_helper"] for result in results))
        self.assertTrue(all(result["defaults_remain_legacy_tests"] for result in results))
        paths = {result["path"] for result in results}
        self.assertIn("tools/build_manual_review_visual_workbench.py", paths)
        self.assertIn("tools/import_manual_review_workbench.py", paths)
        self.assertIn("tools/build_manual_review_export_pipeline_dry_run.py", paths)
        self.assertIn("tools/build_pilot_manual_review_round1_support.py", paths)
        self.assertIn("tools/build_mobile_pilot_review_decision_aid.py", paths)
        self.assertIn("tools/build_ready_action_design_pack.py", paths)
        self.assertIn("tools/build_ready_action_design_review_brief.py", paths)
        self.assertIn("tools/check_ready_action_design_review_gate.py", paths)
        self.assertIn("tools/build_ready_action_design_review_worksheet.py", paths)
        self.assertIn("tools/build_ready_action_design_review_closeout.py", paths)
        self.assertIn("tools/build_ready_action_human_closeout_decision_draft.py", paths)
        self.assertIn("tools/build_ready_action_human_closeout_confirmation_record.py", paths)
        self.assertIn("tools/build_final_evidence_selection_policy_intake.py", paths)
        self.assertIn("tools/build_final_evidence_selection_policy_simulator_spec.py", paths)
        self.assertIn("tools/build_final_evidence_selection_policy_table_draft.py", paths)
        self.assertIn("tools/build_final_evidence_selection_policy_human_review_worksheet.py", paths)
        self.assertIn("tools/build_final_evidence_selection_policy_closeout_envelope.py", paths)
        self.assertIn("tools/build_final_evidence_selection_policy_closeout_decision_draft.py", paths)
        self.assertIn("tools/build_final_evidence_selection_policy_closeout_confirmation_record.py", paths)
        self.assertIn("tools/build_final_evidence_selection_policy_closeout_confirmed_record.py", paths)
        self.assertIn("tools/build_final_evidence_selection_policy_language_revision_worksheet.py", paths)
        self.assertIn("tools/build_final_evidence_selection_policy_language_revision_closeout_draft.py", paths)
        self.assertIn("tools/build_final_evidence_selection_policy_language_revision_confirmation_record.py", paths)
        self.assertIn("tools/build_final_evidence_selection_policy_offline_simulation_input_contract.py", paths)
        self.assertIn("tools/build_final_evidence_selection_policy_offline_simulation.py", paths)
        self.assertIn("tools/check_final_evidence_selection_policy_offline_simulation_gate.py", paths)
        self.assertIn("tools/build_final_evidence_selection_policy_adoption_decision_draft.py", paths)
        self.assertIn("tools/build_final_evidence_selection_policy_series_closeout.py", paths)
        self.assertIn("tools/build_retrieval_input_quality_intake.py", paths)
        self.assertIn("tools/build_retrieval_input_quality_audit_spec.py", paths)
        self.assertIn("tools/build_retrieval_input_quality_offline_audit.py", paths)
        self.assertIn("tools/check_retrieval_input_quality_offline_audit_gate.py", paths)
        self.assertIn("tools/build_retrieval_input_quality_diagnostic_prioritization.py", paths)
        self.assertIn("tools/check_retrieval_input_quality_diagnostic_prioritization_gate.py", paths)
        self.assertIn("tools/build_metadata_chunking_diagnostic_spec.py", paths)
        self.assertIn("tools/check_metadata_chunking_diagnostic_spec_gate.py", paths)
        self.assertIn("tools/build_metadata_chunking_diagnostic_runner_design.py", paths)
        self.assertIn("tools/check_metadata_chunking_diagnostic_runner_design_gate.py", paths)
        self.assertIn("tools/build_metadata_chunking_diagnostic_dry_run_contract.py", paths)
        self.assertIn("tools/build_retrieval_input_quality_series_closeout.py", paths)
        self.assertIn("tools/build_metadata_chunking_diagnostic_runner_manifest.py", paths)
        self.assertIn("tools/run_metadata_chunking_diagnostic_saved_report.py", paths)
        self.assertIn("tools/check_metadata_chunking_diagnostic_saved_report_runner_gate.py", paths)
        self.assertIn("tools/build_metadata_chunking_diagnostic_runner_series_closeout.py", paths)
        self.assertIn("tools/build_evidence_metadata_snapshot_contract.py", paths)
        self.assertIn("tools/run_evidence_metadata_snapshot.py", paths)
        self.assertIn("tools/check_evidence_metadata_snapshot_gate.py", paths)
        self.assertIn("tools/build_evidence_metadata_snapshot_series_closeout.py", paths)
        self.assertIn("tools/build_metadata_chunking_root_cause_report.py", paths)
        self.assertIn("tools/build_metadata_chunking_fix_design.py", paths)
        self.assertIn("tools/check_metadata_chunking_fix_design_gate.py", paths)
        self.assertIn("tools/build_metadata_chunking_series_closeout.py", paths)
        self.assertIn("tools/build_ingestion_metadata_patch_contract.py", paths)
        self.assertIn("tools/check_ingestion_metadata_patch_contract_gate.py", paths)
        self.assertIn("tools/build_ingestion_metadata_patch_dry_run_design.py", paths)
        self.assertIn("tools/check_ingestion_metadata_patch_dry_run_design_gate.py", paths)
        self.assertIn("tools/run_ingestion_metadata_patch_local_dry_run.py", paths)
        self.assertIn("tools/check_ingestion_metadata_patch_local_dry_run_gate.py", paths)
        self.assertIn("tools/build_ingestion_metadata_patch_actual_design.py", paths)
        self.assertIn("tools/check_ingestion_metadata_patch_actual_design_gate.py", paths)
        self.assertIn("tools/check_ingestion_metadata_source_patch.py", paths)
        self.assertIn("tools/build_ingestion_metadata_patch_post_patch_rebuild_dry_run_design.py", paths)
        self.assertIn("tools/check_ingestion_metadata_patch_post_patch_rebuild_dry_run_design_gate.py", paths)
        self.assertIn("tools/run_ingestion_metadata_patch_post_patch_rebuild_dry_run.py", paths)
        self.assertIn("tools/check_ingestion_metadata_patch_post_patch_rebuild_dry_run_gate.py", paths)
        self.assertIn("tools/build_rebuild_authorization_design.py", paths)
        self.assertIn("tools/check_rebuild_authorization_design_gate.py", paths)
        self.assertIn("tools/build_human_rebuild_authorization_worksheet.py", paths)
        self.assertIn("tools/check_human_rebuild_authorization_worksheet_gate.py", paths)
        self.assertIn("tools/build_rebuild_runbook_preflight_contract.py", paths)
        self.assertIn("tools/build_ingestion_metadata_rebuild_planning_series_closeout.py", paths)
        self.assertIn("tools/build_production_rebuild_execution_design.py", paths)
        self.assertIn("tools/check_production_rebuild_execution_design_gate.py", paths)
        self.assertIn("tools/build_human_rebuild_authorization_record_scaffold.py", paths)
        self.assertIn("tools/check_human_rebuild_authorization_record_scaffold_gate.py", paths)
        self.assertIn("tools/build_human_rebuild_authorization_record_draft_design.py", paths)
        self.assertIn("tools/check_human_rebuild_authorization_record_draft_design_gate.py", paths)
        self.assertIn("tools/build_human_rebuild_authorization_record_draft_scaffold.py", paths)
        self.assertIn("tools/check_human_rebuild_authorization_record_draft_scaffold_gate.py", paths)
        self.assertIn("tools/build_human_rebuild_authorization_record_input_workflow_design.py", paths)
        self.assertIn("tools/check_human_rebuild_authorization_record_input_workflow_design_gate.py", paths)
        self.assertIn("tools/build_human_rebuild_authorization_record_input_packet_scaffold.py", paths)
        self.assertIn("tools/check_human_rebuild_authorization_record_input_packet_scaffold_gate.py", paths)
        self.assertIn("tools/build_human_rebuild_authorization_record_input_form_scaffold.py", paths)
        self.assertIn("tools/check_human_rebuild_authorization_record_input_form_scaffold_gate.py", paths)
        self.assertIn("tools/build_production_rebuild_readiness_cutoff.py", paths)
        self.assertIn("tools/build_production_rebuild_live_preflight_runner_design.py", paths)
        self.assertIn("tools/check_production_rebuild_live_preflight_runner_design_gate.py", paths)
        self.assertIn("tools/build_production_rebuild_live_preflight_runner_minimal_implementation_design.py", paths)
        self.assertIn("tools/check_production_rebuild_live_preflight_runner_minimal_implementation_design_gate.py", paths)
        self.assertIn("tools/build_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design.py", paths)
        self.assertIn("tools/check_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_design_gate.py", paths)
        self.assertIn("tools/check_production_rebuild_live_preflight_runner_minimal_implementation_scaffold_gate.py", paths)
        self.assertIn("tools/run_production_rebuild_live_preflight_real_readonly_probe.py", paths)
        self.assertIn("tools/run_production_rebuild_live_preflight_snapshot_reference_probe.py", paths)
        self.assertIn("tools/run_production_rebuild_live_preflight_snapshot_create_reference_capture.py", paths)
        self.assertIn("tools/check_production_rebuild_formal_authorization_gate.py", paths)

    def test_roadmap_archive_snapshot_is_allowed_scaffold_file(self):
        self.assertIn(
            Path("docs/archive/project_review_and_roadmap_v0.4.15.13_snapshot.md"),
            SCAFFOLD_ALLOWED_FILES,
        )

    def test_dry_run_artifact_contract_keeps_nested_tests_artifact_dir(self):
        result = dry_run_artifact_contract_check()

        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["path"], "tests\\manual_review_export_pipeline_dry_run_artifacts")
        self.assertTrue(result["remains_isolated_tests_artifact_dir"])
        self.assertTrue(result["not_mapped_to_reports"])

    def test_default_project_health_report_is_non_runtime_mutating_and_structured(self):
        report = build_report()

        self.assertEqual(report["version"], VERSION)
        self.assertEqual(report["guardrails"]["runtime_state_mutation"], "disallowed")
        self.assertEqual(report["guardrails"]["writes_health_report"], True)
        self.assertEqual(report["guardrails"]["syntax_check_bytecode"], "not_written")
        self.assertEqual(report["guardrails"]["full_eval"], "not_run")
        self.assertIn("summary", report)
        self.assertIn("syntax_compile", report)
        self.assertIn("required_reports", report)
        self.assertIn("advisory_boundaries", report)
        self.assertIn("offline_pattern_scan", report)
        self.assertIn("scaffold_directory_presence", report)
        self.assertIn("scaffold_purity", report)
        self.assertIn("layout_compatibility", report)
        self.assertIn("layout_helper_pilot_defaults", report)
        self.assertIn("dry_run_artifact_contract", report)
        self.assertIn("artifact_index", report)
        self.assertIn("tool_index", report)
        self.assertIn("test_index", report)
        self.assertIn("encoding_hygiene_report", report)
        self.assertIn("tool_index_consistency_report", report)
        self.assertIn("test_index_consistency_report", report)
        self.assertIn("artifact_index_consistency_report", report)
        self.assertIn("layout_migration_readiness_report", report)
        self.assertIn("maintenance_closeout_report", report)
        self.assertIn("version_consistency", report)

    def test_encoding_hygiene_report_check_requires_passed_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "encoding_hygiene_report.json"
            write_json(
                path,
                {
                    "summary": {
                        "status": "failed",
                        "utf8_error_count": 1,
                        "error_count": 1,
                    },
                    "guardrails": {
                        "scanned_files_are_not_modified": True,
                        "file_delete_or_move": "not_performed",
                    },
                },
            )

            result = encoding_hygiene_report_check(path)

        self.assertEqual(result["status"], "failed")
        self.assertIn("encoding_hygiene_status_not_passed", result["errors"])
        self.assertIn("utf8_errors_detected", result["errors"])

    def test_tool_index_consistency_report_check_requires_passed_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "tool_index_consistency_report.json"
            write_json(
                path,
                {
                    "summary": {
                        "status": "failed",
                        "missing_tool_count": 1,
                        "missing_boundary_anchor_count": 1,
                    },
                    "guardrails": {
                        "scanned_files_are_not_modified": True,
                        "tool_move_or_rename": "not_performed",
                    },
                },
            )

            result = tool_index_consistency_report_check(path)

        self.assertEqual(result["status"], "failed")
        self.assertIn("tool_index_consistency_status_not_passed", result["errors"])
        self.assertIn("tool_index_missing_tools_detected", result["errors"])

    def test_test_index_consistency_report_check_requires_passed_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_index_consistency_report.json"
            write_json(
                path,
                {
                    "summary": {
                        "status": "failed",
                        "missing_test_count": 1,
                        "missing_required_anchor_count": 1,
                    },
                    "guardrails": {
                        "scanned_files_are_not_modified": True,
                        "test_move_or_rename": "not_performed",
                    },
                },
            )

            result = test_index_consistency_report_check(path)

        self.assertEqual(result["status"], "failed")
        self.assertIn("test_index_consistency_status_not_passed", result["errors"])
        self.assertIn("test_index_missing_tests_detected", result["errors"])

    def test_artifact_index_consistency_report_check_requires_passed_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "artifact_index_consistency_report.json"
            write_json(
                path,
                {
                    "summary": {
                        "status": "failed",
                        "missing_artifact_count": 1,
                        "missing_required_anchor_count": 1,
                        "missing_semantic_guardrail_count": 1,
                    },
                    "guardrails": {
                        "scanned_files_are_not_modified": True,
                        "report_move_or_migration": "not_performed",
                    },
                },
            )

            result = artifact_index_consistency_report_check(path)

        self.assertEqual(result["status"], "failed")
        self.assertIn("artifact_index_consistency_status_not_passed", result["errors"])
        self.assertIn("artifact_index_missing_artifacts_detected", result["errors"])

    def test_layout_migration_readiness_report_check_blocks_auto_migration(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "layout_migration_readiness_report.json"
            write_json(
                path,
                {
                    "summary": {
                        "status": "blocked",
                        "ready_for_automatic_migration": True,
                        "blocker_count": 1,
                    },
                    "guardrails": {
                        "scanned_files_are_not_modified": True,
                        "file_move_or_migration": "not_performed",
                    },
                },
            )

            result = layout_migration_readiness_report_check(path)

        self.assertEqual(result["status"], "failed")
        self.assertIn("layout_migration_readiness_not_ready_for_planning", result["errors"])
        self.assertIn("layout_migration_auto_migration_not_blocked", result["errors"])

    def test_maintenance_closeout_report_check_requires_passed_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "maintenance_closeout_report.json"
            write_json(
                path,
                {
                    "summary": {
                        "status": "attention_required",
                        "layout_migration": "not_performed",
                        "rag_main_flow_change": "not_performed",
                    },
                    "guardrails": {
                        "scanned_files_are_not_modified": True,
                        "file_move_or_migration": "not_performed",
                    },
                },
            )

            result = maintenance_closeout_report_check(path)

        self.assertEqual(result["status"], "failed")
        self.assertIn("maintenance_closeout_status_not_passed", result["errors"])

    def test_health_check_script_runs_with_direct_tool_execution_import_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "health.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "tools/run_project_health_check.py",
                    "--output",
                    str(output_path),
                    "--fail-on-error",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            report = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["summary"]["status"], "passed")
        self.assertIn("layout_compatibility", report)


if __name__ == "__main__":
    unittest.main()
