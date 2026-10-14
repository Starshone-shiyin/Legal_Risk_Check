import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_final_evidence_selection_policy_closeout_confirmation_record import (
    DEFAULT_DRAFT_REPORT_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    EXPECTED_CASE_COUNT,
    EXPECTED_DRAFT_ROW_COUNT,
    EXPECTED_POLICY_CATEGORIES,
    FORBIDDEN_OUTPUT_KEYS,
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


def load_current_draft() -> dict:
    return json.loads(
        Path("tests/final_evidence_selection_policy_closeout_decision_draft_report.json").read_text(
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


def build_with_draft(draft: dict) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "draft.json"
        write_json(path, copy.deepcopy(draft))
        return build_report(path)


class FinalEvidenceSelectionPolicyCloseoutConfirmationRecordTest(unittest.TestCase):
    def test_default_paths_use_legacy_report_and_docs_markdown_output(self):
        self.assertEqual(
            DEFAULT_DRAFT_REPORT_PATH,
            legacy_report_path("final_evidence_selection_policy_closeout_decision_draft_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("final_evidence_selection_policy_closeout_confirmation_record_report.json"),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/final_evidence_selection_policy_closeout_confirmation_record_v0.4.8.6.md"),
        )

    def test_real_current_report_builds_pending_confirmation_scaffold(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.8.6")
        self.assertEqual(report["schema_kind"], "final_evidence_selection_policy_closeout_confirmation_record_scaffold")
        self.assertEqual(report["scope"], "offline final evidence selection policy human closeout confirmation scaffold only")
        self.assertEqual(report["confirmation_gate"]["status"], "pending_user_confirmation")
        self.assertEqual(report["confirmation_gate"]["allowed_use"], "user_confirmation_record_scaffold_only")
        self.assertTrue(report["confirmation_gate"]["requires_user_confirmation"])
        self.assertFalse(report["confirmation_gate"]["user_confirmation_recorded"])
        self.assertFalse(report["confirmation_gate"]["formal_human_outcome_recorded"])
        self.assertFalse(report["confirmation_gate"]["captures_formal_review_outcome"])
        self.assertFalse(report["confirmation_gate"]["implementation_allowed"])
        self.assertFalse(report["confirmation_gate"]["code_patch_authorized"])
        self.assertEqual(report["confirmation_gate"]["rag_query_integration"], "disallowed")
        self.assertEqual(report["confirmation_gate"]["blockers"], [])

        summary = report["summary"]
        self.assertEqual(summary["confirmation_row_count"], EXPECTED_DRAFT_ROW_COUNT)
        self.assertEqual(summary["source_draft_row_count"], EXPECTED_DRAFT_ROW_COUNT)
        self.assertEqual(summary["unique_case_count"], EXPECTED_CASE_COUNT)
        self.assertEqual(summary["priority_summary"], {"P0": 5, "P1": 3})
        self.assertEqual(summary["pending_user_confirmation_count"], EXPECTED_DRAFT_ROW_COUNT)
        self.assertTrue(summary["requires_user_confirmation"])
        self.assertFalse(summary["user_confirmation_recorded"])
        self.assertFalse(summary["formal_human_outcome_recorded"])
        self.assertFalse(summary["implementation_allowed"])

        rows = report["confirmation_scaffold_rows"]
        self.assertEqual(len(rows), EXPECTED_DRAFT_ROW_COUNT)
        self.assertEqual([row["policy_category"] for row in rows], EXPECTED_POLICY_CATEGORIES)
        for row in rows:
            self.assertEqual(row["confirmation_status"], "pending_user_confirmation")
            self.assertTrue(row["user_confirmation_required"])
            self.assertFalse(row["user_confirmation_recorded"])
            self.assertFalse(row["formal_human_outcome_recorded"])
            self.assertFalse(row["captures_formal_review_outcome"])
            self.assertFalse(row["candidate_route_authorized"])
            self.assertFalse(row["implementation_allowed"])
            self.assertFalse(row["code_patch_authorized"])
            self.assertEqual(row["runtime_adoption_status"], "not_allowed")
            self.assertTrue(row["suggested_closeout_option"])
            self.assertTrue(row["confirmation_prompt"])
            self.assertTrue(row["required_confirmation_basis"])
            self.assertTrue(row["source_case_ids"])
            self.assertIsNone(row["empty_confirmation_fields"]["selected_option"])
            self.assertIsNone(row["empty_confirmation_fields"]["confirmed_by_user"])

        packet = report["confirmation_packet"]
        self.assertFalse(packet["formal_review_outcome_captured"])
        self.assertFalse(packet["user_confirmation_recorded"])
        self.assertFalse(packet["importer_compatible"])
        self.assertEqual(len(packet["recommended_confirmation_order"]), EXPECTED_DRAFT_ROW_COUNT)

        self.assertEqual(report["next_version_handoff"]["recommended_next_step"], "wait_for_explicit_user_confirmation")
        self.assertFalse(report["next_version_handoff"]["runtime_implementation_allowed"])
        self.assertTrue(all(item["status"] == "passed" for item in report["assertions"]))
        for node in walk_dicts(report):
            self.assertFalse(FORBIDDEN_OUTPUT_KEYS & set(node.keys()))

    def test_blocked_or_wrong_source_draft_blocks_confirmation_scaffold(self):
        draft = load_current_draft()
        draft["version"] = "0.4.8.4"
        draft["schema_kind"] = "wrong_schema"
        draft["draft_gate"]["status"] = "blocked"
        draft["draft_gate"]["blockers"] = ["source_problem"]

        report = build_with_draft(draft)

        self.assertEqual(report["confirmation_gate"]["status"], "blocked")
        self.assertFalse(report["confirmation_gate"]["confirmation_scaffold_allowed"])
        self.assertIn("draft_version_mismatch", report["confirmation_gate"]["blockers"])
        self.assertIn("draft_schema_mismatch", report["confirmation_gate"]["blockers"])
        self.assertIn("draft_gate_not_pending", report["confirmation_gate"]["blockers"])
        self.assertIn("draft_gate_has_blockers", report["confirmation_gate"]["blockers"])
        self.assertEqual(assertion_status(report, "source_draft_is_ready_for_confirmation_scaffold"), "failed")

    def test_implementation_or_formal_outcome_in_source_blocks_confirmation_scaffold(self):
        draft = load_current_draft()
        draft["draft_gate"]["implementation_allowed"] = True
        draft["draft_gate"]["code_patch_authorized"] = True
        draft["draft_gate"]["formal_human_outcome_recorded"] = True
        draft["decision_draft_rows"][0]["candidate_route_authorized"] = True
        draft["decision_draft_rows"][0]["implementation_allowed"] = True
        draft["decision_draft_rows"][0]["formal_human_outcome_recorded"] = True

        report = build_with_draft(draft)

        self.assertEqual(report["confirmation_gate"]["status"], "blocked")
        self.assertIn("draft_implementation_not_blocked", report["confirmation_gate"]["blockers"])
        self.assertIn("draft_code_patch_not_blocked", report["confirmation_gate"]["blockers"])
        self.assertIn("draft_records_formal_outcome", report["confirmation_gate"]["blockers"])
        self.assertIn("draft_row_route_authorized", report["confirmation_gate"]["blockers"])
        self.assertIn("draft_row_implementation_not_blocked", report["confirmation_gate"]["blockers"])
        self.assertIn("draft_row_formal_outcome_not_blocked", report["confirmation_gate"]["blockers"])
        self.assertFalse(report["implementation_gate"]["implementation_allowed"])

    def test_draft_row_count_or_order_drift_blocks_confirmation_scaffold(self):
        draft = load_current_draft()
        draft["decision_draft_rows"] = list(reversed(draft["decision_draft_rows"][:-1]))
        draft["summary"]["draft_row_count"] = 7
        draft["summary"]["unique_case_count"] = 4

        report = build_with_draft(draft)

        self.assertEqual(report["confirmation_gate"]["status"], "blocked")
        self.assertIn("draft_row_count_summary_drift", report["confirmation_gate"]["blockers"])
        self.assertIn("draft_row_count_drift", report["confirmation_gate"]["blockers"])
        self.assertIn("draft_case_count_drift", report["confirmation_gate"]["blockers"])
        self.assertIn("draft_policy_category_order_drift", report["confirmation_gate"]["blockers"])
        self.assertIn("draft_policy_id_order_drift", report["confirmation_gate"]["blockers"])
        self.assertEqual(assertion_status(report, "confirmation_scaffold_has_eight_rows"), "failed")

    def test_forbidden_or_advisory_source_keys_block_confirmation_scaffold(self):
        draft = load_current_draft()
        draft["decision_draft_rows"][0]["implementation_plan"] = {"step": "should_not_exist"}
        draft["decision_draft_rows"][0]["ai_suggestion"] = True

        report = build_with_draft(draft)

        self.assertEqual(report["confirmation_gate"]["status"], "blocked")
        self.assertIn("draft_forbidden_key_present:implementation_plan", report["confirmation_gate"]["blockers"])
        self.assertIn("draft_advisory_signal_present:ai_suggestion", report["confirmation_gate"]["blockers"])
        for node in walk_dicts(report):
            self.assertFalse({"work_items", "engineering_tasks", "pending_tasks"} & set(node.keys()))

    def test_mojibake_like_text_blocks_human_readability_gate(self):
        draft = load_current_draft()
        draft["decision_draft_rows"][0]["draft_confirmation_question"] = "\u9428 damaged text"

        report = build_with_draft(draft)

        self.assertEqual(report["confirmation_gate"]["status"], "blocked")
        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("blocked_for_human_readability", report["confirmation_gate"]["blockers"])
        self.assertEqual(assertion_status(report, "text_readability_gate"), "failed")

    def test_markdown_is_scaffold_only_and_readable(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.8.6 Final Evidence Selection Policy Closeout Confirmation Record Scaffold", markdown)
        self.assertIn("does not record the user's actual confirmation", markdown)
        self.assertIn("## Confirmation Scaffold Rows", markdown)
        self.assertIn("## Confirmation Prompts", markdown)
        self.assertIn("`implementation_allowed=false`", markdown)
        self.assertIn("does not implement runtime policy", markdown)
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
            Path("tools/build_final_evidence_selection_policy_closeout_confirmation_record.py"),
            Path("docs/final_evidence_selection_policy_closeout_confirmation_record_v0.4.8.6.md"),
            Path("tests/final_evidence_selection_policy_closeout_confirmation_record_report.json"),
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
