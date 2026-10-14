import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.check_metadata_chunking_diagnostic_runner_design_gate import (
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_RUNNER_DESIGN_REPORT_PATH,
    EXPECTED_SOURCE_REPORTS,
    build_report,
    render_markdown,
)
from tools.build_metadata_chunking_diagnostic_runner_design import (
    EXPECTED_DESIGN_ROW_ORDER,
    FAILURE_BUCKETS,
    OUTPUT_FIELD_CONTRACT,
    PROHIBITED_ACTIONS,
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


def build_with_design(design: dict) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "design.json"
        write_json(path, copy.deepcopy(design))
        return build_report(path)


class MetadataChunkingDiagnosticRunnerDesignGateTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(
            DEFAULT_RUNNER_DESIGN_REPORT_PATH,
            legacy_report_path("metadata_chunking_diagnostic_runner_design_report.json"),
        )
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("metadata_chunking_diagnostic_runner_design_gate_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/metadata_chunking_diagnostic_runner_design_gate_v0.4.9.9.md"))

    def test_real_runner_design_report_passes_gate(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.9.9")
        self.assertEqual(report["schema_kind"], "metadata_chunking_diagnostic_runner_design_gate")
        self.assertEqual(report["gate"]["status"], "open_for_metadata_chunking_diagnostic_dry_run_contract")
        self.assertEqual(report["gate"]["allowed_next_step"], "metadata_chunking_diagnostic_dry_run_contract")
        self.assertEqual(report["gate"]["diagnostic_run"], "not_run")
        self.assertFalse(report["gate"]["implementation_allowed"])
        self.assertFalse(report["gate"]["code_patch_authorized"])
        self.assertFalse(report["gate"]["retrieval_logic_change_allowed"])
        self.assertEqual(report["gate"]["blockers"], [])
        self.assertEqual(report["summary"]["failed_check_count"], 0)
        self.assertEqual(report["summary"]["design_row_count"], 5)
        self.assertEqual(report["summary"]["design_row_order"], EXPECTED_DESIGN_ROW_ORDER)
        self.assertEqual(report["summary"]["output_field_count"], len(OUTPUT_FIELD_CONTRACT))
        self.assertEqual(report["summary"]["failure_bucket_count"], len(FAILURE_BUCKETS))
        self.assertEqual(report["summary"]["source_prohibited_actions"], PROHIBITED_ACTIONS)
        self.assertTrue(all(check["status"] == "passed" for check in report["checks"]))

    def test_source_version_drift_blocks_gate(self):
        design = load_json("tests/metadata_chunking_diagnostic_runner_design_report.json")
        design["version"] = "0.4.9.7"

        report = build_with_design(design)

        self.assertEqual(report["gate"]["status"], "blocked")
        self.assertIn("runner_design_version", report["gate"]["blockers"])

    def test_design_row_order_drift_blocks_gate(self):
        design = load_json("tests/metadata_chunking_diagnostic_runner_design_report.json")
        design["design_rows"] = list(reversed(design["design_rows"]))

        report = build_with_design(design)

        self.assertEqual(report["gate"]["status"], "blocked")
        self.assertIn("design_row_count_and_order", report["gate"]["blockers"])

    def test_output_contract_drift_blocks_gate(self):
        design = load_json("tests/metadata_chunking_diagnostic_runner_design_report.json")
        design["runner_output_contract"]["required_fields"].remove("article_locator_status")

        report = build_with_design(design)

        self.assertEqual(report["gate"]["status"], "blocked")
        self.assertIn("output_contract_stable", report["gate"]["blockers"])

    def test_failure_bucket_drift_blocks_gate(self):
        design = load_json("tests/metadata_chunking_diagnostic_runner_design_report.json")
        design["runner_output_contract"]["failure_buckets"].append("runtime_fix_needed")

        report = build_with_design(design)

        self.assertEqual(report["gate"]["status"], "blocked")
        self.assertIn("failure_buckets_stable", report["gate"]["blockers"])

    def test_prohibited_actions_drift_blocks_gate(self):
        design = load_json("tests/metadata_chunking_diagnostic_runner_design_report.json")
        design["prohibited_actions"].append("run_qdrant_patch")

        report = build_with_design(design)

        self.assertEqual(report["gate"]["status"], "blocked")
        self.assertIn("prohibited_actions_stable", report["gate"]["blockers"])

    def test_source_report_drift_blocks_gate(self):
        design = load_json("tests/metadata_chunking_diagnostic_runner_design_report.json")
        design["runner_input_contract"]["saved_reports"] = EXPECTED_SOURCE_REPORTS[:1]

        report = build_with_design(design)

        self.assertEqual(report["gate"]["status"], "blocked")
        self.assertIn("source_reports_stable", report["gate"]["blockers"])

    def test_runtime_pollution_blocks_gate(self):
        design = load_json("tests/metadata_chunking_diagnostic_runner_design_report.json")
        design["guardrails"]["qdrant_access"] = "allowed"
        design["design_rows"][0]["implementation_allowed"] = True

        report = build_with_design(design)

        self.assertEqual(report["gate"]["status"], "blocked")
        self.assertIn("guardrails_stable", report["gate"]["blockers"])
        self.assertIn("row_boundaries_stable", report["gate"]["blockers"])

    def test_markdown_and_tool_are_non_runtime(self):
        markdown = render_markdown(build_report())
        self.assertIn("v0.4.9.9 Metadata/Chunking Diagnostic Runner Design Gate", markdown)
        self.assertIn("Next allowed step: `metadata_chunking_diagnostic_dry_run_contract`", markdown)
        self.assertIn("does not run diagnostics", markdown)

        target_paths = [
            Path("tools/check_metadata_chunking_diagnostic_runner_design_gate.py"),
            Path("docs/metadata_chunking_diagnostic_runner_design_gate_v0.4.9.9.md"),
            Path("tests/metadata_chunking_diagnostic_runner_design_gate_report.json"),
        ]
        matches = []
        for path in target_paths:
            if path.exists():
                content = path.read_text(encoding="utf-8-sig")
                matches.extend((str(path), pattern) for pattern in PROHIBITED_SOURCE_PATTERNS if pattern in content)
        self.assertEqual(matches, [])


if __name__ == "__main__":
    unittest.main()
