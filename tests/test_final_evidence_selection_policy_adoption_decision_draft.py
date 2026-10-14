import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_final_evidence_selection_policy_adoption_decision_draft import (
    DEFAULT_GATE_REPORT_PATH,
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


def build_with_sources(gate: dict, simulation: dict) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        gate_path = Path(tmpdir) / "gate.json"
        simulation_path = Path(tmpdir) / "simulation.json"
        write_json(gate_path, copy.deepcopy(gate))
        write_json(simulation_path, copy.deepcopy(simulation))
        return build_report(gate_path, simulation_path)


class FinalEvidenceSelectionPolicyAdoptionDecisionDraftTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(
            DEFAULT_GATE_REPORT_PATH,
            legacy_report_path("final_evidence_selection_policy_offline_simulation_gate_report.json"),
        )
        self.assertEqual(
            DEFAULT_SIMULATION_REPORT_PATH,
            legacy_report_path("final_evidence_selection_policy_offline_simulation_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("final_evidence_selection_policy_adoption_decision_draft_report.json"),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/final_evidence_selection_policy_adoption_decision_draft_v0.4.8.14.md"),
        )

    def test_real_sources_build_pending_user_confirmation_draft(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.8.14")
        self.assertEqual(report["schema_kind"], "final_evidence_selection_policy_adoption_decision_draft")
        self.assertEqual(report["draft_gate"]["status"], "pending_user_confirmation")
        self.assertTrue(report["draft_gate"]["requires_user_confirmation"])
        self.assertFalse(report["draft_gate"]["implementation_allowed"])
        self.assertFalse(report["draft_gate"]["code_patch_authorized"])
        self.assertEqual(report["draft_gate"]["allowed_next_step"], "series_closeout")
        self.assertEqual(report["draft_gate"]["blockers"], [])
        self.assertEqual(report["summary"]["draft_row_count"], 8)
        self.assertEqual(report["summary"]["policy_categories"], EXPECTED_POLICY_ORDER)
        self.assertEqual(report["summary"]["requires_user_confirmation_count"], 8)

        rows = report["adoption_decision_draft_rows"]
        self.assertEqual([row["policy_category"] for row in rows], EXPECTED_POLICY_ORDER)
        for row in rows:
            self.assertEqual(row["draft_status"], "pending_user_confirmation")
            self.assertTrue(row["requires_user_confirmation"])
            self.assertEqual(row["runtime_adoption_status"], "not_allowed")
            self.assertFalse(row["implementation_allowed"])
            self.assertFalse(row["code_patch_authorized"])
            self.assertIn("after_separate_approval", row["suggested_adoption_option"])
        self.assertTrue(all(item["status"] == "passed" for item in report["assertions"]))

    def test_blocked_gate_blocks_draft(self):
        gate = load_json("tests/final_evidence_selection_policy_offline_simulation_gate_report.json")
        simulation = load_json("tests/final_evidence_selection_policy_offline_simulation_report.json")
        gate["gate"]["status"] = "blocked"
        gate["gate"]["blockers"] = ["policy_category_order"]

        report = build_with_sources(gate, simulation)

        self.assertEqual(report["draft_gate"]["status"], "blocked")
        self.assertIn("gate_not_open_for_decision_draft", report["draft_gate"]["blockers"])
        self.assertIn("gate_has_blockers", report["draft_gate"]["blockers"])

    def test_simulation_order_drift_blocks_draft(self):
        gate = load_json("tests/final_evidence_selection_policy_offline_simulation_gate_report.json")
        simulation = load_json("tests/final_evidence_selection_policy_offline_simulation_report.json")
        simulation["simulation_result_rows"] = list(reversed(simulation["simulation_result_rows"]))

        report = build_with_sources(gate, simulation)

        self.assertEqual(report["draft_gate"]["status"], "blocked")
        self.assertIn("simulation_category_order_drift", report["draft_gate"]["blockers"])

    def test_simulation_blocking_failure_blocks_draft(self):
        gate = load_json("tests/final_evidence_selection_policy_offline_simulation_gate_report.json")
        simulation = load_json("tests/final_evidence_selection_policy_offline_simulation_report.json")
        simulation["summary"]["blocking_failure_count"] = 1

        report = build_with_sources(gate, simulation)

        self.assertEqual(report["draft_gate"]["status"], "blocked")
        self.assertIn("simulation_has_blocking_failures", report["draft_gate"]["blockers"])

    def test_markdown_and_tool_are_non_runtime(self):
        markdown = render_markdown(build_report())
        self.assertIn("v0.4.8.14 Final Evidence Selection Policy Adoption Decision Draft", markdown)
        self.assertIn("requires explicit user confirmation", markdown)
        self.assertIn("Any future runtime design still needs a separate approved implementation version", markdown)

        target_paths = [
            Path("tools/build_final_evidence_selection_policy_adoption_decision_draft.py"),
            Path("docs/final_evidence_selection_policy_adoption_decision_draft_v0.4.8.14.md"),
            Path("tests/final_evidence_selection_policy_adoption_decision_draft_report.json"),
        ]
        matches = []
        for path in target_paths:
            if path.exists():
                content = path.read_text(encoding="utf-8-sig")
                matches.extend((str(path), pattern) for pattern in PROHIBITED_SOURCE_PATTERNS if pattern in content)
        self.assertEqual(matches, [])


if __name__ == "__main__":
    unittest.main()
