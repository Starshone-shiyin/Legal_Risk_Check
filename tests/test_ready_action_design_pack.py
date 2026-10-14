import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_ready_action_design_pack import (
    DEFAULT_EXPORT_PIPELINE_DRY_RUN_REPORT_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_PROMOTION_REPORT_PATH,
    DESIGN_ONLY_GUARDRAILS,
    build_report,
    render_markdown,
)


FORBIDDEN_OUTPUT_KEYS = {
    "reviewer_input_template",
    "reviewer_decision",
    "workbench_items",
}

PROHIBITED_SOURCE_PATTERNS = [
    "rag_query(",
    "ChatOpenAI",
    "QdrantClient",
    "fetch(",
    "XMLHttpRequest",
    "/ask",
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


def promotion_report() -> dict:
    return {
        "version": "promotion-test",
        "scope": "offline validated decision promotion dry run",
        "summary": {
            "promotion_candidates": 1,
            "ready_action_candidates": 2,
            "valid_records": 1,
            "invalid_records": 0,
            "pending_records": 3,
        },
        "promotion_candidates": [
            {
                "case_id": "case_a",
                "reviewer": "reviewer",
                "reviewed_at": "2026-05-13",
                "decision": "confirm_diagnostic_issue",
                "confirmed_root_causes": [
                    "primary_evidence_gap",
                    "final_evidence_selection_policy",
                ],
                "confirmed_follow_up_actions": [
                    "primary_evidence_fixture_candidate_review",
                    "final_evidence_selection_policy_review",
                ],
                "ready_action_candidates": [
                    {
                        "case_id": "case_a",
                        "action_type": "primary_evidence_fixture_candidate_review",
                        "action_category": "fixture_candidate_governance",
                        "readiness": "ready_from_valid_decision",
                        "priority_score": 20,
                        "risk_level": "high",
                        "expected_domains": ["data compliance"],
                        "source_decision_status": "completed",
                        "validation_status": "valid",
                        "confirmed_root_causes": [
                            "primary_evidence_gap",
                            "final_evidence_selection_policy",
                        ],
                        "target_areas": ["evidence_fixture_candidate_pool"],
                        "blocked_reason": "",
                        "rationale": "Primary support needs fixture review.",
                        "notes": "Design only.",
                    },
                    {
                        "case_id": "case_a",
                        "action_type": "final_evidence_selection_policy_review",
                        "action_category": "final_evidence_policy",
                        "readiness": "ready_from_valid_decision",
                        "priority_score": 20,
                        "risk_level": "high",
                        "expected_domains": ["data compliance"],
                        "source_decision_status": "completed",
                        "validation_status": "valid",
                        "confirmed_root_causes": [
                            "primary_evidence_gap",
                            "final_evidence_selection_policy",
                        ],
                        "target_areas": ["final_evidence_selection_policy_draft"],
                        "blocked_reason": "",
                        "rationale": "Final evidence policy needs design review.",
                        "notes": "Design only.",
                    },
                ],
            }
        ],
    }


def export_report(status: str = "open") -> dict:
    ready = status == "open"
    return {
        "version": "export-test",
        "scope": "manual review export pipeline dry run",
        "summary": {
            "pipeline_conclusion": "ready_for_governed_action_planning" if ready else "blocked_input_rejections_require_review",
            "gate_status": status,
            "gate_blockers": [] if ready else ["manual_review_required"],
            "dry_run_blockers": [] if ready else ["rejected_import_rows"],
            "input_rows": 1,
            "imported_rows": 1 if ready else 0,
            "rejected_rows": 0 if ready else 1,
            "valid_proposed_records": 1 if ready else 0,
            "invalid_proposed_records": 0,
            "pending_proposed_records": 3,
            "promotion_candidates": 1 if ready else 0,
            "ready_action_candidates": 2 if ready else 0,
            "safe_ai_suggestion_input": False,
        },
    }


class ReadyActionDesignPackTest(unittest.TestCase):
    def test_default_paths_use_legacy_reports_and_docs_markdown_output(self):
        self.assertEqual(
            DEFAULT_PROMOTION_REPORT_PATH,
            legacy_report_path("validated_decision_promotion_dry_run_report.json"),
        )
        self.assertEqual(
            DEFAULT_EXPORT_PIPELINE_DRY_RUN_REPORT_PATH,
            legacy_report_path("manual_review_export_pipeline_dry_run_report.json"),
        )
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("ready_action_design_pack_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/ready_action_design_pack_v0.4.7.9.0.md"))

    def test_real_current_reports_build_five_groups_and_eighteen_design_actions(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.7.9.0")
        self.assertEqual(report["schema_kind"], "governed_ready_action_design_pack")
        self.assertEqual(report["guardrails"], DESIGN_ONLY_GUARDRAILS)
        self.assertEqual(report["planning_gate"]["status"], "open_for_design_review")
        self.assertFalse(report["planning_gate"]["implementation_allowed"])
        self.assertEqual(report["summary"]["status"], "ready_for_design_review")
        self.assertEqual(report["summary"]["promotion_candidates"], 5)
        self.assertEqual(report["summary"]["ready_action_candidates"], 18)
        self.assertEqual(report["summary"]["source_ready_action_candidates"], 18)
        self.assertEqual(report["summary"]["pending_records_excluded"], 31)
        self.assertTrue(report["summary"]["pending_records_are_not_design_tasks"])
        self.assertEqual(
            report["summary"]["action_type_summary"],
            {
                "final_evidence_selection_policy_review": 5,
                "functional_typing_fixture_review": 1,
                "high_risk_manual_grounding_review": 3,
                "primary_evidence_fixture_candidate_review": 5,
                "scenario_registry_core_article_review": 4,
            },
        )
        self.assertEqual(len(report["action_groups"]), 5)
        self.assertEqual(len(report["case_design_matrix"]), 5)
        self.assertEqual(len(report["traceability"]["design_action_ids"]), 18)

        for group in report["action_groups"].values():
            self.assertIn("allowed_next_step", group)
            self.assertIn("prohibited_now", group)
            self.assertIn("acceptance_checks", group)
            for action in group["candidate_actions"]:
                self.assertEqual(action["readiness"], "ready_from_valid_decision")
                self.assertEqual(action["source_decision_status"], "completed")
                self.assertEqual(action["validation_status"], "valid")
                self.assertEqual(action["planning_status"], "design_review_only")

        for node in walk_dicts(report):
            self.assertFalse(FORBIDDEN_OUTPUT_KEYS & set(node.keys()))

    def test_gate_blocked_report_does_not_emit_design_actions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            promotion_path = tmp / "promotion.json"
            export_path = tmp / "export.json"
            write_json(promotion_path, promotion_report())
            write_json(export_path, export_report(status="blocked"))

            report = build_report(promotion_path, export_path)

        self.assertEqual(report["summary"]["status"], "blocked_for_design_review")
        self.assertFalse(report["planning_gate"]["design_planning_allowed"])
        self.assertFalse(report["planning_gate"]["implementation_allowed"])
        self.assertEqual(report["summary"]["ready_action_candidates"], 0)
        self.assertEqual(report["summary"]["excluded_ready_action_candidates"], 2)
        self.assertEqual(report["action_groups"], {})
        self.assertIn("closeout_gate_not_open", report["planning_gate"]["blocked_reasons"])
        self.assertIn("source_gate_not_open_for_design_review", report["excluded_scope"]["excluded_ready_action_candidates"][0]["excluded_reasons"])

    def test_synthetic_ready_report_preserves_traceability_without_authorizing_implementation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            promotion_path = tmp / "promotion.json"
            export_path = tmp / "export.json"
            write_json(promotion_path, promotion_report())
            write_json(export_path, export_report(status="open"))

            report = build_report(promotion_path, export_path)

        self.assertEqual(report["summary"]["status"], "ready_for_design_review")
        self.assertEqual(report["summary"]["ready_action_candidates"], 2)
        self.assertEqual(report["summary"]["pending_records_excluded"], 3)
        self.assertEqual(report["summary"]["action_type_summary"]["primary_evidence_fixture_candidate_review"], 1)
        self.assertEqual(report["summary"]["action_type_summary"]["final_evidence_selection_policy_review"], 1)
        self.assertEqual(report["case_design_matrix"][0]["case_id"], "case_a")
        self.assertEqual(report["case_design_matrix"][0]["ready_action_count"], 2)
        self.assertEqual(report["planning_gate"]["implementation_status"], "not_started")
        self.assertTrue(report["planning_gate"]["implementation_requires_future_explicit_approval"])
        self.assertTrue(all(item["status"] == "passed" for item in report["assertions"]))

    def test_markdown_states_design_pack_boundary(self):
        report = build_report()
        markdown = render_markdown(report)

        self.assertIn("只读设计包", markdown)
        self.assertIn("不是样本修补工具", markdown)
        self.assertIn("31 个 pending records", markdown)
        self.assertIn("不修改 hidden seed", markdown)

    def test_source_has_no_runtime_or_backend_patterns(self):
        source = Path("tools/build_ready_action_design_pack.py").read_text(encoding="utf-8")

        for pattern in PROHIBITED_SOURCE_PATTERNS:
            self.assertNotIn(pattern, source)


if __name__ == "__main__":
    unittest.main()
