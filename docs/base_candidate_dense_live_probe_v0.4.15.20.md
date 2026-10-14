# v0.4.15.20 Base Candidate Dense Live Probe

## Scope

This version adds `tools/build_base_candidate_dense_live_probe.py`, an explicit
dense-enabled wrapper around the v0.4.15.19 live read-only probe.

Dense probing is intentionally separated from the default read-only probe
because it may call the external embedding service to generate query vectors.
Qdrant access remains read-only.

## Result

Output:

- `tests/base_candidate_dense_live_probe_v0.4.15.20_report.json`

Summary:

- status: `completed_with_dense_probe`
- checked refs: 14
- Qdrant payload present: 14/14
- runtime metadata filter present: 14/14
- attribution counts:
  - `sparse_rank_cutoff_loss`: 10
  - `dense_rank_cutoff_loss`: 2
  - `base_retrieval_gap_confirmed_with_dense_probe`: 2

## Engineering Interpretation

The remaining ambiguity from v0.4.15.19 is closed. The missing refs are in
Qdrant and pass runtime filters. Most losses are sparse rank/cutoff losses.
Two refs are dense high-k but not dense runtime-k losses. Two refs are not found
by sparse high-k or dense high-k and should be treated as deeper base recall
gaps.

The next practical engineering step is a small runtime validation patch around
base candidate depth/union collection, not anchor expansion.

## Boundary

- Qdrant write: not performed.
- `rag_query`: not called.
- Eval: not run.
- LLM and reranker: not called.
- Dense embedding query generation: explicit opt-in in this version.
- No hidden seed, anchor, prompt, rerank, risk supplement, term preservation,
  scenario registry, fixture, eval case, or retriever runtime change.

## Verification

- `.\venv\Scripts\python.exe -m py_compile tools\build_base_candidate_dense_live_probe.py tests\test_base_candidate_dense_live_probe.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_base_candidate_dense_live_probe`
- `.\venv\Scripts\python.exe tools\build_base_candidate_dense_live_probe.py --mismatch tests\base_candidate_mismatch_summary_v0.4.15.18_report.json --trace tests\targeted_dependency_trace_v0.4.15.16_report.json --collection legal_knowledge --output tests\base_candidate_dense_live_probe_v0.4.15.20_report.json`
