import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_ready_action_design_review_closeout import (
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_WORKSHEET_REPORT_PATH,
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


def load_current_worksheet() -> dict:
    return json.loads(Path("tests/ready_action_design_review_worksheet_report.json").read_text(encoding="utf-8-sig"))


def assertion_status(report: dict, name: str) -> str | None:
    for assertion in report.get("assertions", []):
        if assertion.get("name") == name:
            return assertion.get("status")
    return None


def build_with_temp_worksheet(worksheet: dict) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "worksheet.json"
        write_json(path, copy.deepcopy(worksheet))
        return build_report(path)


class ReadyActionDesignReviewCloseoutTest(unittest.TestCase):
    def test_default_paths_use_legacy_report_and_docs_markdown_output(self):
        self.assertEqual(
            DEFAULT_WORKSHEET_REPORT_PATH,
            legacy_report_path("ready_action_design_review_worksheet_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("ready_action_design_review_closeout_report.json"),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/ready_action_design_review_closeout_v0.4.7.9.4.md"),
        )

    def test_real_current_worksheet_builds_pending_closeout_envelope(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.7.9.4")
        self.assertEqual(report["schema_kind"], "ready_action_design_review_closeout_envelope")
        self.assertEqual(report["scope"], "offline human design review closeout envelope only")
        self.assertEqual(report["closeout_gate"]["status"], "pending_human_design_closeout")
        self.assertTrue(report["closeout_gate"]["human_closeout_allowed"])
        self.assertFalse(report["closeout_gate"]["formal_human_outcome_recorded"])
        self.assertFalse(report["closeout_gate"]["captures_formal_review_outcome"])
        self.assertFalse(report["closeout_gate"]["implementation_allowed"])
        self.assertFalse(report["closeout_gate"]["code_patch_authorized"])
        self.assertFalse(report["closeout_gate"]["next_design_authorized"])
        self.assertEqual(report["closeout_gate"]["handoff_to_implementation"], "not_allowed")
        self.assertEqual(report["closeout_gate"]["blockers"], [])

        summary = report["summary"]
        self.assertEqual(summary["closeout_track_count"], EXPECTED_TRACK_COUNT)
        self.assertEqual(summary["design_action_count"], EXPECTED_READY_ACTION_COUNT)
        self.assertEqual(summary["source_case_count"], EXPECTED_SOURCE_CASE_COUNT)
        self.assertEqual(summary["pending_records_excluded"], EXPECTED_PENDING_EXCLUDED)
        self.assertEqual(summary["priority_band_summary"], {"P0": 3, "P1": 2})
        self.assertFalse(summary["formal_human_outcome_recorded"])
        self.assertFalse(summary["captures_formal_review_outcome"])
        self.assertFalse(summary["implementation_allowed"])
        self.assertFalse(summary["code_patch_authorized"])
        self.assertFalse(summary["next_design_authorized"])

        matrix = report["closeout_matrix"]
        self.assertEqual(len(matrix), EXPECTED_TRACK_COUNT)
        self.assertEqual([row["action_type"] for row in matrix], EXPECTED_REVIEW_ORDER)
        self.assertEqual(
            sum(row["candidate_scope"]["ready_for_design_review_candidates"] for row in matrix),
            EXPECTED_READY_ACTION_COUNT,
        )
        for row in matrix:
            self.assertEqual(row["closeout_status"], "pending_human_closeout")
            self.assertTrue(row["human_closeout_required"])
            self.assertFalse(row["formal_human_outcome_recorded"])
            self.assertFalse(row["captures_formal_review_outcome"])
            self.assertFalse(row["implementation_allowed"])
            self.assertFalse(row["code_patch_authorized"])
            self.assertFalse(row["candidate_route_authorized"])
            self.assertTrue(row["candidate_route"])
            self.assertTrue(row["closeout_question"])
            self.assertTrue(row["minimum_human_basis"])
            self.assertTrue(row["candidate_closeout_options"])
            self.assertTrue(row["traceability"]["source_case_ids"])
            self.assertTrue(row["traceability"]["design_action_ids"])

        self.assertTrue(all(item["status"] == "passed" for item in report["assertions"]))
        for node in walk_dicts(report):
            self.assertFalse(FORBIDDEN_OUTPUT_KEYS & set(node.keys()))

    def test_blocked_source_worksheet_blocks_closeout(self):
        worksheet = load_current_worksheet()
        worksheet["worksheet_gate"]["status"] = "blocked"
        worksheet["worksheet_gate"]["blockers"] = ["not_ready"]

        report = build_with_temp_worksheet(worksheet)

        self.assertEqual(report["closeout_gate"]["status"], "blocked")
        self.assertFalse(report["closeout_gate"]["human_closeout_allowed"])
        self.assertIn("worksheet_gate_not_ready", report["closeout_gate"]["blockers"])
        self.assertIn("worksheet_gate_has_blockers", report["closeout_gate"]["blockers"])
        self.assertFalse(report["implementation_gate"]["implementation_allowed"])
        self.assertFalse(report["implementation_gate"]["code_patch_authorized"])

    def test_wrong_worksheet_schema_or_version_blocks_closeout(self):
        worksheet = load_current_worksheet()
        worksheet["version"] = "0.4.7.9.2"
        worksheet["schema_kind"] = "wrong_schema"

        report = build_with_temp_worksheet(worksheet)

        self.assertEqual(report["closeout_gate"]["status"], "blocked")
        self.assertIn("worksheet_version_mismatch", report["closeout_gate"]["blockers"])
        self.assertIn("worksheet_schema_mismatch", report["closeout_gate"]["blockers"])

    def test_implementation_authorization_in_source_blocks_closeout(self):
        worksheet = load_current_worksheet()
        worksheet["worksheet_gate"]["implementation_allowed"] = True
        worksheet["summary"]["code_patch_authorized"] = True
        worksheet["implementation_gate"]["implementation_allowed"] = True

        report = build_with_temp_worksheet(worksheet)

        self.assertEqual(report["closeout_gate"]["status"], "blocked")
        self.assertIn("worksheet_gate_implementation_not_blocked", report["closeout_gate"]["blockers"])
        self.assertIn("worksheet_summary_code_patch_not_blocked", report["closeout_gate"]["blockers"])
        self.assertIn("worksheet_implementation_gate_not_blocked", report["closeout_gate"]["blockers"])
        self.assertFalse(report["closeout_gate"]["implementation_allowed"])
        self.assertFalse(report["closeout_gate"]["code_patch_authorized"])

    def test_count_and_order_drift_blocks_closeout(self):
        worksheet = load_current_worksheet()
        worksheet["summary"]["design_action_count"] = 17
        worksheet["decision_matrix"] = list(reversed(worksheet["decision_matrix"]))

        report = build_with_temp_worksheet(worksheet)

        self.assertEqual(report["closeout_gate"]["status"], "blocked")
        self.assertIn("worksheet_action_count_drift", report["closeout_gate"]["blockers"])
        self.assertIn("worksheet_matrix_order_drift", report["closeout_gate"]["blockers"])

    def test_forbidden_and_advisory_source_keys_block_without_tasks(self):
        worksheet = load_current_worksheet()
        worksheet["decision_matrix"][0]["implementation_plan"] = {"step": "should_not_exist"}
        worksheet["decision_matrix"][0]["ai_suggestion"] = True

        report = build_with_temp_worksheet(worksheet)

        self.assertEqual(report["closeout_gate"]["status"], "blocked")
        self.assertIn("worksheet_forbidden_key_present:implementation_plan", report["closeout_gate"]["blockers"])
        self.assertIn("worksheet_advisory_signal_present:ai_suggestion", report["closeout_gate"]["blockers"])
        self.assertEqual(report["excluded_scope"]["pending_records_policy"], "background_count_only_not_work_items")
        for node in walk_dicts(report):
            self.assertFalse({"work_items", "engineering_tasks", "pending_tasks"} & set(node.keys()))

    def test_mojibake_like_text_blocks_human_readability_gate(self):
        worksheet = load_current_worksheet()
        worksheet["decision_matrix"][0]["critical_human_question"] = "\u9428 damaged text"

        report = build_with_temp_worksheet(worksheet)

        self.assertEqual(report["closeout_gate"]["status"], "blocked")
        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("blocked_for_human_readability", report["closeout_gate"]["blockers"])
        self.assertEqual(assertion_status(report, "text_readability_gate"), "failed")

    def test_markdown_is_closeout_only_and_readable(self):
        markdown = render_markdown(build_report())

        self.assertIn("人工设计评审的收口外壳", markdown)
        self.assertIn("## Closeout Matrix", markdown)
        self.assertIn("最终证据选择策略评审", markdown)
        self.assertIn("`formal_human_outcome_recorded=false`", markdown)
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
            Path("tools/build_ready_action_design_review_closeout.py"),
            Path("docs/ready_action_design_review_closeout_v0.4.7.9.4.md"),
            Path("tests/ready_action_design_review_closeout_report.json"),
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
