import unittest

from tools.run_rag_eval import (
    apply_report_profile,
    build_contribution_labels,
    build_contribution_summary,
    build_compact_debug_summary,
    build_quality_signal_diagnostics,
    build_risk_level_mismatch_summary,
    build_retrieval_diagnostics,
    build_stability_summary,
    check_expected_risk_level,
    compact_case_report,
    evidence_ref,
)


class RagEvalDiagnosticsTest(unittest.TestCase):
    def test_diagnostics_marks_rerank_miss_when_candidate_reaches_rerank_input(self):
        case = {
            "expected_evidence": [{"source": "Law A", "article_no": 7}],
        }
        result = {
            "debug_info": {
                "dense_candidates": [],
                "sparse_candidates": [{"source": "Law A", "article_no": 7}],
                "union_candidates": [{"source": "Law A", "article_no": 7}],
                "anchor_candidates": [],
                "rerank_input_candidates": [{"source": "Law A", "article_no": 7}],
            },
            "evidence_chain": [{"source": "Law B", "article_no": 1}],
        }

        diagnostics = build_retrieval_diagnostics(case, result)

        self.assertEqual(diagnostics["failure_stage"], "RERANK_MISS")
        self.assertTrue(diagnostics["layers"]["rerank_input"]["satisfied"])
        self.assertFalse(diagnostics["layers"]["final"]["satisfied"])

    def test_diagnostics_marks_retrieval_miss_when_no_layer_matches(self):
        case = {
            "expected_evidence": [{"source": "Law A", "article_no": 7}],
        }
        result = {
            "debug_info": {
                "dense_candidates": [{"source": "Law B", "article_no": 1}],
                "sparse_candidates": [],
                "union_candidates": [{"source": "Law B", "article_no": 1}],
                "anchor_candidates": [],
                "rerank_input_candidates": [{"source": "Law B", "article_no": 1}],
            },
            "evidence_chain": [{"source": "Law B", "article_no": 1}],
        }

        diagnostics = build_retrieval_diagnostics(case, result)

        self.assertEqual(diagnostics["failure_stage"], "RETRIEVAL_MISS")

    def test_contribution_labels_mark_anchor_and_output_rules(self):
        diagnostics = {
            "layers": {
                "union": {"satisfied": False},
                "anchor": {"satisfied": True},
                "rerank_input": {"satisfied": True},
                "final": {"satisfied": True},
            }
        }
        debug_info = {
            "output_contributions": {
                "term_preservation_rules": [{"required_terms": ["公开透明"]}],
                "risk_supplement_rules": [{"index": 1}],
            }
        }

        labels = build_contribution_labels(True, diagnostics, debug_info)

        self.assertIn("ANCHOR_PASS", labels)
        self.assertIn("TERM_PRESERVATION_PASS", labels)
        self.assertIn("RISK_SUPPLEMENT_PASS", labels)

    def test_contribution_labels_mark_pure_llm_pass(self):
        diagnostics = {
            "layers": {
                "union": {"satisfied": True},
                "anchor": {"satisfied": False},
                "rerank_input": {"satisfied": True},
                "final": {"satisfied": True},
            }
        }

        labels = build_contribution_labels(True, diagnostics, {"output_contributions": {}})

        self.assertEqual(labels, ["PURE_LLM_PASS"])

    def test_contribution_labels_skip_failed_case(self):
        labels = build_contribution_labels(
            False,
            {"layers": {"final": {"satisfied": False}}},
            {"output_contributions": {"term_preservation_rules": [{"required_terms": ["公开透明"]}]}},
        )

        self.assertEqual(labels, [])

    def test_contribution_summary_counts_multilabel_reports(self):
        summary = build_contribution_summary([
            {"passed": True, "contribution_labels": ["PURE_LLM_PASS"]},
            {"passed": True, "contribution_labels": ["ANCHOR_PASS", "RISK_SUPPLEMENT_PASS"]},
            {"passed": False, "contribution_labels": ["TERM_PRESERVATION_PASS"]},
        ])

        self.assertEqual(summary["pure_llm_passed"], 1)
        self.assertEqual(summary["anchor_assisted_passed"], 1)
        self.assertEqual(summary["risk_supplement_assisted_passed"], 1)
        self.assertEqual(summary["term_preservation_assisted_passed"], 0)
        self.assertEqual(summary["output_rule_assisted_passed"], 1)

    def test_expected_risk_level_requires_exact_match(self):
        over_risk = check_expected_risk_level(
            {"expected_risk_level": "medium"},
            {"risk_level": "high"},
            enabled=True,
        )
        exact = check_expected_risk_level(
            {"expected_risk_level": "medium"},
            {"risk_level": "medium"},
            enabled=True,
        )
        under_risk = check_expected_risk_level(
            {"expected_risk_level": "high"},
            {"risk_level": "medium"},
            enabled=True,
        )

        self.assertFalse(over_risk.passed)
        self.assertEqual(over_risk.details["mismatch_type"], "over_risk")
        self.assertIn("policy=exact", over_risk.message)
        self.assertTrue(exact.passed)
        self.assertEqual(exact.details["mismatch_type"], "exact_match")
        self.assertFalse(under_risk.passed)
        self.assertEqual(under_risk.details["mismatch_type"], "under_risk")

    def test_risk_level_mismatch_summary_counts_exact_policy_results(self):
        reports = [
            {
                "id": "case_over",
                "checks": [
                    {
                        "name": "expected_risk_level",
                        "passed": False,
                        "details": {
                            "policy": "exact",
                            "actual_level": "high",
                            "expected_level": "medium",
                            "mismatch_type": "over_risk",
                        },
                    }
                ],
            },
            {
                "id": "case_exact",
                "checks": [
                    {
                        "name": "expected_risk_level",
                        "passed": True,
                        "details": {
                            "policy": "exact",
                            "actual_level": "low",
                            "expected_level": "low",
                            "mismatch_type": "exact_match",
                        },
                    }
                ],
            },
        ]

        summary = build_risk_level_mismatch_summary(reports)

        self.assertEqual(summary["checked_count"], 2)
        self.assertEqual(summary["mismatch_counts"], {"over_risk": 1, "exact_match": 1})
        self.assertEqual(summary["mismatch_cases"][0]["id"], "case_over")

    def test_stability_summary_detects_unstable_cases(self):
        run_summaries = [
            {
                "total": 1,
                "passed": 1,
                "reports": [
                    {
                        "id": "case_a",
                        "passed": True,
                        "retrieval_failure_stage": "PASS",
                        "checks": [{"name": "expected_answer_keywords", "passed": True}],
                        "contribution_labels": ["PURE_LLM_PASS"],
                    }
                ],
            },
            {
                "total": 1,
                "passed": 0,
                "reports": [
                    {
                        "id": "case_a",
                        "passed": False,
                        "retrieval_failure_stage": "PASS",
                        "checks": [{"name": "expected_answer_keywords", "passed": False}],
                        "contribution_labels": ["TERM_PRESERVATION_PASS"],
                    }
                ],
            },
        ]

        stability = build_stability_summary(run_summaries)

        self.assertFalse(stability["all_runs_full_pass"])
        self.assertEqual(stability["unstable_cases"][0]["id"], "case_a")

    def test_compact_debug_summary_keeps_counts_without_payloads(self):
        debug_info = {
            "dense_candidates": [{"content": "dense"}],
            "sparse_candidates": [{"content": "sparse"}, {"content": "sparse2"}],
            "union_candidates": [],
            "anchor_candidates": [{"content": "anchor"}],
            "rerank_input_candidates": [{"content": "rerank"}],
            "rerank_full_score_order": [{"content": "full"} for _ in range(3)],
            "final_evidence_selection_trace": {
                "score_epsilon": 0.1,
                "full_rerank_count": 15,
                "selected_count": 3,
                "not_selected_count": 12,
                "selected": [{"large": "payload"}],
            },
            "output_contributions": {
                "term_preservation_rules": [{"payload": "large"}],
                "plain_flag": True,
            },
            "rerank_dense_fallback": True,
        }

        summary = build_compact_debug_summary(debug_info)

        self.assertEqual(summary["candidate_counts"]["sparse"], 2)
        self.assertEqual(summary["candidate_counts"]["rerank_full_score_order"], 3)
        self.assertEqual(summary["final_evidence_selection_trace"]["selected_count"], 3)
        self.assertNotIn("selected", summary["final_evidence_selection_trace"])
        self.assertEqual(summary["output_contribution_counts"]["term_preservation_rules"], 1)
        self.assertTrue(summary["rerank_dense_fallback"])

    def test_compact_case_report_removes_full_debug_info(self):
        report = {
            "id": "case_a",
            "passed": True,
            "checks": [],
            "evidence": [],
            "quality_signal_diagnostics": {"detected_issues": []},
            "contribution_trace": {"risk_supplement_rules": [{"large": "payload"}]},
            "debug_info": {
                "dense_candidates": [{"content": "x" * 1000}],
                "final_evidence_selection_trace": {"selected_count": 3},
            },
        }

        compact = compact_case_report(report)

        self.assertNotIn("debug_info", compact)
        self.assertNotIn("contribution_trace", compact)
        self.assertEqual(compact["id"], "case_a")
        self.assertEqual(compact["quality_signal_diagnostics"], {"detected_issues": []})
        self.assertEqual(compact["debug_info_summary"]["candidate_counts"]["dense"], 1)
        self.assertEqual(compact["contribution_trace_summary"]["risk_supplement_rules"], 1)

    def test_apply_report_profile_compacts_single_and_repeat_reports(self):
        case_report = {
            "id": "case_a",
            "passed": True,
            "checks": [],
            "evidence": [],
            "quality_signal_diagnostics": {},
            "debug_info": {"dense_candidates": [{"content": "x"}]},
        }
        single_summary = {"total": 1, "passed": 1, "reports": [case_report]}
        repeat_summary = {
            "repeat": 1,
            "stability_summary": {"pass_counts": [1]},
            "runs": [{"total": 1, "passed": 1, "reports": [case_report]}],
        }

        compact_single = apply_report_profile(single_summary, "compact")
        compact_repeat = apply_report_profile(repeat_summary, "compact")

        self.assertEqual(compact_single["report_profile"], "compact")
        self.assertNotIn("debug_info", compact_single["reports"][0])
        self.assertEqual(compact_repeat["report_profile"], "compact")
        self.assertNotIn("debug_info", compact_repeat["runs"][0]["reports"][0])
        self.assertIsNot(compact_single, single_summary)

    def test_evidence_ref_maps_known_source_to_generic_ref(self):
        item = {
            "source": "中华人民共和国个人信息保护法",
            "law_name": "中华人民共和国个人信息保护法",
            "article_no": 24,
        }

        self.assertEqual(evidence_ref(item), "pipl::article_24")

    def test_quality_signal_detects_known_bad_and_domain_pollution(self):
        case = {
            "expected_statutes": [
                {
                    "ref": "pipl::article_24",
                    "functional_type": "operative_rule",
                    "supports": ["automated_decision"],
                }
            ],
            "known_bad_evidence": [{"ref": "civil_code::article_610", "reason": "wrong domain"}],
            "contaminating_domains": ["civil_code"],
        }
        result = {
            "evidence_chain": [
                {
                    "source": "中华人民共和国民法典",
                    "law_name": "中华人民共和国民法典",
                    "article_no": 610,
                }
            ],
            "debug_info": {},
        }

        diagnostics = build_quality_signal_diagnostics(case, result)

        self.assertEqual(diagnostics["status"], "review_recommended")
        self.assertIn("known_bad_evidence_leakage", diagnostics["detected_issues"])
        self.assertIn("jurisdiction_or_domain_pollution", diagnostics["detected_issues"])
        self.assertIn("major_issue_evidence_gap", diagnostics["detected_issues"])

    def test_quality_signal_detects_definition_only_substitution(self):
        case = {
            "expected_statutes": [
                {"ref": "pipl::article_28", "functional_type": "definition", "supports": ["sensitive_info"]},
                {"ref": "pipl::article_29", "functional_type": "operative_rule", "supports": ["separate_consent"]},
            ],
        }
        result = {
            "evidence_chain": [
                {
                    "source": "中华人民共和国个人信息保护法",
                    "law_name": "中华人民共和国个人信息保护法",
                    "article_no": 28,
                }
            ],
            "debug_info": {},
        }

        diagnostics = build_quality_signal_diagnostics(case, result)

        self.assertIn("definition_substitutes_operative_rule", diagnostics["detected_issues"])
        self.assertEqual(diagnostics["matched_definition_refs"], ["pipl::article_28"])
        self.assertEqual(diagnostics["matched_operative_refs"], [])

    def _pipl_item(self, article_no, score=None):
        item = {
            "source": "PIPL alias",
            "law_name": "\u4e2d\u534e\u4eba\u6c11\u5171\u548c\u56fd\u4e2a\u4eba\u4fe1\u606f\u4fdd\u62a4\u6cd5",
            "article_no": article_no,
        }
        if score is not None:
            item["score"] = score
        return item

    def _cybersecurity_item(self, article_no, score=None):
        item = {
            "source": "Cybersecurity Law alias",
            "law_name": "\u4e2d\u534e\u4eba\u6c11\u5171\u548c\u56fd\u7f51\u7edc\u5b89\u5168\u6cd5",
            "article_no": article_no,
        }
        if score is not None:
            item["score"] = score
        return item

    def test_quality_signal_detects_same_bucket_selection_order_risk(self):
        case = {
            "expected_statutes": [
                {"ref": "pipl::article_48", "functional_type": "operative_rule"},
            ],
        }
        result = {
            "evidence_chain": [self._pipl_item(24)],
            "debug_info": {
                "final_evidence_selection_trace": {
                    "score_epsilon": 0.1,
                    "selected": [self._pipl_item(24, 0.931)],
                    "not_selected": [self._pipl_item(48, 0.969)],
                }
            },
        }

        diagnostics = build_quality_signal_diagnostics(case, result)

        self.assertIn("same_bucket_selection_order_risk", diagnostics["detected_issues"])
        self.assertEqual(diagnostics["score_order_risks"][0]["not_selected_ref"], "pipl::article_48")
        self.assertEqual(diagnostics["score_order_observations"][0]["not_selected_ref"], "pipl::article_48")

    def test_quality_signal_suppresses_same_bucket_when_expected_evidence_is_satisfied(self):
        case = {"expected_evidence": [self._pipl_item(24)]}
        result = {
            "evidence_chain": [self._pipl_item(24)],
            "debug_info": {
                "final_evidence_selection_trace": {
                    "score_epsilon": 0.1,
                    "selected": [self._pipl_item(24, 0.931)],
                    "not_selected": [self._pipl_item(48, 0.969)],
                }
            },
        }

        diagnostics = build_quality_signal_diagnostics(case, result)

        self.assertNotIn("same_bucket_selection_order_risk", diagnostics["detected_issues"])
        self.assertEqual(diagnostics["score_order_risks"], [])
        self.assertEqual(diagnostics["score_order_observations"][0]["not_selected_ref"], "pipl::article_48")

    def test_quality_signal_suppresses_same_ref_same_bucket_observation(self):
        case = {
            "expected_evidence": [self._pipl_item(24), self._pipl_item(48)],
            "expected_evidence_min_match": 1,
        }
        result = {
            "evidence_chain": [self._pipl_item(24)],
            "debug_info": {
                "final_evidence_selection_trace": {
                    "score_epsilon": 0.1,
                    "selected": [self._pipl_item(24, 0.931)],
                    "not_selected": [self._pipl_item(24, 0.969)],
                }
            },
        }

        diagnostics = build_quality_signal_diagnostics(case, result)

        self.assertEqual(diagnostics["score_order_risks"], [])
        self.assertEqual(diagnostics["score_order_observations"][0]["not_selected_ref"], "pipl::article_24")

    def test_quality_signal_suppresses_noncritical_cross_domain_same_bucket_candidate(self):
        case = {"expected_evidence": [self._pipl_item(24)]}
        result = {
            "evidence_chain": [self._pipl_item(24)],
            "debug_info": {
                "final_evidence_selection_trace": {
                    "score_epsilon": 0.1,
                    "selected": [self._pipl_item(24, 0.931)],
                    "not_selected": [self._cybersecurity_item(20, 0.969)],
                }
            },
        }

        diagnostics = build_quality_signal_diagnostics(case, result)

        self.assertEqual(diagnostics["score_order_risks"], [])
        self.assertNotIn("same_bucket_selection_order_risk", diagnostics["detected_issues"])

    def test_quality_signal_is_not_configured_without_metadata_or_order_risk(self):
        diagnostics = build_quality_signal_diagnostics({"id": "plain"}, {"evidence_chain": [], "debug_info": {}})

        self.assertEqual(diagnostics["status"], "not_configured")
        self.assertEqual(diagnostics["detected_issues"], [])


if __name__ == "__main__":
    unittest.main()
