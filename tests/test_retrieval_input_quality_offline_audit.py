import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_retrieval_input_quality_offline_audit import (
    DEFAULT_ANCHOR_DEPENDENCY_AUDIT_PATH,
    DEFAULT_AUDIT_SPEC_PATH,
    DEFAULT_BASE_RETRIEVAL_AUDIT_PATH,
    DEFAULT_INTAKE_REPORT_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    EXPECTED_BUCKET_ORDER,
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
    "rag_eval_cases.json",
]


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def build_with_sources(spec: dict, intake: dict | None = None, base: dict | None = None, anchor: dict | None = None) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        spec_path = root / "spec.json"
        intake_path = root / "intake.json"
        base_path = root / "base.json"
        anchor_path = root / "anchor.json"
        write_json(spec_path, copy.deepcopy(spec))
        write_json(intake_path, copy.deepcopy(intake if intake is not None else load_json("tests/retrieval_input_quality_intake_report.json")))
        write_json(base_path, copy.deepcopy(base if base is not None else load_json("tests/base_retrieval_quality_audit_report.json")))
        write_json(anchor_path, copy.deepcopy(anchor if anchor is not None else load_json("tests/anchor_dependency_audit_report.json")))
        return build_report(spec_path, intake_path, base_path, anchor_path)


class RetrievalInputQualityOfflineAuditTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(
            DEFAULT_AUDIT_SPEC_PATH,
            legacy_report_path("retrieval_input_quality_audit_spec_report.json"),
        )
        self.assertEqual(
            DEFAULT_INTAKE_REPORT_PATH,
            legacy_report_path("retrieval_input_quality_intake_report.json"),
        )
        self.assertEqual(
            DEFAULT_BASE_RETRIEVAL_AUDIT_PATH,
            legacy_report_path("base_retrieval_quality_audit_report.json"),
        )
        self.assertEqual(
            DEFAULT_ANCHOR_DEPENDENCY_AUDIT_PATH,
            legacy_report_path("anchor_dependency_audit_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("retrieval_input_quality_offline_audit_report.json"),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/retrieval_input_quality_offline_audit_v0.4.9.2.md"),
        )

    def test_real_sources_build_offline_audit(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.9.2")
        self.assertEqual(report["schema_kind"], "retrieval_input_quality_offline_audit")
        self.assertEqual(report["audit_gate"]["status"], "completed_saved_report_offline_audit")
        self.assertFalse(report["audit_gate"]["implementation_allowed"])
        self.assertFalse(report["audit_gate"]["code_patch_authorized"])
        self.assertFalse(report["audit_gate"]["retrieval_logic_change_allowed"])
        self.assertEqual(report["audit_gate"]["blockers"], [])
        self.assertEqual(report["summary"]["audit_row_count"], 5)
        self.assertEqual(report["summary"]["bucket_ids"], EXPECTED_BUCKET_ORDER)
        self.assertGreaterEqual(report["summary"]["high_severity_count"], 3)
        self.assertGreaterEqual(report["summary"]["unique_sample_case_count"], 8)

        rows = report["offline_audit_rows"]
        self.assertEqual([row["bucket_id"] for row in rows], EXPECTED_BUCKET_ORDER)
        impacted = {row["bucket_id"]: row["impacted_case_count"] for row in rows}
        self.assertEqual(impacted["source_article_identity_quality"], 34)
        self.assertEqual(impacted["metadata_chunking_quality"], 33)
        self.assertEqual(impacted["query_lexical_coverage_quality"], 34)
        self.assertEqual(impacted["legal_domain_boundary_quality"], 6)
        self.assertEqual(impacted["anchor_dependency_quality"], 33)
        for row in rows:
            self.assertEqual(row["audit_status"], "completed_saved_report_offline_audit")
            self.assertGreater(row["impacted_case_count"], 0)
            self.assertTrue(row["sample_case_ids"])
            self.assertTrue(row["evidence_signals"])
            self.assertTrue(row["audit_findings"])
            self.assertTrue(row["recommended_next_route"].endswith("_diagnostic_report") or row["recommended_next_route"].endswith("_reduction_diagnostic_report"))
            self.assertFalse(row["runtime_change_allowed"])
            self.assertFalse(row["implementation_allowed"])
            self.assertFalse(row["retrieval_logic_change_allowed"])
        self.assertTrue(all(item["status"] == "passed" for item in report["assertions"]))

    def test_spec_version_drift_blocks_audit(self):
        spec = load_json("tests/retrieval_input_quality_audit_spec_report.json")
        spec["version"] = "0.4.9.0"

        report = build_with_sources(spec)

        self.assertEqual(report["audit_gate"]["status"], "blocked")
        self.assertIn("audit_spec_version_mismatch", report["audit_gate"]["blockers"])

    def test_spec_bucket_order_drift_blocks_audit(self):
        spec = load_json("tests/retrieval_input_quality_audit_spec_report.json")
        spec["audit_spec_rows"] = list(reversed(spec["audit_spec_rows"]))

        report = build_with_sources(spec)

        self.assertEqual(report["audit_gate"]["status"], "blocked")
        self.assertIn("audit_spec_bucket_order_drift", report["audit_gate"]["blockers"])

    def test_spec_gate_drift_blocks_audit(self):
        spec = load_json("tests/retrieval_input_quality_audit_spec_report.json")
        spec["spec_gate"]["status"] = "blocked"
        spec["spec_gate"]["blockers"] = ["manual_blocker"]

        report = build_with_sources(spec)

        self.assertEqual(report["audit_gate"]["status"], "blocked")
        self.assertIn("audit_spec_gate_not_ready", report["audit_gate"]["blockers"])
        self.assertIn("audit_spec_has_blockers", report["audit_gate"]["blockers"])

    def test_markdown_and_outputs_are_non_runtime(self):
        markdown = render_markdown(build_report())
        self.assertIn("v0.4.9.2 Retrieval Input Quality Offline Audit", markdown)
        self.assertIn("saved-report offline audit runner only", markdown)
        self.assertIn("The next step may add a lightweight gate", markdown)

        target_paths = [
            Path("tools/build_retrieval_input_quality_offline_audit.py"),
            Path("docs/retrieval_input_quality_offline_audit_v0.4.9.2.md"),
            Path("tests/retrieval_input_quality_offline_audit_report.json"),
        ]
        matches = []
        for path in target_paths:
            if path.exists():
                content = path.read_text(encoding="utf-8-sig")
                matches.extend((str(path), pattern) for pattern in PROHIBITED_SOURCE_PATTERNS if pattern in content)
        self.assertEqual(matches, [])


if __name__ == "__main__":
    unittest.main()
