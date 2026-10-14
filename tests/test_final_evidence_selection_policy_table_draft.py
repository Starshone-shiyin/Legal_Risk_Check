import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_final_evidence_selection_policy_table_draft import (
    DEFAULT_AUDIT_REPORT_PATH,
    DEFAULT_CONFIRMATION_REPORT_PATH,
    DEFAULT_INTAKE_REPORT_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_SIMULATOR_SPEC_REPORT_PATH,
    EXPECTED_CASE_COUNT,
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


def load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


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


def build_with_sources(**overrides: dict) -> dict:
    sources = {
        "simulator_spec_report_path": load_json("tests/final_evidence_selection_policy_simulator_spec_report.json"),
        "intake_report_path": load_json("tests/final_evidence_selection_policy_intake_report.json"),
        "audit_report_path": load_json("tests/final_evidence_selection_audit_report.json"),
        "confirmation_report_path": load_json("tests/ready_action_human_closeout_confirmation_record_report.json"),
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


class FinalEvidenceSelectionPolicyTableDraftTest(unittest.TestCase):
    def test_default_paths_use_legacy_reports_and_docs_markdown_output(self):
        self.assertEqual(
            DEFAULT_SIMULATOR_SPEC_REPORT_PATH,
            legacy_report_path("final_evidence_selection_policy_simulator_spec_report.json"),
        )
        self.assertEqual(
            DEFAULT_INTAKE_REPORT_PATH,
            legacy_report_path("final_evidence_selection_policy_intake_report.json"),
        )
        self.assertEqual(DEFAULT_AUDIT_REPORT_PATH, legacy_report_path("final_evidence_selection_audit_report.json"))
        self.assertEqual(
            DEFAULT_CONFIRMATION_REPORT_PATH,
            legacy_report_path("ready_action_human_closeout_confirmation_record_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("final_evidence_selection_policy_table_draft_report.json"),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/final_evidence_selection_policy_table_draft_v0.4.8.2.md"),
        )

    def test_real_current_reports_build_saved_report_policy_table_draft(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.8.2")
        self.assertEqual(report["schema_kind"], "final_evidence_selection_policy_table_draft")
        self.assertEqual(report["scope"], "offline final evidence selection policy table draft only")
        self.assertEqual(report["policy_table_gate"]["status"], "ready_for_manual_review_policy_table_draft")
        self.assertEqual(report["policy_table_gate"]["allowed_use"], "offline_policy_table_draft_only")
        self.assertTrue(report["policy_table_gate"]["saved_report_only"])
        self.assertTrue(report["policy_table_gate"]["policy_table_draft_allowed"])
        self.assertFalse(report["policy_table_gate"]["policy_implementation_allowed"])
        self.assertFalse(report["policy_table_gate"]["implementation_allowed"])
        self.assertFalse(report["policy_table_gate"]["code_patch_authorized"])
        self.assertFalse(report["policy_table_gate"]["runtime_policy_implementation_allowed"])
        self.assertFalse(report["policy_table_gate"]["runtime_selection_policy_patch_allowed"])
        self.assertFalse(report["policy_table_gate"]["rerank_change_allowed"])
        self.assertEqual(report["policy_table_gate"]["rag_query_integration"], "disallowed")
        self.assertEqual(report["policy_table_gate"]["blockers"], [])

        summary = report["summary"]
        self.assertEqual(summary["status"], "ready_for_manual_review_policy_table_draft")
        self.assertEqual(summary["confirmed_case_count"], EXPECTED_CASE_COUNT)
        self.assertEqual(summary["policy_table_row_count"], EXPECTED_TABLE_ROW_COUNT)
        self.assertEqual(summary["policy_rows_with_case_signal_count"], EXPECTED_TABLE_ROW_COUNT)
        self.assertEqual(summary["manual_review_required_case_count"], EXPECTED_CASE_COUNT)
        self.assertEqual(summary["next_version_recommendation"], "v0.4.8.3 policy table human review worksheet")
        self.assertFalse(summary["implementation_allowed"])
        self.assertFalse(summary["runtime_policy_implementation_allowed"])
        self.assertFalse(summary["runtime_selection_policy_patch_allowed"])
        self.assertFalse(summary["rerank_change_allowed"])
        self.assertIn("primary_evidence_should_be_preserved", summary["policy_signal_case_summary"])
        self.assertIn("manual_review_required_for_high_risk_gap", summary["policy_signal_case_summary"])

        input_contract = report["input_contract"]
        self.assertEqual(input_contract["contract_type"], "saved_report_only_policy_table_draft_input_contract")
        self.assertEqual(len(input_contract["required_reports"]), 4)
        self.assertIn("runtime policy state", input_contract["forbidden_inputs"])

        table_contract = report["policy_table_contract"]
        self.assertEqual(table_contract["contract_type"], "human_reviewable_policy_table_draft_contract")
        self.assertIn("policy_table_rows", table_contract["required_top_level_fields"])
        self.assertIn("runtime policy patch", table_contract["must_not_emit"])

        rows = report["policy_table_rows"]
        self.assertEqual(len(rows), EXPECTED_TABLE_ROW_COUNT)
        self.assertEqual(
            {row["policy_category"] for row in rows},
            {
                "primary",
                "operative",
                "procedural",
                "liability",
                "scenario_core",
                "definition_only",
                "coverage_floor",
                "high_risk_manual_review",
            },
        )
        self.assertTrue(all(row["policy_status"] == "draft_for_manual_review" for row in rows))
        self.assertTrue(all(row["runtime_adoption_status"] == "not_allowed" for row in rows))
        self.assertTrue(all(row["implementation_allowed"] is False for row in rows))
        self.assertTrue(all(row["case_count"] > 0 for row in rows))
        self.assertIn(
            "definition_only_must_not_substitute_normative_evidence",
            {row["required_quality_signal"] for row in rows},
        )
        self.assertIn(
            "final_coverage_floor_review_needed",
            {row["required_quality_signal"] for row in rows},
        )

        manual_review_gate = report["manual_review_gate"]
        self.assertEqual(manual_review_gate["status"], "manual_review_required_before_runtime_policy")
        self.assertEqual(manual_review_gate["policy_rows_requiring_review_count"], EXPECTED_TABLE_ROW_COUNT)
        self.assertEqual(manual_review_gate["high_risk_manual_review_case_count"], EXPECTED_CASE_COUNT)
        self.assertTrue(manual_review_gate["policy_table_draft_allowed"])
        self.assertFalse(manual_review_gate["runtime_policy_adoption_allowed_without_review"])
        self.assertTrue(manual_review_gate["requires_manual_review_before_runtime_adoption"])

        handoff = report["next_version_handoff"]
        self.assertEqual(handoff["recommended_next_version"], "v0.4.8.3")
        self.assertFalse(handoff["runtime_implementation_allowed"])

        self.assertTrue(all(item["status"] == "passed" for item in report["assertions"]))
        for node in walk_dicts(report):
            self.assertFalse(FORBIDDEN_OUTPUT_KEYS & set(node.keys()))

    def test_simulator_spec_drift_blocks_policy_table_draft(self):
        simulator_spec = load_json("tests/final_evidence_selection_policy_simulator_spec_report.json")
        simulator_spec["version"] = "0.4.8.0"
        simulator_spec["simulator_spec_gate"]["status"] = "blocked"
        simulator_spec["summary"]["next_version_recommendation"] = "v0.4.8.9"
        simulator_spec["manual_review_gate"]["runtime_policy_adoption_allowed_without_review"] = True

        report = build_with_sources(simulator_spec_report_path=simulator_spec)

        self.assertEqual(report["policy_table_gate"]["status"], "blocked")
        self.assertFalse(report["policy_table_gate"]["policy_table_draft_allowed"])
        self.assertIn("simulator_spec_version_mismatch", report["policy_table_gate"]["blockers"])
        self.assertIn("simulator_spec_gate_not_ready", report["policy_table_gate"]["blockers"])
        self.assertIn("simulator_spec_next_version_mismatch", report["policy_table_gate"]["blockers"])
        self.assertIn("simulator_spec_runtime_adoption_not_blocked", report["policy_table_gate"]["blockers"])
        self.assertEqual(assertion_status(report, "source_reports_are_ready_for_policy_table_draft"), "failed")

    def test_source_report_drift_blocks_policy_table_draft(self):
        intake = load_json("tests/final_evidence_selection_policy_intake_report.json")
        intake["version"] = "0.4.7.9"
        audit = load_json("tests/final_evidence_selection_audit_report.json")
        audit["scope"] = "changed"
        confirmation = load_json("tests/ready_action_human_closeout_confirmation_record_report.json")
        confirmation["schema_kind"] = "changed"

        report = build_with_sources(
            intake_report_path=intake,
            audit_report_path=audit,
            confirmation_report_path=confirmation,
        )

        self.assertEqual(report["policy_table_gate"]["status"], "blocked")
        self.assertIn("intake_version_mismatch", report["policy_table_gate"]["blockers"])
        self.assertIn("audit_scope_mismatch", report["policy_table_gate"]["blockers"])
        self.assertIn("confirmation_schema_mismatch", report["policy_table_gate"]["blockers"])

    def test_forbidden_or_advisory_source_keys_block_policy_table_draft(self):
        simulator_spec = load_json("tests/final_evidence_selection_policy_simulator_spec_report.json")
        simulator_spec["case_simulation_spec_matrix"][0]["implementation_plan"] = {"step": "should_not_exist"}
        simulator_spec["case_simulation_spec_matrix"][0]["ai_suggestion"] = True

        report = build_with_sources(simulator_spec_report_path=simulator_spec)

        self.assertEqual(report["policy_table_gate"]["status"], "blocked")
        self.assertIn(
            "simulator_spec_forbidden_key_present:implementation_plan",
            report["policy_table_gate"]["blockers"],
        )
        self.assertIn(
            "simulator_spec_advisory_signal_present:ai_suggestion",
            report["policy_table_gate"]["blockers"],
        )

    def test_mojibake_like_text_blocks_table_readability_gate(self):
        simulator_spec = load_json("tests/final_evidence_selection_policy_simulator_spec_report.json")
        simulator_spec["case_simulation_spec_matrix"][0]["review_reasons"] = ["\u9428 damaged text"]

        report = build_with_sources(simulator_spec_report_path=simulator_spec)

        self.assertEqual(report["policy_table_gate"]["status"], "blocked")
        self.assertIn("blocked_for_human_readability", report["policy_table_gate"]["blockers"])
        self.assertEqual(assertion_status(report, "text_readability_gate"), "failed")

    def test_markdown_is_table_draft_not_runtime_policy(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.8.2 Final Evidence Selection Policy Table Draft", markdown)
        self.assertIn("策略表草案", markdown)
        self.assertIn("不是 runtime policy 实现", markdown)
        self.assertIn("## Policy Table Rows", markdown)
        self.assertIn("## Preservation Rules", markdown)
        self.assertIn("## Manual Review Gate", markdown)
        self.assertIn("不实现 runtime policy", markdown)
        self.assertIn("不修改 rerank", markdown)
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
            Path("tools/build_final_evidence_selection_policy_table_draft.py"),
            Path("docs/final_evidence_selection_policy_table_draft_v0.4.8.2.md"),
            Path("tests/final_evidence_selection_policy_table_draft_report.json"),
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
