from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src.product.schemas import ProductDataResponse, ProductListResponse
from src.product.service import ProductViewModelError, ProductViewModelService


router = APIRouter(prefix="/product", tags=["product"])
service = ProductViewModelService()


def _product_view_model_error_response(error: ProductViewModelError) -> JSONResponse:
    return JSONResponse(
        status_code=error.http_status,
        content={"error": {"code": error.code, "message": error.public_message}},
    )


@router.get("/dashboard/summary", response_model=ProductDataResponse)
async def product_dashboard_summary(company_id: str | None = None, as_of: str | None = None):
    try:
        return ProductDataResponse(data=service.dashboard_summary())
    except ProductViewModelError as exc:
        return _product_view_model_error_response(exc)


@router.get("/legal/workspace", response_model=ProductDataResponse)
async def product_legal_workspace(workspace_id: str | None = None, thread_id: str | None = None):
    try:
        return ProductDataResponse(data=service.legal_workspace())
    except ProductViewModelError as exc:
        return _product_view_model_error_response(exc)


@router.get("/market/signals", response_model=ProductDataResponse)
async def product_market_signals(
    company_id: str | None = None,
    domain: str | None = None,
    as_of: str | None = None,
):
    try:
        return ProductDataResponse(data=service.market_signals())
    except ProductViewModelError as exc:
        return _product_view_model_error_response(exc)


@router.get("/supply-chain/map", response_model=ProductDataResponse)
async def product_supply_chain_map(company_id: str | None = None, map_mode: str | None = None):
    try:
        return ProductDataResponse(data=service.supply_chain_map())
    except ProductViewModelError as exc:
        return _product_view_model_error_response(exc)


@router.get("/lifecycle/risk", response_model=ProductDataResponse)
async def product_lifecycle_risk(company_id: str | None = None):
    try:
        return ProductDataResponse(data=service.lifecycle_risk())
    except ProductViewModelError as exc:
        return _product_view_model_error_response(exc)


@router.get("/risks", response_model=ProductListResponse)
async def product_risks(
    company_id: str | None = None,
    risk_level: str | None = None,
    domain: str | None = None,
    review_status: str | None = None,
):
    try:
        return ProductListResponse(
            items=service.product_risks(
                risk_level=risk_level,
                domain=domain,
                review_status=review_status,
            )
        )
    except ProductViewModelError as exc:
        return _product_view_model_error_response(exc)
