from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from src.supply_chain.schemas import (
    DeleteSupplierResponse,
    SupplierInput,
    SupplierListResponse,
    SupplierResponse,
)
from src.supply_chain.service import SupplierNotFoundError, SupplyChainService


router = APIRouter(prefix="/supply-chain", tags=["supply-chain"])
service = SupplyChainService()


@router.get("/suppliers", response_model=SupplierListResponse)
async def list_suppliers() -> SupplierListResponse:
    return SupplierListResponse(items=service.list_suppliers())


@router.post("/suppliers", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier(payload: SupplierInput) -> SupplierResponse:
    return SupplierResponse(data=service.create_supplier(payload))


@router.put("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(supplier_id: str, payload: SupplierInput) -> SupplierResponse:
    try:
        return SupplierResponse(data=service.update_supplier(supplier_id, payload))
    except SupplierNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="supplier not found") from exc


@router.delete("/suppliers/{supplier_id}", response_model=DeleteSupplierResponse)
async def delete_supplier(supplier_id: str) -> DeleteSupplierResponse:
    try:
        service.delete_supplier(supplier_id)
        return DeleteSupplierResponse(deleted_id=supplier_id)
    except SupplierNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="supplier not found") from exc
