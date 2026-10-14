# v0.4.13.0 Ingestion Metadata Patch Contract

This contract defines the future patch boundary. It does not patch ingestion or rebuild Qdrant.

## Overview

- Status: `ready_for_ingestion_metadata_patch_contract_gate`
- Patch target: `src/rag/ingestion.py::build_article_documents`
- Allowed future scope: `add deterministic chunk_index/chunk_count metadata only`
- Requires rebuild: `True`

## Patch Contract

- Allowed file: `src/rag/ingestion.py`
- Allowed function: `build_article_documents`
- Required metadata fields: `chunk_index, chunk_count`
- Parent article rule: `chunk_index=1`, `chunk_count=1`, no content change.
- Paragraph/item rule: 1-based emission order, `chunk_count=len(article_parts)`, no content change.
- Standard section behavior must remain unchanged.

## Future Tests Required

- build_article_documents parent article has chunk_index=1 and chunk_count=1
- paragraph and item documents have deterministic 1-based chunk_index
- paragraph and item documents have chunk_count equal to len(article_parts)
- page_content and citation output remain unchanged
- build_standard_section_documents contract remains unchanged
- future stable ID drift is explicit and expected before rebuild

## Rebuild Dry-Run Requirements

- estimate affected sources and block types before writing Qdrant
- estimate chunk_id and qdrant_point_id drift before writing Qdrant
- provide rollback path before rebuild
- run qdrant integrity after any approved rebuild
- run targeted RAG eval after any approved rebuild
