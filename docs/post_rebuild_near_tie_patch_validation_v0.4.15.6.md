# v0.4.15.6 Near-Tie Patch Validation

## Conclusion

- status: `passed`
- blockers: `[]`
- runtime patch scope: `same_bucket_deterministic_ordering_only`
- repeat runs: `5`
- unique selected evidence chains: `1`

## Validation Scope

- Reads the post-patch targeted repeat saved report.
- Checks whether each run passed, whether final selection trace is available, and whether final evidence identity is stable.
- This validation only proves the runtime effect of same-bucket deterministic ordering; it does not repair samples, add anchors, or change prompt/risk supplement/eval cases.

## Boundary

This tool does not run eval, call `rag_query`, connect to Qdrant, call an LLM, or mutate runtime state.
If the targeted repeat saved report is missing, this tool fails closed with a blocked validation report.
The runtime patch itself may only stabilize candidate order inside existing Cross-Encoder stable-score buckets; it must not change scores, model, query, `score_epsilon`, top_k, anchor, prompt, risk supplement, term preservation, scenario registry, fixtures, eval cases, or hidden seed.
