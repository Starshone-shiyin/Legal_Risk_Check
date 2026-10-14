# v0.4.8.8 Final Evidence Selection Policy Language Revision Worksheet

This worksheet prepares policy-language revision for the three confirmed rows that must be narrowed before offline simulation design. It does not record final wording, does not authorize runtime policy, and does not modify RAG, rerank, prompts, eval cases, fixtures, or rules.

## Overview

- Worksheet status: `ready_for_policy_language_revision_review`
- Allowed use: `policy_language_revision_worksheet_only`
- Revision rows: 3
- Revision categories: liability, scenario_core, coverage_floor
- Unique cases: 4
- Implementation allowed: False
- Code patch authorized: False

## Revision Rows

| Row | Policy | Priority | Revision focus | Simulation entry condition |
|---|---|---|---|---|
| `FES-POLICY-LANGUAGE-REVISION-001` | `liability` | `P0` | Separate liability or consequence evidence from operative-rule evidence. | A later simulator may test liability preservation only after the row states when liability evidence is required and when it is optional. |
| `FES-POLICY-LANGUAGE-REVISION-002` | `scenario_core` | `P1` | Narrow scenario-core preservation to legally essential scenario facts rather than broad scenario labels. | A later simulator may test scenario-core preservation only after the row defines legally material scenario facts and acceptable substitutes. |
| `FES-POLICY-LANGUAGE-REVISION-003` | `coverage_floor` | `P1` | Define a minimum evidence floor without making every case require every evidence class. | A later simulator may test coverage floor behavior only after the row defines issue-conditioned minimums and stop conditions. |

## Review Questions

### liability
- Wording risk: Language that forces liability evidence into every final set can over-select penalty or consequence provisions even when the legal question only needs an operative rule.
- Target boundary: Require liability evidence only when the answer asserts penalties, liability exposure, enforcement consequence, or remedy consequence.
- Questions:
  - Is the policy category legally necessary for the source cases?
  - Which words would over-preserve non-operative or unrelated evidence?
  - What explicit stop condition prevents broad fallback behavior?
  - What minimal source-case evidence is needed before a later simulator can test this row?

### scenario_core
- Wording risk: Broad scenario-core wording can preserve topical but non-operative materials and mask weak base retrieval.
- Target boundary: Tie scenario-core preservation to case facts that change the applicable legal requirement, such as cross-border transfer, automated decision, sensitive personal information, or employee/consumer context.
- Questions:
  - Is the policy category legally necessary for the source cases?
  - Which words would over-preserve non-operative or unrelated evidence?
  - What explicit stop condition prevents broad fallback behavior?
  - What minimal source-case evidence is needed before a later simulator can test this row?

### coverage_floor
- Wording risk: An overbroad coverage floor can re-create score fusion behavior by forcing unrelated evidence into the final set.
- Target boundary: Require coverage only for issue types that are actually present in the case and allow explicit no-applicable-evidence outcomes.
- Questions:
  - Is the policy category legally necessary for the source cases?
  - Which words would over-preserve non-operative or unrelated evidence?
  - What explicit stop condition prevents broad fallback behavior?
  - What minimal source-case evidence is needed before a later simulator can test this row?

## Simulation Dependency

- Accepted categories waiting for simulation design: primary, operative, procedural, definition_only, high_risk_manual_review
- Revision categories required first: liability, scenario_core, coverage_floor
- Simulation design should wait for revision closeout: True

## Boundaries

- This worksheet is for language review only.
- It does not finalize policy wording.
- `implementation_allowed=false` and `code_patch_authorized=false` must remain unchanged.
- It does not implement runtime policy, final evidence selection runtime, rerank, prompt, or eval case changes.
- It does not modify anchors, hidden seeds, risk supplement, term preservation, scenario registry, fixtures, schema, importer, or dry-run contracts.
- It does not call backend services, Qdrant, LLMs, RAG, or full eval.

## Sources

- policy_closeout_confirmed_record: `tests\final_evidence_selection_policy_closeout_confirmed_record_report.json`
