# v0.4.17.3 RAG Targeted Repeat Closeout

## Scope

v0.4.17.3 executes the bounded targeted repeat suggested by the v0.4.17.2 packet. It runs RAG eval against the existing runtime and `legal_knowledge` collection, but does not modify retriever code, prompts, anchors, rerank, risk supplement rules, term preservation rules, taxonomy, scenario registry, fixtures, eval cases, hidden seeds, or Qdrant data.

## What Was Run

- Input packet: `tests/rag_targeted_rerun_packet_v0.4.17.2_report.json`
- Output report: `tests/targeted_rag_evidence_independence_v0.4.17.3_report.json`
- Case count: 17
- Repeat: 3
- Options: `--check-risk --compact-report`

Command:

```powershell
.\venv\Scripts\python.exe tools\run_rag_eval.py --cases tests\rag_eval_cases.json --check-risk --compact-report --repeat 3 --case-id risk_antitrust_price_fixing_001 --case-id risk_patent_invalid_001 --case-id risk_vat_false_invoice_001 --case-id positive_antitrust_independent_pricing_001 --case-id risk_ai_medical_training_export_001 --case-id risk_algorithm_bias_001 --case-id risk_app_location_ads_002 --case-id risk_chatbot_training_001 --case-id risk_antitrust_concentration_001 --case-id risk_tort_product_liability_001 --case-id positive_company_capital_contribution_001 --case-id positive_company_dividend_001 --case-id risk_antitrust_market_dominance_001 --case-id risk_unfair_competition_confusion_001 --case-id cross_law_export_assessment_001 --case-id dsl_data_classification_001 --case-id pipl_sensitive_definition_001 --output tests\targeted_rag_evidence_independence_v0.4.17.3_report.json
```

The command exits with code `1` because the packet intentionally includes one known strict risk-level failure. The JSON report was still written successfully.

## Result

- pass counts: `[16, 16, 16]`
- total counts: `[17, 17, 17]`
- retrieval stage: `PASS=17` in all three runs
- unstable cases: `0`
- label variation cases: `1`
- persistent failed case: `risk_unfair_competition_confusion_001`

Group result:

| group | run result | interpretation |
|---|---:|---|
| `base_retrieval_query_lexical_triage` | `8/8` in all runs | No targeted repeat failure; do not patch anchor or base retrieval from this packet alone. |
| `output_rule_dependency_review` | `5/5` in all runs | Stable pass; keep observing rule dependency, but no immediate runtime patch. |
| `failed_or_expected_level_review` | `0/1` in all runs | Persistent `over_risk` expected-level / fact-strength review item. |
| `pure_llm_control` | `3/3` in all runs | Control group stable. |

The only label variation is `dsl_data_classification_001`: run 1 is `TERM_PRESERVATION_PASS`, runs 2-3 are `PURE_LLM_PASS`. It does not affect pass/fail, evidence hit, or risk checks.

## Decision

No runtime patch was made in this version.

The targeted repeat does not justify adding anchors or changing prompt/rerank/risk supplement behavior. The next practical step should isolate `risk_unfair_competition_confusion_001` as a legal fact-strength / expected-level review problem, or run a narrow full-eval confirmation before any main-chain patch.

## Verification

- `./venv/Scripts/python.exe tools/run_rag_eval.py ... --repeat 3 ... --output tests/targeted_rag_evidence_independence_v0.4.17.3_report.json`
- `./venv/Scripts/python.exe -m py_compile src/main.py tools/run_project_health_check.py`
- `./venv/Scripts/python.exe -m unittest tests.test_rag_targeted_rerun_packet tests.test_rag_evidence_independence_baseline tests.test_project_health_check tests.test_roadmap_hygiene`
- `./venv/Scripts/python.exe tools/check_test_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_artifact_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_tool_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_encoding_hygiene.py`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`
- `git diff --check`
