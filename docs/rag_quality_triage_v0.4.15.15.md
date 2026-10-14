# v0.4.15.15 RAG Quality Triage

## Scope

This version adds a saved-report-only triage builder:
`tools/build_rag_quality_triage.py`.

The tool reads an existing RAG eval report and summarizes pass quality,
contribution dependency, quality signals, and manual-review markers. It does
not run eval, call `rag_query`, contact Qdrant or an LLM, or mutate runtime
configuration.

## Result

Input:

- `tests/post_roadmap_maintenance_compact_full_rag_eval_v0.4.15.14_report.json`

Output:

- `tests/rag_quality_triage_v0.4.15.15_report.json`

Summary:

- status: `passed_with_high_dependency`
- full eval state: 60/60 passed
- retrieval stages: `{"PASS": 60}`
- anchor assisted: 31/60
- risk supplement assisted: 44/60
- pure LLM pass: 6/60
- anchor and risk supplement assisted: 25/60
- score-order risks: 0
- manual-review markers: `risk_gray_area_ai_training_001`,
  `risk_trademark_non_use_001`
- top dependency triage candidates: `risk_gray_area_ai_training_001`,
  `risk_trademark_non_use_001`, `risk_chatbot_training_001`,
  `risk_employee_data_export_001`,
  `positive_antitrust_independent_pricing_001`,
  `risk_vat_export_refund_001`

## Engineering Interpretation

There is no immediate full-eval failure to repair. The strongest current signal
is dependency quality: many passing cases still rely on anchors and/or risk
supplement output rules. The next engineering step should therefore be
dependency-reduction triage, especially base retrieval / query lexical triage
for anchor-assisted passes and output-rule dependency review for risk
supplement-assisted passes.

## Boundary

- No hidden seed, anchor, prompt, rerank, risk supplement, term preservation,
  scenario registry, fixture, eval case, Qdrant, retriever, or `rag_query`
  change.
- No new gate chain.
- This is a quality triage report, not a runtime fix.

## Verification

- `.\venv\Scripts\python.exe -m py_compile tools\build_rag_quality_triage.py tests\test_rag_quality_triage.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_rag_quality_triage`
- `.\venv\Scripts\python.exe tools\build_rag_quality_triage.py --input tests\post_roadmap_maintenance_compact_full_rag_eval_v0.4.15.14_report.json --output tests\rag_quality_triage_v0.4.15.15_report.json`
