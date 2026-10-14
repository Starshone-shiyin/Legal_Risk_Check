# v0.4.13.2 Ingestion Metadata Patch Dry-Run Design

This report designs a future local dry-run. It does not patch ingestion, write Qdrant, or run RAG.

## Overview

- Status: `ready_for_ingestion_metadata_patch_dry_run_design_gate`
- Dry-run target: `simulate_build_article_documents_boundary_metadata_patch`
- Future runner scope: `local in-memory comparison only`
- Stable ID impact: `expected`

## Comparison Strategy

- build pre-patch documents with current build_article_documents behavior
- build post-patch documents with an isolated simulation helper that only adds chunk_index/chunk_count
- run assign_stable_chunk_ids on cloned pre/post documents to estimate chunk_id and qdrant_point_id drift
- compare page_content, citation, block_type, paragraph_no, item_no, item_label, chunk_index, chunk_count, chunk_id, qdrant_point_id

## Expected Drift

- `chunk_index`
- `chunk_count`
- `chunk_id`
- `qdrant_point_id`

## Forbidden Drift

- `page_content`
- `citation`
- `block_type`
- `paragraph_no`
- `item_no`
- `item_label`
- `parent_article_id`

## Blocking Conditions

- any content_changed row
- any citation_changed row
- any block_type/paragraph_no/item_no/item_label drift
- pre/post document count mismatch for a sample
- missing chunk_index or chunk_count after simulation
