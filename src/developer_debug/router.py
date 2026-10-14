from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from src.developer_debug.service import (
    DebugRunNotFoundError,
    DebugScenarioNotFoundError,
    DeveloperDebugDisabledError,
    DeveloperDebugService,
)
from src.supply_chain.schemas import SupplierRecord


router = APIRouter(prefix="/developer-debug", tags=["developer-debug"])
service = DeveloperDebugService()


def _debug_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, DeveloperDebugDisabledError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="developer debug mode is unavailable")
    if isinstance(exc, (DebugScenarioNotFoundError, DebugRunNotFoundError)):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="debug scenario or run was not found")
    raise exc


@router.get("/status")
async def debug_status() -> dict:
    try:
        return service.status()
    except DeveloperDebugDisabledError as exc:
        raise _debug_http_error(exc) from exc


@router.post("/scenarios/{scenario_id}/runs", status_code=status.HTTP_201_CREATED)
async def create_debug_run(scenario_id: str) -> dict:
    try:
        return service.create_run(scenario_id)
    except (DeveloperDebugDisabledError, DebugScenarioNotFoundError) as exc:
        raise _debug_http_error(exc) from exc


@router.post("/runs/{run_id}/reset")
async def reset_debug_run(run_id: str) -> dict:
    try:
        return service.reset_run(run_id)
    except (DeveloperDebugDisabledError, DebugRunNotFoundError, DebugScenarioNotFoundError) as exc:
        raise _debug_http_error(exc) from exc


@router.get("/runs/{run_id}")
async def get_debug_run(run_id: str) -> dict:
    try:
        return service.run_metadata(run_id)
    except (DeveloperDebugDisabledError, DebugRunNotFoundError) as exc:
        raise _debug_http_error(exc) from exc


@router.post("/runs/{run_id}/execute")
async def execute_debug_run(run_id: str) -> dict:
    try:
        return service.execute_run(run_id)
    except (DeveloperDebugDisabledError, DebugRunNotFoundError) as exc:
        raise _debug_http_error(exc) from exc


@router.get("/runs/{run_id}/suppliers", response_model=list[SupplierRecord])
async def list_debug_suppliers(run_id: str) -> list[SupplierRecord]:
    try:
        return service.suppliers(run_id)
    except (DeveloperDebugDisabledError, DebugRunNotFoundError) as exc:
        raise _debug_http_error(exc) from exc


@router.get("/runs/{run_id}/context")
async def get_debug_run_context(run_id: str) -> dict:
    try:
        return service.scenario_context(run_id)
    except (DeveloperDebugDisabledError, DebugRunNotFoundError) as exc:
        raise _debug_http_error(exc) from exc


@router.post("/runs/{run_id}/live-snapshot")
async def capture_debug_run_live_snapshot(run_id: str) -> dict:
    try:
        return service.live_snapshot(run_id)
    except (DeveloperDebugDisabledError, DebugRunNotFoundError) as exc:
        raise _debug_http_error(exc) from exc
