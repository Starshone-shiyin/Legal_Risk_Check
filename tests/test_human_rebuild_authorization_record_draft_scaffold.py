import ast
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_human_rebuild_authorization_record_draft_scaffold import (
    DEFAULT_DRAFT_DESIGN_GATE_PATH,
    DEFAULT_DRAFT_DESIGN_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    FIELD_ORDER,
    SECTION_ORDER,
    build_report,
    forbidden_output_keys,
    render_markdown,
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def without_generated_at(payload: dict) -> dict:
    clone = copy.deepcopy(payload)
    clone.pop("generated_at", None)
    return clone


class HumanRebuildAuthorizationRecordDraftScaffoldTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(
            DEFAULT_DRAFT_DESIGN_PATH,
            legacy_report_path("human_rebuild_authorization_record_draft_design_report.json"),
        )
        self.assertEqual(
            DEFAULT_DRAFT_DESIGN_GATE_PATH,
            legacy_report_path("human_rebuild_authorization_record_draft_design_gate_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("human_rebuild_authorization_record_draft_scaffold_report.json"),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/human_rebuild_authorization_record_draft_scaffold_v0.4.14.6.md"),
        )

    def test_real_inputs_build_blank_draft_scaffold_only(self):
        report = build_report()
        summary = report["summary"]

        self.assertEqual(report["version"], "0.4.14.6")
        self.assertEqual(report["schema_kind"], "human_rebuild_authorization_record_draft_scaffold")
        self.assertEqual(summary["status"], "pending_human_rebuild_authorization_record_draft_scaffold_gate")
        self.assertEqual(summary["allowed_use"], "blank_draft_scaffold_only")
        self.assertEqual(summary["allowed_next_step"], "human_rebuild_authorization_record_draft_scaffold_gate")
        self.assertTrue(summary["draft_scaffold_only"])
        self.assertTrue(summary["draft_record_scaffold_created"])
        self.assertFalse(summary["draft_record_created"])
        self.assertEqual(summary["field_count"], 10)
        self.assertEqual(summary["section_count"], 7)
        self.assertEqual(summary["human_value_count"], 0)
        self.assertFalse(summary["human_values_collected"])
        self.assertFalse(summary["formal_authorization_record_created"])
        self.assertFalse(summary["human_authorization_record_created"])
        self.assertFalse(summary["human_authorization_record_accepted"])
        self.assertFalse(summary["authorization_granted"])
        self.assertFalse(summary["live_preflight_run"])
        self.assertFalse(summary["production_rebuild_executed"])
        self.assertFalse(summary["qdrant_write_allowed"])
        self.assertFalse(summary["rebuild_allowed"])
        self.assertEqual(summary["full_eval"], "not_run")
        self.assertEqual(summary["blockers"], [])

    def test_rows_preserve_design_order_and_empty_values(self):
        scaffold = build_report()["draft_scaffold"]
        rows = scaffold["rows"]

        self.assertEqual(scaffold["section_order"], SECTION_ORDER)
        self.assertEqual([row["field_id"] for row in rows], FIELD_ORDER)
        for index, row in enumerate(rows, start=1):
            self.assertEqual(row["fill_sequence"], index)
            self.assertEqual(row["requirement"], "required")
            self.assertTrue(row["future_human_input_required"])
            self.assertEqual(row["value_status"], "not_collected")
            self.assertIsNone(row["human_value"])
            self.assertIsNone(row["normalized_value"])
            self.assertEqual(row["review_status"], "pending_future_human_input")
            self.assertEqual(row["authorization_effect_now"], "none")
            self.assertFalse(row["authorization_granted"])
            self.assertFalse(row["qdrant_write_allowed"])
            self.assertFalse(row["rebuild_allowed"])
            self.assertFalse(row["captures_formal_authorization_outcome"])
            self.assertIsInstance(row["guidance"], str)
            self.assertTrue(row["guidance"])

    def test_sections_are_blank_and_match_field_order(self):
        sections = build_report()["draft_scaffold"]["sections"]

        self.assertEqual([section["section_id"] for section in sections], SECTION_ORDER)
        self.assertEqual(sections[0]["field_ids"], ["target_collection", "rebuild_scope"])
        self.assertEqual(sections[2]["field_ids"], [
            "expected_id_drift_acknowledgement",
            "abort_conditions_acknowledgement",
        ])
        for section in sections:
            self.assertEqual(section["value_collection"], "not_collected")
            self.assertEqual(section["authorization_effect"], "none")

    def test_operator_approval_row_is_future_only(self):
        row = next(row for row in build_report()["draft_scaffold"]["rows"] if row["field_id"] == "operator_approval")

        self.assertIn("does not grant current approval", row["guidance"])
        self.assertEqual(row["authorization_effect_now"], "none")
        self.assertFalse(row["authorization_granted"])

    def test_design_or_gate_drift_blocks_scaffold(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            design = tmp / "design.json"
            gate = tmp / "gate.json"
            design_payload = copy.deepcopy(load_json(DEFAULT_DRAFT_DESIGN_PATH))
            gate_payload = copy.deepcopy(load_json(DEFAULT_DRAFT_DESIGN_GATE_PATH))
            design_payload["summary"]["status"] = "authorized"
            design_payload["summary"]["allowed_next_step"] = "live_preflight"
            gate_payload["summary"]["status"] = "failed"
            gate_payload["summary"]["failed_check_count"] = 1
            gate_payload["summary"]["allowed_next_step"] = "production_rebuild"
            write_json(design, design_payload)
            write_json(gate, gate_payload)

            report = build_report(design, gate)

        blockers = set(report["summary"]["blockers"])
        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("draft_design_status_mismatch", blockers)
        self.assertIn("draft_design_next_step_mismatch", blockers)
        self.assertIn("draft_design_gate_not_passed", blockers)
        self.assertIn("draft_design_gate_failed_checks_present", blockers)
        self.assertIn("draft_design_gate_next_step_mismatch", blockers)

    def test_values_or_permissions_drift_blocks_scaffold(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            design = tmp / "design.json"
            gate = tmp / "gate.json"
            design_payload = copy.deepcopy(load_json(DEFAULT_DRAFT_DESIGN_PATH))
            design_payload["summary"]["human_value_count"] = 1
            design_payload["summary"]["human_values_collected"] = True
            design_payload["summary"]["formal_authorization_record_created"] = True
            design_payload["summary"]["authorization_granted"] = True
            design_payload["summary"]["live_preflight_run"] = True
            design_payload["summary"]["qdrant_write_allowed"] = True
            design_payload["summary"]["rebuild_allowed"] = True
            write_json(design, design_payload)
            write_json(gate, load_json(DEFAULT_DRAFT_DESIGN_GATE_PATH))

            report = build_report(design, gate)

        blockers = set(report["summary"]["blockers"])
        self.assertIn("draft_design_human_value_count_mismatch", blockers)
        self.assertIn("draft_design_human_values_collected_mismatch", blockers)
        self.assertIn("draft_design_formal_authorization_record_created_mismatch", blockers)
        self.assertIn("draft_design_authorization_granted_mismatch", blockers)
        self.assertIn("draft_design_live_preflight_run_mismatch", blockers)
        self.assertIn("draft_design_qdrant_write_allowed_mismatch", blockers)
        self.assertIn("draft_design_rebuild_allowed_mismatch", blockers)

    def test_section_or_field_mapping_drift_blocks_scaffold(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            design = tmp / "design.json"
            gate = tmp / "gate.json"
            design_payload = copy.deepcopy(load_json(DEFAULT_DRAFT_DESIGN_PATH))
            design_payload["draft_record_design"]["section_contract"][0]["fields"] = []
            design_payload["draft_record_design"]["field_mappings"][0]["value"] = "prod_collection"
            write_json(design, design_payload)
            write_json(gate, load_json(DEFAULT_DRAFT_DESIGN_GATE_PATH))

            report = build_report(design, gate)

        blockers = set(report["summary"]["blockers"])
        self.assertIn("draft_design_section_contract_mismatch", blockers)
        self.assertIn("draft_design_field_mapping_contract_mismatch", blockers)

    def test_forbidden_output_key_detector_is_generic(self):
        report = {"nested": [{"commands": []}, {"authorized_actions": ["write Qdrant"]}]}

        self.assertEqual(forbidden_output_keys(report), ["authorized_actions", "commands"])
        self.assertEqual(forbidden_output_keys(build_report()), [])

    def test_cli_output_matches_builder_shape_and_utf8_markdown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "draft_scaffold.json"
            summary = Path(tmpdir) / "draft_scaffold.md"
            subprocess.run(
                [
                    sys.executable,
                    "tools/build_human_rebuild_authorization_record_draft_scaffold.py",
                    "--draft-design",
                    str(DEFAULT_DRAFT_DESIGN_PATH),
                    "--draft-design-gate",
                    str(DEFAULT_DRAFT_DESIGN_GATE_PATH),
                    "--output",
                    str(output),
                    "--summary",
                    str(summary),
                ],
                check=True,
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
            )

            cli_report = load_json(output)
            cli_summary = summary.read_text(encoding="utf-8")

        self.assertEqual(without_generated_at(cli_report), without_generated_at(build_report()))
        self.assertIn("只生成未来正式授权记录的空白草案 scaffold", cli_summary)
        self.assertIn("不创建或接受正式授权记录", cli_summary)
        self.assertIn("只允许进入 `human_rebuild_authorization_record_draft_scaffold_gate`", cli_summary)

    def test_source_has_no_runtime_service_imports_or_calls(self):
        source = Path("tools/build_human_rebuild_authorization_record_draft_scaffold.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            if isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)

        forbidden_imports = {"qdrant_client", "openai", "src.rag.retriever", "src.rag.ingestion", "run_rag_eval"}
        self.assertTrue(forbidden_imports.isdisjoint(imports))
        for forbidden_call in ["rag_query(", "QdrantClient(", "OpenAI(", "run_eval("]:
            self.assertNotIn(forbidden_call, source)

    def test_markdown_documents_draft_scaffold_boundary(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.14.6 Human Rebuild Authorization Record Draft Scaffold", markdown)
        self.assertIn("只生成未来正式授权记录的空白草案 scaffold", markdown)
        self.assertIn("不收集人工值", markdown)
        self.assertIn("不创建或接受正式授权记录", markdown)
        self.assertIn("不访问或写入 Qdrant", markdown)
        self.assertIn("仍不代表已经允许填写真实人工值", markdown)
        for forbidden in ["authorized_actions", "ready_to_apply", "commands", "rebuild_steps"]:
            self.assertNotIn(forbidden, markdown)


if __name__ == "__main__":
    unittest.main()
