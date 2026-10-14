# v0.4.15.18 Base Candidate Source / Lexical Mismatch Summary

## Scope

This version adds the saved-report-only summary tool
`tools/build_base_candidate_mismatch_summary.py`.

The tool reads:

- `tests/targeted_dependency_trace_v0.4.15.16_report.json`
- `tests/base_retrieval_query_inspection_v0.4.15.17_report.json`

It summarizes source/article drift and query overlap for the anchor-filled
cases identified in v0.4.15.17. It does not run eval, call `rag_query`, access
Qdrant/LLM, or mutate runtime/config/test fixtures.

## Result

Output:

- `tests/base_candidate_mismatch_summary_v0.4.15.18_report.json`

Summary:

- status: `qdrant_or_live_retrieval_needed`
- inspected cases: 7
- classification counts: `same_source_article_drift=7`
- missing final refs from base union: 14
- `qdrant_stop_required=true`

## Engineering Interpretation

Saved reports now show a consistent pattern: in the seven inspected
anchor-filled cases, base union candidates often come from the correct broad
law source family, but miss the final article-level refs later supplied by
anchors. This means the next diagnostic boundary is no longer query hinting or
anchor expansion.

The saved reports cannot prove which of these is true:

- the final refs are absent from Qdrant payloads;
- the final refs exist but are filtered before union candidate collection;
- the final refs exist but score below candidate cutoffs;
- live retrieval ordering changes under current Qdrant state.

Resolving that requires Qdrant/live retrieval inspection. This version stops at
that boundary.

## Boundary

- No hidden seed, anchor, prompt, rerank, risk supplement, term preservation,
  scenario registry, fixture, eval case, Qdrant, retriever, or `rag_query`
  change.
- The tool reads saved reports only.
- This is an offline RAG grounding diagnostic, not a gate and not a runtime
  fix.

## Verification

- `.\venv\Scripts\python.exe -m py_compile tools\build_base_candidate_mismatch_summary.py tests\test_base_candidate_mismatch_summary.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_base_candidate_mismatch_summary`
- `.\venv\Scripts\python.exe tools\build_base_candidate_mismatch_summary.py --trace tests\targeted_dependency_trace_v0.4.15.16_report.json --inspection tests\base_retrieval_query_inspection_v0.4.15.17_report.json --output tests\base_candidate_mismatch_summary_v0.4.15.18_report.json`
