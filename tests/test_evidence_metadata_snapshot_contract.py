import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_evidence_metadata_snapshot_contract import (
    DEFAULT_CLOSEOUT_PATH,
    DEFAULT_EVAL_CASES_PATH,
    DEFAULT_MANIFEST_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    OUTPUT_FIELDS,
    REQUIRED_METADATA_FIELDS,
    build_report,
    render_markdown,
)


PROHIBITED_SOURCE_PATTERNS = [
    "rag_query(",
    "from src.rag.retriever import rag_query",
    "ChatOpenAI",
    "QdrantClient",
    "fetch(",
    "XMLHttpRequest",
    "/ask",
    "rag_anchor_rules.json",
    "risk_payload_supplement_rules.json",
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class EvidenceMetadataSnapshotContractTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(DEFAULT_CLOSEOUT_PATH, legacy_report_path("metadata_chunking_diagnostic_runner_series_closeout_report.json"))
        self.assertEqual(DEFAULT_MANIFEST_PATH, legacy_report_path("metadata_chunking_diagnostic_runner_manifest_report.json"))
        self.assertEqual(DEFAULT_EVAL_CASES_PATH, Path("tests/rag_eval_cases.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("evidence_metadata_snapshot_contract_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/evidence_metadata_snapshot_contract_v0.4.11.0.md"))

    def test_real_sources_build_ready_contract(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.11.0")
        self.assertEqual(report["schema_kind"], "evidence_metadata_snapshot_contract")
        self.assertEqual(report["contract_gate"]["status"], "ready_for_evidence_metadata_snapshot_runner")
        self.assertEqual(report["contract_gate"]["allowed_next_step"], "read_only_evidence_metadata_snapshot_runner")
        self.assertEqual(report["contract_gate"]["qdrant_access"], "not_run_in_contract")
        self.assertEqual(report["contract_gate"]["future_qdrant_access"], "read_only_payload_scroll_allowed")
        self.assertEqual(report["snapshot_contract"]["sample_case_count"], 8)
        self.assertGreater(report["snapshot_contract"]["target_count"], 8)
        self.assertEqual(report["snapshot_contract"]["required_metadata_fields"], REQUIRED_METADATA_FIELDS)
        self.assertEqual(report["snapshot_contract"]["output_fields"], OUTPUT_FIELDS)
        self.assertFalse(report["contract_gate"]["implementation_allowed"])
        self.assertFalse(report["contract_gate"]["retrieval_logic_change_allowed"])
        self.assertEqual(report["contract_gate"]["blockers"], [])

    def test_closeout_drift_blocks_contract(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            closeout = copy.deepcopy(load_json(DEFAULT_CLOSEOUT_PATH))
            closeout["version"] = "0.4.10.2"
            closeout_path = tmp / "closeout.json"
            write_json(closeout_path, closeout)

            report = build_report(closeout_path, DEFAULT_MANIFEST_PATH, DEFAULT_EVAL_CASES_PATH)

        self.assertEqual(report["contract_gate"]["status"], "blocked")
        self.assertIn("closeout_version_mismatch", report["contract_gate"]["blockers"])

    def test_missing_eval_case_blocks_contract(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            eval_cases = copy.deepcopy(load_json(DEFAULT_EVAL_CASES_PATH))
            eval_cases["cases"] = [case for case in eval_cases["cases"] if case.get("id") != "pipl_principles_001"]
            eval_path = tmp / "rag_eval_cases.json"
            write_json(eval_path, eval_cases)

            report = build_report(DEFAULT_CLOSEOUT_PATH, DEFAULT_MANIFEST_PATH, eval_path)

        self.assertEqual(report["contract_gate"]["status"], "blocked")
        self.assertIn("pipl_principles_001:missing_eval_case", report["contract_gate"]["blockers"])

    def test_markdown_and_tool_are_non_runtime(self):
        markdown = render_markdown(build_report())
        self.assertIn("v0.4.11.0 Evidence Metadata Snapshot Contract", markdown)
        self.assertIn("does not connect to Qdrant or authorize data fixes", markdown)
        self.assertIn("vectors disabled", markdown)

        target_paths = [
            Path("tools/build_evidence_metadata_snapshot_contract.py"),
            Path("docs/evidence_metadata_snapshot_contract_v0.4.11.0.md"),
            Path("tests/evidence_metadata_snapshot_contract_report.json"),
        ]
        matches = []
        for path in target_paths:
            if path.exists():
                content = path.read_text(encoding="utf-8-sig")
                matches.extend((str(path), pattern) for pattern in PROHIBITED_SOURCE_PATTERNS if pattern in content)
        self.assertEqual(matches, [])


if __name__ == "__main__":
    unittest.main()
