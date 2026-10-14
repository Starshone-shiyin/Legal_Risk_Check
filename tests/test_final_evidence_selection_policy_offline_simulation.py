import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_final_evidence_selection_policy_offline_simulation import (
    DEFAULT_INPUT_CONTRACT_PATH,
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


def build_with_contract(contract: dict) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "contract.json"
        write_json(path, copy.deepcopy(contract))
        return build_report(path)


class FinalEvidenceSelectionPolicyOfflineSimulationTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(
            DEFAULT_INPUT_CONTRACT_PATH,
            legacy_report_path("final_evidence_selection_policy_offline_simulation_input_contract_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("final_evidence_selection_policy_offline_simulation_report.json"),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/final_evidence_selection_policy_offline_simulation_v0.4.8.12.md"),
        )

    def test_real_contract_builds_saved_report_simulation(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.8.12")
        self.assertEqual(report["schema_kind"], "final_evidence_selection_policy_offline_simulation")
        self.assertEqual(report["simulation_gate"]["status"], "completed_saved_report_simulation")
        self.assertTrue(report["simulation_gate"]["saved_report_offline_simulation"])
        self.assertFalse(report["simulation_gate"]["implementation_allowed"])
        self.assertFalse(report["simulation_gate"]["code_patch_authorized"])
        self.assertEqual(report["simulation_gate"]["blockers"], [])
        self.assertEqual(report["summary"]["simulation_row_count"], 8)
        self.assertEqual(report["summary"]["policy_categories"], EXPECTED_POLICY_ORDER)
        self.assertEqual(report["summary"]["blocking_failure_count"], 0)
        self.assertEqual(report["summary"]["manual_review_signal_count"], 2)
        self.assertEqual(report["summary"]["simulated_result_summary"], {"pass": 8})

        rows = report["simulation_result_rows"]
        self.assertEqual([row["policy_category"] for row in rows], EXPECTED_POLICY_ORDER)
        self.assertEqual([row["simulated_result"] for row in rows], ["pass"] * 8)
        self.assertEqual(
            [row["policy_category"] for row in rows if row["manual_review_signal"]],
            ["coverage_floor", "high_risk_manual_review"],
        )
        for row in rows:
            self.assertEqual(row["runtime_adoption_status"], "not_allowed")
            self.assertFalse(row["implementation_allowed"])
            self.assertFalse(row["code_patch_authorized"])
        self.assertTrue(all(item["status"] == "passed" for item in report["assertions"]))

    def test_blocked_contract_blocks_simulation(self):
        contract = load_json("tests/final_evidence_selection_policy_offline_simulation_input_contract_report.json")
        contract["contract_gate"]["status"] = "blocked"
        contract["contract_gate"]["implementation_allowed"] = True

        report = build_with_contract(contract)

        self.assertEqual(report["simulation_gate"]["status"], "blocked")
        self.assertIn("input_contract_not_ready", report["simulation_gate"]["blockers"])
        self.assertIn("input_contract_implementation_not_blocked", report["simulation_gate"]["blockers"])
        self.assertGreater(report["summary"]["blocking_failure_count"], 0)

    def test_category_order_drift_blocks_simulation(self):
        contract = load_json("tests/final_evidence_selection_policy_offline_simulation_input_contract_report.json")
        contract["simulation_input_contract_rows"] = list(reversed(contract["simulation_input_contract_rows"]))

        report = build_with_contract(contract)

        self.assertEqual(report["simulation_gate"]["status"], "blocked")
        self.assertIn("input_contract_category_order_drift", report["simulation_gate"]["blockers"])

    def test_markdown_and_tool_are_non_runtime(self):
        markdown = render_markdown(build_report())
        self.assertIn("v0.4.8.12 Final Evidence Selection Policy Offline Simulation", markdown)
        self.assertIn("Implementation allowed: False", markdown)
        self.assertIn("Runtime adoption remains blocked", markdown)

        target_paths = [
            Path("tools/build_final_evidence_selection_policy_offline_simulation.py"),
            Path("docs/final_evidence_selection_policy_offline_simulation_v0.4.8.12.md"),
            Path("tests/final_evidence_selection_policy_offline_simulation_report.json"),
        ]
        matches = []
        for path in target_paths:
            if path.exists():
                content = path.read_text(encoding="utf-8-sig")
                matches.extend((str(path), pattern) for pattern in PROHIBITED_SOURCE_PATTERNS if pattern in content)
        self.assertEqual(matches, [])


if __name__ == "__main__":
    unittest.main()
