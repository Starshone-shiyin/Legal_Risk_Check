# v0.4.8.9 Final Evidence Selection Policy Language Revision Closeout Draft

This draft proposes narrowed wording for the three policy-language rows that still require user confirmation. It is not final policy wording, does not authorize implementation, and does not modify RAG, rerank, prompts, eval cases, fixtures, rules, or the main flow.

## Overview

- Draft status: `draft_pending_user_confirmation`
- Allowed use: `user_confirmation_draft_only`
- Draft rows: 3
- Revision categories: liability, scenario_core, coverage_floor
- Requires user confirmation: True
- Final policy wording recorded: False
- Implementation allowed: False
- Code patch authorized: False

## Suggested Wording Drafts

### liability

- Suggested wording: Preserve liability or consequence evidence only when the answer asserts penalties, liability exposure, enforcement consequences, damages, remedies, or compliance consequences. If the answer only identifies the applicable conduct rule, liability evidence is optional and must not displace operative-rule evidence.
- Must not mean: Do not force penalty, remedy, or consequence provisions into every final evidence set merely because a case is high-risk.
- Acceptance boundary: The row must name the asserted consequence that makes liability evidence necessary, or explicitly record that no liability evidence is required.
- Confirmation question: Confirm whether liability evidence should be required only when the answer expressly discusses penalties, liabilities, remedies, or other legal consequences.
- Post-confirmation route: `eligible_for_future_offline_simulation_design_after_user_confirmation`
- Source cases: pipl_data_export_conditions_001, risk_employee_data_export_001

### scenario_core

- Suggested wording: Preserve scenario-core evidence only when a scenario fact changes the applicable legal requirement, such as cross-border transfer, automated decision, sensitive personal information, employee context, consumer context, or entrusted processing. A broad topic label is not enough.
- Must not mean: Do not preserve topical but non-operative materials simply because they share the same business scene or legal domain label.
- Acceptance boundary: The row must identify the legally material scenario fact and an acceptable substitute that covers the same legal requirement.
- Confirmation question: Confirm whether scenario-core preservation should be limited to facts that change the applicable legal duty or rights analysis.
- Post-confirmation route: `eligible_for_future_offline_simulation_design_after_user_confirmation`
- Source cases: pipl_data_export_conditions_001, risk_ai_medical_training_export_001, risk_employee_data_export_001, risk_employee_facial_001

### coverage_floor

- Suggested wording: Apply the evidence coverage floor only to material issues actually asserted in the answer. For each asserted issue, retain at least one operative or procedural evidence item when such evidence is present in the candidate set; if no applicable evidence is present, record a coverage gap or manual-review signal instead of forcing unrelated evidence.
- Must not mean: Do not recreate score fusion or broad hybrid fallback by requiring every case to include every evidence class.
- Acceptance boundary: The row must be issue-conditioned and must include a stop condition for candidate sets that lack applicable evidence.
- Confirmation question: Confirm whether the coverage floor should be issue-conditioned and should prefer an explicit gap/manual-review signal over unrelated evidence.
- Post-confirmation route: `eligible_for_future_offline_simulation_design_after_user_confirmation`
- Source cases: pipl_data_export_conditions_001, risk_employee_data_export_001

## Confirmation Packet

- The suggested wording above is pending user confirmation.
- It is not importer-compatible and does not capture a formal review outcome.
- A later confirmation record may only be generated after explicit user confirmation or revision instructions.
- Offline simulation design remains blocked until this language closeout is confirmed.

## Boundaries

- This draft does not finalize policy wording.
- `implementation_allowed=false` and `code_patch_authorized=false` must remain unchanged.
- It does not implement runtime final evidence selection policy.
- It does not modify rerank, prompt, eval cases, fixtures, anchors, hidden seeds, risk supplement, term preservation, scenario registry, schema, importer, or dry-run contracts.
- It does not call backend services, Qdrant, LLMs, RAG, or full eval.

## Sources

- language_revision_worksheet: `tests\final_evidence_selection_policy_language_revision_worksheet_report.json`
