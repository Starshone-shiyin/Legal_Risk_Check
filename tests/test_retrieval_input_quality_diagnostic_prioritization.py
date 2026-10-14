import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_retrieval_input_quality_diagnostic_prioritization import (
    DEFAULT_GATE_REPORT_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OFFLINE_AUDIT_REPORT_PATH,
    DEFAULT_OUTPUT_PATH,
    EXPECTED_PRIORITY_ROUTE_ORDER,
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


def build_with_sources(gate: dict, audit: dict | None = None) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        gate_path = Path(tmpdir) / "gate.json"
        audit_path = Path(tmpdir) / "audit.json"
        write_json(gate_path, copy.deepcopy(gate))
        write_json(audit_path, copy.deepcopy(audit if audit is not None else load_json("tests/retrieval_input_quality_offline_audit_report.json")))
        return build_report(gate_path, audit_path)


class RetrievalInputQualityDiagnosticPrioritizationTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(
            DEFAULT_GATE_REPORT_PATH,
            legacy_report_path("retrieval_input_quality_offline_audit_gate_report.json"),
        )
        self.assertEqual(
            DEFAULT_OFFLINE_AUDIT_REPORT_PATH,
            legacy_report_path("retrieval_input_quality_offline_audit_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("retrieval_input_quality_diagnostic_prioritization_report.json"),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/retrieval_input_quality_diagnostic_prioritization_v0.4.9.4.md"),
        )

    def test_real_sources_build_prioritization(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.9.4")
        self.assertEqual(report["schema_kind"], "retrieval_input_quality_diagnostic_prioritization")
        self.assertEqual(report["prioritization_gate"]["status"], "ready_for_diagnostic_spec_design")
        self.assertEqual(report["prioritization_gate"]["allowed_next_step"], "retrieval_input_quality_diagnostic_spec_design")
        self.assertFalse(report["prioritization_gate"]["implementation_allowed"])
        self.assertFalse(report["prioritization_gate"]["code_patch_authorized"])
        self.assertFalse(report["prioritization_gate"]["retrieval_logic_change_allowed"])
        self.assertEqual(report["prioritization_gate"]["blockers"], [])
        self.assertEqual(report["summary"]["priority_row_count"], 5)
        self.assertEqual(report["summary"]["route_order"], EXPECTED_PRIORITY_ROUTE_ORDER)
        self.assertEqual(report["summary"]["top_route"], "metadata_chunking_diagnostic_report")
        self.assertEqual(report["summary"]["severity_summary"], {"high": 3, "medium": 2})

        rows = report["diagnostic_priority_rows"]
        self.assertEqual([row["route_id"] for row in rows], EXPECTED_PRIORITY_ROUTE_ORDER)
        self.assertEqual([row["priority_rank"] for row in rows], [1, 2, 3, 4, 5])
        self.assertEqual(rows[0]["bucket_id"], "metadata_chunking_quality")
        self.assertEqual(rows[1]["bucket_id"], "anchor_dependency_quality")
        for row in rows:
            self.assertGreater(row["impacted_case_count"], 0)
            self.assertTrue(row["entry_conditions"])
            self.assertTrue(row["prohibited_actions"])
            self.assertTrue(row["recommended_artifact"].endswith("_diagnostic_spec"))
            self.assertFalse(row["implementation_allowed"])
            self.assertFalse(row["retrieval_logic_change_allowed"])
        self.assertTrue(all(item["status"] == "passed" for item in report["assertions"]))

    def test_gate_version_drift_blocks_prioritization(self):
        gate = load_json("tests/retrieval_input_quality_offline_audit_gate_report.json")
        gate["version"] = "0.4.9.2"

        report = build_with_sources(gate)

        self.assertEqual(report["prioritization_gate"]["status"], "blocked")
        self.assertIn("gate_version_mismatch", report["prioritization_gate"]["blockers"])

    def test_gate_not_open_blocks_prioritization(self):
        gate = load_json("tests/retrieval_input_quality_offline_audit_gate_report.json")
        gate["gate"]["status"] = "blocked"
        gate["summary"]["failed_check_count"] = 1

        report = build_with_sources(gate)

        self.assertEqual(report["prioritization_gate"]["status"], "blocked")
        self.assertIn("gate_not_open_for_diagnostic_planning", report["prioritization_gate"]["blockers"])
        self.assertIn("gate_failed_checks_present", report["prioritization_gate"]["blockers"])

    def test_audit_route_drift_blocks_prioritization(self):
        gate = load_json("tests/retrieval_input_quality_offline_audit_gate_report.json")
        audit = load_json("tests/retrieval_input_quality_offline_audit_report.json")
        audit["offline_audit_rows"][0]["recommended_next_route"] = "unexpected_route"

        report = build_with_sources(gate, audit)

        self.assertEqual(report["prioritization_gate"]["status"], "blocked")
        self.assertIn("offline_audit_route_set_drift", report["prioritization_gate"]["blockers"])

    def test_audit_bucket_order_drift_blocks_prioritization(self):
        gate = load_json("tests/retrieval_input_quality_offline_audit_gate_report.json")
        audit = load_json("tests/retrieval_input_quality_offline_audit_report.json")
        audit["offline_audit_rows"] = list(reversed(audit["offline_audit_rows"]))

        report = build_with_sources(gate, audit)

        self.assertEqual(report["prioritization_gate"]["status"], "blocked")
        self.assertIn("offline_audit_bucket_order_drift", report["prioritization_gate"]["blockers"])

    def test_markdown_and_tool_are_non_runtime(self):
        markdown = render_markdown(build_report())
        self.assertIn("v0.4.9.4 Retrieval Input Quality Diagnostic Prioritization", markdown)
        self.assertIn("Top route: `metadata_chunking_diagnostic_report`", markdown)
        self.assertIn("This is diagnostic prioritization only", markdown)

        target_paths = [
            Path("tools/build_retrieval_input_quality_diagnostic_prioritization.py"),
            Path("docs/retrieval_input_quality_diagnostic_prioritization_v0.4.9.4.md"),
            Path("tests/retrieval_input_quality_diagnostic_prioritization_report.json"),
        ]
        matches = []
        for path in target_paths:
            if path.exists():
                content = path.read_text(encoding="utf-8-sig")
                matches.extend((str(path), pattern) for pattern in PROHIBITED_SOURCE_PATTERNS if pattern in content)
        self.assertEqual(matches, [])


if __name__ == "__main__":
    unittest.main()
