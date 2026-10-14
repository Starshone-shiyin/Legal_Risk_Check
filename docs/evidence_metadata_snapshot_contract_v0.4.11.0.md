# v0.4.11.0 Evidence Metadata Snapshot Contract

This contract defines a future read-only Qdrant payload snapshot runner. It does not connect to Qdrant or authorize data fixes.

## Overview

- Contract status: `ready_for_evidence_metadata_snapshot_runner`
- Sample cases: 8
- Snapshot targets: 19
- Allowed next step: `read_only_evidence_metadata_snapshot_runner`
- Qdrant access in this version: `not_run_in_contract`

## Boundaries

- Future runner may read Qdrant payloads with vectors disabled.
- No RAG query, embedding call, LLM call, full eval, metadata edit, chunk rewrite, ingestion change, anchor change, or eval-case change is authorized.
- The runner must report Qdrant unavailability as a blocker instead of fabricating evidence-level results.
