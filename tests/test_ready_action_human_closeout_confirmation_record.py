import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_ready_action_human_closeout_confirmation_record import (
    DEFAULT_DRAFT_REPORT_PATH,
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


def load_current_draft() -> dict:
    return json.loads(Path("tests/ready_action_human_closeout_decision_draft_report.json").read_text(encoding="utf-8-sig"))


def assertion_status(report: dict, name: str) -> str | None:
    for assertion in report.get("assertions", []):
        if assertion.get("name") == name:
            return assertion.get("status")
    return None


def build_with_temp_draft(draft: dict) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "draft.json"
        write_json(path, copy.deepcopy(draft))
        return build_report(path)


class ReadyActionHumanCloseoutConfirmationRecordTest(unittest.TestCase):
    def test_default_paths_use_legacy_report_and_docs_markdown_output(self):
        self.assertEqual(
            DEFAULT_DRAFT_REPORT_PATH,
            legacy_report_path("ready_action_human_closeout_decision_draft_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("ready_action_human_closeout_confirmation_record_report.json"),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/ready_action_human_closeout_confirmation_record_v0.4.7.9.6.md"),
        )

    def test_real_current_draft_builds_confirmation_record(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.7.9.6")
        self.assertEqual(report["schema_kind"], "ready_action_human_closeout_confirmation_record")
        self.assertEqual(report["confirmation_gate"]["status"], "confirmed_for_future_design_planning")
        self.assertTrue(report["confirmation_gate"]["user_confirmation_recorded"])
        self.assertTrue(report["confirmation_gate"]["formal_design_closeout_recorded"])
        self.assertTrue(report["confirmation_gate"]["future_design_planning_allowed"])
        self.assertFalse(report["confirmation_gate"]["manual_review_importable"])
        self.assertTrue(report["confirmation_gate"]["not_completed_manual_review_decision"])
        self.assertFalse(report["confirmation_gate"]["implementation_allowed"])
        self.assertFalse(report["confirmation_gate"]["code_patch_authorized"])
        self.assertFalse(report["confirmation_gate"]["next_design_authorized"])
        self.assertEqual(report["confirmation_gate"]["handoff_to_implementation"], "not_allowed")
        self.assertEqual(report["confirmation_gate"]["blockers"], [])

        summary = report["summary"]
        self.assertEqual(summary["confirmation_track_count"], EXPECTED_TRACK_COUNT)
        self.assertEqual(summary["design_action_count"], EXPECTED_READY_ACTION_COUNT)
        self.assertEqual(summary["source_case_count"], EXPECTED_SOURCE_CASE_COUNT)
        self.assertEqual(summary["pending_records_excluded"], EXPECTED_PENDING_EXCLUDED)
        self.assertEqual(summary["priority_band_summary"], {"P0": 3, "P1": 2})
        self.assertTrue(summary["user_confirmation_recorded"])
        self.assertTrue(summary["formal_design_closeout_recorded"])
        self.assertTrue(summary["future_design_planning_allowed"])
        self.assertFalse(summary["manual_review_importable"])
        self.assertTrue(summary["not_completed_manual_review_decision"])
        self.assertFalse(summary["implementation_allowed"])
        self.assertFalse(summary["code_patch_authorized"])
        self.assertFalse(summary["next_design_authorized"])

        matrix = report["confirmation_matrix"]
        self.assertEqual(len(matrix), EXPECTED_TRACK_COUNT)
        self.assertEqual([row["action_type"] for row in matrix], EXPECTED_REVIEW_ORDER)
        self.assertEqual(
            sum(row["candidate_scope"]["ready_for_design_review_candidates"] for row in matrix),
            EXPECTED_READY_ACTION_COUNT,
        )
        for row in matrix:
            self.assertEqual(row["confirmation_status"], "confirmed_for_future_design_planning")
            self.assertTrue(row["user_confirmation_recorded"])
            self.assertTrue(row["future_design_planning_allowed"])
            self.assertFalse(row["manual_review_importable"])
            self.assertTrue(row["not_completed_manual_review_decision"])
            self.assertFalse(row["implementation_allowed"])
            self.assertFalse(row["code_patch_authorized"])
            self.assertFalse(row["next_design_authorized"])
            self.assertTrue(row["confirmed_closeout_option"])
            self.assertTrue(row["confirmed_direction"])
            self.assertTrue(row["confirmed_next_series"])
            self.assertTrue(row["confirmation_basis"])
            self.assertTrue(row["traceability"]["source_case_ids"])
            self.assertTrue(row["traceability"]["design_action_ids"])

        self.assertTrue(all(item["status"] == "passed" for item in report["assertions"]))
        for node in walk_dicts(report):
            self.assertFalse(FORBIDDEN_OUTPUT_KEYS & set(node.keys()))

    def test_blocked_source_draft_blocks_confirmation(self):
        draft = load_current_draft()
        draft["draft_gate"]["status"] = "blocked"
        draft["draft_gate"]["blockers"] = ["not_ready"]

        report = build_with_temp_draft(draft)

        self.assertEqual(report["confirmation_gate"]["status"], "blocked")
        self.assertFalse(report["confirmation_gate"]["user_confirmation_recorded"])
        self.assertFalse(report["confirmation_gate"]["formal_design_closeout_recorded"])
        self.assertFalse(report["confirmation_gate"]["future_design_planning_allowed"])
        self.assertIn("draft_gate_not_pending_confirmation", report["confirmation_gate"]["blockers"])
        self.assertIn("draft_gate_has_blockers", report["confirmation_gate"]["blockers"])

    def test_wrong_draft_schema_or_version_blocks_confirmation(self):
        draft = load_current_draft()
        draft["version"] = "0.4.7.9.4"
        draft["schema_kind"] = "wrong_schema"

        report = build_with_temp_draft(draft)

        self.assertEqual(report["confirmation_gate"]["status"], "blocked")
        self.assertIn("draft_version_mismatch", report["confirmation_gate"]["blockers"])
        self.assertIn("draft_schema_mismatch", report["confirmation_gate"]["blockers"])

    def test_source_formal_outcome_or_implementation_authorization_blocks_confirmation(self):
        draft = load_current_draft()
        draft["draft_gate"]["formal_human_outcome_recorded"] = True
        draft["summary"]["next_design_authorized"] = True
        draft["draft_matrix"][0]["draft_is_importable_decision"] = True
        draft["implementation_gate"]["implementation_allowed"] = True

        report = build_with_temp_draft(draft)

        self.assertEqual(report["confirmation_gate"]["status"], "blocked")
        self.assertIn("draft_records_formal_outcome", report["confirmation_gate"]["blockers"])
        self.assertIn("draft_summary_next_design_not_blocked", report["confirmation_gate"]["blockers"])
        self.assertIn(
            "draft_row_importable_decision_not_blocked:final_evidence_selection_policy_review",
            report["confirmation_gate"]["blockers"],
        )
        self.assertIn("draft_implementation_gate_not_blocked", report["confirmation_gate"]["blockers"])

    def test_count_and_order_drift_blocks_confirmation(self):
        draft = load_current_draft()
        draft["summary"]["design_action_count"] = 17
        draft["draft_matrix"] = list(reversed(draft["draft_matrix"]))

        report = build_with_temp_draft(draft)

        self.assertEqual(report["confirmation_gate"]["status"], "blocked")
        self.assertIn("draft_action_count_drift", report["confirmation_gate"]["blockers"])
        self.assertIn("draft_matrix_order_drift", report["confirmation_gate"]["blockers"])

    def test_forbidden_and_advisory_source_keys_block_without_tasks(self):
        draft = load_current_draft()
        draft["draft_matrix"][0]["implementation_plan"] = {"step": "should_not_exist"}
        draft["draft_matrix"][0]["ai_suggestion"] = True

        report = build_with_temp_draft(draft)

        self.assertEqual(report["confirmation_gate"]["status"], "blocked")
        self.assertIn("draft_forbidden_key_present:implementation_plan", report["confirmation_gate"]["blockers"])
        self.assertIn("draft_advisory_signal_present:ai_suggestion", report["confirmation_gate"]["blockers"])
        self.assertEqual(report["excluded_scope"]["pending_records_policy"], "background_count_only_not_work_items")
        for node in walk_dicts(report):
            self.assertFalse({"work_items", "engineering_tasks", "pending_tasks"} & set(node.keys()))

    def test_mojibake_like_text_blocks_human_readability_gate(self):
        draft = load_current_draft()
        draft["draft_matrix"][0]["draft_rationale"] = "\u9428 damaged text"

        report = build_with_temp_draft(draft)

        self.assertEqual(report["confirmation_gate"]["status"], "blocked")
        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("blocked_for_human_readability", report["confirmation_gate"]["blockers"])
        self.assertEqual(assertion_status(report, "text_readability_gate"), "failed")

    def test_markdown_is_confirmation_record_not_implementation_authorization(self):
        markdown = render_markdown(build_report())

        self.assertIn("用户已确认 5 条设计收口方向", markdown)
        self.assertIn("## Confirmation Matrix", markdown)
        self.assertIn("最终证据选择策略评审", markdown)
        self.assertIn("`manual_review_importable=false`", markdown)
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
            Path("tools/build_ready_action_human_closeout_confirmation_record.py"),
            Path("docs/ready_action_human_closeout_confirmation_record_v0.4.7.9.6.md"),
            Path("tests/ready_action_human_closeout_confirmation_record_report.json"),
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
