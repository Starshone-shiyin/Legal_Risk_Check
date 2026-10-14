import unittest

from src.rag.ingestion import build_article_documents, build_standard_section_documents


ARTICLE_METADATA = {
    "source": "metadata patch sample law",
    "law_name": "metadata patch sample law",
    "document_type": "法律法规",
    "law_level": "法律",
    "authority_level": "test",
    "jurisdiction": "test",
    "issuing_authority": "test",
    "category": "test",
    "version": "0.4.13.8",
    "type": "article",
    "article": "第九十一万三千四百零八条",
    "article_no": 913408,
}


class IngestionMetadataSourcePatchTest(unittest.TestCase):
    def test_parent_article_gets_single_chunk_boundary_metadata(self):
        parts = ["经营者应当依法履行个人信息保护义务。"]
        docs = build_article_documents(parts, ARTICLE_METADATA)
        parent = docs[0]

        self.assertEqual(parent.page_content, parts[0])
        self.assertEqual(parent.metadata["block_type"], "article")
        self.assertEqual(parent.metadata["chunk_index"], 1)
        self.assertEqual(parent.metadata["chunk_count"], 1)
        self.assertEqual(parent.metadata["paragraph_no"], None)
        self.assertEqual(parent.metadata["item_no"], None)
        self.assertEqual(parent.metadata["item_label"], "")
        self.assertIn("第九十一万三千四百零八条", parent.metadata["citation"])

    def test_paragraph_and_item_children_use_article_parts_order(self):
        parts = [
            "个人信息处理者应当按照约定处理个人信息。",
            "（一）明确处理目的、处理方式和保存期限；",
            "（二）建立访问控制、日志审计和删除机制。",
        ]
        docs = build_article_documents(parts, ARTICLE_METADATA)
        children = docs[1:]

        self.assertEqual([doc.page_content for doc in children], parts)
        self.assertEqual([doc.metadata["block_type"] for doc in children], ["paragraph", "item", "item"])
        self.assertEqual([doc.metadata["chunk_index"] for doc in children], [1, 2, 3])
        self.assertEqual([doc.metadata["chunk_count"] for doc in children], [3, 3, 3])
        self.assertEqual(children[0].metadata["paragraph_no"], 1)
        self.assertEqual(children[1].metadata["paragraph_no"], 1)
        self.assertEqual(children[2].metadata["paragraph_no"], 1)
        self.assertEqual(children[1].metadata["item_label"], "（一）")
        self.assertEqual(children[2].metadata["item_label"], "（二）")

    def test_standard_section_chunk_metadata_remains_unchanged(self):
        docs = build_standard_section_documents(
            {
                "heading": "5.4 收集个人信息时的授权同意",
                "section_no": "5.4",
                "section_title": "收集个人信息时的授权同意",
                "section_level": 2,
                "chapter": "5 个人信息的收集",
                "heading_level": "section",
            },
            ["收集个人信息，应向个人信息主体告知收集、使用个人信息的目的、方式和范围等规则。"],
            {
                "source": "信息安全技术 示例标准",
                "law_name": "信息安全技术 示例标准",
                "document_type": "标准",
                "law_level": "国家标准",
                "type": "article",
            },
        )

        heading, section = docs
        self.assertEqual(heading.metadata["block_type"], "heading")
        self.assertNotIn("chunk_index", heading.metadata)
        self.assertEqual(section.metadata["block_type"], "standard_section")
        self.assertEqual(section.metadata["chunk_index"], 1)
        self.assertEqual(section.metadata["chunk_count"], 1)
        self.assertEqual(section.metadata["paragraph_no"], 1)


if __name__ == "__main__":
    unittest.main()
