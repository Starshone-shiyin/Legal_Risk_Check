import tempfile
import unittest
from pathlib import Path

from tools.check_test_index_consistency import build_report


REQUIRED_TEXT = "\n".join([
    "## 定位与约定",
    "## 测试套件",
    "## 测试产物",
    "## Legacy 路径与布局契约",
    "## Advisory 与正式人工复核边界",
    "## 已知误读风险",
    "tests/test_*.py",
    "tests/*.json",
    "tests/*.csv",
    "tests/fixtures/",
    "tests/manual_review_export_pipeline_dry_run_artifacts/",
])


class TestIndexConsistencyTest(unittest.TestCase):
    def test_reports_root_level_tests_missing_from_index(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            test_dir = root / "tests"
            index_path = root / "docs" / "indexes" / "project_test_index.md"
            test_dir.mkdir()
            index_path.parent.mkdir(parents=True)
            (test_dir / "test_known.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
            (test_dir / "test_missing.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
            index_path.write_text(f"{REQUIRED_TEXT}\n`tests/test_known.py`\n", encoding="utf-8")

            report = build_report(root, Path("tests"), Path("docs/indexes/project_test_index.md"))

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("root_level_test_missing_from_index", report["errors"])
        self.assertEqual(report["missing_tests"], ["tests/test_missing.py"])

    def test_requires_core_anchors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            test_dir = root / "tests"
            index_path = root / "docs" / "indexes" / "project_test_index.md"
            test_dir.mkdir()
            index_path.parent.mkdir(parents=True)
            (test_dir / "test_known.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
            index_path.write_text("`tests/test_known.py`\n", encoding="utf-8")

            report = build_report(root, Path("tests"), Path("docs/indexes/project_test_index.md"))

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("missing_required_anchor", report["errors"])
        self.assertGreater(report["summary"]["missing_required_anchor_count"], 0)

    def test_passes_when_all_tests_and_anchors_are_indexed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            test_dir = root / "tests"
            index_path = root / "docs" / "indexes" / "project_test_index.md"
            test_dir.mkdir()
            index_path.parent.mkdir(parents=True)
            (test_dir / "test_known.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
            index_path.write_text(f"{REQUIRED_TEXT}\n`tests/test_known.py`\n", encoding="utf-8")

            report = build_report(root, Path("tests"), Path("docs/indexes/project_test_index.md"))

        self.assertEqual(report["summary"]["status"], "passed")
        self.assertEqual(report["summary"]["missing_test_count"], 0)


if __name__ == "__main__":
    unittest.main()
