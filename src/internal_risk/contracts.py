from __future__ import annotations


INTERNAL_RISK_WORKFLOW_VERSION = "0.1.0"
INTERNAL_RISK_DATA_SOURCE = "fixture_sample"

INTERNAL_RISK_ENDPOINTS = [
    "GET /internal-risk/dashboard",
    "GET /internal-risk/workflow",
    "POST /internal-risk/business-state/initialize",
    "POST /internal-risk/business-state/reset",
    "GET /internal-risk/business-state/audit",
    "POST /internal-risk/business-state/baseline/proposal",
    "POST /internal-risk/business-state/baseline/confirmation",
    "POST /internal-risk/business-state/baseline/cancel",
    "GET /internal-risk/workflow-templates",
    "POST /internal-risk/workflow-templates",
    "POST /internal-risk/workflow-templates/import",
    "POST /internal-risk/workflow-templates/{template_id}/versions",
    "GET /internal-risk/workflow-templates/{template_id}/versions/{version}",
    "GET /internal-risk/workflow-templates/{template_id}/audit",
    "GET /internal-risk/risks",
    "GET /internal-risk/events",
    "POST /internal-risk/events",
    "POST /internal-risk/events/{event_id}/assessment",
    "POST /internal-risk/events/{event_id}/assessment-jobs",
    "GET /internal-risk/assessment-jobs/{assessment_job_id}",
    "POST /internal-risk/assessment-jobs/{assessment_job_id}/retry",
    "PATCH /internal-risk/events/{event_id}/confirmation",
    "GET /internal-risk/gates",
    "PATCH /internal-risk/gates/{gate_id}/checks/{check_id}",
    "PATCH /internal-risk/gates/{gate_id}/decision",
    "GET /internal-risk/tasks",
    "PATCH /internal-risk/tasks/{task_id}",
    "POST /internal-risk/tasks/{task_id}/evidence",
    "GET /internal-risk/reviews",
    "PATCH /internal-risk/reviews/{review_id}",
    "PATCH /internal-risk/risks/{risk_id}/closure",
    "GET /internal-risk/gates/{gate_id}/blockers",
    "GET /internal-risk/risks/{risk_id}/closure-blockers",
]

RUNTIME_ACCESS_GUARDRAILS = {
    "rag": "not_called",
    "qdrant": "not_called",
    "llm": "not_called",
    "external_risk": "not_called",
}
