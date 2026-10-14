import ast
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_human_rebuild_authorization_record_scaffold import (
    AUTHORIZATION_FIELD_ORDER,
    DEFAULT_DESIGN_GATE_PATH,
    DEFAULT_DESIGN_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
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


class HumanRebuildAuthorizationRecordScaffoldTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(DEFAULT_DESIGN_PATH, legacy_report_path("production_rebuild_execution_design_report.json"))
        self.assertEqual(DEFAULT_DESIGN_GATE_PATH, legacy_report_path("production_rebuild_execution_design_gate_report.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("human_rebuild_authorization_record_scaffold_report.json"))
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/human_rebuild_authorization_record_scaffold_v0.4.14.2.md"),
        )

    def test_real_inputs_build_blank_record_scaffold(self):
        report = build_report()
        summary = report["summary"]
        gate = report["authorization_record_scaffold_gate"]

        self.assertEqual(report["version"], "0.4.14.2")
        self.assertEqual(report["schema_kind"], "human_rebuild_authorization_record_scaffold")
        self.assertEqual(summary["status"], "pending_human_authorization_record")
        self.assertEqual(summary["allowed_use"], "human_authorization_record_scaffold_only")
        self.assertEqual(summary["allowed_next_step"], "human_rebuild_authorization_record_scaffold_gate")
        self.assertEqual(summary["scaffold_row_count"], 10)
        self.assertEqual(summary["human_value_count"], 0)
        self.assertFalse(summary["human_values_collected"])
        self.assertFalse(summary["human_authorization_record_created"])
        self.assertFalse(summary["human_authorization_record_accepted"])
        self.assertFalse(summary["authorization_granted"])
        self.assertFalse(summary["live_preflight_run"])
        self.assertFalse(summary["production_rebuild_executed"])
        self.assertFalse(summary["qdrant_write_allowed"])
        self.assertFalse(summary["rebuild_allowed"])
        self.assertEqual(summary["full_eval"], "not_run")
        self.assertEqual(summary["blockers"], [])
        self.assertEqual(gate["status"], "ready_for_human_authorization_record_review")

    def test_rows_match_authorization_field_order_and_remain_empty(self):
        rows = build_report()["authorization_record_scaffold_rows"]

        self.assertEqual([row["field_id"] for row in rows], AUTHORIZATION_FIELD_ORDER)
        for row in rows:
            self.assertTrue(row["human_input_required"])
            self.assertEqual(row["human_value_status"], "not_collected")
            self.assertIsNone(row["empty_authorization_value"])
            self.assertFalse(row["authorization_granted"])
            self.assertFalse(row["live_preflight_allowed"])
            self.assertFalse(row["qdrant_write_allowed"])
            self.assertFalse(row["rebuild_allowed"])
            self.assertFalse(row["captures_formal_authorization_outcome"])

    def test_operator_approval_row_does_not_grant_approval(self):
        row = next(row for row in build_report()["authorization_record_scaffold_rows"] if row["field_id"] == "operator_approval")

        self.assertIn("不把该行视为当前批准", row["guidance"])
        self.assertFalse(row["authorization_granted"])
        self.assertFalse(row["captures_formal_authorization_outcome"])

    def test_gate_failure_blocks_scaffold(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            design = tmp / "design.json"
            gate = tmp / "gate.json"
            write_json(design, load_json(DEFAULT_DESIGN_PATH))
            gate_payload = copy.deepcopy(load_json(DEFAULT_DESIGN_GATE_PATH))
            gate_payload["summary"]["status"] = "failed"
            gate_payload["summary"]["failed_check_count"] = 1
            write_json(gate, gate_payload)

            report = build_report(design, gate)

        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("gate_not_passed", report["summary"]["blockers"])
        self.assertIn("gate_failed_checks_present", report["summary"]["blockers"])

    def test_gate_next_step_drift_blocks_scaffold(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            design = tmp / "design.json"
            gate = tmp / "gate.json"
            write_json(design, load_json(DEFAULT_DESIGN_PATH))
            gate_payload = copy.deepcopy(load_json(DEFAULT_DESIGN_GATE_PATH))
            gate_payload["summary"]["allowed_next_step"] = "live_preflight"
            write_json(gate, gate_payload)

            report = build_report(design, gate)

        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("gate_next_step_mismatch", report["summary"]["blockers"])

    def test_design_permission_drift_blocks_scaffold(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            design = tmp / "design.json"
            gate = tmp / "gate.json"
            design_payload = copy.deepcopy(load_json(DEFAULT_DESIGN_PATH))
            design_payload["summary"]["authorization_granted"] = True
            design_payload["summary"]["live_preflight_run"] = True
            design_payload["summary"]["qdrant_write_allowed"] = True
            design_payload["summary"]["rebuild_allowed"] = True
            write_json(design, design_payload)
            write_json(gate, load_json(DEFAULT_DESIGN_GATE_PATH))

            report = build_report(design, gate)

        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("design_authorization_granted_mismatch", report["summary"]["blockers"])
        self.assertIn("design_live_preflight_run_mismatch", report["summary"]["blockers"])
        self.assertIn("design_qdrant_write_allowed_mismatch", report["summary"]["blockers"])
        self.assertIn("design_rebuild_allowed_mismatch", report["summary"]["blockers"])

    def test_design_contract_drift_blocks_scaffold(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            design = tmp / "design.json"
            gate = tmp / "gate.json"
            design_payload = copy.deepcopy(load_json(DEFAULT_DESIGN_PATH))
            design_payload["execution_design"]["required_authorization_fields"].remove("backup_plan")
            design_payload["execution_design"]["record_contracts"]["silent_extra_record"] = {"fields": []}
            design_payload["execution_design"]["record_contracts"]["preflight_record"]["checks"].remove(
                "target_collection_confirmed"
            )
            design_payload["execution_design"]["blocking_conditions"].append("silent_extra_abort_condition")
            design_payload["execution_design"]["decision_policy"]["main_flow_change"] = "authorized"
            write_json(design, design_payload)
            write_json(gate, load_json(DEFAULT_DESIGN_GATE_PATH))

            report = build_report(design, gate)

        blockers = set(report["summary"]["blockers"])
        self.assertIn("design_authorization_field_order_mismatch", blockers)
        self.assertIn("design_record_contract_order_mismatch", blockers)
        self.assertIn("design_preflight_checks_mismatch", blockers)
        self.assertIn("design_abort_conditions_mismatch", blockers)
        self.assertIn("design_main_flow_policy_mismatch", blockers)

    def test_forbidden_output_key_detector_is_generic(self):
        report = {"nested": [{"commands": []}, {"ready_to_apply": True}], "safe": {"field_id": "target_collection"}}

        self.assertEqual(forbidden_output_keys(report), ["commands", "ready_to_apply"])
        self.assertEqual(forbidden_output_keys(build_report()), [])

    def test_cli_output_matches_builder_shape(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "scaffold.json"
            summary = Path(tmpdir) / "scaffold.md"
            subprocess.run(
                [
                    sys.executable,
                    "tools/build_human_rebuild_authorization_record_scaffold.py",
                    "--design",
                    str(DEFAULT_DESIGN_PATH),
                    "--design-gate",
                    str(DEFAULT_DESIGN_GATE_PATH),
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

        self.assertEqual(without_generated_at(cli_report), without_generated_at(build_report()))

    def test_source_has_no_runtime_service_imports_or_calls(self):
        source = Path("tools/build_human_rebuild_authorization_record_scaffold.py").read_text(encoding="utf-8")
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

        self.assertIn("v0.4.14.2 Human Rebuild Authorization Record Scaffold", markdown)
        self.assertIn("不是授权记录", markdown)
        self.assertIn("不收集人工值", markdown)
        self.assertIn("不运行 live preflight", markdown)
        self.assertIn("不访问或写入 Qdrant", markdown)
        self.assertIn("仍不代表已经允许 live preflight", markdown)
        for forbidden in ["authorized_actions", "ready_to_apply", "commands", "rebuild_steps"]:
            self.assertNotIn(forbidden, markdown)


if __name__ == "__main__":
    unittest.main()
