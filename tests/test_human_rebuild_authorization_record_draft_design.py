import ast
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_human_rebuild_authorization_record_draft_design import (
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_SCAFFOLD_GATE_PATH,
    DEFAULT_SCAFFOLD_PATH,
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


class HumanRebuildAuthorizationRecordDraftDesignTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(DEFAULT_SCAFFOLD_PATH, legacy_report_path("human_rebuild_authorization_record_scaffold_report.json"))
        self.assertEqual(
            DEFAULT_SCAFFOLD_GATE_PATH,
            legacy_report_path("human_rebuild_authorization_record_scaffold_gate_report.json"),
        )
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("human_rebuild_authorization_record_draft_design_report.json"))
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/human_rebuild_authorization_record_draft_design_v0.4.14.4.md"),
        )

    def test_real_inputs_build_draft_design_only(self):
        report = build_report()
        summary = report["summary"]

        self.assertEqual(report["version"], "0.4.14.4")
        self.assertEqual(report["schema_kind"], "human_rebuild_authorization_record_draft_design")
        self.assertEqual(summary["status"], "ready_for_human_rebuild_authorization_record_draft_design_gate")
        self.assertEqual(summary["allowed_next_step"], "human_rebuild_authorization_record_draft_design_gate")
        self.assertTrue(summary["draft_design_only"])
        self.assertFalse(summary["draft_record_created"])
        self.assertEqual(summary["field_mapping_count"], 10)
        self.assertEqual(summary["section_count"], 7)
        self.assertEqual(summary["human_value_count"], 0)
        self.assertFalse(summary["human_values_collected"])
        self.assertFalse(summary["formal_authorization_record_created"])
        self.assertFalse(summary["human_authorization_record_created"])
        self.assertFalse(summary["human_authorization_record_accepted"])
        self.assertFalse(summary["authorization_granted"])
        self.assertFalse(summary["live_preflight_run"])
        self.assertFalse(summary["qdrant_write_allowed"])
        self.assertFalse(summary["rebuild_allowed"])
        self.assertEqual(summary["full_eval"], "not_run")
        self.assertEqual(summary["blockers"], [])

    def test_field_mappings_preserve_order_and_empty_values(self):
        design = build_report()["draft_record_design"]
        mappings = design["field_mappings"]

        self.assertEqual([row["source_scaffold_field"] for row in mappings], FIELD_ORDER)
        self.assertEqual(design["section_order"], SECTION_ORDER)
        for index, row in enumerate(mappings, start=1):
            self.assertEqual(row["fill_sequence"], index)
            self.assertEqual(row["draft_field_id"], FIELD_ORDER[index - 1])
            self.assertTrue(row["future_human_input_required"])
            self.assertEqual(row["draft_value_status"], "not_collected")
            self.assertEqual(row["value_status"], "not_collected")
            self.assertIsNone(row["draft_value_placeholder"])
            self.assertIsNone(row["value"])
            self.assertEqual(row["authorization_effect_now"], "none")
            self.assertFalse(row["authorization_granted"])
            self.assertFalse(row["qdrant_write_allowed"])
            self.assertFalse(row["rebuild_allowed"])
            self.assertFalse(row["captures_formal_authorization_outcome"])

    def test_operator_approval_mapping_is_future_only(self):
        row = next(
            row for row in build_report()["draft_record_design"]["field_mappings"]
            if row["draft_field_id"] == "operator_approval"
        )

        self.assertIn("does not grant current approval", row["guidance"])
        self.assertEqual(row["authorization_effect_now"], "none")
        self.assertFalse(row["authorization_granted"])

    def test_scaffold_or_gate_drift_blocks_design(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            scaffold = tmp / "scaffold.json"
            gate = tmp / "gate.json"
            scaffold_payload = copy.deepcopy(load_json(DEFAULT_SCAFFOLD_PATH))
            gate_payload = copy.deepcopy(load_json(DEFAULT_SCAFFOLD_GATE_PATH))
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
        self.assertIn("scaffold_status_mismatch", blockers)
        self.assertIn("scaffold_next_step_mismatch", blockers)
        self.assertIn("gate_not_passed", blockers)
        self.assertIn("gate_failed_checks_present", blockers)
        self.assertIn("gate_next_step_mismatch", blockers)

    def test_scaffold_values_or_permissions_drift_blocks_design(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            scaffold = tmp / "scaffold.json"
            gate = tmp / "gate.json"
            scaffold_payload = copy.deepcopy(load_json(DEFAULT_SCAFFOLD_PATH))
            scaffold_payload["summary"]["human_value_count"] = 1
            scaffold_payload["summary"]["human_values_collected"] = True
            scaffold_payload["summary"]["formal_authorization_record_created"] = True
            scaffold_payload["summary"]["authorization_granted"] = True
            scaffold_payload["summary"]["live_preflight_run"] = True
            scaffold_payload["summary"]["qdrant_write_allowed"] = True
            scaffold_payload["summary"]["rebuild_allowed"] = True
            write_json(scaffold, scaffold_payload)
            write_json(gate, load_json(DEFAULT_SCAFFOLD_GATE_PATH))

            report = build_report(scaffold, gate)

        blockers = set(report["summary"]["blockers"])
        self.assertIn("scaffold_human_value_count_mismatch", blockers)
        self.assertIn("scaffold_human_values_collected_mismatch", blockers)
        self.assertIn("scaffold_formal_authorization_record_created_mismatch", blockers)
        self.assertIn("scaffold_authorization_granted_mismatch", blockers)
        self.assertIn("scaffold_live_preflight_run_mismatch", blockers)
        self.assertIn("scaffold_qdrant_write_allowed_mismatch", blockers)
        self.assertIn("scaffold_rebuild_allowed_mismatch", blockers)

    def test_scaffold_guardrail_or_contract_drift_blocks_design(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            scaffold = tmp / "scaffold.json"
            gate = tmp / "gate.json"
            scaffold_payload = copy.deepcopy(load_json(DEFAULT_SCAFFOLD_PATH))
            scaffold_payload["guardrails"]["qdrant_write"] = "allowed"
            scaffold_payload["guardrails"]["collection_rebuild"] = "allowed"
            scaffold_payload["input_contract"]["required_authorization_fields"].remove("backup_plan")
            scaffold_payload["authorization_record_scaffold_rows"][0]["human_value_status"] = "collected"
            scaffold_payload["next_version_handoff"]["not_allowed_yet"].remove("write Qdrant")
            write_json(scaffold, scaffold_payload)
            write_json(gate, load_json(DEFAULT_SCAFFOLD_GATE_PATH))

            report = build_report(scaffold, gate)

        blockers = set(report["summary"]["blockers"])
        self.assertIn("scaffold_guardrail_qdrant_write_mismatch", blockers)
        self.assertIn("scaffold_guardrail_collection_rebuild_mismatch", blockers)
        self.assertIn("scaffold_input_contract_fields_mismatch", blockers)
        self.assertIn("scaffold_row_contract_mismatch", blockers)
        self.assertIn("scaffold_handoff_boundary_mismatch", blockers)

    def test_forbidden_output_key_detector_is_generic(self):
        report = {"nested": [{"commands": []}, {"authorized_actions": ["write Qdrant"]}]}

        self.assertEqual(forbidden_output_keys(report), ["authorized_actions", "commands"])
        self.assertEqual(forbidden_output_keys(build_report()), [])

    def test_cli_output_matches_builder_shape(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "draft_design.json"
            summary = Path(tmpdir) / "draft_design.md"
            subprocess.run(
                [
                    sys.executable,
                    "tools/build_human_rebuild_authorization_record_draft_design.py",
                    "--scaffold",
                    str(DEFAULT_SCAFFOLD_PATH),
                    "--scaffold-gate",
                    str(DEFAULT_SCAFFOLD_GATE_PATH),
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
        self.assertIn("只设计未来正式授权记录草案", cli_summary)
        self.assertIn("不创建或接受正式授权记录", cli_summary)
        self.assertIn("只允许进入 `human_rebuild_authorization_record_draft_design_gate`", cli_summary)

    def test_source_has_no_runtime_service_imports_or_calls(self):
        source = Path("tools/build_human_rebuild_authorization_record_draft_design.py").read_text(encoding="utf-8")
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

    def test_markdown_documents_draft_design_boundary(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.14.4 Human Rebuild Authorization Record Draft Design", markdown)
        self.assertIn("只设计未来正式授权记录草案", markdown)
        self.assertIn("不收集人工值", markdown)
        self.assertIn("不创建或接受正式授权记录", markdown)
        self.assertIn("不访问或写入 Qdrant", markdown)
        self.assertIn("仍不代表已经允许填写正式授权", markdown)
        for forbidden in ["authorized_actions", "ready_to_apply", "commands", "rebuild_steps"]:
            self.assertNotIn(forbidden, markdown)


if __name__ == "__main__":
    unittest.main()
