import unittest

from src.rag.evidence_sufficiency import assess_evidence_sufficiency, summarize_evidence_sufficiency


def _local_law_evidence(article_no: int, source: str = "\u6c11\u6cd5\u5178") -> dict:
    return {
        "type": "article",
        "source": source,
        "law_name": source,
        "document_type": "\u6cd5\u5f8b\u6cd5\u89c4",
        "law_level": "\u6cd5\u5f8b",
        "authority_level": "\u5f53\u524d\u6709\u6548",
        "article_no": article_no,
        "citation": f"[{source}\u7b2c{article_no}\u6761]",
    }


class EvidenceSufficiencyTest(unittest.TestCase):
    def test_complete_local_legal_evidence_passes_the_gate(self):
        report = assess_evidence_sufficiency(
            [_local_law_evidence(509), _local_law_evidence(577), _local_law_evidence(584)],
            question="\u5408\u540c\u5c65\u884c\u4e2d\u7684\u9644\u968f\u4e49\u52a1\u600e\u4e48\u89c4\u5b9a\uff1f",
            requested_k=3,
        )
        self.assertEqual(report["status"], "sufficient")
        self.assertEqual(report["recommended_route"], "answer_with_evidence")
        self.assertEqual(report["local_legal_evidence_count"], 3)
        self.assertEqual(report["external_web_evidence_count"], 0)
        self.assertGreaterEqual(report["score"], 0.78)

    def test_web_only_legal_evidence_requires_supplement_not_legal_conclusion(self):
        report = assess_evidence_sufficiency(
            [{
                "type": "web_result",
                "source": "https://www.gov.cn/example",
                "authority_level": "official",
                "citation": "[web source]",
            }],
            question="\u67d0\u9879\u6cd5\u5f8b\u5982\u4f55\u89c4\u5b9a\uff1f",
            requested_k=3,
        )
        self.assertEqual(report["status"], "insufficient")
        self.assertEqual(report["recommended_route"], "web_supplement")
        self.assertEqual(report["local_legal_evidence_count"], 0)
        self.assertEqual(report["external_web_evidence_count"], 1)

    def test_regulated_data_topics_are_treated_as_legal_questions(self):
        report = assess_evidence_sufficiency(
            [_local_law_evidence(28, source="\u4e2a\u4eba\u4fe1\u606f\u4fdd\u62a4\u6cd5")],
            question="\u4ec0\u4e48\u662f\u654f\u611f\u4e2a\u4eba\u4fe1\u606f\uff1f",
            requested_k=1,
        )
        self.assertTrue(report["is_legal_question"])
        self.assertEqual(report["recommended_route"], "answer_with_evidence")

    def test_non_legal_external_fact_can_be_answered_with_authoritative_web_evidence(self):
        report = assess_evidence_sufficiency(
            [{
                "type": "web_result",
                "source": "https://www.gov.cn/example",
                "authority_level": "official",
                "citation": "[web source]",
            }],
            question="\u67e5\u8be2\u67d0\u516c\u544a\u7684\u53d1\u5e03\u65f6\u95f4",
            requested_k=1,
        )
        self.assertEqual(report["status"], "sufficient")
        self.assertEqual(report["recommended_route"], "answer_with_evidence")

    def test_summary_keeps_routing_rates_separate(self):
        summary = summarize_evidence_sufficiency([
            {"score": 1.0, "status": "sufficient", "recommended_route": "answer_with_evidence", "local_legal_evidence_count": 2},
            {"score": 0.3, "status": "insufficient", "recommended_route": "web_supplement", "local_legal_evidence_count": 0},
            {"score": 0.6, "status": "review", "recommended_route": "human_review", "local_legal_evidence_count": 1},
        ])
        self.assertEqual(summary["case_count"], 3)
        self.assertAlmostEqual(summary["sufficient_rate"], 1 / 3, places=6)
        self.assertAlmostEqual(summary["web_supplement_rate"], 1 / 3, places=6)
        self.assertAlmostEqual(summary["human_review_rate"], 1 / 3, places=6)
        self.assertAlmostEqual(summary["local_primary_law_coverage"], 2 / 3, places=6)


if __name__ == "__main__":
    unittest.main()
