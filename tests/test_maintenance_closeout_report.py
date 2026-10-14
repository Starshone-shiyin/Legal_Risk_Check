import tempfile
import unittest
from pathlib import Path

from tools.build_maintenance_closeout_report import build_report


INDEX_DOCS = [
    "docs/indexes/project_structure_index.md",
    "docs/indexes/project_artifact_index.md",
    "docs/indexes/project_tool_index.md",
    "docs/indexes/project_test_index.md",
    "docs/indexes/project_maintenance_index.md",
    "docs/maintenance_terms_guide.md",
]

REPORTS = [
    "tests/encoding_hygiene_report.json",
    "tests/tool_index_consistency_report.json",
    "tests/test_index_consistency_report.json",
    "tests/artifact_index_consistency_report.json",
    "tests/layout_migration_readiness_report.json",
]


def write_json(path: Path, payload: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


class MaintenanceCloseoutReportTest(unittest.TestCase):
    def test_passes_when_reports_and_docs_are_clean(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            for rel_path in INDEX_DOCS:
                path = root / rel_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("# ok\n", encoding="utf-8")
            for rel_path in REPORTS:
                payload = '{"summary": {"status": "passed"}}\n'
                if rel_path.endswith("layout_migration_readiness_report.json"):
                    payload = '{"summary": {"status": "ready_for_planning", "ready_for_automatic_migration": false}}\n'
                write_json(root / rel_path, payload)

            report = build_report(root)

        self.assertEqual(report["summary"]["status"], "passed")
        self.assertEqual(report["summary"]["layout_migration"], "not_performed")
        self.assertEqual(report["summary"]["rag_main_flow_change"], "not_performed")

    def test_flags_failed_reports(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            for rel_path in INDEX_DOCS:
                path = root / rel_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("# ok\n", encoding="utf-8")
            for rel_path in REPORTS:
                payload = '{"summary": {"status": "passed"}}\n'
                if rel_path.endswith("tool_index_consistency_report.json"):
                    payload = '{"summary": {"status": "failed"}}\n'
                if rel_path.endswith("layout_migration_readiness_report.json"):
                    payload = '{"summary": {"status": "ready_for_planning", "ready_for_automatic_migration": false}}\n'
                write_json(root / rel_path, payload)

            report = build_report(root)

        self.assertEqual(report["summary"]["status"], "attention_required")
        self.assertEqual(report["summary"]["failed_report_count"], 1)


if __name__ == "__main__":
    unittest.main()
