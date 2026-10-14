import json
import tempfile
import unittest
from pathlib import Path

from langchain_core.documents import Document

import tools.check_legal_corpus_integrity as checker


def make_doc(**metadata):
    base_metadata = {
        "source": "Law A",
        "document_type": "法律法规",
        "law_level": "法律",
        "authority_level": "国家级",
        "jurisdiction": "全国",
        "issuing_authority": "Authority",
        "category": "test",
        "version": "2026",
        "block_type": "article",
        "article_no": 1,
        "chunk_index": 1,
        "chunk_count": 1,
        "chunk_id": "chunk-a",
        "qdrant_point_id": 1001,
        "citation": "[Law A Article 1]",
    }
    base_metadata.update(metadata)
    return Document(page_content="Article content", metadata=base_metadata)


class LegalCorpusIntegrityTest(unittest.TestCase):
    def write_manifest(self, root: Path, documents: list[dict]) -> Path:
        manifest_path = root / "knowledge_manifest.json"
        manifest_path.write_text(json.dumps({"documents": documents}, ensure_ascii=False), encoding="utf-8")
        return manifest_path

    def base_entry(self, file_path: Path) -> dict:
        return {
            "source": "Law A",
            "file_path": str(file_path),
            "document_type": "法律法规",
            "law_level": "法律",
            "authority_level": "国家级",
            "jurisdiction": "全国",
            "issuing_authority": "Authority",
            "category": "test",
            "domain": "test_domain",
            "version": "2026",
            "effective_date": "2026-01-01",
            "expected_anchors": [{"article_no": 1}],
            "smoke_cases": ["smoke_law_a"],
        }

    def test_build_report_passes_valid_manifest_and_generated_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            knowledge_root = root / "src" / "knowledge"
            knowledge_root.mkdir(parents=True)
            text_file = knowledge_root / "law_a.txt"
            text_file.write_text("sample", encoding="utf-8")
            manifest = self.write_manifest(root, [self.base_entry(text_file)])

            original_load_txt = checker.load_txt
            try:
                checker.load_txt = lambda *args, **kwargs: [make_doc()]
                report = checker.build_report(manifest, knowledge_root)
            finally:
                checker.load_txt = original_load_txt

            self.assertEqual(report["status"], "passed")
            self.assertEqual(report["summary"]["manifest_documents"], 1)
            self.assertEqual(report["summary"]["generated_documents"], 1)
            self.assertEqual(report["summary"]["error_count"], 0)

    def test_build_report_flags_missing_manifest_field_and_orphan_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            knowledge_root = root / "src" / "knowledge"
            knowledge_root.mkdir(parents=True)
            text_file = knowledge_root / "law_a.txt"
            text_file.write_text("sample", encoding="utf-8")
            orphan_file = knowledge_root / "orphan.txt"
            orphan_file.write_text("orphan", encoding="utf-8")
            entry = self.base_entry(text_file)
            entry.pop("jurisdiction")
            manifest = self.write_manifest(root, [entry])

            original_load_txt = checker.load_txt
            try:
                checker.load_txt = lambda *args, **kwargs: [make_doc()]
                report = checker.build_report(manifest, knowledge_root)
            finally:
                checker.load_txt = original_load_txt

            self.assertEqual(report["status"], "failed")
            self.assertIn("missing_manifest_field", report["issue_type_summary"])
            self.assertIn("orphan_knowledge_file", report["issue_type_summary"])
            self.assertEqual(report["summary"]["orphan_knowledge_file_count"], 1)

    def test_build_report_flags_generated_metadata_and_anchor_gaps(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            knowledge_root = root / "src" / "knowledge"
            knowledge_root.mkdir(parents=True)
            text_file = knowledge_root / "law_a.txt"
            text_file.write_text("sample", encoding="utf-8")
            manifest = self.write_manifest(root, [self.base_entry(text_file)])

            bad_doc = make_doc(
                article_no=99,
                chunk_index=2,
                chunk_count=1,
                citation="",
                chunk_id="",
            )

            original_load_txt = checker.load_txt
            try:
                checker.load_txt = lambda *args, **kwargs: [bad_doc]
                report = checker.build_report(manifest, knowledge_root)
            finally:
                checker.load_txt = original_load_txt

            self.assertEqual(report["status"], "failed")
            self.assertIn("missing_generated_metadata", report["issue_type_summary"])
            self.assertIn("invalid_chunk_boundary", report["issue_type_summary"])
            self.assertIn("missing_citation", report["issue_type_summary"])
            self.assertIn("missing_expected_anchor", report["issue_type_summary"])


if __name__ == "__main__":
    unittest.main()
