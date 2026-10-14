# v0.4.9.0 Retrieval Input Quality Intake

This intake converts existing retrieval and evidence diagnostics into governance buckets for future input-quality work. It does not change retrieval behavior.

## Overview

- Intake status: `ready_for_retrieval_input_quality_planning`
- Buckets: 5
- Ready buckets: 5
- Sample cases: 12
- Base gap cases: 34
- Anchor dependency cases: 33
- Implementation allowed: False

## Buckets

| Bucket | Status | Evidence count |
|---|---|---|
| `source_article_identity_quality` | `ready_for_future_quality_audit` | 1 |
| `metadata_chunking_quality` | `ready_for_future_quality_audit` | 33 |
| `query_lexical_coverage_quality` | `ready_for_future_quality_audit` | 34 |
| `legal_domain_boundary_quality` | `ready_for_future_quality_audit` | 6 |
| `anchor_dependency_quality` | `ready_for_future_quality_audit` | 33 |

## Boundaries

- This is saved-report intake only.
- It does not call backend APIs, RAG, Qdrant, or LLM services.
- It does not modify retrieval, rerank, prompts, eval cases, fixtures, anchors, risk rules, or scenario registry.
- The next step should specify audit contracts before any implementation work.
