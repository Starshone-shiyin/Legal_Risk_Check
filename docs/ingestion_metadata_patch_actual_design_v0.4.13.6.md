# v0.4.13.6 Ingestion Metadata Patch Actual Design

This report designs the actual ingestion metadata patch. It does not modify ingestion, write Qdrant, rebuild the collection, or change retrieval.

## Summary

- Status: `ready_for_actual_ingestion_metadata_patch_design_gate`
- Patch target: `src/rag/ingestion.py::build_article_documents`
- Allowed next step: `actual_ingestion_metadata_patch_design_gate`
- Implementation allowed: `False`
- Rebuild allowed: `False`
- Stable ID impact: `expected`

## Patch Rules

- Allowed file: `src/rag/ingestion.py`
- Allowed function: `build_article_documents`
- Parent rule: `{'block_type': 'article', 'chunk_index': 1, 'chunk_count': 1, 'content_change_allowed': False, 'citation_change_allowed': False}`
- Child rule: `{'block_types': ['paragraph', 'item'], 'chunk_index': '1-based emission order across article_parts', 'chunk_count': 'len(article_parts)', 'content_change_allowed': False, 'citation_change_allowed': False}`

## Implementation Sketch

- Set article metadata chunk_index=1 and chunk_count=1 when creating the parent article Document.
- Before iterating article_parts, compute child_chunk_count = len(article_parts) and child_chunk_index = 0.
- For each emitted paragraph or item child, increment child_chunk_index once and attach chunk_index=child_chunk_index and chunk_count=child_chunk_count.
- Do not alter page_content, citation, block_type, paragraph_no, item_no, item_label, parent_article_id, build_standard_section_documents, or assign_stable_chunk_ids.

## Post-Patch Validation Plan

- Add or update direct unit tests for build_article_documents parent article chunk_index=1 and chunk_count=1.
- Assert paragraph and item child chunks use deterministic 1-based emission order.
- Assert paragraph and item child chunks use chunk_count equal to len(article_parts).
- Assert page_content, citation, block_type, paragraph_no, item_no, item_label, and parent_article_id remain unchanged.
- Assert build_standard_section_documents behavior remains unchanged.
- Run a restricted diff check confirming only src/rag/ingestion.py changes among runtime sources.
- Do not rerun the v0.4.13.4 pre-patch drift runner as a post-patch drift expectation; after patch, direct metadata assertions become authoritative.

## Still Not Allowed

- patch src/rag/ingestion.py
- write Qdrant
- rebuild collection
- modify rag_query or retriever
- modify anchor or risk rules
- modify eval cases or fixtures
- run full eval as a substitute for post-patch metadata tests
