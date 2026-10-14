# v0.4.15.17 Base Retrieval / Query Inspection

## Scope

This version adds the saved-report-only inspection tool
`tools/build_base_retrieval_query_inspection.py`.

The tool reads the v0.4.15.16 full-debug trace packet and inspects whether
dependency-heavy passing cases have:

- base union retrieval gaps;
- final evidence refs supplied only by anchors;
- rerank queries that already include related concepts and scenario anchor
  statute hints;
- manual-review/output-rule dependency when union retrieval is already
  satisfied.

## Result

Output:

- `tests/base_retrieval_query_inspection_v0.4.15.17_report.json`

Summary:

- status: `base_retrieval_query_inspection_needed`
- total inspected cases: 8
- `base_union_gap_with_anchor_filled_final_refs`: 7
- `union_satisfied_manual_review_or_output_dependency`: 1
- the 7 anchor-filled cases already include scenario anchor statute hints in
  the rerank query, but base union retrieval still misses final refs later
  supplied by anchors.

## Engineering Interpretation

The current evidence does not support directly adding anchors or changing risk
supplement rules. The main actionable signal is earlier in retrieval: base
union candidate generation is not surfacing the final legal refs even when the
rerank query contains explicit related concepts and scenario anchor statute
hints.

The next useful step is to inspect the base candidate sources and query term
coverage for the seven anchor-filled cases. Any runtime change should wait
until that inspection shows a generalizable defect.

## Boundary

- No hidden seed, anchor, prompt, rerank, risk supplement, term preservation,
  scenario registry, fixture, eval case, Qdrant, retriever, or `rag_query`
  change.
- The tool reads saved reports only.
- This is an inspection artifact, not a runtime fix or gate.

## Verification

- `.\venv\Scripts\python.exe -m py_compile tools\build_base_retrieval_query_inspection.py tests\test_base_retrieval_query_inspection.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_base_retrieval_query_inspection`
- `.\venv\Scripts\python.exe tools\build_base_retrieval_query_inspection.py --trace tests\targeted_dependency_trace_v0.4.15.16_report.json --summary tests\dependency_trace_summary_v0.4.15.16_report.json --output tests\base_retrieval_query_inspection_v0.4.15.17_report.json`
