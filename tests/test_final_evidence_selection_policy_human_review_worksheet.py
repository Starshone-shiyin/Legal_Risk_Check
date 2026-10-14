import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_final_evidence_selection_policy_human_review_worksheet import (
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_TABLE_DRAFT_REPORT_PATH,
    EXPECTED_CASE_COUNT,
    EXPECTED_POLICY_CATEGORIES,
    EXPECTED_TABLE_ROW_COUNT,
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


def load_current_table_draft() -> dict:
    return json.loads(Path("tests/final_evidence_selection_policy_table_draft_report.json").read_text(encoding="utf-8-sig"))


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


def build_with_table_draft(table_draft: dict) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "table_draft.json"
        write_json(path, copy.deepcopy(table_draft))
        return build_report(path)


class FinalEvidenceSelectionPolicyHumanReviewWorksheetTest(unittest.TestCase):
    def test_default_paths_use_legacy_report_and_docs_markdown_output(self):
        self.assertEqual(
            DEFAULT_TABLE_DRAFT_REPORT_PATH,
            legacy_report_path("final_evidence_selection_policy_table_draft_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("final_evidence_selection_policy_human_review_worksheet_report.json"),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/final_evidence_selection_policy_human_review_worksheet_v0.4.8.3.md"),
        )

    def test_real_current_report_builds_review_only_worksheet(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.8.3")
        self.assertEqual(report["schema_kind"], "final_evidence_selection_policy_human_review_worksheet")
        self.assertEqual(report["scope"], "offline final evidence selection policy human review worksheet only")
        self.assertEqual(report["worksheet_gate"]["status"], "ready_for_policy_table_human_review_worksheet")
        self.assertEqual(report["worksheet_gate"]["allowed_use"], "human_policy_review_discussion_only")
        self.assertTrue(report["worksheet_gate"]["saved_report_only"])
        self.assertTrue(report["worksheet_gate"]["human_review_worksheet_allowed"])
        self.assertFalse(report["worksheet_gate"]["implementation_allowed"])
        self.assertFalse(report["worksheet_gate"]["code_patch_authorized"])
        self.assertFalse(report["worksheet_gate"]["runtime_policy_implementation_allowed"])
        self.assertFalse(report["worksheet_gate"]["runtime_selection_policy_patch_allowed"])
        self.assertFalse(report["worksheet_gate"]["rerank_change_allowed"])
        self.assertFalse(report["worksheet_gate"]["captures_formal_review_outcome"])
        self.assertEqual(report["worksheet_gate"]["rag_query_integration"], "disallowed")
        self.assertEqual(report["worksheet_gate"]["blockers"], [])

        summary = report["summary"]
        self.assertEqual(summary["policy_review_row_count"], EXPECTED_TABLE_ROW_COUNT)
        self.assertEqual(summary["source_policy_table_row_count"], EXPECTED_TABLE_ROW_COUNT)
        self.assertEqual(summary["unique_case_count"], EXPECTED_CASE_COUNT)
        self.assertEqual(summary["priority_summary"], {"P0": 5, "P1": 3})
        self.assertEqual(summary["next_version_recommendation"], "v0.4.8.4 policy table human review closeout")
        self.assertFalse(summary["implementation_allowed"])
        self.assertFalse(summary["code_patch_authorized"])
        self.assertFalse(summary["captures_formal_review_outcome"])
        self.assertEqual(summary["rag_query_integration"], "disallowed")

        rows = report["review_worksheet_rows"]
        self.assertEqual(len(rows), EXPECTED_TABLE_ROW_COUNT)
        self.assertEqual([row["policy_category"] for row in rows], EXPECTED_POLICY_CATEGORIES)
        self.assertEqual(sum(row["case_count"] for row in rows), 26)
        for row in rows:
            self.assertEqual(row["worksheet_status"], "ready_for_human_review")
            self.assertTrue(row["human_review_required"])
            self.assertFalse(row["captures_formal_review_outcome"])
            self.assertFalse(row["implementation_allowed"])
            self.assertFalse(row["code_patch_authorized"])
            self.assertEqual(row["runtime_adoption_status"], "not_allowed")
            self.assertTrue(row["review_goal"])
            self.assertTrue(row["review_questions"])
            self.assertTrue(row["acceptance_checks"])
            self.assertTrue(row["applicable_case_ids"])
            self.assertTrue(row["prohibited_now"])
            self.assertTrue(row["traceability"]["source_case_ids"])

        packet = report["human_review_packet"]
        self.assertFalse(packet["formal_review_outcome_captured"])
        self.assertFalse(packet["importer_compatible"])
        self.assertEqual(len(packet["recommended_review_order"]), EXPECTED_TABLE_ROW_COUNT)

        self.assertEqual(report["next_version_handoff"]["recommended_next_version"], "v0.4.8.4")
        self.assertFalse(report["next_version_handoff"]["runtime_implementation_allowed"])
        self.assertTrue(all(item["status"] == "passed" for item in report["assertions"]))
        for node in walk_dicts(report):
            self.assertFalse(FORBIDDEN_OUTPUT_KEYS & set(node.keys()))

    def test_blocked_or_wrong_source_table_draft_blocks_worksheet(self):
        table_draft = load_current_table_draft()
        table_draft["version"] = "0.4.8.1"
        table_draft["schema_kind"] = "wrong_schema"
        table_draft["policy_table_gate"]["status"] = "blocked"
        table_draft["policy_table_gate"]["blockers"] = ["source_problem"]

        report = build_with_table_draft(table_draft)

        self.assertEqual(report["worksheet_gate"]["status"], "blocked")
        self.assertFalse(report["worksheet_gate"]["human_review_worksheet_allowed"])
        self.assertIn("table_draft_version_mismatch", report["worksheet_gate"]["blockers"])
        self.assertIn("table_draft_schema_mismatch", report["worksheet_gate"]["blockers"])
        self.assertIn("table_draft_gate_not_ready", report["worksheet_gate"]["blockers"])
        self.assertIn("table_draft_has_blockers", report["worksheet_gate"]["blockers"])
        self.assertEqual(assertion_status(report, "source_table_draft_is_ready_for_human_review_worksheet"), "failed")

    def test_implementation_authorization_in_source_blocks_worksheet(self):
        table_draft = load_current_table_draft()
        table_draft["policy_table_gate"]["implementation_allowed"] = True
        table_draft["policy_table_gate"]["code_patch_authorized"] = True
        table_draft["policy_table_gate"]["runtime_policy_implementation_allowed"] = True
        table_draft["policy_table_rows"][0]["implementation_allowed"] = True

        report = build_with_table_draft(table_draft)

        self.assertEqual(report["worksheet_gate"]["status"], "blocked")
        self.assertIn("table_draft_implementation_not_blocked", report["worksheet_gate"]["blockers"])
        self.assertIn("table_draft_code_patch_not_blocked", report["worksheet_gate"]["blockers"])
        self.assertIn("table_draft_runtime_policy_not_blocked", report["worksheet_gate"]["blockers"])
        self.assertIn("policy_row_implementation_not_blocked", report["worksheet_gate"]["blockers"])
        self.assertFalse(report["worksheet_gate"]["implementation_allowed"])
        self.assertFalse(report["implementation_gate"]["code_patch_authorized"])

    def test_policy_row_count_or_order_drift_blocks_worksheet(self):
        table_draft = load_current_table_draft()
        table_draft["policy_table_rows"] = list(reversed(table_draft["policy_table_rows"][:-1]))
        table_draft["summary"]["policy_table_row_count"] = 7
        table_draft["summary"]["confirmed_case_count"] = 4

        report = build_with_table_draft(table_draft)

        self.assertEqual(report["worksheet_gate"]["status"], "blocked")
        self.assertIn("policy_table_row_count_drift", report["worksheet_gate"]["blockers"])
        self.assertIn("policy_category_order_drift", report["worksheet_gate"]["blockers"])
        self.assertIn("confirmed_case_count_drift", report["worksheet_gate"]["blockers"])
        self.assertEqual(assertion_status(report, "worksheet_has_eight_review_rows"), "failed")

    def test_forbidden_or_advisory_source_keys_block_worksheet(self):
        table_draft = load_current_table_draft()
        table_draft["policy_table_rows"][0]["implementation_plan"] = {"step": "should_not_exist"}
        table_draft["policy_table_rows"][0]["ai_suggestion"] = True

        report = build_with_table_draft(table_draft)

        self.assertEqual(report["worksheet_gate"]["status"], "blocked")
        self.assertIn("table_draft_forbidden_key_present:implementation_plan", report["worksheet_gate"]["blockers"])
        self.assertIn("table_draft_advisory_signal_present:ai_suggestion", report["worksheet_gate"]["blockers"])
        for node in walk_dicts(report):
            self.assertFalse({"work_items", "engineering_tasks", "pending_tasks"} & set(node.keys()))

    def test_mojibake_like_text_blocks_human_readability_gate(self):
        table_draft = load_current_table_draft()
        table_draft["policy_table_rows"][0]["review_reasons"][0] = "\u9428 damaged text"

        report = build_with_table_draft(table_draft)

        self.assertEqual(report["worksheet_gate"]["status"], "blocked")
        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("blocked_for_human_readability", report["worksheet_gate"]["blockers"])
        self.assertEqual(assertion_status(report, "text_readability_gate"), "failed")

    def test_markdown_is_review_only_and_readable(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.8.3 Final Evidence Selection Policy Human Review Worksheet", markdown)
        self.assertIn("本文件是最终证据选择 policy table 的人工复核 worksheet", markdown)
        self.assertIn("## Review Worksheet Rows", markdown)
        self.assertIn("## Review Questions", markdown)
        self.assertIn("## Acceptance Checks", markdown)
        self.assertIn("`implementation_allowed=false`", markdown)
        self.assertIn("不实现 runtime policy", markdown)
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
            Path("tools/build_final_evidence_selection_policy_human_review_worksheet.py"),
            Path("docs/final_evidence_selection_policy_human_review_worksheet_v0.4.8.3.md"),
            Path("tests/final_evidence_selection_policy_human_review_worksheet_report.json"),
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
