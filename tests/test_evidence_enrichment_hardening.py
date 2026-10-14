import unittest

from tools.check_evidence_coverage import (
    build_evidence_enrichment_index,
    enrich_article_item,
)
from tools.check_evidence_enrichment_hardening import build_report


class EvidenceEnrichmentHardeningTest(unittest.TestCase):
    def test_citation_location_fallback_matches_standard_section(self):
        index = {
            ("信息安全技术 个人信息安全规范", "", "C.1 概述"): {
                "source": "信息安全技术 个人信息安全规范 GB_T_35273_2020",
                "section_no": "C.1 概述",
                "content_preview": "C.1 概述 保障个人信息主体自主意愿。",
                "functional_type": "technical_standard",
                "functional_type_confidence": "metadata",
                "functional_type_matched_rule": "metadata.document_type",
                "enrichment_status": "matched",
            }
        }
        item = {
            "source": "信息安全技术 个人信息安全规范 GB_T_35273_2020",
            "article_no": None,
            "section_no": "",
            "citation": "[《信息安全技术 个人信息安全规范》C.1 概述]",
        }

        enriched = enrich_article_item(item, index)

        self.assertEqual(enriched["enrichment_status"], "matched")
        self.assertEqual(enriched["functional_type"], "technical_standard")
        self.assertIn("自主意愿", enriched["content_preview"])

    def test_build_real_manifest_index_has_entries(self):
        index, summary = build_evidence_enrichment_index()

        self.assertTrue(index)
        self.assertEqual(summary["missing_files"], [])

    def test_hardening_report_detects_missing_fields(self):
        import json
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "coverage.json"
            path.write_text(
                json.dumps(
                    {
                        "version": "test",
                        "cases": [
                            {
                                "case_id": "case_a",
                                "final_evidence": [
                                    {"source": "示例法", "enrichment_status": "not_found"}
                                ],
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            report = build_report(path)

        self.assertEqual(report["summary"]["unmatched_evidence"], 1)
        self.assertFalse(report["summary"]["field_stability_passed"])


if __name__ == "__main__":
    unittest.main()
