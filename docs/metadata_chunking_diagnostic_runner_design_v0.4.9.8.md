# v0.4.9.8 Metadata/Chunking Diagnostic Runner Design

This design defines a future read-only diagnostic runner contract. It does not run diagnostics or authorize metadata, chunking, ingestion, retrieval, rerank, prompt, rule, fixture, or eval-case changes.

## Overview

- Status: `ready_for_metadata_chunking_diagnostic_runner_gate`
- Next allowed step: `metadata_chunking_diagnostic_runner_design_gate`
- Design rows: 5
- Output fields: 10
- Sample cases: 8
- Diagnostic run: `not_run`
- Implementation allowed: False

## Design Rows

| Design row | Check group | Failure buckets |
|---|---|---|
| `MCD-RUNNER-DESIGN-001` | `metadata_identity_fields` | metadata_completeness_gap, citation_identity_gap |
| `MCD-RUNNER-DESIGN-002` | `chunk_boundary_fields` | chunk_boundary_ambiguity |
| `MCD-RUNNER-DESIGN-003` | `article_locator_fields` | article_locator_gap, parent_article_link_gap |
| `MCD-RUNNER-DESIGN-004` | `sample_case_mapping` | sample_case_mapping_gap |
| `MCD-RUNNER-DESIGN-005` | `diagnostic_output_contract` | metadata_completeness_gap, chunk_boundary_ambiguity, parent_article_link_gap, citation_identity_gap, article_locator_gap, sample_case_mapping_gap |

## Output Contract

- `case_id`
- `source_spec_row_id`
- `check_group`
- `metadata_completeness_status`
- `chunk_boundary_status`
- `parent_article_link_status`
- `citation_identity_status`
- `article_locator_status`
- `diagnostic_followup`
- `blocking_findings`

## Boundaries

- This is a runner design only.
- It does not read Qdrant, scan the knowledge base, run RAG, call an LLM, or run full evaluation.
- It does not merge chunks, edit metadata, change ingestion, tune retrieval parameters, add anchors, or modify eval cases/fixtures.
