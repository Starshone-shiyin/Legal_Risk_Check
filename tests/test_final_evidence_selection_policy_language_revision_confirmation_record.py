import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_final_evidence_selection_policy_language_revision_confirmation_record import (
    DEFAULT_DRAFT_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    EXPECTED_CASE_COUNT,
    EXPECTED_REVISION_CATEGORIES,
    FORBIDDEN_OUTPUT_KEYS,
    USER_CONFIRMATION_TEXT,
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
        Path("tests/final_evidence_selection_policy_language_revision_closeout_draft_report.json").read_text(
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


def build_with_source(source: dict) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "draft.json"
        write_json(path, copy.deepcopy(source))
        return build_report(path)


class FinalEvidenceSelectionPolicyLanguageRevisionConfirmationRecordTest(unittest.TestCase):
    def test_default_paths_use_legacy_report_and_docs_markdown_output(self):
        self.assertEqual(
            DEFAULT_DRAFT_PATH,
            legacy_report_path("final_evidence_selection_policy_language_revision_closeout_draft_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("final_evidence_selection_policy_language_revision_confirmation_record_report.json"),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/final_evidence_selection_policy_language_revision_confirmation_record_v0.4.8.10.md"),
        )

    def test_real_current_draft_builds_confirmation_record(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.8.10")
        self.assertEqual(report["schema_kind"], "final_evidence_selection_policy_language_revision_confirmation_record")
        self.assertEqual(report["scope"], "offline final evidence selection policy language revision confirmation record only")
        self.assertEqual(report["confirmation_gate"]["status"], "confirmed_for_future_offline_simulation_design")
        self.assertEqual(report["confirmation_gate"]["allowed_use"], "offline_simulation_design_input_only")
        self.assertTrue(report["confirmation_gate"]["user_confirmation_recorded"])
        self.assertTrue(report["confirmation_gate"]["policy_language_outcome_recorded"])
        self.assertTrue(report["confirmation_gate"]["confirmed_wording_for_offline_design_only"])
        self.assertTrue(report["confirmation_gate"]["may_enter_offline_simulation_design"])
        self.assertFalse(report["confirmation_gate"]["implementation_allowed"])
        self.assertFalse(report["confirmation_gate"]["code_patch_authorized"])
        self.assertFalse(report["confirmation_gate"]["runtime_policy_implementation_allowed"])
        self.assertFalse(report["confirmation_gate"]["runtime_selection_policy_patch_allowed"])
        self.assertFalse(report["confirmation_gate"]["rerank_change_allowed"])
        self.assertFalse(report["confirmation_gate"]["prompt_change_allowed"])
        self.assertEqual(report["confirmation_gate"]["rag_query_integration"], "disallowed")
        self.assertEqual(report["confirmation_gate"]["blockers"], [])

        context = report["confirmation_context"]
        self.assertEqual(context["user_confirmation_text"], USER_CONFIRMATION_TEXT)
        self.assertEqual(context["confirmation_scope"], EXPECTED_REVISION_CATEGORIES)
        self.assertEqual(context["implementation_authorization"], "not_granted")

        summary = report["summary"]
        self.assertEqual(summary["confirmed_row_count"], 3)
        self.assertEqual(summary["source_draft_row_count"], 3)
        self.assertEqual(summary["unique_case_count"], EXPECTED_CASE_COUNT)
        self.assertEqual(summary["revision_categories"], EXPECTED_REVISION_CATEGORIES)
        self.assertEqual(summary["priority_summary"], {"P0": 1, "P1": 2})
        self.assertEqual(summary["user_confirmation_text"], USER_CONFIRMATION_TEXT)
        self.assertTrue(summary["policy_language_outcome_recorded"])
        self.assertTrue(summary["confirmed_wording_for_offline_design_only"])
        self.assertFalse(summary["implementation_allowed"])

        rows = report["confirmed_language_revision_rows"]
        self.assertEqual([row["policy_category"] for row in rows], EXPECTED_REVISION_CATEGORIES)
        for row in rows:
            self.assertEqual(row["confirmation_status"], "confirmed_by_user")
            self.assertTrue(row["user_confirmation_recorded"])
            self.assertEqual(row["user_confirmation_text"], USER_CONFIRMATION_TEXT)
            self.assertTrue(row["confirmed_policy_wording"])
            self.assertTrue(row["confirmed_must_not_mean"])
            self.assertTrue(row["confirmed_acceptance_boundary"])
            self.assertEqual(row["confirmed_post_confirmation_route"], "future_offline_simulation_design_candidate")
            self.assertTrue(row["offline_simulation_design_input_allowed"])
            self.assertFalse(row["runtime_policy_implementation_allowed"])
            self.assertFalse(row["implementation_allowed"])
            self.assertFalse(row["code_patch_authorized"])
            self.assertEqual(row["runtime_adoption_status"], "not_allowed")
            self.assertTrue(row["source_case_ids"])

        handoff = report["offline_simulation_design_handoff"]
        self.assertEqual(handoff["handoff_status"], "ready_for_future_offline_simulation_design")
        self.assertEqual(handoff["confirmed_revision_categories"], EXPECTED_REVISION_CATEGORIES)
        self.assertFalse(handoff["runtime_implementation_allowed"])
        self.assertTrue(handoff["requires_new_version_before_any_simulation_or_runtime_work"])
        self.assertTrue(all(item["status"] == "passed" for item in report["assertions"]))
        for node in walk_dicts(report):
            self.assertFalse(FORBIDDEN_OUTPUT_KEYS & set(node.keys()))

    def test_wrong_or_blocked_source_draft_blocks_confirmation(self):
        source = load_current_draft()
        source["version"] = "0.4.8.8"
        source["schema_kind"] = "wrong_schema"
        source["draft_gate"]["status"] = "blocked"
        source["draft_gate"]["blockers"] = ["source_problem"]

        report = build_with_source(source)

        self.assertEqual(report["confirmation_gate"]["status"], "blocked")
        self.assertIn("source_version_mismatch", report["confirmation_gate"]["blockers"])
        self.assertIn("source_schema_mismatch", report["confirmation_gate"]["blockers"])
        self.assertIn("source_gate_not_pending_confirmation", report["confirmation_gate"]["blockers"])
        self.assertIn("source_gate_has_blockers", report["confirmation_gate"]["blockers"])
        self.assertEqual(assertion_status(report, "source_draft_is_ready_for_confirmation"), "failed")

    def test_source_implementation_or_existing_final_wording_blocks_confirmation(self):
        source = load_current_draft()
        source["draft_gate"]["implementation_allowed"] = True
        source["draft_gate"]["code_patch_authorized"] = True
        source["draft_gate"]["final_policy_wording_recorded"] = True
        source["language_revision_closeout_draft_rows"][0]["implementation_allowed"] = True
        source["language_revision_closeout_draft_rows"][0]["final_policy_wording_recorded"] = True

        report = build_with_source(source)

        self.assertEqual(report["confirmation_gate"]["status"], "blocked")
        self.assertIn("source_implementation_not_blocked", report["confirmation_gate"]["blockers"])
        self.assertIn("source_code_patch_not_blocked", report["confirmation_gate"]["blockers"])
        self.assertIn("source_already_records_final_wording", report["confirmation_gate"]["blockers"])
        self.assertIn("source_row_implementation_not_blocked:liability", report["confirmation_gate"]["blockers"])
        self.assertIn("source_row_already_records_final_wording:liability", report["confirmation_gate"]["blockers"])
        self.assertFalse(report["implementation_gate"]["implementation_allowed"])

    def test_draft_row_count_or_order_drift_blocks_confirmation(self):
        source = load_current_draft()
        source["language_revision_closeout_draft_rows"] = list(reversed(source["language_revision_closeout_draft_rows"]))
        source["summary"]["draft_row_count"] = 2
        source["summary"]["unique_case_count"] = 3

        report = build_with_source(source)

        self.assertEqual(report["confirmation_gate"]["status"], "blocked")
        self.assertIn("source_draft_row_count_drift", report["confirmation_gate"]["blockers"])
        self.assertIn("source_case_count_drift", report["confirmation_gate"]["blockers"])
        self.assertIn("source_category_order_drift", report["confirmation_gate"]["blockers"])
        self.assertEqual(assertion_status(report, "confirmation_categories_are_expected"), "failed")

    def test_missing_source_wording_fields_blocks_confirmation(self):
        source = load_current_draft()
        source["language_revision_closeout_draft_rows"][0]["suggested_policy_wording"] = ""
        source["language_revision_closeout_draft_rows"][0]["must_not_mean"] = ""
        source["language_revision_closeout_draft_rows"][0]["acceptance_boundary"] = ""
        source["language_revision_closeout_draft_rows"][0]["confirmation_question"] = ""

        report = build_with_source(source)

        self.assertEqual(report["confirmation_gate"]["status"], "blocked")
        self.assertIn("source_row_missing_suggested_policy_wording:liability", report["confirmation_gate"]["blockers"])
        self.assertIn("source_row_missing_must_not_mean:liability", report["confirmation_gate"]["blockers"])
        self.assertIn("source_row_missing_acceptance_boundary:liability", report["confirmation_gate"]["blockers"])
        self.assertIn("source_row_missing_confirmation_question:liability", report["confirmation_gate"]["blockers"])

    def test_forbidden_or_advisory_source_keys_block_confirmation(self):
        source = load_current_draft()
        source["language_revision_closeout_draft_rows"][0]["implementation_plan"] = {"step": "should_not_exist"}
        source["language_revision_closeout_draft_rows"][0]["ai_suggestion"] = True

        report = build_with_source(source)

        self.assertEqual(report["confirmation_gate"]["status"], "blocked")
        self.assertIn("source_forbidden_key_present:implementation_plan", report["confirmation_gate"]["blockers"])
        self.assertIn("source_advisory_signal_present:ai_suggestion", report["confirmation_gate"]["blockers"])
        for node in walk_dicts(report):
            self.assertFalse({"work_items", "engineering_tasks", "pending_tasks"} & set(node.keys()))

    def test_mojibake_like_text_blocks_human_readability_gate(self):
        source = load_current_draft()
        source["language_revision_closeout_draft_rows"][0]["suggested_policy_wording"] = "\u9428 damaged text"

        report = build_with_source(source)

        self.assertEqual(report["confirmation_gate"]["status"], "blocked")
        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("blocked_for_human_readability", report["confirmation_gate"]["blockers"])
        self.assertEqual(assertion_status(report, "text_readability_gate"), "failed")

    def test_markdown_is_confirmation_record_only_and_readable(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.8.10 Final Evidence Selection Policy Language Revision Confirmation Record", markdown)
        self.assertIn("User confirmation text: 确认以上三条。", markdown)
        self.assertIn("Confirmed wording", markdown)
        self.assertIn("liability", markdown)
        self.assertIn("scenario_core", markdown)
        self.assertIn("coverage_floor", markdown)
        self.assertIn("Confirmed wording may be used only as future offline simulation design input", markdown)
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
            Path("tools/build_final_evidence_selection_policy_language_revision_confirmation_record.py"),
            Path("docs/final_evidence_selection_policy_language_revision_confirmation_record_v0.4.8.10.md"),
            Path("tests/final_evidence_selection_policy_language_revision_confirmation_record_report.json"),
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
