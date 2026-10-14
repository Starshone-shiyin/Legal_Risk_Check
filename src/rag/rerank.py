from __future__ import annotations

import re
from collections import Counter

from langchain_core.documents import Document


def _call_siliconflow_rerank(question: str, documents: list[str]) -> list[float]:
    """通过 SiliconFlow API 调用 bge-reranker-v2-m3。"""
    import requests
    from src.config import get_settings

    settings = get_settings()
    resp = requests.post(
        f"{settings.siliconflow_base_url}/rerank",
        headers={
            "Authorization": f"Bearer {settings.siliconflow_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "BAAI/bge-reranker-v2-m3",
            "query": question,
            "documents": documents,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results", [])
    scores: list[float | None] = [None] * len(documents)
    for position, item in enumerate(results):
        score = float(item["relevance_score"])
        index = item.get("index", position)
        if isinstance(index, int) and 0 <= index < len(scores):
            scores[index] = score
    return [0.0 if score is None else score for score in scores]


def _candidate_article_key(doc: Document):
    """Return a coarse evidence key used only for candidate-budget diversity."""
    metadata = doc.metadata
    source = metadata.get("source") or metadata.get("law_name") or ""
    parent_article_id = metadata.get("parent_article_id")
    if parent_article_id:
        return ("parent", source, parent_article_id)
    article_no = metadata.get("article_no")
    if article_no is not None:
        return ("article", source, article_no)
    section_no = metadata.get("section_no")
    if section_no:
        return ("section", source, section_no)
    return ("chunk", metadata.get("chunk_id") or doc.page_content[:100])


def _candidate_exact_key(doc: Document):
    metadata = doc.metadata
    return (
        metadata.get("chunk_id")
        or f"{metadata.get('source')}_{metadata.get('article_no') or metadata.get('section_no')}"
        or doc.page_content[:100]
    )


def _sort_results_by_article_order(
    results: list[tuple[Document, float]],
    article_numbers: list[int],
) -> list[tuple[Document, float]]:
    """Make rule-injected article anchors follow the rule's legal order."""
    article_order = {article_no: index for index, article_no in enumerate(article_numbers)}
    block_order = {"article": 0, "paragraph": 1, "item": 2}
    return sorted(
        results,
        key=lambda item: (
            article_order.get(item[0].metadata.get("article_no"), len(article_order)),
            block_order.get(item[0].metadata.get("block_type"), 9),
            item[0].metadata.get("paragraph_no") or 0,
            item[0].metadata.get("item_no") or 0,
        ),
    )


def _limit_candidates_by_article_budget(
    docs: list[Document],
    max_total: int = 15,
    max_per_article: int = 2,
) -> list[Document]:
    """Keep candidates under budget while preventing one article's siblings from crowding out others."""
    selected: list[Document] = []
    selected_exact_keys = set()
    article_counts: Counter = Counter()

    def add(doc: Document, ignore_article_limit: bool = False) -> bool:
        if len(selected) >= max_total:
            return False
        exact_key = _candidate_exact_key(doc)
        if exact_key in selected_exact_keys:
            return False
        article_key = _candidate_article_key(doc)
        if not ignore_article_limit and article_counts[article_key] >= max_per_article:
            return False
        selected.append(doc)
        selected_exact_keys.add(exact_key)
        article_counts[article_key] += 1
        return True

    for doc in docs:
        if article_counts[_candidate_article_key(doc)] == 0:
            add(doc)
    for doc in docs:
        add(doc)
    for doc in docs:
        add(doc, ignore_article_limit=True)
    return selected


def _limit_base_and_anchor_candidates(
    base_docs: list[Document],
    anchor_docs: list[Document],
    max_total: int = 15,
    base_quota: int = 5,
    anchor_quota: int = 10,
) -> list[Document]:
    """Balance organic recall and injected anchors before the single rerank stage."""
    selected: list[Document] = []
    seen_exact_keys = set()

    def add_many(docs: list[Document], limit: int):
        nonlocal selected
        remaining = max(0, min(limit, max_total - len(selected)))
        if remaining == 0:
            return
        fresh_docs = []
        for doc in docs:
            exact_key = _candidate_exact_key(doc)
            if exact_key in seen_exact_keys:
                continue
            fresh_docs.append(doc)
        for doc in _limit_candidates_by_article_budget(fresh_docs, max_total=remaining):
            exact_key = _candidate_exact_key(doc)
            if exact_key in seen_exact_keys or len(selected) >= max_total:
                continue
            selected.append(doc)
            seen_exact_keys.add(exact_key)

    add_many(anchor_docs, anchor_quota)
    add_many(base_docs, base_quota)
    add_many(base_docs + anchor_docs, max_total)
    return selected


def _rerank_document_text(doc: Document, max_chars: int = 900) -> str:
    """Build the text sent to Cross-Encoder without changing the final ranking rule."""
    metadata = doc.metadata
    labels = [
        metadata.get("_anchor_rerank_hint"),
        metadata.get("citation"),
        metadata.get("source") or metadata.get("law_name"),
        metadata.get("article") or metadata.get("section_title"),
    ]
    content = metadata.get("parent_content") or doc.page_content
    text = "\n".join(str(item) for item in labels + [content] if item)
    return text[:max_chars]


_ALIGNMENT_CONSEQUENCE_TERMS = (
    "撤销",
    "注销",
    "无效",
    "解除",
    "终止",
    "停止",
    "禁止",
    "不得",
    "责令",
    "改正",
    "更正",
    "删除",
    "赔偿",
    "补偿",
    "赔付",
    "追偿",
    "罚款",
    "处罚",
    "没收",
    "召回",
    "承担",
    "连带",
)

_ALIGNMENT_CONSEQUENCE_PATTERNS = (
    (
        "责任",
        re.compile(
            r"(承担|法律|赔偿|侵权|违约|连带|补充|主要|民事|行政|刑事|产品|过错|追究)责任"
            r"|责任(承担|认定|主体|范围|后果|追究)"
        ),
    ),
)


_ALIGNMENT_QUERY_STOP_TERMS = (
    "是否",
    "存在",
    "需要",
    "可以",
    "应当",
    "如何",
    "什么",
    "哪些",
    "该",
    "某",
    "公司",
    "平台",
    "风险",
    "法律",
    "规定",
    "相关",
    "有限责任",
)

_ALIGNMENT_LEGAL_CONCEPT_TERMS = (
    "个人信息",
    "敏感个人信息",
    "人脸信息",
    "生物识别",
    "境外",
    "出境",
    "接收方",
    "云服务商",
    "安全评估",
    "申报",
    "告知",
    "同意",
    "单独同意",
    "处理目的",
    "处理方式",
    "保存期限",
    "存储期限",
    "必要性",
    "股权转让",
    "通知",
    "其他股东",
    "优先购买权",
    "注册商标",
    "连续三年",
    "不使用",
    "撤销",
)

_ALIGNMENT_OBLIGATION_COMPLEMENT_TERMS = (
    "告知",
    "单独同意",
    "处理目的",
    "处理方式",
    "联系方式",
    "接收方",
    "保存期限",
    "存储期限",
    "优先购买权",
    "书面通知",
)

_ALIGNMENT_PRIMARY_OBLIGATION_TERMS = (
    "应当",
    "不得",
    "必须",
    "申报",
    "告知",
    "同意",
    "单独同意",
    "优先购买权",
    "撤销",
    "赔偿",
)

_ALIGNMENT_SECONDARY_PROCEDURE_TERMS = (
    "风险自评估报告",
    "提交以下材料",
    "评估以下内容",
    "重点评估",
    "申报书",
)


def _primary_alignment_query(query: str) -> str:
    """Keep only the user's question for evidence coverage checks."""
    lines = [line.strip() for line in str(query or "").splitlines() if line.strip()]
    for line in lines:
        if line.startswith(("相关检索概念", "场景锚点法条")):
            continue
        return line
    return ""


def _normalize_alignment_text(text: str) -> str:
    return re.sub(r"\s+", "", str(text or ""))


def _alignment_query_phrases(query: str) -> set[str]:
    text = _normalize_alignment_text(_primary_alignment_query(query))
    for stop_term in _ALIGNMENT_QUERY_STOP_TERMS:
        text = text.replace(stop_term, "")
    phrases: set[str] = set()
    for span in re.findall(r"[\u4e00-\u9fff]{4,}", text):
        max_size = min(8, len(span))
        for size in range(4, max_size + 1):
            for index in range(0, len(span) - size + 1):
                phrase = span[index : index + size]
                if not any(stop_term in phrase for stop_term in _ALIGNMENT_QUERY_STOP_TERMS):
                    phrases.add(phrase)
    return phrases


def _selector_document_text(doc: Document, max_chars: int = 1800) -> str:
    """Build selector-only evidence text without rerank or anchor helper hints."""
    metadata = doc.metadata
    labels = [
        metadata.get("citation"),
        metadata.get("source") or metadata.get("law_name"),
        metadata.get("article") or metadata.get("section_title"),
    ]
    content = metadata.get("parent_content") or doc.page_content
    text = "\n".join(str(item) for item in labels + [content] if item)
    return text[:max_chars]


def _shared_legal_concepts(query: str, doc: Document) -> set[str]:
    query_text = _normalize_alignment_text(_primary_alignment_query(query))
    doc_text = _normalize_alignment_text(_selector_document_text(doc, max_chars=1800))
    return {
        term
        for term in _ALIGNMENT_LEGAL_CONCEPT_TERMS
        if term in query_text and term in doc_text
    }


def _document_obligation_complements(doc: Document) -> set[str]:
    doc_text = _normalize_alignment_text(_selector_document_text(doc, max_chars=1800))
    return {term for term in _ALIGNMENT_OBLIGATION_COMPLEMENT_TERMS if term in doc_text}


def _document_primary_obligation_terms(doc: Document) -> set[str]:
    doc_text = _normalize_alignment_text(_selector_document_text(doc, max_chars=1800))
    terms = {term for term in _ALIGNMENT_PRIMARY_OBLIGATION_TERMS if term in doc_text}
    if any(term in doc_text for term in _ALIGNMENT_SECONDARY_PROCEDURE_TERMS):
        terms.discard("应当")
    return terms


def _document_has_secondary_procedure_signal(doc: Document) -> bool:
    doc_text = _normalize_alignment_text(_selector_document_text(doc, max_chars=1800))
    return any(term in doc_text for term in _ALIGNMENT_SECONDARY_PROCEDURE_TERMS)


def _alignment_profile(query: str, doc: Document) -> dict[str, set[str]]:
    doc_text = _normalize_alignment_text(_selector_document_text(doc, max_chars=1800))
    query_text = _normalize_alignment_text(_primary_alignment_query(query))
    phrases = {phrase for phrase in _alignment_query_phrases(query) if phrase in doc_text}
    consequences = {
        term
        for term in _ALIGNMENT_CONSEQUENCE_TERMS
        if term in query_text and term in doc_text
    }
    consequences.update(
        term
        for term, pattern in _ALIGNMENT_CONSEQUENCE_PATTERNS
        if term in query_text and pattern.search(doc_text)
    )
    return {"phrases": phrases, "consequences": consequences}


def _alignment_score(profile: dict[str, set[str]]) -> int:
    return len(profile["phrases"]) * 2 + len(profile["consequences"])


def _article_no_as_int(doc: Document) -> int | None:
    article_no = doc.metadata.get("article_no")
    if isinstance(article_no, int):
        return article_no
    if isinstance(article_no, str) and article_no.isdigit():
        return int(article_no)
    return None


def _document_source_key(doc: Document) -> str:
    return str(doc.metadata.get("source") or doc.metadata.get("law_name") or "")


def _is_article_neighborhood_outlier(
    candidate_doc: Document,
    selected: list[tuple[Document, float]],
    max_nearest_distance: int = 40,
    max_selected_span: int = 40,
) -> bool:
    """Avoid replacing a coherent statutory cluster with a distant generic article."""
    candidate_article = _article_no_as_int(candidate_doc)
    if candidate_article is None:
        return False
    candidate_source = _document_source_key(candidate_doc)
    if not candidate_source:
        return False

    selected_articles = []
    for doc, _ in selected:
        source = _document_source_key(doc)
        if source != candidate_source:
            continue
        article_no = _article_no_as_int(doc)
        if article_no is not None:
            selected_articles.append(article_no)
    if len(selected_articles) < 2:
        return False
    if max(selected_articles) - min(selected_articles) > max_selected_span:
        return False
    nearest_distance = min(abs(candidate_article - article_no) for article_no in selected_articles)
    return nearest_distance > max_nearest_distance


def _is_same_source_near_selected_article(
    candidate_doc: Document,
    selected: list[tuple[Document, float]],
    max_nearest_distance: int = 3,
) -> bool:
    candidate_article = _article_no_as_int(candidate_doc)
    if candidate_article is None:
        return False
    candidate_source = _document_source_key(candidate_doc)
    if not candidate_source:
        return False
    for doc, _ in selected:
        source = _document_source_key(doc)
        if source != candidate_source:
            continue
        article_no = _article_no_as_int(doc)
        if article_no is not None and abs(candidate_article - article_no) <= max_nearest_distance:
            return True
    return False


def _has_near_issue_coverage(
    query: str,
    candidate_doc: Document,
    selected: list[tuple[Document, float]],
    profile: dict[str, set[str]],
) -> bool:
    if not _is_same_source_near_selected_article(candidate_doc, selected):
        return False
    if len(profile["phrases"]) >= 2:
        return True
    shared_concepts = _shared_legal_concepts(query, candidate_doc)
    if len(shared_concepts) >= 2:
        return bool(_document_primary_obligation_terms(candidate_doc) or _document_obligation_complements(candidate_doc))
    obligation_complements = _document_obligation_complements(candidate_doc)
    return bool(shared_concepts) and len(obligation_complements) >= 2


def _is_near_obligation_complement(
    query: str,
    candidate_doc: Document,
    selected: list[tuple[Document, float]],
    profile: dict[str, set[str]],
) -> bool:
    if not _is_same_source_near_selected_article(candidate_doc, selected):
        return False
    return bool(_shared_legal_concepts(query, candidate_doc)) and len(_document_obligation_complements(candidate_doc)) >= 2


def _can_balance_repeated_source(
    candidate_doc: Document,
    selected: list[tuple[Document, float]],
) -> bool:
    candidate_source = _document_source_key(candidate_doc)
    if not candidate_source:
        return False
    source_counts = Counter(_document_source_key(doc) for doc, _ in selected)
    return any(source and source != candidate_source and count > 1 for source, count in source_counts.items())


def _near_issue_protected_indexes(query: str, selected: list[tuple[Document, float]]) -> set[int]:
    protected: set[int] = set()
    for index, (doc, _) in enumerate(selected):
        peer_selected = [item for peer_index, item in enumerate(selected) if peer_index != index]
        if not peer_selected:
            continue
        profile = _alignment_profile(query, doc)
        if _has_near_issue_coverage(query, doc, peer_selected, profile) and _document_primary_obligation_terms(doc):
            protected.add(index)
    return protected


def _source_balance_replacement_indexes(
    candidate_doc: Document,
    selected: list[tuple[Document, float]],
) -> list[int]:
    candidate_source = _document_source_key(candidate_doc)
    if not candidate_source:
        return list(range(len(selected)))
    source_counts = Counter(_document_source_key(doc) for doc, _ in selected)
    same_source_indexes = [
        index
        for index, (doc, _) in enumerate(selected)
        if _document_source_key(doc) == candidate_source
    ]
    if same_source_indexes:
        return same_source_indexes
    if source_counts[candidate_source] == 0:
        return list(range(len(selected)))
    unprotected = [
        index
        for index, (doc, _) in enumerate(selected)
        if (
            _document_source_key(doc) == candidate_source
            or not _document_source_key(doc)
            or source_counts[_document_source_key(doc)] > 1
        )
    ]
    return unprotected


def _profile_covers(
    selected_profiles: list[dict[str, set[str]]],
    profile: dict[str, set[str]],
) -> bool:
    covered_phrases = set().union(*(item["phrases"] for item in selected_profiles)) if selected_profiles else set()
    covered_consequences = (
        set().union(*(item["consequences"] for item in selected_profiles)) if selected_profiles else set()
    )
    return profile["phrases"].issubset(covered_phrases) and profile["consequences"].issubset(covered_consequences)


def _has_issue_phrase_coverage(profile: dict[str, set[str]]) -> bool:
    return bool(profile["phrases"])


def _is_high_alignment_profile(profile: dict[str, set[str]]) -> bool:
    has_core_phrase = bool(profile["phrases"])
    has_consequence = bool(profile["consequences"])
    return has_core_phrase and has_consequence


def _retain_high_alignment_evidence(
    selected: list[tuple[Document, float]],
    reranked: list[tuple[Document, float]],
    query: str,
    top_k: int,
) -> list[tuple[Document, float]]:
    """Retain one strong issue-covering candidate already seen by the reranker."""
    if not query or len(selected) < top_k:
        return selected

    selected_exact_keys = {_candidate_exact_key(doc) for doc, _ in selected}
    selected_article_keys = {_candidate_article_key(doc) for doc, _ in selected}
    selected_profiles = [_alignment_profile(query, doc) for doc, _ in selected]
    covered_consequences = (
        set().union(*(item["consequences"] for item in selected_profiles)) if selected_profiles else set()
    )
    candidate: tuple[Document, float, dict[str, set[str]], tuple[int, int, int]] | None = None
    issue_candidate: tuple[Document, float, dict[str, set[str]], tuple[int, int, int, int]] | None = None

    for doc, score in reranked:
        if _candidate_exact_key(doc) in selected_exact_keys:
            continue
        if _candidate_article_key(doc) in selected_article_keys:
            continue
        if _is_article_neighborhood_outlier(doc, selected):
            continue
        profile = _alignment_profile(query, doc)
        has_near_issue_coverage = _has_near_issue_coverage(query, doc, selected, profile)
        if not _has_issue_phrase_coverage(profile) and not has_near_issue_coverage:
            continue
        if _document_has_secondary_procedure_signal(doc) and _near_issue_protected_indexes(query, selected):
            continue
        uncovered_consequences = profile["consequences"] - covered_consequences
        if _is_high_alignment_profile(profile) and not _profile_covers(selected_profiles, profile):
            protected_indexes = _near_issue_protected_indexes(query, selected)
            same_source_indexes = [
                index
                for index, (selected_doc, _) in enumerate(selected)
                if _document_source_key(selected_doc) == _document_source_key(doc)
            ]
            if same_source_indexes and all(index in protected_indexes for index in same_source_indexes):
                continue
            candidate_key = (len(uncovered_consequences), len(profile["consequences"]), _alignment_score(profile))
            if candidate is None or candidate_key > candidate[3]:
                candidate = (doc, score, profile, candidate_key)
        if has_near_issue_coverage:
            profile_already_covered = _profile_covers(selected_profiles, profile)
            has_obligation_complement = bool(_document_obligation_complements(doc))
            if profile_already_covered and not has_obligation_complement and not _can_balance_repeated_source(doc, selected):
                continue
            issue_key = (
                int(_can_balance_repeated_source(doc, selected)),
                int(has_near_issue_coverage),
                len(profile["phrases"]),
                _alignment_score(profile),
                int(float(score) * 1000),
            )
            if issue_candidate is None or issue_key > issue_candidate[3]:
                issue_candidate = (doc, score, profile, issue_key)

    if candidate is None and issue_candidate is None:
        return selected

    replacement = candidate
    issue_is_obligation_complement = (
        issue_candidate is not None
        and _is_near_obligation_complement(query, issue_candidate[0], selected, issue_candidate[2])
    )
    if issue_candidate is not None and (_can_balance_repeated_source(issue_candidate[0], selected) or issue_is_obligation_complement):
        replacement = issue_candidate
    elif replacement is None and issue_candidate is not None:
        replacement = issue_candidate
    if replacement is None:
        return selected

    replacement_indexes = _source_balance_replacement_indexes(replacement[0], selected)
    protected_indexes = _near_issue_protected_indexes(query, selected)
    if replacement is issue_candidate and issue_is_obligation_complement:
        replacement_source = _document_source_key(replacement[0])
        complement_indexes = [
            index
            for index, (doc, _) in enumerate(selected)
            if _document_source_key(doc) != replacement_source and index not in protected_indexes
        ]
        if complement_indexes:
            replacement_indexes = complement_indexes
    unprotected_replacement_indexes = [index for index in replacement_indexes if index not in protected_indexes]
    if unprotected_replacement_indexes:
        replacement_indexes = unprotected_replacement_indexes
    else:
        return selected
    if not replacement_indexes:
        return selected
    if replacement is issue_candidate:
        replacement_source = _document_source_key(replacement[0])
        source_counts = Counter(_document_source_key(doc) for doc, _ in selected)
        replacement_source_already_selected = bool(
            replacement_source
            and any(_document_source_key(doc) == replacement_source for doc, _ in selected)
        )
        repeated_other_source_indexes = [
            index
            for index, (doc, _) in enumerate(selected)
            if (
                not replacement_source_already_selected
                and
                _document_source_key(doc)
                and _document_source_key(doc) != replacement_source
                and source_counts[_document_source_key(doc)] > 1
            )
        ]
        filtered_repeated_other_source_indexes = [
            index for index in repeated_other_source_indexes if index not in protected_indexes
        ]
        if filtered_repeated_other_source_indexes:
            replacement_indexes = filtered_repeated_other_source_indexes
    replacement_indexes = [index for index in replacement_indexes if index not in protected_indexes]
    if not replacement_indexes:
        return selected
    weakest_index = min(
        replacement_indexes,
        key=lambda index: (
            len(selected_profiles[index]["consequences"]),
            _alignment_score(selected_profiles[index]),
            float(selected[index][1]),
        ),
    )
    weakest_score = _alignment_score(selected_profiles[weakest_index])
    if replacement is candidate:
        candidate_score = _alignment_score(replacement[2])
        candidate_adds_consequence = bool(replacement[2]["consequences"] - covered_consequences)
        if not candidate_adds_consequence and weakest_score >= candidate_score:
            replacement = None
    if replacement is issue_candidate:
        replaces_repeated_other_source = any(index == weakest_index for index in replacement_indexes) and (
            _document_source_key(selected[weakest_index][0]) != _document_source_key(replacement[0])
        )
        if not replacement[2]["phrases"] and not replaces_repeated_other_source:
            return selected
        if (
            not replaces_repeated_other_source
            and
            selected_profiles[weakest_index]["phrases"]
            and weakest_score >= _alignment_score(issue_candidate[2])
        ):
            return selected
    if replacement is None:
        return selected

    retained = list(selected)
    retained[weakest_index] = (replacement[0], replacement[1])
    return retained


def _select_diverse_rerank_top(
    reranked: list[tuple[Document, float]],
    top_k: int,
    query: str = "",
) -> list[tuple[Document, float]]:
    """Select top reranked docs while avoiding repeated siblings from the same article."""
    selected: list[tuple[Document, float]] = []
    seen_article_keys = set()
    seen_exact_keys = set()

    for doc, score in reranked:
        exact_key = _candidate_exact_key(doc)
        if exact_key in seen_exact_keys:
            continue
        article_key = _candidate_article_key(doc)
        if article_key in seen_article_keys:
            continue
        selected.append((doc, score))
        seen_exact_keys.add(exact_key)
        seen_article_keys.add(article_key)
        if len(selected) >= top_k:
            return _retain_high_alignment_evidence(selected, reranked, query, top_k)

    for doc, score in reranked:
        exact_key = _candidate_exact_key(doc)
        if exact_key in seen_exact_keys:
            continue
        selected.append((doc, score))
        seen_exact_keys.add(exact_key)
        if len(selected) >= top_k:
            break
    return _retain_high_alignment_evidence(selected, reranked, query, top_k)


def _sort_rerank_scores_stable(
    docs: list[Document],
    scores: list[float],
    score_epsilon: float = 0.1,
) -> list[tuple[Document, float]]:
    """Sort by Cross-Encoder score, preserving candidate order for near-ties."""
    scored = list(zip(docs, scores))
    if score_epsilon <= 0:
        return sorted(scored, key=lambda item: float(item[1]), reverse=True)
    return sorted(
        scored,
        key=lambda item: int(float(item[1]) / score_epsilon),
        reverse=True,
    )


def _same_bucket_stabilization_key(
    item: tuple[int, Document, float],
    query: str,
) -> tuple:
    input_rank, doc, score = item
    profile = _alignment_profile(query, doc) if query else {"phrases": set(), "consequences": set()}
    article_no = _article_no_as_int(doc)
    metadata = doc.metadata
    return (
        -_alignment_score(profile),
        -len(profile["consequences"]),
        -len(profile["phrases"]),
        str(metadata.get("source") or metadata.get("law_name") or ""),
        article_no if article_no is not None else 10**9,
        str(metadata.get("section_no") or ""),
        str(_candidate_exact_key(doc)),
        input_rank,
        -float(score),
    )


def _stabilize_same_bucket_rerank_order(
    reranked: list[tuple[Document, float]],
    query: str = "",
    score_epsilon: float = 0.1,
    max_stabilized_group_size: int = 3,
    max_stabilized_score_span: float = 0.01,
) -> list[tuple[Document, float]]:
    """Make same-bucket near-tie order deterministic without changing rerank scores."""
    if score_epsilon <= 0 or len(reranked) <= 1:
        return reranked

    buckets: list[tuple[int, list[tuple[int, Document, float]]]] = []
    current_bucket: int | None = None
    current_items: list[tuple[int, Document, float]] = []
    for input_rank, (doc, score) in enumerate(reranked):
        bucket = int(float(score) / score_epsilon)
        if current_bucket is None:
            current_bucket = bucket
        if bucket != current_bucket:
            buckets.append((current_bucket, current_items))
            current_bucket = bucket
            current_items = []
        current_items.append((input_rank, doc, float(score)))
    if current_bucket is not None:
        buckets.append((current_bucket, current_items))

    stabilized: list[tuple[Document, float]] = []
    for _, items in buckets:
        scores = [score for _, _, score in items]
        score_span = max(scores) - min(scores) if scores else 0.0
        if (
            1 < len(items) <= max_stabilized_group_size
            and score_span <= max_stabilized_score_span
        ):
            items = sorted(items, key=lambda item: _same_bucket_stabilization_key(item, query))
        stabilized.extend((doc, score) for _, doc, score in items)
    return stabilized


def _format_anchor_rerank_hint(anchors: dict[str, list[int] | set[int]]) -> str:
    """Append scene anchor intent to the rerank query without changing score fusion rules."""
    if not anchors:
        return ""
    parts = []
    for source, article_numbers in anchors.items():
        if not article_numbers:
            continue
        articles = "、".join(f"第{article_no}条" for article_no in article_numbers)
        parts.append(f"{source}{articles}")
    if not parts:
        return ""
    return "场景锚点法条：" + "；".join(parts)
