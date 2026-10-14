# v0.4.12.1 Metadata/Chunking Fix Design

This report is a design handoff only. It does not patch ingestion, rebuild Qdrant, or change retrieval.

## Overview

- Status: `ready_for_fix_design_gate`
- Design target: `build_article_documents_chunk_boundary_metadata`
- Requires rebuild: `True`
- Stable ID impact: `expected`

## Proposed Patch Plan

- `add_article_boundary_metadata`: Assign deterministic chunk_index/chunk_count to article, paragraph, and item documents produced by the legal article ingestion path.
- `preserve_standard_section_contract`: Leave the existing standard_section chunk_index/chunk_count behavior unchanged.
- `rebuild_instead_of_payload_patch`: Because stable chunk IDs include chunk_index, apply the future fix through an ingestion rebuild/dry-run path rather than direct Qdrant payload mutation.

## Metadata Contract

- Required fields: `chunk_index, chunk_count`
- Affected block types: `article, paragraph, item`

## Stable ID Impact

- `assign_stable_chunk_ids` already includes `chunk_index`; future implementation is expected to change chunk IDs and Qdrant point IDs.
- Direct Qdrant payload patching remains disallowed. A rebuild/dry-run plan is required before any data write.

## Required Future Validations

- ingestion unit tests for article/paragraph/item chunk_index and chunk_count
- stable chunk ID drift test documenting expected ID changes
- rebuild dry-run report before writing Qdrant
- qdrant index integrity check after any approved rebuild
- targeted RAG eval after rebuild
- full RAG eval only after behavior-impacting rebuild is approved

## Boundary

- do not patch src/rag/ingestion.py in v0.4.12.1
- do not patch src/rag/retriever.py
- do not write Qdrant payloads
- do not rebuild the collection
- do not change anchor/risk supplement rules
- do not change eval cases or fixtures
