import ast
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_production_rebuild_execution_design import (
    ABORT_CONDITIONS,
    CLOSEOUT_EXPECTATION,
    DEFAULT_CLOSEOUT_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DENIED_GUARDRAILS,
    EXECUTION_PHASES,
    GUARDRAILS,
    PREFLIGHT_CHECKS,
    REQUIRED_AUTHORIZATION_FIELDS,
    build_report,
    render_markdown,
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def comparable(report: dict) -> dict:
    copy_report = copy.deepcopy(report)
    copy_report.pop("generated_at", None)
    return copy_report


class ProductionRebuildExecutionDesignTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(DEFAULT_CLOSEOUT_PATH, legacy_report_path("ingestion_metadata_rebuild_planning_series_closeout_report.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("production_rebuild_execution_design_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/production_rebuild_execution_design_v0.4.14.0.md"))

    def test_real_input_builds_execution_design_from_closeout_only(self):
        report = build_report()
        summary = report["summary"]

        self.assertEqual(report["version"], "0.4.14.0")
        self.assertEqual(report["schema_kind"], "production_rebuild_execution_design")
        self.assertEqual(set(report["inputs"]), {"planning_closeout"})
        self.assertEqual(summary["status"], "ready_for_production_rebuild_execution_design_gate")
        self.assertEqual(summary["allowed_next_step"], "production_rebuild_execution_design_gate")
        self.assertEqual(summary["blockers"], [])
        self.assertTrue(summary["authorization_record_required"])
        self.assertFalse(summary["authorization_record_created"])
        self.assertFalse(summary["authorization_granted"])
        self.assertFalse(summary["live_preflight_run"])
        self.assertFalse(summary["production_rebuild_executed"])
        self.assertFalse(summary["qdrant_write_allowed"])
        self.assertFalse(summary["rebuild_allowed"])
        self.assertEqual(summary["full_eval"], "not_run")

    def test_closeout_source_lineage_matches_expected_version_and_next_step(self):
        source = build_report()["inputs"]["planning_closeout"]

        self.assertTrue(source["present"])
        self.assertEqual(source["version"], CLOSEOUT_EXPECTATION["version"])
        self.assertEqual(source["schema_kind"], CLOSEOUT_EXPECTATION["schema_kind"])
        self.assertEqual(source["status"], CLOSEOUT_EXPECTATION["status"])
        self.assertEqual(source["allowed_next_step"], CLOSEOUT_EXPECTATION["allowed_next_step"])

    def test_record_contract_counts_match_actual_structures(self):
        report = build_report()
        summary = report["summary"]
        design = report["execution_design"]
        records = design["record_contracts"]

        self.assertEqual(design["required_authorization_fields"], REQUIRED_AUTHORIZATION_FIELDS)
        self.assertEqual(design["phase_order"], EXECUTION_PHASES)
        self.assertEqual(records["preflight_record"]["checks"], PREFLIGHT_CHECKS)
        self.assertEqual(design["blocking_conditions"], ABORT_CONDITIONS)
        self.assertEqual(summary["record_contract_count"], len(records))
        self.assertEqual(summary["execution_phase_count"], len(design["phase_order"]))
        self.assertEqual(summary["preflight_check_count"], len(records["preflight_record"]["checks"]))
        self.assertEqual(summary["abort_condition_count"], len(design["blocking_conditions"]))
        self.assertEqual(report["output_contract"]["required_records"], list(records))
        self.assertTrue(records["rebuild_execution_record"]["must_not_be_created_in_this_version"])

    def test_missing_closeout_report_blocks_design(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            missing = Path(tmpdir) / "missing_closeout.json"

            report = build_report(missing)

        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("planning_closeout_missing", report["summary"]["blockers"])
        self.assertEqual(report["summary"]["allowed_next_step"], "blocked")

    def test_closeout_version_schema_status_or_next_step_drift_blocks_design(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            closeout = Path(tmpdir) / "closeout.json"
            payload = copy.deepcopy(load_json(DEFAULT_CLOSEOUT_PATH))
            payload["version"] = "0.4.13.99"
            payload["schema_kind"] = "wrong_schema"
            payload["summary"]["status"] = "failed"
            payload["summary"]["allowed_next_step"] = "production_rebuild"
            write_json(closeout, payload)

            report = build_report(closeout)

        blockers = report["summary"]["blockers"]
        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("planning_closeout_version_mismatch", blockers)
        self.assertIn("planning_closeout_schema_mismatch", blockers)
        self.assertIn("planning_closeout_status_mismatch", blockers)
        self.assertIn("planning_closeout_allowed_next_step_mismatch", blockers)

    def test_closeout_permission_drift_blocks_design(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            closeout = Path(tmpdir) / "closeout.json"
            payload = copy.deepcopy(load_json(DEFAULT_CLOSEOUT_PATH))
            payload["summary"]["authorization_granted"] = True
            payload["summary"]["rebuild_allowed"] = True
            payload["summary"]["qdrant_write_allowed"] = True
            payload["summary"]["live_preflight_run"] = True
            payload["summary"]["production_rebuild_executed"] = True
            write_json(closeout, payload)

            report = build_report(closeout)

        blockers = report["summary"]["blockers"]
        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("planning_closeout_authorization_granted_mismatch", blockers)
        self.assertIn("planning_closeout_rebuild_allowed_mismatch", blockers)
        self.assertIn("planning_closeout_qdrant_write_allowed_mismatch", blockers)
        self.assertIn("planning_closeout_live_preflight_run_mismatch", blockers)
        self.assertIn("planning_closeout_production_rebuild_executed_mismatch", blockers)

    def test_closeout_guardrail_drift_blocks_design(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            closeout = Path(tmpdir) / "closeout.json"
            payload = copy.deepcopy(load_json(DEFAULT_CLOSEOUT_PATH))
            payload["guardrails"]["qdrant_access"] = "allowed"
            payload["guardrails"]["collection_rebuild"] = "allowed"
            payload["guardrails"]["full_eval"] = "run"
            payload["guardrails"]["prompt_mutation"] = "allowed"
            write_json(closeout, payload)

            report = build_report(closeout)

        blockers = report["summary"]["blockers"]
        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("planning_closeout_guardrail_qdrant_access_mismatch", blockers)
        self.assertIn("planning_closeout_guardrail_collection_rebuild_mismatch", blockers)
        self.assertIn("planning_closeout_guardrail_full_eval_mismatch", blockers)
        self.assertIn("planning_closeout_guardrail_prompt_mutation_mismatch", blockers)

    def test_canonical_denylist_is_reflected_in_guardrails_summary_and_handoff(self):
        report = build_report()
        summary = report["summary"]
        handoff = " ".join(report["handoff"]["not_allowed_yet"])

        self.assertEqual({key: report["guardrails"][key] for key in DENIED_GUARDRAILS}, DENIED_GUARDRAILS)
        self.assertEqual({key: GUARDRAILS[key] for key in DENIED_GUARDRAILS}, DENIED_GUARDRAILS)
        self.assertFalse(summary["authorization_record_created"])
        self.assertFalse(summary["authorization_granted"])
        self.assertFalse(summary["live_preflight_run"])
        self.assertFalse(summary["production_rebuild_executed"])
        self.assertFalse(summary["qdrant_write_allowed"])
        self.assertFalse(summary["rebuild_allowed"])
        self.assertEqual(summary["full_eval"], "not_run")
        for phrase in [
            "human authorization record",
            "live preflight",
            "Qdrant",
            "rebuild collection",
            "rag_query",
            "embedding or LLM",
            "full eval",
            "runtime",
            "prompt",
            "eval cases",
        ]:
            self.assertIn(phrase, handoff)

    def test_cli_writes_same_report_shape_as_builder_ignoring_generated_at(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "report.json"
            summary = Path(tmpdir) / "summary.md"
            subprocess.run(
                [
                    sys.executable,
                    "tools/build_production_rebuild_execution_design.py",
                    "--closeout",
                    str(DEFAULT_CLOSEOUT_PATH),
                    "--output",
                    str(output),
                    "--summary",
                    str(summary),
                ],
                check=True,
                cwd=Path(__file__).resolve().parents[1],
            )

            cli_report = load_json(output)

        self.assertEqual(comparable(cli_report), comparable(build_report()))

    def test_tool_has_no_runtime_service_imports(self):
        source_path = Path("tools/build_production_rebuild_execution_design.py")
        tree = ast.parse(source_path.read_text(encoding="utf-8-sig"))
        imported_modules = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.extend(alias.name for alias in node.names)
            if isinstance(node, ast.ImportFrom):
                imported_modules.append(node.module or "")

        forbidden_modules = {
            "qdrant_client",
            "langchain_openai",
            "openai",
            "src.rag.retriever",
            "src.core.qdrant",
            "src.core.vectorstore",
            "tools.run_rag_eval",
            "tools.run_risk_eval",
            "tools.run_report_eval",
        }
        self.assertTrue(forbidden_modules.isdisjoint(imported_modules))

    def test_markdown_documents_design_only_boundary(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.14.0 Production Rebuild Execution Design", markdown)
        self.assertIn("只设计未来生产 rebuild execution series", markdown)
        self.assertIn("只读取 v0.4.13.18 closeout report", markdown)
        self.assertIn("不运行 live preflight", markdown)
        self.assertIn("不访问或写入 Qdrant", markdown)
        self.assertIn("不代表已经允许 live preflight", markdown)


if __name__ == "__main__":
    unittest.main()
