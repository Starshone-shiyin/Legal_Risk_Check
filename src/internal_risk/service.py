from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from time import perf_counter
from typing import Callable
from uuid import uuid4

from src.risk.report import generate_risk_report
from src.document_ingest.service import DocumentIngestError, DocumentIngestService

from src.internal_risk.repository import (
    InternalRiskDataError,
    InternalRiskWorkflowRepository,
    JsonInternalRiskWorkflowRepository,
)
from src.internal_risk.schemas import (
    InternalRiskWorkflow,
    BusinessStateAuditRecord,
    BusinessStateInitializeRequest,
    BusinessStateResetRequest,
    LegacyBaselineConfirmationRequest,
    LegacyBaselineCancelRequest,
    LegacyBaselineProposalRequest,
    LegacyBaselineRegistration,
    EnterpriseCompanyProfile,
    GateDecisionUpdate,
    EvidenceSnapshot,
    ManualReview,
    ManualReviewDecisionEvent,
    ManualReviewDecisionUpdate,
    RemediationTask,
    RemediationTaskStatusEvent,
    RemediationSuggestion,
    ReminderAcknowledgementRequest,
    ReminderRecord,
    RiskAcceptance,
    RiskAcceptanceApprovalRequest,
    RiskAcceptanceCreate,
    RiskGate,
    RiskGateDecisionEvent,
    RiskEvent,
    RiskEventAssessmentRequest,
    RiskEventConfirmation,
    RiskEventConfirmationUpdate,
    RiskEventCreate,
    RiskAssessmentSnapshot,
    RiskAssessmentJob,
    RiskAssessmentJobAuditEvent,
    RiskItem,
    RiskItemStatusEvent,
    RiskClosureUpdate,
    RiskGateCheck,
    GateCheckUpdate,
    SuggestionAdoptionRequest,
    TaskEvidenceUpdate,
    TaskStatusUpdate,
    WorkflowBlocker,
    WorkflowTemplate,
    WorkflowTemplateAuditRecord,
    WorkflowTemplateBinding,
    WorkflowTemplateCreateRequest,
    WorkflowTemplateImportRequest,
    WorkflowTemplateVersionCreateRequest,
)


__all__ = [
    "InternalRiskDataError",
    "RiskWorkflowNotFoundError",
    "RiskWorkflowStateError",
    "InternalRiskWorkflowService",
]


class RiskWorkflowNotFoundError(LookupError):
    pass


class RiskWorkflowStateError(ValueError):
    """A rejected workflow command with auditable, machine-readable blockers."""

    def __init__(self, message: str, blockers: list[WorkflowBlocker] | None = None) -> None:
        super().__init__(message)
        self.blockers = blockers or []


TASK_STATUS_TRANSITIONS = {
    "not_started": {"in_progress", "blocked"},
    "in_progress": {"blocked", "pending_review"},
    "blocked": {"in_progress"},
    "pending_review": {"in_progress", "verified"},
    "verified": set(),
}

MANUAL_REVIEW_DECISION_TASK_STATUS = {
    "approved": "verified",
    "changes_requested": "in_progress",
    "rejected": "in_progress",
}

RISK_EVENT_REPORT_FILTERS = {
    "k",
    "collection_name",
    "doc_type",
    "block_type",
    "document_type",
    "law_name",
    "source",
    "law_level",
    "authority_level",
    "jurisdiction",
    "issuing_authority",
    "legal_effect",
    "standard_type",
    "case_type",
    "patent_type",
    "category",
    "version",
    "score_threshold",
}


class InternalRiskWorkflowService:
    """Internal risk workflow queries with auditable remediation task updates."""

    def __init__(
        self,
        repository: InternalRiskWorkflowRepository | Path | None = None,
        report_generator: Callable[..., dict] | None = None,
        document_service: DocumentIngestService | None = None,
    ) -> None:
        if repository is None:
            self.repository = JsonInternalRiskWorkflowRepository()
        elif isinstance(repository, Path):
            self.repository = JsonInternalRiskWorkflowRepository(repository)
        else:
            self.repository = repository
        self.report_generator = report_generator
        self.document_service = document_service or DocumentIngestService()

    def _payload(self) -> dict:
        return self.repository.load_payload()

    @staticmethod
    def _workflow_raw(payload: dict, company_id: str | None = None) -> dict:
        """Read a company workflow while retaining the original single-workflow fixture shape."""
        workflows = payload.get("workflows")
        if isinstance(workflows, dict):
            if company_id:
                workflow = workflows.get(company_id)
                if workflow is None:
                    raise RiskWorkflowNotFoundError(f"enterprise workflow not found: {company_id}")
                return workflow
            legacy = payload.get("workflow")
            if isinstance(legacy, dict):
                return legacy
            if len(workflows) == 1:
                return next(iter(workflows.values()))
            raise RiskWorkflowNotFoundError("company id is required when more than one enterprise workflow exists")
        workflow = payload.get("workflow")
        if not isinstance(workflow, dict):
            raise InternalRiskDataError("internal risk workflow fixture missing workflow")
        if company_id and workflow.get("company_id") != company_id:
            raise RiskWorkflowNotFoundError(f"enterprise workflow not found: {company_id}")
        return workflow

    @staticmethod
    def _state_digest(workflow: dict) -> str:
        return hashlib.sha256(
            json.dumps(workflow, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _template_content_digest(*, name: str, description: str | None, gates: list) -> str:
        return hashlib.sha256(json.dumps(
            {"name": name, "description": description, "gates": gates},
            ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ).encode("utf-8")).hexdigest()

    @staticmethod
    def _template_store(payload: dict) -> dict:
        store = payload.setdefault("workflow_templates", {})
        if not isinstance(store, dict):
            raise InternalRiskDataError("workflow templates must be an object keyed by company id")
        return store

    def _template_versions(self, payload: dict, company_id: str, template_id: str) -> list[dict]:
        versions = self._template_store(payload).get(company_id, {}).get(template_id)
        if not isinstance(versions, list) or not versions:
            raise RiskWorkflowNotFoundError(f"workflow template not found: {template_id}")
        return versions

    def workflow_templates(self, company_id: str) -> list[WorkflowTemplate]:
        company_templates = self._template_store(self._payload()).get(company_id, {})
        if not isinstance(company_templates, dict):
            raise InternalRiskDataError("workflow templates for company must be an object")
        return [WorkflowTemplate.model_validate(versions[-1]) for versions in company_templates.values() if versions]

    def workflow_template(self, template_id: str, company_id: str, version: int | None = None) -> WorkflowTemplate:
        versions = self._template_versions(self._payload(), company_id, template_id)
        raw = next((item for item in versions if item.get("version") == version), None) if version else versions[-1]
        if raw is None:
            raise RiskWorkflowNotFoundError(f"workflow template version not found: {template_id}@{version}")
        return WorkflowTemplate.model_validate(raw)

    def workflow_template_audit(self, template_id: str, company_id: str) -> list[WorkflowTemplateAuditRecord]:
        # Resolve first so an unauthorized tenant cannot use audit lookup as an existence oracle.
        self.workflow_template(template_id, company_id)
        return [
            WorkflowTemplateAuditRecord.model_validate(item)
            for item in self._payload().get("workflow_template_audit", [])
            if item.get("company_id") == company_id and item.get("template_id") == template_id
        ]

    def _append_workflow_template(
        self,
        payload: dict,
        company_id: str,
        request: WorkflowTemplateCreateRequest | WorkflowTemplateVersionCreateRequest | WorkflowTemplateImportRequest,
        actor_id: str,
        *,
        template_id: str,
        version: int,
        imported: bool,
    ) -> WorkflowTemplate:
        now = datetime.now(timezone.utc)
        gates = [gate.model_dump(mode="json") for gate in request.gates]
        template = WorkflowTemplate(
            template_id=template_id, company_id=company_id, name=request.name,
            description=request.description, version=version, gates=request.gates,
            created_by=actor_id, created_at=now, change_note=request.change_note,
            imported=imported,
            content_sha256=self._template_content_digest(name=request.name, description=request.description, gates=gates),
        )
        company_templates = self._template_store(payload).setdefault(company_id, {})
        company_templates.setdefault(template_id, []).append(template.model_dump(mode="json"))
        action = "imported" if imported else "created" if version == 1 else "version_created"
        payload.setdefault("workflow_template_audit", []).append(WorkflowTemplateAuditRecord(
            audit_id=f"workflow-template-{uuid4().hex[:12]}", company_id=company_id,
            template_id=template_id, version=version, action=action, actor_id=actor_id,
            occurred_at=now, content_sha256=template.content_sha256, change_note=request.change_note,
        ).model_dump(mode="json"))
        self.repository.save_payload(payload)
        return template

    def create_workflow_template(self, request: WorkflowTemplateCreateRequest, company_id: str, actor_id: str) -> WorkflowTemplate:
        payload = self._payload()
        template_id = request.template_id or f"template-{uuid4().hex[:12]}"
        company_templates = self._template_store(payload).setdefault(company_id, {})
        if template_id in company_templates:
            raise RiskWorkflowStateError("workflow template id already exists")
        return self._append_workflow_template(payload, company_id, request, actor_id, template_id=template_id, version=1, imported=False)

    def import_workflow_template(self, request: WorkflowTemplateImportRequest, company_id: str, actor_id: str) -> WorkflowTemplate:
        """Import a validated JSON template as a new tenant-local, immutable version 1."""
        payload = self._payload()
        template_id = request.template_id or f"imported-template-{uuid4().hex[:10]}"
        company_templates = self._template_store(payload).setdefault(company_id, {})
        if template_id in company_templates:
            raise RiskWorkflowStateError("imported workflow template id already exists")
        return self._append_workflow_template(payload, company_id, request, actor_id, template_id=template_id, version=1, imported=True)

    def create_workflow_template_version(
        self, template_id: str, request: WorkflowTemplateVersionCreateRequest, company_id: str, actor_id: str,
    ) -> WorkflowTemplate:
        payload = self._payload()
        versions = self._template_versions(payload, company_id, template_id)
        return self._append_workflow_template(
            payload, company_id, request, actor_id, template_id=template_id,
            version=max(int(item["version"]) for item in versions) + 1, imported=False,
        )

    @staticmethod
    def _instantiate_template_gates(template: WorkflowTemplate, company_id: str) -> list[RiskGate]:
        return [
            RiskGate(
                gate_id=f"gate-{template.template_id[:24]}-{definition.key}", company_id=company_id,
                project_id=f"workflow-template:{template.template_id}@{template.version}",
                title=definition.title, lifecycle_stage=definition.lifecycle_stage,
                decision=definition.decision, owner=definition.owner_role,
                checks=[RiskGateCheck(check_id=f"check-{definition.key}-{index + 1}", title=title)
                        for index, title in enumerate(definition.checks)],
            )
            for definition in template.gates
        ]

    def _resolve_template_for_initialization(
        self, payload: dict, request: BusinessStateInitializeRequest, company_id: str, actor_id: str, now: datetime,
    ) -> tuple[list[RiskGate], WorkflowTemplateBinding | None]:
        if request.workflow_template_version is not None and not request.workflow_template_id:
            raise RiskWorkflowStateError("workflow_template_version requires workflow_template_id")
        if not request.workflow_template_id:
            return [], None
        versions = self._template_versions(payload, company_id, request.workflow_template_id)
        raw = next((item for item in versions if item.get("version") == request.workflow_template_version), None) if request.workflow_template_version else versions[-1]
        if raw is None:
            raise RiskWorkflowNotFoundError(
                f"workflow template version not found: {request.workflow_template_id}@{request.workflow_template_version}"
            )
        template = WorkflowTemplate.model_validate(raw)
        return self._instantiate_template_gates(template, company_id), WorkflowTemplateBinding(
            template_id=template.template_id, version=template.version, name=template.name,
            content_sha256=template.content_sha256, applied_by=actor_id, applied_at=now,
        )

    def initialize_business_state(
        self,
        company_id: str,
        request: BusinessStateInitializeRequest,
        actor_id: str,
    ) -> BusinessStateAuditRecord:
        """Create a blank, isolated business workflow and an immutable reset baseline.

        This only changes the internal-risk fixture. Runtime credentials, providers and
        external source configuration are outside this repository and are never read or written.
        """
        payload = self._payload()
        workflows = payload.setdefault("workflows", {})
        legacy = payload.get("workflow")
        if isinstance(legacy, dict):
            workflows.setdefault(legacy["company_id"], copy.deepcopy(legacy))
        if company_id in workflows:
            raise RiskWorkflowStateError("enterprise business state is already initialized")
        now = request.as_of or datetime.now(timezone.utc)
        profile = EnterpriseCompanyProfile(
            company_name=request.company_name,
            industry=request.industry,
            business_model=request.business_model,
            lifecycle_stages=list(dict.fromkeys(request.lifecycle_stages)),
        )
        template_gates, template_binding = self._resolve_template_for_initialization(
            payload, request, company_id, actor_id, now,
        )
        workflow = InternalRiskWorkflow(
            company_id=company_id,
            as_of=now.isoformat(),
            company_profile=profile,
            workflow_template=template_binding,
            gates=template_gates,
        ).model_dump(mode="json")
        workflows[company_id] = workflow
        baseline_id = f"baseline-{uuid4().hex[:12]}"
        payload.setdefault("business_state_baselines", {})[company_id] = {
            "baseline_id": baseline_id,
            "workflow": copy.deepcopy(workflow),
            "created_at": now.isoformat(),
        }
        record = BusinessStateAuditRecord(
            audit_id=f"business-state-{uuid4().hex[:12]}", action="initialized",
            company_id=company_id, actor_id=actor_id, occurred_at=now, baseline_id=baseline_id,
            resulting_state_sha256=self._state_digest(workflow), reason=request.reason,
        )
        payload.setdefault("business_state_audit", []).append(record.model_dump(mode="json"))
        self.repository.save_payload(payload)
        return record

    def reset_business_state(
        self,
        company_id: str,
        request: BusinessStateResetRequest,
        actor_id: str,
    ) -> BusinessStateAuditRecord:
        """Restore exactly the company baseline and retain an append-only reset receipt."""
        payload = self._payload()
        baseline = payload.get("business_state_baselines", {}).get(company_id)
        if not isinstance(baseline, dict) or not isinstance(baseline.get("workflow"), dict):
            raise RiskWorkflowStateError("enterprise business state has no reset baseline; initialize it first")
        current = self._workflow_raw(payload, company_id)
        restored = copy.deepcopy(baseline["workflow"])
        workflows = payload.setdefault("workflows", {})
        workflows[company_id] = restored
        if payload.get("workflow", {}).get("company_id") == company_id:
            payload["workflow"] = copy.deepcopy(restored)
        now = datetime.now(timezone.utc)
        record = BusinessStateAuditRecord(
            audit_id=f"business-state-{uuid4().hex[:12]}", action="reset",
            company_id=company_id, actor_id=actor_id, occurred_at=now,
            baseline_id=str(baseline.get("baseline_id")),
            previous_state_sha256=self._state_digest(current),
            resulting_state_sha256=self._state_digest(restored), reason=request.reason,
        )
        payload.setdefault("business_state_audit", []).append(record.model_dump(mode="json"))
        self.repository.save_payload(payload)
        return record

    def business_state_audit(self, company_id: str) -> list[BusinessStateAuditRecord]:
        return [
            BusinessStateAuditRecord.model_validate(item)
            for item in self._payload().get("business_state_audit", [])
            if item.get("company_id") == company_id
        ]

    def propose_legacy_baseline(
        self, company_id: str, request: LegacyBaselineProposalRequest, actor_id: str,
    ) -> LegacyBaselineRegistration:
        """Freeze a proposal for a pre-existing tenant; a different decision maker must confirm it."""
        payload = self._payload()
        if company_id in payload.get("business_state_baselines", {}):
            raise RiskWorkflowStateError("enterprise already has a reset baseline")
        registrations = payload.setdefault("legacy_baseline_registrations", {})
        existing = registrations.get(company_id)
        if isinstance(existing, dict) and existing.get("status") == "pending_confirmation":
            raise RiskWorkflowStateError("a legacy baseline proposal is already pending confirmation")
        workflow = copy.deepcopy(self._workflow_raw(payload, company_id))
        now = datetime.now(timezone.utc)
        digest = self._state_digest(workflow)
        registration = LegacyBaselineRegistration(
            registration_id=f"legacy-baseline-{uuid4().hex[:12]}", company_id=company_id,
            baseline_id=f"baseline-{uuid4().hex[:12]}", status="pending_confirmation",
            proposed_by=actor_id, proposed_at=now, proposed_state_sha256=digest,
            reason=request.reason,
        )
        registrations[company_id] = {
            **registration.model_dump(mode="json"),
            "workflow": workflow,
        }
        payload.setdefault("business_state_audit", []).append(BusinessStateAuditRecord(
            audit_id=f"business-state-{uuid4().hex[:12]}", action="baseline_proposed",
            company_id=company_id, actor_id=actor_id, occurred_at=now,
            baseline_id=registration.baseline_id, resulting_state_sha256=digest, reason=request.reason,
        ).model_dump(mode="json"))
        self.repository.save_payload(payload)
        return registration

    def confirm_legacy_baseline(
        self, company_id: str, request: LegacyBaselineConfirmationRequest, actor_id: str,
    ) -> LegacyBaselineRegistration:
        payload = self._payload()
        raw = payload.get("legacy_baseline_registrations", {}).get(company_id)
        if not isinstance(raw, dict) or raw.get("status") != "pending_confirmation":
            raise RiskWorkflowStateError("no pending legacy baseline proposal exists")
        if raw.get("proposed_by") == actor_id:
            raise RiskWorkflowStateError("legacy baseline confirmation requires a different authorized decision maker")
        current = self._workflow_raw(payload, company_id)
        digest = self._state_digest(current)
        if digest != raw.get("proposed_state_sha256"):
            raise RiskWorkflowStateError("business state changed after baseline proposal; submit a fresh proposal")
        now = datetime.now(timezone.utc)
        raw["status"] = "registered"
        raw["confirmed_by"] = actor_id
        raw["confirmed_at"] = now.isoformat()
        raw["resulting_state_sha256"] = digest
        raw["confirmation_reason"] = request.reason
        payload.setdefault("business_state_baselines", {})[company_id] = {
            "baseline_id": raw["baseline_id"], "workflow": copy.deepcopy(raw["workflow"]),
            "created_at": now.isoformat(), "created_by": raw["proposed_by"],
            "confirmed_by": actor_id, "state_sha256": digest,
        }
        registration = LegacyBaselineRegistration.model_validate(raw)
        payload.setdefault("business_state_audit", []).append(BusinessStateAuditRecord(
            audit_id=f"business-state-{uuid4().hex[:12]}", action="baseline_registered",
            company_id=company_id, actor_id=actor_id, occurred_at=now,
            baseline_id=registration.baseline_id, previous_state_sha256=raw["proposed_state_sha256"],
            resulting_state_sha256=digest, reason=request.reason,
        ).model_dump(mode="json"))
        self.repository.save_payload(payload)
        return registration

    def cancel_legacy_baseline(
        self, company_id: str, request: LegacyBaselineCancelRequest, actor_id: str,
    ) -> LegacyBaselineRegistration:
        """Cancel a stale proposal so the current state can be proposed again.

        Cancellation never removes the proposal receipt: it appends an audit
        event and preserves the original digest for later investigation.
        """
        payload = self._payload()
        raw = payload.get("legacy_baseline_registrations", {}).get(company_id)
        if not isinstance(raw, dict) or raw.get("status") != "pending_confirmation":
            raise RiskWorkflowStateError("no pending legacy baseline proposal exists to cancel")
        now = datetime.now(timezone.utc)
        raw.update({
            "status": "cancelled", "cancelled_by": actor_id,
            "cancelled_at": now.isoformat(), "cancellation_reason": request.reason,
        })
        registration = LegacyBaselineRegistration.model_validate(raw)
        payload.setdefault("business_state_audit", []).append(BusinessStateAuditRecord(
            audit_id=f"business-state-{uuid4().hex[:12]}", action="baseline_cancelled",
            company_id=company_id, actor_id=actor_id, occurred_at=now,
            baseline_id=registration.baseline_id,
            previous_state_sha256=registration.proposed_state_sha256,
            resulting_state_sha256=self._state_digest(self._workflow_raw(payload, company_id)),
            reason=request.reason,
        ).model_dump(mode="json"))
        self.repository.save_payload(payload)
        return registration

    def workflow(self, company_id: str | None = None, as_of: str | None = None) -> InternalRiskWorkflow:
        workflow = copy.deepcopy(self._workflow_raw(self._payload(), company_id))
        if as_of:
            workflow["as_of"] = as_of
        return InternalRiskWorkflow.model_validate(workflow)

    def dashboard(self, company_id: str | None = None, as_of: str | None = None) -> InternalRiskWorkflow:
        return self.workflow(company_id=company_id, as_of=as_of)

    def risk_items(
        self,
        company_id: str | None = None,
        risk_level: str | None = None,
        risk_domain: str | None = None,
        lifecycle_stage: str | None = None,
        status: str | None = None,
    ) -> list[RiskItem]:
        items = self.workflow(company_id=company_id).risk_items
        return [
            item
            for item in items
            if (not risk_level or item.risk_level == risk_level)
            and (not risk_domain or item.risk_domain == risk_domain)
            and (not lifecycle_stage or item.lifecycle_stage == lifecycle_stage)
            and (not status or item.status == status)
        ]

    def risks(
        self,
        company_id: str | None = None,
        risk_level: str | None = None,
        risk_domain: str | None = None,
        lifecycle_stage: str | None = None,
        status: str | None = None,
    ) -> list[RiskItem]:
        return self.risk_items(
            company_id=company_id,
            risk_level=risk_level,
            risk_domain=risk_domain,
            lifecycle_stage=lifecycle_stage,
            status=status,
        )

    def risk_item(self, risk_id: str, company_id: str | None = None) -> RiskItem:
        return self._find(self.workflow(company_id=company_id).risk_items, "risk_id", risk_id, "risk item")

    def risk_events(
        self,
        company_id: str | None = None,
        status: str | None = None,
    ) -> list[RiskEvent]:
        events = self.workflow(company_id=company_id).risk_events
        return [event for event in events if not status or event.status == status]

    def risk_event(self, event_id: str, company_id: str | None = None) -> RiskEvent:
        return self._find(self.workflow(company_id=company_id).risk_events, "event_id", event_id, "risk event")

    def create_risk_event(self, event: RiskEventCreate, company_id: str | None = None) -> RiskEvent:
        """Register facts for review. This command intentionally does not create a risk item."""
        payload = self._payload()
        workflow = self._workflow_raw(payload, company_id)
        now = datetime.now(timezone.utc)
        risk_event = RiskEvent(
            event_id=f"event-{uuid4().hex[:12]}",
            company_id=workflow["company_id"],
            project_id=event.project_id,
            title=event.title,
            description=event.description,
            lifecycle_stage=event.lifecycle_stage,
            risk_domain=event.risk_domain,
            occurred_at=event.occurred_at,
            reported_by=event.reported_by,
            source_refs=list(dict.fromkeys(event.source_refs)),
            document_task_ids=list(dict.fromkeys(event.document_task_ids)),
            origin=event.origin,
            external_intake_id=event.external_intake_id,
            matched_object_ids=list(dict.fromkeys(event.matched_object_ids)),
            signal_snapshot=copy.deepcopy(event.signal_snapshot),
            created_at=now,
            updated_at=now,
        )
        workflow.setdefault("risk_events", []).append(risk_event.model_dump(mode="json"))
        self.repository.save_payload(payload)
        return risk_event

    def start_risk_event_assessment_job(
        self,
        event_id: str,
        request: RiskEventAssessmentRequest,
        company_id: str | None = None,
    ) -> RiskAssessmentJob:
        """Persist a tenant-scoped job before the background worker starts.

        This makes a material/RAG assessment observable even if the process is
        interrupted.  The existing synchronous assessment endpoint remains
        available for callers that need an immediate response.
        """
        payload = self._payload()
        workflow = self._workflow_raw(payload, company_id)
        event = next((item for item in workflow.setdefault("risk_events", []) if item.get("event_id") == event_id), None)
        if event is None:
            raise RiskWorkflowNotFoundError(f"risk event not found: {event_id}")
        if event.get("status") != "draft":
            raise RiskWorkflowStateError("only a draft risk event can receive an assessment job")
        jobs = workflow.setdefault("assessment_jobs", [])
        if any(
            item.get("event_id") == event_id and item.get("status") in {"queued", "running"}
            for item in jobs
        ):
            raise RiskWorkflowStateError("a risk event already has an active assessment job")
        filters = {
            key: value
            for key, value in request.input_filters.items()
            if key in RISK_EVENT_REPORT_FILTERS
        }
        now = datetime.now(timezone.utc)
        job = RiskAssessmentJob(
            assessment_job_id=f"assessment-job-{uuid4().hex[:12]}",
            company_id=str(workflow["company_id"]), event_id=event_id,
            input_filters=filters, created_at=now,
            audit_trail=[RiskAssessmentJobAuditEvent(
                stage="accepted", occurred_at=now,
                detail="Assessment request accepted and queued for material/RAG processing.",
            )],
        )
        jobs.append(job.model_dump(mode="json"))
        self.repository.save_payload(payload)
        return job

    def assessment_job(self, assessment_job_id: str, company_id: str | None = None) -> RiskAssessmentJob:
        workflow = self._workflow_raw(self._payload(), company_id)
        return self._find(
            [RiskAssessmentJob.model_validate(item) for item in workflow.get("assessment_jobs", [])],
            "assessment_job_id", assessment_job_id, "risk assessment job",
        )

    def retry_risk_event_assessment_job(
        self, assessment_job_id: str, company_id: str | None = None,
    ) -> RiskAssessmentJob:
        """Requeue one failed job with a bounded, append-only retry receipt."""
        payload = self._payload()
        workflow = self._workflow_raw(payload, company_id)
        for index, raw_job in enumerate(workflow.setdefault("assessment_jobs", [])):
            if raw_job.get("assessment_job_id") != assessment_job_id:
                continue
            job = RiskAssessmentJob.model_validate(raw_job)
            if job.status != "failed":
                raise RiskWorkflowStateError("only a failed assessment job can be retried")
            if job.retry_count >= 2:
                raise RiskWorkflowStateError("assessment job retry limit reached")
            event = next((item for item in workflow.get("risk_events", []) if item.get("event_id") == job.event_id), None)
            if not isinstance(event, dict) or event.get("status") != "draft":
                raise RiskWorkflowStateError("assessment event is no longer eligible for retry")
            now = datetime.now(timezone.utc)
            job.retry_count += 1
            job.status = "queued"
            job.stage = "accepted"
            job.started_at = None
            job.completed_at = None
            job.failure_code = None
            job.failure_message = None
            job.audit_trail.append(RiskAssessmentJobAuditEvent(
                stage="accepted", occurred_at=now,
                detail=f"Retry {job.retry_count}/2 accepted after the previous failure.",
            ))
            workflow["assessment_jobs"][index] = job.model_dump(mode="json")
            self.repository.save_payload(payload)
            return job
        raise RiskWorkflowNotFoundError(f"risk assessment job not found: {assessment_job_id}")

    def _transition_assessment_job(
        self,
        assessment_job_id: str,
        *,
        company_id: str | None,
        status: str,
        stage: str,
        detail: str,
        assessment_snapshot_id: str | None = None,
        result_sha256: str | None = None,
        failure_code: str | None = None,
        failure_message: str | None = None,
    ) -> RiskAssessmentJob:
        payload = self._payload()
        workflow = self._workflow_raw(payload, company_id)
        jobs = workflow.setdefault("assessment_jobs", [])
        for index, raw_job in enumerate(jobs):
            if raw_job.get("assessment_job_id") != assessment_job_id:
                continue
            job = RiskAssessmentJob.model_validate(raw_job)
            now = datetime.now(timezone.utc)
            job.status = status  # type: ignore[assignment]
            job.stage = stage  # type: ignore[assignment]
            if status == "running" and job.started_at is None:
                job.started_at = now
            if status in {"completed", "failed"}:
                job.completed_at = now
            if assessment_snapshot_id is not None:
                job.assessment_snapshot_id = assessment_snapshot_id
            if result_sha256 is not None:
                job.result_sha256 = result_sha256
            if failure_code is not None:
                job.failure_code = failure_code
            if failure_message is not None:
                job.failure_message = failure_message[:500]
            job.audit_trail.append(RiskAssessmentJobAuditEvent(
                stage=stage, occurred_at=now, detail=detail,
            ))
            jobs[index] = job.model_dump(mode="json")
            self.repository.save_payload(payload)
            return job
        raise RiskWorkflowNotFoundError(f"risk assessment job not found: {assessment_job_id}")

    def run_risk_event_assessment_job(
        self,
        assessment_job_id: str,
        company_id: str | None = None,
    ) -> RiskAssessmentJob:
        """Run a persisted assessment job and leave an auditable terminal receipt."""
        job = self.assessment_job(assessment_job_id, company_id)
        if job.status not in {"queued", "running"}:
            return job
        try:
            self._transition_assessment_job(
                assessment_job_id, company_id=company_id, status="running", stage="material_loading",
                detail="Loading completed user materials and recording provenance.",
            )
            self._transition_assessment_job(
                assessment_job_id, company_id=company_id, status="running", stage="rag_assessment",
                detail="Running the RAG evidence and citation-coverage decision gate.",
            )
            event = self.assess_risk_event(
                job.event_id,
                RiskEventAssessmentRequest(input_filters=job.input_filters),
                company_id,
                assessment_job_id=assessment_job_id,
            )
            snapshot = event.assessment_snapshot
            if snapshot is None:
                raise RiskWorkflowStateError("assessment finished without an immutable snapshot")
            result_sha256 = hashlib.sha256(
                json.dumps(snapshot.report, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            return self._transition_assessment_job(
                assessment_job_id, company_id=company_id, status="completed", stage="snapshot_persisted",
                detail="Immutable assessment snapshot persisted; human confirmation remains required.",
                assessment_snapshot_id=snapshot.snapshot_id, result_sha256=result_sha256,
            )
        except Exception as exc:
            error_code = "ASSESSMENT_FAILED"
            if isinstance(exc, RiskWorkflowStateError):
                error_code = "ASSESSMENT_INVALID_STATE"
                document_error = re.search(r"（([A-Z][A-Z0-9_]+)）", str(exc))
                if document_error:
                    error_code = document_error.group(1)
            elif isinstance(exc, DocumentIngestError):
                error_code = exc.code
            return self._transition_assessment_job(
                assessment_job_id, company_id=company_id, status="failed", stage="failed",
                detail="Assessment stopped before an immutable result could be produced.",
                failure_code=error_code, failure_message=str(exc),
            )

    def assess_risk_event(
        self,
        event_id: str,
        request: RiskEventAssessmentRequest,
        company_id: str | None = None,
        *,
        assessment_job_id: str | None = None,
    ) -> RiskEvent:
        """Create one immutable RAG report snapshot; assessment never approves or opens a gate."""
        payload = self._payload()
        events = self._workflow_raw(payload, company_id).setdefault("risk_events", [])
        for index, raw_event in enumerate(events):
            if raw_event.get("event_id") != event_id:
                continue
            event = RiskEvent.model_validate(raw_event)
            if event.status != "draft":
                raise RiskWorkflowStateError("only a draft risk event can receive an assessment snapshot")
            active_jobs = [
                item for item in self._workflow_raw(self._payload(), company_id).get("assessment_jobs", [])
                if item.get("event_id") == event_id and item.get("status") in {"queued", "running"}
            ]
            if any(item.get("assessment_job_id") != assessment_job_id for item in active_jobs):
                raise RiskWorkflowStateError("a risk event has an active assessment job")
            scenario = f"风险事件：{event.title}\n\n触发事实：{event.description}"
            filters = {
                key: value
                for key, value in request.input_filters.items()
                if key in RISK_EVENT_REPORT_FILTERS
            }
            assessment_started_at = perf_counter()
            try:
                materials = self.document_service.build_llm_materials(event.document_task_ids)
            except DocumentIngestError as exc:
                raise RiskWorkflowStateError(
                    f"关联文档不可用于评估（{exc.code}）：{exc.message}"
                ) from exc
            material_load_elapsed_ms = round((perf_counter() - assessment_started_at) * 1000, 2)
            material_sources = [
                {
                    "task_id": material.get("task_id"),
                    "filename": material.get("filename"),
                    "truncated": bool(material.get("truncated")),
                    "content_sha256": hashlib.sha256(
                        str(material.get("content") or "").encode("utf-8")
                    ).hexdigest(),
                    "char_count": len(str(material.get("content") or "")),
                    "authority": "user_uploaded_material_not_legal_authority",
                }
                for material in materials
            ]
            report_started_at = perf_counter()
            report = (self.report_generator or generate_risk_report)(
                scenario,
                **filters,
                user_materials=materials,
                expected_risk_domain=event.risk_domain,
            )
            now = datetime.now(timezone.utc)
            report.setdefault("material_sources", material_sources)
            event.assessment_snapshot = RiskAssessmentSnapshot(
                snapshot_id=f"snapshot-{uuid4().hex[:12]}",
                generated_at=now,
                scenario=scenario,
                report=report,
                input_filters=filters,
                material_sources=material_sources,
                processing_metrics={
                    "material_count": len(material_sources),
                    "completed_at": now.isoformat(),
                    "elapsed_ms": round((perf_counter() - assessment_started_at) * 1000, 2),
                    "stages": {
                        "material_load_elapsed_ms": material_load_elapsed_ms,
                        "rag_report_elapsed_ms": round((perf_counter() - report_started_at) * 1000, 2),
                        "citation_integrity": (report.get("citation_integrity") or {}).get("passed"),
                        "decision_state": report.get("decision_state", "assessable"),
                    },
                },
            )
            event.status = "assessed"
            event.updated_at = now
            events[index] = event.model_dump(mode="json")
            self.repository.save_payload(payload)
            return event
        raise RiskWorkflowNotFoundError(f"risk event not found: {event_id}")

    def confirm_risk_event(self, event_id: str, update: RiskEventConfirmationUpdate, company_id: str | None = None) -> RiskEvent:
        """Record the human decision and create a ledger item only for a confirmed event."""
        payload = self._payload()
        workflow = self._workflow_raw(payload, company_id)
        events = workflow.setdefault("risk_events", [])
        for index, raw_event in enumerate(events):
            if raw_event.get("event_id") != event_id:
                continue
            event = RiskEvent.model_validate(raw_event)
            if event.status != "assessed" or event.assessment_snapshot is None:
                raise RiskWorkflowStateError("a risk event must be assessed before a human decision is recorded")
            now = datetime.now(timezone.utc)
            event.confirmation = RiskEventConfirmation(
                decision=update.decision,
                reviewer=update.reviewer,
                conclusion=update.conclusion,
                decided_at=now,
            )
            event.status = update.decision
            event.updated_at = now
            if update.decision == "confirmed":
                report = event.assessment_snapshot.report
                citation_integrity = report.get("citation_integrity") or {"passed": True}
                citation_coverage = citation_integrity.get("coverage") or {}
                if (
                    report.get("decision_state") == "pending_evidence"
                    or not citation_integrity.get("passed", True)
                    or citation_coverage.get("requires_review")
                ):
                    raise RiskWorkflowStateError(
                        "assessment evidence is insufficient, citation integrity failed, or citation coverage is incomplete; the event must remain pending evidence"
                    )
                proposed_level = report.get("risk_level")
                if proposed_level in {"high", "critical"} and event.reported_by == update.reviewer:
                    raise RiskWorkflowStateError(
                        "high and critical risk events require a confirmer other than the reporter"
                    )
                source_analysis = report.get("source_analysis") or {}
                missing_materials = list(dict.fromkeys([
                    *(report.get("review_reasons") or []),
                    *(source_analysis.get("missing_evidence") or []),
                ]))
                risk_item = RiskItem(
                    risk_id=f"risk-{event.event_id.removeprefix('event-')}",
                    company_id=event.company_id,
                    project_id=event.project_id,
                    title=event.title,
                    lifecycle_stage=event.lifecycle_stage,
                    risk_domain=event.risk_domain,
                    risk_level=proposed_level if proposed_level in {"low", "medium", "high", "critical"} else "medium",
                    status="open",
                    trigger_facts=[event.description],
                    evidence_refs=list(dict.fromkeys([*event.source_refs, *event.document_task_ids])),
                    legal_query_seeds=[event.assessment_snapshot.scenario],
                    missing_materials=missing_materials,
                    origin=event.origin,
                    external_intake_id=event.external_intake_id,
                    matched_object_ids=list(event.matched_object_ids),
                    signal_snapshot=copy.deepcopy(event.signal_snapshot),
                )
                workflow.setdefault("risk_items", []).append(risk_item.model_dump(mode="json"))
                event.confirmed_risk_id = risk_item.risk_id
            events[index] = event.model_dump(mode="json")
            self.repository.save_payload(payload)
            return event
        raise RiskWorkflowNotFoundError(f"risk event not found: {event_id}")

    def gates(
        self,
        company_id: str | None = None,
        lifecycle_stage: str | None = None,
        decision: str | None = None,
    ) -> list[RiskGate]:
        gates = self.workflow(company_id=company_id).gates
        return [
            gate
            for gate in gates
            if (not lifecycle_stage or gate.lifecycle_stage == lifecycle_stage)
            and (not decision or gate.decision == decision)
        ]

    def gate(self, gate_id: str, company_id: str | None = None) -> RiskGate:
        return self._find(self.workflow(company_id=company_id).gates, "gate_id", gate_id, "risk gate")

    def update_gate_check(
        self, gate_id: str, check_id: str, update: GateCheckUpdate, changed_by: str, company_id: str | None = None,
    ) -> RiskGate:
        """Record one operational Gate-check outcome with append-only evidence history."""
        payload = self._payload()
        workflow = self._workflow_raw(payload, company_id)
        for index, raw_gate in enumerate(workflow.get("gates", [])):
            if raw_gate.get("gate_id") != gate_id:
                continue
            gate = RiskGate.model_validate(raw_gate)
            check = next((item for item in gate.checks if item.check_id == check_id), None)
            if check is None:
                raise RiskWorkflowNotFoundError("gate check not found")
            now = datetime.now(timezone.utc)
            check.status = update.status
            check.evidence_refs = list(dict.fromkeys(update.evidence_refs))
            check.evidence_history.append({
                "status": update.status, "evidence_refs": check.evidence_refs,
                "note": update.note, "changed_by": changed_by, "changed_at": now.isoformat(),
            })
            gate.updated_at = now
            workflow["gates"][index] = gate.model_dump(mode="json")
            self.repository.save_payload(payload)
            return gate
        raise RiskWorkflowNotFoundError("risk gate not found")

    def gate_blockers(self, gate_id: str, decision: str = "approved", company_id: str | None = None) -> list[WorkflowBlocker]:
        workflow = self.workflow(company_id=company_id)
        gate = self._find(workflow.gates, "gate_id", gate_id, "risk gate")
        blockers = [WorkflowBlocker(
            code="GATE_CHECK_MISSING", message=f"核验项未完成：{check.title}",
            target_type="gate_check", target_id=check.check_id,
            remediation="补充并核验该准入条件的证据。",
        ) for check in gate.checks if check.status == "missing"]
        linked_risk_ids = set(gate.risk_item_ids)
        linked_tasks = [task for task in workflow.remediation_tasks if task.risk_id in linked_risk_ids]
        reviews = {review.review_id: review for review in workflow.manual_reviews}
        if decision == "approved":
            blockers.extend(WorkflowBlocker(
                code="REMEDIATION_TASK_UNVERIFIED", message=f"整改任务未验证：{task.title}",
                target_type="remediation_task", target_id=task.task_id,
                remediation="完成整改并提交人工复核。",
            ) for task in linked_tasks if task.status != "verified")
            blockers.extend(
                WorkflowBlocker(
                    code="REMEDIATION_REVIEW_UNAPPROVED", message=f"整改任务复核未批准：{task.title}",
                    target_type="manual_review", target_id=task.review_id or task.task_id,
                    remediation="由具备复核权限且非任务责任人的人员完成复核。",
                )
                for task in linked_tasks
                if task.requires_manual_review and (not task.review_id or reviews.get(task.review_id) is None or reviews[task.review_id].status != "approved")
            )
        elif decision == "conditional_approval":
            risks = [risk for risk in workflow.risk_items if risk.risk_id in linked_risk_ids]
            blockers.extend(
                WorkflowBlocker(
                    code="HIGH_RISK_CONDITIONAL_APPROVAL", message=f"高风险事项不可附条件放行：{risk.title}",
                    target_type="risk_item", target_id=risk.risk_id,
                    remediation="完成整改与正式核验后再申请批准。",
                )
                for risk in risks
                if risk.risk_level in {"high", "critical"} and risk.status != "closed"
            )
        return blockers

    def record_gate_decision(self, gate_id: str, update: GateDecisionUpdate, company_id: str | None = None) -> RiskGate:
        """Record an explicit human gate decision after evaluating workflow blockers."""
        payload = self._payload()
        workflow = self._workflow_raw(payload, company_id)
        gates = workflow.get("gates", [])
        for index, raw_gate in enumerate(gates):
            if raw_gate.get("gate_id") != gate_id:
                continue
            blockers = self.gate_blockers(gate_id, update.decision, company_id)
            if update.decision in {"approved", "conditional_approval"} and blockers:
                raise RiskWorkflowStateError("; ".join(blocker.message for blocker in blockers), blockers)
            now = datetime.now(timezone.utc)
            gate = RiskGate.model_validate(raw_gate)
            gate.decision = update.decision
            gate.updated_at = now
            gate.decision_history.append(
                RiskGateDecisionEvent(
                    decision=update.decision,
                    decided_at=now,
                    reviewer=update.reviewer,
                    conclusion=update.conclusion,
                )
            )
            gates[index] = gate.model_dump(mode="json")
            if gate.review_id:
                review = next((item for item in workflow.get("manual_reviews", []) if item.get("review_id") == gate.review_id), None)
                if review is not None:
                    review_status = {
                        "approved": "approved",
                        "conditional_approval": "approved",
                        "rectification_required": "changes_requested",
                        "suspended": "rejected",
                    }[update.decision]
                    review["status"] = review_status
                    review["reviewer"] = update.reviewer
                    review["conclusion"] = update.conclusion
                    review["reviewed_at"] = now.isoformat()
                    review.setdefault("decision_history", []).append({
                        "status": review_status,
                        "changed_at": now.isoformat(),
                        "reviewer": update.reviewer,
                        "conclusion": update.conclusion,
                    })
            self.repository.save_payload(payload)
            return gate
        raise RiskWorkflowNotFoundError(f"risk gate not found: {gate_id}")

    def risk_closure_blockers(self, risk_id: str, company_id: str | None = None) -> list[WorkflowBlocker]:
        workflow = self.workflow(company_id=company_id)
        risk = self._find(workflow.risk_items, "risk_id", risk_id, "risk item")
        tasks = [task for task in workflow.remediation_tasks if task.risk_id == risk.risk_id]
        reviews = {review.review_id: review for review in workflow.manual_reviews}
        gates = [gate for gate in workflow.gates if risk.risk_id in gate.risk_item_ids]
        blockers = [WorkflowBlocker(
            code="REMEDIATION_TASK_UNVERIFIED", message=f"整改任务未验证：{task.title}",
            target_type="remediation_task", target_id=task.task_id,
            remediation="完成整改并提交人工复核。",
        ) for task in tasks if task.status != "verified"]
        blockers.extend(
            WorkflowBlocker(
                code="REMEDIATION_REVIEW_UNAPPROVED", message=f"整改任务复核未批准：{task.title}",
                target_type="manual_review", target_id=task.review_id or task.task_id,
                remediation="由具备复核权限且非任务责任人的人员完成复核。",
            )
            for task in tasks
            if task.requires_manual_review and (not task.review_id or reviews.get(task.review_id) is None or reviews[task.review_id].status != "approved")
        )
        blockers.extend(WorkflowBlocker(
            code="RELATED_GATE_NOT_APPROVED", message=f"关联闸门未通过：{gate.title}",
            target_type="risk_gate", target_id=gate.gate_id,
            remediation="完成关联闸门的证据核验与正式批准。",
        ) for gate in gates if gate.decision != "approved")
        blockers.extend(
            WorkflowBlocker(
                code="GATE_REVIEW_UNAPPROVED", message=f"关联闸门复核未批准：{gate.title}",
                target_type="manual_review", target_id=gate.review_id or gate.gate_id,
                remediation="由授权决策人记录闸门复核结论。",
            )
            for gate in gates
            if not gate.review_id or reviews.get(gate.review_id) is None or reviews[gate.review_id].status != "approved"
        )
        return blockers

    def close_risk(self, risk_id: str, update: RiskClosureUpdate, company_id: str | None = None) -> RiskItem:
        payload = self._payload()
        risks = self._workflow_raw(payload, company_id).get("risk_items", [])
        for index, raw_risk in enumerate(risks):
            if raw_risk.get("risk_id") != risk_id:
                continue
            blockers = self.risk_closure_blockers(risk_id, company_id)
            if blockers:
                raise RiskWorkflowStateError("; ".join(blocker.message for blocker in blockers), blockers)
            now = datetime.now(timezone.utc)
            risk = RiskItem.model_validate(raw_risk)
            risk.status = "closed"
            risk.updated_at = now
            risk.status_history.append(RiskItemStatusEvent(
                status="closed", changed_at=now, changed_by=update.reviewer, note=update.conclusion,
            ))
            risks[index] = risk.model_dump(mode="json")
            self.repository.save_payload(payload)
            return risk
        raise RiskWorkflowNotFoundError(f"risk item not found: {risk_id}")

    def remediation_tasks(
        self,
        company_id: str | None = None,
        risk_id: str | None = None,
        status: str | None = None,
        owner: str | None = None,
    ) -> list[RemediationTask]:
        tasks = self.workflow(company_id=company_id).remediation_tasks
        return [
            task
            for task in tasks
            if (not risk_id or task.risk_id == risk_id)
            and (not status or task.status == status)
            and (not owner or task.owner == owner)
        ]

    def tasks(
        self,
        company_id: str | None = None,
        risk_id: str | None = None,
        status: str | None = None,
        owner: str | None = None,
    ) -> list[RemediationTask]:
        return self.remediation_tasks(
            company_id=company_id,
            risk_id=risk_id,
            status=status,
            owner=owner,
        )

    def remediation_task(self, task_id: str, company_id: str | None = None) -> RemediationTask:
        return self._find(self.workflow(company_id=company_id).remediation_tasks, "task_id", task_id, "remediation task")

    def management_assistance(self, company_id: str | None = None) -> tuple[list[RemediationSuggestion], list[ReminderRecord]]:
        workflow = self.workflow(company_id=company_id)
        return workflow.remediation_suggestions, workflow.reminders

    def refresh_management_assistance(self, company_id: str | None = None) -> tuple[list[RemediationSuggestion], list[ReminderRecord]]:
        """Create reviewable suggestions and reminders without changing risk or task state."""
        payload = self._payload()
        workflow = self._workflow_raw(payload, company_id)
        now = datetime.now(timezone.utc)
        today = now.date()
        suggestions = workflow.setdefault("remediation_suggestions", [])
        reminders = workflow.setdefault("reminders", [])
        existing_suggestion_risks = {
            item.get("risk_id") for item in suggestions if item.get("status") == "pending"
        }
        existing_reminders = {item.get("idempotency_key") for item in reminders}

        for raw_risk in workflow.get("risk_items", []):
            risk = RiskItem.model_validate(raw_risk)
            if risk.status == "closed":
                continue
            if risk.missing_materials and risk.risk_id not in existing_suggestion_risks:
                due_days = 7 if risk.risk_level in {"high", "critical"} else 14
                suggestion = RemediationSuggestion(
                    suggestion_id=f"suggestion-{uuid4().hex[:12]}",
                    company_id=risk.company_id,
                    risk_id=risk.risk_id,
                    project_id=risk.project_id,
                    title=f"补齐{risk.title}的处理安排",
                    suggested_action="核对缺失材料并决定是否建立整改任务",
                    suggested_owner_role=_suggested_owner_role(risk.risk_domain),
                    suggested_due_date=today + timedelta(days=due_days),
                    missing_materials=list(risk.missing_materials),
                    basis=[f"风险等级：{risk.risk_level}", *risk.missing_materials],
                    generated_at=now,
                )
                suggestions.append(suggestion.model_dump(mode="json"))
            if risk.missing_materials:
                self._append_reminder_if_new(
                    reminders,
                    existing_reminders,
                    company_id=risk.company_id,
                    target_type="risk_item",
                    target_id=risk.risk_id,
                    reminder_type="missing_material",
                    title=f"待补材料：{risk.title}",
                    detail="、".join(risk.missing_materials),
                    now=now,
                )

        for raw_task in workflow.get("remediation_tasks", []):
            task = RemediationTask.model_validate(raw_task)
            if task.status in {"verified"}:
                continue
            if task.status == "blocked":
                self._append_reminder_if_new(
                    reminders, existing_reminders, company_id=task.company_id,
                    target_type="remediation_task", target_id=task.task_id,
                    reminder_type="blocked", title=f"整改受阻：{task.title}",
                    detail="请由责任人说明阻塞原因并决定后续安排。", now=now,
                )
            try:
                due_date = date.fromisoformat(task.due_date)
            except ValueError:
                continue
            reminder_type = "overdue" if due_date < today else "due_soon" if due_date <= today + timedelta(days=3) else None
            if reminder_type:
                self._append_reminder_if_new(
                    reminders, existing_reminders, company_id=task.company_id,
                    target_type="remediation_task", target_id=task.task_id,
                    reminder_type=reminder_type, title=f"{'已逾期' if reminder_type == 'overdue' else '临近到期'}：{task.title}",
                    detail=f"计划完成日期：{task.due_date}。系统仅提示，不改变任务状态。", now=now,
                )
        self.repository.save_payload(payload)
        refreshed = InternalRiskWorkflow.model_validate(copy.deepcopy(workflow))
        return refreshed.remediation_suggestions, refreshed.reminders

    @staticmethod
    def _append_reminder_if_new(
        reminders: list[dict],
        known_keys: set[str],
        *,
        company_id: str,
        target_type: str,
        target_id: str,
        reminder_type: str,
        title: str,
        detail: str,
        now: datetime,
    ) -> None:
        key = f"{company_id}:{target_type}:{target_id}:{reminder_type}:management-assistance-v1"
        if key in known_keys:
            return
        reminders.append(ReminderRecord(
            reminder_id=f"reminder-{uuid4().hex[:12]}", company_id=company_id,
            target_type=target_type, target_id=target_id, reminder_type=reminder_type,
            title=title, detail=detail, triggered_at=now, idempotency_key=key,
        ).model_dump(mode="json"))
        known_keys.add(key)

    def adopt_remediation_suggestion(self, suggestion_id: str, request: SuggestionAdoptionRequest, company_id: str | None = None) -> RemediationSuggestion:
        payload = self._payload()
        workflow = self._workflow_raw(payload, company_id)
        suggestions = workflow.setdefault("remediation_suggestions", [])
        for index, raw_suggestion in enumerate(suggestions):
            if raw_suggestion.get("suggestion_id") != suggestion_id:
                continue
            suggestion = RemediationSuggestion.model_validate(raw_suggestion)
            if suggestion.status != "pending":
                raise RiskWorkflowStateError("only a pending remediation suggestion can be adopted")
            risk = self._find(
                [RiskItem.model_validate(item) for item in workflow.get("risk_items", [])],
                "risk_id", suggestion.risk_id, "risk item",
            )
            now = datetime.now(timezone.utc)
            task = RemediationTask(
                task_id=f"task-{uuid4().hex[:12]}", company_id=suggestion.company_id,
                project_id=suggestion.project_id, risk_id=suggestion.risk_id,
                title=suggestion.title, owner=request.owner,
                due_date=(request.due_date or suggestion.suggested_due_date).isoformat(),
                updated_at=now,
                status_history=[RemediationTaskStatusEvent(
                    status="not_started", changed_at=now, changed_by=request.adopted_by,
                    note=f"采纳系统整改建议（{suggestion.suggestion_id}）。",
                )],
            )
            workflow.setdefault("remediation_tasks", []).append(task.model_dump(mode="json"))
            for risk_index, raw_risk in enumerate(workflow.get("risk_items", [])):
                if raw_risk.get("risk_id") == risk.risk_id:
                    raw_risk.setdefault("task_ids", []).append(task.task_id)
                    workflow["risk_items"][risk_index] = raw_risk
                    break
            suggestion.status = "adopted"
            suggestion.adopted_by = request.adopted_by
            suggestion.adopted_at = now
            suggestion.task_id = task.task_id
            suggestions[index] = suggestion.model_dump(mode="json")
            self.repository.save_payload(payload)
            return suggestion
        raise RiskWorkflowNotFoundError(f"remediation suggestion not found: {suggestion_id}")

    def acknowledge_reminder(self, reminder_id: str, request: ReminderAcknowledgementRequest, company_id: str | None = None) -> ReminderRecord:
        payload = self._payload()
        reminders = self._workflow_raw(payload, company_id).setdefault("reminders", [])
        for index, raw_reminder in enumerate(reminders):
            if raw_reminder.get("reminder_id") != reminder_id:
                continue
            reminder = ReminderRecord.model_validate(raw_reminder)
            if reminder.status != "active":
                raise RiskWorkflowStateError("only an active reminder can be acknowledged")
            reminder.status = "acknowledged"
            reminder.acknowledged_by = request.acknowledged_by
            reminder.acknowledged_at = datetime.now(timezone.utc)
            reminders[index] = reminder.model_dump(mode="json")
            self.repository.save_payload(payload)
            return reminder
        raise RiskWorkflowNotFoundError(f"reminder not found: {reminder_id}")

    def create_risk_acceptance(self, risk_id: str, request: RiskAcceptanceCreate, company_id: str | None = None) -> RiskAcceptance:
        """Record a proposed residual-risk acceptance; it is ineffective until a second person approves it."""
        if request.review_on > request.expires_on:
            raise RiskWorkflowStateError("risk acceptance review date must not be after its expiry date")
        payload = self._payload()
        workflow = self._workflow_raw(payload, company_id)
        risk = self._find(
            [RiskItem.model_validate(item) for item in workflow.get("risk_items", [])],
            "risk_id", risk_id, "risk item",
        )
        if risk.status == "closed":
            raise RiskWorkflowStateError("a closed risk cannot receive a new risk acceptance")
        now = datetime.now(timezone.utc)
        acceptance = RiskAcceptance(
            acceptance_id=f"acceptance-{uuid4().hex[:12]}", company_id=risk.company_id,
            risk_id=risk.risk_id, decision_maker=request.decision_maker,
            decision_role=request.decision_role, rationale=request.rationale,
            compensating_controls=list(dict.fromkeys(request.compensating_controls)),
            expires_on=request.expires_on, review_on=request.review_on, created_at=now,
        )
        workflow.setdefault("risk_acceptances", []).append(acceptance.model_dump(mode="json"))
        self.repository.save_payload(payload)
        return acceptance

    def approve_risk_acceptance(self, acceptance_id: str, request: RiskAcceptanceApprovalRequest, company_id: str | None = None) -> RiskAcceptance:
        payload = self._payload()
        acceptances = self._workflow_raw(payload, company_id).setdefault("risk_acceptances", [])
        for index, raw_acceptance in enumerate(acceptances):
            if raw_acceptance.get("acceptance_id") != acceptance_id:
                continue
            acceptance = RiskAcceptance.model_validate(raw_acceptance)
            if acceptance.status != "pending_approval":
                raise RiskWorkflowStateError("only a pending risk acceptance can be approved")
            if acceptance.decision_maker == request.approved_by:
                raise RiskWorkflowStateError("risk acceptance requires approval by a different authorized decision maker")
            if acceptance.expires_on < datetime.now(timezone.utc).date():
                acceptance.status = "expired"
            else:
                acceptance.status = "accepted"
                acceptance.approved_by = request.approved_by
                acceptance.approved_at = datetime.now(timezone.utc)
            acceptances[index] = acceptance.model_dump(mode="json")
            self.repository.save_payload(payload)
            return acceptance
        raise RiskWorkflowNotFoundError(f"risk acceptance not found: {acceptance_id}")

    def add_task_evidence(self, task_id: str, update: TaskEvidenceUpdate, company_id: str | None = None) -> RemediationTask:
        """Attach evidence references without advancing the remediation state."""
        payload = self._payload()
        tasks = self._workflow_raw(payload, company_id).get("remediation_tasks", [])
        for index, raw_task in enumerate(tasks):
            if raw_task.get("task_id") != task_id:
                continue
            now = datetime.now(timezone.utc)
            task = RemediationTask.model_validate(raw_task)
            task.evidence_refs = list(dict.fromkeys([*task.evidence_refs, *update.evidence_refs]))
            task.updated_at = now
            task.status_history.append(
                RemediationTaskStatusEvent(
                    status=task.status,
                    changed_at=now,
                    changed_by=update.changed_by,
                    note=update.note or "Evidence reference attached to remediation task.",
                )
            )
            tasks[index] = task.model_dump(mode="json")
            self.repository.save_payload(payload)
            return task
        raise RiskWorkflowNotFoundError(f"remediation task not found: {task_id}")

    def references_document(self, document_task_id: str, company_id: str | None = None) -> bool:
        return any(
            document_task_id in task.evidence_refs
            for task in self.workflow(company_id=company_id).remediation_tasks
        )

    def manual_reviews(
        self,
        company_id: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        status: str | None = None,
    ) -> list[ManualReview]:
        reviews = self.workflow(company_id=company_id).manual_reviews
        return [
            review
            for review in reviews
            if (not target_type or review.target_type == target_type)
            and (not target_id or review.target_id == target_id)
            and (not status or review.status == status)
        ]

    def manual_review(self, review_id: str, company_id: str | None = None) -> ManualReview:
        return self._find(self.workflow(company_id=company_id).manual_reviews, "review_id", review_id, "manual review")

    def record_manual_review_decision(
        self,
        review_id: str,
        update: ManualReviewDecisionUpdate,
        company_id: str | None = None,
    ) -> ManualReview:
        """Record a human decision and only then advance or reopen its remediation task."""
        payload = self._payload()
        workflow = self._workflow_raw(payload, company_id)
        reviews = workflow.get("manual_reviews", [])
        for review_index, raw_review in enumerate(reviews):
            if raw_review.get("review_id") != review_id:
                continue
            review = ManualReview.model_validate(raw_review)
            if review.status != "pending":
                raise RiskWorkflowStateError("a manual review decision can only be recorded once")
            if review.target_type != "remediation_task":
                raise RiskWorkflowStateError(
                    "gate and risk-item reviews require a role-scoped decision workflow"
                )

            tasks = workflow.get("remediation_tasks", [])
            task = next((item for item in tasks if item.get("task_id") == review.target_id), None)
            if task is None:
                raise RiskWorkflowNotFoundError(f"remediation task not found for review: {review.target_id}")
            if task.get("status") != "pending_review":
                raise RiskWorkflowStateError(
                    "a remediation task must be pending_review before a human decision is recorded"
                )

            related_risk = next(
                (item for item in workflow.get("risk_items", []) if item.get("risk_id") == task.get("risk_id")),
                None,
            )
            if related_risk and related_risk.get("risk_level") in {"high", "critical"} and task.get("owner") == update.reviewer:
                raise RiskWorkflowStateError("high and critical remediation tasks require a reviewer other than the task owner")
            if not task.get("evidence_refs"):
                raise RiskWorkflowStateError("a remediation task needs evidence before a manual review")

            now = datetime.now(timezone.utc)
            review.status = update.status
            review.reviewer = update.reviewer
            review.conclusion = update.conclusion
            review.reviewed_at = now
            evidence_refs = sorted(str(item) for item in task.get("evidence_refs", []))
            evidence_hash = hashlib.sha256("\n".join(evidence_refs).encode("utf-8")).hexdigest()
            review.evidence_snapshot = EvidenceSnapshot(
                evidence_refs=evidence_refs,
                evidence_hash=evidence_hash,
                submitted_by=task.get("status_history", [{}])[-1].get("changed_by", "unknown"),
                submitted_at=now,
            )
            review.decision_history.append(
                ManualReviewDecisionEvent(
                    status=update.status,
                    changed_at=now,
                    reviewer=update.reviewer,
                    conclusion=update.conclusion,
                )
            )
            reviews[review_index] = review.model_dump(mode="json")

            updated_task = RemediationTask.model_validate(task)
            updated_task.status = MANUAL_REVIEW_DECISION_TASK_STATUS[update.status]
            updated_task.updated_at = now
            updated_task.status_history.append(
                RemediationTaskStatusEvent(
                    status=updated_task.status,
                    changed_at=now,
                    changed_by=update.reviewer,
                    note=f"Manual review decision: {update.status}. {update.conclusion}",
                )
            )
            task_index = tasks.index(task)
            tasks[task_index] = updated_task.model_dump(mode="json")
            self.repository.save_payload(payload)
            return review
        raise RiskWorkflowNotFoundError(f"manual review not found: {review_id}")

    def update_task_status(self, task_id: str, update: TaskStatusUpdate, company_id: str | None = None) -> RemediationTask:
        payload = self._payload()
        tasks = self._workflow_raw(payload, company_id).get("remediation_tasks", [])
        for index, raw_task in enumerate(tasks):
            if raw_task.get("task_id") != task_id:
                continue
            now = datetime.now(timezone.utc)
            updated_task = RemediationTask.model_validate(raw_task)
            if update.status != updated_task.status and update.status not in TASK_STATUS_TRANSITIONS[updated_task.status]:
                raise RiskWorkflowStateError(
                    f"task status cannot transition from {updated_task.status} to {update.status}"
                )
            next_evidence_refs = list(update.evidence_refs) if update.evidence_refs is not None else updated_task.evidence_refs
            if update.status == "pending_review" and not next_evidence_refs:
                raise RiskWorkflowStateError(
                    "a remediation task needs at least one evidence reference before pending_review"
                )
            updated_task.status = update.status
            updated_task.updated_at = now
            if update.evidence_refs is not None:
                updated_task.evidence_refs = list(dict.fromkeys(update.evidence_refs))
            updated_task.status_history.append(
                RemediationTaskStatusEvent(
                    status=update.status,
                    changed_at=now,
                    changed_by=update.changed_by,
                    note=update.note,
                )
            )
            tasks[index] = updated_task.model_dump(mode="json")
            self.repository.save_payload(payload)
            return updated_task
        raise RiskWorkflowNotFoundError(f"remediation task not found: {task_id}")

    @staticmethod
    def _find(items: list, key: str, value: str, label: str):
        for item in items:
            if getattr(item, key) == value:
                return item
        raise RiskWorkflowNotFoundError(f"{label} not found: {value}")


def _suggested_owner_role(risk_domain: str) -> str:
    return {
        "data_model_governance": "数据与安全负责人",
        "technology_ip": "研发与知识产权负责人",
        "product_commercialization": "产品与法务负责人",
        "cross_border_supply_chain": "供应链与合规负责人",
        "corporate_finance_governance": "财务与治理负责人",
    }.get(risk_domain, "风险管理负责人")
