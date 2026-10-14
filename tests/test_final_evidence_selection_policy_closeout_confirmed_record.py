import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_final_evidence_selection_policy_closeout_confirmed_record import (
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_SCAFFOLD_REPORT_PATH,
    EXPECTED_CASE_COUNT,
    EXPECTED_POLICY_CATEGORIES,
    EXPECTED_ROW_COUNT,
    EXPECTED_SUGGESTED_OPTIONS,
    FORBIDDEN_OUTPUT_KEYS,
    USER_CONFIRMATION_CONTEXT,
    build_report,
    render_markdown,
)


PROHIBITED_SOURCE_PATTERNS = [
    "rag_query(",
    "from src.rag.retriever import rag_query",
    "ChatOpenAI",
    "QdrantClient",
    "fetch(",
    "XMLHttpRequest",
    "/ask",
    "hidden_eval_seed_cases.json",
    "rag_anchor_rules.json",
    "risk_payload_supplement_rules.json",
    "rag_eval_cases.json",
    "smoke_eval_cases.json",
]


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def load_current_scaffold() -> dict:
    return json.loads(
        Path("tests/final_evidence_selection_policy_closeout_confirmation_record_report.json").read_text(
            encoding="utf-8-sig"
        )
    )


def walk_dicts(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_dicts(child)


def assertion_status(report: dict, name: str) -> str | None:
    for assertion in report.get("assertions", []):
        if assertion.get("name") == name:
            return assertion.get("status")
    return None


def build_with_scaffold(scaffold: dict) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "scaffold.json"
        write_json(path, copy.deepcopy(scaffold))
        return build_report(path)


class FinalEvidenceSelectionPolicyCloseoutConfirmedRecordTest(unittest.TestCase):
    def test_default_paths_use_legacy_report_and_docs_markdown_output(self):
        self.assertEqual(
            DEFAULT_SCAFFOLD_REPORT_PATH,
            legacy_report_path("final_evidence_selection_policy_closeout_confirmation_record_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("final_evidence_selection_policy_closeout_confirmed_record_report.json"),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/final_evidence_selection_policy_closeout_confirmed_record_v0.4.8.7.md"),
        )

    def test_real_current_scaffold_builds_confirmed_record(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.8.7")
        self.assertEqual(report["schema_kind"], "final_evidence_selection_policy_closeout_confirmed_record")
        self.assertEqual(report["scope"], "offline final evidence selection policy closeout confirmed record only")
        self.assertEqual(report["confirmation_gate"]["status"], "confirmed_for_future_offline_design_planning")
        self.assertEqual(report["confirmation_gate"]["allowed_use"], "future_offline_design_planning_input_only")
        self.assertTrue(report["confirmation_gate"]["user_confirmation_recorded"])
        self.assertTrue(report["confirmation_gate"]["formal_policy_closeout_recorded"])
        self.assertFalse(report["confirmation_gate"]["formal_human_outcome_recorded"])
        self.assertFalse(report["confirmation_gate"]["implementation_allowed"])
        self.assertFalse(report["confirmation_gate"]["code_patch_authorized"])
        self.assertFalse(report["confirmation_gate"]["runtime_policy_implementation_allowed"])
        self.assertFalse(report["confirmation_gate"]["runtime_selection_policy_patch_allowed"])
        self.assertFalse(report["confirmation_gate"]["rerank_change_allowed"])
        self.assertFalse(report["confirmation_gate"]["prompt_change_allowed"])
        self.assertEqual(report["confirmation_gate"]["rag_query_integration"], "disallowed")
        self.assertEqual(report["confirmation_gate"]["blockers"], [])

        self.assertEqual(report["confirmation_context"], USER_CONFIRMATION_CONTEXT)
        self.assertEqual(report["summary"]["confirmed_row_count"], EXPECTED_ROW_COUNT)
        self.assertEqual(report["summary"]["source_scaffold_row_count"], EXPECTED_ROW_COUNT)
        self.assertEqual(report["summary"]["unique_case_count"], EXPECTED_CASE_COUNT)
        self.assertEqual(
            report["summary"]["confirmed_closeout_option_summary"],
            {
                "accept_for_future_offline_simulation_design": 5,
                "revise_policy_language_before_closeout": 3,
            },
        )
        self.assertTrue(report["summary"]["user_confirmation_recorded"])
        self.assertFalse(report["summary"]["implementation_allowed"])

        rows = report["confirmed_rows"]
        self.assertEqual(len(rows), EXPECTED_ROW_COUNT)
        self.assertEqual([row["policy_category"] for row in rows], EXPECTED_POLICY_CATEGORIES)
        for row in rows:
            category = row["policy_category"]
            self.assertEqual(row["confirmation_status"], "confirmed_as_suggested_closeout_option")
            self.assertEqual(row["selected_confirmation_option"], "confirm_suggested_closeout_option")
            self.assertEqual(row["confirmed_closeout_option"], EXPECTED_SUGGESTED_OPTIONS[category])
            self.assertTrue(row["user_confirmation_recorded"])
            self.assertTrue(row["formal_policy_closeout_recorded"])
            self.assertFalse(row["formal_human_outcome_recorded"])
            self.assertFalse(row["implementation_allowed"])
            self.assertFalse(row["code_patch_authorized"])
            self.assertFalse(row["candidate_route_authorized"])
            self.assertEqual(row["runtime_adoption_status"], "not_allowed")
            self.assertTrue(row["source_case_ids"])

        handoff = report["next_version_handoff"]
        self.assertEqual(
            handoff["accepted_for_future_offline_simulation_design"],
            ["primary", "operative", "procedural", "definition_only", "high_risk_manual_review"],
        )
        self.assertEqual(
            handoff["requires_policy_language_revision_before_simulation"],
            ["liability", "scenario_core", "coverage_floor"],
        )
        self.assertFalse(handoff["runtime_implementation_allowed"])
        self.assertTrue(all(item["status"] == "passed" for item in report["assertions"]))
        for node in walk_dicts(report):
            self.assertFalse(FORBIDDEN_OUTPUT_KEYS & set(node.keys()))

    def test_wrong_or_blocked_source_scaffold_blocks_confirmed_record(self):
        scaffold = load_current_scaffold()
        scaffold["version"] = "0.4.8.5"
        scaffold["schema_kind"] = "wrong_schema"
        scaffold["confirmation_gate"]["status"] = "blocked"
        scaffold["confirmation_gate"]["blockers"] = ["source_problem"]

        report = build_with_scaffold(scaffold)

        self.assertEqual(report["confirmation_gate"]["status"], "blocked")
        self.assertFalse(report["confirmation_gate"]["user_confirmation_recorded"])
        self.assertIn("scaffold_version_mismatch", report["confirmation_gate"]["blockers"])
        self.assertIn("scaffold_schema_mismatch", report["confirmation_gate"]["blockers"])
        self.assertIn("scaffold_gate_not_pending_confirmation", report["confirmation_gate"]["blockers"])
        self.assertIn("scaffold_gate_has_blockers", report["confirmation_gate"]["blockers"])
        self.assertEqual(assertion_status(report, "source_scaffold_is_ready_for_confirmed_record"), "failed")

    def test_already_confirmed_or_implementation_source_blocks_confirmed_record(self):
        scaffold = load_current_scaffold()
        scaffold["confirmation_gate"]["user_confirmation_recorded"] = True
        scaffold["confirmation_gate"]["implementation_allowed"] = True
        scaffold["confirmation_gate"]["code_patch_authorized"] = True
        scaffold["confirmation_scaffold_rows"][0]["user_confirmation_recorded"] = True
        scaffold["confirmation_scaffold_rows"][0]["implementation_allowed"] = True
        scaffold["confirmation_scaffold_rows"][0]["candidate_route_authorized"] = True

        report = build_with_scaffold(scaffold)

        self.assertEqual(report["confirmation_gate"]["status"], "blocked")
        self.assertIn("scaffold_already_records_user_confirmation", report["confirmation_gate"]["blockers"])
        self.assertIn("scaffold_implementation_not_blocked", report["confirmation_gate"]["blockers"])
        self.assertIn("scaffold_code_patch_not_blocked", report["confirmation_gate"]["blockers"])
        self.assertIn("scaffold_row_already_confirmed", report["confirmation_gate"]["blockers"])
        self.assertIn("scaffold_row_implementation_not_blocked", report["confirmation_gate"]["blockers"])
        self.assertIn("scaffold_row_route_authorized", report["confirmation_gate"]["blockers"])
        self.assertFalse(report["implementation_gate"]["implementation_allowed"])

    def test_row_count_order_or_suggested_option_drift_blocks_confirmed_record(self):
        scaffold = load_current_scaffold()
        scaffold["confirmation_scaffold_rows"] = list(reversed(scaffold["confirmation_scaffold_rows"][:-1]))
        scaffold["summary"]["confirmation_row_count"] = 7
        scaffold["summary"]["unique_case_count"] = 4
        scaffold["summary"]["pending_user_confirmation_count"] = 7
        scaffold["confirmation_scaffold_rows"][0]["suggested_closeout_option"] = "unexpected"

        report = build_with_scaffold(scaffold)

        self.assertEqual(report["confirmation_gate"]["status"], "blocked")
        self.assertIn("scaffold_row_count_summary_drift", report["confirmation_gate"]["blockers"])
        self.assertIn("scaffold_row_count_drift", report["confirmation_gate"]["blockers"])
        self.assertIn("scaffold_case_count_drift", report["confirmation_gate"]["blockers"])
        self.assertIn("scaffold_pending_count_drift", report["confirmation_gate"]["blockers"])
        self.assertIn("scaffold_policy_category_order_drift", report["confirmation_gate"]["blockers"])
        self.assertIn("scaffold_policy_id_order_drift", report["confirmation_gate"]["blockers"])
        self.assertEqual(assertion_status(report, "confirmed_record_has_eight_rows"), "failed")

    def test_forbidden_or_advisory_source_keys_block_confirmed_record(self):
        scaffold = load_current_scaffold()
        scaffold["confirmation_scaffold_rows"][0]["implementation_plan"] = {"step": "should_not_exist"}
        scaffold["confirmation_scaffold_rows"][0]["ai_suggestion"] = True

        report = build_with_scaffold(scaffold)

        self.assertEqual(report["confirmation_gate"]["status"], "blocked")
        self.assertIn("scaffold_forbidden_key_present:implementation_plan", report["confirmation_gate"]["blockers"])
        self.assertIn("scaffold_advisory_signal_present:ai_suggestion", report["confirmation_gate"]["blockers"])
        for node in walk_dicts(report):
            self.assertFalse({"work_items", "engineering_tasks", "pending_tasks"} & set(node.keys()))

    def test_mojibake_like_text_blocks_human_readability_gate(self):
        scaffold = load_current_scaffold()
        scaffold["confirmation_scaffold_rows"][0]["confirmation_prompt"] = "\u9428 damaged text"

        report = build_with_scaffold(scaffold)

        self.assertEqual(report["confirmation_gate"]["status"], "blocked")
        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("blocked_for_human_readability", report["confirmation_gate"]["blockers"])
        self.assertEqual(assertion_status(report, "text_readability_gate"), "failed")

    def test_markdown_is_confirmed_record_only_and_readable(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.8.7 Final Evidence Selection Policy Closeout Confirmed Record", markdown)
        self.assertIn("user's explicit confirmation", markdown)
        self.assertIn("Confirmation text: 确认以上 8 条，按 suggested closeout option 生成 v0.4.8.7。", markdown)
        self.assertIn("## Confirmed Rows", markdown)
        self.assertIn("future_offline_simulation_design_candidate", markdown)
        self.assertIn("policy_language_revision_required_before_simulation", markdown)
        self.assertIn("`implementation_allowed=false`", markdown)
        for token in [
            "implementation_plan",
            "files_to_change",
            "commands",
            "reviewer_decision",
            "work_items",
        ]:
            self.assertNotIn(token, markdown)

    def test_tool_and_outputs_do_not_contain_runtime_or_eval_mutation_patterns(self):
        target_paths = [
            Path("tools/build_final_evidence_selection_policy_closeout_confirmed_record.py"),
            Path("docs/final_evidence_selection_policy_closeout_confirmed_record_v0.4.8.7.md"),
            Path("tests/final_evidence_selection_policy_closeout_confirmed_record_report.json"),
        ]
        matches = []
        for path in target_paths:
            if not path.exists():
                continue
            content = path.read_text(encoding="utf-8-sig")
            for pattern in PROHIBITED_SOURCE_PATTERNS:
                if pattern in content:
                    matches.append((str(path), pattern))
        self.assertEqual(matches, [])


if __name__ == "__main__":
    unittest.main()
