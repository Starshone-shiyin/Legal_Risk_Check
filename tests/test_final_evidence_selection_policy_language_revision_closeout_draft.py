import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_final_evidence_selection_policy_language_revision_closeout_draft import (
    CLOSEOUT_DRAFT_PROFILES,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_WORKSHEET_PATH,
    EXPECTED_CASE_COUNT,
    EXPECTED_REVISION_CATEGORIES,
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


def load_current_worksheet() -> dict:
    return json.loads(
        Path("tests/final_evidence_selection_policy_language_revision_worksheet_report.json").read_text(
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
        path = Path(tmpdir) / "worksheet.json"
        write_json(path, copy.deepcopy(source))
        return build_report(path)


class FinalEvidenceSelectionPolicyLanguageRevisionCloseoutDraftTest(unittest.TestCase):
    def test_default_paths_use_legacy_report_and_docs_markdown_output(self):
        self.assertEqual(
            DEFAULT_WORKSHEET_PATH,
            legacy_report_path("final_evidence_selection_policy_language_revision_worksheet_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("final_evidence_selection_policy_language_revision_closeout_draft_report.json"),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/final_evidence_selection_policy_language_revision_closeout_draft_v0.4.8.9.md"),
        )

    def test_real_current_worksheet_builds_user_confirmation_draft(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.8.9")
        self.assertEqual(report["schema_kind"], "final_evidence_selection_policy_language_revision_closeout_draft")
        self.assertEqual(report["scope"], "offline final evidence selection policy language revision closeout draft only")
        self.assertEqual(report["draft_gate"]["status"], "draft_pending_user_confirmation")
        self.assertEqual(report["draft_gate"]["allowed_use"], "user_confirmation_draft_only")
        self.assertTrue(report["draft_gate"]["requires_user_confirmation"])
        self.assertFalse(report["draft_gate"]["formal_policy_language_outcome_recorded"])
        self.assertFalse(report["draft_gate"]["final_policy_wording_recorded"])
        self.assertFalse(report["draft_gate"]["implementation_allowed"])
        self.assertFalse(report["draft_gate"]["code_patch_authorized"])
        self.assertFalse(report["draft_gate"]["runtime_policy_implementation_allowed"])
        self.assertFalse(report["draft_gate"]["runtime_selection_policy_patch_allowed"])
        self.assertFalse(report["draft_gate"]["rerank_change_allowed"])
        self.assertFalse(report["draft_gate"]["prompt_change_allowed"])
        self.assertEqual(report["draft_gate"]["rag_query_integration"], "disallowed")
        self.assertEqual(report["draft_gate"]["blockers"], [])

        summary = report["summary"]
        self.assertEqual(summary["draft_row_count"], 3)
        self.assertEqual(summary["source_worksheet_row_count"], 3)
        self.assertEqual(summary["unique_case_count"], EXPECTED_CASE_COUNT)
        self.assertEqual(summary["revision_categories"], EXPECTED_REVISION_CATEGORIES)
        self.assertEqual(summary["priority_summary"], {"P0": 1, "P1": 2})
        self.assertTrue(summary["requires_user_confirmation"])
        self.assertFalse(summary["formal_policy_language_outcome_recorded"])
        self.assertFalse(summary["final_policy_wording_recorded"])
        self.assertFalse(summary["implementation_allowed"])

        rows = report["language_revision_closeout_draft_rows"]
        self.assertEqual([row["policy_category"] for row in rows], EXPECTED_REVISION_CATEGORIES)
        for row in rows:
            category = row["policy_category"]
            profile = CLOSEOUT_DRAFT_PROFILES[category]
            self.assertEqual(row["draft_status"], "draft_pending_user_confirmation")
            self.assertTrue(row["requires_user_confirmation"])
            self.assertFalse(row["formal_policy_language_outcome_recorded"])
            self.assertFalse(row["final_policy_wording_recorded"])
            self.assertEqual(row["suggested_policy_wording"], profile["suggested_policy_wording"])
            self.assertEqual(row["must_not_mean"], profile["must_not_mean"])
            self.assertEqual(row["acceptance_boundary"], profile["acceptance_boundary"])
            self.assertEqual(row["confirmation_question"], profile["confirmation_question"])
            self.assertTrue(row["source_wording_risk"])
            self.assertTrue(row["source_target_boundary"])
            self.assertTrue(row["source_simulation_entry_condition"])
            self.assertTrue(row["source_case_ids"])
            self.assertTrue(row["prohibited_now"])
            self.assertFalse(row["implementation_allowed"])
            self.assertFalse(row["code_patch_authorized"])
            self.assertEqual(row["runtime_adoption_status"], "not_allowed")

        packet = report["user_confirmation_packet"]
        self.assertTrue(packet["requires_user_confirmation"])
        self.assertFalse(packet["formal_policy_language_outcome_captured"])
        self.assertFalse(packet["final_policy_wording_recorded"])
        self.assertFalse(packet["importer_compatible"])
        self.assertEqual(len(packet["recommended_review_order"]), 3)
        self.assertEqual(len(packet["confirmation_questions"]), 3)
        self.assertFalse(report["next_version_handoff"]["may_enter_offline_simulation_design"])
        self.assertTrue(report["next_version_handoff"]["requires_user_confirmation_first"])
        self.assertTrue(all(item["status"] == "passed" for item in report["assertions"]))
        for node in walk_dicts(report):
            self.assertFalse(FORBIDDEN_OUTPUT_KEYS & set(node.keys()))

    def test_wrong_or_blocked_source_worksheet_blocks_draft(self):
        source = load_current_worksheet()
        source["version"] = "0.4.8.7"
        source["schema_kind"] = "wrong_schema"
        source["worksheet_gate"]["status"] = "blocked"
        source["worksheet_gate"]["blockers"] = ["source_problem"]

        report = build_with_source(source)

        self.assertEqual(report["draft_gate"]["status"], "blocked")
        self.assertIn("source_version_mismatch", report["draft_gate"]["blockers"])
        self.assertIn("source_schema_mismatch", report["draft_gate"]["blockers"])
        self.assertIn("source_gate_not_ready", report["draft_gate"]["blockers"])
        self.assertIn("source_gate_has_blockers", report["draft_gate"]["blockers"])
        self.assertEqual(assertion_status(report, "source_worksheet_is_ready_for_closeout_draft"), "failed")

    def test_source_implementation_or_formal_wording_blocks_draft(self):
        source = load_current_worksheet()
        source["worksheet_gate"]["implementation_allowed"] = True
        source["worksheet_gate"]["code_patch_authorized"] = True
        source["worksheet_gate"]["formal_policy_language_outcome_recorded"] = True
        source["revision_worksheet_rows"][0]["implementation_allowed"] = True
        source["revision_worksheet_rows"][0]["runtime_adoption_status"] = "allowed"

        report = build_with_source(source)

        self.assertEqual(report["draft_gate"]["status"], "blocked")
        self.assertIn("source_implementation_not_blocked", report["draft_gate"]["blockers"])
        self.assertIn("source_code_patch_not_blocked", report["draft_gate"]["blockers"])
        self.assertIn("source_formal_language_outcome_present", report["draft_gate"]["blockers"])
        self.assertIn("source_row_implementation_not_blocked:liability", report["draft_gate"]["blockers"])
        self.assertIn("source_row_runtime_not_blocked:liability", report["draft_gate"]["blockers"])
        self.assertFalse(report["implementation_gate"]["implementation_allowed"])

    def test_revision_row_count_or_order_drift_blocks_draft(self):
        source = load_current_worksheet()
        source["revision_worksheet_rows"] = list(reversed(source["revision_worksheet_rows"]))
        source["summary"]["revision_row_count"] = 2
        source["summary"]["unique_case_count"] = 3
        source["simulation_design_dependency"]["revision_categories_required_first"] = ["liability"]

        report = build_with_source(source)

        self.assertEqual(report["draft_gate"]["status"], "blocked")
        self.assertIn("source_revision_row_count_drift", report["draft_gate"]["blockers"])
        self.assertIn("source_case_count_drift", report["draft_gate"]["blockers"])
        self.assertIn("source_revision_category_order_drift", report["draft_gate"]["blockers"])
        self.assertIn("source_dependency_revision_categories_drift", report["draft_gate"]["blockers"])
        self.assertEqual(assertion_status(report, "draft_categories_are_expected"), "failed")

    def test_missing_source_language_fields_blocks_draft(self):
        source = load_current_worksheet()
        source["revision_worksheet_rows"][0]["wording_risk"] = ""
        source["revision_worksheet_rows"][0]["target_boundary"] = ""
        source["revision_worksheet_rows"][0]["simulation_entry_condition"] = ""

        report = build_with_source(source)

        self.assertEqual(report["draft_gate"]["status"], "blocked")
        self.assertIn("source_row_missing_wording_risk:liability", report["draft_gate"]["blockers"])
        self.assertIn("source_row_missing_target_boundary:liability", report["draft_gate"]["blockers"])
        self.assertIn("source_row_missing_simulation_entry_condition:liability", report["draft_gate"]["blockers"])

    def test_forbidden_or_advisory_source_keys_block_draft(self):
        source = load_current_worksheet()
        source["revision_worksheet_rows"][0]["implementation_plan"] = {"step": "should_not_exist"}
        source["revision_worksheet_rows"][0]["ai_suggestion"] = True

        report = build_with_source(source)

        self.assertEqual(report["draft_gate"]["status"], "blocked")
        self.assertIn("source_forbidden_key_present:implementation_plan", report["draft_gate"]["blockers"])
        self.assertIn("source_advisory_signal_present:ai_suggestion", report["draft_gate"]["blockers"])
        for node in walk_dicts(report):
            self.assertFalse({"work_items", "engineering_tasks", "pending_tasks"} & set(node.keys()))

    def test_mojibake_like_text_blocks_human_readability_gate(self):
        source = load_current_worksheet()
        source["revision_worksheet_rows"][0]["wording_risk"] = "\u9428 damaged text"

        report = build_with_source(source)

        self.assertEqual(report["draft_gate"]["status"], "blocked")
        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("blocked_for_human_readability", report["draft_gate"]["blockers"])
        self.assertEqual(assertion_status(report, "text_readability_gate"), "failed")

    def test_markdown_is_confirmation_draft_only_and_readable(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.8.9 Final Evidence Selection Policy Language Revision Closeout Draft", markdown)
        self.assertIn("pending user confirmation", markdown)
        self.assertIn("liability", markdown)
        self.assertIn("scenario_core", markdown)
        self.assertIn("coverage_floor", markdown)
        self.assertIn("This draft does not finalize policy wording", markdown)
        self.assertIn("`implementation_allowed=false`", markdown)
        self.assertIn("Offline simulation design remains blocked", markdown)
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
            Path("tools/build_final_evidence_selection_policy_language_revision_closeout_draft.py"),
            Path("docs/final_evidence_selection_policy_language_revision_closeout_draft_v0.4.8.9.md"),
            Path("tests/final_evidence_selection_policy_language_revision_closeout_draft_report.json"),
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
