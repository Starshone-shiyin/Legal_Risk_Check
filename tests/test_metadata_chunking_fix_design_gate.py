import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.check_metadata_chunking_fix_design_gate import (
    DEFAULT_FIX_DESIGN_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_ROOT_CAUSE_PATH,
    build_report,
    render_markdown,
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class MetadataChunkingFixDesignGateTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(DEFAULT_FIX_DESIGN_PATH, legacy_report_path("metadata_chunking_fix_design_report.json"))
        self.assertEqual(DEFAULT_ROOT_CAUSE_PATH, legacy_report_path("metadata_chunking_root_cause_report.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("metadata_chunking_fix_design_gate_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/metadata_chunking_fix_design_gate_v0.4.12.2.md"))

    def test_real_reports_pass_gate(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.12.2")
        self.assertEqual(report["schema_kind"], "metadata_chunking_fix_design_gate")
        self.assertEqual(report["summary"]["status"], "passed")
        self.assertEqual(report["summary"]["failed_check_count"], 0)
        self.assertEqual(report["summary"]["allowed_next_step"], "metadata_chunking_series_closeout")
        self.assertFalse(report["summary"]["implementation_allowed"])

    def test_missing_stable_id_impact_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            design = copy.deepcopy(load_json(DEFAULT_FIX_DESIGN_PATH))
            design["stable_id_impact"]["chunk_id_change_expected"] = False
            design_path = tmp / "fix_design.json"
            write_json(design_path, design)

            report = build_report(design_path, DEFAULT_ROOT_CAUSE_PATH)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("stable_id_impact", {row["check_id"] for row in report["failed_checks"]})

    def test_payload_patch_permission_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            design = copy.deepcopy(load_json(DEFAULT_FIX_DESIGN_PATH))
            design["stable_id_impact"]["direct_payload_patch_allowed"] = True
            design_path = tmp / "fix_design.json"
            write_json(design_path, design)

            report = build_report(design_path, DEFAULT_ROOT_CAUSE_PATH)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("no_payload_patch", {row["check_id"] for row in report["failed_checks"]})

    def test_markdown_reports_gate_status(self):
        markdown = render_markdown(build_report())
        self.assertIn("v0.4.12.2 Metadata/Chunking Fix Design Gate", markdown)
        self.assertIn("Allowed next step", markdown)
        self.assertIn("`PASS`", markdown)


if __name__ == "__main__":
    unittest.main()
