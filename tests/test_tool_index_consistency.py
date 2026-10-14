import tempfile
import unittest
from pathlib import Path

from tools.check_tool_index_consistency import build_report


BOUNDARY_TEXT = "\n".join([
    "root-level `tools/*.py`",
    "可能调用 RAG/Qdrant/LLM",
    "离线诊断工具不得接入",
])


class ToolIndexConsistencyTest(unittest.TestCase):
    def test_reports_root_level_tools_missing_from_index(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            tool_dir = root / "tools"
            index_path = root / "docs" / "indexes" / "project_tool_index.md"
            tool_dir.mkdir()
            index_path.parent.mkdir(parents=True)
            (tool_dir / "covered.py").write_text("print('ok')\n", encoding="utf-8")
            (tool_dir / "missing.py").write_text("print('ok')\n", encoding="utf-8")
            index_path.write_text(f"{BOUNDARY_TEXT}\n`tools/covered.py`\n", encoding="utf-8")

            report = build_report(root, Path("tools"), Path("docs/indexes/project_tool_index.md"))

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("root_level_tool_missing_from_index", report["errors"])
        self.assertEqual(report["missing_tools"], ["tools/missing.py"])

    def test_detects_sensitive_imports_without_docstring_false_positive(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            tool_dir = root / "tools"
            index_path = root / "docs" / "indexes" / "project_tool_index.md"
            tool_dir.mkdir()
            index_path.parent.mkdir(parents=True)
            (tool_dir / "offline.py").write_text(
                '"""Mentions rag_query and QdrantClient only as boundary text."""\n',
                encoding="utf-8",
            )
            (tool_dir / "run_rag_eval.py").write_text(
                "from src.rag.retriever import rag_query\n",
                encoding="utf-8",
            )
            index_path.write_text(
                f"{BOUNDARY_TEXT}\n`tools/offline.py`\n`tools/run_rag_eval.py`\n",
                encoding="utf-8",
            )

            report = build_report(root, Path("tools"), Path("docs/indexes/project_tool_index.md"))

        self.assertEqual(report["summary"]["status"], "passed")
        self.assertEqual(report["summary"]["sensitive_tool_count"], 1)
        self.assertEqual(report["sensitive_tools"][0]["path"], "tools/run_rag_eval.py")
        self.assertEqual(report["sensitive_tools"][0]["signals"][0]["key"], "direct_rag_query")

    def test_detects_vectorstore_qdrant_client_factory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            tool_dir = root / "tools"
            index_path = root / "docs" / "indexes" / "project_tool_index.md"
            tool_dir.mkdir()
            index_path.parent.mkdir(parents=True)
            (tool_dir / "check_qdrant_index_integrity.py").write_text(
                "from src.core.vectorstore import get_qdrant_client\n",
                encoding="utf-8",
            )
            index_path.write_text(
                f"{BOUNDARY_TEXT}\n`tools/check_qdrant_index_integrity.py`\n`tools/*.py`\n",
                encoding="utf-8",
            )

            report = build_report(root, Path("tools"), Path("docs/indexes/project_tool_index.md"))

        self.assertEqual(report["summary"]["status"], "passed")
        self.assertEqual(report["summary"]["sensitive_tool_count"], 1)
        self.assertEqual(report["sensitive_tools"][0]["signals"][0]["key"], "direct_vectorstore_qdrant_client_factory")
        self.assertEqual(report["stale_index_tokens"], [])

    def test_requires_boundary_anchors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            tool_dir = root / "tools"
            index_path = root / "docs" / "indexes" / "project_tool_index.md"
            tool_dir.mkdir()
            index_path.parent.mkdir(parents=True)
            (tool_dir / "tool.py").write_text("print('ok')\n", encoding="utf-8")
            index_path.write_text("`tools/tool.py`\n", encoding="utf-8")

            report = build_report(root, Path("tools"), Path("docs/indexes/project_tool_index.md"))

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("missing_boundary_anchors", report["errors"])
        self.assertEqual(report["summary"]["missing_boundary_anchor_count"], 3)


if __name__ == "__main__":
    unittest.main()
