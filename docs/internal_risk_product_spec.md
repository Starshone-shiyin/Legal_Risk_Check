# Internal Risk Control Product Contract

## Purpose

This document defines the first internal risk-control surface for the project "识险智控——基于法律 RAG 的科创企业动态风控系统". It is deliberately a workflow contract, not a new legal-analysis service: the existing RAG/report output remains the source of legal reasoning, citations, confidence, and human-review recommendations.

The product turns a technology-company event into a traceable control loop:

```text
business event -> risk gate -> RAG-supported assessment -> remediation task -> human review -> closure and reuse
```

## Product Boundary

- Scope: AI and technology-company projects at the stages of data access, model training, release, commercialization, and overseas collaboration.
- Primary users: business owner, R&D/data owner, legal/compliance, risk-control owner, and reviewer.
- Current implementation: the main workspace at `web/website.html` includes an `internal` navigation view that reads the `/internal-risk/*` workflow API. `web/internal-risk-demo.html` remains a focused presentation artifact.
- Non-goals for this iteration: authentication, notification delivery, workflow automation, or automated gate/review approvals.
- Data boundary: every displayed record is `fixture_sample`; it must not be represented as an actual legal conclusion or company record. The workbench may advance remediation-task status through the audited `PATCH /internal-risk/tasks/{task_id}` endpoint. A reviewer may record a guarded decision through `PATCH /internal-risk/reviews/{review_id}` only when the target task is already `pending_review`; this is a human command, never an AI or automatic approval.

## Shared Enumerations

| Field | Values |
| --- | --- |
| `risk_level` | `low`, `medium`, `high`, `critical` |
| `gate_decision` | `approved`, `conditional_approval`, `rectification_required`, `suspended` |
| `task_status` | `not_started`, `in_progress`, `blocked`, `pending_review`, `verified` |
| `review_status` | `pending`, `approved`, `changes_requested`, `rejected` |
| `lifecycle_stage` | `project_initiation`, `data_access`, `model_training`, `product_launch`, `commercialization`, `cross_border` |

## Entities

### Risk Gate

`risk_gate` is the control point before a key business decision. A gate may not approve itself when `review_status` is `required` or its decision is `remediation_required` / `hold`.

```json
{
  "gate_id": "gate-model-training-001",
  "project_id": "proj-copilot-001",
  "stage": "model_training",
  "title": "模型训练前核验",
  "risk_level": "high",
  "decision": "rectification_required",
  "risk_ids": ["ir-data-001", "ir-ip-001"],
  "required_materials": ["数据授权证明", "开源组件清单"],
  "missing_materials": ["境外云服务安全义务说明"],
  "review_status": "pending",
  "owner": "数据治理负责人",
  "due_date": "2026-08-03"
}
```

### Risk Ledger Item

`risk_ledger_item` is the single source of truth for a continuing risk. In the current schema it is represented by `RiskItem`, linking `trigger_facts`, `evidence_refs`, `legal_query_seeds`, `missing_materials`, `task_ids`, and an optional `review_id`. `risk_id` should remain stable across dashboard, lifecycle, legal workspace, external signals, and supply-chain references, extending the existing product view-model pattern.

Required fields: `risk_id`, `company_id`, `project_id`, `title`, `risk_domain`, `risk_level`, `lifecycle_stage`, `status`, `trigger_facts`, `evidence_refs`, `missing_materials`, `task_ids`.

### Remediation Task

`remediation_task` represents an executable control action, not generic advice. A task should contain one owner, a due date, completion evidence, and a closure condition.

Required fields: `task_id`, `company_id`, `project_id`, `risk_id`, `title`, `owner`, `due_date`, `status`, `evidence_refs`, `requires_manual_review`, `updated_at`, `status_history`.

### Human Review

`human_review` is an auditable decision made after the RAG-supported assessment. The UI must separately show the AI/RAG suggestion, its cited evidence, the reviewer decision, and reviewer rationale.

Required fields: `review_id`, `company_id`, `target_type`, `target_id`, `status`, `reviewer`, `conclusion`, `reviewed_at`, `decision_history`. The UI-specific RAG suggestion and citations are derived from the linked `RiskItem` and report output; they are not duplicated as an approval record. For a remediation-task review, an approved decision changes the target task to `verified`; a returned or rejected decision reopens it as `in_progress`, and both records retain actor, timestamp and rationale.

## Integration Mapping

| Existing capability | Internal risk-control consumption |
| --- | --- |
| `/risk/analyze` | Risk fact summary, `risk_level`, categories, recommended actions, confidence, `needs_human_review` |
| `/risk/report` | Executive summary, findings, action plan, legal basis, evidence chain, review reasons |
| `product_risks` | Stable cross-module `risk_id` references and shared risk metadata |
| `lifecycle_risk` | Lifecycle stage and currently linked risk/evidence references |
| External risk / supply-chain modules | Event trigger or affected supplier/region reference; not an automatic approval decision |
| `/internal-risk/workflow` | Complete read model for a company: risks, gates, tasks, reviews, and guardrails |
| `/internal-risk/dashboard`, `/internal-risk/risks`, `/internal-risk/gates`, `/internal-risk/tasks`, `/internal-risk/reviews` | Read models for the four internal-workflow views and their management summary |
| `PATCH /internal-risk/reviews/{review_id}` | Human-only remediation decision command, with review and task audit events |

The current read model is available under `/internal-risk/*`. Do not overload the existing `/product/risks` fixture endpoint with mutable task or review state. Any future command endpoint should use a tenant-scoped persistence provider and record actor identity, transition time, and previous state.

## Risk Event Assessment

Business changes enter the workflow as a `risk_event`: the reporter records the trigger facts, lifecycle stage, risk domain and material references. The system then invokes the existing legal RAG report capability once and stores the resulting report, evidence chain, review reasons, filters and generation time as an immutable assessment snapshot.

The snapshot is an aid to human judgment, never an approval. Only an authorized reviewer may confirm or reject an assessed event. Confirmation creates one new `risk_item` in the internal ledger, carrying the event facts and referenced materials; it does not create a remediation task, change a gate, close a risk, or approve a business action. A rejected event remains auditable but does not enter the ledger.

Available commands are `POST /internal-risk/events`, `POST /internal-risk/events/{event_id}/assessment`, and `PATCH /internal-risk/events/{event_id}/confirmation`. The assessment endpoint accepts only retrieval filters already supported by the risk report and ignores any other caller input.

## Gate Rules

1. A high or critical risk with missing required evidence results in `rectification_required` or `suspended`.
2. A gate linked to a `pending` review cannot reach `approved` before that review is recorded as `approved`.
3. A remediation task may enter `pending_review` only after the required evidence is attached.
4. Closing a risk requires every blocking task to be `verified` and the required review to be `approved`.
5. A review may use `changes_requested` or `rejected` to reopen remediation or return the gate to `rectification_required`; all transitions retain timestamps and actor identity in production.
6. A gate may be recorded as `approved` only by a human reviewer after all its checks are complete, every linked remediation task is `verified`, and every required task review is `approved`.
7. Closing a risk requires all of its remediation tasks and required reviews to be complete, and every linked gate and gate review to be formally `approved`. `conditional_approval` never closes a risk.

## Gate Decision And Risk Closure

The workbench exposes a human-only gate decision command and a separate risk-closure command. Both record reviewer, time, conclusion and an audit event. A decision of `rectification_required` or `suspended` remains available when a project needs to be returned or paused; an approval request is rejected with a concrete blocker list when prerequisites are incomplete.

RAG reports, uploaded PDFs, parser output, external signals and task evidence provide supporting context only. None of them can independently approve a gate or close a risk.

## Presentation Coverage

The integrated workbench and focused presentation page contain three competition-relevant sample scenarios:

1. Customer data used for model training on an overseas cloud service.
2. AI SaaS commercialized through a third-party model API without settled data responsibility.
3. A departing algorithm engineer with access to model weights, source code, and an unreviewed open-source component.

These demonstrate data/model governance, intellectual-property protection, commercialization contracts, and internal accountability without claiming a real-time legal assessment.

## Evidence Attachment

Each remediation task has a compact evidence package. Users may upload a PDF directly from the task, follow its MineU parsing status, preview the parsed Markdown, and download either the parsed copy or original PDF. The upload is immediately linked to the task through the document `task_id`, while external-system material numbers may still be recorded as non-file evidence.

An evidence link is an audit reference, not a legal conclusion: parsing, AI/RAG, and external signals cannot automatically approve a task or gate. A task cannot enter `pending_review` without at least one evidence reference, and a PDF referenced by a remediation task cannot be deleted through the document API. This demonstration version does not yet provide production controls such as role-based permissions, malware scanning, version hashes, retention policies, or tenant isolation; these are required before a real deployment.
