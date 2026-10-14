# v0.4.15.13 RAG Eval Compact Report Profile

## Scope

This version adds an opt-in compact output profile to `tools/run_rag_eval.py`.
The default report remains unchanged. A caller must pass `--compact-report`
when writing an output file to remove bulky per-case debug payloads.

The compact profile is intended for review and repository maintenance when the
full debug trace is not needed. It is not a RAG retrieval, rerank, prompt,
anchor, risk-rule, eval-case, hidden-seed, fixture, or Qdrant change.

## Preserved Fields

Compact case reports keep the normal eval result fields, including:

- case outcome, checks, answer, evidence chain, risk fields, and contribution
  labels;
- `retrieval_diagnostics`;
- `quality_signal_diagnostics`;
- compact `debug_info_summary` counts for candidate pools and final-selection
  trace length;
- compact `contribution_trace_summary` counts.

## Removed Fields

Compact case reports remove the largest per-case payloads:

- full `debug_info`;
- full `contribution_trace`.

The removed payloads are still available by running the same command without
`--compact-report`.

## Validation Result

The focused smoke report
`tests/targeted_compact_report_profile_v0.4.15.13_report.json` was generated
for `risk_algorithm_bias_001` with `--compact-report`.

Result:

- 1/1 passed.
- `retrieval_failure_stage_summary={"PASS": 1}`.
- compact report contains `report_profile="compact"`.
- compact case report contains `debug_info_summary` and does not contain full
  `debug_info`.

## Boundary

- No `rag_query` main-chain behavior change.
- No retriever, rerank, anchor, prompt, risk supplement, term preservation,
  scenario registry, eval case, hidden seed, fixture, or Qdrant change.
- The feature is report-size control for RAG eval diagnostics, not a sample
  patching tool or grounding-quality bypass.

## Verification

- `.\venv\Scripts\python.exe -m py_compile tools\run_rag_eval.py tests\test_rag_eval_diagnostics.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_rag_eval_diagnostics`
- `.\venv\Scripts\python.exe tools\run_rag_eval.py --cases tests\rag_eval_cases.json --output tests\targeted_compact_report_profile_v0.4.15.13_report.json --check-risk --case-id risk_algorithm_bias_001 --compact-report`
