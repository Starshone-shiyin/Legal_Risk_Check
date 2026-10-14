import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_ingestion_metadata_patch_post_patch_rebuild_dry_run_design import (
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_SOURCE_PATCH_REPORT_PATH,
    build_report,
    render_markdown,
    source_patch_blockers,
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class IngestionMetadataPatchPostPatchRebuildDryRunDesignTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(
            DEFAULT_SOURCE_PATCH_REPORT_PATH,
            legacy_report_path("ingestion_metadata_source_patch_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("ingestion_metadata_patch_post_patch_rebuild_dry_run_design_report.json"),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/ingestion_metadata_patch_post_patch_rebuild_dry_run_design_v0.4.13.9.md"),
        )

    def test_real_source_patch_report_builds_design(self):
        report = build_report()
        summary = report["summary"]

        self.assertEqual(report["version"], "0.4.13.9")
        self.assertEqual(report["schema_kind"], "ingestion_metadata_patch_post_patch_rebuild_dry_run_design")
        self.assertEqual(summary["status"], "ready_for_post_patch_rebuild_dry_run_design_gate")
        self.assertEqual(summary["allowed_next_step"], "post_patch_rebuild_dry_run_design_gate")
        self.assertFalse(summary["implementation_allowed"])
        self.assertFalse(summary["runner_creation_allowed"])
        self.assertFalse(summary["qdrant_write_allowed"])
        self.assertFalse(summary["rebuild_allowed"])
        self.assertEqual(summary["full_eval"], "not_run")

    def test_source_patch_report_drift_blocks_design(self):
        source_patch = copy.deepcopy(load_json(DEFAULT_SOURCE_PATCH_REPORT_PATH))
        source_patch["summary"]["allowed_next_step"] = "rebuild_now"

        blockers = source_patch_blockers(source_patch)

        self.assertIn("unexpected_source_patch_next_step", blockers)

    def test_gate_status_or_version_drift_blocks_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            source_patch = copy.deepcopy(load_json(DEFAULT_SOURCE_PATCH_REPORT_PATH))
            source_patch["version"] = "0.4.13.7"
            source_patch["summary"]["status"] = "failed"
            source_patch_path = tmp / "source_patch.json"
            write_json(source_patch_path, source_patch)

            report = build_report(source_patch_path)

        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("source_patch_report_version_mismatch", report["summary"]["blockers"])
        self.assertIn("source_patch_report_not_passed", report["summary"]["blockers"])

    def test_guardrails_do_not_authorize_rebuild_or_runtime_changes(self):
        report = build_report()
        guardrails = report["guardrails"]
        handoff = report["handoff"]

        self.assertTrue(guardrails["design_only"])
        self.assertEqual(guardrails["qdrant_write"], "disallowed")
        self.assertEqual(guardrails["collection_rebuild"], "disallowed")
        self.assertEqual(guardrails["rag_query_integration"], "disallowed")
        self.assertEqual(guardrails["embedding_call"], "disallowed")
        self.assertEqual(guardrails["llm_access"], "disallowed")
        self.assertEqual(guardrails["full_eval"], "not_run")
        self.assertIn("write Qdrant", handoff["not_allowed_yet"])
        self.assertIn("rebuild collection", handoff["not_allowed_yet"])

    def test_design_defines_future_runner_contract_without_creating_runner(self):
        design = build_report()["dry_run_design"]
        output_contract = build_report()["output_contract"]

        self.assertEqual(design["future_runner_name"], "run_ingestion_metadata_patch_post_patch_rebuild_dry_run.py")
        self.assertEqual(design["runner_status"], "not_created_in_this_version")
        self.assertIn("Qdrant collection rebuild", design["forbidden_inputs"])
        self.assertIn("chunk_index", design["comparison_fields"]["must_be_present_after_patch"])
        self.assertIn("qdrant_point_id", design["comparison_fields"]["expected_to_change_if_rebuild_materializes"])
        self.assertIn("content_drift", design["forbidden_drift"])
        self.assertIn("row_fields", output_contract)
        self.assertIn("blocking_conditions", output_contract)

    def test_markdown_keeps_design_only_boundary(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.13.9 补丁后 rebuild dry-run 设计", markdown)
        self.assertIn("不写入 Qdrant", markdown)
        self.assertIn("是否允许创建 runner", markdown)
        self.assertIn("仍不允许", markdown)


if __name__ == "__main__":
    unittest.main()
