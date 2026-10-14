import tempfile
import unittest
from pathlib import Path

from tools.check_artifact_index_consistency import build_report


REQUIRED_TEXT = "\n".join([
    "tests/*.json",
    "tests/*.csv",
    "tests/fixtures/",
    "tests/manual_review_export_pipeline_dry_run_artifacts/",
    "tools/manual_review_visual_workbench/index.html",
    "docs/",
    "reports/eval",
    "reports/audits",
    "reports/manual_review",
    "reports/dry_run",
    "Eval 与回归报告",
    "Evidence 与检索质量诊断",
    "Legal Functional Typing",
    "Manual Review 与治理闭环",
    "Dry-Run 与安全隔离产物",
    "Health Check 与结构维护",
    "工具入口与产物关系",
    "维护规则",
    "不要把 AI suggestion、prescreen、pilot assist、mobile aid 写成 completed manual decision",
    "不要把 `tests/evidence_fixture_candidate_pool.json` 写成已经进入 eval case",
    "不要把 `reports/` scaffold 写成当前权威输出目录",
])


class ArtifactIndexConsistencyTest(unittest.TestCase):
    def test_reports_root_level_artifacts_missing_from_index(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            test_dir = root / "tests"
            index_path = root / "docs" / "indexes" / "project_artifact_index.md"
            test_dir.mkdir()
            index_path.parent.mkdir(parents=True)
            (test_dir / "known_report.json").write_text("{}", encoding="utf-8")
            (test_dir / "missing_report.json").write_text("{}", encoding="utf-8")
            index_path.write_text(f"{REQUIRED_TEXT}\n`tests/known_report.json`\n", encoding="utf-8")

            report = build_report(root, Path("tests"), Path("docs/indexes/project_artifact_index.md"))

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("root_level_artifact_missing_from_index", report["errors"])
        self.assertEqual(report["missing_artifacts"], ["tests/missing_report.json"])

    def test_requires_semantic_guardrails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            test_dir = root / "tests"
            index_path = root / "docs" / "indexes" / "project_artifact_index.md"
            test_dir.mkdir()
            index_path.parent.mkdir(parents=True)
            (test_dir / "known_report.json").write_text("{}", encoding="utf-8")
            index_path.write_text("`tests/known_report.json`\n", encoding="utf-8")

            report = build_report(root, Path("tests"), Path("docs/indexes/project_artifact_index.md"))

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("missing_semantic_guardrail", report["errors"])

    def test_passes_when_artifacts_and_required_text_are_indexed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            test_dir = root / "tests"
            index_path = root / "docs" / "indexes" / "project_artifact_index.md"
            test_dir.mkdir()
            index_path.parent.mkdir(parents=True)
            (test_dir / "known_report.json").write_text("{}", encoding="utf-8")
            (test_dir / "known_table.csv").write_text("a,b\n", encoding="utf-8")
            (test_dir / "known_summary.md").write_text("# ok\n", encoding="utf-8")
            index_path.write_text(
                f"{REQUIRED_TEXT}\n"
                "`tests/known_report.json`\n"
                "`tests/known_table.csv`\n"
                "`tests/known_summary.md`\n",
                encoding="utf-8",
            )

            report = build_report(root, Path("tests"), Path("docs/indexes/project_artifact_index.md"))

        self.assertEqual(report["summary"]["status"], "passed")
        self.assertEqual(report["summary"]["missing_artifact_count"], 0)


if __name__ == "__main__":
    unittest.main()
