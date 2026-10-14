import ast
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_human_rebuild_authorization_record_input_form_scaffold import (
    DEFAULT_INPUT_PACKET_SCAFFOLD_GATE_PATH,
    DEFAULT_INPUT_PACKET_SCAFFOLD_PATH,
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


class HumanRebuildAuthorizationRecordInputFormScaffoldTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(
            DEFAULT_INPUT_PACKET_SCAFFOLD_PATH,
            legacy_report_path("human_rebuild_authorization_record_input_packet_scaffold_report.json"),
        )
        self.assertEqual(
            DEFAULT_INPUT_PACKET_SCAFFOLD_GATE_PATH,
            legacy_report_path("human_rebuild_authorization_record_input_packet_scaffold_gate_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("human_rebuild_authorization_record_input_form_scaffold_report.json"),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/human_rebuild_authorization_record_input_form_scaffold_v0.4.14.12.md"),
        )

    def test_real_inputs_build_blank_form_scaffold_only(self):
        report = build_report()
        summary = report["summary"]

        self.assertEqual(report["version"], "0.4.14.12")
        self.assertEqual(report["schema_kind"], "human_rebuild_authorization_record_input_form_scaffold")
        self.assertEqual(summary["status"], "ready_for_human_rebuild_authorization_record_input_form_scaffold_gate")
        self.assertEqual(summary["allowed_next_step"], "human_rebuild_authorization_record_input_form_scaffold_gate")
        self.assertTrue(summary["input_form_scaffold_only"])
        self.assertTrue(summary["blank_input_form_scaffold_created"])
        self.assertEqual(summary["form_field_count"], 10)
        self.assertEqual(summary["form_section_count"], 7)
        self.assertEqual(summary["human_value_count"], 0)
        self.assertFalse(summary["human_values_collected"])
        self.assertFalse(summary["runnable_input_form_created"])
        self.assertFalse(summary["input_form_created"])
        self.assertFalse(summary["input_importer_created"])
        self.assertFalse(summary["input_values_imported"])
        self.assertFalse(summary["input_values_validated"])
        self.assertFalse(summary["form_values_exported"])
        self.assertFalse(summary["form_values_accepted"])
        self.assertFalse(summary["formal_authorization_record_created"])
        self.assertFalse(summary["authorization_granted"])
        self.assertFalse(summary["live_preflight_run"])
        self.assertFalse(summary["qdrant_write_allowed"])
        self.assertFalse(summary["rebuild_allowed"])
        self.assertEqual(summary["full_eval"], "not_run")
        self.assertEqual(summary["blockers"], [])

    def test_form_sections_and_fields_preserve_packet_contract(self):
        scaffold = build_report()["input_form_scaffold"]
        fields = scaffold["fields"]

        self.assertEqual(scaffold["section_order"], SECTION_ORDER)
        self.assertEqual([section["section_id"] for section in scaffold["sections"]], SECTION_ORDER)
        self.assertEqual([field["field_id"] for field in fields], FIELD_ORDER)
        for section in scaffold["sections"]:
            self.assertTrue(section["label_zh"])
            self.assertTrue(section["field_ids"])
            self.assertEqual(section["value_collection"], "not_collected")
            self.assertEqual(section["interactive_form_effect"], "none")
            self.assertEqual(section["import_effect"], "none")
            self.assertEqual(section["authorization_effect"], "none")
        for index, field in enumerate(fields, start=1):
            self.assertEqual(field["form_field_id"], f"input_form_field_{index:02d}_{field['field_id']}")
            self.assertEqual(field["display_order"], index)
            self.assertEqual(field["input_sequence"], index)
            self.assertEqual(field["requirement"], "required")
            self.assertTrue(field["required"])
            self.assertTrue(field["label_zh"])
            self.assertTrue(field["help_text_zh"])
            self.assertTrue(field["future_editable"])
            self.assertFalse(field["editable_now"])
            self.assertFalse(field["interactive_control_created"])
            self.assertEqual(field["entry_status"], "blank")
            self.assertEqual(field["field_status"], "blank")
            self.assertEqual(field["value_status"], "not_collected")
            self.assertIsNone(field["human_value"])
            self.assertIsNone(field["normalized_value"])
            self.assertEqual(field["import_status"], "not_imported")
            self.assertEqual(field["validation_status_now"], "not_run")
            self.assertEqual(field["review_status"], "pending_future_human_input")
            self.assertEqual(field["authorization_effect_now"], "none")
            self.assertFalse(field["authorization_granted"])
            self.assertFalse(field["qdrant_write_allowed"])
            self.assertFalse(field["rebuild_allowed"])
            self.assertEqual(field["form_scaffold_status"], "ready_for_future_form_scaffold_gate")
            self.assertTrue(field["source_packet_row_id"])
            self.assertTrue(field["source_contract_id"])

    def test_form_policies_are_non_submitting_non_exporting_non_authorizing(self):
        scaffold = build_report()["input_form_scaffold"]

        self.assertEqual(scaffold["form_runtime_status"], "not_created")
        self.assertEqual(scaffold["form_submission_status"], "not_supported")
        self.assertEqual(scaffold["form_export_status"], "not_supported")
        self.assertEqual(scaffold["form_acceptance_status"], "not_accepted")
        self.assertEqual(scaffold["value_collection_status"], "not_collected")
        self.assertEqual(scaffold["form_completion_policy"]["current_form_submittable"], False)
        self.assertEqual(scaffold["form_completion_policy"]["current_form_authorization_effect"], "none")
        self.assertEqual(scaffold["future_form_export_policy"]["current_form_exportable"], False)
        self.assertEqual(scaffold["future_form_export_policy"]["current_form_importable"], False)
        self.assertEqual(scaffold["future_form_export_policy"]["current_form_authorization_effect"], "none")

    def test_operator_approval_is_future_only(self):
        field = next(field for field in build_report()["input_form_scaffold"]["fields"] if field["field_id"] == "operator_approval")

        self.assertEqual(field["future_input_shape"], "future_explicit_yes_no_authorization")
        self.assertEqual(field["future_widget_hint"], "future_yes_no_authorization_control")
        self.assertFalse(field["editable_now"])
        self.assertIsNone(field["human_value"])
        self.assertEqual(field["authorization_effect_now"], "none")
        self.assertFalse(field["authorization_granted"])

    def test_source_status_or_gate_drift_blocks_scaffold(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            packet_path = tmp / "packet.json"
            gate_path = tmp / "gate.json"
            packet = copy.deepcopy(load_json(DEFAULT_INPUT_PACKET_SCAFFOLD_PATH))
            gate = copy.deepcopy(load_json(DEFAULT_INPUT_PACKET_SCAFFOLD_GATE_PATH))
            packet["summary"]["status"] = "authorized"
            packet["summary"]["allowed_next_step"] = "live_preflight"
            gate["summary"]["status"] = "failed"
            gate["summary"]["failed_check_count"] = 1
            gate["summary"]["allowed_next_step"] = "production_rebuild"
            write_json(packet_path, packet)
            write_json(gate_path, gate)

            report = build_report(packet_path, gate_path)

        blockers = set(report["summary"]["blockers"])
        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("input_packet_scaffold_status_mismatch", blockers)
        self.assertIn("input_packet_scaffold_next_step_mismatch", blockers)
        self.assertIn("input_packet_scaffold_gate_not_passed", blockers)
        self.assertIn("input_packet_scaffold_gate_failed_checks_present", blockers)
        self.assertIn("input_packet_scaffold_gate_next_step_mismatch", blockers)

    def test_source_values_or_permissions_drift_blocks_scaffold(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            packet_path = tmp / "packet.json"
            gate_path = tmp / "gate.json"
            packet = copy.deepcopy(load_json(DEFAULT_INPUT_PACKET_SCAFFOLD_PATH))
            packet["summary"]["human_value_count"] = 1
            packet["summary"]["human_values_collected"] = True
            packet["summary"]["input_form_created"] = True
            packet["summary"]["input_importer_created"] = True
            packet["summary"]["input_values_imported"] = True
            packet["summary"]["input_values_validated"] = True
            packet["summary"]["authorization_granted"] = True
            packet["summary"]["qdrant_write_allowed"] = True
            packet["summary"]["rebuild_allowed"] = True
            write_json(packet_path, packet)
            write_json(gate_path, load_json(DEFAULT_INPUT_PACKET_SCAFFOLD_GATE_PATH))

            report = build_report(packet_path, gate_path)

        blockers = set(report["summary"]["blockers"])
        self.assertIn("input_packet_scaffold_human_value_count_mismatch", blockers)
        self.assertIn("input_packet_scaffold_human_values_collected_mismatch", blockers)
        self.assertIn("input_packet_scaffold_input_form_created_mismatch", blockers)
        self.assertIn("input_packet_scaffold_input_importer_created_mismatch", blockers)
        self.assertIn("input_packet_scaffold_input_values_imported_mismatch", blockers)
        self.assertIn("input_packet_scaffold_input_values_validated_mismatch", blockers)
        self.assertIn("input_packet_scaffold_authorization_granted_mismatch", blockers)
        self.assertIn("input_packet_scaffold_qdrant_write_allowed_mismatch", blockers)
        self.assertIn("input_packet_scaffold_rebuild_allowed_mismatch", blockers)

    def test_packet_contract_or_policy_drift_blocks_scaffold(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            packet_path = tmp / "packet.json"
            gate_path = tmp / "gate.json"
            packet = copy.deepcopy(load_json(DEFAULT_INPUT_PACKET_SCAFFOLD_PATH))
            scaffold = packet["input_packet_scaffold"]
            scaffold["sections"][0]["input_form_effect"] = "created"
            scaffold["rows"][0]["entry_status"] = "filled"
            scaffold["rows"][0]["human_value"] = "prod_collection"
            scaffold["future_validation_policy"]["operator_approval_effect"] = "approval_now"
            scaffold["future_import_policy"]["authorization_effect"] = "authorization_now"
            scaffold["packet_completion_policy"]["current_packet_importable"] = True
            write_json(packet_path, packet)
            write_json(gate_path, load_json(DEFAULT_INPUT_PACKET_SCAFFOLD_GATE_PATH))

            report = build_report(packet_path, gate_path)

        blockers = set(report["summary"]["blockers"])
        self.assertIn("input_packet_scaffold_section_contract_mismatch", blockers)
        self.assertIn("input_packet_scaffold_row_contract_mismatch", blockers)
        self.assertIn("input_packet_scaffold_policy_mismatch", blockers)

    def test_handoff_traceability_or_forbidden_key_drift_blocks_scaffold(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            packet_path = tmp / "packet.json"
            gate_path = tmp / "gate.json"
            packet = copy.deepcopy(load_json(DEFAULT_INPUT_PACKET_SCAFFOLD_PATH))
            packet["handoff"]["not_allowed_yet"].remove("write Qdrant")
            packet["traceability"]["packet_field_count"] = 9
            packet["input_packet_scaffold"]["rows"][0]["commands"] = []
            write_json(packet_path, packet)
            write_json(gate_path, load_json(DEFAULT_INPUT_PACKET_SCAFFOLD_GATE_PATH))

            report = build_report(packet_path, gate_path)

        blockers = set(report["summary"]["blockers"])
        self.assertIn("input_packet_scaffold_handoff_boundary_mismatch", blockers)
        self.assertIn("input_packet_scaffold_traceability_count_mismatch", blockers)
        self.assertIn("input_packet_scaffold_forbidden_output_key_present", blockers)

    def test_forbidden_output_key_detector_is_generic(self):
        report = {"nested": [{"form_submission": {}}, {"authorized_actions": ["write Qdrant"]}]}

        self.assertEqual(forbidden_output_keys(report), ["authorized_actions", "form_submission"])
        self.assertEqual(forbidden_output_keys(build_report()), [])

    def test_cli_output_matches_builder_shape_and_utf8_markdown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "input_form_scaffold.json"
            summary = Path(tmpdir) / "input_form_scaffold.md"
            subprocess.run(
                [
                    sys.executable,
                    "tools/build_human_rebuild_authorization_record_input_form_scaffold.py",
                    "--input-packet-scaffold",
                    str(DEFAULT_INPUT_PACKET_SCAFFOLD_PATH),
                    "--input-packet-scaffold-gate",
                    str(DEFAULT_INPUT_PACKET_SCAFFOLD_GATE_PATH),
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
        self.assertIn("未来人工授权输入表单的空白 scaffold", cli_summary)
        self.assertIn("不是可运行表单", cli_summary)
        self.assertIn("只允许进入 `human_rebuild_authorization_record_input_form_scaffold_gate`", cli_summary)

    def test_source_has_no_runtime_service_imports_or_calls(self):
        source = Path("tools/build_human_rebuild_authorization_record_input_form_scaffold.py").read_text(
            encoding="utf-8"
        )
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

    def test_markdown_documents_scaffold_boundary(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.14.12 Human Rebuild Authorization Record Input Form Scaffold", markdown)
        self.assertIn("不收集", markdown)
        self.assertIn("不是 importer", markdown)
        self.assertIn("不创建或接受正式授权记录", markdown)
        self.assertIn("仍不代表已经允许填写真实人工值", markdown)


if __name__ == "__main__":
    unittest.main()
