# v0.4.15.19 Base Candidate Live Read-Only Probe

## Scope

This version adds `tools/build_base_candidate_live_readonly_probe.py`, a targeted
Qdrant live read-only probe for the 14 final refs flagged by v0.4.15.18.

Default execution performs:

- Qdrant collection reachability and point count checks;
- exact payload `scroll` for each missing final ref;
- runtime metadata-filtered `scroll` for each missing final ref;
- sparse retrieval replay at runtime `k=10` and diagnostic `k=100`;
- base union reconstruction from live sparse results.

Dense probing is explicit opt-in through `--enable-dense-probe`, because it may
call the external embedding service to build a query vector.

## Result

Output:

- `tests/base_candidate_live_readonly_probe_v0.4.15.19_report.json`

Summary:

- status: `completed_requires_dense_probe`
- collection: `legal_knowledge`
- Qdrant points count: 7177
- missing refs checked: 14
- Qdrant payload present: 14/14
- runtime metadata filter present: 14/14
- sparse high-k present: 10/14
- attribution counts:
  - `sparse_rank_cutoff_loss`: 10
  - `base_retrieval_gap_requires_dense_probe`: 4

## Engineering Interpretation

The missing final refs are not absent from Qdrant and are not excluded by the
runtime metadata filters. The main confirmed failure mode is sparse retrieval
rank cutoff: ten refs appear in sparse high-k but not in the production sparse
`k=10` path or final base union.

Four refs still require dense rank inspection before final attribution:

- PIPL article 9
- PIPL article 38
- PIPL article 6 in the anonymization case
- VAT article 37

This narrows the next runtime work: avoid anchor expansion. The likely repair
area is base retrieval candidate collection depth, candidate union budgeting,
or dense/sparse recall calibration, validated with dense probe and targeted
regression before changing runtime.

## Boundary

- Qdrant write: not performed.
- `rag_query`: not called.
- Eval: not run.
- LLM and reranker: not called.
- No hidden seed, anchor, prompt, rerank, risk supplement, term preservation,
  scenario registry, fixture, eval case, or retriever runtime change.

## Verification

- `.\venv\Scripts\python.exe -m py_compile tools\build_base_candidate_live_readonly_probe.py tests\test_base_candidate_live_readonly_probe.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_base_candidate_live_readonly_probe`
- `.\venv\Scripts\python.exe tools\build_base_candidate_live_readonly_probe.py --mismatch tests\base_candidate_mismatch_summary_v0.4.15.18_report.json --trace tests\targeted_dependency_trace_v0.4.15.16_report.json --collection legal_knowledge --output tests\base_candidate_live_readonly_probe_v0.4.15.19_report.json`
