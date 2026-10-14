import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools._shared.layout import legacy_report_path
from tools import run_evidence_metadata_snapshot as snapshot
from tools.run_evidence_metadata_snapshot import (
    DEFAULT_CONTRACT_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    build_report,
    render_markdown,
)


PROHIBITED_SOURCE_PATTERNS = [
    "rag_query(",
    "from src.rag.retriever import rag_query",
    "ChatOpenAI",
    "fetch(",
    "XMLHttpRequest",
    "/ask",
    "rag_anchor_rules.json",
    "risk_payload_supplement_rules.json",
    "rag_eval_cases.json",
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class EvidenceMetadataSnapshotTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(DEFAULT_CONTRACT_PATH, legacy_report_path("evidence_metadata_snapshot_contract_report.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("evidence_metadata_snapshot_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/evidence_metadata_snapshot_v0.4.11.1.md"))

    def test_contract_drift_blocks_snapshot(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            contract = copy.deepcopy(load_json(DEFAULT_CONTRACT_PATH))
            contract["version"] = "0.4.10.3"
            contract_path = tmp / "contract.json"
            write_json(contract_path, contract)

            report = build_report(contract_path, "legal_knowledge", "localhost", 6333, 0.1)

        self.assertEqual(report["snapshot_gate"]["status"], "blocked")
        self.assertIn("contract_version_or_schema_mismatch", report["snapshot_gate"]["blockers"])

    def test_qdrant_unavailable_blocks_without_fabricating_rows(self):
        with patch.object(snapshot, "connect_client", side_effect=RuntimeError("offline")):
            report = build_report(DEFAULT_CONTRACT_PATH, "legal_knowledge", "localhost", 6333, 0.1)

        self.assertEqual(report["snapshot_gate"]["status"], "blocked")
        self.assertFalse(report["snapshot_gate"]["qdrant_payload_read"])
        self.assertIn("qdrant_unavailable", report["snapshot_gate"]["blockers"])
        self.assertEqual(report["summary"]["diagnostic_row_count"], 0)
        self.assertEqual(report["diagnostic_rows"], [])

    def test_fake_payloads_generate_rows_without_vectors(self):
        contract = load_json(DEFAULT_CONTRACT_PATH)
        first = contract["snapshot_targets"][0]
        payloads = [
            (
                "point-1",
                {
                    "metadata": {
                        "chunk_id": "chunk-1",
                        "parent_article_id": "law::1",
                        "source": first["expected_source"],
                        "law_name": first["expected_source"],
                        "citation": "[citation]",
                        "block_type": "article",
                        "article_no": first["expected_article_no"],
                        "section_no": first["expected_section_no"],
                        "chunk_index": 1,
                        "chunk_count": 1,
                    },
                    "page_content": "sample content",
                },
            )
        ]
        with patch.object(snapshot, "connect_client", return_value=object()):
            with patch.object(snapshot, "collect_payloads", return_value=payloads):
                report = build_report(DEFAULT_CONTRACT_PATH, "legal_knowledge", "localhost", 6333, 0.1)

        self.assertEqual(report["version"], "0.4.11.1")
        self.assertEqual(report["schema_kind"], "evidence_metadata_snapshot")
        self.assertTrue(report["snapshot_gate"]["qdrant_payload_read"])
        self.assertFalse(report["snapshot_gate"]["with_vectors"])
        self.assertEqual(report["summary"]["diagnostic_row_count"], len(contract["snapshot_targets"]))
        self.assertEqual(report["diagnostic_rows"][0]["matched_point_count"], 1)
        self.assertEqual(report["diagnostic_rows"][0]["metadata_completeness_status"], "passed")

    def test_markdown_and_tool_do_not_call_rag_or_llm(self):
        with patch.object(snapshot, "connect_client", side_effect=RuntimeError("offline")):
            markdown = render_markdown(build_report(DEFAULT_CONTRACT_PATH, "legal_knowledge", "localhost", 6333, 0.1))
        self.assertIn("v0.4.11.1 Evidence Metadata Snapshot", markdown)
        self.assertIn("Payload-only Qdrant scroll", markdown)
        self.assertIn("intentionally blocked", markdown)

        target_paths = [
            Path("tools/run_evidence_metadata_snapshot.py"),
            Path("docs/evidence_metadata_snapshot_v0.4.11.1.md"),
            Path("tests/evidence_metadata_snapshot_report.json"),
        ]
        matches = []
        for path in target_paths:
            if path.exists():
                content = path.read_text(encoding="utf-8-sig")
                matches.extend((str(path), pattern) for pattern in PROHIBITED_SOURCE_PATTERNS if pattern in content)
        self.assertEqual(matches, [])


if __name__ == "__main__":
    unittest.main()
