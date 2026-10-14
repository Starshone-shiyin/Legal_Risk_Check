import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_final_evidence_selection_policy_simulator_spec import (
    DEFAULT_AUDIT_REPORT_PATH,
    DEFAULT_CONFIRMATION_REPORT_PATH,
    DEFAULT_INTAKE_REPORT_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    EXPECTED_CASE_COUNT,
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


class FinalEvidenceSelectionPolicySimulatorSpecTest(unittest.TestCase):
    def test_default_paths_use_legacy_reports_and_docs_markdown_output(self):
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
            legacy_report_path("final_evidence_selection_policy_simulator_spec_report.json"),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/final_evidence_selection_policy_simulator_spec_v0.4.8.1.md"),
        )

    def test_real_current_reports_build_saved_report_simulator_spec(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.8.1")
        self.assertEqual(report["schema_kind"], "final_evidence_selection_policy_simulator_spec")
        self.assertEqual(report["scope"], "offline final evidence selection policy simulator spec only")
        self.assertEqual(report["simulator_spec_gate"]["status"], "ready_for_offline_policy_simulator_spec")
        self.assertEqual(report["simulator_spec_gate"]["allowed_use"], "offline_policy_simulator_spec_only")
        self.assertTrue(report["simulator_spec_gate"]["saved_report_only"])
        self.assertTrue(report["simulator_spec_gate"]["simulator_spec_allowed"])
        self.assertFalse(report["simulator_spec_gate"]["simulator_implementation_allowed"])
        self.assertFalse(report["simulator_spec_gate"]["policy_implementation_allowed"])
        self.assertFalse(report["simulator_spec_gate"]["implementation_allowed"])
        self.assertFalse(report["simulator_spec_gate"]["code_patch_authorized"])
        self.assertFalse(report["simulator_spec_gate"]["runtime_policy_implementation_allowed"])
        self.assertFalse(report["simulator_spec_gate"]["runtime_selection_policy_patch_allowed"])
        self.assertFalse(report["simulator_spec_gate"]["rerank_change_allowed"])
        self.assertEqual(report["simulator_spec_gate"]["rag_query_integration"], "disallowed")
        self.assertEqual(report["simulator_spec_gate"]["blockers"], [])

        summary = report["summary"]
        self.assertEqual(summary["status"], "ready_for_offline_policy_simulator_spec")
        self.assertEqual(summary["confirmed_case_count"], EXPECTED_CASE_COUNT)
        self.assertEqual(summary["source_intake_case_count"], EXPECTED_CASE_COUNT)
        self.assertEqual(summary["audit_high_priority_review_cases"], EXPECTED_CASE_COUNT)
        self.assertEqual(summary["policy_candidate_category_count"], 6)
        self.assertEqual(summary["failure_signal_count"], 8)
        self.assertEqual(summary["manual_review_required_case_count"], EXPECTED_CASE_COUNT)
        self.assertEqual(summary["next_version_recommendation"], "v0.4.8.2 policy table draft")
        self.assertIn("primary_evidence_should_be_preserved", summary["required_quality_signal_summary"])
        self.assertIn("manual_review_required_for_high_risk_gap", summary["required_quality_signal_summary"])
        self.assertFalse(summary["implementation_allowed"])
        self.assertFalse(summary["runtime_policy_implementation_allowed"])
        self.assertFalse(summary["runtime_selection_policy_patch_allowed"])
        self.assertFalse(summary["rerank_change_allowed"])

        input_contract = report["input_contract"]
        self.assertEqual(input_contract["contract_type"], "saved_report_only_input_contract")
        self.assertEqual(len(input_contract["required_reports"]), 3)
        self.assertIn("live RAG output", input_contract["forbidden_inputs"])

        output_contract = report["simulation_output_contract"]
        self.assertEqual(output_contract["contract_type"], "future_offline_simulator_output_contract")
        self.assertIn("case_results", output_contract["required_top_level_fields"])
        self.assertIn("runtime policy patch", output_contract["must_not_emit"])

        categories = report["policy_candidate_categories"]
        self.assertEqual(
            {item["category_id"] for item in categories},
            {"primary", "operative", "procedural", "liability", "scenario_core", "definition_only"},
        )
        self.assertTrue(all(item["allowed_stage"] == "offline_spec_only" for item in categories))

        rows = report["case_simulation_spec_matrix"]
        self.assertEqual(len(rows), EXPECTED_CASE_COUNT)
        self.assertTrue(all(row["spec_status"] == "ready_for_saved_report_simulation_spec" for row in rows))
        self.assertTrue(all(row["manual_review_required"] for row in rows))
        self.assertTrue(all(row["simulator_expected_status"] == "manual_review_required_before_runtime_policy" for row in rows))
        self.assertIn(
            "liability_evidence_should_be_preserved",
            {
                signal["signal_id"]
                for row in rows
                for signal in row["required_quality_signals"]
            },
        )
        self.assertIn(
            "definition_only_must_not_substitute_normative_evidence",
            {
                signal["signal_id"]
                for row in rows
                for signal in row["required_quality_signals"]
            },
        )

        manual_review_gate = report["manual_review_gate"]
        self.assertEqual(manual_review_gate["status"], "manual_review_required_before_runtime_policy")
        self.assertEqual(manual_review_gate["manual_review_required_count"], EXPECTED_CASE_COUNT)
        self.assertTrue(manual_review_gate["design_policy_table_draft_allowed"])
        self.assertFalse(manual_review_gate["runtime_policy_adoption_allowed_without_review"])

        handoff = report["next_version_handoff"]
        self.assertEqual(handoff["recommended_next_version"], "v0.4.8.2")
        self.assertFalse(handoff["runtime_implementation_allowed"])

        self.assertTrue(all(item["status"] == "passed" for item in report["assertions"]))
        for node in walk_dicts(report):
            self.assertFalse(FORBIDDEN_OUTPUT_KEYS & set(node.keys()))

    def test_intake_drift_blocks_simulator_spec(self):
        intake = load_json("tests/final_evidence_selection_policy_intake_report.json")
        intake["version"] = "0.4.7.9.9"
        intake["intake_gate"]["status"] = "blocked"
        intake["policy_simulator_plan"]["runtime_integration_allowed"] = True

        report = build_with_sources(intake_report_path=intake)

        self.assertEqual(report["simulator_spec_gate"]["status"], "blocked")
        self.assertFalse(report["simulator_spec_gate"]["simulator_spec_allowed"])
        self.assertIn("intake_version_mismatch", report["simulator_spec_gate"]["blockers"])
        self.assertIn("intake_gate_not_ready", report["simulator_spec_gate"]["blockers"])
        self.assertIn("intake_runtime_integration_not_blocked", report["simulator_spec_gate"]["blockers"])
        self.assertEqual(assertion_status(report, "source_reports_are_ready_for_simulator_spec"), "failed")

    def test_audit_or_confirmation_drift_blocks_simulator_spec(self):
        audit = load_json("tests/final_evidence_selection_audit_report.json")
        audit["summary"]["high_priority_review_cases"] = 4
        confirmation = load_json("tests/ready_action_human_closeout_confirmation_record_report.json")
        confirmation["confirmation_matrix"][0]["confirmed_next_series"] = "v0.4.9.x"

        report = build_with_sources(
            audit_report_path=audit,
            confirmation_report_path=confirmation,
        )

        self.assertEqual(report["simulator_spec_gate"]["status"], "blocked")
        self.assertIn("audit_high_priority_count_drift", report["simulator_spec_gate"]["blockers"])
        self.assertIn("confirmation_next_series_mismatch", report["simulator_spec_gate"]["blockers"])

    def test_forbidden_or_advisory_source_keys_block_simulator_spec(self):
        intake = load_json("tests/final_evidence_selection_policy_intake_report.json")
        intake["case_intake_matrix"][0]["implementation_plan"] = {"step": "should_not_exist"}
        intake["case_intake_matrix"][0]["ai_suggestion"] = True

        report = build_with_sources(intake_report_path=intake)

        self.assertEqual(report["simulator_spec_gate"]["status"], "blocked")
        self.assertIn("intake_forbidden_key_present:implementation_plan", report["simulator_spec_gate"]["blockers"])
        self.assertIn("intake_advisory_signal_present:ai_suggestion", report["simulator_spec_gate"]["blockers"])

    def test_mojibake_like_text_blocks_spec_readability_gate(self):
        intake = load_json("tests/final_evidence_selection_policy_intake_report.json")
        intake["case_intake_matrix"][0]["review_reasons"] = ["\u9428 damaged text"]

        report = build_with_sources(intake_report_path=intake)

        self.assertEqual(report["simulator_spec_gate"]["status"], "blocked")
        self.assertIn("blocked_for_human_readability", report["simulator_spec_gate"]["blockers"])
        self.assertEqual(assertion_status(report, "text_readability_gate"), "failed")

    def test_markdown_is_spec_not_runtime_policy(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.8.1 Final Evidence Selection Policy Simulator Spec", markdown)
        self.assertIn("离线契约", markdown)
        self.assertIn("不是 runtime policy 实现", markdown)
        self.assertIn("## Input Contract", markdown)
        self.assertIn("## Policy Candidate Categories", markdown)
        self.assertIn("## Case Spec Matrix", markdown)
        self.assertIn("## Failure Signals", markdown)
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
            Path("tools/build_final_evidence_selection_policy_simulator_spec.py"),
            Path("docs/final_evidence_selection_policy_simulator_spec_v0.4.8.1.md"),
            Path("tests/final_evidence_selection_policy_simulator_spec_report.json"),
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
