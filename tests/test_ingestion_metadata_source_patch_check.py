import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.check_ingestion_metadata_source_patch import (
    DEFAULT_GATE_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    build_checks,
    build_report,
    render_markdown,
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class IngestionMetadataSourcePatchCheckTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(DEFAULT_GATE_PATH, legacy_report_path("ingestion_metadata_patch_actual_design_gate_report.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("ingestion_metadata_source_patch_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/ingestion_metadata_source_patch_v0.4.13.8.md"))

    def test_real_patch_report_passes(self):
        report = build_report()
        summary = report["summary"]

        self.assertEqual(report["version"], "0.4.13.8")
        self.assertEqual(report["schema_kind"], "ingestion_metadata_source_patch_check")
        self.assertEqual(summary["status"], "passed")
        self.assertEqual(summary["failed_check_count"], 0)
        self.assertEqual(summary["allowed_next_step"], "post_patch_rebuild_dry_run_design")
        self.assertFalse(summary["qdrant_write_allowed"])
        self.assertFalse(summary["rebuild_allowed"])

    def test_parent_chunk_drift_fails(self):
        gate = load_json(DEFAULT_GATE_PATH)
        observations = build_report()["observations"]
        observations["parent"]["chunk_count"] = 2
        checks = build_checks(gate, observations)

        failed = {check["id"] for check in checks if not check["passed"]}
        self.assertIn("parent_chunk_count", failed)

    def test_child_order_drift_fails(self):
        gate = load_json(DEFAULT_GATE_PATH)
        observations = build_report()["observations"]
        observations["children"][1]["chunk_index"] = 3
        checks = build_checks(gate, observations)

        failed = {check["id"] for check in checks if not check["passed"]}
        self.assertIn("child_chunk_indexes", failed)

    def test_standard_section_drift_fails(self):
        gate = load_json(DEFAULT_GATE_PATH)
        observations = build_report()["observations"]
        observations["standard_section"]["heading_has_chunk_index"] = True
        checks = build_checks(gate, observations)

        failed = {check["id"] for check in checks if not check["passed"]}
        self.assertIn("standard_heading_unchanged", failed)

    def test_gate_failure_blocks_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            gate = copy.deepcopy(load_json(DEFAULT_GATE_PATH))
            gate["summary"]["status"] = "failed"
            gate_path = tmp / "gate.json"
            write_json(gate_path, gate)

            report = build_report(gate_path)

        self.assertEqual(report["summary"]["status"], "failed")
        failed = {check["id"] for check in report["failed_checks"]}
        self.assertIn("gate_status", failed)

    def test_markdown_contains_boundary(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.13.8 入库元数据源码补丁", markdown)
        self.assertIn("不写入 Qdrant", markdown)
        self.assertIn("允许的下一步", markdown)


if __name__ == "__main__":
    unittest.main()
