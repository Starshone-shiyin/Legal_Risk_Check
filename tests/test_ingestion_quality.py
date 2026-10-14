import unittest

from langchain_core.documents import Document

from src.rag.ingestion import assign_stable_chunk_ids
from tools.check_ingestion_quality import anchor_exists, chinese_ratio, summarize_docs


class IngestionQualityTest(unittest.TestCase):
    def test_anchor_exists_matches_article_and_section(self):
        docs = [
            Document(page_content="第五条 示例", metadata={"article_no": 5}),
            Document(page_content="3.1 示例", metadata={"section_no": "3.1"}),
        ]

        self.assertTrue(anchor_exists({"article_no": 5}, docs))
        self.assertTrue(anchor_exists({"section_no": "3.1"}, docs))
        self.assertFalse(anchor_exists({"article_no": 99}, docs))

    def test_summarize_docs_counts_articles_sections_and_citations(self):
        docs = [
            Document(page_content="第五条 示例", metadata={"type": "article", "block_type": "article", "article_no": 5, "citation": "[法第五条]"}),
            Document(page_content="3.1 示例", metadata={"type": "article", "block_type": "standard_section", "section_no": "3.1", "citation": "[标准3.1]"}),
        ]

        summary = summarize_docs(docs)

        self.assertEqual(summary["document_count"], 2)
        self.assertEqual(summary["article_count"], 1)
        self.assertEqual(summary["standard_section_count"], 1)
        self.assertEqual(summary["citation_count"], 2)

    def test_chinese_ratio_detects_readable_text(self):
        self.assertGreater(chinese_ratio("中华人民共和国个人信息保护法"), 0.8)
        self.assertLess(chinese_ratio("abc 123 !!!"), 0.1)

    def test_assign_stable_chunk_ids_is_deterministic(self):
        docs_a = [
            Document(page_content="example", metadata={"source": "Law A", "citation": "[Law A 1]", "block_type": "article"}),
        ]
        docs_b = [
            Document(page_content="example", metadata={"source": "Law A", "citation": "[Law A 1]", "block_type": "article"}),
        ]

        assign_stable_chunk_ids(docs_a)
        assign_stable_chunk_ids(docs_b)

        self.assertEqual(docs_a[0].metadata["chunk_id"], docs_b[0].metadata["chunk_id"])
        self.assertEqual(docs_a[0].metadata["qdrant_point_id"], docs_b[0].metadata["qdrant_point_id"])


if __name__ == "__main__":
    unittest.main()
