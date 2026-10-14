import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.check_metadata_chunking_diagnostic_saved_report_runner_gate import (
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_RUNNER_REPORT_PATH,
    build_report,
    render_markdown,
)


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def build_with_runner(runner: dict) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "runner.json"
        write_json(path, copy.deepcopy(runner))
        return build_report(path)


class MetadataChunkingDiagnosticSavedReportRunnerGateTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(DEFAULT_RUNNER_REPORT_PATH, legacy_report_path("metadata_chunking_diagnostic_saved_report_runner_report.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("metadata_chunking_diagnostic_saved_report_runner_gate_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/metadata_chunking_diagnostic_saved_report_runner_gate_v0.4.10.2.md"))

    def test_real_runner_report_passes_gate(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.10.2")
        self.assertEqual(report["schema_kind"], "metadata_chunking_diagnostic_saved_report_runner_gate")
        self.assertEqual(report["gate"]["status"], "open_for_v0_4_10_series_closeout")
        self.assertEqual(report["gate"]["allowed_next_step"], "v0_4_10_series_closeout")
        self.assertEqual(report["summary"]["source_diagnostic_row_count"], 40)
        self.assertEqual(report["summary"]["source_blocked_row_count"], 0)
        self.assertFalse(report["gate"]["evidence_level_metadata_snapshot_read"])
        self.assertFalse(report["gate"]["implementation_allowed"])
        self.assertEqual(report["gate"]["blockers"], [])
        self.assertTrue(all(check["status"] == "passed" for check in report["checks"]))

    def test_version_drift_blocks_gate(self):
        runner = load_json("tests/metadata_chunking_diagnostic_saved_report_runner_report.json")
        runner["version"] = "0.4.10.0"

        report = build_with_runner(runner)

        self.assertEqual(report["gate"]["status"], "blocked")
        self.assertIn("runner_version", report["gate"]["blockers"])

    def test_blocked_row_blocks_gate(self):
        runner = load_json("tests/metadata_chunking_diagnostic_saved_report_runner_report.json")
        runner["diagnostic_rows"][0]["blocking_findings"] = ["missing_manifest_case_id"]
        runner["summary"]["blocked_row_count"] = 1

        report = build_with_runner(runner)

        self.assertEqual(report["gate"]["status"], "blocked")
        self.assertIn("zero_blocked_rows", report["gate"]["blockers"])

    def test_snapshot_read_blocks_gate(self):
        runner = load_json("tests/metadata_chunking_diagnostic_saved_report_runner_report.json")
        runner["runner_gate"]["evidence_level_metadata_snapshot_read"] = True

        report = build_with_runner(runner)

        self.assertEqual(report["gate"]["status"], "blocked")
        self.assertIn("saved_report_scope_only", report["gate"]["blockers"])

    def test_markdown_is_non_runtime(self):
        markdown = render_markdown(build_report())
        self.assertIn("v0.4.10.2 Metadata/Chunking Saved-Report Runner Gate", markdown)
        self.assertIn("Gate only", markdown)
        self.assertIn("No evidence-level metadata snapshot", markdown)


if __name__ == "__main__":
    unittest.main()
