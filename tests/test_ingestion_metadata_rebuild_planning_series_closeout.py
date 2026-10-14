import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_ingestion_metadata_rebuild_planning_series_closeout import (
    DEFAULT_AUTH_DESIGN_PATH,
    DEFAULT_AUTH_GATE_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_RUNBOOK_PATH,
    DEFAULT_WORKSHEET_GATE_PATH,
    DEFAULT_WORKSHEET_PATH,
    GUARDRAILS,
    SOURCE_EXPECTATIONS,
    build_report,
    render_markdown,
)


SOURCE_ORDER = [
    "authorization_design",
    "authorization_gate",
    "worksheet",
    "worksheet_gate",
    "runbook_contract",
]

DEFAULT_PATHS = {
    "authorization_design": DEFAULT_AUTH_DESIGN_PATH,
    "authorization_gate": DEFAULT_AUTH_GATE_PATH,
    "worksheet": DEFAULT_WORKSHEET_PATH,
    "worksheet_gate": DEFAULT_WORKSHEET_GATE_PATH,
    "runbook_contract": DEFAULT_RUNBOOK_PATH,
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def build_with_paths(paths: dict[str, Path]) -> dict:
    return build_report(
        paths["authorization_design"],
        paths["authorization_gate"],
        paths["worksheet"],
        paths["worksheet_gate"],
        paths["runbook_contract"],
    )


class IngestionMetadataRebuildPlanningSeriesCloseoutTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(DEFAULT_AUTH_DESIGN_PATH, legacy_report_path("rebuild_authorization_design_report.json"))
        self.assertEqual(DEFAULT_AUTH_GATE_PATH, legacy_report_path("rebuild_authorization_design_gate_report.json"))
        self.assertEqual(DEFAULT_WORKSHEET_PATH, legacy_report_path("human_rebuild_authorization_worksheet_report.json"))
        self.assertEqual(DEFAULT_WORKSHEET_GATE_PATH, legacy_report_path("human_rebuild_authorization_worksheet_gate_report.json"))
        self.assertEqual(DEFAULT_RUNBOOK_PATH, legacy_report_path("rebuild_runbook_preflight_contract_report.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, legacy_report_path("ingestion_metadata_rebuild_planning_series_closeout_report.json"))
        self.assertEqual(DEFAULT_MARKDOWN_OUTPUT_PATH, Path("docs/ingestion_metadata_rebuild_planning_series_closeout_v0.4.13.18.md"))

    def test_real_inputs_close_planning_series(self):
        report = build_report()
        summary = report["summary"]

        self.assertEqual(report["version"], "0.4.13.18")
        self.assertEqual(report["schema_kind"], "ingestion_metadata_rebuild_planning_series_closeout")
        self.assertEqual(summary["status"], "closed_for_execution_design_handoff")
        self.assertEqual(summary["completed_report_count"], 5)
        self.assertEqual(summary["allowed_next_step"], "production_rebuild_execution_design")
        self.assertEqual(summary["blockers"], [])
        self.assertFalse(summary["production_rebuild_executed"])
        self.assertFalse(summary["live_preflight_run"])
        self.assertFalse(summary["authorization_granted"])
        self.assertFalse(summary["qdrant_write_allowed"])
        self.assertFalse(summary["rebuild_allowed"])
        self.assertEqual(summary["full_eval"], "not_run")

    def test_source_lineage_matches_expected_versions_and_next_steps(self):
        report = build_report()
        inputs = report["inputs"]

        for key, expectation in SOURCE_EXPECTATIONS.items():
            self.assertTrue(inputs[key]["present"])
            self.assertEqual(inputs[key]["version"], expectation["version"])
            self.assertEqual(inputs[key]["schema_kind"], expectation["schema_kind"])
            self.assertEqual(inputs[key]["status"], expectation["status"])
            self.assertEqual(inputs[key]["allowed_next_step"], expectation["allowed_next_step"])

    def test_missing_source_report_blocks_closeout(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = {key: Path(tmpdir) / f"{key}.json" for key in SOURCE_ORDER}
            for key in SOURCE_ORDER:
                if key != "runbook_contract":
                    write_json(paths[key], load_json(DEFAULT_PATHS[key]))

            report = build_with_paths(paths)

        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("runbook_contract_missing", report["summary"]["blockers"])
        self.assertEqual(report["summary"]["allowed_next_step"], "blocked")

    def test_version_schema_status_or_next_step_drift_blocks_closeout(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = {key: Path(tmpdir) / f"{key}.json" for key in SOURCE_ORDER}
            for key in SOURCE_ORDER:
                payload = copy.deepcopy(load_json(DEFAULT_PATHS[key]))
                if key == "authorization_gate":
                    payload["version"] = "0.4.13.99"
                    payload["schema_kind"] = "wrong_schema"
                    payload["summary"]["status"] = "failed"
                    payload["summary"]["allowed_next_step"] = "production_rebuild"
                write_json(paths[key], payload)

            report = build_with_paths(paths)

        blockers = report["summary"]["blockers"]
        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("authorization_gate_version_mismatch", blockers)
        self.assertIn("authorization_gate_schema_mismatch", blockers)
        self.assertIn("authorization_gate_status_mismatch", blockers)
        self.assertIn("authorization_gate_allowed_next_step_mismatch", blockers)

    def test_authorization_and_rebuild_permission_drift_blocks_every_source(self):
        for key in SOURCE_ORDER:
            with self.subTest(source=key):
                with tempfile.TemporaryDirectory() as tmpdir:
                    paths = {name: Path(tmpdir) / f"{name}.json" for name in SOURCE_ORDER}
                    for name in SOURCE_ORDER:
                        payload = copy.deepcopy(load_json(DEFAULT_PATHS[name]))
                        if name == key:
                            payload["summary"]["authorization_granted"] = True
                            payload["summary"]["rebuild_allowed"] = True
                        write_json(paths[name], payload)

                    report = build_with_paths(paths)

                blockers = report["summary"]["blockers"]
                self.assertEqual(report["summary"]["status"], "blocked")
                self.assertIn(f"{key}_authorization_granted_mismatch", blockers)
                self.assertIn(f"{key}_rebuild_allowed_mismatch", blockers)

    def test_guardrail_drift_blocks_closeout(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = {key: Path(tmpdir) / f"{key}.json" for key in SOURCE_ORDER}
            for key in SOURCE_ORDER:
                payload = copy.deepcopy(load_json(DEFAULT_PATHS[key]))
                if key == "runbook_contract":
                    payload["guardrails"]["qdrant_access"] = "allowed"
                    payload["guardrails"]["collection_rebuild"] = "allowed"
                    payload["guardrails"]["full_eval"] = "run"
                write_json(paths[key], payload)

            report = build_with_paths(paths)

        blockers = report["summary"]["blockers"]
        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("runbook_contract_guardrail_qdrant_access_mismatch", blockers)
        self.assertIn("runbook_contract_guardrail_collection_rebuild_mismatch", blockers)
        self.assertIn("runbook_contract_guardrail_full_eval_mismatch", blockers)

    def test_qdrant_rebuild_full_eval_and_runtime_boundaries_are_closed(self):
        report = build_report()
        guardrails = report["guardrails"]

        self.assertEqual(guardrails["qdrant_access"], "disallowed")
        self.assertEqual(guardrails["qdrant_write"], "disallowed")
        self.assertEqual(guardrails["collection_rebuild"], "disallowed")
        self.assertEqual(guardrails["rag_query_integration"], "disallowed")
        self.assertEqual(guardrails["embedding_call"], "disallowed")
        self.assertEqual(guardrails["llm_access"], "disallowed")
        self.assertEqual(guardrails["full_eval"], "not_run")
        self.assertEqual(guardrails["runtime_mutation"], "disallowed")

    def test_prompt_rerank_and_eval_case_mutation_boundaries_are_closed(self):
        self.assertEqual(GUARDRAILS["prompt_mutation"], "disallowed")
        self.assertEqual(GUARDRAILS["rerank_mutation"], "disallowed")
        self.assertEqual(GUARDRAILS["anchor_mutation"], "disallowed")
        self.assertEqual(GUARDRAILS["risk_rule_mutation"], "disallowed")
        self.assertEqual(GUARDRAILS["risk_supplement_mutation"], "disallowed")
        self.assertEqual(GUARDRAILS["term_preservation_rule_mutation"], "disallowed")
        self.assertEqual(GUARDRAILS["scenario_registry_mutation"], "disallowed")
        self.assertEqual(GUARDRAILS["eval_case_mutation"], "disallowed")
        self.assertEqual(GUARDRAILS["fixture_mutation"], "disallowed")

    def test_handoff_only_allows_execution_design_not_execution(self):
        report = build_report()

        self.assertEqual(report["summary"]["allowed_next_step"], "production_rebuild_execution_design")
        self.assertEqual(report["handoff"]["next_allowed_step"], "design a separate production rebuild execution series")
        self.assertIn("run live preflight", report["handoff"]["not_allowed_yet"])
        self.assertIn("write Qdrant", report["handoff"]["not_allowed_yet"])
        self.assertIn("rebuild collection", report["handoff"]["not_allowed_yet"])

    def test_markdown_documents_non_execution_boundary(self):
        markdown = render_markdown(build_report())

        self.assertIn("v0.4.13.18 Ingestion Metadata Rebuild Planning Series Closeout", markdown)
        self.assertIn("不执行 rebuild", markdown)
        self.assertIn("不运行 live preflight", markdown)
        self.assertIn("不访问 Qdrant", markdown)
        self.assertIn("不代表已经允许生产 Qdrant rebuild", markdown)


if __name__ == "__main__":
    unittest.main()
