from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from src.external_risk.schemas import ExternalRiskSignal
from src.external_risk.service import ExternalRiskService
from src.internal_risk.schemas import RiskEventCreate
from src.internal_risk.service import InternalRiskWorkflowService
from src.risk_intake.repository import JsonRiskIntakeRepository, RiskIntakeDataError
from src.risk_intake.schemas import (
    EnterpriseRiskObject,
    EnterpriseRiskScope,
    ExternalIntakeCase,
    ExternalIntakeSyncBatch,
    ExternalIntakeTriageUpdate,
    ExternalObjectMatch,
    ExternalSignalSnapshot,
    ExternalSyncSourceHealth,
    LifecycleState,
    LifecycleStateTransition,
    LifecycleStateTransitionRequest,
)


class RiskIntakeNotFoundError(LookupError):
    pass


class RiskIntakeStateError(ValueError):
    pass


DOMAIN_TO_INTERNAL = {
    "data_compliance": "data_model_governance",
    "ip": "technology_ip",
    "contract": "product_commercialization",
    "supply_chain": "cross_border_supply_chain",
    "export_control": "cross_border_supply_chain",
    "disclosure": "corporate_finance_governance",
    "corporate_governance": "corporate_finance_governance",
    "market": "corporate_finance_governance",
}

STRONG_MATCH_TYPES = {"supplier_id", "security_code", "alias"}
MATCHING_RULE_VERSION = "strong_object_match_v2"

class RiskIntakeService:
    """Keeps external facts separate until an accountable reviewer promotes them."""

    def __init__(
        self,
        repository: JsonRiskIntakeRepository | Path | None = None,
        external_service: ExternalRiskService | None = None,
        internal_service: InternalRiskWorkflowService | None = None,
    ) -> None:
        self.repository = JsonRiskIntakeRepository() if repository is None else (
            JsonRiskIntakeRepository(repository) if isinstance(repository, Path) else repository
        )
        self.external_service = external_service or ExternalRiskService()
        self.internal_service = internal_service or InternalRiskWorkflowService()

    def scope(self, company_id: str) -> EnterpriseRiskScope:
        raw_scope = self.repository.load_payload()["scopes"].get(company_id)
        if raw_scope is None:
            raise RiskIntakeNotFoundError(f"enterprise scope not found: {company_id}")
        return EnterpriseRiskScope.model_validate(raw_scope)

    def cases(self, company_id: str, status: str | None = None) -> list[ExternalIntakeCase]:
        items = [
            ExternalIntakeCase.model_validate(item)
            for item in self.repository.load_payload()["cases"]
            if item.get("company_id") == company_id
        ]
        return [item for item in items if status is None or item.status == status]

    def sync_batches(self, company_id: str, limit: int = 10) -> list[ExternalIntakeSyncBatch]:
        self.scope(company_id)
        safe_limit = max(1, min(limit, 100))
        batches = [
            ExternalIntakeSyncBatch.model_validate(item)
            for item in self.repository.load_payload().get("sync_batches", [])
            if item.get("company_id") == company_id
        ]
        return sorted(batches, key=lambda item: item.completed_at, reverse=True)[:safe_limit]

    def transition_lifecycle_state(
        self,
        company_id: str,
        state_id: str,
        update: LifecycleStateTransitionRequest,
    ) -> tuple[LifecycleState, LifecycleStateTransition]:
        """Change one business activity state and retain its decision context."""
        payload = self.repository.load_payload()
        raw_scope = payload["scopes"].get(company_id)
        if raw_scope is None:
            raise RiskIntakeNotFoundError(f"enterprise scope not found: {company_id}")
        scope = EnterpriseRiskScope.model_validate(raw_scope)
        state_index = next(
            (index for index, item in enumerate(scope.lifecycle_states) if item.state_id == state_id),
            None,
        )
        if state_index is None:
            raise RiskIntakeNotFoundError(f"lifecycle state not found: {state_id}")
        current = scope.lifecycle_states[state_index]
        if (
            current.business_stage == update.business_stage
            and current.control_stage == update.control_stage
            and current.status == update.status
        ):
            raise RiskIntakeStateError("lifecycle state transition must change the stage or status")

        gate_decision = None
        if update.gate_id:
            gate = next((item for item in self.internal_service.gates() if item.gate_id == update.gate_id), None)
            if gate is None:
                raise RiskIntakeNotFoundError(f"risk gate not found: {update.gate_id}")
            if gate.project_id != current.scope_id:
                raise RiskIntakeStateError("lifecycle state gate must belong to the same business activity")
            if gate.lifecycle_stage != update.control_stage:
                raise RiskIntakeStateError("lifecycle state gate must match the target control stage")
            gate_decision = gate.decision

        effective_from = update.effective_from or datetime.now(timezone.utc)
        transitioned = current.model_copy(update={
            "business_stage": update.business_stage,
            "control_stage": update.control_stage,
            "status": update.status,
            "effective_from": effective_from,
            "owner": update.changed_by,
            "basis": update.basis,
        })
        transition = LifecycleStateTransition(
            transition_id=f"lifecycle-transition-{uuid4().hex[:12]}",
            state_id=current.state_id,
            scope_id=current.scope_id,
            previous_business_stage=current.business_stage,
            previous_control_stage=current.control_stage,
            previous_status=current.status,
            business_stage=transitioned.business_stage,
            control_stage=transitioned.control_stage,
            status=transitioned.status,
            effective_from=effective_from,
            changed_by=update.changed_by,
            basis=update.basis,
            gate_id=update.gate_id,
            gate_decision=gate_decision,
        )
        scope.lifecycle_states[state_index] = transitioned
        scope.lifecycle_state_history.append(transition)
        scope.updated_at = datetime.now(timezone.utc)
        payload["scopes"][company_id] = scope.model_dump(mode="json")
        self.repository.save_payload(payload)
        return transitioned, transition

    def sync_external_cases(
        self,
        company_id: str,
        signals: list[ExternalRiskSignal] | None = None,
    ) -> list[ExternalIntakeCase]:
        """Manual synchronization retained for API compatibility.

        It can only create or refresh pending review cases; triage remains a human action.
        """
        return self._sync_external_cases(company_id, signals)[0]

    def sync_polled_signals(
        self,
        signals: list[ExternalRiskSignal],
        source_health: ExternalSyncSourceHealth | dict | None = None,
    ) -> list[ExternalIntakeSyncBatch]:
        """Apply one external polling result to every registered enterprise scope."""
        health = _coerce_source_health(source_health, default_name="external_intelligence")
        summaries: list[ExternalIntakeSyncBatch] = []
        for company_id in self.repository.load_payload()["scopes"]:
            _, summary = self._sync_external_cases(company_id, signals, source_health=health)
            summaries.append(summary)
        return summaries

    def record_poll_failure(self, reason: str) -> list[ExternalIntakeSyncBatch]:
        """Make a failed poll visible without generating any intake case."""
        health = ExternalSyncSourceHealth(
            source_name="external_intelligence", status="failed", fresh=False,
            checked_at=datetime.now(timezone.utc), message=reason[:1000],
        )
        summaries: list[ExternalIntakeSyncBatch] = []
        for company_id in self.repository.load_payload()["scopes"]:
            _, summary = self._sync_external_cases(company_id, [], source_health=health, errors=[reason])
            summaries.append(summary)
        return summaries

    def _sync_external_cases(
        self,
        company_id: str,
        signals: list[ExternalRiskSignal] | None = None,
        *,
        source_health: ExternalSyncSourceHealth | dict | None = None,
        errors: list[str] | None = None,
    ) -> tuple[list[ExternalIntakeCase], ExternalIntakeSyncBatch]:
        scope = self.scope(company_id)
        payload = self.repository.load_payload()
        now = datetime.now(timezone.utc)
        created_or_updated: list[ExternalIntakeCase] = []
        source_signals = signals if signals is not None else self.external_service.signals(company_id=company_id)
        health = _coerce_source_health(source_health, default_name="manual_sync")
        batch = ExternalIntakeSyncBatch(
            batch_id=f"intake-sync-{uuid4().hex[:12]}", company_id=company_id,
            started_at=now, completed_at=now, matching_rule_version=MATCHING_RULE_VERSION,
            source_health=health, signals_received=len(source_signals), errors=list(errors or []),
        )
        for signal in source_signals:
            if not _signal_is_usable(signal, health):
                batch.skipped_unusable_source_count += 1
                continue
            matches = _match_signal(scope.objects, signal)
            if not matches:
                batch.observation_count += 1
                continue
            domain = _domain_for_signal(signal)
            if domain is None:
                batch.observation_count += 1
                continue
            matching_states = _active_lifecycle_states(scope, matches)
            if not matching_states:
                # An object outside an active business activity remains an external
                # observation. It cannot be treated as a current enterprise case.
                batch.observation_count += 1
                continue
            batch.exact_match_count += len(matches)
            matching_state_ids = sorted(state.state_id for state in matching_states)
            correlation_key = _correlation_key(company_id, signal, matches, domain)
            evidence_hash = _evidence_hash(signal)
            event_fingerprint = _event_fingerprint(signal, matches, domain)
            key = _idempotency_key(correlation_key, event_fingerprint)
            snapshot = _snapshot(signal, now)
            existing_index = next(
                (index for index, item in enumerate(payload["cases"]) if item.get("idempotency_key") == key),
                None,
            )
            correlated_index = next(
                (index for index in range(len(payload["cases"]) - 1, -1, -1)
                if payload["cases"][index].get("correlation_key") == correlation_key),
                None,
            )
            correlated_case = (
                ExternalIntakeCase.model_validate(payload["cases"][correlated_index])
                if correlated_index is not None else None
            )
            prior_rejected = correlated_case if correlated_case and correlated_case.status == "rejected" else None
            if existing_index is None and prior_rejected and prior_rejected.event_fingerprint == event_fingerprint:
                # A reviewer rejection is final for an unchanged external event.
                continue
            if existing_index is None and correlated_case:
                if correlated_case.status == "pending_triage":
                    # Keep one current review item and retain prior source snapshots.
                    existing_index = correlated_index
                elif correlated_case.status != "rejected":
                    # Promotion and merge are human conclusions and cannot be changed by polling.
                    continue
            if existing_index is None:
                item = ExternalIntakeCase(
                    intake_id=f"intake-{uuid4().hex[:12]}",
                    company_id=company_id,
                    idempotency_key=key,
                    correlation_key=correlation_key,
                    event_fingerprint=event_fingerprint,
                    evidence_hash=evidence_hash,
                    matching_rule_version=MATCHING_RULE_VERSION,
                    sync_batch_id=batch.batch_id,
                    source_health=health,
                    supersedes_intake_id=(prior_rejected.intake_id if prior_rejected else None),
                    signal=snapshot,
                    matched_objects=matches,
                    risk_domain=domain,
                    lifecycle_state_ids=matching_state_ids,
                    target_lifecycle_stage=_proposed_control_stage(matching_states),
                    first_seen_at=now,
                    last_seen_at=now,
                    created_at=now,
                    updated_at=now,
                )
                payload["cases"].append(item.model_dump(mode="json"))
                batch.new_case_count += 1
            else:
                item = ExternalIntakeCase.model_validate(payload["cases"][existing_index])
                if item.status != "pending_triage":
                    # Automation cannot reopen or alter a concluded human review.
                    continue
                item.signal_history.append(copy.deepcopy(item.signal))
                item.signal = snapshot
                item.evidence_hash = evidence_hash
                item.event_fingerprint = event_fingerprint
                item.matching_rule_version = MATCHING_RULE_VERSION
                item.sync_batch_id = batch.batch_id
                item.source_health = health
                item.last_seen_at = now
                item.updated_at = now
                payload["cases"][existing_index] = item.model_dump(mode="json")
                batch.updated_case_count += 1
            created_or_updated.append(item)
        batch.completed_at = datetime.now(timezone.utc)
        payload.setdefault("sync_batches", []).append(batch.model_dump(mode="json"))
        self.repository.save_payload(payload)
        return created_or_updated, batch

    def triage_case(self, intake_id: str, update: ExternalIntakeTriageUpdate) -> ExternalIntakeCase:
        payload = self.repository.load_payload()
        for index, raw_case in enumerate(payload["cases"]):
            if raw_case.get("intake_id") != intake_id:
                continue
            case = ExternalIntakeCase.model_validate(raw_case)
            if case.status != "pending_triage":
                raise RiskIntakeStateError("only a pending intake case can be triaged")
            now = datetime.now(timezone.utc)
            case.reviewed_by = update.reviewer
            case.reviewed_at = now
            case.conclusion = update.conclusion
            if update.decision == "promote":
                project_id = update.project_id or _project_for_case(self.scope(case.company_id), case)
                if not project_id:
                    raise RiskIntakeStateError("a promoted case requires a matched active project")
                target_stage = _control_stage_for_project(self.scope(case.company_id), case, project_id)
                if target_stage is None:
                    raise RiskIntakeStateError("the selected project has no active control stage in the enterprise scope")
                event = self.internal_service.create_risk_event(RiskEventCreate(
                    project_id=project_id,
                    title=f"外部观察：{case.signal.title}",
                    description=_event_description(case),
                    lifecycle_stage=target_stage,
                    risk_domain=case.risk_domain,
                    occurred_at=case.signal.observed_at,
                    reported_by=update.reviewer,
                    source_refs=[case.signal.signal_id, case.signal.source],
                    origin="external_signal",
                    external_intake_id=case.intake_id,
                    matched_object_ids=[match.object_id for match in case.matched_objects],
                    signal_snapshot=case.signal.model_dump(mode="json"),
                ))
                case.status = "promoted"
                case.internal_event_id = event.event_id
            elif update.decision == "reject":
                case.status = "rejected"
            else:
                case.status = "merged"
            case.updated_at = now
            payload["cases"][index] = case.model_dump(mode="json")
            self.repository.save_payload(payload)
            return case
        raise RiskIntakeNotFoundError(f"external intake case not found: {intake_id}")


def _normalise(value: str) -> str:
    return "".join(character for character in str(value).lower() if character.isalnum() or "\u4e00" <= character <= "\u9fff")


def _signal_values(signal: ExternalRiskSignal) -> dict[str, set[str]]:
    metadata = signal.metadata or {}
    aliases = [signal.entity, *(metadata.get("aliases") or []), *(metadata.get("affected_entities") or [])]
    return {
        "supplier_id": {_normalise(item) for item in [*signal.affected_supply_links, metadata.get("supplier_id")] if item},
        "security_code": {_normalise(item) for item in [*(metadata.get("security_codes") or []), metadata.get("security_code")] if item},
        "alias": {_normalise(item) for item in aliases if item},
        "tag": {_normalise(item) for item in [*signal.affected_domains, *(metadata.get("industry_tags") or [])] if item},
        "region": {_normalise(item) for item in [*(metadata.get("regions") or []), metadata.get("region")] if item},
    }


def _match_signal(objects: list[EnterpriseRiskObject], signal: ExternalRiskSignal) -> list[ExternalObjectMatch]:
    values = _signal_values(signal)
    strong_matches: list[ExternalObjectMatch] = []
    for obj in objects:
        if not obj.active:
            continue
        candidates = {
            "supplier_id": [obj.supplier_id],
            "security_code": obj.security_codes,
            "alias": [obj.name, *obj.aliases],
            "tag": obj.external_tags,
            "region": obj.regions,
        }
        for match_type, entries in candidates.items():
            overlap = sorted({
                _normalise(entry) for entry in entries if entry and _normalise(entry) in values[match_type]
            })
            if overlap:
                match = ExternalObjectMatch(
                    object_id=obj.object_id,
                    match_type=match_type,
                    matched_values=overlap,
                    score={"supplier_id": 1.0, "security_code": 1.0, "alias": 0.95, "tag": 0.7, "region": 0.7}[match_type],
                    rule_id=f"deterministic_{match_type}_v1",
                )
                if match_type in STRONG_MATCH_TYPES and (
                    match_type != "alias" or _is_trusted_alias_source(signal)
                ):
                    strong_matches.append(match)
                break
    # Tags and regions are contextual observations only; they never create a case.
    return strong_matches


def _domain_for_signal(signal: ExternalRiskSignal) -> str | None:
    domains = [str(item) for item in signal.affected_domains]
    for domain in domains:
        if domain in DOMAIN_TO_INTERNAL:
            return DOMAIN_TO_INTERNAL[domain]
    return None


def _active_lifecycle_states(
    scope: EnterpriseRiskScope,
    matches: list[ExternalObjectMatch],
) -> list[LifecycleState]:
    matched_ids = {match.object_id for match in matches}
    active_state_ids = {
        state_id
        for obj in scope.objects
        if obj.object_id in matched_ids
        for state_id in obj.lifecycle_state_ids
    }
    return [
        state for state in scope.lifecycle_states
        if state.state_id in active_state_ids and state.status == "active"
    ]


def _proposed_control_stage(states: list[LifecycleState]) -> str | None:
    stages = {state.control_stage for state in states if state.control_stage}
    return next(iter(stages)) if len(stages) == 1 else None


def _correlation_key(company_id: str, signal: ExternalRiskSignal, matches: list[ExternalObjectMatch], domain: str) -> str:
    object_ids = ",".join(sorted(match.object_id for match in matches))
    return f"{company_id}:{signal.signal_id}:{object_ids}:{domain}:v2"


def _idempotency_key(correlation_key: str, event_fingerprint: str) -> str:
    return f"{correlation_key}:{event_fingerprint[:16]}"


def _evidence_hash(signal: ExternalRiskSignal) -> str:
    material = {
        "source": signal.source, "as_of": signal.as_of, "title": signal.title,
        "entity": signal.entity, "evidence": signal.evidence, "metadata": signal.metadata,
    }
    encoded = json.dumps(material, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _event_fingerprint(signal: ExternalRiskSignal, matches: list[ExternalObjectMatch], domain: str) -> str:
    material = {
        "signal_id": signal.signal_id, "severity": signal.severity, "direction": signal.direction,
        "domains": sorted(signal.affected_domains), "objects": sorted(match.object_id for match in matches),
        "domain": domain, "evidence_hash": _evidence_hash(signal),
    }
    encoded = json.dumps(material, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _is_trusted_alias_source(signal: ExternalRiskSignal) -> bool:
    trusted = signal.metadata.get("trusted_source") if signal.metadata else None
    return bool(trusted) if trusted is not None else signal.source.startswith("https://")


def _coerce_source_health(
    value: ExternalSyncSourceHealth | dict | None, *, default_name: str,
) -> ExternalSyncSourceHealth:
    if isinstance(value, ExternalSyncSourceHealth):
        return value
    if isinstance(value, dict):
        return ExternalSyncSourceHealth.model_validate(value)
    return ExternalSyncSourceHealth(source_name=default_name, status="manual", fresh=True,
                                    checked_at=datetime.now(timezone.utc))


def _signal_is_usable(signal: ExternalRiskSignal, health: ExternalSyncSourceHealth) -> bool:
    metadata = signal.metadata or {}
    status = str(metadata.get("source_status") or metadata.get("source_freshness") or "").lower()
    feed_id = str(metadata.get("feed_id") or metadata.get("source_id") or "")
    return (
        health.fresh
        and health.status not in {"failed", "stale"}
        and status not in {"failed", "stale"}
        and feed_id not in set(health.blocked_source_ids)
    )


def _snapshot(signal: ExternalRiskSignal, observed_at: datetime) -> ExternalSignalSnapshot:
    return ExternalSignalSnapshot(
        signal_id=signal.signal_id,
        title=signal.title,
        signal_type=signal.signal_type,
        severity=signal.severity,
        as_of=signal.as_of,
        entity=signal.entity,
        affected_domains=list(signal.affected_domains),
        affected_supply_links=list(signal.affected_supply_links),
        evidence=signal.evidence,
        source=signal.source,
        confidence=signal.confidence,
        metadata=copy.deepcopy(signal.metadata),
        observed_at=observed_at,
    )


def _project_for_case(scope: EnterpriseRiskScope, case: ExternalIntakeCase) -> str | None:
    matched_ids = {match.object_id for match in case.matched_objects}
    project_ids = {
        obj.project_id for obj in scope.objects
        if obj.object_id in matched_ids and obj.project_id
    }
    return next(iter(project_ids)) if len(project_ids) == 1 else None


def _control_stage_for_project(
    scope: EnterpriseRiskScope,
    case: ExternalIntakeCase,
    project_id: str,
) -> str | None:
    matched_ids = {match.object_id for match in case.matched_objects}
    project_object_ids = {
        obj.object_id for obj in scope.objects
        if obj.object_id in matched_ids and obj.project_id == project_id and obj.active
    }
    if not project_object_ids:
        raise RiskIntakeStateError("the selected project must belong to a matched enterprise object")
    active_states = _active_lifecycle_states(
        scope,
        [match for match in case.matched_objects if match.object_id in project_object_ids],
    )
    return _proposed_control_stage(active_states)


def _event_description(case: ExternalIntakeCase) -> str:
    object_ids = "、".join(match.object_id for match in case.matched_objects)
    return (
        f"外部信号“{case.signal.title}”于 {case.signal.as_of} 被采集，"
        f"按确定性规则命中企业对象：{object_ids}。"
        f"来源：{case.signal.source}。该记录仅为待核验事实，不构成自动风险结论。"
    )
