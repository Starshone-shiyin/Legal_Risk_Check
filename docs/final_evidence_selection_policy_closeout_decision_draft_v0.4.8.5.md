# v0.4.8.5 Final Evidence Selection Policy Closeout Decision Draft

This file is a user-confirmation draft for final evidence selection policy closeout. It converts the v0.4.8.4 closeout envelope into suggested choices for each policy row. It does not record formal human outcomes and does not authorize runtime policy, rerank, prompt, eval case, or RAG main-flow changes.

## Overview

- Draft status: `draft_pending_user_confirmation`
- Allowed use: `user_confirmation_draft_only`
- Draft rows: 8
- Unique cases: 5
- Requires user confirmation: True
- Next version recommendation: `v0.4.8.6 policy table human closeout confirmation record`
- Implementation allowed: False
- Formal human outcome recorded: False
- Draft is importable decision: False

## Input Contract

- `policy_closeout_envelope`: `tests\final_evidence_selection_policy_closeout_envelope_report.json` (version `0.4.8.4`)

## Decision Draft Rows

| Row | Policy | Category | Status | Suggested option | Next step |
|---|---|---|---|---|---|
| `FES-CLOSEOUT-DRAFT-001` | `FES-POLICY-DRAFT-001` | `primary` | `draft_pending_user_confirmation` | `accept_for_future_offline_simulation_design` | `eligible_for_future_offline_simulation_design_after_user_confirmation` |
| `FES-CLOSEOUT-DRAFT-002` | `FES-POLICY-DRAFT-002` | `operative` | `draft_pending_user_confirmation` | `accept_for_future_offline_simulation_design` | `eligible_for_future_offline_simulation_design_after_user_confirmation` |
| `FES-CLOSEOUT-DRAFT-003` | `FES-POLICY-DRAFT-003` | `procedural` | `draft_pending_user_confirmation` | `accept_for_future_offline_simulation_design` | `eligible_for_future_offline_simulation_design_after_user_confirmation` |
| `FES-CLOSEOUT-DRAFT-004` | `FES-POLICY-DRAFT-004` | `liability` | `draft_pending_user_confirmation` | `revise_policy_language_before_closeout` | `revise_policy_language_then_rebuild_closeout_materials` |
| `FES-CLOSEOUT-DRAFT-005` | `FES-POLICY-DRAFT-005` | `scenario_core` | `draft_pending_user_confirmation` | `revise_policy_language_before_closeout` | `revise_policy_language_then_rebuild_closeout_materials` |
| `FES-CLOSEOUT-DRAFT-006` | `FES-POLICY-DRAFT-006` | `definition_only` | `draft_pending_user_confirmation` | `accept_for_future_offline_simulation_design` | `eligible_for_future_offline_simulation_design_after_user_confirmation` |
| `FES-CLOSEOUT-DRAFT-007` | `FES-POLICY-DRAFT-007` | `coverage_floor` | `draft_pending_user_confirmation` | `revise_policy_language_before_closeout` | `revise_policy_language_then_rebuild_closeout_materials` |
| `FES-CLOSEOUT-DRAFT-008` | `FES-POLICY-DRAFT-008` | `high_risk_manual_review` | `draft_pending_user_confirmation` | `accept_for_future_offline_simulation_design` | `eligible_for_future_offline_simulation_design_after_user_confirmation` |

## Confirmation Questions

### FES-POLICY-DRAFT-001 - primary
- Suggested option: `accept_for_future_offline_simulation_design`
- Confirmation question: Confirm whether this policy row may advance to a later offline simulation design artifact.
- Required basis: Confirm the row expresses a real evidence-selection concern and does not authorize runtime adoption.

### FES-POLICY-DRAFT-002 - operative
- Suggested option: `accept_for_future_offline_simulation_design`
- Confirmation question: Confirm whether this policy row may advance to a later offline simulation design artifact.
- Required basis: Confirm the row expresses a real evidence-selection concern and does not authorize runtime adoption.

### FES-POLICY-DRAFT-003 - procedural
- Suggested option: `accept_for_future_offline_simulation_design`
- Confirmation question: Confirm whether this policy row may advance to a later offline simulation design artifact.
- Required basis: Confirm the row expresses a real evidence-selection concern and does not authorize runtime adoption.

### FES-POLICY-DRAFT-004 - liability
- Suggested option: `revise_policy_language_before_closeout`
- Confirmation question: Confirm whether this policy row needs wording or acceptance-criteria revision before closeout.
- Required basis: Confirm the row is directionally useful but the current wording is too broad, narrow, or ambiguous.

### FES-POLICY-DRAFT-005 - scenario_core
- Suggested option: `revise_policy_language_before_closeout`
- Confirmation question: Confirm whether this policy row needs wording or acceptance-criteria revision before closeout.
- Required basis: Confirm the row is directionally useful but the current wording is too broad, narrow, or ambiguous.

### FES-POLICY-DRAFT-006 - definition_only
- Suggested option: `accept_for_future_offline_simulation_design`
- Confirmation question: Confirm whether this policy row may advance to a later offline simulation design artifact.
- Required basis: Confirm the row expresses a real evidence-selection concern and does not authorize runtime adoption.

### FES-POLICY-DRAFT-007 - coverage_floor
- Suggested option: `revise_policy_language_before_closeout`
- Confirmation question: Confirm whether this policy row needs wording or acceptance-criteria revision before closeout.
- Required basis: Confirm the row is directionally useful but the current wording is too broad, narrow, or ambiguous.

### FES-POLICY-DRAFT-008 - high_risk_manual_review
- Suggested option: `accept_for_future_offline_simulation_design`
- Confirmation question: Confirm whether this policy row may advance to a later offline simulation design artifact.
- Required basis: Confirm the row expresses a real evidence-selection concern and does not authorize runtime adoption.

## Boundaries

- This draft does not capture a formal review outcome.
- `implementation_allowed=false` and `code_patch_authorized=false` must remain unchanged.
- It does not implement runtime policy, final evidence selection runtime, rerank, prompt, or eval case changes.
- It does not modify anchors, hidden seeds, risk supplement, term preservation, scenario registry, fixtures, schema, importer, or dry-run contracts.
- It does not call backend services, Qdrant, LLMs, RAG, or full eval.

## Sources

- policy_closeout_envelope: `tests\final_evidence_selection_policy_closeout_envelope_report.json`
