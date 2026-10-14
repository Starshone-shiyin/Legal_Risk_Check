"""HTTP contracts for persisted custom Skills; execution remains intentionally blocked."""
from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import APIRouter, HTTPException, status

from src.skills.schemas import (
    NODE_TYPE_SPECS,
    DeleteSkillResponse,
    SkillListResponse,
    SkillNodeTypesResponse,
    SkillPayload,
    SkillRecord,
    SkillRunRequest,
    SkillResponse,
    SkillRunResponse,
    SkillValidationResponse,
)
from src.skills.service import BuiltinSkillProtectedError, SkillNotFoundError, SkillService


router = APIRouter(prefix="/skills", tags=["skills"])
service = SkillService()
SkillExecutionHandler = Callable[[SkillRecord, SkillRunRequest, list], Awaitable[SkillRunResponse]]
execution_handler: SkillExecutionHandler | None = None


def configure_execution_handler(handler: SkillExecutionHandler | None) -> None:
    """Configure the application-owned executor without exposing providers to the editor."""
    global execution_handler
    execution_handler = handler


@router.get("/node-types", response_model=SkillNodeTypesResponse)
async def list_node_types() -> SkillNodeTypesResponse:
    return SkillNodeTypesResponse(node_types=NODE_TYPE_SPECS)


@router.post("/validate", response_model=SkillValidationResponse)
async def validate_skill(payload: SkillPayload) -> SkillValidationResponse:
    return service.validate_skill(payload)


@router.get("", response_model=SkillListResponse)
async def list_skills() -> SkillListResponse:
    return SkillListResponse(items=service.list_skills())


@router.post("", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(payload: SkillPayload) -> SkillResponse:
    return SkillResponse(data=service.create_skill(payload))


@router.get("/{skill_id}", response_model=SkillResponse)
async def get_skill(skill_id: str) -> SkillResponse:
    try:
        return SkillResponse(data=service.get_skill(skill_id))
    except SkillNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="skill not found") from exc


@router.put("/{skill_id}", response_model=SkillResponse)
@router.patch("/{skill_id}", response_model=SkillResponse)
async def update_skill(skill_id: str, payload: SkillPayload) -> SkillResponse:
    try:
        return SkillResponse(data=service.update_skill(skill_id, payload))
    except SkillNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="skill not found") from exc
    except BuiltinSkillProtectedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="built-in Skills cannot be edited") from exc


@router.delete("/{skill_id}", response_model=DeleteSkillResponse)
async def delete_skill(skill_id: str) -> DeleteSkillResponse:
    try:
        service.delete_skill(skill_id)
        return DeleteSkillResponse(deleted_id=skill_id)
    except SkillNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="skill not found") from exc
    except BuiltinSkillProtectedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="built-in Skills cannot be deleted") from exc


@router.post("/{skill_id}/run", response_model=SkillRunResponse)
async def run_skill(skill_id: str, request: SkillRunRequest) -> SkillRunResponse:
    try:
        skill = service.get_skill(skill_id)
        plan = service.build_execution_plan(skill_id)
        if execution_handler is not None:
            return await execution_handler(skill, request, plan)
        return service.run_skill(skill_id)
    except SkillNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="skill not found") from exc
