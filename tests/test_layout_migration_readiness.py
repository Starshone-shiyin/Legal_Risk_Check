import tempfile
import unittest
from pathlib import Path

from tools.check_layout_migration_readiness import build_report


REQUIRED_INDEXES = [
    "docs/indexes/project_structure_index.md",
    "docs/indexes/project_artifact_index.md",
    "docs/indexes/project_tool_index.md",
    "docs/indexes/project_test_index.md",
    "docs/indexes/project_maintenance_index.md",
]

SCAFFOLD_DIRS = [
    "reports/eval",
    "reports/audits",
    "reports/manual_review",
    "reports/dry_run",
    "tools/eval",
    "tools/evidence_diagnostics",
    "tools/manual_review",
    "tools/ops",
    "tools/ingestion",
]

REQUIRED_REPORTS = [
    "tests/encoding_hygiene_report.json",
    "tests/tool_index_consistency_report.json",
    "tests/test_index_consistency_report.json",
    "tests/artifact_index_consistency_report.json",
]


def write_report(path: Path, status: str = "passed"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"summary": {"status": "' + status + '"}}\n', encoding="utf-8")


class LayoutMigrationReadinessTest(unittest.TestCase):
    def test_blocks_when_scaffold_contains_migrated_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            for rel_path in REQUIRED_INDEXES:
                path = root / rel_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("# ok\n", encoding="utf-8")
            for rel_path in SCAFFOLD_DIRS:
                path = root / rel_path
                path.mkdir(parents=True, exist_ok=True)
                (path / ".gitkeep").write_text("", encoding="utf-8")
            for rel_path in REQUIRED_REPORTS:
                write_report(root / rel_path)
            (root / "reports" / "eval" / "migrated_report.json").write_text("{}", encoding="utf-8")

            report = build_report(root)

        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("scaffold_contains_migrated_files", report["blockers"])

    def test_ready_for_planning_when_required_inputs_are_clean(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            for rel_path in REQUIRED_INDEXES:
                path = root / rel_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("# ok\n", encoding="utf-8")
            for rel_path in SCAFFOLD_DIRS:
                path = root / rel_path
                path.mkdir(parents=True, exist_ok=True)
                (path / ".gitkeep").write_text("", encoding="utf-8")
            for rel_path in REQUIRED_REPORTS:
                write_report(root / rel_path)

            report = build_report(root)

        self.assertEqual(report["summary"]["status"], "ready_for_planning")
        self.assertFalse(report["summary"]["ready_for_automatic_migration"])


if __name__ == "__main__":
    unittest.main()
