# v0.4.15.8 Post Near-Tie Patch Main-Chain Repair

## Scope

v0.4.15.8 is a main RAG path repair release. It closes the broad regression introduced by the earlier near-tie stabilization scope and restores the full saved RAG eval set to 60/60.

This release does not change hidden seeds, anchors, prompts, risk supplement rules, term preservation rules, scenario registry, fixtures, or eval cases.

## Problem

After v0.4.15.7, a full RAG eval run showed a regression:

- Report: `tests/post_near_tie_patch_full_rag_eval_v0.4.15.8_report.json`
- Result: 31/60 passed
- Retrieval failure stage summary: `PASS=32`, `RERANK_MISS=28`

The root cause was that same-bucket stabilization used the existing coarse stable-score bucket and reordered large groups. That was too broad: it could override meaningful Cross-Encoder order inside a large bucket instead of only stabilizing true near ties.

## Runtime Repair

`src/rag/retriever.py` now limits `_stabilize_same_bucket_rerank_order()` to small true near-tie groups:

- maximum stabilized group size: 3
- maximum score span: 0.01
- large same-bucket groups keep their existing Cross-Encoder order

This preserves the original Cross-Encoder ranking for broad buckets while still stabilizing the small boundary cases that motivated v0.4.15.6.

## Risk Taxonomy Repair

The final remaining full-eval failure after the retriever scope repair was `risk_antitrust_market_dominance_001`. Retrieval passed, but risk level stayed `medium` although the structured risk type already contained `滥用市场支配地位风险`.

`src/risk/taxonomy.py` now lets `classify_risk_categories()` match an exact taxonomy `name` in structured inputs, not only keyword aliases. This allows `infer_taxonomy_risk_level()` to upgrade the risk level to the taxonomy default `high` when the RAG payload already contains the canonical risk type name.

## Validation Results

- Targeted near-tie regression repeat: `tests/targeted_post_near_tie_regression_v0.4.15.8_report.json`
  - 5 selected cases, repeat 3
  - all runs full pass
- Targeted antitrust risk-level repeat: `tests/targeted_antitrust_risk_level_v0.4.15.8_report.json`
  - repeat 3
  - all runs full pass
- Final full RAG eval: `tests/post_near_tie_patch_full_rag_eval_after_scope_fix_v0.4.15.8_report.json`
  - 60/60 passed
  - retrieval failure stage summary: `PASS=60`

## Boundary

- No anchor change.
- No prompt change.
- No eval case change.
- No hidden seed change.
- No risk supplement rule change.
- No term preservation rule change.
- No scenario registry change.
- No Qdrant rebuild.

This is a narrow main-chain repair: it reduces the blast radius of an existing stabilization patch and improves structured taxonomy inference from canonical risk type names.
