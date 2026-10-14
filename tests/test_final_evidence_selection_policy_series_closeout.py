import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_final_evidence_selection_policy_series_closeout import (
    DEFAULT_ADOPTION_DRAFT_PATH,
    DEFAULT_GATE_REPORT_PATH,
    DEFAULT_INPUT_CONTRACT_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_SIMULATION_REPORT_PATH,
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


def build_with_sources(adoption: dict, gate: dict, simulation: dict, contract: dict) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        adoption_path = Path(tmpdir) / "adoption.json"
        gate_path = Path(tmpdir) / "gate.json"
        simulation_path = Path(tmpdir) / "simulation.json"
        contract_path = Path(tmpdir) / "contract.json"
        write_json(adoption_path, copy.deepcopy(adoption))
        write_json(gate_path, copy.deepcopy(gate))
        write_json(simulation_path, copy.deepcopy(simulation))
        write_json(contract_path, copy.deepcopy(contract))
        return build_report(adoption_path, gate_path, simulation_path, contract_path)


class FinalEvidenceSelectionPolicySeriesCloseoutTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(
            DEFAULT_ADOPTION_DRAFT_PATH,
            legacy_report_path("final_evidence_selection_policy_adoption_decision_draft_report.json"),
        )
        self.assertEqual(
            DEFAULT_GATE_REPORT_PATH,
            legacy_report_path("final_evidence_selection_policy_offline_simulation_gate_report.json"),
        )
        self.assertEqual(
            DEFAULT_SIMULATION_REPORT_PATH,
            legacy_report_path("final_evidence_selection_policy_offline_simulation_report.json"),
        )
        self.assertEqual(
            DEFAULT_INPUT_CONTRACT_PATH,
            legacy_report_path("final_evidence_selection_policy_offline_simulation_input_contract_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("final_evidence_selection_policy_series_closeout_report.json"),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/final_evidence_selection_policy_series_closeout_v0.4.8.15.md"),
        )

    def test_real_sources_close_series_for_offline_design(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.8.15")
        self.assertEqual(report["schema_kind"], "final_evidence_selection_policy_series_closeout")
        self.assertEqual(report["closeout_gate"]["status"], "v0_4_8_series_closed_for_offline_design")
        self.assertFalse(report["closeout_gate"]["formal_user_adoption_recorded"])
        self.assertFalse(report["closeout_gate"]["implementation_allowed"])
        self.assertFalse(report["closeout_gate"]["code_patch_authorized"])
        self.assertEqual(report["closeout_gate"]["blockers"], [])
        self.assertEqual(report["summary"]["completed_step_count"], 16)
        self.assertEqual(report["summary"]["policy_categories"], EXPECTED_POLICY_ORDER)
        self.assertEqual(report["summary"]["adoption_draft_row_count"], 8)
        self.assertEqual(report["summary"]["pending_user_confirmation_count"], 8)
        self.assertEqual(report["summary"]["next_recommended_series"], "v0.4.9.x retrieval input quality governance")
        self.assertTrue(all(item["status"] == "passed" for item in report["assertions"]))

    def test_blocked_adoption_draft_blocks_closeout(self):
        adoption = load_json("tests/final_evidence_selection_policy_adoption_decision_draft_report.json")
        gate = load_json("tests/final_evidence_selection_policy_offline_simulation_gate_report.json")
        simulation = load_json("tests/final_evidence_selection_policy_offline_simulation_report.json")
        contract = load_json("tests/final_evidence_selection_policy_offline_simulation_input_contract_report.json")
        adoption["draft_gate"]["status"] = "blocked"

        report = build_with_sources(adoption, gate, simulation, contract)

        self.assertEqual(report["closeout_gate"]["status"], "blocked")
        self.assertIn("adoption_draft_not_pending_user_confirmation", report["closeout_gate"]["blockers"])

    def test_adoption_order_drift_blocks_closeout(self):
        adoption = load_json("tests/final_evidence_selection_policy_adoption_decision_draft_report.json")
        gate = load_json("tests/final_evidence_selection_policy_offline_simulation_gate_report.json")
        simulation = load_json("tests/final_evidence_selection_policy_offline_simulation_report.json")
        contract = load_json("tests/final_evidence_selection_policy_offline_simulation_input_contract_report.json")
        adoption["adoption_decision_draft_rows"] = list(reversed(adoption["adoption_decision_draft_rows"]))

        report = build_with_sources(adoption, gate, simulation, contract)

        self.assertEqual(report["closeout_gate"]["status"], "blocked")
        self.assertIn("adoption_draft_category_order_drift", report["closeout_gate"]["blockers"])

    def test_runtime_pollution_blocks_closeout(self):
        adoption = load_json("tests/final_evidence_selection_policy_adoption_decision_draft_report.json")
        gate = load_json("tests/final_evidence_selection_policy_offline_simulation_gate_report.json")
        simulation = load_json("tests/final_evidence_selection_policy_offline_simulation_report.json")
        contract = load_json("tests/final_evidence_selection_policy_offline_simulation_input_contract_report.json")
        adoption["draft_gate"]["implementation_allowed"] = True

        report = build_with_sources(adoption, gate, simulation, contract)

        self.assertEqual(report["closeout_gate"]["status"], "blocked")
        self.assertIn("adoption_draft_implementation_not_blocked", report["closeout_gate"]["blockers"])

    def test_markdown_and_tool_are_non_runtime(self):
        markdown = render_markdown(build_report())
        self.assertIn("v0.4.8.15 Final Evidence Selection Policy Series Closeout", markdown)
        self.assertIn("closed for offline design, not runtime implementation", markdown)
        self.assertIn("Future runtime policy work needs a separately approved version", markdown)

        target_paths = [
            Path("tools/build_final_evidence_selection_policy_series_closeout.py"),
            Path("docs/final_evidence_selection_policy_series_closeout_v0.4.8.15.md"),
            Path("tests/final_evidence_selection_policy_series_closeout_report.json"),
        ]
        matches = []
        for path in target_paths:
            if path.exists():
                content = path.read_text(encoding="utf-8-sig")
                matches.extend((str(path), pattern) for pattern in PROHIBITED_SOURCE_PATTERNS if pattern in content)
        self.assertEqual(matches, [])


if __name__ == "__main__":
    unittest.main()
