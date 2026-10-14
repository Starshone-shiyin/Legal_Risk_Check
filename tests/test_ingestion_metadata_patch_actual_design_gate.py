import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.check_ingestion_metadata_patch_actual_design_gate import (
    DEFAULT_ACTUAL_DESIGN_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    build_report,
    render_markdown,
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class IngestionMetadataPatchActualDesignGateTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(DEFAULT_ACTUAL_DESIGN_PATH, legacy_report_path("ingestion_metadata_patch_actual_design_report.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("ingestion_metadata_patch_actual_design_gate_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/ingestion_metadata_patch_actual_design_gate_v0.4.13.7.md"))

    def test_real_design_passes_gate(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.13.7")
        self.assertEqual(report["schema_kind"], "ingestion_metadata_patch_actual_design_gate")
        self.assertEqual(report["summary"]["status"], "passed")
        self.assertEqual(report["summary"]["failed_check_count"], 0)
        self.assertEqual(report["summary"]["allowed_next_step"], "minimal_ingestion_metadata_source_patch")
        self.assertFalse(report["summary"]["implementation_allowed"])
        self.assertFalse(report["summary"]["qdrant_write_allowed"])
        self.assertFalse(report["summary"]["rebuild_allowed"])

    def test_wrong_allowed_file_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            design = copy.deepcopy(load_json(DEFAULT_ACTUAL_DESIGN_PATH))
            design["patch_design"]["allowed_file"] = "src/rag/retriever.py"
            path = tmp / "design.json"
            write_json(path, design)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("single_file_scope", {row["check_id"] for row in report["failed_checks"]})

    def test_child_count_rule_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            design = copy.deepcopy(load_json(DEFAULT_ACTUAL_DESIGN_PATH))
            design["patch_design"]["child_chunk_rule"]["chunk_count"] = "len(child_docs)"
            path = tmp / "design.json"
            write_json(path, design)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("child_count_rule", {row["check_id"] for row in report["failed_checks"]})

    def test_missing_validation_plan_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            design = copy.deepcopy(load_json(DEFAULT_ACTUAL_DESIGN_PATH))
            design["post_patch_validation_plan"] = [
                item for item in design["post_patch_validation_plan"] if "build_standard_section_documents" not in item
            ]
            path = tmp / "design.json"
            write_json(path, design)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("validation_standard_sections", {row["check_id"] for row in report["failed_checks"]})

    def test_implementation_permission_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            design = copy.deepcopy(load_json(DEFAULT_ACTUAL_DESIGN_PATH))
            design["summary"]["implementation_allowed"] = True
            path = tmp / "design.json"
            write_json(path, design)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("implementation_blocked", {row["check_id"] for row in report["failed_checks"]})

    def test_qdrant_rebuild_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            design = copy.deepcopy(load_json(DEFAULT_ACTUAL_DESIGN_PATH))
            design["guardrails"]["collection_rebuild"] = "allowed"
            path = tmp / "design.json"
            write_json(path, design)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("qdrant_rebuild_blocked", {row["check_id"] for row in report["failed_checks"]})

    def test_missing_handoff_boundary_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            design = copy.deepcopy(load_json(DEFAULT_ACTUAL_DESIGN_PATH))
            design["handoff"]["not_allowed_yet"].remove("modify eval cases or fixtures")
            path = tmp / "design.json"
            write_json(path, design)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("handoff_boundaries", {row["check_id"] for row in report["failed_checks"]})

    def test_markdown_reports_gate_status(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.13.7 Ingestion Metadata Patch Actual Design Gate", markdown)
        self.assertIn("Allowed next step", markdown)
        self.assertIn("`PASS`", markdown)


if __name__ == "__main__":
    unittest.main()
