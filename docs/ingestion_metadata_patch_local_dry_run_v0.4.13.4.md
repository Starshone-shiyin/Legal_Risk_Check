# v0.4.13.4 Ingestion Metadata Patch Local Dry-Run

This report runs a local in-memory simulation only. It does not patch ingestion, write Qdrant, or run RAG.

## Summary

- Status: `passed`
- Samples: `3`
- Documents: `8` pre / `8` post
- Boundary metadata drift rows: `8`
- Chunk ID drift rows: `8`
- Qdrant point ID drift rows: `8`
- Forbidden drift rows: `0`
- Allowed next step: `ingestion_metadata_patch_local_dry_run_gate`

## Samples

### single_paragraph_article

- Pre block counts: `{'article': 1, 'paragraph': 1, 'item': 0}`
- Post block counts: `{'article': 1, 'paragraph': 1, 'item': 0}`
- Blockers: `[]`

### multi_paragraph_article

- Pre block counts: `{'article': 1, 'paragraph': 2, 'item': 0}`
- Post block counts: `{'article': 1, 'paragraph': 2, 'item': 0}`
- Blockers: `[]`

### paragraph_with_items

- Pre block counts: `{'article': 1, 'paragraph': 0, 'item': 2}`
- Post block counts: `{'article': 1, 'paragraph': 0, 'item': 2}`
- Blockers: `[]`

## Guardrails

- `local_in_memory_only`: `True`
- `qdrant_access`: `disallowed`
- `qdrant_write`: `disallowed`
- `knowledge_base_fulltext_scan`: `disallowed`
- `rag_query_integration`: `disallowed`
- `embedding_call`: `disallowed`
- `llm_access`: `disallowed`
- `full_eval`: `not_run`
- `implementation_allowed`: `False`
- `code_patch_authorized`: `False`
- `retrieval_logic_change_allowed`: `False`
- `ingestion_source_mutation`: `disallowed`
- `anchor_mutation`: `disallowed`
- `risk_rule_mutation`: `disallowed`
- `eval_case_mutation`: `disallowed`
