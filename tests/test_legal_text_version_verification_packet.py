import tempfile
import unittest
from pathlib import Path

from tools.build_legal_text_version_verification_packet import build_report, write_json


def review_row(*, legal_reasoning="《反不正当竞争法》第6条规定混淆行为。"):
    return {
        "case_id": "case_a",
        "expected_case_metadata": {
            "legal_reasoning": legal_reasoning,
            "expected_evidence": [{"source": "中华人民共和国反不正当竞争法", "article_no": 7}],
        },
        "final_evidence_refs_by_run": [
            [{"source": "中华人民共和国反不正当竞争法", "article_no": 7}],
            [{"source": "中华人民共和国反不正当竞争法", "article_no": 7}],
        ],
    }


def snapshot():
    return {
        "law": "中华人民共和国反不正当竞争法",
        "sources": [{"url": "https://example.test/law"}],
        "conclusion": {
            "current_law_confusion_behavior_article_no": 7,
            "prior_2019_law_confusion_behavior_article_no": 6,
        },
    }


class LegalTextVersionVerificationPacketTest(unittest.TestCase):
    def build_with(self, rows, snapshot_payload=None):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_path = root / "review.json"
            snapshot_path = root / "snapshot.json"
            write_json(review_path, {"case_rows": rows})
            write_json(snapshot_path, snapshot_payload or snapshot())
            return build_report(review_path, snapshot_path)

    def test_prior_article_reference_with_current_article_evidence_is_version_drift(self):
        report = self.build_with([review_row()])

        row = report["case_rows"][0]
        self.assertEqual(report["summary"]["status"], "legal_text_version_verified")
        self.assertEqual(row["classification"], "metadata_article_numbering_drift_current_evidence_valid")
        self.assertTrue(row["current_evidence_valid"])
        self.assertTrue(row["article_numbering_drift"])
        self.assertFalse(row["runtime_patch_allowed"])
        self.assertEqual(report["summary"]["eval_case_change_recommendation"], "manual_review_required_before_change")

    def test_current_article_reasoning_is_current_law_evidence_valid(self):
        report = self.build_with([review_row(legal_reasoning="《反不正当竞争法》第七条规定混淆行为。")])

        row = report["case_rows"][0]
        self.assertEqual(row["classification"], "current_law_evidence_valid")
        self.assertFalse(row["article_numbering_drift"])

    def test_missing_current_article_requires_mapping_review(self):
        bad_row = review_row()
        bad_row["expected_case_metadata"]["expected_evidence"] = [{"source": "中华人民共和国反不正当竞争法", "article_no": 6}]
        bad_row["final_evidence_refs_by_run"] = [[{"source": "中华人民共和国反不正当竞争法", "article_no": 6}]]

        report = self.build_with([bad_row])

        self.assertEqual(report["case_rows"][0]["classification"], "legal_text_mapping_review_required")


if __name__ == "__main__":
    unittest.main()
