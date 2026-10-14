# v0.4.9.10 Metadata/Chunking Diagnostic Dry-Run Contract

This contract defines a future dry-run runner interface. It does not implement the runner, run diagnostics, read Qdrant, scan the knowledge base, call RAG, or call an LLM.

## Overview

- Status: `ready_for_v0_4_9_series_closeout`
- Next allowed step: `v0_4_9_series_closeout`
- Contract rows: 5
- Dry-run output fields: 14
- Runner implemented: False
- Diagnostic run: `not_run`
- Implementation allowed: False

## Contract Rows

| Contract row | Group | Status |
|---|---|---|
| `MCD-DRY-RUN-CONTRACT-001` | `input_saved_report_contract` | `ready_for_future_dry_run_runner` |
| `MCD-DRY-RUN-CONTRACT-002` | `cli_argument_contract` | `ready_for_future_dry_run_runner` |
| `MCD-DRY-RUN-CONTRACT-003` | `diagnostic_output_contract` | `ready_for_future_dry_run_runner` |
| `MCD-DRY-RUN-CONTRACT-004` | `failure_handling_contract` | `ready_for_future_dry_run_runner` |
| `MCD-DRY-RUN-CONTRACT-005` | `non_runtime_boundary_contract` | `ready_for_future_dry_run_runner` |

## Dry-Run Output Fields

- `report_version`
- `case_id`
- `source_spec_row_id`
- `check_group`
- `dry_run_status`
- `metadata_completeness_status`
- `chunk_boundary_status`
- `parent_article_link_status`
- `citation_identity_status`
- `article_locator_status`
- `diagnostic_followup`
- `blocking_findings`
- `source_runner_design_status`
- `source_design_gate_status`

## Boundaries

- This is a dry-run contract only.
- It does not create the future runner entrypoint.
- It does not read Qdrant, scan the knowledge base, run RAG, call an LLM, or run full evaluation.
- It does not merge chunks, edit metadata, change ingestion, tune retrieval parameters, add anchors, or modify eval cases/fixtures.
