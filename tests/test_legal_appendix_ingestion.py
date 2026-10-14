import tempfile
import unittest
from pathlib import Path

from src.rag.ingestion import load_txt


class LegalAppendixIngestionTest(unittest.TestCase):
    def test_attached_table_is_not_merged_into_last_article(self):
        text = """第一条 正文内容。

第二条 最后一条正文。

附表一：

环境保护税税目税额表

税目 计税单位 税额
大气污染物 每污染当量 1.2元

附表二：

应税污染物和当量值表

污染物 污染当量值
总汞 0.0005
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "示例法.txt"
            path.write_text(text, encoding="utf-8")
            docs = load_txt(str(path), source_name="示例法", category="财税")

        appendix_docs = [doc for doc in docs if doc.metadata.get("block_type") == "appendix_table"]
        last_article_docs = [doc for doc in docs if doc.metadata.get("article_no") == 2]

        self.assertEqual({doc.metadata["appendix"] for doc in appendix_docs}, {"附表一", "附表二"})
        self.assertTrue(all(doc.metadata["article_no"] is None for doc in appendix_docs))
        self.assertTrue(all("附表" in doc.metadata["citation"] for doc in appendix_docs))
        self.assertTrue(all("环境保护税" not in doc.page_content for doc in last_article_docs))
        self.assertTrue(any("大气污染物" in doc.page_content for doc in appendix_docs))

    def test_compact_articles_are_split_without_blank_lines(self):
        text = """第一条 第一条内容。
第二条 第二条内容。
附表一：
示例表
字段 值
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "紧凑示例法.txt"
            path.write_text(text, encoding="utf-8")
            docs = load_txt(str(path), source_name="紧凑示例法", category="财税")

        article_numbers = {doc.metadata.get("article_no") for doc in docs if doc.metadata.get("block_type") == "article"}
        self.assertEqual(article_numbers, {1, 2})
        self.assertTrue(any(doc.metadata.get("appendix") == "附表一" for doc in docs))


if __name__ == "__main__":
    unittest.main()
