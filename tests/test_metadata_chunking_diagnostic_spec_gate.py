import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.check_metadata_chunking_diagnostic_spec_gate import (
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_SPEC_REPORT_PATH,
    EXPECTED_PROHIBITED_ACTIONS,
    EXPECTED_REQUIRED_METADATA_FIELDS,
    EXPECTED_SPEC_ROW_ORDER,
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


def build_with_spec(spec: dict) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "spec.json"
        write_json(path, copy.deepcopy(spec))
        return build_report(path)


class MetadataChunkingDiagnosticSpecGateTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(
            DEFAULT_SPEC_REPORT_PATH,
            legacy_report_path("metadata_chunking_diagnostic_spec_report.json"),
        )
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("metadata_chunking_diagnostic_spec_gate_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/metadata_chunking_diagnostic_spec_gate_v0.4.9.7.md"))

    def test_real_spec_report_passes_gate(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.9.7")
        self.assertEqual(report["schema_kind"], "metadata_chunking_diagnostic_spec_gate")
        self.assertEqual(report["gate"]["status"], "open_for_metadata_chunking_diagnostic_runner_design")
        self.assertEqual(report["gate"]["allowed_next_step"], "metadata_chunking_diagnostic_runner_design")
        self.assertEqual(report["gate"]["diagnostic_run"], "not_run")
        self.assertFalse(report["gate"]["implementation_allowed"])
        self.assertFalse(report["gate"]["code_patch_authorized"])
        self.assertFalse(report["gate"]["retrieval_logic_change_allowed"])
        self.assertEqual(report["gate"]["blockers"], [])
        self.assertEqual(report["summary"]["failed_check_count"], 0)
        self.assertEqual(report["summary"]["spec_row_count"], 5)
        self.assertEqual(report["summary"]["spec_row_order"], EXPECTED_SPEC_ROW_ORDER)
        self.assertEqual(report["summary"]["source_sample_case_count"], 8)
        self.assertEqual(report["summary"]["source_required_metadata_fields"], EXPECTED_REQUIRED_METADATA_FIELDS)
        self.assertEqual(report["summary"]["source_prohibited_actions"], EXPECTED_PROHIBITED_ACTIONS)
        self.assertTrue(all(check["status"] == "passed" for check in report["checks"]))

    def test_source_version_drift_blocks_gate(self):
        spec = load_json("tests/metadata_chunking_diagnostic_spec_report.json")
        spec["version"] = "0.4.9.5"

        report = build_with_spec(spec)

        self.assertEqual(report["gate"]["status"], "blocked")
        self.assertIn("spec_version", report["gate"]["blockers"])

    def test_spec_row_order_drift_blocks_gate(self):
        spec = load_json("tests/metadata_chunking_diagnostic_spec_report.json")
        spec["spec_rows"] = list(reversed(spec["spec_rows"]))

        report = build_with_spec(spec)

        self.assertEqual(report["gate"]["status"], "blocked")
        self.assertIn("spec_row_count_and_order", report["gate"]["blockers"])

    def test_missing_required_metadata_field_blocks_gate(self):
        spec = load_json("tests/metadata_chunking_diagnostic_spec_report.json")
        spec["required_metadata_field_coverage"]["covered_by_spec"].remove("chunk_id")

        report = build_with_spec(spec)

        self.assertEqual(report["gate"]["status"], "blocked")
        self.assertIn("required_metadata_fields_covered", report["gate"]["blockers"])

    def test_sample_scope_gap_blocks_gate(self):
        spec = load_json("tests/metadata_chunking_diagnostic_spec_report.json")
        spec["sample_case_scope"]["case_ids"] = spec["sample_case_scope"]["case_ids"][:2]

        report = build_with_spec(spec)

        self.assertEqual(report["gate"]["status"], "blocked")
        self.assertIn("sample_scope_stable", report["gate"]["blockers"])

    def test_runtime_pollution_blocks_gate(self):
        spec = load_json("tests/metadata_chunking_diagnostic_spec_report.json")
        spec["spec_gate"]["implementation_allowed"] = True
        spec["spec_rows"][0]["retrieval_logic_change_allowed"] = True

        report = build_with_spec(spec)

        self.assertEqual(report["gate"]["status"], "blocked")
        self.assertIn("gate_runtime_changes_blocked", report["gate"]["blockers"])
        self.assertIn("row_runtime_changes_blocked", report["gate"]["blockers"])

    def test_prohibited_actions_drift_blocks_gate(self):
        spec = load_json("tests/metadata_chunking_diagnostic_spec_report.json")
        spec["prohibited_actions"].append("new_runtime_patch")

        report = build_with_spec(spec)

        self.assertEqual(report["gate"]["status"], "blocked")
        self.assertIn("prohibited_actions_stable", report["gate"]["blockers"])

    def test_markdown_and_tool_are_non_runtime(self):
        markdown = render_markdown(build_report())
        self.assertIn("v0.4.9.7 Metadata/Chunking Diagnostic Spec Gate", markdown)
        self.assertIn("Next allowed step: `metadata_chunking_diagnostic_runner_design`", markdown)
        self.assertIn("does not run diagnostics", markdown)

        target_paths = [
            Path("tools/check_metadata_chunking_diagnostic_spec_gate.py"),
            Path("docs/metadata_chunking_diagnostic_spec_gate_v0.4.9.7.md"),
            Path("tests/metadata_chunking_diagnostic_spec_gate_report.json"),
        ]
        matches = []
        for path in target_paths:
            if path.exists():
                content = path.read_text(encoding="utf-8-sig")
                matches.extend((str(path), pattern) for pattern in PROHIBITED_SOURCE_PATTERNS if pattern in content)
        self.assertEqual(matches, [])


if __name__ == "__main__":
    unittest.main()
