# v0.4.10.0 Metadata/Chunking Diagnostic Runner Manifest

This manifest expands approved saved-report samples into diagnostic runner inputs. It does not implement or execute the runner.

## Overview

- Status: `ready_for_saved_report_metadata_chunking_diagnostic_runner`
- Next allowed step: `saved_report_metadata_chunking_diagnostic_runner`
- Cases: 8
- Check groups: 5
- Manifest items: 40
- Diagnostic run: `not_run`
- Implementation allowed: False

## Boundaries

- Saved reports only.
- No diagnostic execution in this version.
- No Qdrant access, knowledge-base fulltext scan, RAG call, LLM call, metadata edit, chunk rewrite, ingestion change, anchor change, or eval-case change.
