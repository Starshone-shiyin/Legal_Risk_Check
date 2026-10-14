import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.check_ingestion_metadata_patch_contract_gate import (
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


class IngestionMetadataPatchContractGateTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(DEFAULT_CONTRACT_PATH, legacy_report_path("ingestion_metadata_patch_contract_report.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("ingestion_metadata_patch_contract_gate_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/ingestion_metadata_patch_contract_gate_v0.4.13.1.md"))

    def test_real_contract_passes_gate(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.13.1")
        self.assertEqual(report["schema_kind"], "ingestion_metadata_patch_contract_gate")
        self.assertEqual(report["summary"]["status"], "passed")
        self.assertEqual(report["summary"]["failed_check_count"], 0)
        self.assertEqual(report["summary"]["allowed_next_step"], "ingestion_metadata_patch_dry_run_design")
        self.assertFalse(report["summary"]["implementation_allowed"])
        self.assertFalse(report["summary"]["qdrant_write_allowed"])

    def test_runtime_file_scope_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            contract = copy.deepcopy(load_json(DEFAULT_CONTRACT_PATH))
            contract["patch_contract"]["allowed_files"].append("src/rag/retriever.py")
            contract_path = tmp / "contract.json"
            write_json(contract_path, contract)

            report = build_report(contract_path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("allowed_file_scope", {row["check_id"] for row in report["failed_checks"]})

    def test_parent_rule_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            contract = copy.deepcopy(load_json(DEFAULT_CONTRACT_PATH))
            contract["patch_contract"]["parent_article_rule"]["chunk_count"] = "len(article_parts)"
            contract_path = tmp / "contract.json"
            write_json(contract_path, contract)

            report = build_report(contract_path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("parent_article_rule", {row["check_id"] for row in report["failed_checks"]})

    def test_qdrant_write_permission_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            contract = copy.deepcopy(load_json(DEFAULT_CONTRACT_PATH))
            contract["guardrails"]["qdrant_write"] = "allowed"
            contract_path = tmp / "contract.json"
            write_json(contract_path, contract)

            report = build_report(contract_path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("qdrant_blocked", {row["check_id"] for row in report["failed_checks"]})

    def test_markdown_reports_contract_gate_status(self):
        markdown = render_markdown(build_report())
        self.assertIn("v0.4.13.1 Ingestion Metadata Patch Contract Gate", markdown)
        self.assertIn("Allowed next step", markdown)
        self.assertIn("`PASS`", markdown)


if __name__ == "__main__":
    unittest.main()
