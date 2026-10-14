import ast
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.check_human_rebuild_authorization_record_input_packet_scaffold_gate import (
    DEFAULT_INPUT_PACKET_SCAFFOLD_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    FIELD_ORDER,
    SECTION_ORDER,
    build_report,
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


class HumanRebuildAuthorizationRecordInputPacketScaffoldGateTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(
            DEFAULT_INPUT_PACKET_SCAFFOLD_PATH,
            legacy_report_path("human_rebuild_authorization_record_input_packet_scaffold_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("human_rebuild_authorization_record_input_packet_scaffold_gate_report.json"),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/human_rebuild_authorization_record_input_packet_scaffold_gate_v0.4.14.11.md"),
        )

    def test_real_input_packet_scaffold_passes_gate(self):
        report = build_report()
        summary = report["summary"]

        self.assertEqual(report["version"], "0.4.14.11")
        self.assertEqual(report["schema_kind"], "human_rebuild_authorization_record_input_packet_scaffold_gate")
        self.assertEqual(summary["status"], "passed")
        self.assertEqual(summary["check_count"], 16)
        self.assertEqual(summary["failed_check_count"], 0)
        self.assertEqual(summary["allowed_next_step"], "human_rebuild_authorization_record_input_form_scaffold")
        self.assertFalse(summary["human_values_collected"])
        self.assertFalse(summary["input_form_created"])
        self.assertFalse(summary["input_importer_created"])
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
        self.assertEqual(summary["forbidden_output_key_count"], 0)

    def test_status_or_source_lineage_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "input_packet_scaffold.json"
            payload = copy.deepcopy(load_json(DEFAULT_INPUT_PACKET_SCAFFOLD_PATH))
            payload["version"] = "0.4.14.99"
            payload["summary"]["status"] = "authorized"
            payload["summary"]["allowed_next_step"] = "live_preflight"
            payload["inputs"]["human_rebuild_authorization_record_input_workflow_design_gate"]["version"] = "0.4.14.99"
            payload["inputs"]["human_rebuild_authorization_record_input_workflow_design_gate"]["status"] = "failed"
            payload["inputs"]["legacy_report"] = {"version": "0.4.13.18"}
            write_json(path, payload)

            report = build_report(path)

        failed = {row["check_id"] for row in report["failed_checks"]}
        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("input_packet_scaffold_version", failed)
        self.assertIn("input_packet_scaffold_status", failed)
        self.assertIn("source_lineage", failed)

    def test_values_import_validation_or_permission_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "input_packet_scaffold.json"
            payload = copy.deepcopy(load_json(DEFAULT_INPUT_PACKET_SCAFFOLD_PATH))
            payload["summary"]["human_value_count"] = 1
            payload["summary"]["human_values_collected"] = True
            payload["summary"]["input_form_created"] = True
            payload["summary"]["input_importer_created"] = True
            payload["summary"]["input_values_imported"] = True
            payload["summary"]["input_values_validated"] = True
            payload["summary"]["formal_authorization_record_created"] = True
            payload["summary"]["authorization_granted"] = True
            payload["summary"]["live_preflight_run"] = True
            payload["summary"]["qdrant_write_allowed"] = True
            payload["summary"]["rebuild_allowed"] = True
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("no_values_or_authorization", {row["check_id"] for row in report["failed_checks"]})

    def test_internal_gate_or_guardrail_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "input_packet_scaffold.json"
            payload = copy.deepcopy(load_json(DEFAULT_INPUT_PACKET_SCAFFOLD_PATH))
            payload["input_packet_scaffold_gate"]["allowed_use"] = "authorization_record"
            payload["input_packet_scaffold_gate"]["input_importer_created"] = True
            payload["input_packet_scaffold_gate"]["qdrant_write_allowed"] = True
            payload["guardrails"]["input_importer_created"] = True
            payload["guardrails"]["qdrant_write"] = "allowed"
            payload["guardrails"]["collection_rebuild"] = "allowed"
            write_json(path, payload)

            report = build_report(path)

        failed = {row["check_id"] for row in report["failed_checks"]}
        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("internal_gate_locked", failed)
        self.assertIn("guardrails_locked", failed)

    def test_section_contract_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "input_packet_scaffold.json"
            payload = copy.deepcopy(load_json(DEFAULT_INPUT_PACKET_SCAFFOLD_PATH))
            scaffold = payload["input_packet_scaffold"]
            scaffold["packet_status"] = "completed"
            scaffold["section_order"] = list(reversed(SECTION_ORDER))
            scaffold["sections"][0]["field_ids"] = []
            scaffold["sections"][0]["input_form_effect"] = "created"
            scaffold["sections"][0]["import_effect"] = "imported"
            scaffold["sections"][0]["authorization_effect"] = "granted"
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("section_contract_locked", {row["check_id"] for row in report["failed_checks"]})

    def test_row_blank_contract_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "input_packet_scaffold.json"
            payload = copy.deepcopy(load_json(DEFAULT_INPUT_PACKET_SCAFFOLD_PATH))
            row = payload["input_packet_scaffold"]["rows"][0]
            row["field_id"] = FIELD_ORDER[1]
            row["entry_status"] = "filled"
            row["value_status"] = "collected"
            row["human_value"] = "prod_collection"
            row["normalized_value"] = "prod_collection"
            row["import_status"] = "imported"
            row["validation_status_now"] = "passed"
            row["authorization_granted"] = True
            row["qdrant_write_allowed"] = True
            row["guidance_source"] = ""
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("row_blank_contract_locked", {row["check_id"] for row in report["failed_checks"]})

    def test_operator_approval_current_authorization_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "input_packet_scaffold.json"
            payload = copy.deepcopy(load_json(DEFAULT_INPUT_PACKET_SCAFFOLD_PATH))
            row = payload["input_packet_scaffold"]["rows"][FIELD_ORDER.index("operator_approval")]
            row["human_value"] = "yes"
            row["authorization_effect_now"] = "granted"
            row["authorization_granted"] = True
            row["qdrant_write_allowed"] = True
            row["rebuild_allowed"] = True
            write_json(path, payload)

            report = build_report(path)

        failed = {row["check_id"] for row in report["failed_checks"]}
        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("operator_approval_future_only", failed)

    def test_future_policy_handoff_or_traceability_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "input_packet_scaffold.json"
            payload = copy.deepcopy(load_json(DEFAULT_INPUT_PACKET_SCAFFOLD_PATH))
            scaffold = payload["input_packet_scaffold"]
            scaffold["future_validation_policy"]["operator_approval_effect"] = "approval_now"
            scaffold["future_import_policy"]["authorization_effect"] = "authorization_now"
            scaffold["packet_completion_policy"]["current_packet_importable"] = True
            payload["handoff"]["not_allowed_yet"].remove("write Qdrant")
            payload["traceability"]["packet_field_count"] = 9
            write_json(path, payload)

            report = build_report(path)

        failed = {row["check_id"] for row in report["failed_checks"]}
        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("future_validation_policy_locked", failed)
        self.assertIn("future_import_policy_locked", failed)
        self.assertIn("packet_completion_policy_locked", failed)
        self.assertIn("handoff_boundaries", failed)
        self.assertIn("traceability_counts", failed)

    def test_forbidden_output_key_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "input_packet_scaffold.json"
            payload = copy.deepcopy(load_json(DEFAULT_INPUT_PACKET_SCAFFOLD_PATH))
            payload["input_packet_scaffold"]["rows"][0]["commands"] = []
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertEqual(report["summary"]["forbidden_output_key_count"], 1)
        self.assertIn("forbidden_output_keys_absent", {row["check_id"] for row in report["failed_checks"]})

    def test_cli_output_matches_builder_shape_and_utf8_markdown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "input_packet_scaffold_gate.json"
            summary = Path(tmpdir) / "input_packet_scaffold_gate.md"
            subprocess.run(
                [
                    sys.executable,
                    "tools/check_human_rebuild_authorization_record_input_packet_scaffold_gate.py",
                    "--input-packet-scaffold",
                    str(DEFAULT_INPUT_PACKET_SCAFFOLD_PATH),
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
        self.assertIn("只检查 v0.4.14.10 保存的 input packet scaffold", cli_summary)
        self.assertIn("不创建输入表单或 importer", cli_summary)
        self.assertIn("只允许进入 `human_rebuild_authorization_record_input_form_scaffold`", cli_summary)

    def test_source_has_no_runtime_service_imports_or_calls(self):
        source = Path("tools/check_human_rebuild_authorization_record_input_packet_scaffold_gate.py").read_text(
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

    def test_markdown_documents_gate_boundary(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.14.11 Human Rebuild Authorization Record Input Packet Scaffold Gate", markdown)
        self.assertIn("不收集", markdown)
        self.assertIn("不创建输入表单或 importer", markdown)
        self.assertIn("不访问或写入 Qdrant", markdown)
        self.assertIn("不 rebuild collection", markdown)
        self.assertIn("仍不代表已经允许填写真实人工值", markdown)


if __name__ == "__main__":
    unittest.main()
