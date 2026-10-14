import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.run_metadata_chunking_diagnostic_saved_report import (
    DEFAULT_DRY_RUN_CONTRACT_REPORT_PATH,
    DEFAULT_MANIFEST_REPORT_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    build_report,
    render_markdown,
)


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def build_with_sources(manifest: dict, contract: dict | None = None) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest_path = Path(tmpdir) / "manifest.json"
        contract_path = Path(tmpdir) / "contract.json"
        write_json(manifest_path, copy.deepcopy(manifest))
        write_json(contract_path, copy.deepcopy(contract if contract is not None else load_json("tests/metadata_chunking_diagnostic_dry_run_contract_report.json")))
        return build_report(manifest_path, contract_path)


class MetadataChunkingDiagnosticSavedReportRunnerTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(DEFAULT_MANIFEST_REPORT_PATH, legacy_report_path("metadata_chunking_diagnostic_runner_manifest_report.json"))
        self.assertEqual(DEFAULT_DRY_RUN_CONTRACT_REPORT_PATH, legacy_report_path("metadata_chunking_diagnostic_dry_run_contract_report.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("metadata_chunking_diagnostic_saved_report_runner_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/metadata_chunking_diagnostic_saved_report_runner_v0.4.10.1.md"))

    def test_real_sources_run_saved_report_diagnostic(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.10.1")
        self.assertEqual(report["schema_kind"], "metadata_chunking_diagnostic_saved_report_runner")
        self.assertEqual(report["runner_gate"]["status"], "completed_saved_report_metadata_chunking_diagnostic")
        self.assertEqual(report["runner_gate"]["allowed_next_step"], "metadata_chunking_diagnostic_saved_report_runner_gate")
        self.assertEqual(report["summary"]["diagnostic_row_count"], 40)
        self.assertEqual(report["summary"]["blocked_row_count"], 0)
        self.assertEqual(report["summary"]["case_count"], 8)
        self.assertEqual(report["summary"]["check_group_count"], 5)
        self.assertEqual(report["runner_gate"]["diagnostic_run"], "saved_report_scope_only")
        self.assertFalse(report["runner_gate"]["evidence_level_metadata_snapshot_read"])
        self.assertFalse(report["runner_gate"]["implementation_allowed"])
        self.assertEqual(report["runner_gate"]["blockers"], [])
        self.assertTrue(all(row["dry_run_status"] == "completed_saved_report_scope" for row in report["diagnostic_rows"]))
        self.assertTrue(all(item["status"] == "passed" for item in report["assertions"]))

    def test_manifest_drift_blocks_runner(self):
        manifest = load_json("tests/metadata_chunking_diagnostic_runner_manifest_report.json")
        manifest["version"] = "0.4.9.9"

        report = build_with_sources(manifest)

        self.assertEqual(report["runner_gate"]["status"], "blocked")
        self.assertIn("manifest_version_mismatch", report["runner_gate"]["blockers"])

    def test_missing_manifest_contract_bits_blocks_runner(self):
        manifest = load_json("tests/metadata_chunking_diagnostic_runner_manifest_report.json")
        manifest["manifest_items"][0]["required_fields"] = []

        report = build_with_sources(manifest)

        self.assertEqual(report["runner_gate"]["status"], "blocked")
        self.assertIn("diagnostic_rows_blocked", report["runner_gate"]["blockers"])

    def test_contract_drift_blocks_runner(self):
        manifest = load_json("tests/metadata_chunking_diagnostic_runner_manifest_report.json")
        contract = load_json("tests/metadata_chunking_diagnostic_dry_run_contract_report.json")
        contract["dry_run_output_contract"]["required_fields"].remove("article_locator_status")

        report = build_with_sources(manifest, contract)

        self.assertEqual(report["runner_gate"]["status"], "blocked")
        self.assertIn("dry_run_output_contract_drift", report["runner_gate"]["blockers"])

    def test_markdown_is_non_runtime(self):
        markdown = render_markdown(build_report())
        self.assertIn("v0.4.10.1 Metadata/Chunking Saved-Report Diagnostic Runner", markdown)
        self.assertIn("Saved-report scope only", markdown)
        self.assertIn("Evidence-level metadata quality still requires", markdown)


if __name__ == "__main__":
    unittest.main()
