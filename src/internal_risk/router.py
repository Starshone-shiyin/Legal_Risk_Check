from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import JSONResponse

from src.internal_risk.schemas import (
    BusinessStateAuditResponse,
    BusinessStateAuditListResponse,
    BusinessStateInitializeRequest,
    BusinessStateResetRequest,
    LegacyBaselineConfirmationRequest,
    LegacyBaselineCancelRequest,
    LegacyBaselineProposalRequest,
    LegacyBaselineRegistrationResponse,
    InternalRiskWorkflowResponse,
    ManagementAssistanceResponse,
    GateDecisionUpdate,
    GateCheckUpdate,
    ManualReviewListResponse,
    ManualReviewDecisionUpdate,
    ManualReviewResponse,
    ReminderAcknowledgementRequest,
    ReminderResponse,
    RemediationTaskListResponse,
    RemediationTaskResponse,
    RiskGateListResponse,
    RiskGateResponse,
    RiskEventAssessmentRequest,
    RiskEventAssessmentJobResponse,
    RiskAssessmentJobResponse,
    RiskEventConfirmationUpdate,
    RiskEventCreate,
    RiskEventListResponse,
    RiskEventResponse,
    RiskItemListResponse,
    RiskItemResponse,
    RiskAcceptanceApprovalRequest,
    RiskAcceptanceCreate,
    RiskAcceptanceResponse,
    RiskClosureUpdate,
    WorkflowBlockerListResponse,
    WorkflowTemplateCreateRequest,
    WorkflowTemplateAuditListResponse,
    WorkflowTemplateImportRequest,
    WorkflowTemplateListResponse,
    WorkflowTemplateResponse,
    WorkflowTemplateVersionCreateRequest,
    TaskEvidenceUpdate,
    TaskStatusUpdate,
    RemediationSuggestionResponse,
    SuggestionAdoptionRequest,
)
from src.internal_risk.service import (
    InternalRiskDataError,
    InternalRiskWorkflowService,
    RiskWorkflowNotFoundError,
    RiskWorkflowStateError,
)
from src.core.enterprise_access import EnterpriseActor, require_company, require_enterprise_actor, require_role


router = APIRouter(prefix="/internal-risk", tags=["internal-risk"])
service = InternalRiskWorkflowService()


def _actor_name(actor: EnterpriseActor) -> str:
    return actor.actor_id


def _target_company(target: object, actor: EnterpriseActor) -> None:
    if getattr(target, "company_id", None) != actor.company_id:
        raise RiskWorkflowNotFoundError("enterprise record not found")


def _error_response(status_code: int, code: str, message: str, blockers: list | None = None) -> JSONResponse:
    error = {"code": code, "message": message}
    if blockers:
        error["blockers"] = [item.model_dump(mode="json") if hasattr(item, "model_dump") else item for item in blockers]
    return JSONResponse(status_code=status_code, content={"error": error})


def _service_error_response(error: Exception) -> JSONResponse:
    if isinstance(error, RiskWorkflowNotFoundError):
        return _error_response(404, "INTERNAL_RISK_NOT_FOUND", str(error))
    if isinstance(error, RiskWorkflowStateError):
        return _error_response(409, "INTERNAL_RISK_INVALID_STATE", str(error), error.blockers)
    return _error_response(503, "INTERNAL_RISK_DATA_UNAVAILABLE", str(error))


@router.get("/dashboard", response_model=InternalRiskWorkflowResponse)
async def dashboard(company_id: str | None = None, as_of: str | None = None, actor: EnterpriseActor = Depends(require_enterprise_actor)):
    try:
        return InternalRiskWorkflowResponse(data=service.dashboard(company_id=require_company(actor, company_id), as_of=as_of))
    except InternalRiskDataError as exc:
        return _service_error_response(exc)


@router.get("/workflow", response_model=InternalRiskWorkflowResponse)
async def workflow(company_id: str | None = None, as_of: str | None = None, actor: EnterpriseActor = Depends(require_enterprise_actor)):
    try:
        return InternalRiskWorkflowResponse(data=service.workflow(company_id=require_company(actor, company_id), as_of=as_of))
    except InternalRiskDataError as exc:
        return _service_error_response(exc)


@router.post("/business-state/initialize", response_model=BusinessStateAuditResponse, status_code=201)
async def initialize_business_state(payload: BusinessStateInitializeRequest, actor: EnterpriseActor = Depends(require_enterprise_actor)):
    """Initialize a company-scoped test/business workflow without touching runtime configuration."""
    try:
        require_role(actor, "risk_decision_maker")
        return BusinessStateAuditResponse(data=service.initialize_business_state(actor.company_id, payload, _actor_name(actor)))
    except (RiskWorkflowStateError, InternalRiskDataError) as exc:
        return _service_error_response(exc)


@router.post("/business-state/reset", response_model=BusinessStateAuditResponse)
async def reset_business_state(payload: BusinessStateResetRequest, actor: EnterpriseActor = Depends(require_enterprise_actor)):
    try:
        require_role(actor, "risk_decision_maker")
        return BusinessStateAuditResponse(data=service.reset_business_state(actor.company_id, payload, _actor_name(actor)))
    except (RiskWorkflowStateError, InternalRiskDataError) as exc:
        return _service_error_response(exc)


@router.get("/business-state/audit", response_model=BusinessStateAuditListResponse)
async def business_state_audit(actor: EnterpriseActor = Depends(require_enterprise_actor)):
    try:
        return BusinessStateAuditListResponse(items=service.business_state_audit(actor.company_id))
    except InternalRiskDataError as exc:
        return _service_error_response(exc)


@router.post("/business-state/baseline/proposal", response_model=LegacyBaselineRegistrationResponse, status_code=201)
async def propose_legacy_baseline(payload: LegacyBaselineProposalRequest, actor: EnterpriseActor = Depends(require_enterprise_actor)):
    try:
        require_role(actor, "risk_decision_maker")
        return LegacyBaselineRegistrationResponse(
            data=service.propose_legacy_baseline(actor.company_id, payload, _actor_name(actor))
        )
    except (RiskWorkflowNotFoundError, RiskWorkflowStateError, InternalRiskDataError) as exc:
        return _service_error_response(exc)


@router.post("/business-state/baseline/confirmation", response_model=LegacyBaselineRegistrationResponse)
async def confirm_legacy_baseline(payload: LegacyBaselineConfirmationRequest, actor: EnterpriseActor = Depends(require_enterprise_actor)):
    try:
        require_role(actor, "risk_decision_maker")
        return LegacyBaselineRegistrationResponse(
            data=service.confirm_legacy_baseline(actor.company_id, payload, _actor_name(actor))
        )
    except (RiskWorkflowNotFoundError, RiskWorkflowStateError, InternalRiskDataError) as exc:
        return _service_error_response(exc)


@router.post("/business-state/baseline/cancel", response_model=LegacyBaselineRegistrationResponse)
async def cancel_legacy_baseline(payload: LegacyBaselineCancelRequest, actor: EnterpriseActor = Depends(require_enterprise_actor)):
    """Withdraw a pending legacy baseline proposal before re-proposing current state."""
    try:
        require_role(actor, "risk_decision_maker")
        return LegacyBaselineRegistrationResponse(
            data=service.cancel_legacy_baseline(actor.company_id, payload, _actor_name(actor))
        )
    except (RiskWorkflowNotFoundError, RiskWorkflowStateError, InternalRiskDataError) as exc:
        return _service_error_response(exc)


@router.get("/workflow-templates", response_model=WorkflowTemplateListResponse)
async def workflow_templates(actor: EnterpriseActor = Depends(require_enterprise_actor)):
    try:
        return WorkflowTemplateListResponse(items=service.workflow_templates(actor.company_id))
    except InternalRiskDataError as exc:
        return _service_error_response(exc)


@router.get("/workflow-templates/{template_id}/versions/{version}", response_model=WorkflowTemplateResponse)
async def workflow_template_version(template_id: str, version: int, actor: EnterpriseActor = Depends(require_enterprise_actor)):
    try:
        return WorkflowTemplateResponse(data=service.workflow_template(template_id, actor.company_id, version))
    except (RiskWorkflowNotFoundError, InternalRiskDataError) as exc:
        return _service_error_response(exc)


@router.get("/workflow-templates/{template_id}/audit", response_model=WorkflowTemplateAuditListResponse)
async def workflow_template_audit(template_id: str, actor: EnterpriseActor = Depends(require_enterprise_actor)):
    try:
        return WorkflowTemplateAuditListResponse(items=service.workflow_template_audit(template_id, actor.company_id))
    except (RiskWorkflowNotFoundError, InternalRiskDataError) as exc:
        return _service_error_response(exc)


@router.post("/workflow-templates", response_model=WorkflowTemplateResponse, status_code=201)
async def create_workflow_template(payload: WorkflowTemplateCreateRequest, actor: EnterpriseActor = Depends(require_enterprise_actor)):
    try:
        require_role(actor, "risk_decision_maker")
        return WorkflowTemplateResponse(data=service.create_workflow_template(payload, actor.company_id, _actor_name(actor)))
    except (RiskWorkflowStateError, InternalRiskDataError) as exc:
        return _service_error_response(exc)


@router.post("/workflow-templates/import", response_model=WorkflowTemplateResponse, status_code=201)
async def import_workflow_template(payload: WorkflowTemplateImportRequest, actor: EnterpriseActor = Depends(require_enterprise_actor)):
    try:
        require_role(actor, "risk_decision_maker")
        return WorkflowTemplateResponse(data=service.import_workflow_template(payload, actor.company_id, _actor_name(actor)))
    except (RiskWorkflowStateError, InternalRiskDataError) as exc:
        return _service_error_response(exc)


@router.post("/workflow-templates/{template_id}/versions", response_model=WorkflowTemplateResponse, status_code=201)
async def create_workflow_template_version(
    template_id: str, payload: WorkflowTemplateVersionCreateRequest, actor: EnterpriseActor = Depends(require_enterprise_actor),
):
    try:
        require_role(actor, "risk_decision_maker")
        return WorkflowTemplateResponse(
            data=service.create_workflow_template_version(template_id, payload, actor.company_id, _actor_name(actor))
        )
    except (RiskWorkflowNotFoundError, RiskWorkflowStateError, InternalRiskDataError) as exc:
        return _service_error_response(exc)


@router.get("/risks", response_model=RiskItemListResponse)
async def risks(
    company_id: str | None = None,
    risk_level: str | None = None,
    risk_domain: str | None = None,
    lifecycle_stage: str | None = None,
    status: str | None = None, actor: EnterpriseActor = Depends(require_enterprise_actor),
):
    try:
        return RiskItemListResponse(
            items=service.risks(
                company_id=require_company(actor, company_id),
                risk_level=risk_level,
                risk_domain=risk_domain,
                lifecycle_stage=lifecycle_stage,
                status=status,
            )
        )
    except InternalRiskDataError as exc:
        return _service_error_response(exc)


@router.get("/events", response_model=RiskEventListResponse)
async def events(company_id: str | None = None, status: str | None = None, actor: EnterpriseActor = Depends(require_enterprise_actor)):
    try:
        return RiskEventListResponse(items=service.risk_events(company_id=require_company(actor, company_id), status=status))
    except InternalRiskDataError as exc:
        return _service_error_response(exc)


@router.post("/events", response_model=RiskEventResponse, status_code=201)
async def create_event(payload: RiskEventCreate, actor: EnterpriseActor = Depends(require_enterprise_actor)):
    try:
        require_role(actor, "risk_operator")
        return RiskEventResponse(data=service.create_risk_event(payload.model_copy(update={"reported_by": _actor_name(actor)}), actor.company_id))
    except (RiskWorkflowNotFoundError, RiskWorkflowStateError, InternalRiskDataError) as exc:
        return _service_error_response(exc)


@router.post("/events/{event_id}/assessment", response_model=RiskEventResponse)
async def assess_event(event_id: str, payload: RiskEventAssessmentRequest, actor: EnterpriseActor = Depends(require_enterprise_actor)):
    try:
        require_role(actor, "risk_operator")
        _target_company(service.risk_event(event_id, actor.company_id), actor)
        return RiskEventResponse(data=service.assess_risk_event(event_id, payload, actor.company_id))
    except (RiskWorkflowNotFoundError, RiskWorkflowStateError, InternalRiskDataError) as exc:
        return _service_error_response(exc)


@router.post("/events/{event_id}/assessment-jobs", response_model=RiskEventAssessmentJobResponse, status_code=202)
async def start_assessment_job(
    event_id: str,
    payload: RiskEventAssessmentRequest,
    background_tasks: BackgroundTasks,
    actor: EnterpriseActor = Depends(require_enterprise_actor),
):
    """Queue a material-backed RAG assessment and return its durable audit handle."""
    try:
        require_role(actor, "risk_operator")
        _target_company(service.risk_event(event_id, actor.company_id), actor)
        job = service.start_risk_event_assessment_job(event_id, payload, actor.company_id)
        background_tasks.add_task(service.run_risk_event_assessment_job, job.assessment_job_id, actor.company_id)
        return RiskEventAssessmentJobResponse(data=job)
    except (RiskWorkflowNotFoundError, RiskWorkflowStateError, InternalRiskDataError) as exc:
        return _service_error_response(exc)


@router.get("/assessment-jobs/{assessment_job_id}", response_model=RiskAssessmentJobResponse)
async def get_assessment_job(assessment_job_id: str, actor: EnterpriseActor = Depends(require_enterprise_actor)):
    try:
        return RiskAssessmentJobResponse(data=service.assessment_job(assessment_job_id, actor.company_id))
    except (RiskWorkflowNotFoundError, InternalRiskDataError) as exc:
        return _service_error_response(exc)


@router.post("/assessment-jobs/{assessment_job_id}/retry", response_model=RiskEventAssessmentJobResponse, status_code=202)
async def retry_assessment_job(
    assessment_job_id: str, background_tasks: BackgroundTasks, actor: EnterpriseActor = Depends(require_enterprise_actor),
):
    try:
        require_role(actor, "risk_operator")
        job = service.retry_risk_event_assessment_job(assessment_job_id, actor.company_id)
        background_tasks.add_task(service.run_risk_event_assessment_job, job.assessment_job_id, actor.company_id)
        return RiskEventAssessmentJobResponse(data=job)
    except (RiskWorkflowNotFoundError, RiskWorkflowStateError, InternalRiskDataError) as exc:
        return _service_error_response(exc)


@router.patch("/events/{event_id}/confirmation", response_model=RiskEventResponse)
async def confirm_event(event_id: str, payload: RiskEventConfirmationUpdate, actor: EnterpriseActor = Depends(require_enterprise_actor)):
    try:
        require_role(actor, "risk_reviewer")
        _target_company(service.risk_event(event_id, actor.company_id), actor)
        return RiskEventResponse(data=service.confirm_risk_event(event_id, payload.model_copy(update={"reviewer": _actor_name(actor)}), actor.company_id))
    except (RiskWorkflowNotFoundError, RiskWorkflowStateError, InternalRiskDataError) as exc:
        return _service_error_response(exc)


@router.get("/gates", response_model=RiskGateListResponse)
async def gates(
    company_id: str | None = None,
    lifecycle_stage: str | None = None,
    decision: str | None = None,
    actor: EnterpriseActor = Depends(require_enterprise_actor),
):
    try:
        return RiskGateListResponse(
            items=service.gates(company_id=require_company(actor, company_id), lifecycle_stage=lifecycle_stage, decision=decision)
        )
    except InternalRiskDataError as exc:
        return _service_error_response(exc)


@router.patch("/gates/{gate_id}/decision", response_model=RiskGateResponse)
async def record_gate_decision(gate_id: str, payload: GateDecisionUpdate, actor: EnterpriseActor = Depends(require_enterprise_actor)):
    try:
        require_role(actor, "risk_decision_maker")
        _target_company(service.gate(gate_id, actor.company_id), actor)
        return RiskGateResponse(data=service.record_gate_decision(gate_id, payload.model_copy(update={"reviewer": _actor_name(actor)}), actor.company_id))
    except (RiskWorkflowNotFoundError, RiskWorkflowStateError, InternalRiskDataError) as exc:
        return _service_error_response(exc)


@router.patch("/gates/{gate_id}/checks/{check_id}", response_model=RiskGateResponse)
async def update_gate_check(gate_id: str, check_id: str, payload: GateCheckUpdate, actor: EnterpriseActor = Depends(require_enterprise_actor)):
    try:
        require_role(actor, "risk_operator", "risk_reviewer")
        _target_company(service.gate(gate_id, actor.company_id), actor)
        return RiskGateResponse(data=service.update_gate_check(gate_id, check_id, payload, _actor_name(actor), actor.company_id))
    except (RiskWorkflowNotFoundError, RiskWorkflowStateError, InternalRiskDataError) as exc:
        return _service_error_response(exc)


@router.get("/gates/{gate_id}/blockers", response_model=WorkflowBlockerListResponse)
async def gate_blockers(
    gate_id: str, decision: str = "approved", actor: EnterpriseActor = Depends(require_enterprise_actor),
):
    try:
        _target_company(service.gate(gate_id, actor.company_id), actor)
        return WorkflowBlockerListResponse(items=service.gate_blockers(gate_id, decision, actor.company_id))
    except (RiskWorkflowNotFoundError, InternalRiskDataError) as exc:
        return _service_error_response(exc)


@router.get("/tasks", response_model=RemediationTaskListResponse)
async def tasks(
    company_id: str | None = None,
    risk_id: str | None = None,
    status: str | None = None,
    owner: str | None = None,
    actor: EnterpriseActor = Depends(require_enterprise_actor),
):
    try:
        return RemediationTaskListResponse(
            items=service.tasks(company_id=require_company(actor, company_id), risk_id=risk_id, status=status, owner=owner)
        )
    except InternalRiskDataError as exc:
        return _service_error_response(exc)


@router.get("/management-assistance", response_model=ManagementAssistanceResponse)
async def management_assistance(company_id: str | None = None, actor: EnterpriseActor = Depends(require_enterprise_actor)):
    try:
        suggestions, reminders = service.management_assistance(company_id=require_company(actor, company_id))
        return ManagementAssistanceResponse(suggestions=suggestions, reminders=reminders)
    except (RiskWorkflowNotFoundError, InternalRiskDataError) as exc:
        return _service_error_response(exc)


@router.post("/management-assistance/refresh", response_model=ManagementAssistanceResponse)
async def refresh_management_assistance(company_id: str | None = None, actor: EnterpriseActor = Depends(require_enterprise_actor)):
    try:
        require_role(actor, "risk_operator")
        suggestions, reminders = service.refresh_management_assistance(company_id=require_company(actor, company_id))
        return ManagementAssistanceResponse(suggestions=suggestions, reminders=reminders)
    except (RiskWorkflowNotFoundError, InternalRiskDataError) as exc:
        return _service_error_response(exc)


@router.post("/management-assistance/suggestions/{suggestion_id}/adoption", response_model=RemediationSuggestionResponse)
async def adopt_remediation_suggestion(suggestion_id: str, payload: SuggestionAdoptionRequest, actor: EnterpriseActor = Depends(require_enterprise_actor)):
    try:
        require_role(actor, "risk_operator")
        suggestion = next((item for item in service.management_assistance(actor.company_id)[0] if item.suggestion_id == suggestion_id), None)
        if suggestion is None:
            raise RiskWorkflowNotFoundError("remediation suggestion not found")
        return RemediationSuggestionResponse(data=service.adopt_remediation_suggestion(suggestion_id, payload.model_copy(update={"adopted_by": _actor_name(actor)}), actor.company_id))
    except (RiskWorkflowNotFoundError, RiskWorkflowStateError, InternalRiskDataError) as exc:
        return _service_error_response(exc)


@router.patch("/management-assistance/reminders/{reminder_id}/acknowledgement", response_model=ReminderResponse)
async def acknowledge_reminder(reminder_id: str, payload: ReminderAcknowledgementRequest, actor: EnterpriseActor = Depends(require_enterprise_actor)):
    try:
        require_role(actor, "risk_operator", "risk_reviewer")
        reminder = next((item for item in service.management_assistance(actor.company_id)[1] if item.reminder_id == reminder_id), None)
        if reminder is None:
            raise RiskWorkflowNotFoundError("reminder not found")
        return ReminderResponse(data=service.acknowledge_reminder(reminder_id, payload.model_copy(update={"acknowledged_by": _actor_name(actor)}), actor.company_id))
    except (RiskWorkflowNotFoundError, RiskWorkflowStateError, InternalRiskDataError) as exc:
        return _service_error_response(exc)


@router.post("/risks/{risk_id}/acceptances", response_model=RiskAcceptanceResponse, status_code=201)
async def create_risk_acceptance(risk_id: str, payload: RiskAcceptanceCreate, actor: EnterpriseActor = Depends(require_enterprise_actor)):
    try:
        require_role(actor, "risk_decision_maker")
        _target_company(service.risk_item(risk_id, actor.company_id), actor)
        return RiskAcceptanceResponse(data=service.create_risk_acceptance(risk_id, payload.model_copy(update={"decision_maker": _actor_name(actor)}), actor.company_id))
    except (RiskWorkflowNotFoundError, RiskWorkflowStateError, InternalRiskDataError) as exc:
        return _service_error_response(exc)


@router.patch("/risk-acceptances/{acceptance_id}/approval", response_model=RiskAcceptanceResponse)
async def approve_risk_acceptance(acceptance_id: str, payload: RiskAcceptanceApprovalRequest, actor: EnterpriseActor = Depends(require_enterprise_actor)):
    try:
        require_role(actor, "risk_decision_maker")
        acceptance = next((item for item in service.workflow(actor.company_id).risk_acceptances if item.acceptance_id == acceptance_id), None)
        if acceptance is None:
            raise RiskWorkflowNotFoundError("risk acceptance not found")
        return RiskAcceptanceResponse(data=service.approve_risk_acceptance(acceptance_id, payload.model_copy(update={"approved_by": _actor_name(actor)}), actor.company_id))
    except (RiskWorkflowNotFoundError, RiskWorkflowStateError, InternalRiskDataError) as exc:
        return _service_error_response(exc)


@router.patch("/tasks/{task_id}", response_model=RemediationTaskResponse)
async def update_task(task_id: str, payload: TaskStatusUpdate, actor: EnterpriseActor = Depends(require_enterprise_actor)):
    try:
        require_role(actor, "risk_operator")
        _target_company(service.remediation_task(task_id, actor.company_id), actor)
        return RemediationTaskResponse(data=service.update_task_status(task_id, payload.model_copy(update={"changed_by": _actor_name(actor)}), actor.company_id))
    except (RiskWorkflowNotFoundError, RiskWorkflowStateError, InternalRiskDataError) as exc:
        return _service_error_response(exc)


@router.post("/tasks/{task_id}/evidence", response_model=RemediationTaskResponse)
async def add_task_evidence(task_id: str, payload: TaskEvidenceUpdate, actor: EnterpriseActor = Depends(require_enterprise_actor)):
    try:
        require_role(actor, "risk_operator")
        _target_company(service.remediation_task(task_id, actor.company_id), actor)
        return RemediationTaskResponse(data=service.add_task_evidence(task_id, payload.model_copy(update={"changed_by": _actor_name(actor)}), actor.company_id))
    except (RiskWorkflowNotFoundError, RiskWorkflowStateError, InternalRiskDataError) as exc:
        return _service_error_response(exc)


@router.patch("/risks/{risk_id}/closure", response_model=RiskItemResponse)
async def close_risk(risk_id: str, payload: RiskClosureUpdate, actor: EnterpriseActor = Depends(require_enterprise_actor)):
    try:
        require_role(actor, "risk_decision_maker")
        _target_company(service.risk_item(risk_id, actor.company_id), actor)
        return RiskItemResponse(data=service.close_risk(risk_id, payload.model_copy(update={"reviewer": _actor_name(actor)}), actor.company_id))
    except (RiskWorkflowNotFoundError, RiskWorkflowStateError, InternalRiskDataError) as exc:
        return _service_error_response(exc)


@router.get("/risks/{risk_id}/closure-blockers", response_model=WorkflowBlockerListResponse)
async def risk_closure_blockers(risk_id: str, actor: EnterpriseActor = Depends(require_enterprise_actor)):
    try:
        _target_company(service.risk_item(risk_id, actor.company_id), actor)
        return WorkflowBlockerListResponse(items=service.risk_closure_blockers(risk_id, actor.company_id))
    except (RiskWorkflowNotFoundError, InternalRiskDataError) as exc:
        return _service_error_response(exc)


@router.get("/reviews", response_model=ManualReviewListResponse)
async def reviews(
    company_id: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    status: str | None = None,
    actor: EnterpriseActor = Depends(require_enterprise_actor),
):
    try:
        return ManualReviewListResponse(
            items=service.manual_reviews(
                company_id=require_company(actor, company_id),
                target_type=target_type,
                target_id=target_id,
                status=status,
            )
        )
    except InternalRiskDataError as exc:
        return _service_error_response(exc)


@router.patch("/reviews/{review_id}", response_model=ManualReviewResponse)
async def record_manual_review_decision(review_id: str, payload: ManualReviewDecisionUpdate, actor: EnterpriseActor = Depends(require_enterprise_actor)):
    try:
        require_role(actor, "risk_reviewer")
        _target_company(service.manual_review(review_id, actor.company_id), actor)
        return ManualReviewResponse(data=service.record_manual_review_decision(review_id, payload.model_copy(update={"reviewer": _actor_name(actor)}), actor.company_id))
    except (RiskWorkflowNotFoundError, RiskWorkflowStateError, InternalRiskDataError) as exc:
        return _service_error_response(exc)
