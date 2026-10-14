import unittest

from tools.run_impact_eval import (
    case_matches_documents,
    select_cases_for_impact,
    source_matches,
)


class ImpactEvalTest(unittest.TestCase):
    def test_source_matches_allows_fuzzy_manifest_names(self):
        self.assertTrue(source_matches("个人信息保护法", "中华人民共和国个人信息保护法"))
        self.assertTrue(source_matches("中华人民共和国个人信息保护法", "个人信息保护法"))
        self.assertFalse(source_matches("数据安全法", "中华人民共和国个人信息保护法"))

    def test_case_matches_by_expected_evidence_source(self):
        documents = [{"source": "中华人民共和国个人信息保护法", "domain": "data_compliance", "category": "数据合规"}]
        case = {
            "expected_evidence": [{"source": "个人信息保护法", "article_no": 28}],
            "filters": {"category": "数据合规"},
        }

        self.assertTrue(case_matches_documents(case, documents))

    def test_case_matches_by_impact_domain(self):
        documents = [{"source": "数据出境安全评估办法", "domain": "data_export", "category": "数据合规"}]
        case = {
            "impact_domains": ["data_export"],
            "expected_evidence": [],
        }

        self.assertTrue(case_matches_documents(case, documents))

    def test_select_cases_for_impact_filters_unrelated_cases(self):
        documents = [{"source": "中华人民共和国数据安全法", "domain": "data_compliance", "category": "数据合规"}]
        cases = [
            {"id": "hit", "expected_evidence": [{"source": "中华人民共和国数据安全法", "article_no": 21}]},
            {"id": "miss", "expected_evidence": [{"source": "个人信息出境标准合同办法", "article_no": 8}]},
        ]

        selected = select_cases_for_impact(cases, documents)

        self.assertEqual([case["id"] for case in selected], ["hit"])


if __name__ == "__main__":
    unittest.main()
