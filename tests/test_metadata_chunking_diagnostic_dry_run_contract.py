import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_metadata_chunking_diagnostic_dry_run_contract import (
    CONTRACT_ROW_ORDER,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_RUNNER_DESIGN_GATE_REPORT_PATH,
    DEFAULT_RUNNER_DESIGN_REPORT_PATH,
    DRY_RUN_OUTPUT_FIELDS,
    PROHIBITED_ACTIONS,
    build_report,
    render_markdown,
)
from tools.build_metadata_chunking_diagnostic_runner_design import FAILURE_BUCKETS, OUTPUT_FIELD_CONTRACT


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


def build_with_sources(design_gate: dict, design: dict | None = None) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        gate_path = Path(tmpdir) / "design_gate.json"
        design_path = Path(tmpdir) / "design.json"
        write_json(gate_path, copy.deepcopy(design_gate))
        write_json(design_path, copy.deepcopy(design if design is not None else load_json("tests/metadata_chunking_diagnostic_runner_design_report.json")))
        return build_report(gate_path, design_path)


class MetadataChunkingDiagnosticDryRunContractTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(
            DEFAULT_RUNNER_DESIGN_GATE_REPORT_PATH,
            legacy_report_path("metadata_chunking_diagnostic_runner_design_gate_report.json"),
        )
        self.assertEqual(DEFAULT_RUNNER_DESIGN_REPORT_PATH, legacy_report_path("metadata_chunking_diagnostic_runner_design_report.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("metadata_chunking_diagnostic_dry_run_contract_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/metadata_chunking_diagnostic_dry_run_contract_v0.4.9.10.md"))

    def test_real_sources_build_contract(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.9.10")
        self.assertEqual(report["schema_kind"], "metadata_chunking_diagnostic_dry_run_contract")
        self.assertEqual(report["contract_gate"]["status"], "ready_for_v0_4_9_series_closeout")
        self.assertEqual(report["contract_gate"]["allowed_next_step"], "v0_4_9_series_closeout")
        self.assertFalse(report["contract_gate"]["runner_implemented"])
        self.assertEqual(report["contract_gate"]["diagnostic_run"], "not_run")
        self.assertFalse(report["contract_gate"]["implementation_allowed"])
        self.assertFalse(report["contract_gate"]["code_patch_authorized"])
        self.assertFalse(report["contract_gate"]["retrieval_logic_change_allowed"])
        self.assertEqual(report["contract_gate"]["blockers"], [])
        self.assertEqual(report["summary"]["contract_row_count"], 5)
        self.assertEqual(report["summary"]["contract_row_order"], CONTRACT_ROW_ORDER)
        self.assertEqual(report["dry_run_output_contract"]["required_fields"], DRY_RUN_OUTPUT_FIELDS)
        self.assertEqual(report["dry_run_output_contract"]["failure_buckets"], FAILURE_BUCKETS)
        self.assertEqual(report["prohibited_actions"], PROHIBITED_ACTIONS)
        self.assertTrue(all(field in DRY_RUN_OUTPUT_FIELDS for field in OUTPUT_FIELD_CONTRACT))
        self.assertTrue(all(row["status"] == "ready_for_future_dry_run_runner" for row in report["contract_rows"]))
        self.assertTrue(all(item["status"] == "passed" for item in report["assertions"]))

    def test_design_gate_version_drift_blocks_contract(self):
        gate = load_json("tests/metadata_chunking_diagnostic_runner_design_gate_report.json")
        gate["version"] = "0.4.9.8"

        report = build_with_sources(gate)

        self.assertEqual(report["contract_gate"]["status"], "blocked")
        self.assertIn("design_gate_version_mismatch", report["contract_gate"]["blockers"])

    def test_design_gate_not_open_blocks_contract(self):
        gate = load_json("tests/metadata_chunking_diagnostic_runner_design_gate_report.json")
        gate["gate"]["status"] = "blocked"
        gate["summary"]["failed_check_count"] = 1

        report = build_with_sources(gate)

        self.assertEqual(report["contract_gate"]["status"], "blocked")
        self.assertIn("design_gate_not_open_for_dry_run_contract", report["contract_gate"]["blockers"])
        self.assertIn("design_gate_failed_checks_present", report["contract_gate"]["blockers"])

    def test_runner_design_version_drift_blocks_contract(self):
        gate = load_json("tests/metadata_chunking_diagnostic_runner_design_gate_report.json")
        design = load_json("tests/metadata_chunking_diagnostic_runner_design_report.json")
        design["version"] = "0.4.9.7"

        report = build_with_sources(gate, design)

        self.assertEqual(report["contract_gate"]["status"], "blocked")
        self.assertIn("runner_design_version_mismatch", report["contract_gate"]["blockers"])

    def test_runner_design_row_order_drift_blocks_contract(self):
        gate = load_json("tests/metadata_chunking_diagnostic_runner_design_gate_report.json")
        design = load_json("tests/metadata_chunking_diagnostic_runner_design_report.json")
        design["design_rows"] = list(reversed(design["design_rows"]))

        report = build_with_sources(gate, design)

        self.assertEqual(report["contract_gate"]["status"], "blocked")
        self.assertIn("runner_design_row_order_drift", report["contract_gate"]["blockers"])

    def test_runner_design_output_contract_drift_blocks_contract(self):
        gate = load_json("tests/metadata_chunking_diagnostic_runner_design_gate_report.json")
        design = load_json("tests/metadata_chunking_diagnostic_runner_design_report.json")
        design["runner_output_contract"]["required_fields"].remove("citation_identity_status")

        report = build_with_sources(gate, design)

        self.assertEqual(report["contract_gate"]["status"], "blocked")
        self.assertIn("runner_design_output_contract_drift", report["contract_gate"]["blockers"])

    def test_runtime_pollution_blocks_contract(self):
        gate = load_json("tests/metadata_chunking_diagnostic_runner_design_gate_report.json")
        gate["gate"]["implementation_allowed"] = True

        report = build_with_sources(gate)

        self.assertEqual(report["contract_gate"]["status"], "blocked")
        self.assertIn("design_gate_runtime_boundary_drift", report["contract_gate"]["blockers"])

    def test_markdown_and_tool_are_non_runtime(self):
        markdown = render_markdown(build_report())
        self.assertIn("v0.4.9.10 Metadata/Chunking Diagnostic Dry-Run Contract", markdown)
        self.assertIn("This is a dry-run contract only", markdown)
        self.assertIn("Runner implemented: False", markdown)

        target_paths = [
            Path("tools/build_metadata_chunking_diagnostic_dry_run_contract.py"),
            Path("docs/metadata_chunking_diagnostic_dry_run_contract_v0.4.9.10.md"),
            Path("tests/metadata_chunking_diagnostic_dry_run_contract_report.json"),
        ]
        matches = []
        for path in target_paths:
            if path.exists():
                content = path.read_text(encoding="utf-8-sig")
                matches.extend((str(path), pattern) for pattern in PROHIBITED_SOURCE_PATTERNS if pattern in content)
        self.assertEqual(matches, [])


if __name__ == "__main__":
    unittest.main()
