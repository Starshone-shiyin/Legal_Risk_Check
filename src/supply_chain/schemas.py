from __future__ import annotations

from datetime import datetime
import re
from typing import Literal

from pydantic import BaseModel, Field


RiskLevel = Literal["low", "medium", "high", "critical"]
ControlStatus = Literal["not_started", "monitoring", "mitigating", "closed"]


def normalize_security_code(value: str | None) -> str | None:
    """Normalize common listed-instrument inputs to the market workflow symbol format."""
    if value is None or not value.strip():
        return None
    compact = value.strip().lower().replace(".", "").replace("-", "").replace(" ", "")
    if re.fullmatch(r"(?:sh|sz|bj)\d{6}", compact):
        return compact
    if re.fullmatch(r"\d{6}", compact):
        return ("sh" if compact[0] in "569" else "bj" if compact[0] in "48" else "sz") + compact
    if re.fullmatch(r"(?:hk)?\d{1,5}", compact):
        return f"hk_{re.sub(r'^hk', '', compact).zfill(4)}"
    if re.fullmatch(r"(?:us_)?[a-z]{1,8}", compact):
        return f"us_{compact.removeprefix('us_').upper()}"
    raise ValueError("证券代码格式不支持，请使用 600519、sh688981、hk00700 或 NVDA")


class SupplierInput(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    country: str = Field(min_length=1, max_length=80)
    province: str | None = Field(default=None, max_length=80)
    city: str | None = Field(default=None, max_length=80)
    category: str = Field(min_length=1, max_length=80)
    spend_share: float = Field(default=0, ge=0, le=100)
    criticality: float = Field(default=50, ge=0, le=100)
    alternate_sources: int = Field(default=0, ge=0, le=99)
    compliance_risk: float = Field(default=0, ge=0, le=100)
    external_tags: list[str] = Field(default_factory=list, max_length=16)
    external_signal_ids: list[str] = Field(default_factory=list, max_length=32)
    security_code: str | None = Field(default=None, max_length=20)
    risk_owner: str | None = Field(default=None, max_length=80)
    control_status: ControlStatus = "not_started"
    last_reviewed_at: str | None = Field(default=None, max_length=10)
    evidence_refs: list[str] = Field(default_factory=list, max_length=16)
    record_scope: Literal["business_record", "competition_scenario"] = "business_record"
    mapping_evidence_grade: Literal["unverified", "scenario_proxy", "document_referenced", "contract_verified"] = "unverified"
    relationship_boundary: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=1000)

    def model_post_init(self, __context: object) -> None:
        self.security_code = normalize_security_code(self.security_code)


class SupplierRecord(SupplierInput):
    supplier_id: str
    created_at: datetime
    updated_at: datetime


class SupplierListResponse(BaseModel):
    status: Literal["ok"] = "ok"
    items: list[SupplierRecord] = Field(default_factory=list)


class SupplierResponse(BaseModel):
    status: Literal["ok"] = "ok"
    data: SupplierRecord


class DeleteSupplierResponse(BaseModel):
    status: Literal["ok"] = "ok"
    deleted_id: str
