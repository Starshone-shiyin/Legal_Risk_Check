import tempfile
import unittest
from pathlib import Path

from tools.build_ready_action_routing_dry_run import (
    ROUTE_ANCHOR,
    ROUTE_FINAL_SELECTION,
    ROUTE_FIXTURE,
    ROUTE_RETRIEVAL_INPUT,
    ROUTE_SCENARIO_CORE,
    build_report,
    route_for_action,
)


class ReadyActionRoutingDryRunTest(unittest.TestCase):
    def test_route_for_action_maps_metadata_review(self):
        route = route_for_action("metadata_chunking_or_query_coverage_review")

        self.assertEqual(route, ROUTE_RETRIEVAL_INPUT)

    def test_future_series_routes_are_not_swapped(self):
        self.assertEqual(ROUTE_FINAL_SELECTION, "v0.4.8.x_final_evidence_selection_policy_design")
        self.assertEqual(ROUTE_RETRIEVAL_INPUT, "v0.4.9.x_retrieval_input_quality_governance")
        self.assertNotIn("v0.4.8.x", ROUTE_RETRIEVAL_INPUT)
        self.assertNotIn("v0.4.9.x", ROUTE_FINAL_SELECTION)
        self.assertNotIn("v0.4.", ROUTE_SCENARIO_CORE)
        self.assertNotIn("v0.4.", ROUTE_FIXTURE)
        self.assertNotIn("v0.4.", ROUTE_ANCHOR)

    def test_route_for_action_maps_all_design_route_families(self):
        self.assertEqual(
            route_for_action("final_evidence_selection_policy_review"),
            ROUTE_FINAL_SELECTION,
        )
        self.assertEqual(
            route_for_action("metadata_chunking_or_query_coverage_review"),
            ROUTE_RETRIEVAL_INPUT,
        )
        self.assertEqual(
            route_for_action("scenario_registry_core_article_review"),
            ROUTE_SCENARIO_CORE,
        )
        self.assertEqual(
            route_for_action("primary_evidence_fixture_candidate_review"),
            ROUTE_FIXTURE,
        )
        self.assertEqual(
            route_for_action("anchor_dependency_governance_review"),
            ROUTE_ANCHOR,
        )

    def test_only_ready_candidates_are_routed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            actions = tmp / "actions.json"
            progress = tmp / "progress.json"
            actions.write_text(
                __import__("json").dumps(
                    {
                        "version": "0.4.7.5.2",
                        "action_candidates": [
                            {
                                "case_id": "case_ready",
                                "action_type": "metadata_chunking_or_query_coverage_review",
                                "readiness": "ready_from_valid_decision",
                                "priority_score": 10,
                                "expected_domains": ["数据合规"],
                            },
                            {
                                "case_id": "case_blocked",
                                "action_type": "anchor_dependency_governance_review",
                                "readiness": "blocked_pending_manual_review",
                                "priority_score": 9,
                                "expected_domains": ["数据合规"],
                            },
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            progress.write_text(
                __import__("json").dumps(
                    {"version": "0.4.7.6.2", "summary": {"completed_cases": 1, "pending_cases": 1}},
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            report = build_report(actions, progress)

        self.assertEqual(report["version"], "0.4.7.6.3")
        self.assertEqual(report["summary"]["ready_routes"], 1)
        self.assertEqual(report["summary"]["blocked_candidates"], 1)
        self.assertEqual(report["ready_routes"][0]["route"], ROUTE_RETRIEVAL_INPUT)


if __name__ == "__main__":
    unittest.main()
