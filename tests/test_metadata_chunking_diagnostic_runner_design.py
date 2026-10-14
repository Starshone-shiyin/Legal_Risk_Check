import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_metadata_chunking_diagnostic_runner_design import (
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_SPEC_GATE_REPORT_PATH,
    DEFAULT_SPEC_REPORT_PATH,
    EXPECTED_DESIGN_ROW_ORDER,
    FAILURE_BUCKETS,
    OUTPUT_FIELD_CONTRACT,
    PROHIBITED_ACTIONS,
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


def build_with_sources(spec_gate: dict, spec: dict | None = None) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        gate_path = Path(tmpdir) / "gate.json"
        spec_path = Path(tmpdir) / "spec.json"
        write_json(gate_path, copy.deepcopy(spec_gate))
        write_json(spec_path, copy.deepcopy(spec if spec is not None else load_json("tests/metadata_chunking_diagnostic_spec_report.json")))
        return build_report(gate_path, spec_path)


class MetadataChunkingDiagnosticRunnerDesignTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(DEFAULT_SPEC_GATE_REPORT_PATH, legacy_report_path("metadata_chunking_diagnostic_spec_gate_report.json"))
        self.assertEqual(DEFAULT_SPEC_REPORT_PATH, legacy_report_path("metadata_chunking_diagnostic_spec_report.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("metadata_chunking_diagnostic_runner_design_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/metadata_chunking_diagnostic_runner_design_v0.4.9.8.md"))

    def test_real_sources_build_runner_design(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.9.8")
        self.assertEqual(report["schema_kind"], "metadata_chunking_diagnostic_runner_design")
        self.assertEqual(report["runner_design_gate"]["status"], "ready_for_metadata_chunking_diagnostic_runner_gate")
        self.assertEqual(report["runner_design_gate"]["allowed_next_step"], "metadata_chunking_diagnostic_runner_design_gate")
        self.assertEqual(report["runner_design_gate"]["diagnostic_run"], "not_run")
        self.assertFalse(report["runner_design_gate"]["implementation_allowed"])
        self.assertFalse(report["runner_design_gate"]["code_patch_authorized"])
        self.assertFalse(report["runner_design_gate"]["retrieval_logic_change_allowed"])
        self.assertEqual(report["runner_design_gate"]["blockers"], [])
        self.assertEqual(report["summary"]["design_row_count"], 5)
        self.assertEqual(report["summary"]["design_row_order"], EXPECTED_DESIGN_ROW_ORDER)
        self.assertEqual(report["runner_output_contract"]["required_fields"], OUTPUT_FIELD_CONTRACT)
        self.assertEqual(report["runner_output_contract"]["failure_buckets"], FAILURE_BUCKETS)
        self.assertEqual(report["prohibited_actions"], PROHIBITED_ACTIONS)
        self.assertTrue(all(row["status"] == "ready_for_future_read_only_runner" for row in report["design_rows"]))
        self.assertTrue(all(item["status"] == "passed" for item in report["assertions"]))

    def test_spec_gate_version_drift_blocks_design(self):
        gate = load_json("tests/metadata_chunking_diagnostic_spec_gate_report.json")
        gate["version"] = "0.4.9.6"

        report = build_with_sources(gate)

        self.assertEqual(report["runner_design_gate"]["status"], "blocked")
        self.assertIn("spec_gate_version_mismatch", report["runner_design_gate"]["blockers"])

    def test_spec_gate_not_open_blocks_design(self):
        gate = load_json("tests/metadata_chunking_diagnostic_spec_gate_report.json")
        gate["gate"]["status"] = "blocked"
        gate["summary"]["failed_check_count"] = 1

        report = build_with_sources(gate)

        self.assertEqual(report["runner_design_gate"]["status"], "blocked")
        self.assertIn("spec_gate_not_open_for_runner_design", report["runner_design_gate"]["blockers"])
        self.assertIn("spec_gate_failed_checks_present", report["runner_design_gate"]["blockers"])

    def test_spec_version_drift_blocks_design(self):
        gate = load_json("tests/metadata_chunking_diagnostic_spec_gate_report.json")
        spec = load_json("tests/metadata_chunking_diagnostic_spec_report.json")
        spec["version"] = "0.4.9.5"

        report = build_with_sources(gate, spec)

        self.assertEqual(report["runner_design_gate"]["status"], "blocked")
        self.assertIn("spec_version_mismatch", report["runner_design_gate"]["blockers"])

    def test_spec_row_order_drift_blocks_design(self):
        gate = load_json("tests/metadata_chunking_diagnostic_spec_gate_report.json")
        spec = load_json("tests/metadata_chunking_diagnostic_spec_report.json")
        spec["spec_rows"] = list(reversed(spec["spec_rows"]))

        report = build_with_sources(gate, spec)

        self.assertEqual(report["runner_design_gate"]["status"], "blocked")
        self.assertIn("design_row_order_preserved", report["runner_design_gate"]["blockers"])

    def test_runtime_pollution_blocks_design(self):
        gate = load_json("tests/metadata_chunking_diagnostic_spec_gate_report.json")
        gate["gate"]["implementation_allowed"] = True

        report = build_with_sources(gate)

        self.assertEqual(report["runner_design_gate"]["status"], "blocked")
        self.assertIn("spec_gate_runtime_boundary_drift", report["runner_design_gate"]["blockers"])

    def test_markdown_and_tool_are_non_runtime(self):
        markdown = render_markdown(build_report())
        self.assertIn("v0.4.9.8 Metadata/Chunking Diagnostic Runner Design", markdown)
        self.assertIn("This is a runner design only", markdown)
        self.assertIn("metadata_completeness_status", markdown)

        target_paths = [
            Path("tools/build_metadata_chunking_diagnostic_runner_design.py"),
            Path("docs/metadata_chunking_diagnostic_runner_design_v0.4.9.8.md"),
            Path("tests/metadata_chunking_diagnostic_runner_design_report.json"),
        ]
        matches = []
        for path in target_paths:
            if path.exists():
                content = path.read_text(encoding="utf-8-sig")
                matches.extend((str(path), pattern) for pattern in PROHIBITED_SOURCE_PATTERNS if pattern in content)
        self.assertEqual(matches, [])


if __name__ == "__main__":
    unittest.main()
