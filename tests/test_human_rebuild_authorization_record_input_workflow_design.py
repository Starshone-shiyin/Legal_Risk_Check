import ast
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_human_rebuild_authorization_record_input_workflow_design import (
    DEFAULT_DRAFT_SCAFFOLD_GATE_PATH,
    DEFAULT_DRAFT_SCAFFOLD_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    FIELD_ORDER,
    WORKFLOW_PHASES,
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


class HumanRebuildAuthorizationRecordInputWorkflowDesignTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(
            DEFAULT_DRAFT_SCAFFOLD_PATH,
            legacy_report_path("human_rebuild_authorization_record_draft_scaffold_report.json"),
        )
        self.assertEqual(
            DEFAULT_DRAFT_SCAFFOLD_GATE_PATH,
            legacy_report_path("human_rebuild_authorization_record_draft_scaffold_gate_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("human_rebuild_authorization_record_input_workflow_design_report.json"),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/human_rebuild_authorization_record_input_workflow_design_v0.4.14.8.md"),
        )

    def test_real_inputs_build_workflow_design_only(self):
        report = build_report()
        summary = report["summary"]

        self.assertEqual(report["version"], "0.4.14.8")
        self.assertEqual(report["schema_kind"], "human_rebuild_authorization_record_input_workflow_design")
        self.assertEqual(summary["status"], "ready_for_human_rebuild_authorization_record_input_workflow_design_gate")
        self.assertEqual(summary["allowed_next_step"], "human_rebuild_authorization_record_input_workflow_design_gate")
        self.assertTrue(summary["input_workflow_design_only"])
        self.assertEqual(summary["workflow_phase_count"], len(WORKFLOW_PHASES))
        self.assertEqual(summary["field_input_contract_count"], 10)
        self.assertEqual(summary["human_value_count"], 0)
        self.assertFalse(summary["human_values_collected"])
        self.assertFalse(summary["input_form_created"])
        self.assertFalse(summary["input_values_imported"])
        self.assertFalse(summary["input_values_validated"])
        self.assertFalse(summary["draft_record_created"])
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

    def test_field_contracts_preserve_order_and_empty_values(self):
        contracts = build_report()["input_workflow_design"]["field_input_contracts"]

        self.assertEqual([row["field_id"] for row in contracts], FIELD_ORDER)
        for index, row in enumerate(contracts, start=1):
            self.assertEqual(row["input_sequence"], index)
            self.assertEqual(row["requirement"], "required")
            self.assertTrue(row["future_input_required"])
            self.assertEqual(row["current_value_status"], "not_collected")
            self.assertIsNone(row["current_human_value"])
            self.assertIsNone(row["current_normalized_value"])
            self.assertEqual(row["validation_status_now"], "not_run")
            self.assertEqual(row["authorization_effect_now"], "none")
            self.assertFalse(row["authorization_granted"])
            self.assertFalse(row["qdrant_write_allowed"])
            self.assertFalse(row["rebuild_allowed"])
            self.assertIsInstance(row["guidance_source"], str)
            self.assertTrue(row["guidance_source"])

    def test_workflow_phases_are_design_only(self):
        phases = build_report()["input_workflow_design"]["workflow_phases"]

        self.assertEqual([phase["sequence"] for phase in phases], list(range(1, len(WORKFLOW_PHASES) + 1)))
        self.assertEqual(phases[-1]["phase_id"], "formal_record_candidate_handoff")
        for phase in phases:
            self.assertIn("future", phase["purpose"])
            self.assertNotEqual(phase["authorization_effect"], "granted")
            self.assertNotIn("executed", phase["input_value_effect"])

    def test_operator_approval_contract_is_future_only(self):
        row = next(
            row for row in build_report()["input_workflow_design"]["field_input_contracts"]
            if row["field_id"] == "operator_approval"
        )

        self.assertEqual(row["future_input_shape"], "future_explicit_yes_no_authorization")
        self.assertEqual(row["authorization_effect_now"], "none")
        self.assertFalse(row["authorization_granted"])

    def test_scaffold_or_gate_drift_blocks_design(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            scaffold = tmp / "scaffold.json"
            gate = tmp / "gate.json"
            scaffold_payload = copy.deepcopy(load_json(DEFAULT_DRAFT_SCAFFOLD_PATH))
            gate_payload = copy.deepcopy(load_json(DEFAULT_DRAFT_SCAFFOLD_GATE_PATH))
            scaffold_payload["summary"]["status"] = "authorized"
            scaffold_payload["summary"]["allowed_next_step"] = "live_preflight"
            gate_payload["summary"]["status"] = "failed"
            gate_payload["summary"]["failed_check_count"] = 1
            gate_payload["summary"]["allowed_next_step"] = "production_rebuild"
            write_json(scaffold, scaffold_payload)
            write_json(gate, gate_payload)

            report = build_report(scaffold, gate)

        blockers = set(report["summary"]["blockers"])
        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("draft_scaffold_status_mismatch", blockers)
        self.assertIn("draft_scaffold_next_step_mismatch", blockers)
        self.assertIn("draft_scaffold_gate_not_passed", blockers)
        self.assertIn("draft_scaffold_gate_failed_checks_present", blockers)
        self.assertIn("draft_scaffold_gate_next_step_mismatch", blockers)

    def test_values_or_permissions_drift_blocks_design(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            scaffold = tmp / "scaffold.json"
            gate = tmp / "gate.json"
            scaffold_payload = copy.deepcopy(load_json(DEFAULT_DRAFT_SCAFFOLD_PATH))
            scaffold_payload["summary"]["human_value_count"] = 1
            scaffold_payload["summary"]["human_values_collected"] = True
            scaffold_payload["summary"]["formal_authorization_record_created"] = True
            scaffold_payload["summary"]["authorization_granted"] = True
            scaffold_payload["summary"]["live_preflight_run"] = True
            scaffold_payload["summary"]["qdrant_write_allowed"] = True
            scaffold_payload["summary"]["rebuild_allowed"] = True
            write_json(scaffold, scaffold_payload)
            write_json(gate, load_json(DEFAULT_DRAFT_SCAFFOLD_GATE_PATH))

            report = build_report(scaffold, gate)

        blockers = set(report["summary"]["blockers"])
        self.assertIn("draft_scaffold_human_value_count_mismatch", blockers)
        self.assertIn("draft_scaffold_human_values_collected_mismatch", blockers)
        self.assertIn("draft_scaffold_formal_authorization_record_created_mismatch", blockers)
        self.assertIn("draft_scaffold_authorization_granted_mismatch", blockers)
        self.assertIn("draft_scaffold_live_preflight_run_mismatch", blockers)
        self.assertIn("draft_scaffold_qdrant_write_allowed_mismatch", blockers)
        self.assertIn("draft_scaffold_rebuild_allowed_mismatch", blockers)

    def test_row_or_section_drift_blocks_design(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            scaffold = tmp / "scaffold.json"
            gate = tmp / "gate.json"
            scaffold_payload = copy.deepcopy(load_json(DEFAULT_DRAFT_SCAFFOLD_PATH))
            scaffold_payload["draft_scaffold"]["rows"][0]["human_value"] = "prod_collection"
            scaffold_payload["draft_scaffold"]["sections"][0]["field_ids"] = []
            write_json(scaffold, scaffold_payload)
            write_json(gate, load_json(DEFAULT_DRAFT_SCAFFOLD_GATE_PATH))

            report = build_report(scaffold, gate)

        blockers = set(report["summary"]["blockers"])
        self.assertIn("draft_scaffold_row_contract_mismatch", blockers)
        self.assertIn("draft_scaffold_section_contract_mismatch", blockers)

    def test_forbidden_output_key_detector_is_generic(self):
        report = {"nested": [{"commands": []}, {"authorized_actions": ["write Qdrant"]}]}

        self.assertEqual(forbidden_output_keys(report), ["authorized_actions", "commands"])
        self.assertEqual(forbidden_output_keys(build_report()), [])

    def test_cli_output_matches_builder_shape_and_utf8_markdown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "input_workflow_design.json"
            summary = Path(tmpdir) / "input_workflow_design.md"
            subprocess.run(
                [
                    sys.executable,
                    "tools/build_human_rebuild_authorization_record_input_workflow_design.py",
                    "--draft-scaffold",
                    str(DEFAULT_DRAFT_SCAFFOLD_PATH),
                    "--draft-scaffold-gate",
                    str(DEFAULT_DRAFT_SCAFFOLD_GATE_PATH),
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
        self.assertIn("只设计未来人工输入、导入、校验和确认流程", cli_summary)
        self.assertIn("不创建或接受正式授权记录", cli_summary)
        self.assertIn("只允许进入 `human_rebuild_authorization_record_input_workflow_design_gate`", cli_summary)

    def test_source_has_no_runtime_service_imports_or_calls(self):
        source = Path("tools/build_human_rebuild_authorization_record_input_workflow_design.py").read_text(encoding="utf-8")
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

    def test_markdown_documents_workflow_design_boundary(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.14.8 Human Rebuild Authorization Record Input Workflow Design", markdown)
        self.assertIn("只设计未来人工输入、导入、校验和确认流程", markdown)
        self.assertIn("不收集人工值", markdown)
        self.assertIn("不创建或接受正式授权记录", markdown)
        self.assertIn("不访问或写入 Qdrant", markdown)
        self.assertIn("仍不代表已经允许填写真实人工值", markdown)
        for forbidden in ["authorized_actions", "ready_to_apply", "commands", "rebuild_steps"]:
            self.assertNotIn(forbidden, markdown)


if __name__ == "__main__":
    unittest.main()
