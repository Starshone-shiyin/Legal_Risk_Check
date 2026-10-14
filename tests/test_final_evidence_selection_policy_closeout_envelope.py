import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_final_evidence_selection_policy_closeout_envelope import (
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_WORKSHEET_REPORT_PATH,
    EXPECTED_CASE_COUNT,
    EXPECTED_POLICY_CATEGORIES,
    EXPECTED_REVIEW_ROW_COUNT,
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
        Path("tests/final_evidence_selection_policy_human_review_worksheet_report.json").read_text(
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


def build_with_worksheet(worksheet: dict) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "worksheet.json"
        write_json(path, copy.deepcopy(worksheet))
        return build_report(path)


class FinalEvidenceSelectionPolicyCloseoutEnvelopeTest(unittest.TestCase):
    def test_default_paths_use_legacy_report_and_docs_markdown_output(self):
        self.assertEqual(
            DEFAULT_WORKSHEET_REPORT_PATH,
            legacy_report_path("final_evidence_selection_policy_human_review_worksheet_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("final_evidence_selection_policy_closeout_envelope_report.json"),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/final_evidence_selection_policy_closeout_envelope_v0.4.8.4.md"),
        )

    def test_real_current_report_builds_pending_closeout_envelope(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.8.4")
        self.assertEqual(report["schema_kind"], "final_evidence_selection_policy_closeout_envelope")
        self.assertEqual(report["scope"], "offline final evidence selection policy closeout envelope only")
        self.assertEqual(report["closeout_gate"]["status"], "pending_policy_table_human_closeout")
        self.assertEqual(report["closeout_gate"]["allowed_use"], "human_closeout_discussion_only")
        self.assertTrue(report["closeout_gate"]["saved_report_only"])
        self.assertTrue(report["closeout_gate"]["closeout_envelope_allowed"])
        self.assertFalse(report["closeout_gate"]["implementation_allowed"])
        self.assertFalse(report["closeout_gate"]["code_patch_authorized"])
        self.assertFalse(report["closeout_gate"]["runtime_policy_implementation_allowed"])
        self.assertFalse(report["closeout_gate"]["runtime_selection_policy_patch_allowed"])
        self.assertFalse(report["closeout_gate"]["rerank_change_allowed"])
        self.assertFalse(report["closeout_gate"]["formal_human_outcome_recorded"])
        self.assertFalse(report["closeout_gate"]["captures_formal_review_outcome"])
        self.assertEqual(report["closeout_gate"]["rag_query_integration"], "disallowed")
        self.assertEqual(report["closeout_gate"]["blockers"], [])

        summary = report["summary"]
        self.assertEqual(summary["closeout_row_count"], EXPECTED_REVIEW_ROW_COUNT)
        self.assertEqual(summary["source_review_row_count"], EXPECTED_REVIEW_ROW_COUNT)
        self.assertEqual(summary["unique_case_count"], EXPECTED_CASE_COUNT)
        self.assertEqual(summary["priority_summary"], {"P0": 5, "P1": 3})
        self.assertEqual(summary["pending_human_closeout_count"], EXPECTED_REVIEW_ROW_COUNT)
        self.assertEqual(summary["next_version_recommendation"], "v0.4.8.5 policy table human closeout decision draft")
        self.assertFalse(summary["formal_human_outcome_recorded"])
        self.assertFalse(summary["implementation_allowed"])
        self.assertFalse(summary["code_patch_authorized"])
        self.assertEqual(summary["rag_query_integration"], "disallowed")

        rows = report["closeout_rows"]
        self.assertEqual(len(rows), EXPECTED_REVIEW_ROW_COUNT)
        self.assertEqual([row["policy_category"] for row in rows], EXPECTED_POLICY_CATEGORIES)
        for row in rows:
            self.assertEqual(row["closeout_status"], "pending_human_closeout")
            self.assertFalse(row["formal_human_outcome_recorded"])
            self.assertFalse(row["captures_formal_review_outcome"])
            self.assertFalse(row["candidate_route_authorized"])
            self.assertFalse(row["implementation_allowed"])
            self.assertFalse(row["code_patch_authorized"])
            self.assertEqual(row["runtime_adoption_status"], "not_allowed")
            self.assertTrue(row["closeout_question"])
            self.assertTrue(row["minimum_human_basis"])
            self.assertTrue(row["available_closeout_options"])
            self.assertTrue(row["source_review_questions"])
            self.assertTrue(row["source_acceptance_checks"])
            self.assertTrue(row["source_case_ids"])
            self.assertTrue(row["prohibited_now"])

        packet = report["closeout_packet"]
        self.assertFalse(packet["formal_review_outcome_captured"])
        self.assertFalse(packet["importer_compatible"])
        self.assertEqual(len(packet["recommended_closeout_order"]), EXPECTED_REVIEW_ROW_COUNT)
        self.assertEqual(len(packet["closeout_options"]), 5)

        self.assertEqual(report["next_version_handoff"]["recommended_next_version"], "v0.4.8.5")
        self.assertFalse(report["next_version_handoff"]["runtime_implementation_allowed"])
        self.assertTrue(all(item["status"] == "passed" for item in report["assertions"]))
        for node in walk_dicts(report):
            self.assertFalse(FORBIDDEN_OUTPUT_KEYS & set(node.keys()))

    def test_blocked_or_wrong_source_worksheet_blocks_closeout(self):
        worksheet = load_current_worksheet()
        worksheet["version"] = "0.4.8.2"
        worksheet["schema_kind"] = "wrong_schema"
        worksheet["worksheet_gate"]["status"] = "blocked"
        worksheet["worksheet_gate"]["blockers"] = ["source_problem"]

        report = build_with_worksheet(worksheet)

        self.assertEqual(report["closeout_gate"]["status"], "blocked")
        self.assertFalse(report["closeout_gate"]["closeout_envelope_allowed"])
        self.assertIn("worksheet_version_mismatch", report["closeout_gate"]["blockers"])
        self.assertIn("worksheet_schema_mismatch", report["closeout_gate"]["blockers"])
        self.assertIn("worksheet_gate_not_ready", report["closeout_gate"]["blockers"])
        self.assertIn("worksheet_has_blockers", report["closeout_gate"]["blockers"])
        self.assertEqual(assertion_status(report, "source_worksheet_is_ready_for_closeout_envelope"), "failed")

    def test_implementation_or_formal_outcome_in_source_blocks_closeout(self):
        worksheet = load_current_worksheet()
        worksheet["worksheet_gate"]["implementation_allowed"] = True
        worksheet["worksheet_gate"]["code_patch_authorized"] = True
        worksheet["worksheet_gate"]["captures_formal_review_outcome"] = True
        worksheet["review_worksheet_rows"][0]["implementation_allowed"] = True
        worksheet["review_worksheet_rows"][0]["captures_formal_review_outcome"] = True

        report = build_with_worksheet(worksheet)

        self.assertEqual(report["closeout_gate"]["status"], "blocked")
        self.assertIn("worksheet_implementation_not_blocked", report["closeout_gate"]["blockers"])
        self.assertIn("worksheet_code_patch_not_blocked", report["closeout_gate"]["blockers"])
        self.assertIn("worksheet_formal_outcome_not_blocked", report["closeout_gate"]["blockers"])
        self.assertIn("worksheet_row_implementation_not_blocked", report["closeout_gate"]["blockers"])
        self.assertIn("worksheet_row_formal_outcome_not_blocked", report["closeout_gate"]["blockers"])
        self.assertFalse(report["closeout_gate"]["implementation_allowed"])
        self.assertFalse(report["implementation_gate"]["code_patch_authorized"])

    def test_review_row_count_or_order_drift_blocks_closeout(self):
        worksheet = load_current_worksheet()
        worksheet["review_worksheet_rows"] = list(reversed(worksheet["review_worksheet_rows"][:-1]))
        worksheet["summary"]["policy_review_row_count"] = 7
        worksheet["summary"]["unique_case_count"] = 4

        report = build_with_worksheet(worksheet)

        self.assertEqual(report["closeout_gate"]["status"], "blocked")
        self.assertIn("worksheet_review_row_count_summary_drift", report["closeout_gate"]["blockers"])
        self.assertIn("worksheet_review_row_count_drift", report["closeout_gate"]["blockers"])
        self.assertIn("worksheet_case_count_drift", report["closeout_gate"]["blockers"])
        self.assertIn("worksheet_policy_category_order_drift", report["closeout_gate"]["blockers"])
        self.assertIn("worksheet_policy_id_order_drift", report["closeout_gate"]["blockers"])
        self.assertEqual(assertion_status(report, "closeout_has_eight_rows"), "failed")

    def test_forbidden_or_advisory_source_keys_block_closeout(self):
        worksheet = load_current_worksheet()
        worksheet["review_worksheet_rows"][0]["implementation_plan"] = {"step": "should_not_exist"}
        worksheet["review_worksheet_rows"][0]["ai_suggestion"] = True

        report = build_with_worksheet(worksheet)

        self.assertEqual(report["closeout_gate"]["status"], "blocked")
        self.assertIn("worksheet_forbidden_key_present:implementation_plan", report["closeout_gate"]["blockers"])
        self.assertIn("worksheet_advisory_signal_present:ai_suggestion", report["closeout_gate"]["blockers"])
        for node in walk_dicts(report):
            self.assertFalse({"work_items", "engineering_tasks", "pending_tasks"} & set(node.keys()))

    def test_mojibake_like_text_blocks_human_readability_gate(self):
        worksheet = load_current_worksheet()
        worksheet["review_worksheet_rows"][0]["review_questions"][0] = "\u9428 damaged text"

        report = build_with_worksheet(worksheet)

        self.assertEqual(report["closeout_gate"]["status"], "blocked")
        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("blocked_for_human_readability", report["closeout_gate"]["blockers"])
        self.assertEqual(assertion_status(report, "text_readability_gate"), "failed")

    def test_markdown_is_closeout_only_and_readable(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.8.4 Final Evidence Selection Policy Closeout Envelope", markdown)
        self.assertIn("本文件是最终证据选择 policy table 的人工收口外壳", markdown)
        self.assertIn("## Closeout Rows", markdown)
        self.assertIn("## Closeout Questions", markdown)
        self.assertIn("## Closeout Options", markdown)
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
            Path("tools/build_final_evidence_selection_policy_closeout_envelope.py"),
            Path("docs/final_evidence_selection_policy_closeout_envelope_v0.4.8.4.md"),
            Path("tests/final_evidence_selection_policy_closeout_envelope_report.json"),
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
