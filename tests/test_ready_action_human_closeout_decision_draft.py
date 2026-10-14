import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_ready_action_human_closeout_decision_draft import (
    DEFAULT_CLOSEOUT_REPORT_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    EXPECTED_PENDING_EXCLUDED,
    EXPECTED_READY_ACTION_COUNT,
    EXPECTED_REVIEW_ORDER,
    EXPECTED_SOURCE_CASE_COUNT,
    EXPECTED_TRACK_COUNT,
    FORBIDDEN_OUTPUT_KEYS,
    build_report,
    render_markdown,
)


PROHIBITED_SOURCE_PATTERNS = [
    "rag_query(",
    "src.rag.retriever",
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


def walk_dicts(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_dicts(child)


def load_current_closeout() -> dict:
    return json.loads(Path("tests/ready_action_design_review_closeout_report.json").read_text(encoding="utf-8-sig"))


def assertion_status(report: dict, name: str) -> str | None:
    for assertion in report.get("assertions", []):
        if assertion.get("name") == name:
            return assertion.get("status")
    return None


def build_with_temp_closeout(closeout: dict) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "closeout.json"
        write_json(path, copy.deepcopy(closeout))
        return build_report(path)


class ReadyActionHumanCloseoutDecisionDraftTest(unittest.TestCase):
    def test_default_paths_use_legacy_report_and_docs_markdown_output(self):
        self.assertEqual(
            DEFAULT_CLOSEOUT_REPORT_PATH,
            legacy_report_path("ready_action_design_review_closeout_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("ready_action_human_closeout_decision_draft_report.json"),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/ready_action_human_closeout_decision_draft_v0.4.7.9.5.md"),
        )

    def test_real_current_closeout_builds_user_confirmation_draft(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.7.9.5")
        self.assertEqual(report["schema_kind"], "ready_action_human_closeout_decision_draft")
        self.assertEqual(report["scope"], "offline user-confirmation draft only")
        self.assertEqual(report["draft_gate"]["status"], "draft_pending_user_confirmation")
        self.assertEqual(report["draft_gate"]["allowed_use"], "user_confirmation_draft_only")
        self.assertTrue(report["draft_gate"]["requires_user_confirmation"])
        self.assertFalse(report["draft_gate"]["formal_human_outcome_recorded"])
        self.assertFalse(report["draft_gate"]["captures_formal_review_outcome"])
        self.assertFalse(report["draft_gate"]["draft_is_importable_decision"])
        self.assertFalse(report["draft_gate"]["implementation_allowed"])
        self.assertFalse(report["draft_gate"]["code_patch_authorized"])
        self.assertFalse(report["draft_gate"]["next_design_authorized"])
        self.assertEqual(report["draft_gate"]["handoff_to_implementation"], "not_allowed")
        self.assertEqual(report["draft_gate"]["blockers"], [])

        summary = report["summary"]
        self.assertEqual(summary["draft_track_count"], EXPECTED_TRACK_COUNT)
        self.assertEqual(summary["design_action_count"], EXPECTED_READY_ACTION_COUNT)
        self.assertEqual(summary["source_case_count"], EXPECTED_SOURCE_CASE_COUNT)
        self.assertEqual(summary["pending_records_excluded"], EXPECTED_PENDING_EXCLUDED)
        self.assertEqual(summary["priority_band_summary"], {"P0": 3, "P1": 2})
        self.assertTrue(summary["requires_user_confirmation"])
        self.assertFalse(summary["formal_human_outcome_recorded"])
        self.assertFalse(summary["draft_is_importable_decision"])
        self.assertFalse(summary["implementation_allowed"])
        self.assertFalse(summary["code_patch_authorized"])
        self.assertFalse(summary["next_design_authorized"])

        matrix = report["draft_matrix"]
        self.assertEqual(len(matrix), EXPECTED_TRACK_COUNT)
        self.assertEqual([row["action_type"] for row in matrix], EXPECTED_REVIEW_ORDER)
        self.assertEqual(
            sum(row["candidate_scope"]["ready_for_design_review_candidates"] for row in matrix),
            EXPECTED_READY_ACTION_COUNT,
        )
        for row in matrix:
            self.assertEqual(row["draft_status"], "draft_pending_user_confirmation")
            self.assertTrue(row["requires_user_confirmation"])
            self.assertFalse(row["formal_human_outcome_recorded"])
            self.assertFalse(row["captures_formal_review_outcome"])
            self.assertFalse(row["draft_is_importable_decision"])
            self.assertFalse(row["implementation_allowed"])
            self.assertFalse(row["code_patch_authorized"])
            self.assertFalse(row["next_design_authorized"])
            self.assertTrue(row["draft_option"])
            self.assertTrue(row["draft_closeout_direction"])
            self.assertTrue(row["draft_rationale"])
            self.assertTrue(row["draft_required_confirmation"])
            self.assertTrue(row["traceability"]["source_case_ids"])
            self.assertTrue(row["traceability"]["design_action_ids"])

        self.assertTrue(all(item["status"] == "passed" for item in report["assertions"]))
        for node in walk_dicts(report):
            self.assertFalse(FORBIDDEN_OUTPUT_KEYS & set(node.keys()))

    def test_blocked_source_closeout_blocks_draft(self):
        closeout = load_current_closeout()
        closeout["closeout_gate"]["status"] = "blocked"
        closeout["closeout_gate"]["blockers"] = ["not_ready"]

        report = build_with_temp_closeout(closeout)

        self.assertEqual(report["draft_gate"]["status"], "blocked")
        self.assertIn("closeout_gate_not_pending", report["draft_gate"]["blockers"])
        self.assertIn("closeout_gate_has_blockers", report["draft_gate"]["blockers"])
        self.assertFalse(report["implementation_gate"]["implementation_allowed"])
        self.assertFalse(report["implementation_gate"]["code_patch_authorized"])

    def test_wrong_closeout_schema_or_version_blocks_draft(self):
        closeout = load_current_closeout()
        closeout["version"] = "0.4.7.9.3"
        closeout["schema_kind"] = "wrong_schema"

        report = build_with_temp_closeout(closeout)

        self.assertEqual(report["draft_gate"]["status"], "blocked")
        self.assertIn("closeout_version_mismatch", report["draft_gate"]["blockers"])
        self.assertIn("closeout_schema_mismatch", report["draft_gate"]["blockers"])

    def test_formal_outcome_or_implementation_authorization_blocks_draft(self):
        closeout = load_current_closeout()
        closeout["closeout_gate"]["formal_human_outcome_recorded"] = True
        closeout["summary"]["next_design_authorized"] = True
        closeout["closeout_matrix"][0]["candidate_route_authorized"] = True
        closeout["implementation_gate"]["implementation_allowed"] = True

        report = build_with_temp_closeout(closeout)

        self.assertEqual(report["draft_gate"]["status"], "blocked")
        self.assertIn("closeout_records_formal_outcome", report["draft_gate"]["blockers"])
        self.assertIn("closeout_summary_next_design_not_blocked", report["draft_gate"]["blockers"])
        self.assertIn(
            "closeout_row_candidate_route_authorized:final_evidence_selection_policy_review",
            report["draft_gate"]["blockers"],
        )
        self.assertIn("closeout_implementation_gate_not_blocked", report["draft_gate"]["blockers"])
        self.assertFalse(report["draft_gate"]["implementation_allowed"])
        self.assertFalse(report["draft_gate"]["next_design_authorized"])

    def test_count_and_order_drift_blocks_draft(self):
        closeout = load_current_closeout()
        closeout["summary"]["design_action_count"] = 17
        closeout["closeout_matrix"] = list(reversed(closeout["closeout_matrix"]))

        report = build_with_temp_closeout(closeout)

        self.assertEqual(report["draft_gate"]["status"], "blocked")
        self.assertIn("closeout_action_count_drift", report["draft_gate"]["blockers"])
        self.assertIn("closeout_matrix_order_drift", report["draft_gate"]["blockers"])

    def test_forbidden_and_advisory_source_keys_block_without_tasks(self):
        closeout = load_current_closeout()
        closeout["closeout_matrix"][0]["implementation_plan"] = {"step": "should_not_exist"}
        closeout["closeout_matrix"][0]["ai_suggestion"] = True

        report = build_with_temp_closeout(closeout)

        self.assertEqual(report["draft_gate"]["status"], "blocked")
        self.assertIn("closeout_forbidden_key_present:implementation_plan", report["draft_gate"]["blockers"])
        self.assertIn("closeout_advisory_signal_present:ai_suggestion", report["draft_gate"]["blockers"])
        self.assertEqual(report["excluded_scope"]["pending_records_policy"], "background_count_only_not_work_items")
        for node in walk_dicts(report):
            self.assertFalse({"work_items", "engineering_tasks", "pending_tasks"} & set(node.keys()))

    def test_mojibake_like_text_blocks_human_readability_gate(self):
        closeout = load_current_closeout()
        closeout["closeout_matrix"][0]["minimum_human_basis"] = "\u9428 damaged text"

        report = build_with_temp_closeout(closeout)

        self.assertEqual(report["draft_gate"]["status"], "blocked")
        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("blocked_for_human_readability", report["draft_gate"]["blockers"])
        self.assertEqual(assertion_status(report, "text_readability_gate"), "failed")

    def test_markdown_is_confirmation_draft_only_and_readable(self):
        markdown = render_markdown(build_report())

        self.assertIn("待用户确认的人工收口草案", markdown)
        self.assertIn("## Draft Matrix", markdown)
        self.assertIn("最终证据选择策略评审", markdown)
        self.assertIn("`requires_user_confirmation=true`", markdown)
        self.assertIn("`formal_human_outcome_recorded=false`", markdown)
        self.assertIn("`draft_is_importable_decision=false`", markdown)
        self.assertIn("`implementation_allowed=false`", markdown)
        self.assertIn("不修改 hidden seed、anchor、rerank、prompt", markdown)
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
            Path("tools/build_ready_action_human_closeout_decision_draft.py"),
            Path("docs/ready_action_human_closeout_decision_draft_v0.4.7.9.5.md"),
            Path("tests/ready_action_human_closeout_decision_draft_report.json"),
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
