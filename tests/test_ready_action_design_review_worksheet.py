import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_ready_action_design_review_worksheet import (
    DEFAULT_BRIEF_REPORT_PATH,
    DEFAULT_GATE_REPORT_PATH,
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


def load_current_gate() -> dict:
    return json.loads(Path("tests/ready_action_design_review_gate_report.json").read_text(encoding="utf-8-sig"))


def load_current_brief() -> dict:
    return json.loads(Path("tests/ready_action_design_review_brief_report.json").read_text(encoding="utf-8-sig"))


def assertion_status(report: dict, name: str) -> str | None:
    for assertion in report.get("assertions", []):
        if assertion.get("name") == name:
            return assertion.get("status")
    return None


def build_with_temp_reports(gate: dict, brief: dict, *, update_gate_input_path: bool = True) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        gate_path = root / "gate.json"
        brief_path = root / "brief.json"
        gate_payload = copy.deepcopy(gate)
        brief_payload = copy.deepcopy(brief)
        if update_gate_input_path:
            gate_payload.setdefault("inputs", {}).setdefault("ready_action_design_review_brief_report", {})[
                "path"
            ] = str(brief_path)
        write_json(gate_path, gate_payload)
        write_json(brief_path, brief_payload)
        return build_report(gate_path, brief_path)


class ReadyActionDesignReviewWorksheetTest(unittest.TestCase):
    def test_default_paths_use_legacy_report_and_docs_markdown_output(self):
        self.assertEqual(
            DEFAULT_GATE_REPORT_PATH,
            legacy_report_path("ready_action_design_review_gate_report.json"),
        )
        self.assertEqual(
            DEFAULT_BRIEF_REPORT_PATH,
            legacy_report_path("ready_action_design_review_brief_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("ready_action_design_review_worksheet_report.json"),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/ready_action_design_review_worksheet_v0.4.7.9.3.md"),
        )

    def test_real_current_reports_build_review_only_decision_matrix(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.7.9.3")
        self.assertEqual(report["schema_kind"], "ready_action_design_review_worksheet_decision_matrix")
        self.assertEqual(report["scope"], "offline human design review worksheet only")
        self.assertEqual(report["worksheet_gate"]["status"], "ready_for_human_design_review_matrix")
        self.assertTrue(report["worksheet_gate"]["human_design_review_allowed"])
        self.assertEqual(report["worksheet_gate"]["allowed_use"], "human_design_review_discussion_only")
        self.assertFalse(report["worksheet_gate"]["implementation_allowed"])
        self.assertFalse(report["worksheet_gate"]["code_patch_authorized"])
        self.assertEqual(report["worksheet_gate"]["handoff_to_implementation"], "not_allowed")
        self.assertFalse(report["worksheet_gate"]["captures_formal_review_outcome"])
        self.assertEqual(report["worksheet_gate"]["blockers"], [])

        summary = report["summary"]
        self.assertEqual(summary["review_track_count"], EXPECTED_TRACK_COUNT)
        self.assertEqual(summary["design_action_count"], EXPECTED_READY_ACTION_COUNT)
        self.assertEqual(summary["source_case_count"], EXPECTED_SOURCE_CASE_COUNT)
        self.assertEqual(summary["pending_records_excluded"], EXPECTED_PENDING_EXCLUDED)
        self.assertEqual(summary["priority_band_summary"], {"P0": 3, "P1": 2})
        self.assertFalse(summary["implementation_allowed"])
        self.assertFalse(summary["code_patch_authorized"])
        self.assertFalse(summary["captures_formal_review_outcome"])

        matrix = report["decision_matrix"]
        self.assertEqual(len(matrix), EXPECTED_TRACK_COUNT)
        self.assertEqual([row["action_type"] for row in matrix], EXPECTED_REVIEW_ORDER)
        self.assertEqual(
            sum(row["candidate_scope"]["ready_for_design_review_candidates"] for row in matrix),
            EXPECTED_READY_ACTION_COUNT,
        )
        for row in matrix:
            self.assertEqual(row["worksheet_status"], "ready_for_human_design_review")
            self.assertTrue(row["human_review_required"])
            self.assertFalse(row["implementation_allowed"])
            self.assertFalse(row["code_patch_authorized"])
            self.assertTrue(row["critical_human_question"])
            self.assertTrue(row["review_goal"])
            self.assertTrue(row["review_prompts"])
            self.assertTrue(row["design_checkpoints"])
            self.assertTrue(row["prohibited_now"])
            self.assertTrue(row["traceability"]["source_case_ids"])
            self.assertTrue(row["traceability"]["design_action_ids"])

        self.assertTrue(all(item["status"] == "passed" for item in report["assertions"]))
        for node in walk_dicts(report):
            self.assertFalse(FORBIDDEN_OUTPUT_KEYS & set(node.keys()))

    def test_blocked_source_gate_blocks_worksheet(self):
        gate = load_current_gate()
        brief = load_current_brief()
        gate["gate"]["status"] = "blocked"
        gate["gate"]["blockers"] = ["manual_boundary_not_ready"]

        report = build_with_temp_reports(gate, brief)

        self.assertEqual(report["worksheet_gate"]["status"], "blocked")
        self.assertFalse(report["worksheet_gate"]["human_design_review_allowed"])
        self.assertIn("gate_not_open_for_human_design_review", report["worksheet_gate"]["blockers"])
        self.assertIn("gate_has_blockers", report["worksheet_gate"]["blockers"])
        self.assertFalse(report["implementation_gate"]["implementation_allowed"])
        self.assertFalse(report["implementation_gate"]["code_patch_authorized"])

    def test_wrong_brief_contract_blocks_worksheet(self):
        gate = load_current_gate()
        brief = load_current_brief()
        brief["version"] = "0.4.7.9.0"
        brief["schema_kind"] = "wrong_schema"

        report = build_with_temp_reports(gate, brief)

        self.assertEqual(report["worksheet_gate"]["status"], "blocked")
        self.assertIn("brief_version_mismatch", report["worksheet_gate"]["blockers"])
        self.assertIn("brief_schema_mismatch", report["worksheet_gate"]["blockers"])
        self.assertFalse(report["worksheet_gate"]["implementation_allowed"])

    def test_implementation_authorization_in_source_blocks_worksheet(self):
        gate = load_current_gate()
        brief = load_current_brief()
        gate["gate"]["implementation_allowed"] = True
        brief["summary"]["code_patch_authorized"] = True

        report = build_with_temp_reports(gate, brief)

        self.assertEqual(report["worksheet_gate"]["status"], "blocked")
        self.assertIn("gate_implementation_not_blocked", report["worksheet_gate"]["blockers"])
        self.assertIn("brief_summary_code_patch_not_blocked", report["worksheet_gate"]["blockers"])
        self.assertFalse(report["worksheet_gate"]["implementation_allowed"])
        self.assertFalse(report["worksheet_gate"]["code_patch_authorized"])

    def test_count_and_order_drift_blocks_worksheet(self):
        gate = load_current_gate()
        brief = load_current_brief()
        gate["review_scope"]["design_action_count"] = 17
        brief["summary"]["ready_for_design_review_candidates"] = 17
        brief["summary"]["review_order"] = list(reversed(EXPECTED_REVIEW_ORDER))

        report = build_with_temp_reports(gate, brief)

        self.assertEqual(report["worksheet_gate"]["status"], "blocked")
        self.assertIn("gate_action_count_drift", report["worksheet_gate"]["blockers"])
        self.assertIn("brief_ready_action_count_drift", report["worksheet_gate"]["blockers"])
        self.assertIn("brief_review_order_drift", report["worksheet_gate"]["blockers"])

    def test_gate_brief_input_path_mismatch_blocks_worksheet(self):
        report = build_with_temp_reports(load_current_gate(), load_current_brief(), update_gate_input_path=False)

        self.assertEqual(report["worksheet_gate"]["status"], "blocked")
        self.assertIn("gate_brief_input_path_mismatch", report["worksheet_gate"]["blockers"])

    def test_forbidden_and_advisory_source_keys_block_without_creating_tasks(self):
        gate = load_current_gate()
        brief = load_current_brief()
        brief["track_briefs"][0]["implementation_plan"] = {"step": "should_not_exist"}
        brief["track_briefs"][0]["ai_suggestion"] = True

        report = build_with_temp_reports(gate, brief)

        self.assertEqual(report["worksheet_gate"]["status"], "blocked")
        self.assertIn("brief_forbidden_key_present:implementation_plan", report["worksheet_gate"]["blockers"])
        self.assertIn("brief_advisory_signal_present:ai_suggestion", report["worksheet_gate"]["blockers"])
        self.assertEqual(report["excluded_scope"]["pending_records_policy"], "background_count_only_not_work_items")
        for node in walk_dicts(report):
            self.assertFalse({"work_items", "engineering_tasks", "pending_tasks"} & set(node.keys()))

    def test_mojibake_like_text_blocks_human_readability_gate(self):
        gate = load_current_gate()
        brief = load_current_brief()
        brief["track_briefs"][0]["review_questions"][0] = "\u9428 damaged text"

        report = build_with_temp_reports(gate, brief)

        self.assertEqual(report["worksheet_gate"]["status"], "blocked")
        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("blocked_for_human_readability", report["worksheet_gate"]["blockers"])
        self.assertEqual(assertion_status(report, "text_readability_gate"), "failed")

    def test_markdown_is_review_only_and_readable(self):
        markdown = render_markdown(build_report())

        self.assertIn("本文件是人工设计评审用的 worksheet", markdown)
        self.assertIn("## Review Matrix", markdown)
        self.assertIn("最终证据选择策略评审", markdown)
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
            Path("tools/build_ready_action_design_review_worksheet.py"),
            Path("docs/ready_action_design_review_worksheet_v0.4.7.9.3.md"),
            Path("tests/ready_action_design_review_worksheet_report.json"),
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
