import unittest
from unittest.mock import patch

from langchain_core.documents import Document

from src.rag.experiment_profiles import list_experiment_profiles, resolve_experiment_profile
from src.rag.retriever import rag_query


class _FakeVectorStore:
    def similarity_search_with_score(self, *args, **kwargs):
        return [
            (
                Document(
                    page_content="当事人应当遵循诚信原则。",
                    metadata={
                        "source": "中华人民共和国民法典",
                        "law_name": "中华人民共和国民法典",
                        "article_no": 509,
                        "article": "第五百零九条",
                        "type": "article",
                        "block_type": "article",
                        "citation": "[《中华人民共和国民法典》第五百零九条]",
                    },
                ),
                0.91,
            )
        ]


class RetrievalAblationProfileTest(unittest.TestCase):
    def test_profiles_are_explicit_and_ordered(self):
        self.assertIsNone(resolve_experiment_profile(None))
        self.assertFalse(resolve_experiment_profile("M1_dense").enable_sparse_recall)
        self.assertTrue(resolve_experiment_profile("M2_hybrid").enable_sparse_recall)
        self.assertTrue(resolve_experiment_profile("M3_concept").enable_concept_anchors)
        self.assertTrue(resolve_experiment_profile("M4_full").enable_reranker)
        with self.assertRaises(ValueError):
            resolve_experiment_profile("unknown")

    def test_controlled_profiles_add_one_capability_at_a_time(self):
        names = [f"C{index}_{suffix}" for index, suffix in enumerate([
            "dense",
            "hybrid",
            "query_expansion",
            "concept_anchors",
            "scene_anchors",
            "complex_planner",
            "cross_encoder",
        ])]
        profiles = [resolve_experiment_profile(name) for name in names]
        switches = (
            "enable_sparse_recall",
            "enable_concept_expansion",
            "enable_concept_anchors",
            "enable_deterministic_anchors",
            "enable_complex_planner",
            "enable_reranker",
        )
        for previous, current in zip(profiles, profiles[1:]):
            changed = [name for name in switches if getattr(previous, name) != getattr(current, name)]
            self.assertEqual(len(changed), 1, f"{previous.name} -> {current.name}: {changed}")
        self.assertEqual([profile.name for profile in list_experiment_profiles()[:7]], names)

    @patch("src.rag.retriever.get_vectorstore", return_value=_FakeVectorStore())
    @patch("src.rag.retriever.retrieve_with_sparse")
    @patch("src.rag.retriever._call_siliconflow_rerank")
    def test_profile_switches_isolate_sparse_and_rerank(self, rerank, sparse, _vectorstore):
        sparse.return_value = []
        rerank.return_value = [1.8]

        dense_result = rag_query("普通法律问题", experiment_profile="M1_dense", retrieval_only=True, debug=True)
        sparse_result = rag_query("普通法律问题", experiment_profile="M2_hybrid", retrieval_only=True, debug=True)
        full_result = rag_query("普通法律问题", experiment_profile="M4_full", retrieval_only=True, debug=True)

        self.assertEqual(dense_result["debug_info"]["final_evidence_selection_trace"]["mode"], "candidate_order_without_rerank")
        self.assertEqual(sparse_result["debug_info"]["final_evidence_selection_trace"]["mode"], "candidate_order_without_rerank")
        self.assertEqual(full_result["debug_info"]["final_evidence_selection_trace"]["mode"], "cross_encoder")
        self.assertEqual(sparse.call_count, 2)
        self.assertEqual(rerank.call_count, 1)

    def test_default_profile_is_production_compatibility_mode(self):
        self.assertIsNone(resolve_experiment_profile(None))


if __name__ == "__main__":
    unittest.main()
