import tempfile
import unittest
from pathlib import Path

from src.rag.legal_functional_typing import (
    FUNCTION_DEFINITION,
    FUNCTION_LIABILITY,
    FUNCTION_OPERATIVE_RULE,
    FUNCTION_PROCEDURAL,
    FUNCTION_TECHNICAL_STANDARD,
    FUNCTION_UNRELATED_OR_CONTEXTUAL,
    classify_evidence_function,
    classify_legal_function,
    has_operative_support,
)
from tools.audit_legal_functional_typing import build_report


class LegalFunctionalTypingTest(unittest.TestCase):
    def test_metadata_functional_type_takes_priority(self):
        result = classify_legal_function(
            "text without obvious cues",
            {"functional_type": FUNCTION_LIABILITY},
        )

        self.assertEqual(result.functional_type, FUNCTION_LIABILITY)
        self.assertEqual(result.confidence, "metadata")

    def test_definition_cue_is_classified(self):
        result = classify_legal_function("本法所称个人信息，是指以电子或者其他方式记录的信息。")

        self.assertEqual(result.functional_type, FUNCTION_DEFINITION)
        self.assertIn("本法所称", result.matched_terms)

    def test_liability_has_higher_priority_than_obligation(self):
        result = classify_legal_function("违反本法规定的，由主管部门责令改正，并处以罚款。")

        self.assertEqual(result.functional_type, FUNCTION_LIABILITY)

    def test_procedural_cue_is_classified(self):
        result = classify_legal_function("个人信息处理者应当向主管部门提交安全评估材料。")

        self.assertEqual(result.functional_type, FUNCTION_PROCEDURAL)

    def test_operational_obligation_cue_is_classified(self):
        result = classify_legal_function("处理个人信息应当采取必要措施保障个人信息安全。")

        self.assertEqual(result.functional_type, FUNCTION_OPERATIVE_RULE)
        self.assertTrue(has_operative_support([result.functional_type]))

    def test_tax_substantive_cue_is_operational_support(self):
        result = classify_legal_function("应纳税额为当期销项税额抵扣当期进项税额后的余额。")

        self.assertEqual(result.functional_type, FUNCTION_OPERATIVE_RULE)
        self.assertTrue(has_operative_support([result.functional_type]))

    def test_tax_liability_priority_over_tax_cue(self):
        result = classify_legal_function("纳税人违反本法规定的，由税务机关责令改正，并依法处以罚款。")

        self.assertEqual(result.functional_type, FUNCTION_LIABILITY)

    def test_structural_context_uses_primary_text_not_source_metadata(self):
        substantive_result = classify_legal_function(
            "应纳税额为当期销项税额抵扣当期进项税额后的余额。",
            {
                "source": "中华人民共和国增值税法",
                "document_type": "法律法规",
            },
        )
        title_result = classify_legal_function(
            "中华人民共和国增值税法",
            {
                "source": "中华人民共和国增值税法",
                "document_type": "法律法规",
            },
        )

        self.assertEqual(substantive_result.functional_type, FUNCTION_OPERATIVE_RULE)
        self.assertEqual(title_result.functional_type, FUNCTION_UNRELATED_OR_CONTEXTUAL)

    def test_standard_metadata_is_technical_standard(self):
        result = classify_evidence_function(
            {
                "source": "信息安全技术 个人信息安全规范 GB_T_35273_2020",
                "document_type": "标准",
                "content": "个人信息控制者宜建立安全能力。",
            }
        )

        self.assertEqual(result.functional_type, FUNCTION_TECHNICAL_STANDARD)

    def test_audit_report_builds_from_manifest_without_main_flow(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            law_file = tmp / "sample_law.txt"
            manifest_file = tmp / "manifest.json"
            law_file.write_text(
                "第一条 本法所称测试信息，是指用于测试的信息。\n\n"
                "第二条 处理测试信息应当采取必要安全措施。\n\n"
                "第三条 违反本法规定的，由主管部门责令改正，并处罚款。\n",
                encoding="utf-8",
            )
            manifest_file.write_text(
                '{"documents":[{"source":"测试法","file_path":"'
                + str(law_file).replace("\\", "\\\\")
                + '","document_type":"法律法规","category":"测试","domain":"test"}]}',
                encoding="utf-8",
            )

            report = build_report(manifest_path=manifest_file)

        self.assertEqual(report["summary"]["total_documents"], 1)
        self.assertGreater(report["summary"]["total_chunks"], 0)
        self.assertIn(FUNCTION_OPERATIVE_RULE, report["summary"]["functional_type_summary"])


if __name__ == "__main__":
    unittest.main()
