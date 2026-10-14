"""检索模块"""
# rag_query 主路径收敛为 Dense -> Sparse -> Union -> Anchor -> Cut -> Cross-Encoder。
# BM25 仅作为分层召回补充，不参与分数融合或加权排序。
# Cross-Encoder 是唯一最终排序器；失败时仅回退到 dense top-3。
# v0.4.5.x 修正 rerank index、anchor/candidate 预算、父条文输入与专利过滤。
# v0.4.5.6+ 稳定规则锚点顺序，并保留证据支持的法定原词。
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import perf_counter
from typing import Any

from langchain_core.documents import Document

from src.core.vectorstore import COLLECTION_NAME, get_vectorstore
from src.rag.answer_policy import (
    apply_answer_mode_policy,
    detect_external_fact_needs,
    determine_answer_mode,
)
from src.rag.answer_generation import generate_answer_payload
from src.rag.complex_case import (
    build_complex_case_fast_payload,
    extract_complex_case_issues,
    format_complex_case_plan,
    is_complex_multi_issue_question,
    plan_complex_case_issues,
)
from src.rag.domain_router import (
    get_category_supplements,
    get_scene_anchors,
    route_question,
)
from src.rag.debug_trace import (
    _debug_final_evidence_selection_trace,
    _debug_rerank_full_score_order,
    summarize_debug_results,
)
from src.rag.evidence import (
    build_context,
    build_evidence_chain,
    build_missing_evidence,
    build_supported_items,
    calculate_retrieval_confidence,
    should_request_human_review,
)
from src.rag.evidence_sufficiency import assess_evidence_sufficiency
from src.rag.filters import (
    RetrievalFilters,
)
from src.rag.experiment_profiles import resolve_experiment_profile
from src.rag.llm_json import (
    parse_llm_json,
)
from src.rag.query_planning import (
    analyze_query_with_llm,
    build_search_query,
    calculate_keyword_boost,
    expand_query_terms,
)
from src.rag.legal_concepts import (
    find_missing_concept_primary_anchors,
    get_concept_anchors,
    get_concept_domain,
    get_concept_primary_anchors,
    summarize_concept_matches,
)
from src.rag.qdrant_access import (
    fetch_article_numbers_with_scores,
    fetch_article_range_with_scores,
    fetch_standard_sections_with_scores,
    merge_results,
    point_to_document,
)
from src.rag.rerank import (
    _call_siliconflow_rerank,
    _alignment_profile,
    _candidate_article_key,
    _candidate_exact_key,
    _format_anchor_rerank_hint,
    _limit_base_and_anchor_candidates,
    _limit_candidates_by_article_budget,
    _rerank_document_text,
    _select_diverse_rerank_top,
    _sort_rerank_scores_stable,
    _sort_results_by_article_order,
    _stabilize_same_bucket_rerank_order,
)
from src.rag.retrieval_ops import (
    collapse_parent_results,
    merge_union as _merge_union,
    retrieve,
    retrieve_with_keyword_match,
    retrieve_with_scores,
    retrieve_with_sparse,
)
from src.rag.risk_enrichment import (
    RISK_PAYLOAD_SUPPLEMENT_RULES,
    enrich_answer_legal_terms,
    enrich_risk_payload,
    validate_risk_payload_supplement_rules,
)
from src.rag.rules import (
    ANTI_MONOPOLY_LAW_NAME,
    ANTI_UNFAIR_COMPETITION_LAW_NAME,
    CIVIL_CODE_NAME,
    COMPANY_LAW_NAME,
    DATA_EXPORT_MEASURES_NAME,
    HIGH_RISK_QUESTION_HINTS,
    LOW_RISK_QUESTION_HINTS,
    MEDIUM_RISK_QUESTION_HINTS,
    PATENT_LAW_NAME,
    PIPL_LAW_NAME,
    STANDARD_CONTRACT_MEASURES_NAME,
    STATE_SECRETS_LAW_NAME,
    TRADEMARK_LAW_NAME,
    VAT_LAW_NAME,
    add_article_anchors,
    infer_filters_from_question,
    infer_rule_based_risk_level,
    infer_scene_article_anchors,
    is_standard_scope_question,
    looks_like_low_risk_question,
    match_scene_anchors_from_rules,
    matched_scene_rules_from_config,
    source_allows_named_supplement,
    standard_anchor_sections,
)


logger = logging.getLogger(__name__)

BASE_DENSE_CANDIDATE_K = 5
BASE_SPARSE_CANDIDATE_K = 20
BASE_UNION_CANDIDATE_LIMIT = 15
RERANK_INPUT_CANDIDATE_LIMIT = 15
RERANK_BASE_CANDIDATE_QUOTA = 5
RERANK_ANCHOR_CANDIDATE_QUOTA = 10
SENSITIVE_PERSONAL_INFO_SIGNAL_TERMS = (
    "敏感个人信息",
    "精确轨迹",
    "行驶轨迹",
    "位置轨迹",
    "轨迹信息",
    "精准定位",
)


def has_sensitive_personal_info_signal(question: str) -> bool:
    """Recognize scenario wording that requires the PIPL sensitive-data anchor."""
    return any(term in str(question or "") for term in SENSITIVE_PERSONAL_INFO_SIGNAL_TERMS)


def _ensure_anchor_evidence(
    reranked_results: list[tuple[Document, float]],
    anchor_results: list[tuple[Document, float]],
    expected: dict[str, list[int]],
    top_k: int,
) -> list[tuple[Document, float]]:
    """Keep direct, scenario-matched articles in the final evidence window."""
    if not expected or not anchor_results:
        return reranked_results

    protected: list[tuple[Document, float]] = []
    protected_article_keys: set[tuple[str, int]] = set()
    for doc, score in anchor_results:
        metadata = doc.metadata
        source = str(metadata.get("source") or metadata.get("law_name") or "").strip()
        try:
            article_no = int(metadata.get("article_no"))
        except (TypeError, ValueError):
            continue
        if article_no not in expected.get(source, []):
            continue
        article_key = (source, article_no)
        if article_key in protected_article_keys:
            continue
        protected_article_keys.add(article_key)
        protected.append((doc, score))

    if not protected:
        return reranked_results

    selected = list(protected)
    selected_keys = {_candidate_exact_key(doc) for doc, _ in selected}
    for doc, score in reranked_results:
        key = _candidate_exact_key(doc)
        if key in selected_keys:
            continue
        selected.append((doc, score))
        selected_keys.add(key)
        if len(selected) >= top_k:
            break
    return selected[:top_k]


def _ensure_concept_primary_evidence(
    reranked_results: list[tuple[Document, float]],
    concept_anchor_results: list[tuple[Document, float]],
    question: str,
    top_k: int,
) -> list[tuple[Document, float]]:
    """Keep the primary direct source for a recognized legal concept in evidence."""
    expected = get_concept_primary_anchors(question)
    return _ensure_anchor_evidence(
        reranked_results,
        concept_anchor_results,
        expected,
        top_k,
    )


def _concept_evidence_budget(question: str, default_top_k: int) -> int:
    """Reserve enough evidence slots for distinct recognized concept sources."""
    expected = get_concept_primary_anchors(question)
    primary_count = sum(
        len({int(article_no) for article_no in article_numbers})
        for article_numbers in expected.values()
    )
    return min(8, max(default_top_k, primary_count))


def _scene_evidence_budget(
    scene_anchors: dict[str, list[int]],
    default_top_k: int,
) -> int:
    """Reserve a compact final-evidence window for a matched legal scenario."""
    article_count = sum(
        len({int(article_no) for article_no in article_numbers})
        for article_numbers in scene_anchors.values()
    )
    # Four articles are enough for a principle or requirement checklist while
    # keeping ordinary answers concise. Concept primary sources may take one slot.
    return min(8, max(default_top_k, min(4, article_count)))


def _combined_evidence_budget(
    question: str,
    scene_anchors: dict[str, list[int]],
    default_top_k: int,
) -> int:
    """Reserve slots for the union of scene and concept-primary articles."""
    protected = {
        (source, int(article_no))
        for source, article_numbers in scene_anchors.items()
        for article_no in article_numbers
    }
    for source, article_numbers in get_concept_primary_anchors(question).items():
        protected.update((source, int(article_no)) for article_no in article_numbers)
    return min(8, max(default_top_k, len(protected)))


def build_filters_payload(
    doc_type: str | None,
    block_type: str | None,
    document_type: str | None,
    law_name: str | None,
    source: str | None,
    law_level: str | None,
    authority_level: str | None,
    jurisdiction: str | None,
    issuing_authority: str | None,
    legal_effect: str | None,
    standard_type: str | None,
    case_type: str | None,
    patent_type: str | None,
    category: str | None,
    version: str | None,
    score_threshold: float | None,
    candidate_k: int,
) -> dict:
    """构造接口和调试信息共用的过滤器摘要。"""
    return {
        "doc_type": doc_type,
        "block_type": block_type,
        "document_type": document_type,
        "law_name": law_name,
        "source": source,
        "law_level": law_level,
        "authority_level": authority_level,
        "jurisdiction": jurisdiction,
        "issuing_authority": issuing_authority,
        "legal_effect": legal_effect,
        "standard_type": standard_type,
        "case_type": case_type,
        "patent_type": patent_type,
        "category": category,
        "version": version,
        "score_threshold": score_threshold,
        "candidate_k": candidate_k,
    }



def rag_query(
    question: str,
    collection_name: str = COLLECTION_NAME,
    k: int = 5,
    doc_type: str | None = "article",
    block_type: str | None = None,
    document_type: str | None = None,
    law_name: str | None = None,
    source: str | None = None,
    law_level: str | None = None,
    authority_level: str | None = None,
    jurisdiction: str | None = None,
    issuing_authority: str | None = None,
    legal_effect: str | None = None,
    standard_type: str | None = None,
    case_type: str | None = None,
    patent_type: str | None = None,
    category: str | None = None,
    version: str | None = None,
    score_threshold: float | None = None,
    debug: bool = False,
    use_reranker: bool = False,
    use_reasoning: bool = False,
    use_hybrid: bool = False,
    user_materials: list[dict] | None = None,
    experiment_profile: str | None = None,
    retrieval_only: bool = False,
    external_evidence: list[dict] | None = None,
):
    """RAG 完整链路：Dense/BM25 分层召回，Anchor 注入，Cross-Encoder 单一排序。"""
    retrieval_started_at = perf_counter()
    profile = resolve_experiment_profile(experiment_profile)
    use_sparse_recall = profile.enable_sparse_recall if profile else True
    use_concept_expansion = profile.enable_concept_expansion if profile else True
    use_concept_anchors = profile.enable_concept_anchors if profile else True
    use_deterministic_anchors = profile.enable_deterministic_anchors if profile else True
    use_complex_planner = profile.enable_complex_planner if profile else True
    use_cross_encoder = profile.enable_reranker if profile else True

    complex_multi_issue = use_complex_planner and is_complex_multi_issue_question(question)
    final_top_k = 8 if complex_multi_issue else 3
    complex_case_plans = plan_complex_case_issues(question) if complex_multi_issue else []
    answer_mode = determine_answer_mode(question, complex_case_plans)
    external_fact_needs = detect_external_fact_needs(question)
    union_candidate_limit = 30 if complex_multi_issue else BASE_UNION_CANDIDATE_LIMIT
    rerank_input_limit = 30 if complex_multi_issue else RERANK_INPUT_CANDIDATE_LIMIT
    rerank_base_quota = 10 if complex_multi_issue else RERANK_BASE_CANDIDATE_QUOTA
    rerank_anchor_quota = 20 if complex_multi_issue else RERANK_ANCHOR_CANDIDATE_QUOTA
    document_type, law_level, standard_type = infer_filters_from_question(
        question,
        document_type=document_type,
        law_level=law_level,
        standard_type=standard_type,
    )

    # 1. 检索
    candidate_k = rerank_input_limit
    # v0.4.0.2: LLM 法律语义理解层（默认关闭，高风险场景按需开启 use_reasoning=True）
    reasoning = analyze_query_with_llm(question) if use_reasoning else {}
    concept_matches = summarize_concept_matches(question) if use_concept_expansion else []
    concept_anchor_map = (
        get_concept_anchors(question)
        if use_concept_anchors and concept_matches
        else {}
    )
    if use_concept_anchors:
        final_top_k = _concept_evidence_budget(question, final_top_k)
    unified_scene_anchors = (
        {}
        if complex_multi_issue or not use_deterministic_anchors
        else match_scene_anchors_from_rules(question, category)
    )
    final_top_k = _combined_evidence_budget(question, unified_scene_anchors, final_top_k)
    planning_domain = category or get_concept_domain(question)

    search_query = (
        build_search_query(question, domain=planning_domain, reasoning=reasoning)
        if concept_matches
        else question
    )
    filters = build_filters_payload(
        doc_type,
        block_type,
        document_type,
        law_name,
        source,
        law_level,
        authority_level,
        jurisdiction,
        issuing_authority,
        legal_effect,
        standard_type,
        case_type,
        patent_type,
        category,
        version,
        score_threshold,
        candidate_k,
    )
    debug_info = None
    if debug:
        debug_info = {
            "question": question,
            "used_query": search_query,
            "used_rerank_query": search_query,
            "filters": filters,
            "candidate_k": candidate_k,
            "reasoning": reasoning,
            "legal_concepts": concept_matches,
            "planning_domain": planning_domain,
            "answer_mode": answer_mode,
            "external_fact_needs": external_fact_needs,
            "dense_candidates": [],
            "sparse_candidates": [],
            "union_candidates": [],
            "anchor_candidates": [],
            "rerank_input_candidates": [],
            "deterministic_supplements": {},
            "rerank_dense_fallback": False,
            "rerank_full_score_order": [],
            "final_evidence_selection_trace": {},
            "output_contributions": {},
            "merged_candidate_count": 0,
            "reranked_candidates": [],
            "final_candidates": [],
            "experiment_profile": profile.to_dict() if profile else None,
        }
        if complex_case_plans:
            debug_info["complex_case_plan"] = complex_case_plans

    retrieval_filters = RetrievalFilters(
        doc_type=doc_type, block_type=block_type, document_type=document_type,
        law_name=law_name, source=source, law_level=law_level,
        authority_level=authority_level, jurisdiction=jurisdiction,
        issuing_authority=issuing_authority, legal_effect=legal_effect,
        standard_type=standard_type, case_type=case_type, patent_type=patent_type,
        category=category, version=version,
    )
    metadata_filter = retrieval_filters.to_qdrant_filter()
    vectorstore = get_vectorstore(collection_name)
    dense_results = vectorstore.similarity_search_with_score(
        question,
        k=BASE_DENSE_CANDIDATE_K,
        filter=metadata_filter,
        score_threshold=score_threshold,
    )
    if not dense_results and retrieval_filters.is_default_article_filter():
        dense_results = vectorstore.similarity_search_with_score(
            question,
            k=BASE_DENSE_CANDIDATE_K,
            score_threshold=score_threshold,
        )
    dense_docs = [doc for doc, _ in dense_results]

    sparse_results = (
        retrieve_with_sparse(
            question,
            collection_name=collection_name,
            k=BASE_SPARSE_CANDIDATE_K,
            filters=retrieval_filters,
        )
        if use_sparse_recall
        else []
    )
    sparse_docs = [doc for doc, _ in sparse_results]

    seen = set()
    merged = []
    for doc in dense_docs + sparse_docs:
        key = _candidate_exact_key(doc)
        if key in seen:
            continue
        seen.add(key)
        merged.append(doc)
    merged = _limit_candidates_by_article_budget(merged, max_total=union_candidate_limit)
    anchor_candidates: list[tuple[Document, float]] = []

    if debug_info is not None:
        debug_info["dense_candidates"] = summarize_debug_results(dense_results)
        debug_info["sparse_candidates"] = summarize_debug_results(sparse_results, limit=BASE_SPARSE_CANDIDATE_K)
        debug_info["union_candidates"] = summarize_debug_results(
            [(doc, 0.0) for doc in merged],
            limit=union_candidate_limit,
        )

    if complex_case_plans:
        plan_anchor_results: list[tuple[Document, float]] = []
        plan_retrieval_results: list[tuple[Document, float]] = []

        batched_anchors: dict[str, set[int]] = {}
        for plan in complex_case_plans:
            for target_law_name, article_numbers in plan.get("anchors", {}).items():
                batched_anchors.setdefault(target_law_name, set()).update(article_numbers)
        for target_law_name, article_numbers in batched_anchors.items():
            if not source_allows_named_supplement(law_name, source, target_law_name):
                continue
            plan_anchor_results.extend(fetch_article_numbers_with_scores(
                collection_name=collection_name,
                article_numbers=sorted(article_numbers),
                doc_type=doc_type,
                block_type=block_type,
                document_type=document_type,
                law_name=law_name or target_law_name,
                source=source,
                law_level=law_level,
                authority_level=authority_level,
                jurisdiction=jurisdiction,
                issuing_authority=issuing_authority,
                legal_effect=legal_effect,
                standard_type=standard_type,
                case_type=case_type,
                patent_type=patent_type,
                category=None,
                version=version,
            ))

        def retrieve_for_plan(plan: dict[str, Any]) -> list[tuple[Document, float]]:
            if plan.get("missing_laws") and not plan.get("anchors"):
                return []
            plan_query = plan.get("query") or plan.get("issue") or question
            try:
                plan_dense_results = vectorstore.similarity_search_with_score(
                    plan_query,
                    k=2,
                    filter=metadata_filter,
                    score_threshold=score_threshold,
                )
                plan_sparse_results = (
                    retrieve_with_sparse(
                        plan_query,
                        collection_name=collection_name,
                        k=3,
                        filters=retrieval_filters,
                    )
                    if use_sparse_recall
                    else []
                )
            except Exception:
                logger.warning("Complex issue retrieval failed", exc_info=True)
                return []
            return merge_results(plan_dense_results, plan_sparse_results)

        if len(complex_case_plans) == 1:
            plan_retrieval_results = retrieve_for_plan(complex_case_plans[0])
        else:
            max_workers = min(6, len(complex_case_plans))
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(retrieve_for_plan, plan) for plan in complex_case_plans]
                for future in as_completed(futures):
                    plan_retrieval_results = merge_results(plan_retrieval_results, future.result())

        if plan_anchor_results:
            anchor_candidates = merge_results(anchor_candidates, plan_anchor_results)
        for doc, _ in plan_retrieval_results:
            key = _candidate_exact_key(doc)
            if key in seen:
                continue
            seen.add(key)
            merged.append(doc)
        merged = _limit_candidates_by_article_budget(merged, max_total=union_candidate_limit)
        if debug_info is not None:
            debug_info["deterministic_supplements"]["complex_case_plan_anchors"] = summarize_debug_results(
                plan_anchor_results,
                limit=30,
            )
            debug_info["deterministic_supplements"]["complex_case_plan_retrieval"] = summarize_debug_results(
                plan_retrieval_results,
                limit=30,
            )

    if use_deterministic_anchors and "原则" in question:
        supplement_law_name = law_name
        if (
            document_type in {None, "法律法规"}
            and source is None
            and law_name is None
            and "个人信息" in question
        ):
            supplement_law_name = PIPL_LAW_NAME
        principle_results = fetch_article_range_with_scores(
            collection_name=collection_name,
            start_article_no=5,
            end_article_no=8,
            doc_type=doc_type,
            block_type=block_type,
            document_type=document_type,
            law_name=supplement_law_name,
            source=source,
            law_level=law_level,
            authority_level=authority_level,
            jurisdiction=jurisdiction,
            issuing_authority=issuing_authority,
            legal_effect=legal_effect,
            standard_type=standard_type,
            case_type=case_type,
            patent_type=patent_type,
            category=category,
            version=version,
        )
        principle_results = _sort_results_by_article_order(principle_results, [5, 6, 7, 8])
        if debug_info is not None:
            debug_info["deterministic_supplements"]["principle_articles_5_to_9"] = summarize_debug_results(
                principle_results
            )
        anchor_candidates = merge_results(anchor_candidates, principle_results)

    # Exact location or trajectory data is a sensitive-personal-information
    # signal even when the question is phrased in business terms rather than
    # using the statutory label.
    sensitive_personal_info_signal = has_sensitive_personal_info_signal(question)
    sensitive_results: list[tuple[Document, float]] = []
    export_condition_results: list[tuple[Document, float]] = []
    export_condition_expected: dict[str, list[int]] = {}
    if (
        use_deterministic_anchors
        and sensitive_personal_info_signal
        and document_type in {None, "法律法规"}
        and source_allows_named_supplement(law_name, source, PIPL_LAW_NAME)
    ):
        sensitive_results = fetch_article_range_with_scores(
            collection_name=collection_name,
            start_article_no=28,
            end_article_no=28,
            doc_type=doc_type,
            block_type=block_type,
            document_type=document_type,
            law_name=law_name or PIPL_LAW_NAME,
            source=source,
            law_level=law_level,
            authority_level=authority_level,
            jurisdiction=jurisdiction,
            issuing_authority=issuing_authority,
            legal_effect=legal_effect,
            standard_type=standard_type,
            case_type=case_type,
            patent_type=patent_type,
            category=category,
            version=version,
        )
        if debug_info is not None:
            debug_info["deterministic_supplements"]["pipl_sensitive_article_28"] = summarize_debug_results(
                sensitive_results
            )
        anchor_candidates = merge_results(anchor_candidates, sensitive_results)

    if (
        use_deterministic_anchors
        and "撤回同意" in question
        and document_type in {None, "法律法规"}
        and source_allows_named_supplement(law_name, source, PIPL_LAW_NAME)
    ):
        consent_results = fetch_article_numbers_with_scores(
            collection_name=collection_name,
            article_numbers=[15, 16, 47],
            doc_type=doc_type,
            block_type=block_type,
            document_type=document_type,
            law_name=law_name or PIPL_LAW_NAME,
            source=source,
            law_level=law_level,
            authority_level=authority_level,
            jurisdiction=jurisdiction,
            issuing_authority=issuing_authority,
            legal_effect=legal_effect,
            standard_type=standard_type,
            case_type=case_type,
            patent_type=patent_type,
            category=category,
            version=version,
        )
        if debug_info is not None:
            debug_info["deterministic_supplements"]["pipl_consent_articles_15_16_47"] = summarize_debug_results(
                consent_results
            )
        anchor_candidates = merge_results(anchor_candidates, consent_results)

    if (
        use_deterministic_anchors
        and (
            "个人信息出境" in question
            or (
                "个人信息" in question
                and "境外" in question
                and any(term in question for term in ["提供", "传输", "转移"])
            )
        )
        and any(hint in question for hint in ["条件", "具备", "需要", "是否必须", "是否足够", "申报"])
        and document_type in {None, "法律法规"}
    ):
        # The generated answer normally needs the transfer path, separate
        # consent and threshold/localisation conditions together.  Reserve a
        # small evidence window before reranking so these primary provisions
        # cannot be displaced by merely similar articles.
        final_top_k = max(final_top_k, 7 if sensitive_results else 6)
        if source_allows_named_supplement(law_name, source, PIPL_LAW_NAME):
            export_condition_results.extend(fetch_article_range_with_scores(
                collection_name=collection_name,
                start_article_no=38,
                # Article 38 is the outbound-transfer path; Articles 39 and
                # 40 supply the accompanying separate-consent and threshold /
                # localisation conditions.  Keeping this compact contiguous
                # window prevents an otherwise grounded answer from citing
                # Article 40 while the final evidence window omits it.
                end_article_no=40,
                doc_type=doc_type,
                block_type=block_type,
                document_type=document_type,
                law_name=law_name or PIPL_LAW_NAME,
                source=source,
                law_level=law_level,
                authority_level=authority_level,
                jurisdiction=jurisdiction,
                issuing_authority=issuing_authority,
                legal_effect=legal_effect,
                standard_type=standard_type,
                case_type=case_type,
                patent_type=patent_type,
                category=category,
                version=version,
            ))
            export_condition_expected[PIPL_LAW_NAME] = [38, 39, 40]
            if sensitive_results:
                export_condition_results.extend(sensitive_results)
                export_condition_expected[PIPL_LAW_NAME] = [28, 38, 39, 40]
        if source_allows_named_supplement(law_name, source, STANDARD_CONTRACT_MEASURES_NAME):
            export_condition_results.extend(fetch_article_range_with_scores(
                collection_name=collection_name,
                start_article_no=5,
                end_article_no=5,
                doc_type=doc_type,
                block_type=block_type,
                document_type=document_type,
                law_name=law_name or STANDARD_CONTRACT_MEASURES_NAME,
                source=source,
                law_level=law_level,
                authority_level=authority_level,
                jurisdiction=jurisdiction,
                issuing_authority=issuing_authority,
                legal_effect=legal_effect,
                standard_type=standard_type,
                case_type=case_type,
                patent_type=patent_type,
                category=category,
                version=version,
            ))
            export_condition_expected[STANDARD_CONTRACT_MEASURES_NAME] = [5]
        if debug_info is not None:
            debug_info["deterministic_supplements"]["personal_info_export_conditions"] = summarize_debug_results(
                export_condition_results
            )
        anchor_candidates = merge_results(anchor_candidates, export_condition_results)

    if (
        use_deterministic_anchors
        and "标准合同" in question
        and "重新评估" in question
        and document_type in {None, "法律法规"}
        and source_allows_named_supplement(law_name, source, STANDARD_CONTRACT_MEASURES_NAME)
    ):
        contract_reassessment_results = fetch_article_range_with_scores(
            collection_name=collection_name,
            start_article_no=8,
            end_article_no=8,
            doc_type=doc_type,
            block_type=block_type,
            document_type=document_type,
            law_name=law_name or STANDARD_CONTRACT_MEASURES_NAME,
            source=source,
            law_level=law_level,
            authority_level=authority_level,
            jurisdiction=jurisdiction,
            issuing_authority=issuing_authority,
            legal_effect=legal_effect,
            standard_type=standard_type,
            case_type=case_type,
            patent_type=patent_type,
            category=category,
            version=version,
        )
        if debug_info is not None:
            debug_info["deterministic_supplements"]["standard_contract_article_8"] = summarize_debug_results(
                contract_reassessment_results
            )
        anchor_candidates = merge_results(anchor_candidates, contract_reassessment_results)

    if (
        use_deterministic_anchors
        and "数据出境安全评估" in question
        and any(hint in question for hint in ["重点评估", "评估哪些", "哪些内容"])
        and document_type in {None, "法律法规"}
    ):
        data_export_assessment_results = []
        if source_allows_named_supplement(law_name, source, DATA_EXPORT_MEASURES_NAME):
            data_export_assessment_results.extend(fetch_article_range_with_scores(
                collection_name=collection_name,
                start_article_no=5,
                end_article_no=5,
                doc_type=doc_type,
                block_type=block_type,
                document_type=document_type,
                law_name=law_name or DATA_EXPORT_MEASURES_NAME,
                source=source,
                law_level=law_level,
                authority_level=authority_level,
                jurisdiction=jurisdiction,
                issuing_authority=issuing_authority,
                legal_effect=legal_effect,
                standard_type=standard_type,
                case_type=case_type,
                patent_type=patent_type,
                category=category,
                version=version,
            ))
        if source_allows_named_supplement(law_name, source, PIPL_LAW_NAME):
            data_export_assessment_results.extend(fetch_article_range_with_scores(
                collection_name=collection_name,
                start_article_no=55,
                end_article_no=55,
                doc_type=doc_type,
                block_type=block_type,
                document_type=document_type,
                law_name=law_name or PIPL_LAW_NAME,
                source=source,
                law_level=law_level,
                authority_level=authority_level,
                jurisdiction=jurisdiction,
                issuing_authority=issuing_authority,
                legal_effect=legal_effect,
                standard_type=standard_type,
                case_type=case_type,
                patent_type=patent_type,
                category=category,
                version=version,
            ))
        if debug_info is not None:
            debug_info["deterministic_supplements"]["data_export_assessment"] = summarize_debug_results(
                data_export_assessment_results
            )
        anchor_candidates = merge_results(anchor_candidates, data_export_assessment_results)

    concept_anchor_results: list[tuple[Document, float]] = []
    for target_law_name, article_numbers in concept_anchor_map.items():
        if not source_allows_named_supplement(law_name, source, target_law_name):
            continue
        fetched_concept_results = fetch_article_numbers_with_scores(
            collection_name=collection_name,
            article_numbers=list(article_numbers),
            doc_type=doc_type,
            block_type=block_type,
            document_type=document_type,
            law_name=law_name or target_law_name,
            source=source,
            law_level=law_level,
            authority_level=authority_level,
            jurisdiction=jurisdiction,
            issuing_authority=issuing_authority,
            legal_effect=legal_effect,
            standard_type=standard_type,
            case_type=case_type,
            patent_type=patent_type,
            category=category,
            version=version,
        )
        for doc, _ in fetched_concept_results:
            doc.metadata.setdefault(
                "_anchor_rerank_hint",
                "法学术语直接法源：该条文对应用户问题中的明确法律概念，应优先判断其是否直接回答问题。",
            )
        concept_anchor_results.extend(
            _sort_results_by_article_order(fetched_concept_results, list(article_numbers))
        )
    if concept_anchor_results:
        if debug_info is not None:
            debug_info["deterministic_supplements"]["legal_concept_anchors"] = summarize_debug_results(
                concept_anchor_results
            )
        anchor_candidates = merge_results(concept_anchor_results, anchor_candidates)

    # v0.3.10: 统一从 JSON 规则库匹配场景锚点（覆盖全部 7 个法域）
    # 若 category 已知则限定匹配范围；否则跨域匹配（保留数据合规兼容性）
    scene_anchor_results = []
    for target_law_name, article_numbers in unified_scene_anchors.items():
        if not source_allows_named_supplement(law_name, source, target_law_name):
            continue
        sorted_article_numbers = list(article_numbers)
        fetched_scene_results = fetch_article_numbers_with_scores(
            collection_name=collection_name,
            article_numbers=sorted_article_numbers,
            doc_type=doc_type,
            block_type=block_type,
            document_type=document_type,
            law_name=law_name or target_law_name,
            source=source,
            law_level=law_level,
            authority_level=authority_level,
            jurisdiction=jurisdiction,
            issuing_authority=issuing_authority,
            legal_effect=legal_effect,
            standard_type=standard_type,
            case_type=case_type,
            patent_type=patent_type,
            category=category,
            version=version,
        )
        scene_anchor_results.extend(
            _sort_results_by_article_order(fetched_scene_results, sorted_article_numbers)
        )
    if scene_anchor_results:
        if debug_info is not None:
            debug_info["deterministic_supplements"]["scene_article_anchors"] = summarize_debug_results(
                scene_anchor_results
            )
        anchor_candidates = merge_results(scene_anchor_results, anchor_candidates)

    # v0.3.9: 从 JSON 规则库补充领域分类锚点
    if use_deterministic_anchors and category and not scene_anchor_results:
        category_anchors = get_category_supplements(category) if category != "数据合规" else {}
        if not category_anchors and category == "数据合规":
            # 数据合规 domain 保留原有硬编码逻辑，此处跳过
            pass
        category_anchor_results = []
        for target_law_name, article_numbers in category_anchors.items():
            if not source_allows_named_supplement(law_name, source, target_law_name):
                continue
            category_anchor_results.extend(fetch_article_numbers_with_scores(
                collection_name=collection_name,
                article_numbers=sorted(article_numbers),
                doc_type=doc_type, block_type=block_type,
                document_type=document_type,
                law_name=target_law_name, source=source,
                law_level=law_level, authority_level=authority_level,
                jurisdiction=jurisdiction, issuing_authority=issuing_authority,
                legal_effect=legal_effect, standard_type=standard_type,
                case_type=case_type, patent_type=patent_type,
                category=category, version=version,
            ))
        if category_anchor_results:
            if debug_info is not None:
                debug_info["deterministic_supplements"]["category_anchors"] = summarize_debug_results(
                    category_anchor_results
                )
            anchor_candidates = merge_results(anchor_candidates, category_anchor_results)

    anchor_sections = (
        standard_anchor_sections(question, document_type)
        if use_deterministic_anchors
        else []
    )
    if anchor_sections:
        standard_anchor_results = fetch_standard_sections_with_scores(
            collection_name=collection_name,
            section_numbers=anchor_sections,
            doc_type=doc_type,
            block_type="standard_section",
            document_type=document_type,
            law_name=law_name,
            source=source,
            law_level=law_level,
            authority_level=authority_level,
            jurisdiction=jurisdiction,
            issuing_authority=issuing_authority,
            legal_effect=legal_effect,
            standard_type=standard_type,
            case_type=case_type,
            patent_type=patent_type,
            category=category,
            version=version,
        )
        if debug_info is not None:
            debug_info["deterministic_supplements"]["standard_anchor_sections"] = summarize_debug_results(
                standard_anchor_results
            )
        anchor_candidates = merge_results(anchor_candidates, standard_anchor_results)

    anchors = [doc for doc, _ in anchor_candidates]
    for doc in anchors:
        key = _candidate_exact_key(doc)
        if key not in seen:
            doc.metadata.setdefault("_anchor_rerank_hint", "场景锚点候选：该法条由规则锚点命中，应优先判断其是否直接回应当前问题。")
            merged.append(doc)
            seen.add(key)
    if anchor_candidates:
        anchor_docs_by_key = {}
        anchor_keys_in_order = []
        for doc, _ in anchor_candidates:
            key = _candidate_exact_key(doc)
            if key in anchor_docs_by_key:
                continue
            anchor_docs_by_key[key] = doc
            anchor_keys_in_order.append(key)
        protected_anchor_keys = set(anchor_docs_by_key)
        protected_anchors = [anchor_docs_by_key[key] for key in anchor_keys_in_order if key in seen]
        base_candidates = [doc for doc in merged if _candidate_exact_key(doc) not in protected_anchor_keys]
        merged = _limit_base_and_anchor_candidates(
            base_candidates,
            protected_anchors,
            max_total=rerank_input_limit,
            base_quota=rerank_base_quota,
            anchor_quota=rerank_anchor_quota,
        )
    else:
        merged = _limit_candidates_by_article_budget(merged, max_total=rerank_input_limit)

    if debug_info is not None:
        debug_info["anchor_candidates"] = summarize_debug_results(anchor_candidates)
        debug_info["rerank_input_candidates"] = summarize_debug_results(
            [(doc, 0.0) for doc in merged],
            limit=rerank_input_limit,
        )

    rerank_query = build_search_query(question, domain=category, reasoning=reasoning)
    if complex_case_plans:
        issue_query_hint = "\n".join(
            f"问题{plan['id']}：{plan['issue']}；法域：{'、'.join(plan['domains'])}"
            for plan in complex_case_plans
        )
        rerank_query = f"{rerank_query}\n复杂案例问题拆解：\n{issue_query_hint}"
    anchor_hint = _format_anchor_rerank_hint(unified_scene_anchors)
    if anchor_hint:
        rerank_query = f"{rerank_query}\n{anchor_hint}"
    if concept_anchor_map:
        concept_parts = []
        for target_law_name, article_numbers in concept_anchor_map.items():
            articles = "、".join(f"第{article_no}条" for article_no in article_numbers)
            concept_parts.append(f"{target_law_name}{articles}")
        rerank_query = f"{rerank_query}\n法学术语直接法源：" + "；".join(concept_parts)
    if debug_info is not None:
        debug_info["used_rerank_query"] = rerank_query

    def cross_encoder_rerank(
        query: str,
        docs: list[Document],
        top_k: int = 3,
        selector_query: str = "",
    ) -> list[tuple[Document, float]]:
        if not docs:
            return []
        documents = [_rerank_document_text(doc) for doc in docs]
        scores = _call_siliconflow_rerank(query, documents)
        if len(scores) != len(docs):
            logger.warning("Reranker returned %d scores for %d docs", len(scores), len(docs))
            return []
        reranked = _sort_rerank_scores_stable(docs, [float(score) for score in scores])
        reranked_pairs = [(doc, float(score)) for doc, score in reranked]
        reranked_pairs = _stabilize_same_bucket_rerank_order(
            reranked_pairs,
            query=selector_query or query,
        )
        selected = _select_diverse_rerank_top(
            reranked_pairs,
            top_k=top_k,
            query=selector_query or query,
        )
        if debug_info is not None:
            debug_info["rerank_full_score_order"] = _debug_rerank_full_score_order(docs, reranked_pairs)
            debug_info["final_evidence_selection_trace"] = _debug_final_evidence_selection_trace(
                docs,
                reranked_pairs,
                selected,
                mode="cross_encoder",
                top_k=top_k,
            )
        return selected

    if complex_multi_issue:
        reranked_results = [(doc, 0.0) for doc in merged[:final_top_k]]
        if debug_info is not None:
            debug_info["final_evidence_selection_trace"] = {
                "mode": "complex_case_planner_fast_path",
                "top_k": final_top_k,
                "reason": "skip_cross_encoder_for_planned_multi_issue_case",
            }
    elif use_cross_encoder:
        try:
            reranked_results = cross_encoder_rerank(rerank_query, merged, top_k=final_top_k, selector_query=question)
        except Exception:
            logger.warning("Cross-Encoder rerank failed; falling back to dense top-3", exc_info=True)
            reranked_results = []
    else:
        reranked_results = [(doc, 0.0) for doc in merged[:final_top_k]]
        if debug_info is not None:
            debug_info["final_evidence_selection_trace"] = {
                "mode": "candidate_order_without_rerank",
                "top_k": final_top_k,
                "reason": "experiment_profile_disabled_cross_encoder",
            }

    if not reranked_results:
        if debug_info is not None:
            debug_info["rerank_dense_fallback"] = True
        fallback_candidates = concept_anchor_results + dense_results
        fallback_by_key = {}
        for doc, score in fallback_candidates:
            fallback_by_key.setdefault(_candidate_exact_key(doc), (doc, float(score)))
        reranked_results = list(fallback_by_key.values())[:final_top_k]
        if debug_info is not None:
            fallback_docs = [doc for doc, _ in fallback_candidates]
            fallback_pairs = [(doc, float(score)) for doc, score in reranked_results]
            debug_info["final_evidence_selection_trace"] = _debug_final_evidence_selection_trace(
                fallback_docs,
                fallback_pairs,
                fallback_pairs,
                mode="dense_fallback",
                top_k=final_top_k,
                reason="empty_reranked_results",
            )

    reranked_results = _ensure_anchor_evidence(
        reranked_results,
        scene_anchor_results,
        unified_scene_anchors,
        final_top_k,
    )
    reranked_results = _ensure_concept_primary_evidence(
        reranked_results,
        concept_anchor_results,
        question,
        final_top_k,
    )
    if export_condition_results:
        reranked_results = _ensure_anchor_evidence(
            reranked_results,
            export_condition_results,
            export_condition_expected,
            final_top_k,
        )

    if debug_info is not None:
        debug_info["merged_candidate_count"] = len(merged)
        debug_info["reranked_candidates"] = summarize_debug_results(reranked_results)
        debug_info["final_candidates"] = summarize_debug_results(reranked_results)

    evidence_results = reranked_results
    if complex_multi_issue and anchor_candidates:
        evidence_by_key = {}
        for plan in complex_case_plans:
            added_for_plan = 0
            for doc, score in anchor_candidates:
                metadata = doc.metadata
                source = metadata.get("source") or metadata.get("law_name")
                article_no = metadata.get("article_no")
                if source not in plan.get("anchors", {}) or article_no not in plan["anchors"][source]:
                    continue
                key = _candidate_exact_key(doc)
                if key in evidence_by_key:
                    continue
                evidence_by_key[key] = (doc, score)
                added_for_plan += 1
                if added_for_plan >= 4:
                    break
        for doc, score in reranked_results:
            key = _candidate_exact_key(doc)
            if key in evidence_by_key:
                continue
            evidence_by_key[key] = (doc, score)
        evidence_results = list(evidence_by_key.values())[:24]

    evidence_chain = build_evidence_chain(evidence_results, used_query=search_query)
    if external_evidence:
        evidence_chain.extend(external_evidence[:8])
    retrieval_confidence = calculate_retrieval_confidence(evidence_chain, k)
    missing_evidence = build_missing_evidence(evidence_chain, retrieval_confidence, k)
    evidence_sufficiency = assess_evidence_sufficiency(
        evidence_chain,
        question=question,
        requested_k=k,
    )
    for gap in evidence_sufficiency["gaps"]:
        if gap not in missing_evidence:
            missing_evidence.append(gap)
    missing_evidence.extend(find_missing_concept_primary_anchors(question, evidence_chain))
    user_materials = user_materials or []
    retrieval_elapsed_ms = round((perf_counter() - retrieval_started_at) * 1000, 2)
    if debug_info is not None:
        debug_info["retrieval_elapsed_ms"] = retrieval_elapsed_ms

    if retrieval_only:
        response = {
            "answer": "",
            "retrieval_only": True,
            "experiment_profile": profile.to_dict() if profile else None,
            "confidence_score": retrieval_confidence,
            "answer_confidence": None,
            "retrieval_confidence": retrieval_confidence,
            "needs_human_review": should_request_human_review(
                retrieval_confidence,
                None,
                None,
                missing_evidence,
            ),
            "missing_evidence": missing_evidence,
            "risk_level": None,
            "risk_types": [],
            "risk_type_evidence": [],
            "recommended_actions": [],
            "recommended_action_evidence": [],
            "evidence_chain": evidence_chain,
            "filters": filters,
            "sources": [
                {
                    "article": item.get("article", ""),
                    "citation": item.get("citation", ""),
                    "content": item.get("content", ""),
                }
                for item in evidence_chain
            ],
            "retrieval_elapsed_ms": retrieval_elapsed_ms,
            "evidence_sufficiency": evidence_sufficiency,
        }
        if debug_info is not None:
            response["debug_info"] = debug_info
        return response

    context = build_context(evidence_chain)
    if complex_case_plans:
        missing_laws = []
        for plan in complex_case_plans:
            missing_laws.extend(plan.get("missing_laws", []))
        missing_laws = list(dict.fromkeys(missing_laws))
        if missing_laws:
            missing_evidence.append("当前知识库未入库或未覆盖：" + "、".join(missing_laws))
        context = f"{format_complex_case_plan(complex_case_plans)}\n\n{context}"

    if not evidence_chain and not user_materials:
        response = {
            "answer": "未检索到足以回答该问题的法律法规、标准或其他合规依据，请调整问题或过滤条件后重试。",
            "confidence_score": 0.0,
            "answer_confidence": 0.0,
            "retrieval_confidence": retrieval_confidence,
            "needs_human_review": True,
            "missing_evidence": missing_evidence,
            "risk_level": None,
            "risk_types": [],
            "risk_type_evidence": [],
            "recommended_actions": [],
            "recommended_action_evidence": [],
            "evidence_chain": [],
            "filters": filters,
            "sources": [],
            "evidence_sufficiency": evidence_sufficiency,
        }
        if debug_info is not None:
            response["debug_info"] = debug_info
        response["evidence_sufficiency"] = evidence_sufficiency
        return apply_answer_mode_policy(
            response,
            question=question,
            mode=answer_mode,
            external_fact_needs=external_fact_needs,
            evidence_chain=[],
        )

    if complex_case_plans and not user_materials:
        complex_payload = build_complex_case_fast_payload(
            question,
            complex_case_plans,
            evidence_chain,
            retrieval_confidence,
            missing_evidence,
            filters,
            debug_info=debug_info,
        )
        complex_payload["evidence_sufficiency"] = evidence_sufficiency
        return apply_answer_mode_policy(
            complex_payload,
            question=question,
            mode=answer_mode,
            external_fact_needs=external_fact_needs,
            evidence_chain=evidence_chain,
        )

    response = generate_answer_payload(
        question=question,
        context=context,
        evidence_chain=evidence_chain,
        retrieval_confidence=retrieval_confidence,
        missing_evidence=missing_evidence,
        filters=filters,
        category=category,
        answer_mode=answer_mode,
        user_materials=user_materials,
        debug_info=debug_info,
    )
    response["evidence_sufficiency"] = evidence_sufficiency
    return apply_answer_mode_policy(
        response,
        question=question,
        mode=answer_mode,
        external_fact_needs=external_fact_needs,
        evidence_chain=evidence_chain,
    )


if __name__ == "__main__":
    result = rag_query("未经用户同意收集个人信息会有什么后果？")
    print("=== 回答 ===")
    print(result["answer"])
    print("\n=== 引用条文 ===")
    for s in result["sources"]:
        print(f"  {s['article']}: {s['content'][:60]}...")
