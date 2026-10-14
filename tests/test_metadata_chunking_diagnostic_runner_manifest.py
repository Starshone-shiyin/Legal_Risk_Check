import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_metadata_chunking_diagnostic_runner_manifest import (
    DEFAULT_DRY_RUN_CONTRACT_REPORT_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_SERIES_CLOSEOUT_REPORT_PATH,
    DEFAULT_SPEC_REPORT_PATH,
    build_report,
    render_markdown,
)


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def build_with_sources(closeout: dict, contract: dict | None = None, spec: dict | None = None) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        closeout_path = Path(tmpdir) / "closeout.json"
        contract_path = Path(tmpdir) / "contract.json"
        spec_path = Path(tmpdir) / "spec.json"
        write_json(closeout_path, copy.deepcopy(closeout))
        write_json(contract_path, copy.deepcopy(contract if contract is not None else load_json("tests/metadata_chunking_diagnostic_dry_run_contract_report.json")))
        write_json(spec_path, copy.deepcopy(spec if spec is not None else load_json("tests/metadata_chunking_diagnostic_spec_report.json")))
        return build_report(closeout_path, contract_path, spec_path)


class MetadataChunkingDiagnosticRunnerManifestTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(DEFAULT_SERIES_CLOSEOUT_REPORT_PATH, legacy_report_path("retrieval_input_quality_series_closeout_report.json"))
        self.assertEqual(DEFAULT_DRY_RUN_CONTRACT_REPORT_PATH, legacy_report_path("metadata_chunking_diagnostic_dry_run_contract_report.json"))
        self.assertEqual(DEFAULT_SPEC_REPORT_PATH, legacy_report_path("metadata_chunking_diagnostic_spec_report.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("metadata_chunking_diagnostic_runner_manifest_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/metadata_chunking_diagnostic_runner_manifest_v0.4.10.0.md"))

    def test_real_sources_build_manifest(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.10.0")
        self.assertEqual(report["schema_kind"], "metadata_chunking_diagnostic_runner_manifest")
        self.assertEqual(report["manifest_gate"]["status"], "ready_for_saved_report_metadata_chunking_diagnostic_runner")
        self.assertEqual(report["manifest_gate"]["allowed_next_step"], "saved_report_metadata_chunking_diagnostic_runner")
        self.assertEqual(report["summary"]["case_count"], 8)
        self.assertEqual(report["summary"]["check_group_count"], 5)
        self.assertEqual(report["summary"]["manifest_item_count"], 40)
        self.assertFalse(report["manifest_gate"]["diagnostic_runner_implemented"])
        self.assertEqual(report["manifest_gate"]["diagnostic_run"], "not_run")
        self.assertFalse(report["manifest_gate"]["implementation_allowed"])
        self.assertEqual(report["manifest_gate"]["blockers"], [])
        self.assertTrue(all(item["diagnostic_input_status"] == "ready_for_saved_report_runner" for item in report["manifest_items"]))
        self.assertTrue(all(item["status"] == "passed" for item in report["assertions"]))

    def test_closeout_drift_blocks_manifest(self):
        closeout = load_json("tests/retrieval_input_quality_series_closeout_report.json")
        closeout["version"] = "0.4.9.10"

        report = build_with_sources(closeout)

        self.assertEqual(report["manifest_gate"]["status"], "blocked")
        self.assertIn("series_closeout_version_mismatch", report["manifest_gate"]["blockers"])

    def test_contract_drift_blocks_manifest(self):
        closeout = load_json("tests/retrieval_input_quality_series_closeout_report.json")
        contract = load_json("tests/metadata_chunking_diagnostic_dry_run_contract_report.json")
        contract["contract_gate"]["status"] = "blocked"

        report = build_with_sources(closeout, contract)

        self.assertEqual(report["manifest_gate"]["status"], "blocked")
        self.assertIn("dry_run_contract_not_ready", report["manifest_gate"]["blockers"])

    def test_spec_order_drift_blocks_manifest(self):
        closeout = load_json("tests/retrieval_input_quality_series_closeout_report.json")
        spec = load_json("tests/metadata_chunking_diagnostic_spec_report.json")
        spec["spec_rows"] = list(reversed(spec["spec_rows"]))

        report = build_with_sources(closeout, spec=spec)

        self.assertEqual(report["manifest_gate"]["status"], "blocked")
        self.assertIn("spec_check_group_order_drift", report["manifest_gate"]["blockers"])

    def test_markdown_is_non_runtime(self):
        markdown = render_markdown(build_report())
        self.assertIn("v0.4.10.0 Metadata/Chunking Diagnostic Runner Manifest", markdown)
        self.assertIn("No diagnostic execution in this version", markdown)
        self.assertIn("Saved reports only", markdown)


if __name__ == "__main__":
    unittest.main()
