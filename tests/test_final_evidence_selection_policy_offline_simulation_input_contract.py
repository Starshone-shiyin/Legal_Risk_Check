import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_final_evidence_selection_policy_offline_simulation_input_contract import (
    DEFAULT_CONFIRMED_RECORD_PATH,
    DEFAULT_LANGUAGE_CONFIRMATION_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    EXPECTED_POLICY_ORDER,
    build_report,
    render_markdown,
)


PROHIBITED_SOURCE_PATTERNS = [
    "rag_query(",
    "from src.rag.retriever import rag_query",
    "ChatOpenAI",
    "QdrantClient",
    "fetch(",
    "XMLHttpRequest",
    "/ask",
    "rag_anchor_rules.json",
    "risk_payload_supplement_rules.json",
    "rag_eval_cases.json",
]


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def build_with_sources(closeout: dict, language: dict) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        closeout_path = Path(tmpdir) / "closeout.json"
        language_path = Path(tmpdir) / "language.json"
        write_json(closeout_path, copy.deepcopy(closeout))
        write_json(language_path, copy.deepcopy(language))
        return build_report(closeout_path, language_path)


class FinalEvidenceSelectionPolicyOfflineSimulationInputContractTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(
            DEFAULT_CONFIRMED_RECORD_PATH,
            legacy_report_path("final_evidence_selection_policy_closeout_confirmed_record_report.json"),
        )
        self.assertEqual(
            DEFAULT_LANGUAGE_CONFIRMATION_PATH,
            legacy_report_path("final_evidence_selection_policy_language_revision_confirmation_record_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("final_evidence_selection_policy_offline_simulation_input_contract_report.json"),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/final_evidence_selection_policy_offline_simulation_input_contract_v0.4.8.11.md"),
        )

    def test_real_sources_build_contract(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.8.11")
        self.assertEqual(report["schema_kind"], "final_evidence_selection_policy_offline_simulation_input_contract")
        self.assertEqual(report["contract_gate"]["status"], "ready_for_saved_report_offline_simulation")
        self.assertEqual(report["contract_gate"]["allowed_use"], "saved_report_offline_simulation_input_only")
        self.assertTrue(report["contract_gate"]["simulation_not_run"])
        self.assertFalse(report["contract_gate"]["implementation_allowed"])
        self.assertFalse(report["contract_gate"]["code_patch_authorized"])
        self.assertEqual(report["contract_gate"]["rag_query_integration"], "disallowed")
        self.assertEqual(report["contract_gate"]["blockers"], [])
        self.assertEqual(report["summary"]["contract_row_count"], 8)
        self.assertEqual(report["summary"]["policy_categories"], EXPECTED_POLICY_ORDER)
        self.assertEqual(report["summary"]["accepted_category_count"], 5)
        self.assertEqual(report["summary"]["confirmed_language_category_count"], 3)
        self.assertTrue(report["summary"]["simulation_not_run"])

        rows = report["simulation_input_contract_rows"]
        self.assertEqual([row["policy_category"] for row in rows], EXPECTED_POLICY_ORDER)
        self.assertEqual(len([row for row in rows if row["source_kind"] == "v0.4.8.7_confirmed_closeout_category"]), 5)
        self.assertEqual(len([row for row in rows if row["source_kind"] == "v0.4.8.10_confirmed_language_revision"]), 3)
        for row in rows:
            self.assertTrue(row["simulation_input_allowed"])
            self.assertFalse(row["implementation_allowed"])
            self.assertFalse(row["code_patch_authorized"])
            self.assertEqual(row["runtime_adoption_status"], "not_allowed")
        self.assertTrue(all(item["status"] == "passed" for item in report["assertions"]))

    def test_wrong_or_blocked_sources_block_contract(self):
        closeout = load_json("tests/final_evidence_selection_policy_closeout_confirmed_record_report.json")
        language = load_json("tests/final_evidence_selection_policy_language_revision_confirmation_record_report.json")
        closeout["version"] = "0.4.8.6"
        closeout["confirmation_gate"]["status"] = "blocked"
        language["confirmation_gate"]["status"] = "blocked"

        report = build_with_sources(closeout, language)

        self.assertEqual(report["contract_gate"]["status"], "blocked")
        self.assertIn("closeout_version_mismatch", report["contract_gate"]["blockers"])
        self.assertIn("closeout_gate_not_confirmed", report["contract_gate"]["blockers"])
        self.assertIn("language_gate_not_confirmed", report["contract_gate"]["blockers"])

    def test_category_order_drift_blocks_contract(self):
        closeout = load_json("tests/final_evidence_selection_policy_closeout_confirmed_record_report.json")
        language = load_json("tests/final_evidence_selection_policy_language_revision_confirmation_record_report.json")
        closeout["confirmed_rows"] = list(reversed(closeout["confirmed_rows"]))

        report = build_with_sources(closeout, language)

        self.assertEqual(report["contract_gate"]["status"], "blocked")
        self.assertIn("accepted_category_order_drift", report["contract_gate"]["blockers"])

    def test_markdown_and_tool_are_non_runtime(self):
        markdown = render_markdown(build_report())
        self.assertIn("v0.4.8.11 Final Evidence Selection Policy Offline Simulation Input Contract", markdown)
        self.assertIn("Simulation not run: True", markdown)
        self.assertIn("`implementation_allowed=false`", markdown)

        target_paths = [
            Path("tools/build_final_evidence_selection_policy_offline_simulation_input_contract.py"),
            Path("docs/final_evidence_selection_policy_offline_simulation_input_contract_v0.4.8.11.md"),
            Path("tests/final_evidence_selection_policy_offline_simulation_input_contract_report.json"),
        ]
        matches = []
        for path in target_paths:
            if path.exists():
                content = path.read_text(encoding="utf-8-sig")
                matches.extend((str(path), pattern) for pattern in PROHIBITED_SOURCE_PATTERNS if pattern in content)
        self.assertEqual(matches, [])


if __name__ == "__main__":
    unittest.main()
