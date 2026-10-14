import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools import build_retrieval_input_quality_series_closeout as closeout
from tools.build_retrieval_input_quality_series_closeout import (
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    SERIES_REPORTS,
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


class RetrievalInputQualitySeriesCloseoutTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("retrieval_input_quality_series_closeout_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/retrieval_input_quality_series_closeout_v0.4.9.11.md"))

    def test_real_sources_close_series(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.9.11")
        self.assertEqual(report["schema_kind"], "retrieval_input_quality_series_closeout")
        self.assertEqual(report["closeout_gate"]["status"], "v0_4_9_series_closed_for_diagnostic_governance")
        self.assertEqual(report["closeout_gate"]["allowed_next_step"], "v0.4.10.x read-only metadata/chunking diagnostic runner series")
        self.assertFalse(report["closeout_gate"]["diagnostic_runner_implemented"])
        self.assertEqual(report["closeout_gate"]["diagnostic_run"], "not_run")
        self.assertFalse(report["closeout_gate"]["implementation_allowed"])
        self.assertFalse(report["closeout_gate"]["code_patch_authorized"])
        self.assertFalse(report["closeout_gate"]["retrieval_logic_change_allowed"])
        self.assertEqual(report["closeout_gate"]["blockers"], [])
        self.assertEqual(report["summary"]["completed_step_count"], 11)
        self.assertEqual(report["summary"]["expected_step_count"], 11)
        self.assertEqual(report["summary"]["completed_versions"], [version for version, _, _, _ in SERIES_REPORTS])
        self.assertTrue(all(row["closeout_status"] == "passed" for row in report["series_rows"]))
        self.assertTrue(all(item["status"] == "passed" for item in report["assertions"]))

    def test_version_drift_blocks_closeout(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            patched = []
            for version, step, path, schema in SERIES_REPORTS:
                payload = copy.deepcopy(load_json(path))
                if step == "metadata_chunking_diagnostic_dry_run_contract":
                    payload["version"] = "0.4.9.9"
                target = tmp / path.name
                write_json(target, payload)
                patched.append((version, step, target, schema))
            original = closeout.SERIES_REPORTS
            closeout.SERIES_REPORTS = patched
            try:
                report = build_report()
            finally:
                closeout.SERIES_REPORTS = original

        self.assertEqual(report["closeout_gate"]["status"], "blocked")
        self.assertIn("metadata_chunking_diagnostic_dry_run_contract:version_mismatch", report["closeout_gate"]["blockers"])

    def test_missing_report_blocks_closeout(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            patched = []
            for version, step, path, schema in SERIES_REPORTS:
                target = tmp / path.name
                if step != "metadata_chunking_diagnostic_runner_design_gate":
                    write_json(target, load_json(path))
                patched.append((version, step, target, schema))
            original = closeout.SERIES_REPORTS
            closeout.SERIES_REPORTS = patched
            try:
                report = build_report()
            finally:
                closeout.SERIES_REPORTS = original

        self.assertEqual(report["closeout_gate"]["status"], "blocked")
        self.assertIn("metadata_chunking_diagnostic_runner_design_gate:missing_report", report["closeout_gate"]["blockers"])

    def test_markdown_and_tool_are_non_runtime(self):
        markdown = render_markdown(build_report())
        self.assertIn("v0.4.9.11 Retrieval Input Quality Series Closeout", markdown)
        self.assertIn("closed for offline governance, not runtime implementation", markdown)
        self.assertIn("Future diagnostic runner work needs a separately approved series", markdown)

        target_paths = [
            Path("tools/build_retrieval_input_quality_series_closeout.py"),
            Path("docs/retrieval_input_quality_series_closeout_v0.4.9.11.md"),
            Path("tests/retrieval_input_quality_series_closeout_report.json"),
        ]
        matches = []
        for path in target_paths:
            if path.exists():
                content = path.read_text(encoding="utf-8-sig")
                matches.extend((str(path), pattern) for pattern in PROHIBITED_SOURCE_PATTERNS if pattern in content)
        self.assertEqual(matches, [])


if __name__ == "__main__":
    unittest.main()
