# v0.4.9.1 Retrieval Input Quality Audit Spec

This specification turns the v0.4.9.0 intake buckets into offline audit contracts. It does not run audits or change retrieval behavior.

## Overview

- Spec status: `ready_for_future_offline_audit_design`
- Audit specs: 5
- Priority summary: {'P0': 3, 'P1': 2}
- Required output fields: 30
- Gate checks: 15
- Audits not run: True
- Implementation allowed: False

## Audit Specs

| Spec | Bucket | Priority | Status |
|---|---|---|---|
| `RIQ-AUDIT-SPEC-001` | `source_article_identity_quality` | `P0` | `ready_for_future_offline_audit` |
| `RIQ-AUDIT-SPEC-002` | `metadata_chunking_quality` | `P0` | `ready_for_future_offline_audit` |
| `RIQ-AUDIT-SPEC-003` | `query_lexical_coverage_quality` | `P1` | `ready_for_future_offline_audit` |
| `RIQ-AUDIT-SPEC-004` | `legal_domain_boundary_quality` | `P1` | `ready_for_future_offline_audit` |
| `RIQ-AUDIT-SPEC-005` | `anchor_dependency_quality` | `P0` | `ready_for_future_offline_audit` |

## Boundaries

- This is an audit specification only.
- It does not execute audits, call backend APIs, RAG, Qdrant, or LLM services.
- It does not modify retrieval, rerank, prompts, eval cases, fixtures, anchors, risk rules, or scenario registry.
- The next step may build an offline audit runner against this contract.
