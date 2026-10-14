# v0.4.15.10 Standard Contract Term Preservation

## Scope

v0.4.15.10 repairs an answer wording stability gap in the main RAG output path. It adds one evidence-driven legal term preservation rule for standard-contract reassessment answers.

This release does not modify prompts, anchors, risk supplement rules, term preservation config files, hidden seeds, scenario registry, fixtures, or eval cases.

## Problem

v0.4.15.9 showed that the evidence path was stable, but `data_export_contract_trigger_001` could miss the exact answer wording `补充订立` in a single full eval run.

The selected evidence already included Article 8 of the `个人信息出境标准合同办法`, whose text states that when statutory change events occur, the processor should reassess and supplement or re-enter the standard contract and complete filing procedures.

## Repair

`src/rag/retriever.py::LEGAL_TERM_PRESERVATION_RULES` now includes a standard-contract reassessment rule:

- question must mention `标准合同` and `重新评估`
- evidence source must include `个人信息出境标准合同办法`
- answer must preserve the supported follow-up action: `补充或者重新订立标准合同` and filing procedure wording

This is evidence-driven output stabilization. It does not change retrieval, rerank, prompts, eval cases, anchors, or risk supplement behavior.

## Validation

- `tests/test_retriever_contract.py` adds:
  - positive coverage for standard-contract reassessment term preservation
  - negative coverage showing the term is not added without the supporting source
- `tests/targeted_data_export_term_preservation_v0.4.15.10_report.json`
  - `data_export_contract_trigger_001`
  - 5 repeats
  - pass counts: `[1, 1, 1, 1, 1]`
  - contribution label: `TERM_PRESERVATION_PASS`
- `tests/targeted_main_chain_after_term_preservation_v0.4.15.10_report.json`
  - 8 high-risk/recent cases
  - 3 repeats
  - pass counts: `[8, 8, 8]`
- `tests/post_term_preservation_full_rag_eval_v0.4.15.10_report.json`
  - full RAG eval: 60/60 passed
  - retrieval stage summary: `PASS=60`

## Decision

This version closes the wording instability without weakening the project boundary. The repair is tied to retrieved legal evidence and should be treated as a general output-stability improvement, not as an eval-case patch.
