import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_metadata_chunking_diagnostic_spec import (
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_PRIORITIZATION_GATE_REPORT_PATH,
    DEFAULT_PRIORITIZATION_REPORT_PATH,
    PROHIBITED_ACTIONS,
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
    "rag_eval_cases.json",
]


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def build_with_sources(gate_report: dict, prioritization_report: dict | None = None) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        gate_path = Path(tmpdir) / "gate.json"
        prioritization_path = Path(tmpdir) / "prioritization.json"
        write_json(gate_path, copy.deepcopy(gate_report))
        write_json(
            prioritization_path,
            copy.deepcopy(
                prioritization_report
                if prioritization_report is not None
                else load_json("tests/retrieval_input_quality_diagnostic_prioritization_report.json")
            ),
        )
        return build_report(gate_path, prioritization_path)


class MetadataChunkingDiagnosticSpecTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(
            DEFAULT_PRIORITIZATION_GATE_REPORT_PATH,
            legacy_report_path("retrieval_input_quality_diagnostic_prioritization_gate_report.json"),
        )
        self.assertEqual(
            DEFAULT_PRIORITIZATION_REPORT_PATH,
            legacy_report_path("retrieval_input_quality_diagnostic_prioritization_report.json"),
        )
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("metadata_chunking_diagnostic_spec_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/metadata_chunking_diagnostic_spec_v0.4.9.6.md"))

    def test_real_sources_build_spec(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.9.6")
        self.assertEqual(report["schema_kind"], "metadata_chunking_diagnostic_spec")
        self.assertEqual(report["spec_gate"]["status"], "ready_for_future_metadata_chunking_diagnostic_runner")
        self.assertEqual(report["spec_gate"]["allowed_next_step"], "metadata_chunking_diagnostic_runner_design")
        self.assertTrue(report["spec_gate"]["diagnostic_not_run"])
        self.assertFalse(report["spec_gate"]["implementation_allowed"])
        self.assertFalse(report["spec_gate"]["code_patch_authorized"])
        self.assertFalse(report["spec_gate"]["retrieval_logic_change_allowed"])
        self.assertEqual(report["spec_gate"]["blockers"], [])
        self.assertEqual(report["summary"]["check_group_count"], 5)
        self.assertEqual(report["summary"]["sample_case_count"], 8)
        self.assertEqual(report["summary"]["impacted_case_count"], 33)
        self.assertEqual(report["summary"]["top_route"], "metadata_chunking_diagnostic_report")
        self.assertEqual(report["prohibited_actions"], PROHIBITED_ACTIONS)
        self.assertEqual(report["sample_case_scope"]["scope_limit"], "saved_report_samples_only")

        covered_fields = set(report["required_metadata_field_coverage"]["covered_by_spec"])
        for field in REQUIRED_METADATA_FIELDS:
            self.assertIn(field, covered_fields)
        for row in report["spec_rows"]:
            self.assertTrue(row["sample_case_ids"])
            self.assertTrue(row["evidence_signals"])
            self.assertTrue(row["diagnostic_only"])
            self.assertFalse(row["implementation_allowed"])
            self.assertFalse(row["code_patch_authorized"])
            self.assertFalse(row["retrieval_logic_change_allowed"])
        self.assertTrue(all(item["status"] == "passed" for item in report["assertions"]))

    def test_gate_version_drift_blocks_spec(self):
        gate = load_json("tests/retrieval_input_quality_diagnostic_prioritization_gate_report.json")
        gate["version"] = "0.4.9.4"

        report = build_with_sources(gate)

        self.assertEqual(report["spec_gate"]["status"], "blocked")
        self.assertIn("prioritization_gate_version_mismatch", report["spec_gate"]["blockers"])

    def test_gate_not_open_blocks_spec(self):
        gate = load_json("tests/retrieval_input_quality_diagnostic_prioritization_gate_report.json")
        gate["gate"]["status"] = "blocked"
        gate["summary"]["failed_check_count"] = 1

        report = build_with_sources(gate)

        self.assertEqual(report["spec_gate"]["status"], "blocked")
        self.assertIn("prioritization_gate_not_open_for_metadata_chunking_spec", report["spec_gate"]["blockers"])
        self.assertIn("prioritization_gate_failed_checks_present", report["spec_gate"]["blockers"])

    def test_top_route_drift_blocks_spec(self):
        gate = load_json("tests/retrieval_input_quality_diagnostic_prioritization_gate_report.json")
        prioritization = load_json("tests/retrieval_input_quality_diagnostic_prioritization_report.json")
        prioritization["summary"]["top_route"] = "query_lexical_coverage_diagnostic_report"

        report = build_with_sources(gate, prioritization)

        self.assertEqual(report["spec_gate"]["status"], "blocked")
        self.assertIn("metadata_chunking_not_top_route", report["spec_gate"]["blockers"])

    def test_recommended_artifact_drift_blocks_spec(self):
        gate = load_json("tests/retrieval_input_quality_diagnostic_prioritization_gate_report.json")
        prioritization = load_json("tests/retrieval_input_quality_diagnostic_prioritization_report.json")
        prioritization["diagnostic_priority_rows"][0]["recommended_artifact"] = "unexpected_spec"

        report = build_with_sources(gate, prioritization)

        self.assertEqual(report["spec_gate"]["status"], "blocked")
        self.assertIn("metadata_chunking_recommended_artifact_drift", report["spec_gate"]["blockers"])

    def test_runtime_pollution_blocks_spec(self):
        gate = load_json("tests/retrieval_input_quality_diagnostic_prioritization_gate_report.json")
        prioritization = load_json("tests/retrieval_input_quality_diagnostic_prioritization_report.json")
        prioritization["diagnostic_priority_rows"][0]["implementation_allowed"] = True

        report = build_with_sources(gate, prioritization)

        self.assertEqual(report["spec_gate"]["status"], "blocked")
        self.assertIn("metadata_chunking_row_runtime_boundary_drift", report["spec_gate"]["blockers"])

    def test_markdown_and_tool_are_non_runtime(self):
        markdown = render_markdown(build_report())
        self.assertIn("v0.4.9.6 Metadata/Chunking Diagnostic Spec", markdown)
        self.assertIn("Diagnostic not run: True", markdown)
        self.assertIn("merge chunks", markdown)

        target_paths = [
            Path("tools/build_metadata_chunking_diagnostic_spec.py"),
            Path("docs/metadata_chunking_diagnostic_spec_v0.4.9.6.md"),
            Path("tests/metadata_chunking_diagnostic_spec_report.json"),
        ]
        matches = []
        for path in target_paths:
            if path.exists():
                content = path.read_text(encoding="utf-8-sig")
                matches.extend((str(path), pattern) for pattern in PROHIBITED_SOURCE_PATTERNS if pattern in content)
        self.assertEqual(matches, [])


if __name__ == "__main__":
    unittest.main()
