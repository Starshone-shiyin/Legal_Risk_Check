import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.check_final_evidence_selection_policy_offline_simulation_gate import (
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


def build_with_simulation(simulation: dict) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "simulation.json"
        write_json(path, copy.deepcopy(simulation))
        return build_report(path)


class FinalEvidenceSelectionPolicyOfflineSimulationGateTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(
            DEFAULT_SIMULATION_REPORT_PATH,
            legacy_report_path("final_evidence_selection_policy_offline_simulation_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("final_evidence_selection_policy_offline_simulation_gate_report.json"),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/final_evidence_selection_policy_offline_simulation_gate_v0.4.8.13.md"),
        )

    def test_real_simulation_report_passes_gate(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.8.13")
        self.assertEqual(report["schema_kind"], "final_evidence_selection_policy_offline_simulation_gate")
        self.assertEqual(report["gate"]["status"], "open_for_policy_adoption_decision_draft")
        self.assertEqual(report["gate"]["allowed_next_step"], "policy_adoption_decision_draft")
        self.assertFalse(report["gate"]["implementation_allowed"])
        self.assertFalse(report["gate"]["code_patch_authorized"])
        self.assertEqual(report["gate"]["blockers"], [])
        self.assertEqual(report["summary"]["failed_check_count"], 0)
        self.assertEqual(report["summary"]["simulation_row_count"], 8)
        self.assertEqual(report["summary"]["policy_categories"], EXPECTED_POLICY_ORDER)
        self.assertEqual(report["summary"]["result_summary"], {"pass": 8})
        self.assertEqual(report["summary"]["manual_review_signal_count"], 2)
        self.assertEqual(report["summary"]["blocking_failure_count"], 0)
        self.assertTrue(all(check["status"] == "passed" for check in report["checks"]))

    def test_blocking_failure_blocks_gate(self):
        simulation = load_json("tests/final_evidence_selection_policy_offline_simulation_report.json")
        simulation["summary"]["blocking_failure_count"] = 1

        report = build_with_simulation(simulation)

        self.assertEqual(report["gate"]["status"], "blocked")
        self.assertIn("blocking_failure_count", report["gate"]["blockers"])

    def test_missing_required_row_field_blocks_gate(self):
        simulation = load_json("tests/final_evidence_selection_policy_offline_simulation_report.json")
        del simulation["simulation_result_rows"][0]["simulated_policy_effect"]

        report = build_with_simulation(simulation)

        self.assertEqual(report["gate"]["status"], "blocked")
        self.assertIn("all_rows_have_required_fields", report["gate"]["blockers"])

    def test_category_order_drift_blocks_gate(self):
        simulation = load_json("tests/final_evidence_selection_policy_offline_simulation_report.json")
        simulation["simulation_result_rows"] = list(reversed(simulation["simulation_result_rows"]))

        report = build_with_simulation(simulation)

        self.assertEqual(report["gate"]["status"], "blocked")
        self.assertIn("policy_category_order", report["gate"]["blockers"])

    def test_runtime_adoption_pollution_blocks_gate(self):
        simulation = load_json("tests/final_evidence_selection_policy_offline_simulation_report.json")
        simulation["simulation_result_rows"][0]["implementation_allowed"] = True
        simulation["simulation_gate"]["code_patch_authorized"] = True

        report = build_with_simulation(simulation)

        self.assertEqual(report["gate"]["status"], "blocked")
        self.assertIn("row_runtime_adoption_blocked", report["gate"]["blockers"])
        self.assertIn("gate_runtime_adoption_blocked", report["gate"]["blockers"])

    def test_markdown_and_tool_are_non_runtime(self):
        markdown = render_markdown(build_report())
        self.assertIn("v0.4.8.13 Final Evidence Selection Policy Offline Simulation Gate", markdown)
        self.assertIn("Implementation allowed: False", markdown)
        self.assertIn("Passing this gate only allows a policy adoption decision draft", markdown)

        target_paths = [
            Path("tools/check_final_evidence_selection_policy_offline_simulation_gate.py"),
            Path("docs/final_evidence_selection_policy_offline_simulation_gate_v0.4.8.13.md"),
            Path("tests/final_evidence_selection_policy_offline_simulation_gate_report.json"),
        ]
        matches = []
        for path in target_paths:
            if path.exists():
                content = path.read_text(encoding="utf-8-sig")
                matches.extend((str(path), pattern) for pattern in PROHIBITED_SOURCE_PATTERNS if pattern in content)
        self.assertEqual(matches, [])


if __name__ == "__main__":
    unittest.main()
