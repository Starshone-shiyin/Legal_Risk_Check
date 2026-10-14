# v0.4.9.4 Retrieval Input Quality Diagnostic Prioritization

This report ranks diagnostic routes from the passed offline audit gate. It is planning only and does not authorize runtime changes.

## Overview

- Status: `ready_for_diagnostic_spec_design`
- Priority rows: 5
- Top route: `metadata_chunking_diagnostic_report`
- Severity summary: {'high': 3, 'medium': 2}
- Total impacted signal count: 140
- Implementation allowed: False

## Priority Matrix

| Rank | Route | Bucket | Severity | Impacted cases |
|---:|---|---|---|---:|
| 1 | `metadata_chunking_diagnostic_report` | `metadata_chunking_quality` | `high` | 33 |
| 2 | `anchor_dependency_reduction_diagnostic_report` | `anchor_dependency_quality` | `high` | 33 |
| 3 | `query_lexical_coverage_diagnostic_report` | `query_lexical_coverage_quality` | `high` | 34 |
| 4 | `source_article_identity_diagnostic_report` | `source_article_identity_quality` | `medium` | 34 |
| 5 | `legal_domain_boundary_diagnostic_report` | `legal_domain_boundary_quality` | `medium` | 6 |

## Boundaries

- This is diagnostic prioritization only.
- It does not run evaluation, call backend/vector/language-model services, or change runtime behavior.
- It does not authorize retrieval, rerank, prompt, anchor, risk rule, fixture, scenario registry, or eval-case changes.
- The next step may gate this prioritization before any diagnostic spec work.
