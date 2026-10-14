import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_final_evidence_selection_policy_closeout_decision_draft import (
    DEFAULT_CLOSEOUT_REPORT_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    EXPECTED_CASE_COUNT,
    EXPECTED_CLOSEOUT_ROW_COUNT,
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


def load_current_closeout() -> dict:
    return json.loads(
        Path("tests/final_evidence_selection_policy_closeout_envelope_report.json").read_text(
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


def build_with_closeout(closeout: dict) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "closeout.json"
        write_json(path, copy.deepcopy(closeout))
        return build_report(path)


class FinalEvidenceSelectionPolicyCloseoutDecisionDraftTest(unittest.TestCase):
    def test_default_paths_use_legacy_report_and_docs_markdown_output(self):
        self.assertEqual(
            DEFAULT_CLOSEOUT_REPORT_PATH,
            legacy_report_path("final_evidence_selection_policy_closeout_envelope_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("final_evidence_selection_policy_closeout_decision_draft_report.json"),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/final_evidence_selection_policy_closeout_decision_draft_v0.4.8.5.md"),
        )

    def test_real_current_report_builds_user_confirmation_draft(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.8.5")
        self.assertEqual(report["schema_kind"], "final_evidence_selection_policy_closeout_decision_draft")
        self.assertEqual(report["scope"], "offline final evidence selection policy human closeout decision draft only")
        self.assertEqual(report["draft_gate"]["status"], "draft_pending_user_confirmation")
        self.assertEqual(report["draft_gate"]["allowed_use"], "user_confirmation_draft_only")
        self.assertTrue(report["draft_gate"]["requires_user_confirmation"])
        self.assertFalse(report["draft_gate"]["formal_human_outcome_recorded"])
        self.assertFalse(report["draft_gate"]["captures_formal_review_outcome"])
        self.assertFalse(report["draft_gate"]["draft_is_importable_decision"])
        self.assertFalse(report["draft_gate"]["implementation_allowed"])
        self.assertFalse(report["draft_gate"]["code_patch_authorized"])
        self.assertEqual(report["draft_gate"]["rag_query_integration"], "disallowed")
        self.assertEqual(report["draft_gate"]["blockers"], [])

        summary = report["summary"]
        self.assertEqual(summary["draft_row_count"], EXPECTED_CLOSEOUT_ROW_COUNT)
        self.assertEqual(summary["source_closeout_row_count"], EXPECTED_CLOSEOUT_ROW_COUNT)
        self.assertEqual(summary["unique_case_count"], EXPECTED_CASE_COUNT)
        self.assertEqual(summary["priority_summary"], {"P0": 5, "P1": 3})
        self.assertEqual(
            summary["suggested_closeout_option_summary"],
            {
                "accept_for_future_offline_simulation_design": 5,
                "revise_policy_language_before_closeout": 3,
            },
        )
        self.assertEqual(summary["next_version_recommendation"], "v0.4.8.6 policy table human closeout confirmation record")
        self.assertTrue(summary["requires_user_confirmation"])
        self.assertFalse(summary["formal_human_outcome_recorded"])
        self.assertFalse(summary["implementation_allowed"])

        rows = report["decision_draft_rows"]
        self.assertEqual(len(rows), EXPECTED_CLOSEOUT_ROW_COUNT)
        self.assertEqual([row["policy_category"] for row in rows], EXPECTED_POLICY_CATEGORIES)
        for row in rows:
            self.assertEqual(row["draft_status"], "draft_pending_user_confirmation")
            self.assertTrue(row["requires_user_confirmation"])
            self.assertFalse(row["formal_human_outcome_recorded"])
            self.assertFalse(row["captures_formal_review_outcome"])
            self.assertFalse(row["draft_is_importable_decision"])
            self.assertFalse(row["candidate_route_authorized"])
            self.assertFalse(row["implementation_allowed"])
            self.assertFalse(row["code_patch_authorized"])
            self.assertEqual(row["runtime_adoption_status"], "not_allowed")
            self.assertTrue(row["suggested_closeout_option"])
            self.assertTrue(row["draft_confirmation_question"])
            self.assertTrue(row["required_confirmation_basis"])
            self.assertTrue(row["draft_next_step"])
            self.assertTrue(row["source_case_ids"])
            self.assertTrue(row["prohibited_now"])

        packet = report["user_confirmation_packet"]
        self.assertFalse(packet["formal_review_outcome_captured"])
        self.assertFalse(packet["importer_compatible"])
        self.assertEqual(len(packet["recommended_review_order"]), EXPECTED_CLOSEOUT_ROW_COUNT)
        self.assertIn("accept_for_future_offline_simulation_design", packet["allowed_draft_options"])

        self.assertEqual(report["next_version_handoff"]["recommended_next_version"], "v0.4.8.6")
        self.assertFalse(report["next_version_handoff"]["runtime_implementation_allowed"])
        self.assertTrue(all(item["status"] == "passed" for item in report["assertions"]))
        for node in walk_dicts(report):
            self.assertFalse(FORBIDDEN_OUTPUT_KEYS & set(node.keys()))

    def test_blocked_or_wrong_source_closeout_blocks_draft(self):
        closeout = load_current_closeout()
        closeout["version"] = "0.4.8.3"
        closeout["schema_kind"] = "wrong_schema"
        closeout["closeout_gate"]["status"] = "blocked"
        closeout["closeout_gate"]["blockers"] = ["source_problem"]

        report = build_with_closeout(closeout)

        self.assertEqual(report["draft_gate"]["status"], "blocked")
        self.assertFalse(report["draft_gate"]["decision_draft_allowed"])
        self.assertIn("closeout_version_mismatch", report["draft_gate"]["blockers"])
        self.assertIn("closeout_schema_mismatch", report["draft_gate"]["blockers"])
        self.assertIn("closeout_gate_not_pending", report["draft_gate"]["blockers"])
        self.assertIn("closeout_gate_has_blockers", report["draft_gate"]["blockers"])
        self.assertEqual(assertion_status(report, "source_closeout_is_ready_for_decision_draft"), "failed")

    def test_implementation_or_formal_outcome_in_source_blocks_draft(self):
        closeout = load_current_closeout()
        closeout["closeout_gate"]["implementation_allowed"] = True
        closeout["closeout_gate"]["code_patch_authorized"] = True
        closeout["closeout_gate"]["formal_human_outcome_recorded"] = True
        closeout["closeout_rows"][0]["candidate_route_authorized"] = True
        closeout["closeout_rows"][0]["implementation_allowed"] = True
        closeout["closeout_rows"][0]["formal_human_outcome_recorded"] = True

        report = build_with_closeout(closeout)

        self.assertEqual(report["draft_gate"]["status"], "blocked")
        self.assertIn("closeout_implementation_not_blocked", report["draft_gate"]["blockers"])
        self.assertIn("closeout_code_patch_not_blocked", report["draft_gate"]["blockers"])
        self.assertIn("closeout_records_formal_outcome", report["draft_gate"]["blockers"])
        self.assertIn("closeout_row_route_authorized", report["draft_gate"]["blockers"])
        self.assertIn("closeout_row_implementation_not_blocked", report["draft_gate"]["blockers"])
        self.assertIn("closeout_row_formal_outcome_not_blocked", report["draft_gate"]["blockers"])
        self.assertFalse(report["implementation_gate"]["implementation_allowed"])

    def test_closeout_row_count_or_order_drift_blocks_draft(self):
        closeout = load_current_closeout()
        closeout["closeout_rows"] = list(reversed(closeout["closeout_rows"][:-1]))
        closeout["summary"]["closeout_row_count"] = 7
        closeout["summary"]["unique_case_count"] = 4

        report = build_with_closeout(closeout)

        self.assertEqual(report["draft_gate"]["status"], "blocked")
        self.assertIn("closeout_row_count_summary_drift", report["draft_gate"]["blockers"])
        self.assertIn("closeout_row_count_drift", report["draft_gate"]["blockers"])
        self.assertIn("closeout_case_count_drift", report["draft_gate"]["blockers"])
        self.assertIn("closeout_policy_category_order_drift", report["draft_gate"]["blockers"])
        self.assertIn("closeout_policy_id_order_drift", report["draft_gate"]["blockers"])
        self.assertEqual(assertion_status(report, "draft_has_eight_rows"), "failed")

    def test_forbidden_or_advisory_source_keys_block_draft(self):
        closeout = load_current_closeout()
        closeout["closeout_rows"][0]["implementation_plan"] = {"step": "should_not_exist"}
        closeout["closeout_rows"][0]["ai_suggestion"] = True

        report = build_with_closeout(closeout)

        self.assertEqual(report["draft_gate"]["status"], "blocked")
        self.assertIn("closeout_forbidden_key_present:implementation_plan", report["draft_gate"]["blockers"])
        self.assertIn("closeout_advisory_signal_present:ai_suggestion", report["draft_gate"]["blockers"])
        for node in walk_dicts(report):
            self.assertFalse({"work_items", "engineering_tasks", "pending_tasks"} & set(node.keys()))

    def test_mojibake_like_text_blocks_human_readability_gate(self):
        closeout = load_current_closeout()
        closeout["closeout_rows"][0]["closeout_question"] = "\u9428 damaged text"

        report = build_with_closeout(closeout)

        self.assertEqual(report["draft_gate"]["status"], "blocked")
        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("blocked_for_human_readability", report["draft_gate"]["blockers"])
        self.assertEqual(assertion_status(report, "text_readability_gate"), "failed")

    def test_markdown_is_draft_only_and_readable(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.8.5 Final Evidence Selection Policy Closeout Decision Draft", markdown)
        self.assertIn("This file is a user-confirmation draft", markdown)
        self.assertIn("## Decision Draft Rows", markdown)
        self.assertIn("## Confirmation Questions", markdown)
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
            Path("tools/build_final_evidence_selection_policy_closeout_decision_draft.py"),
            Path("docs/final_evidence_selection_policy_closeout_decision_draft_v0.4.8.5.md"),
            Path("tests/final_evidence_selection_policy_closeout_decision_draft_report.json"),
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
