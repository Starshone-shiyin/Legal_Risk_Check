# v0.4.8.14 Final Evidence Selection Policy Adoption Decision Draft

This draft records suggested adoption routes for human confirmation. It is not a final decision and does not authorize runtime implementation.

## Overview

- Draft status: `pending_user_confirmation`
- Rows: 8
- Requires user confirmation: True
- Implementation allowed: False

## Draft Rows

| Row | Category | Suggested option |
|---|---|---|
| `FES-ADOPTION-DRAFT-001` | `primary` | `accept_for_future_runtime_design_after_separate_approval` |
| `FES-ADOPTION-DRAFT-002` | `operative` | `accept_for_future_runtime_design_after_separate_approval` |
| `FES-ADOPTION-DRAFT-003` | `procedural` | `accept_for_future_runtime_design_after_separate_approval` |
| `FES-ADOPTION-DRAFT-004` | `liability` | `accept_as_context_only_for_future_runtime_design_after_separate_approval` |
| `FES-ADOPTION-DRAFT-005` | `scenario_core` | `accept_as_grounding_floor_candidate_after_separate_approval` |
| `FES-ADOPTION-DRAFT-006` | `definition_only` | `accept_as_demotion_rule_candidate_after_separate_approval` |
| `FES-ADOPTION-DRAFT-007` | `coverage_floor` | `accept_as_manual_review_gate_candidate_after_separate_approval` |
| `FES-ADOPTION-DRAFT-008` | `high_risk_manual_review` | `accept_as_manual_review_routing_candidate_after_separate_approval` |

## Boundaries

- This draft requires explicit user confirmation before any later step treats it as a decision.
- It does not run eval, backend calls, RAG, Qdrant, or LLM calls.
- It does not modify retrieval, rerank, prompts, eval cases, fixtures, anchors, risk rules, or scenario registry.
- Any future runtime design still needs a separate approved implementation version.
