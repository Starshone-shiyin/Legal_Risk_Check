import ast
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.check_human_rebuild_authorization_record_input_form_scaffold_gate import (
    DEFAULT_INPUT_FORM_SCAFFOLD_PATH,
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


class HumanRebuildAuthorizationRecordInputFormScaffoldGateTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(
            DEFAULT_INPUT_FORM_SCAFFOLD_PATH,
            legacy_report_path("human_rebuild_authorization_record_input_form_scaffold_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("human_rebuild_authorization_record_input_form_scaffold_gate_report.json"),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/human_rebuild_authorization_record_input_form_scaffold_gate_v0.4.14.13.md"),
        )

    def test_real_input_form_scaffold_passes_gate(self):
        report = build_report()
        summary = report["summary"]

        self.assertEqual(report["version"], "0.4.14.13")
        self.assertEqual(report["schema_kind"], "human_rebuild_authorization_record_input_form_scaffold_gate")
        self.assertEqual(summary["status"], "passed")
        self.assertEqual(summary["check_count"], 17)
        self.assertEqual(summary["failed_check_count"], 0)
        self.assertEqual(summary["allowed_next_step"], "human_rebuild_authorization_record_input_importer_design")
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
        self.assertFalse(summary["production_rebuild_executed"])
        self.assertFalse(summary["qdrant_write_allowed"])
        self.assertFalse(summary["rebuild_allowed"])
        self.assertEqual(summary["full_eval"], "not_run")
        self.assertEqual(summary["forbidden_output_key_count"], 0)

    def test_status_or_source_lineage_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "form_scaffold.json"
            payload = copy.deepcopy(load_json(DEFAULT_INPUT_FORM_SCAFFOLD_PATH))
            payload["version"] = "0.4.14.99"
            payload["summary"]["status"] = "authorized"
            payload["summary"]["allowed_next_step"] = "live_preflight"
            payload["inputs"]["human_rebuild_authorization_record_input_packet_scaffold_gate"]["version"] = "0.4.14.99"
            payload["inputs"]["human_rebuild_authorization_record_input_packet_scaffold_gate"]["status"] = "failed"
            payload["inputs"]["legacy_report"] = {"version": "0.4.13.18"}
            write_json(path, payload)

            report = build_report(path)

        failed = {row["check_id"] for row in report["failed_checks"]}
        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("input_form_scaffold_version", failed)
        self.assertIn("input_form_scaffold_status", failed)
        self.assertIn("source_lineage", failed)

    def test_values_form_export_or_permissions_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "form_scaffold.json"
            payload = copy.deepcopy(load_json(DEFAULT_INPUT_FORM_SCAFFOLD_PATH))
            payload["summary"]["human_value_count"] = 1
            payload["summary"]["human_values_collected"] = True
            payload["summary"]["runnable_input_form_created"] = True
            payload["summary"]["input_form_created"] = True
            payload["summary"]["input_importer_created"] = True
            payload["summary"]["input_values_imported"] = True
            payload["summary"]["input_values_validated"] = True
            payload["summary"]["form_values_exported"] = True
            payload["summary"]["authorization_granted"] = True
            payload["summary"]["qdrant_write_allowed"] = True
            payload["summary"]["rebuild_allowed"] = True
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("no_values_or_authorization", {row["check_id"] for row in report["failed_checks"]})

    def test_internal_gate_or_guardrail_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "form_scaffold.json"
            payload = copy.deepcopy(load_json(DEFAULT_INPUT_FORM_SCAFFOLD_PATH))
            payload["input_form_scaffold_gate"]["allowed_use"] = "authorization_record"
            payload["input_form_scaffold_gate"]["runnable_input_form_created"] = True
            payload["input_form_scaffold_gate"]["qdrant_write_allowed"] = True
            payload["guardrails"]["runnable_input_form_created"] = True
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
            path = Path(tmpdir) / "form_scaffold.json"
            payload = copy.deepcopy(load_json(DEFAULT_INPUT_FORM_SCAFFOLD_PATH))
            scaffold = payload["input_form_scaffold"]
            scaffold["form_runtime_status"] = "created"
            scaffold["form_submission_status"] = "supported"
            scaffold["section_order"] = list(reversed(SECTION_ORDER))
            scaffold["sections"][0]["label_zh"] = ""
            scaffold["sections"][0]["field_ids"] = []
            scaffold["sections"][0]["interactive_form_effect"] = "created"
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("section_contract_locked", {row["check_id"] for row in report["failed_checks"]})

    def test_field_blank_contract_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "form_scaffold.json"
            payload = copy.deepcopy(load_json(DEFAULT_INPUT_FORM_SCAFFOLD_PATH))
            field = payload["input_form_scaffold"]["fields"][0]
            field["field_id"] = FIELD_ORDER[1]
            field["label_zh"] = ""
            field["future_widget_hint"] = "real_text_input"
            field["editable_now"] = True
            field["interactive_control_created"] = True
            field["entry_status"] = "filled"
            field["human_value"] = "prod_collection"
            field["normalized_value"] = "prod_collection"
            field["import_status"] = "imported"
            field["validation_status_now"] = "passed"
            field["authorization_granted"] = True
            field["qdrant_write_allowed"] = True
            field["guidance_source"] = ""
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("field_blank_contract_locked", {row["check_id"] for row in report["failed_checks"]})

    def test_operator_approval_current_authorization_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "form_scaffold.json"
            payload = copy.deepcopy(load_json(DEFAULT_INPUT_FORM_SCAFFOLD_PATH))
            field = payload["input_form_scaffold"]["fields"][FIELD_ORDER.index("operator_approval")]
            field["human_value"] = "yes"
            field["editable_now"] = True
            field["authorization_effect_now"] = "granted"
            field["authorization_granted"] = True
            field["qdrant_write_allowed"] = True
            field["rebuild_allowed"] = True
            write_json(path, payload)

            report = build_report(path)

        failed = {row["check_id"] for row in report["failed_checks"]}
        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("operator_approval_future_only", failed)

    def test_policy_handoff_or_traceability_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "form_scaffold.json"
            payload = copy.deepcopy(load_json(DEFAULT_INPUT_FORM_SCAFFOLD_PATH))
            scaffold = payload["input_form_scaffold"]
            scaffold["future_validation_policy"]["operator_approval_effect"] = "approval_now"
            scaffold["future_import_policy"]["authorization_effect"] = "authorization_now"
            scaffold["form_completion_policy"]["current_form_submittable"] = True
            scaffold["future_form_export_policy"]["current_form_exportable"] = True
            payload["handoff"]["not_allowed_yet"].remove("write Qdrant")
            payload["traceability"]["form_field_count"] = 9
            write_json(path, payload)

            report = build_report(path)

        failed = {row["check_id"] for row in report["failed_checks"]}
        self.assertEqual(report["summary"]["status"], "failed")
        self.assertIn("future_validation_policy_locked", failed)
        self.assertIn("future_import_policy_locked", failed)
        self.assertIn("form_completion_policy_locked", failed)
        self.assertIn("future_form_export_policy_locked", failed)
        self.assertIn("handoff_boundaries", failed)
        self.assertIn("traceability_counts", failed)

    def test_forbidden_output_key_drift_fails_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "form_scaffold.json"
            payload = copy.deepcopy(load_json(DEFAULT_INPUT_FORM_SCAFFOLD_PATH))
            payload["input_form_scaffold"]["fields"][0]["form_submission"] = {}
            payload["input_form_scaffold"]["commands"] = []
            write_json(path, payload)

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "failed")
        self.assertEqual(report["summary"]["forbidden_output_key_count"], 2)
        self.assertIn("forbidden_output_keys_absent", {row["check_id"] for row in report["failed_checks"]})

    def test_cli_output_matches_builder_shape_and_utf8_markdown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "input_form_scaffold_gate.json"
            summary = Path(tmpdir) / "input_form_scaffold_gate.md"
            subprocess.run(
                [
                    sys.executable,
                    "tools/check_human_rebuild_authorization_record_input_form_scaffold_gate.py",
                    "--input-form-scaffold",
                    str(DEFAULT_INPUT_FORM_SCAFFOLD_PATH),
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
        self.assertIn("只检查 v0.4.14.12 保存的 input form scaffold", cli_summary)
        self.assertIn("不创建可运行输入表单或 importer", cli_summary)
        self.assertIn("只允许进入 `human_rebuild_authorization_record_input_importer_design`", cli_summary)

    def test_source_has_no_runtime_service_imports_or_calls(self):
        source = Path("tools/check_human_rebuild_authorization_record_input_form_scaffold_gate.py").read_text(
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

        self.assertIn("v0.4.14.13 Human Rebuild Authorization Record Input Form Scaffold Gate", markdown)
        self.assertIn("不收集", markdown)
        self.assertIn("不创建可运行输入表单或 importer", markdown)
        self.assertIn("不访问或写入 Qdrant", markdown)
        self.assertIn("不 rebuild collection", markdown)
        self.assertIn("仍不代表已经允许填写真实人工值", markdown)


if __name__ == "__main__":
    unittest.main()
