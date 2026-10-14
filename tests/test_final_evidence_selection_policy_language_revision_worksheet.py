import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_final_evidence_selection_policy_language_revision_worksheet import (
    DEFAULT_CONFIRMED_RECORD_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    EXPECTED_REVISION_CATEGORIES,
    EXPECTED_REVISION_ROUTE,
    EXPECTED_SIMULATION_CATEGORIES,
    FORBIDDEN_OUTPUT_KEYS,
    REVISION_GUIDANCE,
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


def load_current_confirmed_record() -> dict:
    return json.loads(
        Path("tests/final_evidence_selection_policy_closeout_confirmed_record_report.json").read_text(
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
        path = Path(tmpdir) / "confirmed.json"
        write_json(path, copy.deepcopy(source))
        return build_report(path)


class FinalEvidenceSelectionPolicyLanguageRevisionWorksheetTest(unittest.TestCase):
    def test_default_paths_use_legacy_report_and_docs_markdown_output(self):
        self.assertEqual(
            DEFAULT_CONFIRMED_RECORD_PATH,
            legacy_report_path("final_evidence_selection_policy_closeout_confirmed_record_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("final_evidence_selection_policy_language_revision_worksheet_report.json"),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/final_evidence_selection_policy_language_revision_worksheet_v0.4.8.8.md"),
        )

    def test_real_current_confirmed_record_builds_revision_worksheet(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.8.8")
        self.assertEqual(report["schema_kind"], "final_evidence_selection_policy_language_revision_worksheet")
        self.assertEqual(report["scope"], "offline final evidence selection policy language revision worksheet only")
        self.assertEqual(report["worksheet_gate"]["status"], "ready_for_policy_language_revision_review")
        self.assertEqual(report["worksheet_gate"]["allowed_use"], "policy_language_revision_worksheet_only")
        self.assertFalse(report["worksheet_gate"]["formal_policy_language_outcome_recorded"])
        self.assertFalse(report["worksheet_gate"]["implementation_allowed"])
        self.assertFalse(report["worksheet_gate"]["code_patch_authorized"])
        self.assertFalse(report["worksheet_gate"]["runtime_policy_implementation_allowed"])
        self.assertFalse(report["worksheet_gate"]["runtime_selection_policy_patch_allowed"])
        self.assertFalse(report["worksheet_gate"]["rerank_change_allowed"])
        self.assertFalse(report["worksheet_gate"]["prompt_change_allowed"])
        self.assertEqual(report["worksheet_gate"]["rag_query_integration"], "disallowed")
        self.assertEqual(report["worksheet_gate"]["blockers"], [])

        summary = report["summary"]
        self.assertEqual(summary["revision_row_count"], 3)
        self.assertEqual(summary["source_confirmed_row_count"], 8)
        self.assertEqual(summary["source_revision_row_count"], 3)
        self.assertEqual(summary["revision_categories"], EXPECTED_REVISION_CATEGORIES)
        self.assertEqual(summary["priority_summary"], {"P0": 1, "P1": 2})
        self.assertFalse(summary["implementation_allowed"])
        self.assertFalse(summary["code_patch_authorized"])

        rows = report["revision_worksheet_rows"]
        self.assertEqual([row["policy_category"] for row in rows], EXPECTED_REVISION_CATEGORIES)
        for row in rows:
            category = row["policy_category"]
            self.assertEqual(row["confirmed_followup_route"], EXPECTED_REVISION_ROUTE)
            self.assertEqual(row["worksheet_status"], "ready_for_policy_language_review")
            self.assertEqual(row["revision_focus"], REVISION_GUIDANCE[category]["revision_focus"])
            self.assertEqual(row["wording_risk"], REVISION_GUIDANCE[category]["wording_risk"])
            self.assertEqual(row["target_boundary"], REVISION_GUIDANCE[category]["target_boundary"])
            self.assertTrue(row["acceptance_checks"])
            self.assertTrue(row["review_questions"])
            self.assertTrue(row["source_case_ids"])
            self.assertFalse(row["implementation_allowed"])
            self.assertFalse(row["code_patch_authorized"])
            self.assertEqual(row["runtime_adoption_status"], "not_allowed")

        dependency = report["simulation_design_dependency"]
        self.assertEqual(dependency["accepted_categories_waiting_for_simulation_design"], EXPECTED_SIMULATION_CATEGORIES)
        self.assertEqual(dependency["revision_categories_required_first"], EXPECTED_REVISION_CATEGORIES)
        self.assertTrue(dependency["simulation_design_should_wait_for_revision_closeout"])
        self.assertFalse(dependency["runtime_implementation_allowed"])
        self.assertTrue(all(item["status"] == "passed" for item in report["assertions"]))
        for node in walk_dicts(report):
            self.assertFalse(FORBIDDEN_OUTPUT_KEYS & set(node.keys()))

    def test_wrong_or_blocked_source_record_blocks_worksheet(self):
        source = load_current_confirmed_record()
        source["version"] = "0.4.8.6"
        source["schema_kind"] = "wrong_schema"
        source["confirmation_gate"]["status"] = "blocked"
        source["confirmation_gate"]["blockers"] = ["source_problem"]

        report = build_with_source(source)

        self.assertEqual(report["worksheet_gate"]["status"], "blocked")
        self.assertIn("source_version_mismatch", report["worksheet_gate"]["blockers"])
        self.assertIn("source_schema_mismatch", report["worksheet_gate"]["blockers"])
        self.assertIn("source_gate_not_confirmed", report["worksheet_gate"]["blockers"])
        self.assertIn("source_gate_has_blockers", report["worksheet_gate"]["blockers"])
        self.assertEqual(assertion_status(report, "source_confirmed_record_is_ready_for_language_revision"), "failed")

    def test_source_implementation_or_missing_confirmation_blocks_worksheet(self):
        source = load_current_confirmed_record()
        source["confirmation_gate"]["user_confirmation_recorded"] = False
        source["confirmation_gate"]["implementation_allowed"] = True
        source["confirmation_gate"]["code_patch_authorized"] = True
        source["confirmed_rows"][3]["implementation_allowed"] = True
        source["confirmed_rows"][3]["candidate_route_authorized"] = True

        report = build_with_source(source)

        self.assertEqual(report["worksheet_gate"]["status"], "blocked")
        self.assertIn("source_user_confirmation_missing", report["worksheet_gate"]["blockers"])
        self.assertIn("source_implementation_not_blocked", report["worksheet_gate"]["blockers"])
        self.assertIn("source_code_patch_not_blocked", report["worksheet_gate"]["blockers"])
        self.assertIn("source_revision_row_implementation_not_blocked:liability", report["worksheet_gate"]["blockers"])
        self.assertIn("source_revision_row_route_authorized:liability", report["worksheet_gate"]["blockers"])
        self.assertFalse(report["implementation_gate"]["implementation_allowed"])

    def test_revision_count_or_order_drift_blocks_worksheet(self):
        source = load_current_confirmed_record()
        source["confirmed_rows"] = list(reversed(source["confirmed_rows"]))
        source["summary"]["confirmed_row_count"] = 7
        source["summary"]["unique_case_count"] = 4
        source["summary"]["confirmed_followup_route_summary"][EXPECTED_REVISION_ROUTE] = 2

        report = build_with_source(source)

        self.assertEqual(report["worksheet_gate"]["status"], "blocked")
        self.assertIn("source_row_count_summary_drift", report["worksheet_gate"]["blockers"])
        self.assertIn("source_case_count_drift", report["worksheet_gate"]["blockers"])
        self.assertIn("source_revision_route_count_drift", report["worksheet_gate"]["blockers"])
        self.assertIn("source_revision_category_order_drift", report["worksheet_gate"]["blockers"])
        self.assertEqual(assertion_status(report, "worksheet_categories_are_expected"), "failed")

    def test_forbidden_or_advisory_source_keys_block_worksheet(self):
        source = load_current_confirmed_record()
        source["confirmed_rows"][3]["implementation_plan"] = {"step": "should_not_exist"}
        source["confirmed_rows"][3]["ai_suggestion"] = True

        report = build_with_source(source)

        self.assertEqual(report["worksheet_gate"]["status"], "blocked")
        self.assertIn("source_forbidden_key_present:implementation_plan", report["worksheet_gate"]["blockers"])
        self.assertIn("source_advisory_signal_present:ai_suggestion", report["worksheet_gate"]["blockers"])
        for node in walk_dicts(report):
            self.assertFalse({"work_items", "engineering_tasks", "pending_tasks"} & set(node.keys()))

    def test_mojibake_like_text_blocks_human_readability_gate(self):
        source = load_current_confirmed_record()
        source["confirmed_rows"][3]["confirmation_basis"]["source_required_basis"] = "\u9428 damaged text"

        report = build_with_source(source)

        self.assertEqual(report["worksheet_gate"]["status"], "blocked")
        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("blocked_for_human_readability", report["worksheet_gate"]["blockers"])
        self.assertEqual(assertion_status(report, "text_readability_gate"), "failed")

    def test_markdown_is_revision_worksheet_only_and_readable(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.8.8 Final Evidence Selection Policy Language Revision Worksheet", markdown)
        self.assertIn("language review only", markdown)
        self.assertIn("liability", markdown)
        self.assertIn("scenario_core", markdown)
        self.assertIn("coverage_floor", markdown)
        self.assertIn("Simulation design should wait for revision closeout: True", markdown)
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
            Path("tools/build_final_evidence_selection_policy_language_revision_worksheet.py"),
            Path("docs/final_evidence_selection_policy_language_revision_worksheet_v0.4.8.8.md"),
            Path("tests/final_evidence_selection_policy_language_revision_worksheet_report.json"),
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
