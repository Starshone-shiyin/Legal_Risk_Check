# v0.4.8.10 Final Evidence Selection Policy Language Revision Confirmation Record

This record captures the user's confirmation of the three narrowed policy-language drafts. The confirmed wording is only an input for future offline simulation design. It does not authorize runtime policy, rerank, prompt, eval case, fixture, rule, schema, importer, backend, Qdrant, LLM, or RAG main-flow changes.

## Overview

- Confirmation status: `confirmed_for_future_offline_simulation_design`
- Allowed use: `offline_simulation_design_input_only`
- Confirmed rows: 3
- Revision categories: liability, scenario_core, coverage_floor
- User confirmation recorded: True
- User confirmation text: 确认以上三条。
- May enter offline simulation design: True
- Implementation allowed: False
- Code patch authorized: False

## Confirmed Wording

### liability

- Confirmed wording: Preserve liability or consequence evidence only when the answer asserts penalties, liability exposure, enforcement consequences, damages, remedies, or compliance consequences. If the answer only identifies the applicable conduct rule, liability evidence is optional and must not displace operative-rule evidence.
- Must not mean: Do not force penalty, remedy, or consequence provisions into every final evidence set merely because a case is high-risk.
- Acceptance boundary: The row must name the asserted consequence that makes liability evidence necessary, or explicitly record that no liability evidence is required.
- Confirmed route: `future_offline_simulation_design_candidate`
- Source cases: pipl_data_export_conditions_001, risk_employee_data_export_001

### scenario_core

- Confirmed wording: Preserve scenario-core evidence only when a scenario fact changes the applicable legal requirement, such as cross-border transfer, automated decision, sensitive personal information, employee context, consumer context, or entrusted processing. A broad topic label is not enough.
- Must not mean: Do not preserve topical but non-operative materials simply because they share the same business scene or legal domain label.
- Acceptance boundary: The row must identify the legally material scenario fact and an acceptable substitute that covers the same legal requirement.
- Confirmed route: `future_offline_simulation_design_candidate`
- Source cases: pipl_data_export_conditions_001, risk_ai_medical_training_export_001, risk_employee_data_export_001, risk_employee_facial_001

### coverage_floor

- Confirmed wording: Apply the evidence coverage floor only to material issues actually asserted in the answer. For each asserted issue, retain at least one operative or procedural evidence item when such evidence is present in the candidate set; if no applicable evidence is present, record a coverage gap or manual-review signal instead of forcing unrelated evidence.
- Must not mean: Do not recreate score fusion or broad hybrid fallback by requiring every case to include every evidence class.
- Acceptance boundary: The row must be issue-conditioned and must include a stop condition for candidate sets that lack applicable evidence.
- Confirmed route: `future_offline_simulation_design_candidate`
- Source cases: pipl_data_export_conditions_001, risk_employee_data_export_001

## Boundaries

- Confirmed wording may be used only as future offline simulation design input.
- `implementation_allowed=false` and `code_patch_authorized=false` remain unchanged.
- This record does not implement runtime final evidence selection policy.
- It does not modify rerank, prompt, eval cases, fixtures, anchors, hidden seeds, risk supplement, term preservation, scenario registry, schema, importer, or dry-run contracts.
- It does not call backend services, Qdrant, LLMs, RAG, or full eval.

## Sources

- language_revision_closeout_draft: `tests\final_evidence_selection_policy_language_revision_closeout_draft_report.json`
