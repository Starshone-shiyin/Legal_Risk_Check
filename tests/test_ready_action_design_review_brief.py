import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_ready_action_design_review_brief import (
    DEFAULT_DESIGN_PACK_REPORT_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    PROHIBITED_KEY_NAMES,
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


def minimal_design_pack(
    *,
    status: str = "ready_for_design_review",
    planning_status: str = "open_for_design_review",
    assertions_passed: bool = True,
) -> dict:
    return {
        "version": "0.4.7.9.0",
        "schema_kind": "governed_ready_action_design_pack",
        "scope": "offline ready action design pack",
        "inputs": {
            "promotion_dry_run_report": {"path": "promotion.json"},
            "export_pipeline_dry_run_report": {"path": "export.json"},
        },
        "guardrails": {
            "design_only": True,
            "not_action_approval": True,
            "implementation_patch_generation": "disallowed",
            "automatic_migration_ready": False,
            "code_patch_authorized": False,
            "schema_mutation": "disallowed",
            "manual_review_schema_mutation": "disallowed",
            "manual_review_importer_mutation": "disallowed",
            "manual_review_dry_run_contract_mutation": "disallowed",
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
        },
        "planning_gate": {
            "status": planning_status,
            "design_planning_allowed": planning_status == "open_for_design_review",
            "implementation_allowed": False,
            "implementation_status": "not_started",
            "implementation_requires_future_explicit_approval": True,
            "blocked_reasons": [],
        },
        "summary": {
            "status": status,
            "design_only": True,
            "implementation_allowed": False,
            "promotion_candidates": 2,
            "ready_action_candidates": 3,
            "source_ready_action_candidates": 3,
            "excluded_ready_action_candidates": 0,
            "ready_case_count": 2,
            "pending_records_excluded": 31,
            "pending_records_are_not_design_tasks": True,
            "design_track_count": 2,
            "action_type_summary": {
                "final_evidence_selection_policy_review": 2,
                "functional_typing_fixture_review": 1,
            },
        },
        "action_groups": {
            "functional_typing_fixture_review": {
                "design_track_id": "legal_functional_typing_fixture_review",
                "action_type": "functional_typing_fixture_review",
                "action_category": "functional_typing_quality",
                "priority_band": "P1",
                "ready_action_count": 1,
                "case_count": 1,
                "source_case_ids": ["case_b"],
                "expected_domains": ["数据合规"],
                "risk_level_summary": {"high": 1},
                "confirmed_root_cause_summary": {"functional_typing_metadata": 1},
                "target_area_summary": {"legal_functional_typing_fixture_pool": 1},
                "prohibited_now": ["functional_type_config_change", "golden_fixture_write"],
                "candidate_actions": [
                    {
                        "design_action_id": "case_b::functional_typing_fixture_review",
                        "case_id": "case_b",
                        "readiness": "ready_from_valid_decision",
                        "source_decision_status": "completed",
                        "validation_status": "valid",
                        "blocked_reason": "",
                        "priority_score": 9,
                    }
                ],
            },
            "final_evidence_selection_policy_review": {
                "design_track_id": "final_evidence_selection_policy_design",
                "action_type": "final_evidence_selection_policy_review",
                "action_category": "final_evidence_policy",
                "priority_band": "P0",
                "ready_action_count": 2,
                "case_count": 2,
                "source_case_ids": ["case_a", "case_b"],
                "expected_domains": ["数据合规"],
                "risk_level_summary": {"high": 2},
                "confirmed_root_cause_summary": {"final_evidence_selection_policy": 2},
                "target_area_summary": {"final_evidence_selection_policy_draft": 2},
                "prohibited_now": ["rerank_change", "prompt_change"],
                "candidate_actions": [
                    {
                        "design_action_id": "case_a::final_evidence_selection_policy_review",
                        "case_id": "case_a",
                        "readiness": "ready_from_valid_decision",
                        "source_decision_status": "completed",
                        "validation_status": "valid",
                        "blocked_reason": "",
                        "priority_score": 20,
                    },
                    {
                        "design_action_id": "case_b::final_evidence_selection_policy_review",
                        "case_id": "case_b",
                        "readiness": "ready_from_valid_decision",
                        "source_decision_status": "completed",
                        "validation_status": "valid",
                        "blocked_reason": "",
                        "priority_score": 18,
                    },
                ],
            },
        },
        "excluded_scope": {
            "pending_records_excluded": 31,
            "pending_records_are_not_confirmed_tasks": True,
            "excluded_ready_action_candidates": [],
            "pending_case_policy": "Pending records remain outside this design pack.",
        },
        "traceability": {
            "source_case_ids": ["case_a", "case_b"],
            "design_action_ids": [
                "case_a::final_evidence_selection_policy_review",
                "case_b::final_evidence_selection_policy_review",
                "case_b::functional_typing_fixture_review",
            ],
            "source_reports": ["promotion.json", "export.json"],
        },
        "assertions": [
            {
                "name": "source_ready",
                "status": "passed" if assertions_passed else "failed",
            }
        ],
    }


class ReadyActionDesignReviewBriefTest(unittest.TestCase):
    def test_default_paths_use_legacy_report_and_docs_markdown_output(self):
        self.assertEqual(
            DEFAULT_DESIGN_PACK_REPORT_PATH,
            legacy_report_path("ready_action_design_pack_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("ready_action_design_review_brief_report.json"),
        )
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/ready_action_design_review_brief_v0.4.7.9.1.md"))

    def test_real_current_design_pack_builds_ordered_brief_without_authorizing_implementation(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.7.9.1")
        self.assertEqual(report["schema_kind"], "ready_action_design_review_brief")
        self.assertEqual(report["summary"]["status"], "ready_for_human_design_review")
        self.assertEqual(report["summary"]["source_design_pack_version"], "0.4.7.9.0")
        self.assertEqual(report["summary"]["promotion_candidates"], 5)
        self.assertEqual(report["summary"]["ready_for_design_review_candidates"], 18)
        self.assertEqual(report["summary"]["source_ready_action_candidates"], 18)
        self.assertEqual(report["summary"]["ready_case_count"], 5)
        self.assertEqual(report["summary"]["pending_records_excluded"], 31)
        self.assertEqual(report["summary"]["design_track_count"], 5)
        self.assertFalse(report["brief_gate"]["implementation_allowed"])
        self.assertFalse(report["guardrails"]["implementation_allowed"])
        self.assertFalse(report["guardrails"]["code_patch_authorized"])
        self.assertFalse(report["summary"]["implementation_allowed"])
        self.assertFalse(report["summary"]["code_patch_authorized"])
        self.assertTrue(report["brief_gate"]["implementation_requires_future_explicit_approval"])

        self.assertEqual(
            report["summary"]["review_order"],
            [
                "final_evidence_selection_policy_review",
                "primary_evidence_fixture_candidate_review",
                "high_risk_manual_grounding_review",
                "scenario_registry_core_article_review",
                "functional_typing_fixture_review",
            ],
        )
        self.assertEqual(report["summary"]["priority_band_summary"], {"P0": 3, "P1": 2})
        self.assertEqual(len(report["traceability"]["design_action_ids"]), 18)
        self.assertTrue(all(item["status"] == "passed" for item in report["assertions"]))

        for track in report["track_briefs"]:
            self.assertIn("review_questions", track)
            self.assertIn("decision_points", track)
            self.assertIn("entry_criteria", track)
            self.assertIn("exit_criteria", track)
            self.assertIn("future_validation_before_implementation", track)
            self.assertIn("traceability", track)
            self.assertNotIn("implementation_plan", track)
            self.assertIn("future_validation_before_implementation", track)
            self.assertNotIn("files_to_change", track)
            self.assertNotIn("commands", track)

        for node in walk_dicts(report):
            self.assertFalse(PROHIBITED_KEY_NAMES & set(node.keys()))

    def test_synthetic_brief_preserves_traceability_and_stable_priority_sort(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "design_pack.json"
            write_json(path, minimal_design_pack())

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "ready_for_human_design_review")
        self.assertEqual(report["summary"]["review_order"][0], "final_evidence_selection_policy_review")
        self.assertEqual(report["summary"]["review_order"][1], "functional_typing_fixture_review")
        self.assertEqual(report["summary"]["pending_records_excluded"], 31)
        self.assertTrue(report["summary"]["pending_records_are_not_tasks"])
        self.assertEqual(
            set(report["traceability"]["design_action_ids"]),
            {
                "case_a::final_evidence_selection_policy_review",
                "case_b::final_evidence_selection_policy_review",
                "case_b::functional_typing_fixture_review",
            },
        )
        self.assertEqual(report["track_briefs"][0]["display_name"], "最终证据选择策略评审")
        self.assertIn("不是已批准的代码修改。", report["track_briefs"][0]["what_this_does_not_mean"])

    def test_blocked_or_failed_source_pack_blocks_brief(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "design_pack.json"
            write_json(
                path,
                minimal_design_pack(
                    status="blocked_for_design_review",
                    planning_status="blocked_for_design_review",
                    assertions_passed=False,
                ),
            )

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "blocked_for_human_design_review")
        self.assertEqual(report["summary"]["ready_for_design_review_candidates"], 0)
        self.assertEqual(report["summary"]["design_track_count"], 0)
        self.assertEqual(report["track_briefs"], [])
        self.assertFalse(report["brief_gate"]["human_design_review_allowed"])
        self.assertFalse(report["brief_gate"]["implementation_allowed"])
        self.assertFalse(report["summary"]["implementation_allowed"])
        self.assertFalse(report["guardrails"]["implementation_allowed"])
        self.assertIn("source_summary_not_ready_for_design_review", report["brief_gate"]["blockers"])
        self.assertIn("source_assertions_not_all_passed", report["brief_gate"]["blockers"])

    def test_pending_records_do_not_become_tasks_or_decisions(self):
        report = build_report()
        serialized = json.dumps(report, ensure_ascii=False).lower()

        self.assertIn("pending records are background only", report["excluded_scope"]["pending_records_policy"].lower())
        self.assertNotIn("pending_task", serialized)
        self.assertNotIn("pending_tasks", serialized)
        self.assertNotIn("backlog", serialized)
        self.assertNotIn("ready_to_apply", serialized)

    def test_markdown_explains_plain_language_boundaries(self):
        report = build_report()
        markdown = render_markdown(report)

        self.assertIn("给人工评审使用的简报", markdown)
        self.assertIn("不修 RAG", markdown)
        self.assertIn("推荐评审顺序", markdown)
        self.assertIn("最终证据选择策略评审", markdown)
        self.assertIn("31 个 pending records 只作为背景统计", markdown)

    def test_source_has_no_runtime_backend_or_prohibited_config_patterns(self):
        source = Path("tools/build_ready_action_design_review_brief.py").read_text(encoding="utf-8")

        for pattern in PROHIBITED_SOURCE_PATTERNS:
            self.assertNotIn(pattern, source)


if __name__ == "__main__":
    unittest.main()
