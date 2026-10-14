import json
import unittest
from pathlib import Path

from langchain_core.documents import Document

from src.rag.domain_router import route_question
from src.rag.ingestion import clean_legal_line, extract_article_metadata
from src.rag.legal_concepts import (
    detect_legal_concepts,
    find_missing_concept_primary_anchors,
    get_concept_anchors,
    get_concept_query_terms,
)
from src.rag.query_planning import build_search_query
from src.rag.retriever import _concept_evidence_budget, _ensure_concept_primary_evidence


class LegalConceptsTest(unittest.TestCase):
    def test_incidental_duty_maps_to_civil_code_article_509(self):
        question = "什么是附随义务？"

        matches = detect_legal_concepts(question)

        self.assertEqual(matches[0]["id"], "contract_incidental_duty")
        self.assertEqual(get_concept_anchors(question), {"中华人民共和国民法典": [509, 558]})
        self.assertEqual(route_question(question).domain, "民商事")

    def test_gift_with_obligation_does_not_use_incidental_duty_anchor(self):
        question = "什么是赠与附义务？"

        matches = detect_legal_concepts(question)

        self.assertEqual(matches[0]["id"], "gift_with_obligation")
        self.assertEqual(get_concept_anchors(question), {"中华人民共和国民法典": [661]})

    def test_concept_expansion_adds_statutory_language(self):
        terms = get_concept_query_terms("什么是附随义务？")
        search_query = build_search_query("什么是附随义务？", domain="民商事")

        self.assertIn("诚信原则", terms)
        self.assertIn("通知义务", terms)
        self.assertIn("保密义务", terms)
        self.assertIn("合同履行", search_query)

    def test_missing_primary_anchor_is_reported_as_recall_gap(self):
        gaps = find_missing_concept_primary_anchors("什么是附随义务？", [])

        self.assertEqual(
            gaps,
            ["已识别法学术语，但对应直接法源未召回：中华人民共和国民法典第509条"],
        )

    def test_recalled_primary_anchor_clears_recall_gap(self):
        evidence = [{"source": "中华人民共和国民法典", "article_no": 509}]

        self.assertEqual(find_missing_concept_primary_anchors("什么是附随义务？", evidence), [])

    def test_primary_concept_source_is_retained_after_rerank(self):
        question = "什么是附随义务？"
        unrelated = Document(
            page_content="董事会义务",
            metadata={"source": "中华人民共和国公司法", "article_no": 144, "chunk_id": "unrelated"},
        )
        primary = Document(
            page_content="通知、协助、保密等义务",
            metadata={"source": "中华人民共和国民法典", "article_no": 509, "chunk_id": "primary"},
        )

        selected = _ensure_concept_primary_evidence(
            [(unrelated, 0.99)],
            [(primary, 1.0)],
            question,
            top_k=3,
        )

        self.assertEqual(selected[0][0].metadata["article_no"], 509)

    def test_longer_term_suppresses_only_the_overlapping_short_term(self):
        specific = detect_legal_concepts("什么是非法人组织？")
        self.assertEqual([concept["id"] for concept in specific], ["unincorporated_organization"])

        parallel = detect_legal_concepts("法人和非法人组织有何区别？")
        self.assertEqual(
            [concept["id"] for concept in parallel],
            ["unincorporated_organization", "legal_person"],
        )

        subject_comparison = detect_legal_concepts("民法上的自然人、法人、非法人组织有何异同？")
        self.assertIn("civil_subject", [concept["id"] for concept in subject_comparison])

    def test_civil_concept_anchors_cover_common_definition_questions(self):
        cases = {
            "什么是表见代理？": ("apparent_agency", [172]),
            "什么是不当得利？": ("unjust_enrichment", [122, 985]),
            "什么是诉讼时效？": ("limitation_of_action", [188, 192, 193, 194, 195, 196, 197, 198, 199]),
            "什么是股东有限责任？": ("shareholder_limited_liability", [4]),
        }
        for question, (concept_id, articles) in cases.items():
            with self.subTest(question=question):
                matches = detect_legal_concepts(question)
                self.assertEqual(matches[0]["id"], concept_id)
                self.assertEqual(
                    get_concept_anchors(question)[matches[0]["anchors"][0]["source"]],
                    articles,
                )

    def test_data_concept_anchors_cover_definition_questions(self):
        cases = {
            "什么是敏感个人信息？": ("sensitive_personal_information", [28, 29, 30]),
            "什么是个人信息处理原则？": ("personal_information_principles", [5, 6, 7, 8]),
            "什么是数据分类分级？": ("data_classification_grading", [21]),
        }
        for question, (concept_id, articles) in cases.items():
            with self.subTest(question=question):
                matches = detect_legal_concepts(question)
                self.assertEqual(matches[0]["id"], concept_id)
                self.assertEqual(
                    get_concept_anchors(question)[matches[0]["anchors"][0]["source"]],
                    articles,
                )

    def test_personality_rights_question_recalls_privacy_reputation_and_remedy_law(self):
        question = (
            "甲曾因酒驾犯罪而受到刑事处罚，乙在小区微信群中说甲是罪犯。"
            "关于本案，下列说法正确的有？A乙侵犯了甲的名誉权 "
            "B乙侵犯了甲的隐私权 C甲请求乙赔礼道歉、消除影响不受诉讼时效期间的限制 "
            "D乙侵犯了甲的个人信息权益"
        )

        concept_ids = {concept["id"] for concept in detect_legal_concepts(question)}
        self.assertTrue({
            "personality_rights_remedies",
            "reputation_right",
            "privacy_right",
            "criminal_record_privacy",
            "civil_personal_information_rights",
        }.issubset(concept_ids))

        anchors = get_concept_anchors(question)["中华人民共和国民法典"]
        for article_no in (995, 1024, 1032, 1033, 1034, 1035, 1036, 1037):
            self.assertIn(article_no, anchors)

        self.assertNotIn("personal_information_subject_rights", concept_ids)

    def test_multi_concept_question_reserves_evidence_for_each_primary_article(self):
        question = "名誉权、隐私权、赔礼道歉、个人信息权益和诉讼时效的区别"

        self.assertEqual(_concept_evidence_budget(question, 3), 5)
        self.assertEqual(_concept_evidence_budget("什么是隐私权？", 3), 3)

    def test_configured_concept_anchors_exist_in_knowledge_base(self):
        root = Path(__file__).parents[1]
        config = json.loads((root / "config" / "legal_concepts.json").read_text(encoding="utf-8"))
        article_index = {}
        for path in (root / "src" / "knowledge").rglob("*.txt"):
            article_numbers = set()
            for line in path.read_text(encoding="utf-8").splitlines():
                _, article_no = extract_article_metadata(clean_legal_line(line))
                if article_no is not None:
                    article_numbers.add(article_no)
            article_index[path.stem] = article_numbers

        missing = []
        for concept in config.get("concepts", []):
            for anchor in concept.get("anchors", []):
                source = anchor.get("source")
                for article_no in anchor.get("articles", []):
                    if article_no not in article_index.get(source, set()):
                        missing.append((concept.get("id"), source, article_no))

        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
