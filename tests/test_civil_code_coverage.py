import unittest

from tools.judge_civil_code_coverage import build_judgment
from src.rag.legal_concepts import detect_legal_concepts, get_concept_anchors


class CivilCodeCoverageTest(unittest.TestCase):
    def test_civil_code_coverage_judge_accepts_current_source_and_mapping(self):
        judgment = build_judgment()

        self.assertEqual(judgment["verdict"], "accepted")
        self.assertEqual(judgment["summary"]["source_article_count"], 1260)
        self.assertEqual(len(judgment["books"]), 7)

    def test_representative_question_from_each_book_has_a_direct_anchor(self):
        cases = {
            "监护人的职责包括什么？": ("guardianship", 34),
            "什么是抵押权？": ("mortgage", 394),
            "格式条款提供方有什么提示说明义务？": ("standard_terms", 496),
            "公开他人私密信息是否侵害隐私权？": ("privacy_right", 1032),
            "夫妻共同财产的范围如何认定？": ("marital_property", 1062),
            "法定继承人的继承顺序是什么？": ("statutory_inheritance", 1127),
            "一般侵权责任的过错原则是什么？": ("tort_liability", 1165),
        }
        for question, (concept_id, article_no) in cases.items():
            with self.subTest(question=question):
                self.assertEqual(detect_legal_concepts(question)[0]["id"], concept_id)
                self.assertIn(article_no, get_concept_anchors(question)["中华人民共和国民法典"])


if __name__ == "__main__":
    unittest.main()
