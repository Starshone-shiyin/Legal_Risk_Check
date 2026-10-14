import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_final_evidence_selection_policy_intake import (
    DEFAULT_CLOSEOUT_REPORT_PATH,
    DEFAULT_CONFIRMATION_REPORT_PATH,
    DEFAULT_DECISION_DRAFT_REPORT_PATH,
    DEFAULT_DESIGN_PACK_REPORT_PATH,
    DEFAULT_FINAL_SELECTION_AUDIT_REPORT_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_WORKSHEET_REPORT_PATH,
    EXPECTED_CONFIRMED_CASE_COUNT,
    EXPECTED_FINAL_SELECTION_ACTION_COUNT,
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


def walk_dicts(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_dicts(child)


def load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def assertion_status(report: dict, name: str) -> str | None:
    for assertion in report.get("assertions", []):
        if assertion.get("name") == name:
            return assertion.get("status")
    return None


def build_with_sources(**overrides: dict) -> dict:
    sources = {
        "confirmation_report_path": load_json("tests/ready_action_human_closeout_confirmation_record_report.json"),
        "decision_draft_report_path": load_json("tests/ready_action_human_closeout_decision_draft_report.json"),
        "closeout_report_path": load_json("tests/ready_action_design_review_closeout_report.json"),
        "worksheet_report_path": load_json("tests/ready_action_design_review_worksheet_report.json"),
        "design_pack_report_path": load_json("tests/ready_action_design_pack_report.json"),
        "final_selection_audit_report_path": load_json("tests/final_evidence_selection_audit_report.json"),
    }
    sources.update(overrides)
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        paths = {}
        for key, payload in sources.items():
            path = root / f"{key}.json"
            write_json(path, copy.deepcopy(payload))
            paths[key] = path
        return build_report(**paths)


class FinalEvidenceSelectionPolicyIntakeTest(unittest.TestCase):
    def test_default_paths_use_legacy_reports_and_docs_markdown_output(self):
        self.assertEqual(
            DEFAULT_CONFIRMATION_REPORT_PATH,
            legacy_report_path("ready_action_human_closeout_confirmation_record_report.json"),
        )
        self.assertEqual(
            DEFAULT_DECISION_DRAFT_REPORT_PATH,
            legacy_report_path("ready_action_human_closeout_decision_draft_report.json"),
        )
        self.assertEqual(
            DEFAULT_CLOSEOUT_REPORT_PATH,
            legacy_report_path("ready_action_design_review_closeout_report.json"),
        )
        self.assertEqual(
            DEFAULT_WORKSHEET_REPORT_PATH,
            legacy_report_path("ready_action_design_review_worksheet_report.json"),
        )
        self.assertEqual(DEFAULT_DESIGN_PACK_REPORT_PATH, legacy_report_path("ready_action_design_pack_report.json"))
        self.assertEqual(
            DEFAULT_FINAL_SELECTION_AUDIT_REPORT_PATH,
            legacy_report_path("final_evidence_selection_audit_report.json"),
        )
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("final_evidence_selection_policy_intake_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/final_evidence_selection_policy_intake_v0.4.8.0.md"))

    def test_real_current_reports_build_design_intake(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.8.0")
        self.assertEqual(report["schema_kind"], "final_evidence_selection_policy_design_intake")
        self.assertEqual(report["intake_gate"]["status"], "ready_for_policy_design_intake")
        self.assertEqual(report["intake_gate"]["allowed_use"], "final_evidence_selection_policy_design_input_only")
        self.assertTrue(report["intake_gate"]["design_intake_allowed"])
        self.assertFalse(report["intake_gate"]["policy_implementation_allowed"])
        self.assertFalse(report["intake_gate"]["implementation_allowed"])
        self.assertFalse(report["intake_gate"]["code_patch_authorized"])
        self.assertFalse(report["intake_gate"]["runtime_selection_policy_patch_allowed"])
        self.assertFalse(report["intake_gate"]["rerank_change_allowed"])
        self.assertEqual(report["intake_gate"]["rag_query_integration"], "disallowed")
        self.assertEqual(report["intake_gate"]["blockers"], [])

        summary = report["summary"]
        self.assertEqual(summary["status"], "ready_for_policy_design_intake")
        self.assertEqual(summary["confirmed_next_series"], "v0.4.8.x")
        self.assertEqual(summary["confirmed_case_count"], EXPECTED_CONFIRMED_CASE_COUNT)
        self.assertEqual(summary["design_action_count"], EXPECTED_FINAL_SELECTION_ACTION_COUNT)
        self.assertEqual(summary["matched_high_priority_case_count"], EXPECTED_CONFIRMED_CASE_COUNT)
        self.assertEqual(summary["policy_question_count"], 6)
        self.assertEqual(summary["preservation_item_count"], 6)
        self.assertEqual(summary["case_domain_occurrence_summary"], {"市场秩序": 1, "数据合规": 5})
        self.assertIn("occurrence count", summary["case_domain_counting_note"])
        self.assertFalse(summary["implementation_allowed"])
        self.assertFalse(summary["code_patch_authorized"])
        self.assertFalse(summary["rerank_change_allowed"])
        self.assertFalse(summary["runtime_selection_policy_patch_allowed"])

        case_rows = report["case_intake_matrix"]
        self.assertEqual(len(case_rows), EXPECTED_CONFIRMED_CASE_COUNT)
        self.assertTrue(all(row["intake_status"] == "policy_design_input_ready" for row in case_rows))
        self.assertEqual({row["audit_priority"] for row in case_rows}, {"high"})
        self.assertIn("risk_employee_data_export_001", {row["case_id"] for row in case_rows})
        self.assertTrue(all(row["lost_evidence_summary"]["count"] >= 1 for row in case_rows))

        preservation_items = report["preservation_rule_discussion_items"]
        self.assertEqual(len(preservation_items), 6)
        self.assertTrue(all(item["allowed_stage"] in {"design_discussion_only", "simulator_design_input_only"} for item in preservation_items))
        self.assertIn("preserve_primary_evidence", {item["item_id"] for item in preservation_items})
        self.assertIn("preserve_liability_evidence", {item["item_id"] for item in preservation_items})

        simulator = report["policy_simulator_plan"]
        self.assertEqual(simulator["recommended_next_version"], "v0.4.8.1")
        self.assertEqual(simulator["input_policy"], "saved_reports_only")
        self.assertFalse(simulator["runtime_integration_allowed"])
        self.assertFalse(simulator["rerank_change_allowed"])

        self.assertTrue(all(item["status"] == "passed" for item in report["assertions"]))
        for node in walk_dicts(report):
            self.assertFalse(FORBIDDEN_OUTPUT_KEYS & set(node.keys()))

    def test_confirmation_or_design_pack_drift_blocks_intake(self):
        confirmation = load_json("tests/ready_action_human_closeout_confirmation_record_report.json")
        confirmation["confirmation_gate"]["status"] = "blocked"
        confirmation["confirmation_matrix"][0]["confirmed_next_series"] = "v0.4.9.x"
        design_pack = load_json("tests/ready_action_design_pack_report.json")
        design_pack["action_groups"]["final_evidence_selection_policy_review"]["ready_action_count"] = 4

        report = build_with_sources(
            confirmation_report_path=confirmation,
            design_pack_report_path=design_pack,
        )

        self.assertEqual(report["intake_gate"]["status"], "blocked")
        self.assertFalse(report["intake_gate"]["design_intake_allowed"])
        self.assertIn("confirmation_gate_not_confirmed", report["intake_gate"]["blockers"])
        self.assertIn("final_selection_next_series_mismatch", report["intake_gate"]["blockers"])
        self.assertIn("design_pack_final_selection_action_count_drift", report["intake_gate"]["blockers"])
        self.assertEqual(assertion_status(report, "source_reports_are_ready_for_intake"), "failed")

    def test_final_selection_audit_drift_blocks_intake(self):
        audit = load_json("tests/final_evidence_selection_audit_report.json")
        audit["version"] = "0.4.7.4.4"
        audit["summary"]["high_priority_review_cases"] = 4

        report = build_with_sources(final_selection_audit_report_path=audit)

        self.assertEqual(report["intake_gate"]["status"], "blocked")
        self.assertIn("final_selection_audit_version_mismatch", report["intake_gate"]["blockers"])
        self.assertIn("audit_high_priority_count_drift", report["intake_gate"]["blockers"])

    def test_forbidden_or_advisory_source_keys_block_intake(self):
        confirmation = load_json("tests/ready_action_human_closeout_confirmation_record_report.json")
        confirmation["confirmation_matrix"][0]["implementation_plan"] = {"step": "should_not_exist"}
        confirmation["confirmation_matrix"][0]["ai_suggestion"] = True

        report = build_with_sources(confirmation_report_path=confirmation)

        self.assertEqual(report["intake_gate"]["status"], "blocked")
        self.assertIn("confirmation_forbidden_key_present:implementation_plan", report["intake_gate"]["blockers"])
        self.assertIn("confirmation_advisory_signal_present:ai_suggestion", report["intake_gate"]["blockers"])

    def test_mojibake_like_text_blocks_intake_readability_gate(self):
        confirmation = load_json("tests/ready_action_human_closeout_confirmation_record_report.json")
        confirmation["confirmation_matrix"][0]["confirmation_basis"] = "\u9428 damaged text"

        report = build_with_sources(confirmation_report_path=confirmation)

        self.assertEqual(report["intake_gate"]["status"], "blocked")
        self.assertIn("blocked_for_human_readability", report["intake_gate"]["blockers"])
        self.assertEqual(assertion_status(report, "text_readability_gate"), "failed")

    def test_markdown_is_design_intake_not_runtime_patch(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.8.0 Final Evidence Selection Policy Design Intake", markdown)
        self.assertIn("不实现策略、不修改 rerank、不接入主流程", markdown)
        self.assertIn("## Policy Questions", markdown)
        self.assertIn("## Preservation Discussion Items", markdown)
        self.assertIn("## Case Intake Matrix", markdown)
        self.assertIn("`implementation_allowed=false`", markdown)
        self.assertIn("`code_patch_authorized=false`", markdown)
        self.assertIn("`rerank_change_allowed=false`", markdown)
        for token in [
            "implementation_plan",
            "files_to_change",
            "commands",
            "work_items",
            "engineering_tasks",
        ]:
            self.assertNotIn(token, markdown)

    def test_tool_and_outputs_do_not_contain_runtime_or_eval_mutation_patterns(self):
        target_paths = [
            Path("tools/build_final_evidence_selection_policy_intake.py"),
            Path("docs/final_evidence_selection_policy_intake_v0.4.8.0.md"),
            Path("tests/final_evidence_selection_policy_intake_report.json"),
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
