from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from src.risk_intake.schemas import (
    ExternalIntakeCaseListResponse,
    ExternalIntakeCaseResponse,
    ExternalIntakeSyncBatchListResponse,
    ExternalIntakeTriageUpdate,
    LifecycleStateTransitionRequest,
    LifecycleStateTransitionResponse,
    RiskIntakeScopeResponse,
)
from src.risk_intake.service import (
    RiskIntakeDataError,
    RiskIntakeNotFoundError,
    RiskIntakeService,
    RiskIntakeStateError,
)
from src.core.enterprise_access import EnterpriseActor, require_company, require_enterprise_actor, require_role


router = APIRouter(prefix="/risk-intake", tags=["risk-intake"])
service = RiskIntakeService()


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": {"code": code, "message": message}})


def _service_error(error: Exception) -> JSONResponse:
    if isinstance(error, RiskIntakeNotFoundError):
        return _error_response(404, "RISK_INTAKE_NOT_FOUND", str(error))
    if isinstance(error, RiskIntakeStateError):
        return _error_response(409, "RISK_INTAKE_INVALID_STATE", str(error))
    return _error_response(503, "RISK_INTAKE_DATA_UNAVAILABLE", str(error))


@router.get("/scopes/{company_id}", response_model=RiskIntakeScopeResponse)
async def scope(company_id: str, actor: EnterpriseActor = Depends(require_enterprise_actor)):
    try:
        return RiskIntakeScopeResponse(data=service.scope(require_company(actor, company_id)))
    except (RiskIntakeNotFoundError, RiskIntakeDataError) as exc:
        return _service_error(exc)


@router.post(
    "/scopes/{company_id}/lifecycle-states/{state_id}/transitions",
    response_model=LifecycleStateTransitionResponse,
)
async def transition_lifecycle_state(
    company_id: str,
    state_id: str,
    payload: LifecycleStateTransitionRequest,
    actor: EnterpriseActor = Depends(require_enterprise_actor),
):
    try:
        require_role(actor, "risk_decision_maker")
        state, transition = service.transition_lifecycle_state(require_company(actor, company_id), state_id, payload.model_copy(update={"changed_by": actor.actor_id}))
        return LifecycleStateTransitionResponse(data=state, transition=transition)
    except (RiskIntakeNotFoundError, RiskIntakeStateError, RiskIntakeDataError) as exc:
        return _service_error(exc)


@router.get("/external-cases", response_model=ExternalIntakeCaseListResponse)
async def external_cases(company_id: str, status: str | None = None, actor: EnterpriseActor = Depends(require_enterprise_actor)):
    try:
        return ExternalIntakeCaseListResponse(items=service.cases(require_company(actor, company_id), status=status))
    except (RiskIntakeNotFoundError, RiskIntakeDataError) as exc:
        return _service_error(exc)


@router.post("/external-cases/sync", response_model=ExternalIntakeCaseListResponse)
async def sync_external_cases(company_id: str, actor: EnterpriseActor = Depends(require_enterprise_actor)):
    try:
        require_role(actor, "risk_operator")
        return ExternalIntakeCaseListResponse(items=service.sync_external_cases(require_company(actor, company_id)))
    except (RiskIntakeNotFoundError, RiskIntakeDataError) as exc:
        return _service_error(exc)


@router.get("/external-cases/sync-summary", response_model=ExternalIntakeSyncBatchListResponse)
async def external_case_sync_summary(company_id: str, limit: int = 10, actor: EnterpriseActor = Depends(require_enterprise_actor)):
    try:
        return ExternalIntakeSyncBatchListResponse(items=service.sync_batches(require_company(actor, company_id), limit=limit))
    except (RiskIntakeNotFoundError, RiskIntakeDataError) as exc:
        return _service_error(exc)


@router.patch("/external-cases/{intake_id}/triage", response_model=ExternalIntakeCaseResponse)
async def triage_external_case(intake_id: str, payload: ExternalIntakeTriageUpdate, actor: EnterpriseActor = Depends(require_enterprise_actor)):
    try:
        require_role(actor, "risk_operator")
        case = next((item for item in service.cases(actor.company_id) if item.intake_id == intake_id), None)
        if case is None:
            raise RiskIntakeNotFoundError("external intake case not found")
        return ExternalIntakeCaseResponse(data=service.triage_case(intake_id, payload.model_copy(update={"reviewer": actor.actor_id})))
    except (RiskIntakeNotFoundError, RiskIntakeStateError, RiskIntakeDataError) as exc:
        return _service_error(exc)
