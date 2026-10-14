from __future__ import annotations

import ipaddress

from fastapi import APIRouter, HTTPException, Request

from src.external_risk.router import service as external_risk_service
from src.runtime_settings.schemas import RuntimeSettingsResponse, RuntimeSettingsUpdate, RuntimeSettingsUpdateResponse
from src.runtime_settings.service import RuntimeSettingsError, read_runtime_settings, update_runtime_settings


router = APIRouter(prefix="/settings", tags=["settings"])


def _require_local_settings_access(request: Request) -> None:
    host = request.client.host if request.client else ""
    if host == "testclient":
        return
    try:
        if ipaddress.ip_address(host).is_loopback:
            return
    except ValueError:
        pass
    raise HTTPException(status_code=403, detail="Runtime settings are available only from the local machine")


@router.get("/runtime", response_model=RuntimeSettingsResponse)
async def get_runtime_settings(request: Request):
    _require_local_settings_access(request)
    return RuntimeSettingsResponse(data=read_runtime_settings())


@router.put("/runtime", response_model=RuntimeSettingsUpdateResponse)
async def save_runtime_settings(update: RuntimeSettingsUpdate, request: Request):
    _require_local_settings_access(request)
    try:
        data, restart_required = update_runtime_settings(update)
        external_risk_service.reload_runtime_configuration()
        return RuntimeSettingsUpdateResponse(data=data, restart_required=restart_required)
    except RuntimeSettingsError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
