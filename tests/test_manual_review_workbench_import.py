import json
import tempfile
import unittest
from pathlib import Path

from tools.import_manual_review_workbench import (
    DEFAULT_DECISION_SCHEMA_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_REPORT_PATH,
    DEFAULT_WORKBENCH_INPUT_PATH,
    build_outputs,
)
from tools._shared.layout import legacy_report_path


def write_schema(path: Path):
    path.write_text(
        __import__("json").dumps(
            {
                "version": "0.4.7.5.0",
                "summary": {"total_decision_records": 1},
                "decision_records": [
                    {
                        "case_id": "case_a",
                        "decision_status": "pending",
                        "reviewer_decision": {},
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


class ManualReviewWorkbenchImportTest(unittest.TestCase):
    def test_default_paths_keep_legacy_report_output_without_migrating_schema_or_csv(self):
        self.assertEqual(DEFAULT_DECISION_SCHEMA_PATH, Path("tests/evidence_manual_review_decision_schema.json"))
        self.assertEqual(DEFAULT_WORKBENCH_INPUT_PATH, Path("tests/evidence_manual_review_workbench.csv"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, Path("tests/proposed_manual_review_decision_schema.json"))
        self.assertEqual(DEFAULT_REPORT_PATH, legacy_report_path("manual_review_workbench_import_report.json"))

    def test_csv_import_is_rejected_as_unsupported_formal_input(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            schema = tmp / "schema.json"
            csv_path = tmp / "workbench.csv"
            write_schema(schema)
            csv_path.write_text(
                "\n".join(
                    [
                        "case_id,reviewer,reviewed_at,decision,rationale",
                        "case_a,reviewer,2026-05-11,confirm_diagnostic_issue,Confirmed.",
                    ]
                ),
                encoding="utf-8",
            )

            proposed, report = build_outputs(schema, csv_path)

        self.assertEqual(proposed["version"], "0.4.7.7.1")
        self.assertEqual(proposed["inputs"]["source_decision_schema_version"], "0.4.7.5.0")
        self.assertEqual(report["summary"]["imported_rows"], 0)
        self.assertEqual(report["summary"]["rejected_rows"], 1)
        self.assertEqual(report["summary"]["unsupported_workbench_input"], 1)
        record = proposed["decision_records"][0]
        self.assertEqual(record["decision_status"], "pending")
        self.assertEqual(record["reviewer_decision"], {})

    def test_unknown_and_empty_rows_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            schema = tmp / "schema.json"
            csv_path = tmp / "workbench.csv"
            write_schema(schema)
            csv_path.write_text(
                "\n".join(
                    [
                        "case_id,reviewer,decision",
                        "unknown,reviewer,defer",
                        "case_a,,",
                    ]
                ),
                encoding="utf-8",
            )

            _, report = build_outputs(schema, csv_path)

        self.assertEqual(report["summary"]["imported_rows"], 0)
        self.assertEqual(report["summary"]["rejected_rows"], 2)
        self.assertEqual(report["summary"]["unsupported_workbench_input"], 2)

    def test_json_import_accepts_only_filled_visual_workbench_export_contract(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            schema = tmp / "schema.json"
            workbench_json = tmp / "filled_workbench.json"
            write_schema(schema)
            workbench_json.write_text(
                json.dumps(
                    {
                        "version": "filled-test",
                        "scope": "filled visual manual review workbench export",
                        "summary": {
                            "export_policy": "ready_human_drafts_only",
                            "exported_case_ids": ["case_a"],
                            "exported_draft_items": 1,
                            "total_workbench_items": 1,
                        },
                        "workbench_items": [
                            {
                                "case_id": "case_a",
                                "reviewer_input_template": {
                                    "reviewer": "reviewer",
                                    "reviewed_at": "2026-05-13",
                                    "decision": "confirm_diagnostic_issue",
                                    "confirmed_root_causes": ["metadata_chunking_or_query_coverage"],
                                    "confirmed_follow_up_actions": ["metadata_chunking_or_query_coverage_review"],
                                    "rationale": "Human reviewer confirmed the issue.",
                                },
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            proposed, report = build_outputs(schema, workbench_json)

        self.assertEqual(report["summary"]["imported_rows"], 1)
        self.assertEqual(report["summary"]["invalid_json_workbench_export"], 0)
        self.assertEqual(proposed["decision_records"][0]["decision_status"], "completed")

    def test_advisory_json_with_reviewer_template_is_rejected_by_outer_contract(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            schema = tmp / "schema.json"
            advisory_json = tmp / "advisory.json"
            write_schema(schema)
            advisory_json.write_text(
                json.dumps(
                    {
                        "schema_kind": "advisory_mobile_pilot_review_decision_aid",
                        "advisory_packet_only": True,
                        "contains_completed_manual_decisions": False,
                        "workbench_items": [
                            {
                                "case_id": "case_a",
                                "reviewer_input_template": {
                                    "reviewer": "not human export",
                                    "reviewed_at": "2026-05-13",
                                    "decision": "confirm_diagnostic_issue",
                                    "rationale": "Should not import.",
                                },
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            proposed, report = build_outputs(schema, advisory_json)

        self.assertEqual(report["summary"]["imported_rows"], 0)
        self.assertEqual(report["summary"]["rejected_rows"], 1)
        self.assertEqual(report["summary"]["invalid_json_workbench_export"], 1)
        self.assertEqual(proposed["decision_records"][0]["decision_status"], "pending")
        self.assertEqual(proposed["decision_records"][0]["reviewer_decision"], {})

    def test_completed_decision_requires_core_human_fields_before_status_changes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            schema = tmp / "schema.json"
            workbench_json = tmp / "filled_workbench.json"
            write_schema(schema)
            workbench_json.write_text(
                json.dumps(
                    {
                        "scope": "filled visual manual review workbench export",
                        "summary": {"export_policy": "ready_human_drafts_only"},
                        "workbench_items": [
                            {
                                "case_id": "case_a",
                                "reviewer_input_template": {
                                    "decision": "confirm_diagnostic_issue",
                                    "rationale": "Missing reviewer and date.",
                                },
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            proposed, report = build_outputs(schema, workbench_json)

        self.assertEqual(report["summary"]["imported_rows"], 0)
        self.assertEqual(report["summary"]["rejected_rows"], 1)
        self.assertEqual(report["summary"]["incomplete_completed_reviewer_fields"], 1)
        self.assertEqual(proposed["decision_records"][0]["decision_status"], "pending")
        self.assertEqual(proposed["decision_records"][0]["reviewer_decision"], {})

    def test_filled_json_with_ai_or_advisory_item_marker_is_rejected_per_item(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            schema = tmp / "schema.json"
            workbench_json = tmp / "filled_workbench.json"
            write_schema(schema)
            workbench_json.write_text(
                json.dumps(
                    {
                        "version": "filled-test",
                        "scope": "filled visual manual review workbench export",
                        "summary": {
                            "export_policy": "ready_human_drafts_only",
                            "exported_case_ids": ["case_a"],
                            "exported_draft_items": 1,
                            "total_workbench_items": 1,
                        },
                        "workbench_items": [
                            {
                                "case_id": "case_a",
                                "advisory_only": True,
                                "ai_review_suggestion": {"ai_suggestion": True},
                                "reviewer_input_template": {
                                    "reviewer": "Codex",
                                    "reviewed_at": "2026-05-13",
                                    "decision": "confirm_diagnostic_issue",
                                    "confirmed_root_causes": ["metadata_chunking_or_query_coverage"],
                                    "confirmed_follow_up_actions": ["metadata_chunking_or_query_coverage_review"],
                                    "rationale": "AI辅助预填，需人工最终确认。",
                                    "human_confirmation_required": True,
                                },
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            proposed, report = build_outputs(schema, workbench_json)

        self.assertEqual(report["summary"]["imported_rows"], 0)
        self.assertEqual(report["summary"]["rejected_rows"], 1)
        self.assertEqual(report["summary"]["advisory_review_marker"], 1)
        self.assertEqual(proposed["decision_records"][0]["decision_status"], "pending")
        self.assertEqual(proposed["decision_records"][0]["reviewer_decision"], {})

    def test_filled_json_export_metadata_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            schema = tmp / "schema.json"
            workbench_json = tmp / "filled_workbench.json"
            write_schema(schema)
            workbench_json.write_text(
                json.dumps(
                    {
                        "version": "filled-test",
                        "scope": "filled visual manual review workbench export",
                        "summary": {
                            "export_policy": "ready_human_drafts_only",
                            "exported_case_ids": ["other_case"],
                            "exported_draft_items": 1,
                            "total_workbench_items": 1,
                        },
                        "workbench_items": [
                            {
                                "case_id": "case_a",
                                "reviewer_input_template": {
                                    "reviewer": "Human Reviewer",
                                    "reviewed_at": "2026-05-13",
                                    "decision": "confirm_diagnostic_issue",
                                    "confirmed_root_causes": ["metadata_chunking_or_query_coverage"],
                                    "confirmed_follow_up_actions": ["metadata_chunking_or_query_coverage_review"],
                                    "rationale": "Human reviewer confirmed the issue.",
                                },
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            proposed, report = build_outputs(schema, workbench_json)

        self.assertEqual(report["summary"]["imported_rows"], 0)
        self.assertEqual(report["summary"]["rejected_rows"], 1)
        self.assertEqual(report["summary"]["export_metadata_mismatch"], 1)
        self.assertEqual(proposed["decision_records"][0]["decision_status"], "pending")


if __name__ == "__main__":
    unittest.main()
