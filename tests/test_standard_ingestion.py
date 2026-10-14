import unittest
from pathlib import Path

from src.rag.ingestion import load_txt


class StandardIngestionTest(unittest.TestCase):
    def test_numbered_standard_sections_are_ingested_as_citable_blocks(self):
        path = Path("tests/fixtures/standard_sample.txt")
        docs = load_txt(str(path), source_name="信息安全技术 示例标准")

        section_docs = [doc for doc in docs if doc.metadata.get("block_type") == "standard_section"]
        section_numbers = {doc.metadata.get("section_no") for doc in section_docs}
        principle_doc = next(doc for doc in section_docs if doc.metadata.get("section_no") == "4")

        self.assertEqual(principle_doc.metadata["document_type"], "标准")
        self.assertEqual(principle_doc.metadata["law_level"], "国家标准")
        self.assertEqual(principle_doc.metadata["standard_type"], "推荐性国家标准")
        self.assertEqual(principle_doc.metadata["type"], "article")
        self.assertIn("4", section_numbers)
        self.assertIn("4.1", section_numbers)
        self.assertIn("[《信息安全技术 示例标准》4 基本原则]", principle_doc.metadata["citation"])
        self.assertIn("合法、正当、必要", principle_doc.page_content)


if __name__ == "__main__":
    unittest.main()
