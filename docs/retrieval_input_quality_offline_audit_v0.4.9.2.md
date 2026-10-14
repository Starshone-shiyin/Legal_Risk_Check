# v0.4.9.2 Retrieval Input Quality Offline Audit

This report runs the v0.4.9.1 audit contract against existing saved reports only. It records impact signals and diagnostic routing without changing retrieval behavior.

## Overview

- Audit status: `completed_saved_report_offline_audit`
- Audit rows: 5
- High severity rows: 3
- Total impacted signal count: 140
- Unique sample cases: 9
- Implementation allowed: False

## Audit Results

| Result | Bucket | Severity | Impacted cases | Next route |
|---|---|---|---:|---|
| `RIQ-OFFLINE-AUDIT-001` | `source_article_identity_quality` | `medium` | 34 | `source_article_identity_diagnostic_report` |
| `RIQ-OFFLINE-AUDIT-002` | `metadata_chunking_quality` | `high` | 33 | `metadata_chunking_diagnostic_report` |
| `RIQ-OFFLINE-AUDIT-003` | `query_lexical_coverage_quality` | `high` | 34 | `query_lexical_coverage_diagnostic_report` |
| `RIQ-OFFLINE-AUDIT-004` | `legal_domain_boundary_quality` | `medium` | 6 | `legal_domain_boundary_diagnostic_report` |
| `RIQ-OFFLINE-AUDIT-005` | `anchor_dependency_quality` | `high` | 33 | `anchor_dependency_reduction_diagnostic_report` |

## Boundaries

- This is a saved-report offline audit runner only.
- It does not call backend APIs, vector stores, language models, or run full evaluation.
- It does not modify retrieval, rerank, prompts, eval cases, fixtures, anchors, risk rules, or scenario registry.
- The next step may add a lightweight gate for this offline audit report.
