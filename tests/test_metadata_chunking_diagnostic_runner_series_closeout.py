import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools import build_metadata_chunking_diagnostic_runner_series_closeout as closeout
from tools.build_metadata_chunking_diagnostic_runner_series_closeout import (
    DEFAULT_GATE_PATH,
    DEFAULT_MANIFEST_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_RUNNER_PATH,
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


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class MetadataChunkingDiagnosticRunnerSeriesCloseoutTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(DEFAULT_MANIFEST_PATH, legacy_report_path("metadata_chunking_diagnostic_runner_manifest_report.json"))
        self.assertEqual(DEFAULT_RUNNER_PATH, legacy_report_path("metadata_chunking_diagnostic_saved_report_runner_report.json"))
        self.assertEqual(DEFAULT_GATE_PATH, legacy_report_path("metadata_chunking_diagnostic_saved_report_runner_gate_report.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("metadata_chunking_diagnostic_runner_series_closeout_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/metadata_chunking_diagnostic_runner_series_closeout_v0.4.10.3.md"))

    def test_real_sources_close_series(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.10.3")
        self.assertEqual(report["schema_kind"], "metadata_chunking_diagnostic_runner_series_closeout")
        self.assertEqual(report["closeout_gate"]["status"], "v0_4_10_series_closed_for_saved_report_diagnostic")
        self.assertEqual(report["closeout_gate"]["allowed_next_step"], "v0.4.11.x evidence-level metadata snapshot read-only diagnostic design")
        self.assertEqual(report["summary"]["completed_step_count"], 3)
        self.assertEqual(report["summary"]["expected_step_count"], 3)
        self.assertEqual(report["summary"]["manifest_item_count"], 40)
        self.assertEqual(report["summary"]["diagnostic_row_count"], 40)
        self.assertEqual(report["summary"]["blocked_row_count"], 0)
        self.assertFalse(report["summary"]["evidence_level_metadata_snapshot_read"])
        self.assertFalse(report["closeout_gate"]["implementation_allowed"])
        self.assertFalse(report["closeout_gate"]["code_patch_authorized"])
        self.assertFalse(report["closeout_gate"]["retrieval_logic_change_allowed"])
        self.assertEqual(report["closeout_gate"]["blockers"], [])
        self.assertTrue(all(row["closeout_status"] == "passed" for row in report["series_rows"]))
        self.assertTrue(all(item["status"] == "passed" for item in report["assertions"]))

    def test_version_drift_blocks_closeout(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            manifest = copy.deepcopy(load_json(DEFAULT_MANIFEST_PATH))
            runner = copy.deepcopy(load_json(DEFAULT_RUNNER_PATH))
            gate = copy.deepcopy(load_json(DEFAULT_GATE_PATH))
            gate["version"] = "0.4.10.1"
            manifest_path = tmp / "manifest.json"
            runner_path = tmp / "runner.json"
            gate_path = tmp / "gate.json"
            write_json(manifest_path, manifest)
            write_json(runner_path, runner)
            write_json(gate_path, gate)

            report = build_report(manifest_path, runner_path, gate_path)

        self.assertEqual(report["closeout_gate"]["status"], "blocked")
        self.assertIn("saved_report_runner_gate:version_mismatch", report["closeout_gate"]["blockers"])

    def test_snapshot_scope_drift_blocks_closeout(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            manifest = copy.deepcopy(load_json(DEFAULT_MANIFEST_PATH))
            runner = copy.deepcopy(load_json(DEFAULT_RUNNER_PATH))
            gate = copy.deepcopy(load_json(DEFAULT_GATE_PATH))
            runner["summary"]["evidence_level_metadata_snapshot_read"] = True
            manifest_path = tmp / "manifest.json"
            runner_path = tmp / "runner.json"
            gate_path = tmp / "gate.json"
            write_json(manifest_path, manifest)
            write_json(runner_path, runner)
            write_json(gate_path, gate)

            report = build_report(manifest_path, runner_path, gate_path)

        self.assertEqual(report["closeout_gate"]["status"], "blocked")
        self.assertIn("runner_snapshot_scope_drift", report["closeout_gate"]["blockers"])

    def test_matrix_drift_blocks_closeout(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            manifest = copy.deepcopy(load_json(DEFAULT_MANIFEST_PATH))
            runner = copy.deepcopy(load_json(DEFAULT_RUNNER_PATH))
            gate = copy.deepcopy(load_json(DEFAULT_GATE_PATH))
            runner["diagnostic_rows"][0]["check_group"] = "wrong_group"
            manifest_path = tmp / "manifest.json"
            runner_path = tmp / "runner.json"
            gate_path = tmp / "gate.json"
            write_json(manifest_path, manifest)
            write_json(runner_path, runner)
            write_json(gate_path, gate)

            report = build_report(manifest_path, runner_path, gate_path)

        self.assertEqual(report["closeout_gate"]["status"], "blocked")
        self.assertIn("manifest_runner_matrix_mismatch", report["closeout_gate"]["blockers"])

    def test_markdown_and_tool_are_non_runtime(self):
        markdown = render_markdown(build_report())
        self.assertIn("v0.4.10.3 Metadata/Chunking Diagnostic Runner Series Closeout", markdown)
        self.assertIn("validates saved-report runner readiness, not real evidence-level metadata quality", markdown)
        self.assertIn("Future evidence-level metadata snapshot work needs a separately approved read-only design series", markdown)

        target_paths = [
            Path("tools/build_metadata_chunking_diagnostic_runner_series_closeout.py"),
            Path("docs/metadata_chunking_diagnostic_runner_series_closeout_v0.4.10.3.md"),
            Path("tests/metadata_chunking_diagnostic_runner_series_closeout_report.json"),
        ]
        matches = []
        for path in target_paths:
            if path.exists():
                content = path.read_text(encoding="utf-8-sig")
                matches.extend((str(path), pattern) for pattern in PROHIBITED_SOURCE_PATTERNS if pattern in content)
        self.assertEqual(matches, [])


if __name__ == "__main__":
    unittest.main()
