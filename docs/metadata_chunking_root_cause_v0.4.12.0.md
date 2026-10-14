# v0.4.12.0 Metadata/Chunking Root-Cause Report

This report converts the v0.4.11.x evidence snapshot findings into a root-cause hypothesis. It does not authorize a fix.

## Overview

- Status: `ready_for_metadata_chunking_fix_design`
- Primary root cause: `ingestion_article_chunks_missing_boundary_metadata`
- Confidence: `high`
- Chunk boundary ambiguity count: 19
- Qdrant integrity passed: True

## Boundary

- No ingestion patch, Qdrant rebuild, retrieval change, anchor change, prompt change, or eval-case edit is authorized.
- Next step is fix design, not implementation.
