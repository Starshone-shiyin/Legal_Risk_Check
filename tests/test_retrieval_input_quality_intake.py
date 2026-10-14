import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_retrieval_input_quality_intake import (
    DEFAULT_ANCHOR_DEPENDENCY_AUDIT_PATH,
    DEFAULT_BASE_RETRIEVAL_AUDIT_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_ROOT_CAUSE_ACTION_PLAN_PATH,
    DEFAULT_SERIES_CLOSEOUT_PATH,
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


def build_with_sources(base: dict, anchor: dict, action_plan: dict, closeout: dict) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir) / "base.json"
        anchor_path = Path(tmpdir) / "anchor.json"
        action_path = Path(tmpdir) / "action.json"
        closeout_path = Path(tmpdir) / "closeout.json"
        write_json(base_path, copy.deepcopy(base))
        write_json(anchor_path, copy.deepcopy(anchor))
        write_json(action_path, copy.deepcopy(action_plan))
        write_json(closeout_path, copy.deepcopy(closeout))
        return build_report(base_path, anchor_path, action_path, closeout_path)


class RetrievalInputQualityIntakeTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(
            DEFAULT_BASE_RETRIEVAL_AUDIT_PATH,
            legacy_report_path("base_retrieval_quality_audit_report.json"),
        )
        self.assertEqual(
            DEFAULT_ANCHOR_DEPENDENCY_AUDIT_PATH,
            legacy_report_path("anchor_dependency_audit_report.json"),
        )
        self.assertEqual(
            DEFAULT_ROOT_CAUSE_ACTION_PLAN_PATH,
            legacy_report_path("evidence_root_cause_action_plan.json"),
        )
        self.assertEqual(
            DEFAULT_SERIES_CLOSEOUT_PATH,
            legacy_report_path("final_evidence_selection_policy_series_closeout_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("retrieval_input_quality_intake_report.json"),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/retrieval_input_quality_intake_v0.4.9.0.md"),
        )

    def test_real_sources_build_intake(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.9.0")
        self.assertEqual(report["schema_kind"], "retrieval_input_quality_intake")
        self.assertEqual(report["intake_gate"]["status"], "ready_for_retrieval_input_quality_planning")
        self.assertFalse(report["intake_gate"]["implementation_allowed"])
        self.assertFalse(report["intake_gate"]["code_patch_authorized"])
        self.assertFalse(report["intake_gate"]["retrieval_logic_change_allowed"])
        self.assertEqual(report["intake_gate"]["blockers"], [])
        self.assertEqual(report["summary"]["bucket_count"], 5)
        self.assertGreaterEqual(report["summary"]["ready_bucket_count"], 4)
        self.assertEqual(report["summary"]["total_base_gap_cases"], 34)
        self.assertEqual(report["summary"]["total_anchor_dependency_cases"], 33)
        self.assertEqual(report["summary"]["metadata_or_chunking_review_candidates"], 33)
        self.assertEqual(report["summary"]["zero_base_recall_cases"], 25)
        self.assertEqual(report["summary"]["anchor_masking_base_retrieval_gap_cases"], 33)
        self.assertGreater(report["summary"]["sample_case_count"], 0)
        self.assertEqual(report["summary"]["next_version_recommendation"], "v0.4.9.1 retrieval input quality audit spec")

        bucket_ids = [row["bucket_id"] for row in report["intake_buckets"]]
        self.assertEqual(
            bucket_ids,
            [
                "source_article_identity_quality",
                "metadata_chunking_quality",
                "query_lexical_coverage_quality",
                "legal_domain_boundary_quality",
                "anchor_dependency_quality",
            ],
        )
        self.assertTrue(all(row["implementation_allowed"] is False for row in report["intake_buckets"]))
        self.assertTrue(all(item["status"] == "passed" for item in report["assertions"]))

    def test_source_version_drift_blocks_intake(self):
        base = load_json("tests/base_retrieval_quality_audit_report.json")
        anchor = load_json("tests/anchor_dependency_audit_report.json")
        action_plan = load_json("tests/evidence_root_cause_action_plan.json")
        closeout = load_json("tests/final_evidence_selection_policy_series_closeout_report.json")
        base["version"] = "0.4.7.4.2"
        closeout["closeout_gate"]["status"] = "blocked"

        report = build_with_sources(base, anchor, action_plan, closeout)

        self.assertEqual(report["intake_gate"]["status"], "blocked")
        self.assertIn("base_retrieval_audit_version_mismatch", report["intake_gate"]["blockers"])
        self.assertIn("v0_4_8_series_not_closed", report["intake_gate"]["blockers"])

    def test_empty_gap_sources_block_intake(self):
        base = load_json("tests/base_retrieval_quality_audit_report.json")
        anchor = load_json("tests/anchor_dependency_audit_report.json")
        action_plan = load_json("tests/evidence_root_cause_action_plan.json")
        closeout = load_json("tests/final_evidence_selection_policy_series_closeout_report.json")
        base["summary"]["total_base_gap_cases"] = 0
        anchor["summary"]["total_anchor_dependency_cases"] = 0

        report = build_with_sources(base, anchor, action_plan, closeout)

        self.assertEqual(report["intake_gate"]["status"], "blocked")
        self.assertIn("base_retrieval_audit_has_no_gap_cases", report["intake_gate"]["blockers"])
        self.assertIn("anchor_dependency_audit_has_no_cases", report["intake_gate"]["blockers"])

    def test_markdown_and_tool_are_non_runtime(self):
        markdown = render_markdown(build_report())
        self.assertIn("v0.4.9.0 Retrieval Input Quality Intake", markdown)
        self.assertIn("does not change retrieval behavior", markdown)
        self.assertIn("The next step should specify audit contracts", markdown)

        target_paths = [
            Path("tools/build_retrieval_input_quality_intake.py"),
            Path("docs/retrieval_input_quality_intake_v0.4.9.0.md"),
            Path("tests/retrieval_input_quality_intake_report.json"),
        ]
        matches = []
        for path in target_paths:
            if path.exists():
                content = path.read_text(encoding="utf-8-sig")
                matches.extend((str(path), pattern) for pattern in PROHIBITED_SOURCE_PATTERNS if pattern in content)
        self.assertEqual(matches, [])


if __name__ == "__main__":
    unittest.main()
