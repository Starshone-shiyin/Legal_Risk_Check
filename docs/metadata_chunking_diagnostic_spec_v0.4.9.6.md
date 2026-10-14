# v0.4.9.6 Metadata/Chunking Diagnostic Spec

This specification defines the first metadata/chunking diagnostic contract from saved planning reports only. It does not run a diagnostic or authorize changes.

## Overview

- Status: `ready_for_future_metadata_chunking_diagnostic_runner`
- Next allowed step: `metadata_chunking_diagnostic_runner_design`
- Check groups: 5
- Required fields: 23
- Sample cases: 8
- Impacted case signal: 33
- Diagnostic not run: True
- Implementation allowed: False

## Check Groups

| Spec row | Check group | Required fields |
|---|---|---|
| `MCD-SPEC-001` | `metadata_identity_fields` | chunk_id, parent_article_id, law_name, source, article_no_or_section_no, citation |
| `MCD-SPEC-002` | `chunk_boundary_fields` | chunk_index, chunk_count, block_type, paragraph_no, item_no |
| `MCD-SPEC-003` | `article_locator_fields` | article_no, section_no, section_title, parent_article_id, citation |
| `MCD-SPEC-004` | `sample_case_mapping` | case_id, expected_evidence_id, source_audit_result_id, evidence_signals |
| `MCD-SPEC-005` | `diagnostic_output_contract` | case_id, metadata_field_status, chunk_boundary_status, parent_article_link_status, citation_identity_status, diagnostic_followup |

## Sample Case Scope

- `cross_law_export_assessment_001`
- `pipl_principles_001`
- `pipl_sensitive_definition_001`
- `positive_antitrust_independent_pricing_001`
- `risk_ai_medical_training_export_001`
- `risk_algorithm_bias_001`
- `risk_antitrust_price_fixing_001`
- `risk_app_location_ads_002`

## Prohibited Actions

- `merge_or_rewrite_chunks`
- `edit_metadata`
- `change_ingestion_pipeline`
- `tune_retrieval_parameters`
- `add_anchor_rules`
- `modify_eval_cases_or_fixtures`

## Boundaries

- This is a metadata/chunking diagnostic specification only.
- It does not merge chunks, edit metadata, change ingestion, tune retrieval parameters, add anchors, or modify eval cases/fixtures.
- It does not call backend/vector/language-model services and does not run full evaluation.
