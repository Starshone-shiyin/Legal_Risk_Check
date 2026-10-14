from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from src.internal_risk.contracts import (
    INTERNAL_RISK_DATA_SOURCE,
    INTERNAL_RISK_WORKFLOW_VERSION,
    RUNTIME_ACCESS_GUARDRAILS,
)


RiskLevel = Literal["low", "medium", "high", "critical"]
RiskDomain = Literal[
    "data_model_governance",
    "technology_ip",
    "product_commercialization",
    "cross_border_supply_chain",
    "corporate_finance_governance",
]
LifecycleStage = Literal[
    "establishment",
    "research_and_development",
    "market_access",
    "market_expansion",
    "strategic_adjustment",
    "project_initiation",
    "data_access",
    "model_training",
    "product_launch",
    "commercialization",
    "financing",
    "scale_expansion",
    "exit",
    "cross_border",
]
RiskItemStatus = Literal["open", "mitigating", "closed"]
RiskEventStatus = Literal["draft", "assessed", "confirmed", "rejected"]
RiskEventDecision = Literal["confirmed", "rejected"]
RiskGateDecision = Literal[
    "approved",
    "conditional_approval",
    "rectification_required",
    "suspended",
]
TaskStatus = Literal["not_started", "in_progress", "blocked", "pending_review", "verified"]
ManualReviewStatus = Literal["pending", "approved", "changes_requested", "rejected"]
ReviewTargetType = Literal["risk_item", "risk_gate", "remediation_task"]
SuggestionStatus = Literal["pending", "adopted", "dismissed"]
ReminderType = Literal["missing_material", "due_soon", "overdue", "blocked"]
ReminderStatus = Literal["active", "acknowledged"]
RiskAcceptanceStatus = Literal["pending_approval", "accepted", "expired"]
RiskAssessmentJobStatus = Literal["queued", "running", "completed", "failed"]
RiskAssessmentJobStage = Literal[
    "accepted",
    "material_loading",
    "rag_assessment",
    "snapshot_persisted",
    "failed",
]


class InternalRiskResponseMeta(BaseModel):
    contract_version: str = INTERNAL_RISK_WORKFLOW_VERSION
    fixture_version: str = INTERNAL_RISK_WORKFLOW_VERSION
    data_source: Literal["fixture_sample"] = INTERNAL_RISK_DATA_SOURCE
    runtime_data_access: dict[str, str] = Field(default_factory=lambda: dict(RUNTIME_ACCESS_GUARDRAILS))


class EnterpriseCompanyProfile(BaseModel):
    """Business identity kept with a workflow; it never contains runtime credentials."""

    company_name: str = Field(min_length=2, max_length=160)
    industry: str = Field(min_length=2, max_length=120)
    business_model: Literal["to_b", "to_c", "mixed"] = "to_b"
    lifecycle_stages: list[LifecycleStage] = Field(default_factory=list, max_length=20)


class BusinessStateAuditRecord(BaseModel):
    audit_id: str
    action: Literal["initialized", "reset", "baseline_proposed", "baseline_registered", "baseline_cancelled"]
    company_id: str
    actor_id: str
    occurred_at: datetime
    baseline_id: str
    previous_state_sha256: str | None = None
    resulting_state_sha256: str
    reason: str | None = None


WorkflowTemplateRole = Literal[
    "risk_viewer", "risk_operator", "risk_reviewer", "risk_decision_maker",
]


class WorkflowTemplateGate(BaseModel):
    """A portable gate definition.  It contains no tenant data or credentials."""

    key: str = Field(pattern=r"^[a-z][a-z0-9_-]{1,62}$")
    title: str = Field(min_length=2, max_length=160)
    lifecycle_stage: LifecycleStage
    owner_role: WorkflowTemplateRole = "risk_reviewer"
    checks: list[str] = Field(min_length=1, max_length=30)
    decision: RiskGateDecision = "rectification_required"

    @model_validator(mode="after")
    def checks_are_distinct(self) -> "WorkflowTemplateGate":
        normalized = [item.strip() for item in self.checks if item.strip()]
        if len(normalized) != len(self.checks) or len(set(normalized)) != len(normalized):
            raise ValueError("template gate checks must be non-empty and unique")
        self.checks = normalized
        return self


class WorkflowTemplate(BaseModel):
    template_id: str
    company_id: str
    name: str
    description: str | None = None
    version: int = Field(ge=1)
    gates: list[WorkflowTemplateGate] = Field(min_length=1, max_length=50)
    created_by: str
    created_at: datetime
    change_note: str | None = None
    imported: bool = False
    content_sha256: str

    @model_validator(mode="after")
    def gate_keys_are_distinct(self) -> "WorkflowTemplate":
        keys = [gate.key for gate in self.gates]
        if len(keys) != len(set(keys)):
            raise ValueError("template gate keys must be unique")
        return self


class WorkflowTemplateBinding(BaseModel):
    template_id: str
    version: int
    name: str
    content_sha256: str
    applied_by: str
    applied_at: datetime


class WorkflowTemplateAuditRecord(BaseModel):
    audit_id: str
    company_id: str
    template_id: str
    version: int
    action: Literal["created", "imported", "version_created"]
    actor_id: str
    occurred_at: datetime
    content_sha256: str
    change_note: str | None = None


class LegacyBaselineRegistration(BaseModel):
    registration_id: str
    company_id: str
    baseline_id: str
    status: Literal["pending_confirmation", "registered", "cancelled"]
    proposed_by: str
    proposed_at: datetime
    confirmed_by: str | None = None
    confirmed_at: datetime | None = None
    proposed_state_sha256: str
    resulting_state_sha256: str | None = None
    reason: str
    cancelled_by: str | None = None
    cancelled_at: datetime | None = None
    cancellation_reason: str | None = None


class WorkflowBlocker(BaseModel):
    code: str
    message: str
    target_type: Literal["risk_gate", "risk_item", "remediation_task", "manual_review", "gate_check"]
    target_id: str
    remediation: str | None = None


class RiskItem(BaseModel):
    risk_id: str
    company_id: str
    project_id: str
    title: str
    lifecycle_stage: LifecycleStage
    risk_domain: RiskDomain
    risk_level: RiskLevel
    status: RiskItemStatus = "open"
    trigger_facts: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    legal_query_seeds: list[str] = Field(default_factory=list)
    missing_materials: list[str] = Field(default_factory=list)
    task_ids: list[str] = Field(default_factory=list)
    review_id: str | None = None
    origin: Literal["manual", "external_signal"] = "manual"
    external_intake_id: str | None = None
    matched_object_ids: list[str] = Field(default_factory=list)
    signal_snapshot: dict[str, Any] | None = None
    updated_at: datetime | None = None
    status_history: list["RiskItemStatusEvent"] = Field(default_factory=list)


class RiskItemStatusEvent(BaseModel):
    status: RiskItemStatus
    changed_at: datetime
    changed_by: str
    note: str


class RiskAssessmentSnapshot(BaseModel):
    """Immutable RAG report retained as context for a human event decision."""

    snapshot_id: str
    generated_at: datetime
    scenario: str
    report: dict[str, Any] = Field(default_factory=dict)
    input_filters: dict[str, Any] = Field(default_factory=dict)
    material_sources: list[dict[str, Any]] = Field(default_factory=list)
    processing_metrics: dict[str, Any] = Field(default_factory=dict)


class RiskAssessmentJobAuditEvent(BaseModel):
    """Append-only status receipt for an asynchronous material/RAG assessment."""

    stage: RiskAssessmentJobStage
    occurred_at: datetime
    detail: str


class RiskAssessmentJob(BaseModel):
    """Tenant-scoped, queryable assessment work item.

    The result remains on the event's immutable assessment snapshot.  This job
    records scheduling and execution history without duplicating source text.
    """

    assessment_job_id: str
    company_id: str
    event_id: str
    status: RiskAssessmentJobStatus = "queued"
    stage: RiskAssessmentJobStage = "accepted"
    input_filters: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    assessment_snapshot_id: str | None = None
    result_sha256: str | None = None
    failure_code: str | None = None
    failure_message: str | None = None
    retry_count: int = Field(default=0, ge=0, le=2)
    audit_trail: list[RiskAssessmentJobAuditEvent] = Field(default_factory=list)


class RiskEventConfirmation(BaseModel):
    decision: RiskEventDecision
    reviewer: str
    conclusion: str
    decided_at: datetime


class RiskEvent(BaseModel):
    event_id: str
    company_id: str
    project_id: str
    title: str
    description: str
    lifecycle_stage: LifecycleStage
    risk_domain: RiskDomain
    occurred_at: datetime
    reported_by: str
    source_refs: list[str] = Field(default_factory=list)
    document_task_ids: list[str] = Field(default_factory=list)
    origin: Literal["manual", "external_signal"] = "manual"
    external_intake_id: str | None = None
    matched_object_ids: list[str] = Field(default_factory=list)
    signal_snapshot: dict[str, Any] | None = None
    status: RiskEventStatus = "draft"
    created_at: datetime
    updated_at: datetime
    assessment_snapshot: RiskAssessmentSnapshot | None = None
    confirmation: RiskEventConfirmation | None = None
    confirmed_risk_id: str | None = None


class RiskGateCheck(BaseModel):
    check_id: str
    title: str
    status: Literal["passed", "missing", "not_applicable"] = "missing"
    evidence_refs: list[str] = Field(default_factory=list)
    evidence_history: list[dict[str, Any]] = Field(default_factory=list)


class RiskGateDecisionEvent(BaseModel):
    decision: RiskGateDecision
    decided_at: datetime
    reviewer: str
    conclusion: str


class RiskGate(BaseModel):
    gate_id: str
    company_id: str
    project_id: str
    title: str
    lifecycle_stage: LifecycleStage
    decision: RiskGateDecision
    owner: str
    risk_item_ids: list[str] = Field(default_factory=list)
    checks: list[RiskGateCheck] = Field(default_factory=list)
    review_id: str | None = None
    updated_at: datetime | None = None
    decision_history: list[RiskGateDecisionEvent] = Field(default_factory=list)


class RemediationTaskStatusEvent(BaseModel):
    status: TaskStatus
    changed_at: datetime
    changed_by: str
    note: str | None = None


class RemediationTask(BaseModel):
    task_id: str
    company_id: str
    project_id: str
    risk_id: str
    title: str
    owner: str
    due_date: str
    status: TaskStatus = "not_started"
    evidence_refs: list[str] = Field(default_factory=list)
    requires_manual_review: bool = True
    review_id: str | None = None
    updated_at: datetime
    status_history: list[RemediationTaskStatusEvent] = Field(default_factory=list)


class EvidenceSnapshot(BaseModel):
    evidence_refs: list[str] = Field(default_factory=list)
    evidence_hash: str
    submitted_by: str
    submitted_at: datetime


class RemediationSuggestion(BaseModel):
    suggestion_id: str
    company_id: str
    risk_id: str
    project_id: str
    title: str
    suggested_action: str
    suggested_owner_role: str
    suggested_due_date: date
    missing_materials: list[str] = Field(default_factory=list)
    basis: list[str] = Field(default_factory=list)
    rule_version: str = "management-assistance-v1"
    generated_at: datetime
    status: SuggestionStatus = "pending"
    adopted_by: str | None = None
    adopted_at: datetime | None = None
    task_id: str | None = None


class ReminderRecord(BaseModel):
    reminder_id: str
    company_id: str
    target_type: Literal["risk_item", "remediation_task"]
    target_id: str
    reminder_type: ReminderType
    title: str
    detail: str
    rule_version: str = "management-assistance-v1"
    triggered_at: datetime
    idempotency_key: str
    status: ReminderStatus = "active"
    acknowledged_by: str | None = None
    acknowledged_at: datetime | None = None


class RiskAcceptance(BaseModel):
    acceptance_id: str
    company_id: str
    risk_id: str
    decision_maker: str
    decision_role: Literal["risk_owner", "executive_sponsor"]
    rationale: str
    compensating_controls: list[str] = Field(default_factory=list)
    expires_on: date
    review_on: date
    status: RiskAcceptanceStatus = "pending_approval"
    approved_by: str | None = None
    approved_at: datetime | None = None
    created_at: datetime


class ManualReview(BaseModel):
    review_id: str
    company_id: str
    target_type: ReviewTargetType
    target_id: str
    status: ManualReviewStatus = "pending"
    reviewer: str | None = None
    conclusion: str | None = None
    reviewed_at: datetime | None = None
    decision_history: list["ManualReviewDecisionEvent"] = Field(default_factory=list)
    evidence_snapshot: EvidenceSnapshot | None = None


class ManualReviewDecisionEvent(BaseModel):
    status: Literal["approved", "changes_requested", "rejected"]
    changed_at: datetime
    reviewer: str
    conclusion: str


class InternalRiskWorkflow(BaseModel):
    company_id: str
    as_of: str
    company_profile: EnterpriseCompanyProfile | None = None
    workflow_template: WorkflowTemplateBinding | None = None
    risk_items: list[RiskItem] = Field(default_factory=list)
    risk_events: list[RiskEvent] = Field(default_factory=list)
    assessment_jobs: list[RiskAssessmentJob] = Field(default_factory=list)
    gates: list[RiskGate] = Field(default_factory=list)
    remediation_tasks: list[RemediationTask] = Field(default_factory=list)
    manual_reviews: list[ManualReview] = Field(default_factory=list)
    remediation_suggestions: list[RemediationSuggestion] = Field(default_factory=list)
    reminders: list[ReminderRecord] = Field(default_factory=list)
    risk_acceptances: list[RiskAcceptance] = Field(default_factory=list)
    guardrails: list[str] = Field(default_factory=list)


class TaskStatusUpdate(BaseModel):
    status: TaskStatus
    changed_by: str = Field(default="system", min_length=1, max_length=80)
    note: str | None = Field(default=None, max_length=1000)
    evidence_refs: list[str] | None = None


class RiskEventCreate(BaseModel):
    project_id: str = Field(default="project-medical-copilot", min_length=1, max_length=120)
    title: str = Field(min_length=2, max_length=160)
    description: str = Field(min_length=10, max_length=4000)
    lifecycle_stage: LifecycleStage
    risk_domain: RiskDomain
    occurred_at: datetime
    reported_by: str = Field(min_length=1, max_length=80)
    source_refs: list[str] = Field(default_factory=list, max_length=20)
    document_task_ids: list[str] = Field(default_factory=list, max_length=3)
    origin: Literal["manual", "external_signal"] = "manual"
    external_intake_id: str | None = Field(default=None, max_length=120)
    matched_object_ids: list[str] = Field(default_factory=list, max_length=40)
    signal_snapshot: dict[str, Any] | None = None


class BusinessStateInitializeRequest(BaseModel):
    """Creates an isolated, empty workflow for a signed enterprise actor."""

    company_name: str = Field(min_length=2, max_length=160)
    industry: str = Field(default="半导体设备上游材料", min_length=2, max_length=120)
    business_model: Literal["to_b", "to_c", "mixed"] = "to_b"
    lifecycle_stages: list[LifecycleStage] = Field(
        default_factory=lambda: [
            "establishment",
            "research_and_development",
            "market_access",
            "commercialization",
            "financing",
            "scale_expansion",
            "strategic_adjustment",
        ],
        min_length=1,
        max_length=20,
    )
    as_of: datetime | None = None
    reason: str | None = Field(default=None, max_length=1000)
    workflow_template_id: str | None = Field(default=None, min_length=2, max_length=80)
    workflow_template_version: int | None = Field(default=None, ge=1)


class BusinessStateResetRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=1000)


class LegacyBaselineProposalRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=1000)


class LegacyBaselineConfirmationRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=1000)


class LegacyBaselineCancelRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=1000)


class WorkflowTemplateCreateRequest(BaseModel):
    template_id: str | None = Field(default=None, pattern=r"^[a-z][a-z0-9_-]{1,62}$")
    name: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    gates: list[WorkflowTemplateGate] = Field(min_length=1, max_length=50)
    change_note: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def gate_keys_are_distinct(self) -> "WorkflowTemplateCreateRequest":
        keys = [gate.key for gate in self.gates]
        if len(keys) != len(set(keys)):
            raise ValueError("template gate keys must be unique")
        return self


class WorkflowTemplateVersionCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    gates: list[WorkflowTemplateGate] = Field(min_length=1, max_length=50)
    change_note: str = Field(min_length=1, max_length=1000)


class WorkflowTemplateImportRequest(BaseModel):
    """JSON import payload; imported ids are namespaced by the receiving enterprise."""

    template_id: str | None = Field(default=None, pattern=r"^[a-z][a-z0-9_-]{1,62}$")
    name: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    gates: list[WorkflowTemplateGate] = Field(min_length=1, max_length=50)
    source_version: int | None = Field(default=None, ge=1)
    change_note: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def gate_keys_are_distinct(self) -> "WorkflowTemplateImportRequest":
        keys = [gate.key for gate in self.gates]
        if len(keys) != len(set(keys)):
            raise ValueError("template gate keys must be unique")
        return self


class BusinessStateAuditResponse(BaseModel):
    status: Literal["ok"] = "ok"
    data: BusinessStateAuditRecord
    meta: InternalRiskResponseMeta = Field(default_factory=InternalRiskResponseMeta)


class BusinessStateAuditListResponse(BaseModel):
    status: Literal["ok"] = "ok"
    items: list[BusinessStateAuditRecord] = Field(default_factory=list)
    meta: InternalRiskResponseMeta = Field(default_factory=InternalRiskResponseMeta)


class LegacyBaselineRegistrationResponse(BaseModel):
    status: Literal["ok"] = "ok"
    data: LegacyBaselineRegistration
    meta: InternalRiskResponseMeta = Field(default_factory=InternalRiskResponseMeta)


class WorkflowTemplateResponse(BaseModel):
    status: Literal["ok"] = "ok"
    data: WorkflowTemplate
    meta: InternalRiskResponseMeta = Field(default_factory=InternalRiskResponseMeta)


class WorkflowTemplateListResponse(BaseModel):
    status: Literal["ok"] = "ok"
    items: list[WorkflowTemplate] = Field(default_factory=list)
    meta: InternalRiskResponseMeta = Field(default_factory=InternalRiskResponseMeta)


class WorkflowTemplateAuditListResponse(BaseModel):
    status: Literal["ok"] = "ok"
    items: list[WorkflowTemplateAuditRecord] = Field(default_factory=list)
    meta: InternalRiskResponseMeta = Field(default_factory=InternalRiskResponseMeta)


class WorkflowBlockerListResponse(BaseModel):
    status: Literal["ok"] = "ok"
    items: list[WorkflowBlocker] = Field(default_factory=list)
    meta: InternalRiskResponseMeta = Field(default_factory=InternalRiskResponseMeta)


class RiskEventAssessmentRequest(BaseModel):
    input_filters: dict[str, Any] = Field(default_factory=dict)


class RiskEventAssessmentJobResponse(BaseModel):
    status: Literal["accepted"] = "accepted"
    data: RiskAssessmentJob
    meta: InternalRiskResponseMeta = Field(default_factory=InternalRiskResponseMeta)


class RiskAssessmentJobResponse(BaseModel):
    status: Literal["ok"] = "ok"
    data: RiskAssessmentJob
    meta: InternalRiskResponseMeta = Field(default_factory=InternalRiskResponseMeta)


class RiskEventConfirmationUpdate(BaseModel):
    decision: RiskEventDecision
    reviewer: str = Field(min_length=1, max_length=80)
    conclusion: str = Field(min_length=1, max_length=1000)


class GateDecisionUpdate(BaseModel):
    decision: RiskGateDecision
    reviewer: str = Field(min_length=1, max_length=80)
    conclusion: str = Field(min_length=1, max_length=1000)


class GateCheckUpdate(BaseModel):
    status: Literal["passed", "missing", "not_applicable"]
    evidence_refs: list[str] = Field(default_factory=list, max_length=30)
    note: str = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def passed_check_requires_evidence(self) -> "GateCheckUpdate":
        """Do not let a completed gate check bypass the evidence control."""
        self.evidence_refs = list(dict.fromkeys(
            reference.strip() for reference in self.evidence_refs if reference.strip()
        ))
        if self.status == "passed" and not self.evidence_refs:
            raise ValueError("a passed gate check requires at least one evidence reference")
        return self


class RiskClosureUpdate(BaseModel):
    reviewer: str = Field(min_length=1, max_length=80)
    conclusion: str = Field(min_length=1, max_length=1000)


class TaskEvidenceUpdate(BaseModel):
    evidence_refs: list[str] = Field(min_length=1, max_length=20)
    changed_by: str = Field(default="system", min_length=1, max_length=80)
    note: str | None = Field(default=None, max_length=1000)


class SuggestionAdoptionRequest(BaseModel):
    owner: str = Field(min_length=1, max_length=80)
    adopted_by: str = Field(min_length=1, max_length=80)
    due_date: date | None = None


class ReminderAcknowledgementRequest(BaseModel):
    acknowledged_by: str = Field(min_length=1, max_length=80)


class RiskAcceptanceCreate(BaseModel):
    decision_maker: str = Field(min_length=1, max_length=80)
    decision_role: Literal["risk_owner", "executive_sponsor"]
    rationale: str = Field(min_length=1, max_length=1000)
    compensating_controls: list[str] = Field(min_length=1, max_length=20)
    expires_on: date
    review_on: date


class RiskAcceptanceApprovalRequest(BaseModel):
    approved_by: str = Field(min_length=1, max_length=80)


class ManualReviewDecisionUpdate(BaseModel):
    status: Literal["approved", "changes_requested", "rejected"]
    reviewer: str = Field(min_length=1, max_length=80)
    conclusion: str = Field(min_length=1, max_length=1000)


class InternalRiskWorkflowResponse(BaseModel):
    status: Literal["ok"] = "ok"
    data: InternalRiskWorkflow
    meta: InternalRiskResponseMeta = Field(default_factory=InternalRiskResponseMeta)


class RiskItemListResponse(BaseModel):
    status: Literal["ok"] = "ok"
    items: list[RiskItem] = Field(default_factory=list)
    meta: InternalRiskResponseMeta = Field(default_factory=InternalRiskResponseMeta)


class RiskEventListResponse(BaseModel):
    status: Literal["ok"] = "ok"
    items: list[RiskEvent] = Field(default_factory=list)
    meta: InternalRiskResponseMeta = Field(default_factory=InternalRiskResponseMeta)


class RiskEventResponse(BaseModel):
    status: Literal["ok"] = "ok"
    data: RiskEvent
    meta: InternalRiskResponseMeta = Field(default_factory=InternalRiskResponseMeta)


class RiskGateListResponse(BaseModel):
    status: Literal["ok"] = "ok"
    items: list[RiskGate] = Field(default_factory=list)
    meta: InternalRiskResponseMeta = Field(default_factory=InternalRiskResponseMeta)


class RiskGateResponse(BaseModel):
    status: Literal["ok"] = "ok"
    data: RiskGate
    meta: InternalRiskResponseMeta = Field(default_factory=InternalRiskResponseMeta)


class RiskItemResponse(BaseModel):
    status: Literal["ok"] = "ok"
    data: RiskItem
    meta: InternalRiskResponseMeta = Field(default_factory=InternalRiskResponseMeta)


class RemediationTaskListResponse(BaseModel):
    status: Literal["ok"] = "ok"
    items: list[RemediationTask] = Field(default_factory=list)
    meta: InternalRiskResponseMeta = Field(default_factory=InternalRiskResponseMeta)


class ManualReviewListResponse(BaseModel):
    status: Literal["ok"] = "ok"
    items: list[ManualReview] = Field(default_factory=list)
    meta: InternalRiskResponseMeta = Field(default_factory=InternalRiskResponseMeta)


class RemediationTaskResponse(BaseModel):
    status: Literal["ok"] = "ok"
    data: RemediationTask
    meta: InternalRiskResponseMeta = Field(default_factory=InternalRiskResponseMeta)


class ManualReviewResponse(BaseModel):
    status: Literal["ok"] = "ok"
    data: ManualReview
    meta: InternalRiskResponseMeta = Field(default_factory=InternalRiskResponseMeta)


class ManagementAssistanceResponse(BaseModel):
    status: Literal["ok"] = "ok"
    suggestions: list[RemediationSuggestion] = Field(default_factory=list)
    reminders: list[ReminderRecord] = Field(default_factory=list)
    meta: InternalRiskResponseMeta = Field(default_factory=InternalRiskResponseMeta)


class RemediationSuggestionResponse(BaseModel):
    status: Literal["ok"] = "ok"
    data: RemediationSuggestion
    meta: InternalRiskResponseMeta = Field(default_factory=InternalRiskResponseMeta)


class ReminderResponse(BaseModel):
    status: Literal["ok"] = "ok"
    data: ReminderRecord
    meta: InternalRiskResponseMeta = Field(default_factory=InternalRiskResponseMeta)


class RiskAcceptanceResponse(BaseModel):
    status: Literal["ok"] = "ok"
    data: RiskAcceptance
    meta: InternalRiskResponseMeta = Field(default_factory=InternalRiskResponseMeta)
