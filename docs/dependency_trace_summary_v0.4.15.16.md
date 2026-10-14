# v0.4.15.16 Dependency Trace Summary

## Scope

This version captures a targeted full-debug trace packet for dependency-heavy
passing cases identified by v0.4.15.15. It then summarizes that trace with the
saved-report-only builder `tools/build_dependency_trace_summary.py`.

The targeted eval run intentionally omits `--compact-report` so that
`debug_info`, rerank full score order, final evidence selection trace, and
output contribution trace remain available for inspection.

## Inputs

- `tests/rag_quality_triage_v0.4.15.15_report.json`
- `tests/targeted_dependency_trace_v0.4.15.16_report.json`

## Outputs

- `tests/dependency_trace_summary_v0.4.15.16_report.json`

## Result

- Targeted trace packet: 8/8 passed.
- Retrieval stages: `{"PASS": 8}`.
- Contribution labels in targeted trace: `ANCHOR_PASS=7`,
  `RISK_SUPPLEMENT_PASS=8`.
- Dependency summary:
  - `base_union_gap_anchor_filled`: 7 cases
  - `union_satisfied_but_manual_review_or_output_rule_dependency`: 1 case
- Human review markers:
  - `risk_gray_area_ai_training_001`
  - `risk_trademark_non_use_001`

## Engineering Interpretation

The targeted packet does not show a current failure. It shows why these cases
are high-priority quality work:

- Most dependency-heavy passing cases still have base union retrieval gaps that
  anchors fill.
- The next useful engineering step is query lexical / base retrieval inspection
  before any anchor change.
- `risk_trademark_non_use_001` is different: union retrieval is already
  satisfied, but manual-review/output-rule dependency remains visible.

## Boundary

- No hidden seed, anchor, prompt, rerank, risk supplement, term preservation,
  scenario registry, fixture, eval case, Qdrant, retriever, or `rag_query`
  change.
- The summary builder is saved-report-only.
- This version is an observability packet, not a runtime fix or a new gate.

## Verification

- `.\venv\Scripts\python.exe tools\run_rag_eval.py --cases tests\rag_eval_cases.json --output tests\targeted_dependency_trace_v0.4.15.16_report.json --check-risk --case-id risk_gray_area_ai_training_001 --case-id risk_trademark_non_use_001 --case-id risk_chatbot_training_001 --case-id risk_employee_data_export_001 --case-id positive_antitrust_independent_pricing_001 --case-id risk_vat_export_refund_001 --case-id risk_ai_medical_training_export_001 --case-id risk_contract_auto_renewal_001`
- `.\venv\Scripts\python.exe -m py_compile tools\build_dependency_trace_summary.py tests\test_dependency_trace_summary.py`
- `.\venv\Scripts\python.exe -m unittest tests.test_dependency_trace_summary`
- `.\venv\Scripts\python.exe tools\build_dependency_trace_summary.py --input tests\targeted_dependency_trace_v0.4.15.16_report.json --triage tests\rag_quality_triage_v0.4.15.15_report.json --output tests\dependency_trace_summary_v0.4.15.16_report.json`
