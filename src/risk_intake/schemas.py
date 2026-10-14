from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from src.internal_risk.schemas import LifecycleStage, RiskDomain
from src.risk_intake.contracts import RISK_INTAKE_DATA_SOURCE, RISK_INTAKE_VERSION


BusinessStage = Literal[
    "formation", "research", "market_access", "product", "commercialization",
    "financing", "growth", "scaling", "transition", "exit", "operation",
]
LifecycleStateStatus = Literal["baseline_pending", "planned", "active", "paused", "completed"]
RiskObjectType = Literal[
    "company", "project", "product", "contract", "supplier", "region", "technology"
]
ExternalMatchType = Literal["supplier_id", "security_code", "alias", "tag", "region"]
ExternalIntakeStatus = Literal["pending_triage", "promoted", "rejected", "merged"]
TriageDecision = Literal["promote", "reject", "merge"]
SyncSourceStatus = Literal["healthy", "stale", "failed", "manual"]


class RiskIntakeResponseMeta(BaseModel):
    contract_version: str = RISK_INTAKE_VERSION
    fixture_version: str = RISK_INTAKE_VERSION
    data_source: Literal["fixture_sample"] = RISK_INTAKE_DATA_SOURCE


class LifecycleState(BaseModel):
    state_id: str
    scope_id: str
    scope_type: RiskObjectType
    business_stage: BusinessStage
    control_stage: LifecycleStage | None = None
    status: LifecycleStateStatus = "baseline_pending"
    effective_from: datetime | None = None
    owner: str | None = None
    basis: str | None = None


class LifecycleStateTransition(BaseModel):
    """Append-only record of an accountable lifecycle-state change."""

    transition_id: str
    state_id: str
    scope_id: str
    previous_business_stage: BusinessStage
    previous_control_stage: LifecycleStage | None = None
    previous_status: LifecycleStateStatus
    business_stage: BusinessStage
    control_stage: LifecycleStage | None = None
    status: LifecycleStateStatus
    effective_from: datetime
    changed_by: str
    basis: str
    gate_id: str | None = None
    gate_decision: str | None = None


class LifecycleStateTransitionRequest(BaseModel):
    business_stage: BusinessStage
    control_stage: LifecycleStage | None = None
    status: LifecycleStateStatus
    changed_by: str = Field(min_length=1, max_length=80)
    basis: str = Field(min_length=1, max_length=1000)
    effective_from: datetime | None = None
    gate_id: str | None = Field(default=None, max_length=120)


class EnterpriseRiskObject(BaseModel):
    object_id: str
    object_type: RiskObjectType
    name: str
    aliases: list[str] = Field(default_factory=list)
    external_tags: list[str] = Field(default_factory=list)
    security_codes: list[str] = Field(default_factory=list)
    regions: list[str] = Field(default_factory=list)
    supplier_id: str | None = None
    project_id: str | None = None
    lifecycle_state_ids: list[str] = Field(default_factory=list)
    active: bool = True


class EnterpriseRiskScope(BaseModel):
    company_id: str
    name: str
    profile_version: str = "1"
    industry_package: str | None = None
    objects: list[EnterpriseRiskObject] = Field(default_factory=list)
    lifecycle_states: list[LifecycleState] = Field(default_factory=list)
    lifecycle_state_history: list[LifecycleStateTransition] = Field(default_factory=list)
    updated_at: datetime


class ExternalSignalSnapshot(BaseModel):
    signal_id: str
    title: str
    signal_type: str
    severity: str
    as_of: str
    entity: str
    affected_domains: list[str] = Field(default_factory=list)
    affected_supply_links: list[str] = Field(default_factory=list)
    evidence: str
    source: str
    confidence: float
    metadata: dict[str, Any] = Field(default_factory=dict)
    observed_at: datetime


class ExternalObjectMatch(BaseModel):
    object_id: str
    match_type: ExternalMatchType
    matched_values: list[str]
    score: float = Field(ge=0, le=1)
    rule_id: str


class ExternalSyncSourceHealth(BaseModel):
    """The condition of the source used for one intake synchronization batch."""

    source_name: str = "external_intelligence"
    status: SyncSourceStatus = "manual"
    fresh: bool = True
    checked_at: datetime | None = None
    cache_updated_at: datetime | None = None
    blocked_source_ids: list[str] = Field(default_factory=list)
    message: str | None = None


class ExternalIntakeCase(BaseModel):
    intake_id: str
    company_id: str
    idempotency_key: str
    correlation_key: str | None = None
    event_fingerprint: str | None = None
    evidence_hash: str | None = None
    matching_rule_version: str = "strong_object_match_v2"
    sync_batch_id: str | None = None
    source_health: ExternalSyncSourceHealth | None = None
    supersedes_intake_id: str | None = None
    signal: ExternalSignalSnapshot
    matched_objects: list[ExternalObjectMatch] = Field(default_factory=list)
    risk_domain: RiskDomain
    lifecycle_state_ids: list[str] = Field(default_factory=list)
    # A candidate can span more than one activity. The responsible reviewer selects
    # the affected project before an internal event receives its control stage.
    target_lifecycle_stage: LifecycleStage | None = None
    status: ExternalIntakeStatus = "pending_triage"
    first_seen_at: datetime
    last_seen_at: datetime
    created_at: datetime
    updated_at: datetime
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    conclusion: str | None = None
    internal_event_id: str | None = None
    signal_history: list[ExternalSignalSnapshot] = Field(default_factory=list)


class ExternalIntakeSyncBatch(BaseModel):
    batch_id: str
    company_id: str
    started_at: datetime
    completed_at: datetime
    matching_rule_version: str = "strong_object_match_v2"
    source_health: ExternalSyncSourceHealth
    signals_received: int = Field(default=0, ge=0)
    exact_match_count: int = Field(default=0, ge=0)
    new_case_count: int = Field(default=0, ge=0)
    updated_case_count: int = Field(default=0, ge=0)
    observation_count: int = Field(default=0, ge=0)
    skipped_unusable_source_count: int = Field(default=0, ge=0)
    errors: list[str] = Field(default_factory=list)


class ExternalIntakeTriageUpdate(BaseModel):
    decision: TriageDecision
    reviewer: str = Field(min_length=1, max_length=80)
    conclusion: str = Field(min_length=1, max_length=1000)
    project_id: str | None = Field(default=None, max_length=120)


class RiskIntakeScopeResponse(BaseModel):
    status: Literal["ok"] = "ok"
    data: EnterpriseRiskScope
    meta: RiskIntakeResponseMeta = Field(default_factory=RiskIntakeResponseMeta)


class LifecycleStateTransitionResponse(BaseModel):
    status: Literal["ok"] = "ok"
    data: LifecycleState
    transition: LifecycleStateTransition
    meta: RiskIntakeResponseMeta = Field(default_factory=RiskIntakeResponseMeta)


class ExternalIntakeCaseListResponse(BaseModel):
    status: Literal["ok"] = "ok"
    items: list[ExternalIntakeCase] = Field(default_factory=list)
    meta: RiskIntakeResponseMeta = Field(default_factory=RiskIntakeResponseMeta)


class ExternalIntakeCaseResponse(BaseModel):
    status: Literal["ok"] = "ok"
    data: ExternalIntakeCase
    meta: RiskIntakeResponseMeta = Field(default_factory=RiskIntakeResponseMeta)


class ExternalIntakeSyncBatchListResponse(BaseModel):
    status: Literal["ok"] = "ok"
    items: list[ExternalIntakeSyncBatch] = Field(default_factory=list)
    meta: RiskIntakeResponseMeta = Field(default_factory=RiskIntakeResponseMeta)
