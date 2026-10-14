# v0.4.8.11 Final Evidence Selection Policy Offline Simulation Input Contract

This contract merges the five accepted policy categories and three confirmed language revisions into saved-report-only input for a future offline simulation. It does not run simulation and does not authorize runtime changes.

## Overview

- Contract status: `ready_for_saved_report_offline_simulation`
- Allowed use: `saved_report_offline_simulation_input_only`
- Contract rows: 8
- Policy categories: primary, operative, procedural, liability, scenario_core, definition_only, coverage_floor, high_risk_manual_review
- Simulation not run: True
- Implementation allowed: False

## Contract Rows

| Row | Category | Source | Wording status | Simulation input |
|---|---|---|---|---|
| `FES-OFFLINE-SIM-INPUT-001` | `primary` | `v0.4.8.7_confirmed_closeout_category` | `accepted_without_language_revision` | True |
| `FES-OFFLINE-SIM-INPUT-002` | `operative` | `v0.4.8.7_confirmed_closeout_category` | `accepted_without_language_revision` | True |
| `FES-OFFLINE-SIM-INPUT-003` | `procedural` | `v0.4.8.7_confirmed_closeout_category` | `accepted_without_language_revision` | True |
| `FES-OFFLINE-SIM-INPUT-004` | `liability` | `v0.4.8.10_confirmed_language_revision` | `confirmed_language_revision` | True |
| `FES-OFFLINE-SIM-INPUT-005` | `scenario_core` | `v0.4.8.10_confirmed_language_revision` | `confirmed_language_revision` | True |
| `FES-OFFLINE-SIM-INPUT-006` | `definition_only` | `v0.4.8.7_confirmed_closeout_category` | `accepted_without_language_revision` | True |
| `FES-OFFLINE-SIM-INPUT-007` | `coverage_floor` | `v0.4.8.10_confirmed_language_revision` | `confirmed_language_revision` | True |
| `FES-OFFLINE-SIM-INPUT-008` | `high_risk_manual_review` | `v0.4.8.7_confirmed_closeout_category` | `accepted_without_language_revision` | True |

## Boundaries

- This contract is input only for later saved-report offline simulation.
- It does not run simulation, full eval, RAG, Qdrant, or LLM calls.
- It does not modify `rag_query`, rerank, prompts, eval cases, fixtures, rules, schemas, or imports.
- `implementation_allowed=false` and `code_patch_authorized=false` remain fixed.
