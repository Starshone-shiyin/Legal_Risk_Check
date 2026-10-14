import unittest

from langchain_core.documents import Document

from src.rag.retriever import (
    BASE_SPARSE_CANDIDATE_K,
    BASE_UNION_CANDIDATE_LIMIT,
    RERANK_ANCHOR_CANDIDATE_QUOTA,
    RERANK_BASE_CANDIDATE_QUOTA,
    RERANK_INPUT_CANDIDATE_LIMIT,
    _alignment_profile,
    _debug_final_evidence_selection_trace,
    _debug_rerank_full_score_order,
    _limit_base_and_anchor_candidates,
    _limit_candidates_by_article_budget,
    _format_anchor_rerank_hint,
    _rerank_document_text,
    _select_diverse_rerank_top,
    _stabilize_same_bucket_rerank_order,
    _sort_results_by_article_order,
    _sort_rerank_scores_stable,
    build_search_query,
    infer_filters_from_question,
    match_scene_anchors_from_rules,
)
from tools.run_rag_eval import expected_evidence_layer_status, expected_evidence_required_count


def doc(source: str, article_no: int, chunk_id: str) -> Document:
    return Document(
        page_content=f"{source} article {article_no} {chunk_id}",
        metadata={
            "source": source,
            "article_no": article_no,
            "chunk_id": chunk_id,
        },
    )


class CandidateBudgetTest(unittest.TestCase):
    def test_base_candidate_depth_constants_expand_recall_before_rerank(self):
        self.assertEqual(BASE_SPARSE_CANDIDATE_K, 20)
        self.assertEqual(BASE_UNION_CANDIDATE_LIMIT, 15)
        self.assertEqual(RERANK_INPUT_CANDIDATE_LIMIT, 15)
        self.assertEqual(RERANK_BASE_CANDIDATE_QUOTA, 5)
        self.assertEqual(RERANK_ANCHOR_CANDIDATE_QUOTA, 10)

    def test_article_siblings_do_not_crowd_out_distinct_articles(self):
        docs = [
            doc("Law A", 1, "a1"),
            doc("Law A", 1, "a2"),
            doc("Law A", 1, "a3"),
            doc("Law B", 2, "b1"),
            doc("Law C", 3, "c1"),
        ]

        selected = _limit_candidates_by_article_budget(docs, max_total=3)

        self.assertEqual(
            [(item.metadata["source"], item.metadata["article_no"]) for item in selected],
            [("Law A", 1), ("Law B", 2), ("Law C", 3)],
        )

    def test_budget_fills_with_second_sibling_when_space_remains(self):
        docs = [
            doc("Law A", 1, "a1"),
            doc("Law A", 1, "a2"),
            doc("Law B", 2, "b1"),
        ]

        selected = _limit_candidates_by_article_budget(docs, max_total=3)

        self.assertEqual([item.metadata["chunk_id"] for item in selected], ["a1", "b1", "a2"])

    def test_balanced_budget_keeps_base_and_anchor_candidates(self):
        base_docs = [
            doc("Law A", 1, "base-1"),
            doc("Law A", 2, "base-2"),
            doc("Law A", 3, "base-3"),
            doc("Law A", 4, "base-4"),
        ]
        anchor_docs = [
            doc("Law A", 5, "anchor-5"),
            doc("Law A", 6, "anchor-6"),
            doc("Law A", 7, "anchor-7"),
            doc("Law A", 8, "anchor-8"),
        ]

        selected = _limit_base_and_anchor_candidates(
            base_docs,
            anchor_docs,
            max_total=6,
            base_quota=2,
            anchor_quota=4,
        )

        selected_ids = [item.metadata["chunk_id"] for item in selected]
        self.assertEqual(selected_ids[:4], ["anchor-5", "anchor-6", "anchor-7", "anchor-8"])
        self.assertEqual(selected_ids[4:], ["base-1", "base-2"])

    def test_anchor_results_follow_rule_article_order(self):
        results = [
            (doc("Law A", 13, "a13"), 1.0),
            (doc("Law A", 7, "a7"), 1.0),
            (doc("Law A", 9, "a9"), 1.0),
            (doc("Law A", 8, "a8"), 1.0),
        ]

        selected = _sort_results_by_article_order(results, [7, 8, 9, 13])

        self.assertEqual([item.metadata["article_no"] for item, _ in selected], [7, 8, 9, 13])

    def test_rerank_text_uses_parent_article_context(self):
        candidate = Document(
            page_content="item fragment",
            metadata={
                "source": "Law A",
                "citation": "[Law A Article 4 Item 2]",
                "article": "Article 4",
                "parent_content": "Article 4 full legal context with all filing conditions.",
            },
        )

        text = _rerank_document_text(candidate)

        self.assertIn("[Law A Article 4 Item 2]", text)
        self.assertIn("Article 4 full legal context", text)
        self.assertNotIn("item fragment", text)

    def test_rerank_query_can_use_existing_legal_expansion(self):
        question = "\u4e2a\u4eba\u4fe1\u606f\u5904\u7406\u5e94\u9075\u5faa\u54ea\u4e9b\u57fa\u672c\u539f\u5219\uff1f"

        query = build_search_query(question)

        self.assertIn("\u76f8\u5173\u68c0\u7d22\u6982\u5ff5", query)
        self.assertIn("\u8bda\u4fe1", query)

    def test_generic_principle_query_does_not_require_rag_scope_globals(self):
        question = "\u5408\u540c\u5c65\u884c\u5e94\u9075\u5faa\u54ea\u4e9b\u539f\u5219\uff1f"

        query = build_search_query(question)

        self.assertIn(question, query)

    def test_civil_principle_query_expands_legal_principle_terms(self):
        question = "\u6c11\u6cd5\u5178\u89c4\u5b9a\u4e86\u54ea\u4e9b\u6c11\u4e8b\u6d3b\u52a8\u57fa\u672c\u539f\u5219\uff1f"

        query = build_search_query(question, domain="\u6c11\u5546\u4e8b")

        self.assertIn("\u5e73\u7b49", query)
        self.assertIn("\u81ea\u613f", query)
        self.assertIn("\u516c\u5e8f\u826f\u4fd7", query)

    def test_keyword_boost_principle_query_uses_metadata_scope(self):
        from src.rag.retriever import calculate_keyword_boost

        boost, hits = calculate_keyword_boost(
            "\u4e2a\u4eba\u4fe1\u606f\u5904\u7406\u5e94\u9075\u5faa\u54ea\u4e9b\u57fa\u672c\u539f\u5219\uff1f",
            "\u5904\u7406\u4e2a\u4eba\u4fe1\u606f\u5e94\u5f53\u9075\u5faa\u5408\u6cd5\u3001\u6b63\u5f53\u3001\u5fc5\u8981\u548c\u8bda\u4fe1\u539f\u5219\u3002",
            {
                "law_name": "\u4e2d\u534e\u4eba\u6c11\u5171\u548c\u56fd\u4e2a\u4eba\u4fe1\u606f\u4fdd\u62a4\u6cd5",
                "source": "\u4e2d\u534e\u4eba\u6c11\u5171\u548c\u56fd\u4e2a\u4eba\u4fe1\u606f\u4fdd\u62a4\u6cd5",
                "article_no": 5,
                "block_type": "article",
            },
        )

        self.assertGreater(boost, 0.5)
        self.assertIn("\u539f\u5219", hits)

    def test_rerank_top_avoids_repeated_article_siblings(self):
        reranked = [
            (doc("Law A", 1, "a1"), 0.99),
            (doc("Law A", 1, "a2"), 0.98),
            (doc("Law A", 2, "a3"), 0.97),
            (doc("Law A", 3, "a4"), 0.96),
        ]

        selected = _select_diverse_rerank_top(reranked, top_k=3)

        self.assertEqual(
            [item.metadata["article_no"] for item, _ in selected],
            [1, 2, 3],
        )

    def test_rerank_top_retains_high_alignment_evidence_from_rerank_input(self):
        query = (
            "\u67d0\u516c\u53f8\u6ce8\u518c\u5546\u6807\u540e"
            "\u8fde\u7eed\u4e09\u5e74\u672a\u5b9e\u9645\u4f7f\u7528\uff0c"
            "\u8be5\u5546\u6807\u662f\u5426\u5b58\u5728\u88ab\u64a4\u9500\u98ce\u9669\uff1f"
        )
        weak_top = [
            Document(
                page_content="\u5546\u6807\u4e13\u7528\u6743\u4fdd\u62a4\u548c\u4fb5\u6743\u884c\u4e3a\u3002",
                metadata={"source": "Law A", "article_no": 57, "chunk_id": "a57"},
            ),
            Document(
                page_content="\u6ce8\u518c\u5546\u6807\u4e3a\u5546\u6807\u5c40\u6838\u51c6\u6ce8\u518c\u7684\u5546\u6807\u3002",
                metadata={"source": "Law A", "article_no": 3, "chunk_id": "a3"},
            ),
            Document(
                page_content="\u4e0d\u5f97\u4f5c\u4e3a\u5546\u6807\u6ce8\u518c\u7684\u6807\u5fd7\u8303\u56f4\u3002",
                metadata={"source": "Law A", "article_no": 11, "chunk_id": "a11"},
            ),
        ]
        aligned = Document(
            page_content=(
                "\u6ce8\u518c\u5546\u6807\u6210\u4e3a\u5176\u6838\u5b9a\u4f7f\u7528\u7684"
                "\u5546\u54c1\u7684\u901a\u7528\u540d\u79f0\u6216\u8005\u6ca1\u6709\u6b63\u5f53"
                "\u7406\u7531\u8fde\u7eed\u4e09\u5e74\u4e0d\u4f7f\u7528\u7684\uff0c"
                "\u4efb\u4f55\u5355\u4f4d\u6216\u8005\u4e2a\u4eba\u53ef\u4ee5"
                "\u5411\u5546\u6807\u5c40\u7533\u8bf7\u64a4\u9500\u8be5\u6ce8\u518c\u5546\u6807\u3002"
            ),
            metadata={"source": "Law A", "article_no": 49, "chunk_id": "a49"},
        )
        reranked = [(item, 0.99 - index * 0.01) for index, item in enumerate(weak_top + [aligned])]

        selected = _select_diverse_rerank_top(reranked, top_k=3, query=query)

        self.assertIn(49, [item.metadata["article_no"] for item, _ in selected])
        self.assertEqual(len(selected), 3)

    def test_rerank_top_does_not_retain_unrelated_consequence_only_candidate(self):
        query = (
            "\u67d0\u516c\u53f8\u6ce8\u518c\u5546\u6807\u540e"
            "\u8fde\u7eed\u4e09\u5e74\u672a\u5b9e\u9645\u4f7f\u7528\uff0c"
            "\u8be5\u5546\u6807\u662f\u5426\u5b58\u5728\u88ab\u64a4\u9500\u98ce\u9669\uff1f"
        )
        reranked = [
            (
                Document(
                    page_content="\u5546\u6807\u4e13\u7528\u6743\u4fdd\u62a4\u548c\u4fb5\u6743\u884c\u4e3a\u3002",
                    metadata={"source": "Law A", "article_no": 57, "chunk_id": "a57"},
                ),
                0.99,
            ),
            (
                Document(
                    page_content="\u6ce8\u518c\u5546\u6807\u4e3a\u5546\u6807\u5c40\u6838\u51c6\u6ce8\u518c\u7684\u5546\u6807\u3002",
                    metadata={"source": "Law A", "article_no": 3, "chunk_id": "a3"},
                ),
                0.98,
            ),
            (
                Document(
                    page_content="\u4e0d\u5f97\u4f5c\u4e3a\u5546\u6807\u6ce8\u518c\u7684\u6807\u5fd7\u8303\u56f4\u3002",
                    metadata={"source": "Law A", "article_no": 11, "chunk_id": "a11"},
                ),
                0.97,
            ),
            (
                Document(
                    page_content="\u5408\u540c\u89e3\u9664\u540e\u53ef\u4ee5\u8bf7\u6c42\u64a4\u9500\u76f8\u5173\u767b\u8bb0\u3002",
                    metadata={"source": "Law B", "article_no": 91, "chunk_id": "b91"},
                ),
                0.1,
            ),
        ]

        selected = _select_diverse_rerank_top(reranked, top_k=3, query=query)

        self.assertNotIn(91, [item.metadata["article_no"] for item, _ in selected])

    def test_rerank_top_does_not_retain_high_overlap_without_consequence_signal(self):
        query = (
            "\u67d0\u516c\u53f8\u6ce8\u518c\u5546\u6807\u540e"
            "\u8fde\u7eed\u4e09\u5e74\u672a\u5b9e\u9645\u4f7f\u7528\uff0c"
            "\u8be5\u5546\u6807\u662f\u5426\u5b58\u5728\u88ab\u64a4\u9500\u98ce\u9669\uff1f"
        )
        reranked = [
            (doc("Law A", 57, "a57"), 0.99),
            (doc("Law A", 3, "a3"), 0.98),
            (doc("Law A", 11, "a11"), 0.97),
            (
                Document(
                    page_content=(
                        "\u8be5\u516c\u53f8\u6ce8\u518c\u5546\u6807\u540e"
                        "\u8fde\u7eed\u4e09\u5e74\u672a\u5b9e\u9645\u4f7f\u7528\uff0c"
                        "\u5e94\u5efa\u7acb\u4f7f\u7528\u6863\u6848\u548c\u76d1\u6d4b\u673a\u5236\u3002"
                    ),
                    metadata={"source": "Law A", "article_no": 88, "chunk_id": "a88"},
                ),
                0.1,
            ),
        ]

        selected = _select_diverse_rerank_top(reranked, top_k=3, query=query)

        self.assertNotIn(88, [item.metadata["article_no"] for item, _ in selected])

    def test_rerank_top_does_not_replace_when_consequence_already_covered(self):
        query = (
            "\u67d0\u516c\u53f8\u6ce8\u518c\u5546\u6807\u540e"
            "\u8fde\u7eed\u4e09\u5e74\u672a\u5b9e\u9645\u4f7f\u7528\uff0c"
            "\u8be5\u5546\u6807\u662f\u5426\u5b58\u5728\u88ab\u64a4\u9500\u98ce\u9669\uff1f"
        )
        selected_cover = Document(
            page_content="\u8fde\u7eed\u4e09\u5e74\u4e0d\u4f7f\u7528\u7684\uff0c\u53ef\u7533\u8bf7\u64a4\u9500\u6ce8\u518c\u5546\u6807\u3002",
            metadata={"source": "Law A", "article_no": 49, "chunk_id": "a49"},
        )
        duplicate_cover = Document(
            page_content="\u6709\u5173\u6ce8\u518c\u5546\u6807\u672a\u4f7f\u7528\u7684\u64a4\u9500\u7a0b\u5e8f\u6750\u6599\u3002",
            metadata={"source": "Law A", "article_no": 50, "chunk_id": "a50"},
        )
        reranked = [
            (selected_cover, 0.99),
            (doc("Law A", 3, "a3"), 0.98),
            (doc("Law A", 11, "a11"), 0.97),
            (duplicate_cover, 0.1),
        ]

        selected = _select_diverse_rerank_top(reranked, top_k=3, query=query)

        self.assertEqual([item.metadata["article_no"] for item, _ in selected], [49, 3, 11])

    def test_rerank_top_rejects_distant_generic_article_in_same_source_cluster(self):
        query = "\u5546\u54c1\u5b58\u5728\u8d28\u91cf\u7f3a\u9677\u5bfc\u81f4\u6d88\u8d39\u8005\u53d7\u4f24\uff0c\u662f\u5426\u9700\u8981\u627f\u62c5\u8d54\u507f\u8d23\u4efb\uff1f"
        reranked = [
            (
                Document(
                    page_content="\u56e0\u4ea7\u54c1\u5b58\u5728\u7f3a\u9677\u9020\u6210\u4ed6\u4eba\u635f\u5bb3\u7684\uff0c\u53ef\u4ee5\u5411\u751f\u4ea7\u8005\u6216\u9500\u552e\u8005\u8bf7\u6c42\u8d54\u507f\u3002",
                    metadata={"source": "Law A", "article_no": 1203, "chunk_id": "a1203"},
                ),
                0.99,
            ),
            (
                Document(
                    page_content="\u56e0\u7b2c\u4e09\u4eba\u8fc7\u9519\u4f7f\u4ea7\u54c1\u5b58\u5728\u7f3a\u9677\u7684\uff0c\u8d54\u507f\u540e\u53ef\u8ffd\u507f\u3002",
                    metadata={"source": "Law A", "article_no": 1204, "chunk_id": "a1204"},
                ),
                0.98,
            ),
            (
                Document(
                    page_content="\u660e\u77e5\u4ea7\u54c1\u7f3a\u9677\u4ecd\u9500\u552e\u7684\uff0c\u53ef\u8bf7\u6c42\u60e9\u7f5a\u6027\u8d54\u507f\u3002",
                    metadata={"source": "Law A", "article_no": 1207, "chunk_id": "a1207"},
                ),
                0.97,
            ),
            (
                Document(
                    page_content="\u8d28\u91cf\u7f3a\u9677\u9020\u6210\u4ed6\u4eba\u635f\u5bb3\u7684\uff0c\u627f\u62c5\u8fde\u5e26\u8d23\u4efb\u5e76\u53ef\u8ffd\u507f\u3002",
                    metadata={"source": "Law A", "article_no": 1252, "chunk_id": "a1252"},
                ),
                0.1,
            ),
        ]

        selected = _select_diverse_rerank_top(reranked, top_k=3, query=query)

        self.assertEqual([item.metadata["article_no"] for item, _ in selected], [1203, 1204, 1207])

    def test_rerank_top_retains_nearby_alignment_candidate(self):
        query = (
            "\u67d0\u516c\u53f8\u6ce8\u518c\u5546\u6807\u540e"
            "\u8fde\u7eed\u4e09\u5e74\u672a\u5b9e\u9645\u4f7f\u7528\uff0c"
            "\u8be5\u5546\u6807\u662f\u5426\u5b58\u5728\u88ab\u64a4\u9500\u98ce\u9669\uff1f"
        )
        reranked = [
            (doc("Law A", 57, "a57"), 0.99),
            (doc("Law A", 3, "a3"), 0.98),
            (doc("Law A", 11, "a11"), 0.97),
            (
                Document(
                    page_content="\u8fde\u7eed\u4e09\u5e74\u4e0d\u4f7f\u7528\u7684\uff0c\u53ef\u4ee5\u7533\u8bf7\u64a4\u9500\u8be5\u6ce8\u518c\u5546\u6807\u3002",
                    metadata={"source": "Law A", "article_no": 49, "chunk_id": "a49"},
                ),
                0.1,
            ),
        ]

        selected = _select_diverse_rerank_top(reranked, top_k=3, query=query)

        self.assertIn(49, [item.metadata["article_no"] for item, _ in selected])

    def test_rerank_top_replaces_weak_fragment_with_nearby_issue_article(self):
        query = "\u6709\u9650\u8d23\u4efb\u516c\u53f8\u80a1\u4e1c\u5bf9\u5916\u8f6c\u8ba9\u80a1\u6743\uff0c\u672a\u901a\u77e5\u5176\u4ed6\u80a1\u4e1c\uff0c\u662f\u5426\u6709\u6548\uff1f"
        reranked = [
            (
                Document(
                    page_content="\u4eba\u6c11\u6cd5\u9662\u5f3a\u5236\u6267\u884c\u7a0b\u5e8f\u8f6c\u8ba9\u80a1\u6743\u65f6\uff0c\u5e94\u5f53\u901a\u77e5\u516c\u53f8\u53ca\u5168\u4f53\u80a1\u4e1c\u3002",
                    metadata={"source": "Law A", "article_no": 85, "chunk_id": "a85"},
                ),
                0.99,
            ),
            (
                Document(
                    page_content="\u80a1\u4e1c\u8f6c\u8ba9\u80a1\u6743\u7684\uff0c\u5e94\u5f53\u4e66\u9762\u901a\u77e5\u516c\u53f8\uff0c\u8bf7\u6c42\u53d8\u66f4\u80a1\u4e1c\u540d\u518c\u3002",
                    metadata={"source": "Law A", "article_no": 86, "chunk_id": "a86"},
                ),
                0.98,
            ),
            (
                Document(
                    page_content="\uff08\u516d\uff09\u6709\u9650\u8d23\u4efb\u516c\u53f8\u80a1\u4e1c\u7684\u59d3\u540d\u6216\u8005\u540d\u79f0\u3002",
                    metadata={"source": "Law A", "article_no": 32, "chunk_id": "a32"},
                ),
                0.97,
            ),
            (
                Document(
                    page_content=(
                        "\u80a1\u4e1c\u5411\u80a1\u4e1c\u4ee5\u5916\u7684\u4eba\u8f6c\u8ba9\u80a1\u6743\u7684\uff0c"
                        "\u5e94\u5f53\u5c06\u80a1\u6743\u8f6c\u8ba9\u4e8b\u9879\u4e66\u9762\u901a\u77e5\u5176\u4ed6\u80a1\u4e1c\uff0c"
                        "\u5176\u4ed6\u80a1\u4e1c\u5728\u540c\u7b49\u6761\u4ef6\u4e0b\u6709\u4f18\u5148\u8d2d\u4e70\u6743\u3002"
                    ),
                    metadata={"source": "Law A", "article_no": 84, "chunk_id": "a84"},
                ),
                0.1,
            ),
        ]

        selected = _select_diverse_rerank_top(reranked, top_k=3, query=query)

        self.assertIn(84, [item.metadata["article_no"] for item, _ in selected])
        self.assertNotIn(32, [item.metadata["article_no"] for item, _ in selected])

    def test_rerank_top_retains_nearby_cross_border_notice_article(self):
        query = (
            "\u5e73\u53f0\u5904\u7406\u8d85\u8fc7100\u4e07\u7528\u6237\u4e2a\u4eba\u4fe1\u606f\uff0c"
            "\u5c06\u8ba2\u5355\u6570\u636e\u4f20\u8f93\u7ed9\u5883\u5916\u4e91\u670d\u52a1\u5546\uff0c"
            "\u672a\u7533\u62a5\u6570\u636e\u51fa\u5883\u5b89\u5168\u8bc4\u4f30\uff0c\u662f\u5426\u5408\u89c4\uff1f"
        )
        reranked = [
            (
                Document(
                    page_content="\u4e2a\u4eba\u4fe1\u606f\u5904\u7406\u8005\u5411\u5883\u5916\u63d0\u4f9b\u4e2a\u4eba\u4fe1\u606f\u7684\uff0c\u5e94\u5177\u5907\u5b89\u5168\u8bc4\u4f30\u7b49\u6761\u4ef6\u3002",
                    metadata={"source": "Law A", "article_no": 38, "chunk_id": "a38"},
                ),
                0.99,
            ),
            (
                Document(
                    page_content=(
                        "\u6570\u636e\u51fa\u5883\u4e2d\u548c\u51fa\u5883\u540e\u906d\u5230\u6cc4\u9732\u7b49\u7684\u98ce\u9669\uff0c"
                        "\u4e2a\u4eba\u4fe1\u606f\u6743\u76ca\u7ef4\u62a4\u7684\u6e20\u9053\u662f\u5426\u901a\u7545\u7b49\u3002"
                    ),
                    metadata={"source": "Law B", "article_no": 5, "chunk_id": "b5"},
                ),
                0.9999,
            ),
            (
                Document(
                    page_content="\u5904\u7406\u8005100\u4e07\u4eba\u4ee5\u4e0a\u4e2a\u4eba\u4fe1\u606f\u5411\u5883\u5916\u63d0\u4f9b\u4e2a\u4eba\u4fe1\u606f\uff0c\u5e94\u5f53\u7533\u62a5\u6570\u636e\u51fa\u5883\u5b89\u5168\u8bc4\u4f30\u3002",
                    metadata={"source": "Law B", "article_no": 4, "chunk_id": "b4"},
                ),
                0.98,
            ),
            (
                Document(
                    page_content=(
                        "\u4e2a\u4eba\u4fe1\u606f\u5904\u7406\u8005\u5411\u5883\u5916\u63d0\u4f9b\u4e2a\u4eba\u4fe1\u606f\u7684\uff0c"
                        "\u5e94\u5f53\u5411\u4e2a\u4eba\u544a\u77e5\u5883\u5916\u63a5\u6536\u65b9\u7684\u540d\u79f0\u3001"
                        "\u5904\u7406\u76ee\u7684\u3001\u5904\u7406\u65b9\u5f0f\u7b49\u4e8b\u9879\u3002"
                    ),
                    metadata={"source": "Law A", "article_no": 39, "chunk_id": "a39"},
                ),
                0.1,
            ),
        ]

        selected = _select_diverse_rerank_top(reranked, top_k=3, query=query)

        self.assertIn(39, [item.metadata["article_no"] for item, _ in selected])
        self.assertIn(4, [item.metadata["article_no"] for item, _ in selected])
        self.assertNotIn(5, [item.metadata["article_no"] for item, _ in selected])

    def test_rerank_top_does_not_replace_nearby_notice_article_with_secondary_procedure(self):
        query = (
            "\u67d0\u8de8\u5883\u7535\u5546\u5e73\u53f0\u5904\u7406\u8d85\u8fc7100\u4e07\u7528\u6237\u4e2a\u4eba\u4fe1\u606f\uff0c"
            "\u5e76\u5c06\u7528\u6237\u8ba2\u5355\u6570\u636e\u4f20\u8f93\u7ed9\u5883\u5916\u4e91\u670d\u52a1\u5546\uff0c"
            "\u672a\u7533\u62a5\u6570\u636e\u51fa\u5883\u5b89\u5168\u8bc4\u4f30\uff0c\u662f\u5426\u5408\u89c4\uff1f"
        )
        selected_seed = [
            (
                Document(
                    page_content="\u4e2a\u4eba\u4fe1\u606f\u5904\u7406\u8005\u5411\u5883\u5916\u63d0\u4f9b\u4e2a\u4eba\u4fe1\u606f\u7684\uff0c\u5e94\u5f53\u5177\u5907\u5b89\u5168\u8bc4\u4f30\u7b49\u6761\u4ef6\u3002",
                    metadata={"source": "PIPL", "article_no": 38, "chunk_id": "p38"},
                ),
                0.98,
            ),
            (
                Document(
                    page_content=(
                        "\u4e2a\u4eba\u4fe1\u606f\u5904\u7406\u8005\u5411\u5883\u5916\u63d0\u4f9b\u4e2a\u4eba\u4fe1\u606f\u7684\uff0c"
                        "\u5e94\u5f53\u5411\u4e2a\u4eba\u544a\u77e5\u5883\u5916\u63a5\u6536\u65b9\u7684\u8054\u7cfb\u65b9\u5f0f\u3001"
                        "\u5904\u7406\u76ee\u7684\u3001\u5904\u7406\u65b9\u5f0f\uff0c\u5e76\u53d6\u5f97\u5355\u72ec\u540c\u610f\u3002"
                    ),
                    metadata={"source": "PIPL", "article_no": 39, "chunk_id": "p39"},
                ),
                0.97,
            ),
            (
                Document(
                    page_content="\u5904\u7406100\u4e07\u4eba\u4ee5\u4e0a\u4e2a\u4eba\u4fe1\u606f\u5411\u5883\u5916\u63d0\u4f9b\u7684\uff0c\u5e94\u5f53\u7533\u62a5\u6570\u636e\u51fa\u5883\u5b89\u5168\u8bc4\u4f30\u3002",
                    metadata={"source": "Export Measures", "article_no": 4, "chunk_id": "m4"},
                ),
                0.96,
            ),
        ]
        secondary_procedure = (
            Document(
                page_content=(
                    "\u5e94\u5f53\u5f00\u5c55\u98ce\u9669\u81ea\u8bc4\u4f30\uff0c\u91cd\u70b9\u8bc4\u4f30\u4ee5\u4e0b\u5185\u5bb9\uff1a"
                    "\u6570\u636e\u51fa\u5883\u4e2d\u548c\u51fa\u5883\u540e\u906d\u5230\u6cc4\u9732\u7b49\u98ce\u9669\uff0c"
                    "\u4e2a\u4eba\u4fe1\u606f\u6743\u76ca\u7ef4\u62a4\u6e20\u9053\u662f\u5426\u901a\u7545\u7b49\u3002"
                ),
                metadata={"source": "Export Measures", "article_no": 5, "chunk_id": "m5"},
            ),
            0.999,
        )
        reranked = selected_seed + [secondary_procedure]

        selected = _select_diverse_rerank_top(reranked, top_k=3, query=query)

        self.assertEqual([item.metadata["article_no"] for item, _ in selected], [38, 39, 4])

    def test_rerank_top_never_replaces_protected_near_issue_evidence(self):
        query = (
            "\u4e2a\u4eba\u4fe1\u606f\u5904\u7406\u8005\u5411\u5883\u5916\u63d0\u4f9b\u4e2a\u4eba\u4fe1\u606f\uff0c"
            "\u5e94\u5f53\u544a\u77e5\u5904\u7406\u76ee\u7684\u5e76\u53d6\u5f97\u5355\u72ec\u540c\u610f\uff0c\u662f\u5426\u5408\u89c4\uff1f"
        )
        reranked = [
            (
                Document(
                    page_content=(
                        "\u4e2a\u4eba\u4fe1\u606f\u5904\u7406\u8005\u5411\u5883\u5916\u63d0\u4f9b\u4e2a\u4eba\u4fe1\u606f\u7684\uff0c"
                        "\u5e94\u5f53\u5177\u5907\u5b89\u5168\u8bc4\u4f30\u7b49\u6761\u4ef6\u3002"
                    ),
                    metadata={"source": "Law A", "article_no": 38, "chunk_id": "a38"},
                ),
                0.99,
            ),
            (
                Document(
                    page_content=(
                        "\u4e2a\u4eba\u4fe1\u606f\u5904\u7406\u8005\u5411\u5883\u5916\u63d0\u4f9b\u4e2a\u4eba\u4fe1\u606f\u7684\uff0c"
                        "\u5e94\u5f53\u544a\u77e5\u5904\u7406\u76ee\u7684\u3001\u5904\u7406\u65b9\u5f0f\uff0c"
                        "\u5e76\u53d6\u5f97\u5355\u72ec\u540c\u610f\u3002"
                    ),
                    metadata={"source": "Law A", "article_no": 39, "chunk_id": "a39"},
                ),
                0.98,
            ),
            (
                Document(
                    page_content=(
                        "\u4e2a\u4eba\u4fe1\u606f\u5904\u7406\u8005\u5411\u5883\u5916\u63d0\u4f9b\u4e2a\u4eba\u4fe1\u606f\u7684\uff0c"
                        "\u5e94\u5f53\u4fdd\u62a4\u4e2a\u4eba\u4fe1\u606f\u6743\u76ca\u5e76\u5c65\u884c\u544a\u77e5\u4e49\u52a1\u3002"
                    ),
                    metadata={"source": "Law A", "article_no": 40, "chunk_id": "a40"},
                ),
                0.97,
            ),
            (
                Document(
                    page_content=(
                        "\u4e2a\u4eba\u4fe1\u606f\u5904\u7406\u8005\u5411\u5883\u5916\u63d0\u4f9b\u4e2a\u4eba\u4fe1\u606f\u7684\uff0c"
                        "\u5e94\u5f53\u8bb0\u5f55\u5904\u7406\u76ee\u7684\u3001\u5904\u7406\u65b9\u5f0f\u548c\u5355\u72ec\u540c\u610f\u60c5\u51b5\u3002"
                    ),
                    metadata={"source": "Law A", "article_no": 41, "chunk_id": "a41"},
                ),
                0.1,
            ),
        ]

        selected = _select_diverse_rerank_top(reranked, top_k=3, query=query)

        self.assertEqual([item.metadata["chunk_id"] for item, _ in selected], ["a38", "a39", "a40"])

    def test_alignment_profile_does_not_treat_limited_liability_as_consequence(self):
        query = "\u6709\u9650\u8d23\u4efb\u516c\u53f8\u80a1\u4e1c\u5bf9\u5916\u8f6c\u8ba9\u80a1\u6743\uff0c\u672a\u901a\u77e5\u5176\u4ed6\u80a1\u4e1c\uff0c\u662f\u5426\u6709\u6548\uff1f"
        candidate = Document(
            page_content="\uff08\u516d\uff09\u6709\u9650\u8d23\u4efb\u516c\u53f8\u80a1\u4e1c\u7684\u59d3\u540d\u6216\u8005\u540d\u79f0\u3002",
            metadata={"source": "Law A", "article_no": 32, "chunk_id": "a32"},
        )

        profile = _alignment_profile(query, candidate)

        self.assertEqual(profile["consequences"], set())

    def test_selector_does_not_consume_anchor_hint_lines(self):
        query = (
            "\u573a\u666f\u951a\u70b9\u6cd5\u6761\uff1a"
            "Law A\u7b2c4\u6761\uff1bLaw B\u7b2c5\u6761"
        )
        reranked = [
            (doc("Law A", 4, "a4"), 0.99),
            (doc("Law B", 5, "b5"), 0.98),
            (doc("Law C", 6, "c6"), 0.97),
            (
                Document(
                    page_content="Law A article 5 text",
                    metadata={"source": "Law A", "article_no": 5, "chunk_id": "a5"},
                ),
                0.1,
            ),
        ]

        selected = _select_diverse_rerank_top(reranked, top_k=3, query=query)

        self.assertEqual([item.metadata["chunk_id"] for item, _ in selected], ["a4", "b5", "c6"])

    def test_alignment_profile_ignores_hint_only_query(self):
        query = "\u573a\u666f\u951a\u70b9\u6cd5\u6761\uff1aLaw A\u7b2c5\u6761"
        candidate = Document(
            page_content="Law A article 5 text",
            metadata={"source": "Law A", "article_no": 5, "chunk_id": "a5"},
        )

        profile = _alignment_profile(query, candidate)

        self.assertEqual(profile["phrases"], set())
        self.assertEqual(profile["consequences"], set())

    def test_alignment_profile_ignores_anchor_rerank_hint_metadata(self):
        query = "\u67d0\u516c\u53f8\u672a\u544a\u77e5\u4e2a\u4eba\u4fe1\u606f\u5904\u7406\u76ee\u7684\uff0c\u662f\u5426\u6709\u98ce\u9669\uff1f"
        candidate = Document(
            page_content="\u8be5\u6761\u6587\u4e0e\u95ee\u9898\u65e0\u5173\u3002",
            metadata={
                "source": "Law A",
                "article_no": 5,
                "chunk_id": "a5",
                "_anchor_rerank_hint": "\u573a\u666f\u951a\u70b9\u5019\u9009\uff1a\u544a\u77e5\u4e2a\u4eba\u4fe1\u606f\u5904\u7406\u76ee\u7684",
            },
        )

        profile = _alignment_profile(query, candidate)

        self.assertEqual(profile["phrases"], set())
        self.assertEqual(profile["consequences"], set())

    def test_near_tie_rerank_scores_keep_candidate_order(self):
        docs = [
            doc("Law A", 5, "a5"),
            doc("Law A", 6, "a6"),
            doc("Law A", 57, "a57"),
        ]

        sorted_docs = _sort_rerank_scores_stable(docs, [0.9991, 0.9990, 0.9998])

        self.assertEqual([item.metadata["article_no"] for item, _ in sorted_docs], [5, 6, 57])

    def test_anchor_order_survives_small_rerank_score_gap(self):
        docs = [
            doc("Law A", 2, "a2"),
            doc("Law A", 15, "a15"),
            doc("Law A", 21, "a21"),
        ]

        sorted_docs = _sort_rerank_scores_stable(docs, [0.991, 0.994, 0.999])

        self.assertEqual([item.metadata["article_no"] for item, _ in sorted_docs], [2, 15, 21])

    def test_same_bucket_stabilization_is_independent_from_candidate_order(self):
        query = "\u5e73\u53f0\u5904\u7406\u4e2a\u4eba\u4fe1\u606f\uff0c\u672a\u5c65\u884c\u544a\u77e5\u4e49\u52a1\uff0c\u9700\u8981\u627f\u62c5\u4ec0\u4e48\u8d23\u4efb\uff1f"
        aligned = Document(
            page_content="\u4e2a\u4eba\u4fe1\u606f\u5904\u7406\u8005\u5e94\u5f53\u544a\u77e5\u5904\u7406\u76ee\u7684\uff0c\u672a\u5c65\u884c\u4e49\u52a1\u7684\u5e94\u627f\u62c5\u8d23\u4efb\u3002",
            metadata={"source": "Law B", "article_no": 20, "chunk_id": "b20"},
        )
        weak = Document(
            page_content="\u672c\u6cd5\u6240\u79f0\u4e2a\u4eba\u4fe1\u606f\uff0c\u662f\u4ee5\u7535\u5b50\u6216\u8005\u5176\u4ed6\u65b9\u5f0f\u8bb0\u5f55\u7684\u4fe1\u606f\u3002",
            metadata={"source": "Law A", "article_no": 4, "chunk_id": "a4"},
        )

        first_order = _stabilize_same_bucket_rerank_order(
            [(weak, 0.991), (aligned, 0.999)],
            query=query,
        )
        second_order = _stabilize_same_bucket_rerank_order(
            [(aligned, 0.999), (weak, 0.991)],
            query=query,
        )

        self.assertEqual([item.metadata["chunk_id"] for item, _ in first_order], ["b20", "a4"])
        self.assertEqual([item.metadata["chunk_id"] for item, _ in second_order], ["b20", "a4"])

    def test_same_bucket_stabilization_preserves_cross_bucket_priority(self):
        query = "\u5e73\u53f0\u662f\u5426\u9700\u8981\u5c65\u884c\u544a\u77e5\u4e49\u52a1\uff1f"
        high_bucket_weak = doc("Law A", 4, "a4")
        low_bucket_aligned = Document(
            page_content="\u5e94\u5f53\u544a\u77e5\u4e2a\u4eba\u4fe1\u606f\u5904\u7406\u76ee\u7684\u548c\u5904\u7406\u65b9\u5f0f\u3002",
            metadata={"source": "Law B", "article_no": 20, "chunk_id": "b20"},
        )

        stabilized = _stabilize_same_bucket_rerank_order(
            [(high_bucket_weak, 0.91), (low_bucket_aligned, 0.89)],
            query=query,
        )

        self.assertEqual([item.metadata["chunk_id"] for item, _ in stabilized], ["a4", "b20"])

    def test_same_bucket_stabilization_does_not_reorder_large_buckets(self):
        query = "\u5e73\u53f0\u5904\u7406\u4e2a\u4eba\u4fe1\u606f\uff0c\u672a\u5c65\u884c\u544a\u77e5\u4e49\u52a1\uff0c\u9700\u8981\u627f\u62c5\u4ec0\u4e48\u8d23\u4efb\uff1f"
        weak_a = doc("Law A", 4, "a4")
        weak_b = doc("Law A", 5, "a5")
        aligned = Document(
            page_content="\u4e2a\u4eba\u4fe1\u606f\u5904\u7406\u8005\u5e94\u5f53\u544a\u77e5\u5904\u7406\u76ee\u7684\uff0c\u672a\u5c65\u884c\u4e49\u52a1\u7684\u5e94\u627f\u62c5\u8d23\u4efb\u3002",
            metadata={"source": "Law B", "article_no": 20, "chunk_id": "b20"},
        )
        weak_c = doc("Law A", 6, "a6")

        stabilized = _stabilize_same_bucket_rerank_order(
            [(weak_a, 0.999), (weak_b, 0.998), (aligned, 0.997), (weak_c, 0.996)],
            query=query,
        )

        self.assertEqual(
            [item.metadata["chunk_id"] for item, _ in stabilized],
            ["a4", "a5", "b20", "a6"],
        )

    def test_debug_rerank_full_score_order_preserves_input_and_rerank_ranks(self):
        docs = [
            doc("Law A", 24, "a24"),
            doc("Law A", 48, "a48"),
            doc("Law B", 20, "b20"),
        ]
        reranked = [(docs[2], 0.88), (docs[0], 0.82), (docs[1], 0.81)]

        trace = _debug_rerank_full_score_order(docs, reranked)

        self.assertEqual([item["chunk_id"] for item in trace], ["b20", "a24", "a48"])
        self.assertEqual([item["rerank_rank"] for item in trace], [1, 2, 3])
        self.assertEqual([item["input_rank"] for item in trace], [3, 1, 2])
        self.assertEqual(trace[0]["score"], 0.88)
        self.assertIn("article", trace[0]["article_key"])

    def test_debug_final_selection_trace_does_not_change_selected_results(self):
        docs = [
            doc("Law A", 24, "a24"),
            doc("Law A", 24, "a24-sibling"),
            doc("Law A", 48, "a48"),
            doc("Law B", 20, "b20"),
        ]
        reranked = [(docs[0], 0.99), (docs[1], 0.98), (docs[2], 0.97), (docs[3], 0.96)]
        selected = _select_diverse_rerank_top(reranked, top_k=3)

        trace = _debug_final_evidence_selection_trace(
            docs,
            reranked,
            selected,
            mode="cross_encoder",
            top_k=3,
        )

        self.assertEqual([doc.metadata["chunk_id"] for doc, _ in selected], ["a24", "a48", "b20"])
        self.assertEqual(trace["mode"], "cross_encoder")
        self.assertEqual(trace["input_count"], 4)
        self.assertEqual(trace["full_rerank_count"], 4)
        self.assertEqual(trace["selected_count"], 3)
        self.assertEqual([item["chunk_id"] for item in trace["selected"]], ["a24", "a48", "b20"])
        self.assertEqual([item["final_rank"] for item in trace["selected"]], [1, 2, 3])
        self.assertEqual([item["rerank_rank"] for item in trace["selected"]], [1, 3, 4])
        self.assertEqual([item["chunk_id"] for item in trace["not_selected"]], ["a24-sibling"])

    def test_anchor_rerank_hint_keeps_scene_article_intent_in_query(self):
        hint = _format_anchor_rerank_hint(
            {"\u4e2d\u534e\u4eba\u6c11\u5171\u548c\u56fd\u4e2a\u4eba\u4fe1\u606f\u4fdd\u62a4\u6cd5": {13, 17, 28, 29}}
        )

        self.assertIn("\u573a\u666f\u951a\u70b9\u6cd5\u6761", hint)
        self.assertIn("\u7b2c13\u6761", hint)
        self.assertIn("\u7b2c29\u6761", hint)

    def test_patent_question_defaults_to_legal_regulation_documents(self):
        question = "\u6388\u4e88\u4e13\u5229\u6743\u9700\u8981\u6ee1\u8db3\u54ea\u4e9b\u6761\u4ef6\uff1f"

        document_type, law_level, standard_type = infer_filters_from_question(
            question,
            document_type=None,
            law_level=None,
            standard_type=None,
        )

        self.assertEqual(document_type, "\u6cd5\u5f8b\u6cd5\u89c4")
        self.assertIsNone(law_level)
        self.assertIsNone(standard_type)

    def test_market_order_scene_anchors_use_eval_article_numbers(self):
        false_ad = match_scene_anchors_from_rules(
            "\u865a\u6784\u4ea7\u54c1\u529f\u80fd\u5e76\u8bef\u5bfc\u6d88\u8d39\u8005",
            "\u5e02\u573a\u79e9\u5e8f",
        )
        trade_secret = match_scene_anchors_from_rules(
            "\u5458\u5de5\u79bb\u804c\u540e\u5c06\u5ba2\u6237\u540d\u5355\u5e26\u81f3\u65b0\u516c\u53f8\u4f7f\u7528",
            "\u5e02\u573a\u79e9\u5e8f",
        )

        self.assertIn(9, next(iter(false_ad.values())))
        self.assertIn(10, next(iter(trade_secret.values())))

    def test_pipl_scene_anchors_cover_notice_consent_sensitive_triplet(self):
        anchors = match_scene_anchors_from_rules(
            "\u7cbe\u51c6\u5b9a\u4f4d\u4fe1\u606f\u7528\u4e8e\u5e7f\u544a\u63a8\u8350",
            "\u6570\u636e\u5408\u89c4",
        )

        self.assertTrue({13, 17, 28, 29}.issubset(next(iter(anchors.values()))))

    def test_eval_min_match_contract_supports_top3_evidence(self):
        expected_items = [{"article_no": i} for i in [13, 17, 28, 29]]
        case = {"expected_evidence": expected_items, "expected_evidence_min_match": 3}
        evidence_items = [{"article_no": i} for i in [17, 28, 29]]

        required_count = expected_evidence_required_count(case, expected_items, "all")
        status = expected_evidence_layer_status(
            expected_items,
            evidence_items,
            "all",
            required_count,
        )

        self.assertEqual(required_count, 3)
        self.assertTrue(status["satisfied"])


if __name__ == "__main__":
    unittest.main()
