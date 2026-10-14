import unittest

from src.rag.taxonomy import infer_document_classification
from src.risk.taxonomy import classify_risk_categories, infer_taxonomy_risk_level


class TaxonomyInferenceTest(unittest.TestCase):
    def test_law_is_detected_before_generic_standard_words(self):
        result = infer_document_classification(
            "中华人民共和国个人信息保护法",
            "全国人民代表大会常务委员会通过。个人信息处理者可以订立标准合同。",
        )

        self.assertEqual(result.document_type, "法律法规")
        self.assertEqual(result.law_level, "法律")
        self.assertEqual(result.authority_level, "国家级")

    def test_department_rule_with_standard_contract_in_title(self):
        result = infer_document_classification(
            "个人信息出境标准合同办法",
            "国家互联网信息办公室令。本办法规定个人信息出境标准合同备案要求。",
        )

        self.assertEqual(result.document_type, "法律法规")
        self.assertEqual(result.law_level, "部门规章")
        self.assertEqual(result.issuing_authority, "国家互联网信息办公室")

    def test_three_national_standard_types(self):
        mandatory = infer_document_classification("示例强制标准", "GB 12345-2020")
        recommended = infer_document_classification("示例推荐标准", "GB/T 35273-2020")
        guidance = infer_document_classification("示例指导文件", "GB/Z 99999-2020")

        self.assertEqual(mandatory.standard_type, "强制性国家标准")
        self.assertEqual(recommended.standard_type, "推荐性国家标准")
        self.assertEqual(guidance.standard_type, "国家标准化指导性技术文件")

    def test_case_and_patent_types(self):
        case = infer_document_classification("指导性案例1号", "最高人民法院发布指导性案例")
        patent = infer_document_classification("一种数据处理方法", "申请号 CN202410000000 发明人 张三 权利要求书")

        self.assertEqual(case.document_type, "案例")
        self.assertEqual(case.case_type, "指导性案例")
        self.assertEqual(patent.document_type, "专利")
        self.assertEqual(patent.patent_type, "发明专利")


class RiskTaxonomyInferenceTest(unittest.TestCase):
    def test_structured_risk_type_name_can_upgrade_level(self):
        categories = classify_risk_categories(["\u6ee5\u7528\u5e02\u573a\u652f\u914d\u5730\u4f4d\u98ce\u9669"])

        self.assertEqual([item["id"] for item in categories], ["abuse_of_dominance"])
        self.assertEqual(infer_taxonomy_risk_level(categories, fallback="medium"), "high")


if __name__ == "__main__":
    unittest.main()
