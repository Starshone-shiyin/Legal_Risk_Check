import tempfile
import unittest
from pathlib import Path

from tools.check_evidence_coverage import (
    DEFAULT_HIDDEN_REPORT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_RAG_REPORT_PATH,
    ISSUE_ANCHOR_DEPENDENT_COVERAGE,
    ISSUE_FINAL_PRIMARY_GAP,
    ISSUE_FUNCTIONAL_TYPE_GAP,
    ISSUE_LAYER_COVERAGE_REGRESSION,
    ISSUE_OPERATIVE_SUPPORT_GAP,
    ISSUE_SCENARIO_CORE_GAP,
    build_evidence_enrichment_index,
    build_coverage_report,
    evaluate_case,
)


def layer(matched, missing, required_count=1):
    return {
        "matched_count": len(matched),
        "expected_count": len(matched) + len(missing),
        "required_count": required_count,
        "satisfied": len(matched) >= required_count,
        "matched": matched,
        "missing": missing,
    }


class EvidenceCoverageTest(unittest.TestCase):
    def test_default_paths_remain_legacy_tests_reports(self):
        self.assertEqual(DEFAULT_RAG_REPORT_PATH, Path("tests/rag_eval_report.json"))
        self.assertEqual(DEFAULT_HIDDEN_REPORT_PATH, Path("tests/hidden_eval_report.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, Path("tests/evidence_coverage_report.json"))

    def test_final_evidence_gap_is_reported(self):
        expected_a = {"source": "示例法", "article_no": 1}
        expected_b = {"source": "示例法", "article_no": 2}
        report = {
            "id": "case_gap",
            "evidence": [expected_a],
            "retrieval_diagnostics": {
                "layers": {
                    "dense": layer([], [expected_a, expected_b]),
                    "sparse": layer([expected_a], [expected_b]),
                    "union": layer([expected_a], [expected_b]),
                    "anchor": layer([expected_a, expected_b], []),
                    "rerank_input": layer([expected_a, expected_b], []),
                    "final": layer([expected_a], [expected_b]),
                }
            },
        }

        result = evaluate_case(report)

        self.assertEqual(result["final_evidence_coverage"]["coverage_ratio"], 0.5)
        self.assertIn(ISSUE_FINAL_PRIMARY_GAP, result["detected_issues"])
        self.assertIn(ISSUE_ANCHOR_DEPENDENT_COVERAGE, result["detected_issues"])
        self.assertIn(ISSUE_LAYER_COVERAGE_REGRESSION, result["detected_issues"])

    def test_scenario_core_gap_is_reported_without_case_specific_logic(self):
        core_a = {"source": "示例法", "article_no": 10}
        core_b = {"source": "示例法", "article_no": 11}
        report = {
            "id": "case_core",
            "evidence": [core_a],
            "retrieval_diagnostics": {
                "layers": {
                    name: layer([core_a], [core_b])
                    for name in ("dense", "sparse", "union", "anchor", "rerank_input", "final")
                }
            },
        }
        scenario = {"domain": "示例领域", "core_articles": [core_a, core_b]}

        result = evaluate_case(report, scenario)

        self.assertEqual(result["scenario_core_coverage"]["coverage_ratio"], 0.5)
        self.assertIn(ISSUE_SCENARIO_CORE_GAP, result["detected_issues"])
        self.assertEqual(result["expected_domains"], ["示例领域"])

    def test_functional_type_gap_uses_generic_classifier(self):
        expected = {"source": "示例法", "article_no": 1}
        evidence = {"source": "示例法", "article_no": 1, "content": "背景叙述文本。"}
        report = {
            "id": "case_functional_gap",
            "evidence": [evidence],
            "retrieval_diagnostics": {
                "layers": {
                    name: layer([expected], [])
                    for name in ("dense", "sparse", "union", "anchor", "rerank_input", "final")
                }
            },
        }

        result = evaluate_case(report)

        self.assertIn(ISSUE_OPERATIVE_SUPPORT_GAP, result["detected_issues"])
        self.assertIn(ISSUE_FUNCTIONAL_TYPE_GAP, result["detected_issues"])

    def test_manifest_enrichment_adds_preview_and_functional_type(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            law_file = tmp / "law.txt"
            law_file.write_text(
                "《示例法》\n\n第一条 数据处理者应当采取必要措施保护数据安全。\n",
                encoding="utf-8",
            )
            manifest = tmp / "manifest.json"
            config = tmp / "types.json"
            manifest.write_text(
                __import__("json").dumps(
                    {
                        "documents": [
                            {
                                "source": "示例法",
                                "file_path": str(law_file),
                                "document_type": "法律法规",
                                "category": "示例领域",
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            config.write_text(
                __import__("json").dumps(
                    {
                        "version": "test",
                        "functional_types": [{"id": "operative_rule"}],
                        "operative_support_types": ["operative_rule"],
                        "rules": [
                            {
                                "id": "must_rule",
                                "functional_type": "operative_rule",
                                "priority": 10,
                                "confidence": "rule_high",
                                "contains": ["应当"],
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            index, summary = build_evidence_enrichment_index(manifest, config)
            report = {
                "id": "case_enriched",
                "evidence": [{"source": "示例法", "article_no": 1}],
                "retrieval_diagnostics": {
                    "layers": {
                        name: layer([{"source": "示例法", "article_no": 1}], [])
                        for name in ("dense", "sparse", "union", "anchor", "rerank_input", "final")
                    }
                },
            }
            result = evaluate_case(report, enrichment_index=index)

        self.assertTrue(summary["indexed_keys"])
        self.assertTrue(result["functional_type_coverage"]["evaluable"])
        self.assertTrue(result["functional_type_coverage"]["has_operative_support"])
        self.assertEqual(result["enrichment_coverage"]["matched_ratio"], 1.0)
        self.assertEqual(result["final_evidence"][0]["functional_type"], "operative_rule")
        self.assertIn("应当采取必要措施", result["final_evidence"][0]["content_preview"])

    def test_repository_report_builds_and_skips_missing_hidden_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            rag_report = tmp / "rag.json"
            hidden_report = tmp / "missing_hidden.json"
            scenario_registry = tmp / "scenario.json"
            output_case = {
                "id": "repo_case",
                "evidence": [{"source": "示例法", "article_no": 1}],
                "retrieval_diagnostics": {
                    "layers": {
                        name: layer([{"source": "示例法", "article_no": 1}], [])
                        for name in ("dense", "sparse", "union", "anchor", "rerank_input", "final")
                    }
                },
            }
            rag_report.write_text(
                '{"reports":[' + __import__("json").dumps(output_case, ensure_ascii=False) + "]}",
                encoding="utf-8",
            )
            scenario_registry.write_text('{"scenarios":[]}', encoding="utf-8")

            report = build_coverage_report(
                rag_report,
                hidden_report,
                scenario_registry,
                knowledge_manifest_path=None,
            )

        self.assertEqual(report["version"], "0.4.7.4.1")
        self.assertEqual(report["summary"]["total_cases"], 1)
        self.assertEqual(report["inputs"]["skipped_inputs"], [str(hidden_report)])


if __name__ == "__main__":
    unittest.main()
