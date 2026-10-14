import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools._shared.layout import legacy_report_path
from tools.build_retrieval_input_quality_audit_spec import (
    DEFAULT_INTAKE_REPORT_PATH,
    DEFAULT_MARKDOWN_OUTPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    EXPECTED_BUCKET_ORDER,
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


def build_with_intake(intake: dict) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "intake.json"
        write_json(path, copy.deepcopy(intake))
        return build_report(path)


class RetrievalInputQualityAuditSpecTest(unittest.TestCase):
    def test_default_paths(self):
        self.assertEqual(
            DEFAULT_INTAKE_REPORT_PATH,
            legacy_report_path("retrieval_input_quality_intake_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            legacy_report_path("retrieval_input_quality_audit_spec_report.json"),
        )
        self.assertEqual(
            DEFAULT_MARKDOWN_OUTPUT_PATH,
            Path("docs/retrieval_input_quality_audit_spec_v0.4.9.1.md"),
        )

    def test_real_intake_builds_audit_spec(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.9.1")
        self.assertEqual(report["schema_kind"], "retrieval_input_quality_audit_spec")
        self.assertEqual(report["spec_gate"]["status"], "ready_for_future_offline_audit_design")
        self.assertTrue(report["spec_gate"]["audits_not_run"])
        self.assertFalse(report["spec_gate"]["implementation_allowed"])
        self.assertFalse(report["spec_gate"]["code_patch_authorized"])
        self.assertFalse(report["spec_gate"]["retrieval_logic_change_allowed"])
        self.assertEqual(report["spec_gate"]["blockers"], [])
        self.assertEqual(report["summary"]["audit_spec_count"], 5)
        self.assertEqual(report["summary"]["bucket_ids"], EXPECTED_BUCKET_ORDER)
        self.assertEqual(report["summary"]["priority_summary"], {"P0": 3, "P1": 2})
        self.assertGreaterEqual(report["summary"]["required_output_field_count"], 25)
        self.assertGreaterEqual(report["summary"]["gate_check_count"], 15)

        rows = report["audit_spec_rows"]
        self.assertEqual([row["bucket_id"] for row in rows], EXPECTED_BUCKET_ORDER)
        for row in rows:
            self.assertEqual(row["audit_spec_status"], "ready_for_future_offline_audit")
            self.assertTrue(row["required_inputs"])
            self.assertTrue(row["required_output_fields"])
            self.assertTrue(row["gate_checks"])
            self.assertEqual(row["runtime_adoption_status"], "not_allowed")
            self.assertFalse(row["implementation_allowed"])
            self.assertFalse(row["retrieval_logic_change_allowed"])
        self.assertTrue(all(item["status"] == "passed" for item in report["assertions"]))

    def test_intake_version_drift_blocks_spec(self):
        intake = load_json("tests/retrieval_input_quality_intake_report.json")
        intake["version"] = "0.4.8.15"

        report = build_with_intake(intake)

        self.assertEqual(report["spec_gate"]["status"], "blocked")
        self.assertIn("intake_version_mismatch", report["spec_gate"]["blockers"])

    def test_intake_bucket_order_drift_blocks_spec(self):
        intake = load_json("tests/retrieval_input_quality_intake_report.json")
        intake["intake_buckets"] = list(reversed(intake["intake_buckets"]))

        report = build_with_intake(intake)

        self.assertEqual(report["spec_gate"]["status"], "blocked")
        self.assertIn("intake_bucket_order_drift", report["spec_gate"]["blockers"])

    def test_runtime_pollution_blocks_spec(self):
        intake = load_json("tests/retrieval_input_quality_intake_report.json")
        intake["intake_gate"]["implementation_allowed"] = True
        intake["intake_gate"]["retrieval_logic_change_allowed"] = True

        report = build_with_intake(intake)

        self.assertEqual(report["spec_gate"]["status"], "blocked")
        self.assertIn("intake_implementation_not_blocked", report["spec_gate"]["blockers"])
        self.assertIn("intake_retrieval_logic_not_blocked", report["spec_gate"]["blockers"])

    def test_markdown_and_tool_are_non_runtime(self):
        markdown = render_markdown(build_report())
        self.assertIn("v0.4.9.1 Retrieval Input Quality Audit Spec", markdown)
        self.assertIn("does not run audits or change retrieval behavior", markdown)
        self.assertIn("The next step may build an offline audit runner", markdown)

        target_paths = [
            Path("tools/build_retrieval_input_quality_audit_spec.py"),
            Path("docs/retrieval_input_quality_audit_spec_v0.4.9.1.md"),
            Path("tests/retrieval_input_quality_audit_spec_report.json"),
        ]
        matches = []
        for path in target_paths:
            if path.exists():
                content = path.read_text(encoding="utf-8-sig")
                matches.extend((str(path), pattern) for pattern in PROHIBITED_SOURCE_PATTERNS if pattern in content)
        self.assertEqual(matches, [])


if __name__ == "__main__":
    unittest.main()
