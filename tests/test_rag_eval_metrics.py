import unittest

from src.rag.eval_metrics import calculate_case_metrics, summarize_case_metrics


class RagEvalMetricsTest(unittest.TestCase):
    def test_case_metrics_match_expected_articles(self):
        evidence = [
            {"source": "法典", "article_no": 2},
            {"source": "法典", "article_no": 1},
            {"source": "公司法", "article_no": 3},
        ]
        expected = [
            {"source": "法典", "article_no": 1},
            {"source": "公司法", "article_no": 3},
        ]
        metrics = calculate_case_metrics(evidence, expected, 3)
        self.assertEqual(metrics["matched_evidence"], 2)
        self.assertEqual(metrics["evidence_recall_at_k"], 1.0)
        self.assertEqual(metrics["mrr_at_k"], 0.5)
        self.assertGreater(metrics["ndcg_at_k"], 0.6)
        self.assertEqual(metrics["multi_source_coverage"], 1.0)

    def test_summary_includes_latency_percentiles(self):
        summary = summarize_case_metrics([
            {"evidence_recall_at_k": 1.0, "mrr_at_k": 1.0, "ndcg_at_k": 1.0, "multi_source_coverage": 1.0, "retrieval_elapsed_ms": 10},
            {"evidence_recall_at_k": 0.0, "mrr_at_k": 0.0, "ndcg_at_k": 0.0, "multi_source_coverage": 0.0, "retrieval_elapsed_ms": 20},
        ])
        self.assertEqual(summary["case_count"], 2)
        self.assertEqual(summary["retrieval_time_p50_ms"], 15)
        self.assertEqual(summary["retrieval_time_p95_ms"], 20)

    def test_versioned_standard_source_matches_canonical_name(self):
        metrics = calculate_case_metrics(
            [{"source": "信息安全技术 个人信息安全规范 GB_T_35273_2020", "section_no": "5.2"}],
            [{"source": "信息安全技术 个人信息安全规范", "section_no": "5.2"}],
            3,
        )
        self.assertEqual(metrics["evidence_recall_at_k"], 1.0)

    def test_duplicate_chunks_for_one_article_do_not_inflate_ndcg(self):
        metrics = calculate_case_metrics(
            [
                {"source": "数据安全法", "article_no": 21, "block_type": "article"},
                {"source": "数据安全法", "article_no": 21, "block_type": "paragraph"},
                {"source": "数据安全法", "article_no": 21, "block_type": "paragraph"},
            ],
            [{"source": "数据安全法", "article_no": 21}],
            3,
        )
        self.assertEqual(metrics["matched_evidence"], 1)
        self.assertEqual(metrics["ndcg_at_k"], 1.0)


if __name__ == "__main__":
    unittest.main()
