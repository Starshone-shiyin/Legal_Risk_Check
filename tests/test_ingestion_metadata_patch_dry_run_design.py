import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_ingestion_metadata_patch_dry_run_design import (
    DEFAULT_CONTRACT_GATE_PATH,
    DEFAULT_CONTRACT_PATH,
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


class IngestionMetadataPatchDryRunDesignTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(DEFAULT_CONTRACT_PATH, legacy_report_path("ingestion_metadata_patch_contract_report.json"))
        self.assertEqual(DEFAULT_CONTRACT_GATE_PATH, legacy_report_path("ingestion_metadata_patch_contract_gate_report.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("ingestion_metadata_patch_dry_run_design_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/ingestion_metadata_patch_dry_run_design_v0.4.13.2.md"))

    def test_real_inputs_build_design(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.13.2")
        self.assertEqual(report["schema_kind"], "ingestion_metadata_patch_dry_run_design")
        self.assertEqual(report["design_gate"]["status"], "ready_for_ingestion_metadata_patch_dry_run_design_gate")
        self.assertEqual(report["summary"]["dry_run_target"], "simulate_build_article_documents_boundary_metadata_patch")
        self.assertFalse(report["design_gate"]["implementation_allowed"])
        self.assertFalse(report["design_gate"]["qdrant_write_allowed"])

    def test_design_defines_expected_and_forbidden_drift(self):
        design = build_report()["dry_run_design"]

        self.assertIn("chunk_index", design["expected_metadata_drift"])
        self.assertIn("chunk_count", design["expected_metadata_drift"])
        self.assertIn("chunk_id", design["expected_metadata_drift"])
        self.assertIn("qdrant_point_id", design["expected_metadata_drift"])
        self.assertIn("page_content", design["forbidden_metadata_drift"])
        self.assertIn("citation", design["forbidden_metadata_drift"])
        self.assertIn("block_type", design["forbidden_metadata_drift"])

    def test_gate_failure_blocks_design(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            gate = copy.deepcopy(load_json(DEFAULT_CONTRACT_GATE_PATH))
            gate["summary"]["status"] = "failed"
            gate_path = tmp / "gate.json"
            write_json(gate_path, gate)

            report = build_report(DEFAULT_CONTRACT_PATH, gate_path)

        self.assertEqual(report["design_gate"]["status"], "blocked")
        self.assertIn("contract_gate_not_passed", report["design_gate"]["blockers"])

    def test_output_contract_blocks_content_and_citation_drift(self):
        output = build_report()["output_contract"]

        self.assertIn("any content_changed row", output["blocking_conditions"])
        self.assertIn("any citation_changed row", output["blocking_conditions"])
        self.assertIn("pre/post document count mismatch for a sample", output["blocking_conditions"])
        self.assertIn("chunk_id_changed", output["required_row_fields"])

    def test_markdown_keeps_dry_run_only_boundary(self):
        markdown = render_markdown(build_report())
        self.assertIn("v0.4.13.2 Ingestion Metadata Patch Dry-Run Design", markdown)
        self.assertIn("does not patch ingestion", markdown)
        self.assertIn("Forbidden Drift", markdown)


if __name__ == "__main__":
    unittest.main()
