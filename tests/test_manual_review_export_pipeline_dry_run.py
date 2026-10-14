import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.build_manual_review_export_pipeline_dry_run import (
    DEFAULT_ARTIFACT_DIR,
    DEFAULT_CONTRACT_REPORT_PATH,
    DEFAULT_DECISION_SCHEMA_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_WORKBENCH_INPUT_PATH,
    build_report,
)
from tools._shared.layout import legacy_report_path


def write_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def minimal_schema() -> dict:
    return {
        "version": "schema-test",
        "summary": {"total_decision_records": 1},
        "decision_records": [
            {
                "case_id": "case_ready",
                "decision_status": "pending",
                "priority_score": 9,
                "reviewer_decision": {},
                "suggested_follow_up_actions": ["metadata_chunking_or_query_coverage_review"],
            }
        ],
    }


def minimal_contract() -> dict:
    return {
        "version": "contract-test",
        "scope": "manual review intake contract",
        "guardrails": {"overwrite_original_schema": "disallowed"},
    }


class ManualReviewExportPipelineDryRunTest(unittest.TestCase):
    def test_default_paths_keep_legacy_reports_and_isolated_artifact_dir(self):
        self.assertEqual(DEFAULT_DECISION_SCHEMA_PATH, Path("tests/evidence_manual_review_decision_schema.json"))
        self.assertEqual(
            DEFAULT_WORKBENCH_INPUT_PATH,
            Path("tests/manual_review_ai_suggestion_prefill_high_confidence_12_v2.json"),
        )
        self.assertEqual(DEFAULT_CONTRACT_REPORT_PATH, legacy_report_path("manual_review_intake_contract_report.json"))
        self.assertEqual(DEFAULT_ARTIFACT_DIR, Path("tests/manual_review_export_pipeline_dry_run_artifacts"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("manual_review_export_pipeline_dry_run_report.json"))

    def test_ai_suggestion_input_is_blocked_without_completed_decision(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            schema = tmp / "schema.json"
            workbench = tmp / "ai_suggestion.json"
            contract = tmp / "contract.json"
            artifact_dir = tmp / "artifacts"
            write_json(schema, minimal_schema())
            write_json(contract, minimal_contract())
            write_json(
                workbench,
                {
                    "version": "safe-suggestion-test",
                    "human_confirmation_required": True,
                    "reviewer_input_template_written": False,
                    "guardrails": {
                        "advisory_draft_only": True,
                        "reviewer_decision_import": "disallowed_without_human_copy",
                    },
                    "workbench_items": [
                        {
                            "case_id": "case_ready",
                            "ai_review_suggestion": {
                                "ai_suggestion": True,
                                "decision": "confirm_diagnostic_issue",
                                "confirmed_root_causes": ["metadata_chunking_or_query_coverage"],
                                "confirmed_follow_up_actions": ["metadata_chunking_or_query_coverage_review"],
                                "rationale": "AI suggestion only.",
                                "human_confirmation_required": True,
                            },
                        }
                    ],
                },
            )

            report = build_report(schema, workbench, contract, artifact_dir)

        self.assertEqual(report["version"], "0.4.7.8.14")
        self.assertTrue(report["input_profile"]["safe_ai_suggestion_input"])
        self.assertEqual(report["summary"]["pipeline_conclusion"], "blocked_as_expected_ai_suggestion_only")
        self.assertEqual(report["summary"]["imported_rows"], 0)
        self.assertEqual(report["summary"]["rejected_rows"], 1)
        self.assertEqual(report["summary"]["invalid_json_workbench_export"], 1)
        self.assertEqual(report["summary"]["promotion_candidates"], 0)
        self.assertEqual(report["summary"]["gate_status"], "blocked")
        self.assertIn("no_imported_review_rows", report["summary"]["gate_blockers"])

    def test_advisory_json_with_importable_fields_is_rejected_by_outer_contract(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            schema = tmp / "schema.json"
            workbench = tmp / "malicious_advisory.json"
            contract = tmp / "contract.json"
            artifact_dir = tmp / "artifacts"
            write_json(schema, minimal_schema())
            write_json(contract, minimal_contract())
            write_json(
                workbench,
                {
                    "schema_kind": "advisory_mobile_pilot_review_decision_aid",
                    "advisory_packet_only": True,
                    "contains_completed_manual_decisions": False,
                    "workbench_items": [
                        {
                            "case_id": "case_ready",
                            "reviewer_input_template": {
                                "reviewer": "Not a human export",
                                "reviewed_at": "2026-05-13",
                                "decision": "confirm_diagnostic_issue",
                                "confirmed_root_causes": ["metadata_chunking_or_query_coverage"],
                                "confirmed_follow_up_actions": ["metadata_chunking_or_query_coverage_review"],
                                "rationale": "This should be rejected at the JSON input contract.",
                            },
                        }
                    ],
                },
            )

            report = build_report(schema, workbench, contract, artifact_dir)
            proposed = json.loads(Path(report["artifacts"]["proposed_schema"]).read_text(encoding="utf-8"))

        self.assertEqual(report["summary"]["imported_rows"], 0)
        self.assertEqual(report["summary"]["promotion_candidates"], 0)
        self.assertEqual(report["summary"]["ready_action_candidates"], 0)
        self.assertEqual(report["summary"]["gate_status"], "blocked")
        self.assertEqual(report["summary"]["pipeline_conclusion"], "blocked_input_rejections_require_review")
        self.assertIn("invalid_json_workbench_export", report["summary"]["dry_run_blockers"])
        self.assertEqual(proposed["decision_records"][0]["decision_status"], "pending")
        self.assertEqual(proposed["decision_records"][0]["reviewer_decision"], {})

    def test_pilot_checklist_only_export_is_blocked_without_completed_decision(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            schema = tmp / "schema.json"
            workbench = tmp / "pilot_checklist_only.json"
            contract = tmp / "contract.json"
            artifact_dir = tmp / "artifacts"
            write_json(schema, minimal_schema())
            write_json(contract, minimal_contract())
            write_json(
                workbench,
                {
                    "version": "0.4.7.8.16",
                    "scope": "filled visual manual review workbench export",
                    "summary": {
                        "total_source_workbench_items": 1,
                        "total_workbench_items": 0,
                        "exported_draft_items": 0,
                        "pilot_checklist_marked_cases": 1,
                        "export_policy": "ready_human_drafts_only",
                    },
                    "workbench_items": [],
                },
            )

            report = build_report(schema, workbench, contract, artifact_dir)

        self.assertEqual(report["summary"]["imported_rows"], 0)
        self.assertEqual(report["summary"]["promotion_candidates"], 0)
        self.assertEqual(report["summary"]["ready_action_candidates"], 0)
        self.assertEqual(report["summary"]["gate_status"], "blocked")
        self.assertEqual(report["summary"]["pipeline_conclusion"], "blocked_manual_review_required")
        self.assertIn("no_imported_review_rows", report["summary"]["gate_blockers"])

    def test_completed_valid_human_workbench_opens_dry_run_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            schema = tmp / "schema.json"
            workbench = tmp / "filled_workbench.json"
            contract = tmp / "contract.json"
            artifact_dir = tmp / "artifacts"
            write_json(schema, minimal_schema())
            write_json(contract, minimal_contract())
            write_json(
                workbench,
                {
                    "version": "filled-test",
                    "scope": "filled visual manual review workbench export",
                    "summary": {"export_policy": "ready_human_drafts_only"},
                    "workbench_items": [
                        {
                            "case_id": "case_ready",
                            "reviewer_input_template": {
                                "reviewer": "Human Reviewer",
                                "reviewed_at": "2026-05-12",
                                "decision": "confirm_diagnostic_issue",
                                "confirmed_root_causes": ["metadata_chunking_or_query_coverage"],
                                "rejected_root_causes": [],
                                "confirmed_follow_up_actions": ["metadata_chunking_or_query_coverage_review"],
                                "proposed_change_targets": ["knowledge_manifest_metadata"],
                                "fixture_candidate": False,
                                "rationale": "Human reviewer confirmed the retrieval input quality issue.",
                                "notes": "ready for dry run",
                            },
                        }
                    ],
                },
            )

            report = build_report(schema, workbench, contract, artifact_dir)
            proposed = json.loads(Path(report["artifacts"]["proposed_schema"]).read_text(encoding="utf-8"))

        self.assertFalse(report["input_profile"]["safe_ai_suggestion_input"])
        self.assertEqual(report["summary"]["pipeline_conclusion"], "ready_for_governed_action_planning")
        self.assertEqual(report["summary"]["imported_rows"], 1)
        self.assertEqual(report["summary"]["changed_cases"], 1)
        self.assertEqual(report["summary"]["invalid_proposed_records"], 0)
        self.assertEqual(report["summary"]["promotion_candidates"], 1)
        self.assertEqual(report["summary"]["ready_action_candidates"], 1)
        self.assertEqual(report["summary"]["gate_status"], "open")
        self.assertEqual(proposed["decision_records"][0]["decision_status"], "completed")

    def test_cleaned_pilot5_workbench_opens_current_dry_run_gate(self):
        report = build_report(
            Path("tests/evidence_manual_review_decision_schema.json"),
            Path("tests/filled_manual_review_workbench_pilot5_cleaned_2026-05-13.json"),
            Path("tests/manual_review_intake_contract_report.json"),
            Path("tests/manual_review_export_pipeline_dry_run_artifacts"),
        )

        self.assertEqual(report["summary"]["pipeline_conclusion"], "ready_for_governed_action_planning")
        self.assertEqual(report["summary"]["imported_rows"], 5)
        self.assertEqual(report["summary"]["rejected_rows"], 0)
        self.assertEqual(report["summary"]["changed_cases"], 5)
        self.assertEqual(report["summary"]["promotion_candidates"], 5)
        self.assertEqual(report["summary"]["ready_action_candidates"], 18)
        self.assertEqual(report["summary"]["gate_status"], "open")

    def test_mixed_valid_and_rejected_rows_do_not_become_ready(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            schema = tmp / "schema.json"
            workbench = tmp / "mixed_workbench.json"
            contract = tmp / "contract.json"
            artifact_dir = tmp / "artifacts"
            write_json(schema, minimal_schema())
            write_json(contract, minimal_contract())
            write_json(
                workbench,
                {
                    "version": "mixed-filled-test",
                    "scope": "filled visual manual review workbench export",
                    "summary": {"export_policy": "ready_human_drafts_only"},
                    "workbench_items": [
                        {
                            "case_id": "case_ready",
                            "reviewer_input_template": {
                                "reviewer": "Human Reviewer",
                                "reviewed_at": "2026-05-12",
                                "decision": "confirm_diagnostic_issue",
                                "confirmed_root_causes": ["metadata_chunking_or_query_coverage"],
                                "rejected_root_causes": [],
                                "confirmed_follow_up_actions": ["metadata_chunking_or_query_coverage_review"],
                                "proposed_change_targets": ["knowledge_manifest_metadata"],
                                "fixture_candidate": False,
                                "rationale": "Human reviewer confirmed the retrieval input quality issue.",
                                "notes": "",
                            },
                        },
                        {
                            "case_id": "unknown_case",
                            "reviewer_input_template": {
                                "reviewer": "Human Reviewer",
                                "reviewed_at": "2026-05-12",
                                "decision": "defer",
                                "rationale": "This row should be rejected because the case id is unknown.",
                            },
                        },
                    ],
                },
            )

            report = build_report(schema, workbench, contract, artifact_dir)

        self.assertEqual(report["summary"]["imported_rows"], 1)
        self.assertEqual(report["summary"]["rejected_rows"], 1)
        self.assertEqual(report["summary"]["gate_status"], "open")
        self.assertEqual(report["summary"]["pipeline_conclusion"], "blocked_input_rejections_require_review")
        self.assertIn("rejected_import_rows", report["summary"]["dry_run_blockers"])
        self.assertIn("unknown_case_id", report["summary"]["dry_run_blockers"])

    def test_dry_run_writes_only_to_isolated_artifact_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            schema = tmp / "schema.json"
            workbench = tmp / "empty.json"
            contract = tmp / "contract.json"
            artifact_dir = tmp / "isolated_artifacts"
            canonical = tmp / "proposed_manual_review_decision_schema.json"
            canonical.write_text("canonical", encoding="utf-8")
            write_json(schema, minimal_schema())
            write_json(contract, minimal_contract())
            write_json(
                workbench,
                {
                    "version": "empty",
                    "scope": "filled visual manual review workbench export",
                    "summary": {"export_policy": "ready_human_drafts_only"},
                    "workbench_items": [{"case_id": "case_ready"}],
                },
            )

            report = build_report(schema, workbench, contract, artifact_dir)
            canonical_content = canonical.read_text(encoding="utf-8")

        self.assertEqual(canonical_content, "canonical")
        self.assertTrue(str(report["artifacts"]["proposed_schema"]).endswith("_dry_run.json"))
        self.assertIn("canonical_pipeline_artifact_overwrite", report["guardrails"])

    def test_cli_refuses_canonical_output_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            schema = tmp / "schema.json"
            workbench = tmp / "empty.json"
            contract = tmp / "contract.json"
            artifact_dir = tmp / "artifacts"
            output = tmp / "proposed_manual_review_decision_schema.json"
            write_json(schema, minimal_schema())
            write_json(contract, minimal_contract())
            write_json(
                workbench,
                {
                    "version": "empty",
                    "scope": "filled visual manual review workbench export",
                    "summary": {"export_policy": "ready_human_drafts_only"},
                    "workbench_items": [{"case_id": "case_ready"}],
                },
            )
            output.write_text("canonical", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    "tools/build_manual_review_export_pipeline_dry_run.py",
                    "--decision-schema",
                    str(schema),
                    "--workbench-input",
                    str(workbench),
                    "--contract-report",
                    str(contract),
                    "--artifact-dir",
                    str(artifact_dir),
                    "--output",
                    str(output),
                ],
                cwd=Path.cwd(),
                text=True,
                capture_output=True,
                timeout=20,
                check=False,
            )
            output_content = output.read_text(encoding="utf-8")

        self.assertEqual(result.returncode, 2)
        self.assertIn("Refusing to write dry-run report", result.stderr)
        self.assertEqual(output_content, "canonical")


if __name__ == "__main__":
    unittest.main()
