import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.check_retrieval_input_quality_diagnostic_prioritization_gate import (
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_PRIORITIZATION_REPORT_PATH,
    EXPECTED_ARTIFACT_ORDER,
    EXPECTED_ROUTE_ORDER,
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


def build_with_prioritization(prioritization: dict) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "prioritization.json"
        write_json(path, copy.deepcopy(prioritization))
        return build_report(path)


class RetrievalInputQualityDiagnosticPrioritizationGateTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(
            DEFAULT_PRIORITIZATION_REPORT_PATH,
            legacy_report_path("retrieval_input_quality_diagnostic_prioritization_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("retrieval_input_quality_diagnostic_prioritization_gate_report.json"),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/retrieval_input_quality_diagnostic_prioritization_gate_v0.4.9.5.md"),
        )

    def test_real_prioritization_report_passes_gate(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.9.5")
        self.assertEqual(report["schema_kind"], "retrieval_input_quality_diagnostic_prioritization_gate")
        self.assertEqual(report["gate"]["status"], "open_for_metadata_chunking_diagnostic_spec")
        self.assertEqual(report["gate"]["allowed_next_step"], "metadata_chunking_diagnostic_spec")
        self.assertFalse(report["gate"]["implementation_allowed"])
        self.assertFalse(report["gate"]["code_patch_authorized"])
        self.assertFalse(report["gate"]["retrieval_logic_change_allowed"])
        self.assertEqual(report["gate"]["blockers"], [])
        self.assertEqual(report["summary"]["failed_check_count"], 0)
        self.assertEqual(report["summary"]["priority_row_count"], 5)
        self.assertEqual(report["summary"]["route_order"], EXPECTED_ROUTE_ORDER)
        self.assertEqual(report["summary"]["recommended_artifact_order"], EXPECTED_ARTIFACT_ORDER)
        self.assertEqual(report["summary"]["severity_summary"], {"high": 3, "medium": 2})
        self.assertTrue(all(check["status"] == "passed" for check in report["checks"]))

    def test_source_version_drift_blocks_gate(self):
        prioritization = load_json("tests/retrieval_input_quality_diagnostic_prioritization_report.json")
        prioritization["version"] = "0.4.9.3"

        report = build_with_prioritization(prioritization)

        self.assertEqual(report["gate"]["status"], "blocked")
        self.assertIn("prioritization_version", report["gate"]["blockers"])

    def test_route_order_drift_blocks_gate(self):
        prioritization = load_json("tests/retrieval_input_quality_diagnostic_prioritization_report.json")
        prioritization["diagnostic_priority_rows"] = list(reversed(prioritization["diagnostic_priority_rows"]))

        report = build_with_prioritization(prioritization)

        self.assertEqual(report["gate"]["status"], "blocked")
        self.assertIn("priority_route_order", report["gate"]["blockers"])
        self.assertIn("priority_rank_order", report["gate"]["blockers"])

    def test_missing_required_field_blocks_gate(self):
        prioritization = load_json("tests/retrieval_input_quality_diagnostic_prioritization_report.json")
        del prioritization["diagnostic_priority_rows"][0]["entry_conditions"]

        report = build_with_prioritization(prioritization)

        self.assertEqual(report["gate"]["status"], "blocked")
        self.assertIn("required_row_fields", report["gate"]["blockers"])

    def test_row_content_gap_blocks_gate(self):
        prioritization = load_json("tests/retrieval_input_quality_diagnostic_prioritization_report.json")
        prioritization["diagnostic_priority_rows"][0]["entry_conditions"] = []
        prioritization["diagnostic_priority_rows"][1]["planning_status"] = "draft"

        report = build_with_prioritization(prioritization)

        self.assertEqual(report["gate"]["status"], "blocked")
        self.assertIn("row_content_complete", report["gate"]["blockers"])

    def test_runtime_change_pollution_blocks_gate(self):
        prioritization = load_json("tests/retrieval_input_quality_diagnostic_prioritization_report.json")
        prioritization["diagnostic_priority_rows"][0]["implementation_allowed"] = True
        prioritization["prioritization_gate"]["retrieval_logic_change_allowed"] = True

        report = build_with_prioritization(prioritization)

        self.assertEqual(report["gate"]["status"], "blocked")
        self.assertIn("row_runtime_changes_blocked", report["gate"]["blockers"])
        self.assertIn("gate_runtime_changes_blocked", report["gate"]["blockers"])

    def test_markdown_and_tool_are_non_runtime(self):
        markdown = render_markdown(build_report())
        self.assertIn("v0.4.9.5 Retrieval Input Quality Diagnostic Prioritization Gate", markdown)
        self.assertIn("First allowed artifact: `metadata_chunking_diagnostic_spec`", markdown)
        self.assertIn("Passing this gate only allows a metadata/chunking diagnostic specification", markdown)

        target_paths = [
            Path("tools/check_retrieval_input_quality_diagnostic_prioritization_gate.py"),
            Path("docs/retrieval_input_quality_diagnostic_prioritization_gate_v0.4.9.5.md"),
            Path("tests/retrieval_input_quality_diagnostic_prioritization_gate_report.json"),
        ]
        matches = []
        for path in target_paths:
            if path.exists():
                content = path.read_text(encoding="utf-8-sig")
                matches.extend((str(path), pattern) for pattern in PROHIBITED_SOURCE_PATTERNS if pattern in content)
        self.assertEqual(matches, [])


if __name__ == "__main__":
    unittest.main()
