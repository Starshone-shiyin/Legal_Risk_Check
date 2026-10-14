import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.check_ready_action_design_review_gate import (
    DEFAULT_BRIEF_REPORT_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    EXPECTED_REVIEW_ORDER,
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


def load_current_brief() -> dict:
    return json.loads(Path("tests/ready_action_design_review_brief_report.json").read_text(encoding="utf-8-sig"))


class ReadyActionDesignReviewGateTest(unittest.TestCase):
    def test_default_paths_use_legacy_report_and_docs_markdown_output(self):
        self.assertEqual(
            DEFAULT_BRIEF_REPORT_PATH,
            legacy_report_path("ready_action_design_review_brief_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("ready_action_design_review_gate_report.json"),
        )
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/ready_action_design_review_gate_v0.4.7.9.2.md"))

    def test_real_current_brief_opens_human_design_review_gate_only(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.7.9.2")
        self.assertEqual(report["schema_kind"], "ready_action_design_review_gate")
        self.assertEqual(report["gate"]["status"], "open_for_human_design_review_only")
        self.assertEqual(report["gate"]["allowed_use"], "human_design_review_discussion_only")
        self.assertEqual(report["gate"]["design_spec_draft_status"], "draft_material_available_only")
        self.assertTrue(report["gate"]["human_design_review_allowed"])
        self.assertFalse(report["gate"]["implementation_allowed"])
        self.assertFalse(report["gate"]["code_patch_authorized"])
        self.assertEqual(report["gate"]["handoff_to_implementation"], "not_allowed")
        self.assertTrue(report["gate"]["future_explicit_implementation_approval_required"])
        self.assertEqual(report["gate"]["blockers"], [])

        self.assertEqual(report["source_brief"]["version"], "0.4.7.9.1")
        self.assertEqual(report["source_brief"]["schema_kind"], "ready_action_design_review_brief")
        self.assertEqual(report["source_brief"]["source_design_pack_version"], "0.4.7.9.0")
        self.assertEqual(report["source_integrity"]["status"], "passed")
        self.assertEqual(report["review_scope"]["design_action_count"], 18)
        self.assertEqual(report["review_scope"]["source_case_count"], 5)
        self.assertEqual(report["review_scope"]["design_track_count"], 5)
        self.assertEqual(report["review_scope"]["pending_records_excluded"], 31)
        self.assertEqual(report["review_scope"]["priority_band_summary"], {"P0": 3, "P1": 2})
        self.assertEqual(report["review_scope"]["review_order"], EXPECTED_REVIEW_ORDER)
        self.assertEqual(len(report["traceability"]["design_action_ids"]), 18)
        self.assertTrue(all(item["status"] == "passed" for item in report["assertions"]))

        for track in report["track_gates"]:
            self.assertEqual(track["status"], "open_for_human_design_review_only")
            self.assertEqual(track["allowed_use"], "human_design_review_discussion_only")
            self.assertFalse(track["implementation_allowed"])
            self.assertFalse(track["code_patch_authorized"])
            self.assertTrue(track["traceability"]["design_action_ids"])
            self.assertTrue(track["traceability"]["source_case_ids"])

        for node in walk_dicts(report):
            self.assertFalse(FORBIDDEN_OUTPUT_KEYS & set(node.keys()))

    def test_traceability_ids_are_closed_under_source_brief(self):
        report = build_report()

        top_ids = set(report["traceability"]["design_action_ids"])
        track_ids = {
            action_id
            for track in report["track_gates"]
            for action_id in track["traceability"]["design_action_ids"]
        }
        self.assertEqual(track_ids, top_ids)

    def test_wrong_schema_or_blocked_brief_blocks_gate(self):
        brief = load_current_brief()
        brief["schema_kind"] = "wrong_schema"
        brief["brief_gate"]["status"] = "blocked_for_design_review_brief"
        brief["brief_gate"]["human_design_review_allowed"] = False
        brief["assertions"][0]["status"] = "failed"

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "brief.json"
            write_json(path, brief)

            report = build_report(path)

        self.assertEqual(report["gate"]["status"], "blocked")
        self.assertFalse(report["gate"]["human_design_review_allowed"])
        self.assertFalse(report["gate"]["implementation_allowed"])
        self.assertIn("source_brief_schema_mismatch", report["gate"]["blockers"])
        self.assertIn("source_brief_gate_not_open", report["gate"]["blockers"])
        self.assertIn("source_assertions_not_all_passed", report["gate"]["blockers"])

    def test_source_design_pack_not_ready_blocks_gate(self):
        brief = load_current_brief()
        brief["source_design_pack"]["summary_status"] = "blocked"

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "brief.json"
            write_json(path, brief)

            report = build_report(path)

        self.assertEqual(report["gate"]["status"], "blocked")
        self.assertFalse(report["gate"]["human_design_review_allowed"])
        self.assertFalse(report["gate"]["implementation_allowed"])
        self.assertIn("source_design_pack_summary_not_ready", report["gate"]["blockers"])

    def test_implementation_authorization_in_source_blocks_gate(self):
        brief = load_current_brief()
        brief["brief_gate"]["implementation_allowed"] = True
        brief["summary"]["implementation_allowed"] = True
        brief["guardrails"]["implementation_allowed"] = True

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "brief.json"
            write_json(path, brief)

            report = build_report(path)

        self.assertEqual(report["gate"]["status"], "blocked")
        self.assertFalse(report["gate"]["implementation_allowed"])
        self.assertIn("source_brief_gate_implementation_not_blocked", report["gate"]["blockers"])
        self.assertIn("source_summary_implementation_not_blocked", report["gate"]["blockers"])
        self.assertIn("source_brief_guardrail_mismatch:implementation_allowed", report["gate"]["blockers"])

    def test_pending_or_advisory_signals_block_gate_without_becoming_tasks(self):
        brief = load_current_brief()
        brief["safe_ai_suggestion_input"] = True
        brief["excluded_scope"]["pending_backlog"] = ["case_x"]

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "brief.json"
            write_json(path, brief)

            report = build_report(path)

        serialized = json.dumps(report, ensure_ascii=False).lower()
        self.assertEqual(report["gate"]["status"], "blocked")
        self.assertIn("source_advisory_signal_present:safe_ai_suggestion_input", report["gate"]["blockers"])
        self.assertIn("source_forbidden_key_present:pending_backlog", report["gate"]["blockers"])
        self.assertEqual(report["excluded_scope"]["pending_records_policy"], "background_count_only_not_work_items")
        self.assertNotIn("pending_task", serialized)
        self.assertNotIn("pending_tasks", serialized)
        self.assertNotIn("ready_to_apply", serialized)

    def test_unexpected_traceability_or_review_order_blocks_gate(self):
        brief = load_current_brief()
        brief["track_briefs"][0]["traceability"]["design_action_ids"].append("unexpected::action")
        brief["summary"]["review_order"] = list(reversed(brief["summary"]["review_order"]))

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "brief.json"
            write_json(path, brief)

            report = build_report(path)

        self.assertEqual(report["gate"]["status"], "blocked")
        self.assertIn("source_review_order_drift", report["gate"]["blockers"])
        self.assertIn("track_action_ids_not_subset_of_top_traceability:final_evidence_selection_policy_review", report["gate"]["blockers"])

    def test_each_brief_guardrail_mismatch_blocks_gate(self):
        brief = load_current_brief()
        guardrail_expectations = {
            "brief_only": True,
            "source_design_pack_only": True,
            "not_action_approval": True,
            "not_implementation_authorization": True,
            "implementation_allowed": False,
            "code_patch_authorized": False,
            "pending_records_to_tasks": "disallowed",
            "fixture_write_to_eval": "disallowed",
            "scenario_registry_mutation": "disallowed",
            "eval_case_mutation": "disallowed",
            "hidden_seed_mutation": "disallowed",
            "anchor_mutation": "disallowed",
            "rerank_mutation": "disallowed",
            "prompt_mutation": "disallowed",
            "risk_rule_mutation": "disallowed",
            "term_preservation_rule_mutation": "disallowed",
            "rag_query_integration": "disallowed",
            "main_flow_mutation": "disallowed",
            "backend_api_write": "disallowed",
            "qdrant_access": "disallowed",
            "llm_access": "disallowed",
            "full_eval": "not_run",
        }

        for key, expected in guardrail_expectations.items():
            with self.subTest(key=key):
                mutated = copy.deepcopy(brief)
                mutated["guardrails"][key] = "mutated" if expected is not True else False
                with tempfile.TemporaryDirectory() as tmpdir:
                    path = Path(tmpdir) / "brief.json"
                    write_json(path, mutated)
                    report = build_report(path)

                self.assertEqual(report["gate"]["status"], "blocked")
                self.assertIn(f"source_brief_guardrail_mismatch:{key}", report["gate"]["blockers"])

    def test_markdown_explains_gate_is_not_implementation_authorization(self):
        report = build_report()
        markdown = render_markdown(report)

        self.assertIn("人工设计评审入口门禁", markdown)
        self.assertIn("不批准任何代码、配置或样例修改", markdown)
        self.assertIn("implementation_allowed=false", markdown)
        self.assertIn("AI suggestion", markdown)
        self.assertNotIn("implementation_plan", markdown)
        self.assertNotIn("files_to_change", markdown)
        self.assertNotIn("commands", markdown)

    def test_source_has_no_runtime_backend_or_prohibited_config_patterns(self):
        source = Path("tools/check_ready_action_design_review_gate.py").read_text(encoding="utf-8")

        for pattern in PROHIBITED_SOURCE_PATTERNS:
            self.assertNotIn(pattern, source)


if __name__ == "__main__":
    unittest.main()
