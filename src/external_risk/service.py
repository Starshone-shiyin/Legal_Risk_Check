from __future__ import annotations

import copy
import hashlib
import json
import re
import threading
from pathlib import Path
from typing import Any
from datetime import datetime, timezone

from src.external_risk.repository import (
    FixtureExternalRiskRepository,
    ExternalRiskDataError,
    ExternalRiskRepository,
)
from src.external_risk.providers import provider_statuses
from src.external_risk.commodity_catalog import CATALOG_BY_SYMBOL, catalog_display_name
from src.external_risk.intelligence import NewsPolicyRssExternalRiskProvider
from src.external_risk.provider_config import ExternalRiskProviderConfig, load_provider_config
from src.external_risk.providers import (
    AkShareExternalRiskProvider,
    CompositeExternalSignalProvider,
    ExternalSignalProvider,
    TencentHttpExternalRiskProvider,
)
from src.external_risk.schemas import (
    ExternalRiskContext,
    ExternalRiskDataQuality,
    ExternalRiskChainAlert,
    ExternalRiskDashboardSummary,
    ExternalRiskIntelligenceStatus,
    ExternalRiskMarketDashboard,
    ExternalRiskProviderStatus,
    ExternalRiskWorkflowGraph,
    ExternalRiskRelationshipProjection,
    ExternalRiskSupplyChainSync,
    ExternalRiskSupplyChainSyncItem,
    ExternalRiskWorkflowMergeRequest,
    ExternalRiskQuoteSeries,
    ExternalRiskSignal,
    LegalQueryPlan,
    LegalQueryTask,
    TechCompanyRiskFinding,
)
from src.supply_chain.repository import SupplyChainRepository

__all__ = ["ExternalRiskDataError", "ExternalRiskService"]


class ExternalRiskWorkflowConflictError(ExternalRiskDataError):
    """Raised when a canvas is saved from an out-of-date workflow revision."""

    def __init__(self, message: str, *, current_graph: ExternalRiskWorkflowGraph, diff: dict[str, Any]) -> None:
        super().__init__(message)
        self.current_graph = current_graph
        self.diff = diff


_WORKFLOW_GRAPH_LOCK = threading.RLock()


class ExternalRiskService:
    """Read-only foundation for market, commodity, supply-chain, and tech risk signals."""

    def __init__(
        self,
        repository: ExternalRiskRepository | Path | None = None,
        live_provider: ExternalSignalProvider | None = None,
        intelligence_provider: NewsPolicyRssExternalRiskProvider | None = None,
        supply_chain_repository: SupplyChainRepository | None = None,
    ) -> None:
        if repository is None:
            self.repository = FixtureExternalRiskRepository()
        elif isinstance(repository, Path):
            self.repository = FixtureExternalRiskRepository(repository)
        else:
            self.repository = repository
        self.live_provider = live_provider
        self.intelligence_provider = intelligence_provider
        self._intelligence_provider_instance = intelligence_provider
        self._intelligence_provider_config: ExternalRiskProviderConfig | None = None
        self._live_provider_instance = live_provider
        self._live_provider_config: ExternalRiskProviderConfig | None = None
        self._last_live_provider_status: ExternalRiskProviderStatus | None = None
        self.supply_chain_repository = supply_chain_repository or SupplyChainRepository()

    def _payload(self) -> dict[str, Any]:
        return self.repository.load_payload()

    def context(self, company_id: str | None = None, as_of: str | None = None) -> ExternalRiskContext:
        payload = copy.deepcopy(self._payload())
        context = payload.get("context")
        if not isinstance(context, dict):
            raise ExternalRiskDataError("external risk fixture missing context")
        if company_id and context.get("company", {}).get("company_id") != company_id:
            context = {
                **context,
                "company": {
                    **context.get("company", {}),
                    "company_id": company_id,
                    "name": context.get("company", {}).get("name", "未配置企业"),
                },
            }
        if as_of:
            context["as_of"] = as_of
        return ExternalRiskContext(**context)

    def signals(
        self,
        company_id: str | None = None,
        signal_type: str | None = None,
        severity: str | None = None,
    ) -> list[ExternalRiskSignal]:
        context = self.context(company_id=company_id)
        signals = context.signals
        if signal_type:
            signals = [signal for signal in signals if signal.signal_type == signal_type]
        if severity:
            signals = [signal for signal in signals if signal.severity == severity]
        return signals

    def findings(
        self,
        company_id: str | None = None,
        risk_domain: str | None = None,
        severity: str | None = None,
    ) -> list[TechCompanyRiskFinding]:
        context = self.context(company_id=company_id)
        findings = context.findings
        if risk_domain:
            findings = [finding for finding in findings if finding.risk_domain == risk_domain]
        if severity:
            findings = [finding for finding in findings if finding.severity == severity]
        return findings

    def legal_query_plan(
        self,
        company_id: str | None = None,
        risk_domain: str | None = None,
        severity: str | None = None,
        include_live: bool = True,
        live_signals: list[ExternalRiskSignal] | None = None,
    ) -> LegalQueryPlan:
        context = self.context(company_id=company_id)
        findings = context.findings
        if risk_domain:
            findings = [finding for finding in findings if finding.risk_domain == risk_domain]
        if severity:
            findings = [finding for finding in findings if finding.severity == severity]
        signal_by_id = {signal.signal_id: signal for signal in context.signals}
        tasks: list[LegalQueryTask] = []
        for finding in findings:
            triggered_signals = [
                signal_by_id[signal_id]
                for signal_id in finding.triggering_signal_ids
                if signal_id in signal_by_id
            ]
            fact_background = _fact_background(finding, triggered_signals)
            for index, query in enumerate(finding.legal_query_seeds, start=1):
                tasks.append(
                    LegalQueryTask(
                        task_id=f"{finding.finding_id}-query-{index:02d}",
                        finding_id=finding.finding_id,
                        risk_domain=finding.risk_domain,
                        severity=finding.severity,
                        query=query,
                        fact_background=fact_background,
                        triggering_signal_ids=finding.triggering_signal_ids,
                        evidence_refs=[signal.signal_id for signal in triggered_signals],
                        suggested_filters=_suggested_filters(finding.risk_domain),
                    )
                )
        if include_live:
            current_live_signals = live_signals if live_signals is not None else self.live_signals(provider="composite")
            tasks = [
                *_live_signal_legal_query_tasks(
                    current_live_signals,
                    risk_domain=risk_domain,
                    severity=severity,
                ),
                *tasks,
            ]
        return LegalQueryPlan(
            company=context.company,
            as_of=context.as_of,
            tasks=tasks,
            guardrails=[
                "外部行情、商品期货、供应链和政策信号只作为事实背景，不作为法律依据。",
                "每个查询任务必须由法律 RAG 重新检索法规、监管规则或合同依据。",
                "报告中应保留 signal_id、as_of、source 和 confidence，便于复核事实快照。",
                "仅风险域单点匹配的市场或关系信号不得自动创建法律任务；需补充受控确认或权威法规事件。",
            ],
        )

    def provider_statuses(self) -> list[ExternalRiskProviderStatus]:
        statuses = provider_statuses(intelligence_provider=self._intelligence_provider())
        # Keep the UI honest about the request just made.  The former
        # implementation rebuilt providers for this status call, resetting
        # their ``runtime_access`` to ``not_called`` after a live refresh.
        live_provider = self._live_provider()
        if isinstance(live_provider, CompositeExternalSignalProvider):
            actual = {provider.provider_id: provider.status() for provider in live_provider.providers}
            statuses = [actual.get(item.provider_id, item) for item in statuses]
        return statuses

    def live_provider_status(self) -> ExternalRiskProviderStatus:
        return self._last_live_provider_status or self._live_provider().status()

    def intelligence_provider_status(self) -> ExternalRiskProviderStatus:
        return self._intelligence_provider().status()

    def intelligence_status(self) -> ExternalRiskIntelligenceStatus:
        return self._intelligence_provider().intelligence_status()

    def live_signals(
        self,
        provider: str = "composite",
        signal_type: str | None = None,
        symbol: str | None = None,
        commodity_group: str | None = None,
    ) -> list[ExternalRiskSignal]:
        if provider not in {"composite", "http", "tencent", "akshare", "news_policy"}:
            return []
        selected_provider = self._live_provider()
        if provider == "akshare":
            selected_provider = AkShareExternalRiskProvider()
        elif provider in {"http", "tencent"}:
            selected_provider = TencentHttpExternalRiskProvider()
        elif provider == "news_policy":
            selected_provider = self._intelligence_provider()
        signals = selected_provider.live_signals(
            signal_type=signal_type,
            symbol=symbol,
            commodity_group=commodity_group,
        )
        self._last_live_provider_status = selected_provider.status()
        return signals

    def refresh_intelligence(self) -> list[ExternalRiskSignal]:
        return self._intelligence_provider().refresh()

    def poll_intelligence(self) -> list[ExternalRiskSignal]:
        return self._intelligence_provider().live_signals()

    def reload_runtime_configuration(self) -> None:
        """Recreate cached provider state after local runtime settings change."""
        if self.intelligence_provider is None:
            self._intelligence_provider_instance = None
            self._intelligence_provider_config = None
        if self.live_provider is None:
            self._live_provider_instance = None
            self._live_provider_config = None
        self._last_live_provider_status = None

    def _live_provider(self) -> ExternalSignalProvider:
        if self.live_provider is not None:
            return self.live_provider
        config = load_provider_config()
        if self._live_provider_instance is None or self._live_provider_config != config:
            self._live_provider_instance = CompositeExternalSignalProvider(
                [
                    TencentHttpExternalRiskProvider(config),
                    AkShareExternalRiskProvider(config),
                    self._intelligence_provider(),
                ]
            )
            self._live_provider_config = config
            self._last_live_provider_status = None
        return self._live_provider_instance

    def _intelligence_provider(self) -> NewsPolicyRssExternalRiskProvider:
        if self.intelligence_provider is not None:
            return self.intelligence_provider
        config = load_provider_config()
        if self._intelligence_provider_instance is None or self._intelligence_provider_config != config:
            self._intelligence_provider_instance = NewsPolicyRssExternalRiskProvider(config)
            self._intelligence_provider_config = config
        return self._intelligence_provider_instance

    def market_dashboard(
        self,
        company_id: str | None = None,
        include_live: bool = True,
        limit: int = 12,
    ) -> ExternalRiskMarketDashboard:
        context = self.context(company_id=company_id)
        provider_signals = self.live_signals(provider="composite") if include_live else []
        try:
            graph = self.workflow_graph()
        except ExternalRiskDataError:
            # A corrupted optional canvas must not hide otherwise reviewable
            # provider evidence; its absence simply removes graph matching.
            graph = ExternalRiskWorkflowGraph()
        live_signals = _relevant_live_signals(provider_signals, context.company, graph)
        market_observations = _broad_supply_chain_observations(
            provider_signals,
            excluded_signal_ids={signal.signal_id for signal in live_signals},
        )
        # Market data must only contain reviewable provider output. Fixtures remain
        # available to their dedicated context and legal-reference endpoints.
        merged_signals = _dedupe_signals(live_signals)
        sorted_signals = sorted(
            merged_signals,
            # The dashboard is a live watchlist: the newest observation must
            # surface even when an older item has a higher severity.
            key=_dashboard_signal_priority,
            reverse=True,
        )[: max(1, limit)]
        live_tasks = _live_signal_legal_query_tasks(live_signals)
        provider_statuses = self.provider_statuses()
        intelligence_status = self.intelligence_status()
        live_status = self.live_provider_status()
        live_signal_count = len(merged_signals)
        high_or_above_count = len(
            [signal for signal in sorted_signals if signal.severity in {"high", "critical"}]
        )
        chain_alerts = _chain_alerts(merged_signals, graph)
        # The score uses every current signal; the UI limit must not change the risk result.
        risk_profile = _risk_coefficient_profile(merged_signals, chain_alerts=chain_alerts)
        risk_coefficient = risk_profile["score"]
        data_mode = "live_provider" if live_signal_count else "unavailable_live_provider"
        provider_mode = "live" if live_signal_count or live_status.mode == "live" else "disabled"
        summary = ExternalRiskDashboardSummary(
            headline=_dashboard_headline(sorted_signals, live_signal_count),
            signal_count=len(sorted_signals),
            live_signal_count=live_signal_count,
            high_or_above_count=high_or_above_count,
            legal_task_count=len(live_tasks),
            risk_coefficient=risk_coefficient,
            risk_coefficient_level=_risk_coefficient_level(risk_coefficient),
            risk_coefficient_formula=(
                r"R=100\left(0.22S+0.20M+0.16T+0.16C+0.14L+0.12P\right),"
                r"\quad S=1-\prod_i\left(1-c_ir_i s_i\right),"
                r"\quad C=1-\prod_j\left(1-a_j\right)"
            ),
            risk_coefficient_components=risk_profile["components"],
            risk_coefficient_quality=risk_profile["quality"],
            provider_mode=provider_mode,  # type: ignore[arg-type]
            data_mode=data_mode,  # type: ignore[arg-type]
        )
        return ExternalRiskMarketDashboard(
            company=context.company,
            as_of=context.as_of,
            summary=summary,
            signals=sorted_signals,
            market_observations=market_observations[:12],
            chain_alerts=chain_alerts,
            findings=[],
            legal_query_tasks=live_tasks,
            provider_statuses=provider_statuses,
            intelligence_status=intelligence_status,
            data_quality=_dashboard_data_quality(
                graph=graph,
                live_status=live_status,
                intelligence_status=self.intelligence_provider_status(),
            ),
            guardrails=[
                "External market, commodity, supply-chain, and policy signals are factual context only, not legal authority.",
                "Every query task must retrieve applicable laws, regulatory rules, or contracts before legal conclusions are drawn.",
                "Keep signal_id, as_of, source, and confidence for each reviewable market fact.",
            ],
        )

    def quote_series(
        self,
        symbol: str = "sh000001",
        interval: str = "intraday",
    ) -> ExternalRiskQuoteSeries:
        normalized_interval = interval if interval in {"intraday", "daily", "weekly", "monthly"} else "intraday"
        provider = TencentHttpExternalRiskProvider()
        points, source = provider.quote_series(symbol=symbol, interval=normalized_interval)
        name = provider.quote_name(symbol) or _quote_name(symbol)
        quote_metadata = _quote_display_metadata(
            symbol=symbol,
            name=name,
            points=points,
            interval=normalized_interval,
        )
        return ExternalRiskQuoteSeries(
            symbol=symbol,
            name=name,
            provider=provider.provider_id,
            interval=normalized_interval,  # type: ignore[arg-type]
            source=source,  # type: ignore[arg-type]
            as_of=points[-1].time if points else "",
            points=points,
            **quote_metadata,
        )

    def workflow_graph(self) -> ExternalRiskWorkflowGraph:
        path = _workflow_graph_path()
        if not path.exists():
            return self._attach_supply_chain_sync(ExternalRiskWorkflowGraph(storage_path=str(path)))
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ExternalRiskDataError(f"external risk workflow graph is unreadable: {exc}") from exc
        graph = _hydrate_workflow_graph(ExternalRiskWorkflowGraph(**payload))
        graph.storage_path = str(path)
        return self._attach_supply_chain_sync(graph)

    def save_workflow_graph(self, graph: ExternalRiskWorkflowGraph) -> ExternalRiskWorkflowGraph:
        path = _workflow_graph_path()
        with _WORKFLOW_GRAPH_LOCK:
            current_revision = 0
            if path.exists():
                try:
                    current_payload = json.loads(path.read_text(encoding="utf-8"))
                    current_revision = int(current_payload.get("revision", 0))
                except (OSError, ValueError, json.JSONDecodeError) as exc:
                    raise ExternalRiskDataError(f"external risk workflow graph is unreadable: {exc}") from exc
            if graph.revision != current_revision:
                current = _hydrate_workflow_graph(ExternalRiskWorkflowGraph(**current_payload)) if path.exists() else ExternalRiskWorkflowGraph()
                current.storage_path = str(path)
                raise ExternalRiskWorkflowConflictError(
                    f"workflow revision conflict: expected {current_revision}, received {graph.revision}",
                    current_graph=current,
                    diff=_workflow_graph_diff(graph, current),
                )
            saved = _write_workflow_graph(path, graph, revision=current_revision + 1)
            return self._attach_supply_chain_sync(saved)

    def merge_workflow_graph(self, request: ExternalRiskWorkflowMergeRequest) -> ExternalRiskWorkflowGraph:
        """Merge a stale local draft only after an explicit named confirmation.

        The merge is additive: server-side nodes/relations which are absent
        from the draft are retained.  This prevents an old tab from silently
        deleting another user's work.  Destructive edits require a reload and
        a normal save against the current revision.
        """
        path = _workflow_graph_path()
        with _WORKFLOW_GRAPH_LOCK:
            current = self.workflow_graph()
            if request.base_revision >= current.revision:
                raise ExternalRiskDataError("workflow merge requires a stale draft revision")
            merged = _additive_workflow_merge(current, request.draft)
            now = datetime.now(timezone.utc).isoformat(timespec="seconds")
            merged.merge_audit = [
                *current.merge_audit[-49:],
                {
                    "merged_at": now,
                    "confirmed_by": request.confirmed_by.strip(),
                    "confirmation_note": request.confirmation_note.strip(),
                    "base_revision": request.base_revision,
                    "into_revision": current.revision,
                    "strategy": "additive_preserve_server_changes",
                },
            ]
            saved = _write_workflow_graph(path, merged, revision=current.revision + 1)
            return self._attach_supply_chain_sync(saved)

    def _attach_supply_chain_sync(self, graph: ExternalRiskWorkflowGraph) -> ExternalRiskWorkflowGraph:
        """Return current, auditable canvas-to-supplier-map synchronization state.

        The graph owns relationships; the supplier workspace owns supplier
        master data. A supplier node is synchronized only when its explicit
        ``supplier_id`` still exists in that master map. Supplier-shaped
        canvas nodes without an ID are deliberately surfaced as an action,
        never silently created as suppliers.
        """
        graph = graph.model_copy(deep=True)
        try:
            known_ids = {
                str(item.get("supplier_id") or "").strip()
                for item in self.supply_chain_repository.load()
                if str(item.get("supplier_id") or "").strip()
            }
        except (OSError, ValueError, json.JSONDecodeError):
            known_ids = set()
        bound = list(dict.fromkeys(graph.bound_supplier_ids))
        synchronized = [supplier_id for supplier_id in bound if supplier_id in known_ids]
        missing = [supplier_id for supplier_id in bound if supplier_id not in known_ids]
        unbound = [
            ExternalRiskSupplyChainSyncItem(
                node_id=node.id,
                symbol=node.symbol,
                name=node.name,
                category=node.group or node.lane,
            )
            for node in graph.nodes
            if node.node_kind == "supplier" and not node.supplier_id
        ]
        action_required = bool(missing or unbound)
        if action_required:
            parts: list[str] = []
            if synchronized:
                parts.append(f"已同步 {len(synchronized)} 个绑定供应链节点")
            if missing:
                parts.append(f"{len(missing)} 个绑定节点未在供应链地图中找到")
            if unbound:
                parts.append(f"{len(unbound)} 个画布供应商节点尚未绑定")
            message = "；".join(parts) + "。请前往供应链地图维护节点后再确认。"
        else:
            message = (
                f"已同步 {len(synchronized)} 个绑定供应链节点。"
                if synchronized else "当前画布没有需要同步的供应链节点。"
            )
        graph.supply_chain_sync = ExternalRiskSupplyChainSync(
            status="action_required" if action_required else "synchronized",
            bound_supplier_ids=bound,
            synchronized_supplier_ids=synchronized,
            missing_supplier_ids=missing,
            unbound_supplier_nodes=unbound,
            message=message,
        )
        return graph


def _bound_supplier_ids(graph: ExternalRiskWorkflowGraph) -> list[str]:
    """Derive the persisted supplier binding from the canonical canvas nodes.

    The supplier workspace is an inventory view; a supplier is not considered
    part of the risk transmission map until its canvas node is explicitly
    saved.  Keeping the IDs here prevents the two views from silently claiming
    a relationship that the user has not committed.
    """
    return list(dict.fromkeys(
        node.supplier_id
        for node in graph.nodes
        if node.node_kind == "supplier" and node.supplier_id
    ))


def _relation_id(link: Any) -> str:
    """Keep a stable ID for legacy endpoint-only relationship records."""
    if getattr(link, "relation_id", None):
        return str(link.relation_id)
    digest = hashlib.sha1(
        f"{link.source}\x1f{link.target}\x1f{link.relation or ''}".encode("utf-8")
    ).hexdigest()[:16]
    return f"rel-{digest}"


def _default_correlation_layers(link: Any, nodes_by_id: dict[str, Any]) -> list[str]:
    source = nodes_by_id.get(link.source)
    target = nodes_by_id.get(link.target)
    layers = ["path"]
    if getattr(source, "node_kind", None) == "market" or getattr(target, "node_kind", None) == "market":
        layers.insert(0, "material")
    if getattr(source, "node_kind", None) == "supplier" and getattr(target, "node_kind", None) == "supplier":
        layers.insert(0, "counterparty")
    return layers


def _relationship_projections(graph: ExternalRiskWorkflowGraph) -> list[ExternalRiskRelationshipProjection]:
    nodes_by_id = {node.id: node for node in graph.nodes}
    buckets = {
        "supplier_master": [],
        "product_supply_chain": [],
        "commodity_futures": [],
    }
    for link in graph.links:
        relation_id = _relation_id(link)
        source = nodes_by_id.get(link.source)
        target = nodes_by_id.get(link.target)
        if source is None or target is None:
            continue
        buckets["product_supply_chain"].append(relation_id)
        if source.node_kind == "supplier" or target.node_kind == "supplier":
            buckets["supplier_master"].append(relation_id)
        if source.node_kind == "market" or target.node_kind == "market":
            buckets["commodity_futures"].append(relation_id)
    return [
        ExternalRiskRelationshipProjection(projection=name, relation_ids=relation_ids)
        for name, relation_ids in buckets.items()
    ]


def _hydrate_workflow_graph(graph: ExternalRiskWorkflowGraph) -> ExternalRiskWorkflowGraph:
    """Migrate relation metadata in memory without breaking old map documents."""
    nodes_by_id = {node.id: node for node in graph.nodes}
    for link in graph.links:
        link.relation_id = _relation_id(link)
        if not link.correlation_layers:
            link.correlation_layers = _default_correlation_layers(link, nodes_by_id)  # type: ignore[assignment]
        else:
            link.correlation_layers = list(dict.fromkeys(link.correlation_layers))
        # Legacy links did not identify what evidence the line represented.
        # Do not upgrade them into a commercial relationship merely because a
        # user once confirmed the line.  Simulation-labelled links are
        # explicitly rendered as scenario proxies; all other legacy links
        # remain unverified until their owner supplies evidence metadata.
        relation = str(link.relation or "").lower()
        if link.evidence_grade == "unverified" and "simulation" in relation:
            link.evidence_grade = "scenario_proxy"
        if link.relationship_scope == "industry_proxy" and "cost" in relation:
            link.relationship_scope = "cost_proxy"
        if link.evidence_grade == "scenario_proxy" and not link.boundary_note:
            link.boundary_note = "比赛演练的行业或成本传导代理，不代表真实交易、供货、股权或控制关系。"
        # A name or a timestamp alone is not a controlled confirmation.
        if not (link.confirmed_by and link.confirmed_at):
            link.confirmed_by = None
            link.confirmed_at = None
    graph.bound_supplier_ids = _bound_supplier_ids(graph)
    graph.relationship_projections = _relationship_projections(graph)
    return graph


def _dashboard_data_quality(
    *,
    graph: ExternalRiskWorkflowGraph,
    live_status: ExternalRiskProviderStatus,
    intelligence_status: ExternalRiskProviderStatus,
) -> ExternalRiskDataQuality:
    """Describe the evidence boundary in one place for the dashboard.

    ``runtime_access`` reports the outcome of this service instance's latest
    request.  It deliberately does not infer that supplier records or canvas
    links have been verified by an external provider.
    """
    grades = {
        "unverified": 0,
        "scenario_proxy": 0,
        "document_referenced": 0,
        "contract_verified": 0,
    }
    for link in graph.links:
        grades[link.evidence_grade] = grades.get(link.evidence_grade, 0) + 1
    documented_relationships = sum(
        1 for link in graph.links
        if link.evidence_grade in {"document_referenced", "contract_verified"}
    )
    scenario_relationships = grades.get("scenario_proxy", 0)
    relationship_access = (
        "live_verified"
        if documented_relationships and not scenario_relationships
        else "scenario_record"
        if scenario_relationships
        else "fixture_only"
    )
    relationship_boundary = (
        "当前画布仅保留经公开披露材料核验的关系；证券代码用于实时行情锚定。"
        "公开披露可证明已披露的供货/业务关系，但未披露的合同金额、期限、排他性和持续性仍需单独核验。"
        if relationship_access == "live_verified"
        else "供应商台账和当前画布关系均为比赛演练记录；证券代码可用于行情锚定，"
        "不构成真实采购、供货、订单、股权或控制关系证明。"
    )
    return ExternalRiskDataQuality(
        market_data_access=live_status.runtime_access,
        commodity_data_access=live_status.runtime_access,
        news_policy_data_access=intelligence_status.runtime_access,
        supply_chain_data_access=relationship_access,
        relationship_evidence_counts=grades,
        relationship_boundary=relationship_boundary,
    )


def _write_workflow_graph(path: Path, graph: ExternalRiskWorkflowGraph, *, revision: int) -> ExternalRiskWorkflowGraph:
    path.parent.mkdir(parents=True, exist_ok=True)
    graph = _hydrate_workflow_graph(graph)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    graph.revision = revision
    graph.updated_at = now
    graph.storage_path = str(path)
    for link in graph.links:
        link.updated_at = now
    graph_payload = graph.model_dump(mode="json") if hasattr(graph, "model_dump") else graph.dict()
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(graph_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)
    return graph


def _public_node_payload(node: Any) -> dict[str, Any]:
    payload = node.model_dump(mode="json") if hasattr(node, "model_dump") else node.dict()
    return payload


def _public_relation_payload(link: Any) -> dict[str, Any]:
    payload = link.model_dump(mode="json") if hasattr(link, "model_dump") else link.dict()
    return payload


def _workflow_graph_diff(draft: ExternalRiskWorkflowGraph, current: ExternalRiskWorkflowGraph) -> dict[str, Any]:
    draft = _hydrate_workflow_graph(draft.model_copy(deep=True))
    current = _hydrate_workflow_graph(current.model_copy(deep=True))
    draft_nodes = {node.id: node for node in draft.nodes}
    current_nodes = {node.id: node for node in current.nodes}
    draft_relations = {_relation_id(link): link for link in draft.links}
    current_relations = {_relation_id(link): link for link in current.links}

    def changed(left: Any, right: Any, serializer) -> bool:
        return serializer(left) != serializer(right)

    return {
        "base_revision": draft.revision,
        "current_revision": current.revision,
        "nodes": {
            "draft_only": sorted(set(draft_nodes) - set(current_nodes)),
            "server_only": sorted(set(current_nodes) - set(draft_nodes)),
            "changed": sorted(node_id for node_id in set(draft_nodes).intersection(current_nodes)
                              if changed(draft_nodes[node_id], current_nodes[node_id], _public_node_payload)),
        },
        "relations": {
            "draft_only": sorted(set(draft_relations) - set(current_relations)),
            "server_only": sorted(set(current_relations) - set(draft_relations)),
            "changed": sorted(relation_id for relation_id in set(draft_relations).intersection(current_relations)
                              if changed(draft_relations[relation_id], current_relations[relation_id], _public_relation_payload)),
            # Keep the original aggregate field for existing clients, but
            # distinguish newly introduced draft relations from legacy/current
            # unconfirmed links so a reviewer can focus on the actual change.
            "draft_added_unconfirmed_relation_ids": sorted(
                relation_id for relation_id in set(draft_relations) - set(current_relations)
                if not (draft_relations[relation_id].confirmed_by and draft_relations[relation_id].confirmed_at)
            ),
            "preexisting_unconfirmed_relation_ids": sorted(
                relation_id for relation_id in set(draft_relations).intersection(current_relations)
                if not (current_relations[relation_id].confirmed_by and current_relations[relation_id].confirmed_at)
            ),
            "changed_unconfirmed_relation_ids": sorted(
                relation_id for relation_id in set(draft_relations).intersection(current_relations)
                if changed(draft_relations[relation_id], current_relations[relation_id], _public_relation_payload)
                and not (draft_relations[relation_id].confirmed_by and draft_relations[relation_id].confirmed_at)
            ),
            "unconfirmed_draft_relation_ids": sorted(
                relation_id for relation_id, link in draft_relations.items()
                if not (link.confirmed_by and link.confirmed_at)
            ),
        },
        "merge_policy": "additive_preserve_server_changes; deletion_requires_reload_and_current_revision",
    }


def _additive_workflow_merge(current: ExternalRiskWorkflowGraph, draft: ExternalRiskWorkflowGraph) -> ExternalRiskWorkflowGraph:
    current = _hydrate_workflow_graph(current.model_copy(deep=True))
    draft = _hydrate_workflow_graph(draft.model_copy(deep=True))
    nodes = {node.id: node for node in current.nodes}
    nodes.update({node.id: node for node in draft.nodes})
    relations = {_relation_id(link): link for link in current.links}
    for relation_id, draft_link in {_relation_id(link): link for link in draft.links}.items():
        server_link = relations.get(relation_id)
        if server_link and server_link.confirmed_by and server_link.confirmed_at and not (draft_link.confirmed_by and draft_link.confirmed_at):
            draft_link.confirmed_by = server_link.confirmed_by
            draft_link.confirmed_at = server_link.confirmed_at
        relations[relation_id] = draft_link
    return ExternalRiskWorkflowGraph(
        version=current.version,
        revision=current.revision,
        nodes=list(nodes.values()),
        links=list(relations.values()),
        merge_audit=current.merge_audit,
    )


def _relevant_live_signals(
    signals: list[ExternalRiskSignal],
    company: Any,
    graph: ExternalRiskWorkflowGraph,
) -> list[ExternalRiskSignal]:
    """Keep live signals only when their company/material/graph basis is known.

    The result preserves the provider evidence and adds a compact explanation
    under ``metadata.relevance`` so an analyst can audit why a live item was
    included instead of treating a generic market feed as company-specific.
    """
    company_text = " ".join([
        str(getattr(company, "tech_sector", "")),
        *[str(value) for value in getattr(company, "core_products", [])],
        *[str(value) for value in getattr(company, "key_materials", [])],
        *[str(value) for value in getattr(company, "key_regions", [])],
    ]).lower()
    material_tokens = {
        token
        for value in getattr(company, "key_materials", [])
        for token in re.split(r"[^a-z0-9\u4e00-\u9fff]+", str(value).lower().replace("_", " "))
        if len(token) > 1
    }
    # Common catalog aliases that occur in enterprise material profiles.
    material_tokens.update({"silicon"} if "industrial" in material_tokens and "silicon" in company_text else set())
    graph_symbols = {node.symbol.lower() for node in graph.nodes}
    graph_text = " ".join(
        " ".join(filter(None, [node.symbol, node.name, node.group, node.lane, *node.recommendations]))
        for node in graph.nodes
    ).lower()
    sensitive_domains = set(getattr(company, "sensitive_domains", []))
    selected: list[ExternalRiskSignal] = []
    for signal in signals:
        metadata = dict(signal.metadata)
        content = " ".join([
            signal.entity,
            signal.title,
            signal.evidence,
            str(metadata.get("commodity_group", "")),
            *[str(value) for value in metadata.get("industry_tags", []) if value],
            *[str(value) for value in signal.affected_supply_links if value],
        ]).lower()
        matched: list[str] = []
        signal_symbols = {
            str(value).lower()
            for key in ("symbol", "commodity_symbols", "instrument_symbols")
            for value in (
                metadata.get(key, [])
                if isinstance(metadata.get(key), list)
                else [metadata.get(key)]
            )
            if value
        }
        if signal.entity.lower() in graph_symbols or signal_symbols.intersection(graph_symbols):
            matched.append("graph_instrument")
        if any(token in content for token in material_tokens):
            matched.append("company_material")
        if any(token and token in graph_text for token in material_tokens) and any(token in content for token in material_tokens):
            matched.append("material_graph_path")
        if any(keyword in content for keyword in ("半导体", "芯片", "晶圆", "semiconductor", "chip", "wafer")) and (
            "semiconductor" in company_text or "半导体" in company_text or "semiconductor" in graph_text
        ):
            matched.append("company_sector")
        if set(signal.affected_domains).intersection(sensitive_domains) and signal.signal_type in {"policy", "supply_chain"}:
            matched.append("company_risk_scope")
        if not matched:
            continue
        metadata["relevance"] = {
            "status": "included",
            "matched_on": list(dict.fromkeys(matched)),
            "company_id": getattr(company, "company_id", None),
            "workflow_revision": graph.revision,
            "bound_supplier_ids": graph.bound_supplier_ids,
        }
        selected.append(signal.model_copy(update={"metadata": metadata}))
    return selected


_BROAD_SUPPLY_CHAIN_ENTITIES = {
    "supply_chain_market_observation",
    "transport_disruption",
    "energy_cost_policy",
    "product_quality",
    "trade_remedy",
}


def _broad_supply_chain_observations(
    signals: list[ExternalRiskSignal],
    *,
    excluded_signal_ids: set[str] | None = None,
) -> list[ExternalRiskSignal]:
    """Return cross-industry chain facts without treating them as company risk."""
    excluded = excluded_signal_ids or set()
    candidates: list[ExternalRiskSignal] = []
    for signal in signals:
        if signal.signal_id in excluded or signal.signal_type not in {"news", "policy", "supply_chain"}:
            continue
        if signal.metadata.get("risk_scope") == "general_regulatory_environment":
            continue
        industry_tags = signal.metadata.get("industry_tags")
        has_industry_tag = isinstance(industry_tags, list) and any(str(tag).strip() for tag in industry_tags)
        if signal.entity not in _BROAD_SUPPLY_CHAIN_ENTITIES and not has_industry_tag:
            continue
        if "supply_chain" not in signal.affected_domains and not signal.affected_supply_links:
            continue
        metadata = {
            **signal.metadata,
            "observation_scope": "broad_supply_chain",
            "risk_inclusion": "context_only",
        }
        candidates.append(signal.model_copy(update={"metadata": metadata}))
    return sorted(_dedupe_signals(candidates), key=_dashboard_signal_priority, reverse=True)


def _fact_background(
    finding: TechCompanyRiskFinding,
    signals: list[ExternalRiskSignal],
) -> str:
    facts = [signal.evidence for signal in signals]
    if not facts:
        return finding.summary
    return f"{finding.summary} 触发事实：" + "；".join(facts)


def _suggested_filters(risk_domain: str) -> dict[str, Any]:
    if risk_domain == "export_control":
        return {"category": "安全合规"}
    if risk_domain == "ip":
        return {"category": "知识产权"}
    if risk_domain == "data_compliance":
        return {"category": "数据合规"}
    if risk_domain in {"contract", "supply_chain", "disclosure", "corporate_governance"}:
        return {"document_type": "法律法规"}
    return {}


LIVE_LEGAL_QUERY_TEMPLATES = {
    "market": "市场异常波动下融资、担保和重大事项信息披露的法律核查要点",
    "supply_chain": "能源、原材料或供应约束变化下采购和销售合同的调价、履约与风险分配",
    "contract": "贸易救济或关税变化对跨境采购、销售合同和税费承担的影响",
    "export_control": "出口管制、出口管理或实体清单变化下订单履行、技术支持与再出口合规义务",
    "disclosure": "监管措施或行政处罚触发的信息披露、内部调查、整改与责任追究要求",
    "data_compliance": "数据安全事件或监管处罚触发的处置、通报、整改和对外合同义务",
    "ip": "知识产权争议或技术限制对研发、许可和供应合同的影响",
    "corporate_governance": "外部风险事件下公司治理、内控留痕和董事会决策义务",
}


def _live_signal_legal_query_tasks(
    signals: list[ExternalRiskSignal],
    *,
    risk_domain: str | None = None,
    severity: str | None = None,
) -> list[LegalQueryTask]:
    selected: dict[tuple[str, str, str], ExternalRiskSignal] = {}
    for signal in signals:
        if signal.metadata.get("risk_scope") == "general_regulatory_environment":
            continue
        if signal.direction not in {"negative", "mixed"}:
            continue
        if severity and signal.severity != severity:
            continue
        if not _legal_task_is_qualified(signal):
            continue
        domain = _legal_domain_for_signal(signal)
        if not domain or (risk_domain and domain != risk_domain):
            continue
        source_key = str(signal.metadata.get("feed_id") or signal.source or signal.signal_type)
        key = (source_key, signal.entity, domain)
        current = selected.get(key)
        if current is None or _signal_priority(signal) > _signal_priority(current):
            selected[key] = signal

    ordered = sorted(selected.values(), key=_signal_priority, reverse=True)[:8]
    tasks: list[LegalQueryTask] = []
    for signal in ordered:
        domain = _legal_domain_for_signal(signal)
        if not domain:
            continue
        task_id = f"live-{signal.signal_id}-{domain}"
        title = signal.title[:100]
        tasks.append(
            LegalQueryTask(
                task_id=task_id,
                finding_id=f"live-{signal.entity}",
                risk_domain=domain,  # type: ignore[arg-type]
                severity=signal.severity,
                query=f"{LIVE_LEGAL_QUERY_TEMPLATES[domain]}（外部事件：{title}）",
                fact_background=_live_signal_fact_background(signal),
                triggering_signal_ids=[signal.signal_id],
                evidence_refs=[signal.signal_id],
                suggested_filters=_suggested_filters(domain),
                metadata={
                    "origin": "live_external_signal",
                    "signal_title": signal.title,
                    "signal_source": signal.source,
                    "feed_name": signal.metadata.get("feed_name"),
                    "instrument_label": signal.metadata.get("instrument_label"),
                    "csrc_instruments": signal.metadata.get("csrc_instruments", []),
                    "csrc_instrument_status": signal.metadata.get("csrc_instrument_status"),
                    "source_stale": bool(signal.metadata.get("source_stale")),
                    "risk_relevance": signal.metadata.get("risk_relevance", 1.0),
                },
            )
        )
    return tasks


def _legal_task_is_qualified(signal: ExternalRiskSignal) -> bool:
    """Do not turn a single relationship/risk-domain match into legal work.

    A direct official policy or regulatory action remains eligible, as does a
    named analyst confirmation.  Ordinary market, commodity and map matches
    require corroboration across at least two risk domains before they enter
    the legal-RAG queue.
    """
    if bool(signal.metadata.get("legal_task_confirmed")):
        return True
    domains = {str(domain) for domain in signal.affected_domains}
    if len(domains) >= 2:
        return True
    feed_id = str(signal.metadata.get("feed_id") or "").lower()
    source = str(signal.source or "").lower()
    official = (
        signal.signal_type == "policy"
        and ("official" in feed_id or "csrc" in feed_id or ".gov" in source or ".gov.cn" in source)
    )
    return official


def _legal_domain_for_signal(signal: ExternalRiskSignal) -> str | None:
    if signal.signal_type == "market":
        return "market"
    if signal.signal_type == "commodity_futures":
        return "supply_chain" if "supply_chain" in signal.affected_domains else "contract"
    priority = (
        "export_control",
        "data_compliance",
        "disclosure",
        "contract",
        "supply_chain",
        "ip",
        "corporate_governance",
        "market",
    )
    for domain in priority:
        if domain in signal.affected_domains:
            return domain
    return None


def _live_signal_fact_background(signal: ExternalRiskSignal) -> str:
    feed_name = str(signal.metadata.get("feed_name") or signal.signal_type)
    relevance = _numeric_value(signal.metadata.get("risk_relevance")) or 1.0
    freshness = "来源最近抓取失败，当前使用最近成功快照。" if signal.metadata.get("source_stale") else ""
    disclosed_instruments = signal.metadata.get("csrc_instruments")
    if isinstance(disclosed_instruments, list) and disclosed_instruments:
        instrument_context = f"；涉及证券：{'、'.join(str(item) for item in disclosed_instruments[:6])}"
    elif signal.metadata.get("csrc_instrument_status") == "not_disclosed":
        instrument_context = "；涉及证券：官方公告未披露"
    else:
        instrument_context = ""
    return (
        f"实时外部信号：{signal.title}。来源：{feed_name}；时间：{signal.as_of}；"
        f"风险相关度：{relevance:.0%}{instrument_context}；证据：{signal.evidence}；原文：{signal.source}。{freshness}"
    )


CHAIN_SYMBOLS_BY_LINK = {
    "copper": ("hf_CAD", "bk_BK0877", "bk_BK0457"),
    "aluminum": ("hf_AHD", "bk_BK0457"),
    "tin": ("hf_SND", "bk_BK0877"),
    "nickel": ("hf_NID",),
    "zinc": ("hf_ZSD",),
    "wti_crude": ("hf_CL", "if_SC0", "if_EC0"),
    "natural_gas": ("hf_NG",),
    "semiconductor_materials": ("sh688146", "sh688106", "sh688268"),
    "semiconductor_equipment": ("bk_BK1326", "sh688012", "sh688072"),
    "cross_border_delivery": ("if_EC0", "hf_CL"),
    "electricity": ("bk_BK0457",),
    "energy_supply": ("if_SC0", "hf_CL"),
    "maritime_logistics": ("if_EC0", "sh601919", "sh600026", "sh601872", "sh601022"),
    "oil_transport": ("hf_CL", "if_SC0", "sh601857", "sh600028", "sh600938", "sh600026", "sh601872"),
    "energy": ("hf_CL", "if_SC0", "sh601857", "sh600028", "sh600938"),
}

INDUSTRY_TAG_LABELS = {
    "maritime_logistics": "海运物流",
    "oil_transport": "油运",
    "energy": "能源",
    "semiconductor": "半导体",
    "semiconductor_materials": "半导体材料",
    "semiconductor_equipment": "半导体设备",
    "copper": "铜",
    "aluminum": "铝",
    "tin": "锡",
}

NODE_INDUSTRY_TAGS = {
    "if_EC0": ("maritime_logistics",),
    "hf_CL": ("oil_transport", "energy"),
    "if_SC0": ("oil_transport", "energy"),
    "sh601857": ("oil_transport", "energy"),
    "sh600028": ("oil_transport", "energy"),
    "sh600938": ("oil_transport", "energy"),
    "sh601919": ("maritime_logistics",),
    "sh600026": ("maritime_logistics", "oil_transport"),
    "sh601872": ("maritime_logistics", "oil_transport"),
    "sh601022": ("maritime_logistics",),
    "sh688146": ("semiconductor", "semiconductor_materials"),
    "sh688106": ("semiconductor", "semiconductor_materials"),
    "sh688268": ("semiconductor", "semiconductor_materials"),
    "bk_BK1326": ("semiconductor", "semiconductor_equipment"),
    "sh688012": ("semiconductor", "semiconductor_equipment"),
    "sh688072": ("semiconductor", "semiconductor_equipment"),
    "hf_CAD": ("copper",),
    "hf_AHD": ("aluminum",),
    "hf_SND": ("tin",),
}


def _chain_alerts(
    signals: list[ExternalRiskSignal],
    graph: ExternalRiskWorkflowGraph,
) -> list[ExternalRiskChainAlert]:
    nodes_by_id = {node.id: node for node in graph.nodes}
    node_ids_by_symbol: dict[str, list[str]] = {}
    for node in graph.nodes:
        node_ids_by_symbol.setdefault(node.symbol, []).append(node.id)
    downstream: dict[str, list[str]] = {node.id: [] for node in graph.nodes}
    links_by_pair: dict[tuple[str, str], Any] = {}
    for link in graph.links:
        # A drawn or imported line is review context only until a named owner
        # confirms both the relationship and its timestamp.  It may be shown
        # on the canvas, but must not affect formal chain transmission or the
        # risk coefficient calculated from these alerts.
        if link.source in nodes_by_id and link.target in nodes_by_id and link.confirmed_by and link.confirmed_at:
            downstream[link.source].append(link.target)
            links_by_pair[(link.source, link.target)] = link

    alerts: list[ExternalRiskChainAlert] = []
    for signal in signals:
        if signal.direction not in {"negative", "mixed"}:
            continue
        if signal.metadata.get("risk_scope") == "general_regulatory_environment":
            continue
        industry_tags = _signal_industry_tags(signal)
        root_symbols = _chain_root_symbols(signal, industry_tags)
        root_ids = [node_id for symbol in root_symbols for node_id in node_ids_by_symbol.get(symbol, [])]
        industry_ids = _industry_related_node_ids(graph, industry_tags)
        if not root_ids and not industry_ids:
            continue
        root_strength = _signal_evidence_weight(signal) * _severity_intensity(signal.severity)
        if root_strength < 0.08:
            continue
        impacts: dict[str, tuple[float, list[str]]] = {}
        for root_id in root_ids:
            _propagate_chain_impact(root_id, root_strength, downstream, impacts)
        for industry_id in industry_ids:
            if industry_id not in impacts:
                _propagate_chain_impact(industry_id, root_strength * 0.72, downstream, impacts)
        ranked = sorted(impacts.items(), key=lambda item: item[1][0], reverse=True)
        # A root instrument alone is direct market context, not an approved
        # supply-chain transmission.  At least one confirmed relationship
        # must be traversed before this alert is eligible for the formal
        # chain-transmission component of the risk coefficient.
        if not any(len(impact[1][1]) > 1 for impact in ranked):
            continue
        affected_ids = [node_id for node_id, _impact in ranked[:8]]
        transmission = max((impact[0] for _node_id, impact in ranked), default=0.0)
        if not affected_ids or transmission < 0.08:
            continue
        affected_symbols = [nodes_by_id[node_id].symbol for node_id in affected_ids]
        # The highest score is normally the root market node.  It is useful
        # for severity but not a transmission path; choose the strongest path
        # that actually traversed a confirmed relationship so callers always
        # see the downstream terminal that justified the alert.
        primary_impact = next((impact for _node_id, impact in ranked if len(impact[1]) > 1), None)
        primary_path = primary_impact[1] if primary_impact else []
        path_links = [
            links_by_pair[(source, target)]
            for source, target in zip(primary_path, primary_path[1:])
            if (source, target) in links_by_pair
        ]
        relationship_grade = _path_relationship_evidence_grade(path_links)
        boundary_notes = list(dict.fromkeys(
            str(link.boundary_note).strip() for link in path_links if str(link.boundary_note).strip()
        ))
        association_type = "mixed" if root_ids and industry_ids else "workflow" if root_ids else "industry"
        external_instruments = _external_instruments(signal, root_symbols, node_ids_by_symbol)
        alert_id = f"chain-{signal.signal_id}"
        alerts.append(
            ExternalRiskChainAlert(
                alert_id=alert_id,
                signal_id=signal.signal_id,
                severity=_chain_severity(transmission),
                source_symbol=next((symbol for symbol in root_symbols if symbol in node_ids_by_symbol), root_symbols[0] if root_symbols else None),
                affected_node_ids=affected_ids,
                affected_symbols=affected_symbols,
                path_node_ids=primary_path,
                association_type=association_type,
                association_tags=[INDUSTRY_TAG_LABELS.get(tag, tag) for tag in industry_tags],
                external_instruments=external_instruments,
                transmission_score=round(min(transmission, 1.0), 2),
                summary=(
                    f"{signal.title} 可沿当前产业链传导至 {len(affected_ids)} 个节点；"
                    f"首要受影响节点为 {nodes_by_id[affected_ids[0]].symbol}。"
                ),
                evidence_refs=[signal.signal_id],
                relationship_evidence_grade=relationship_grade,  # type: ignore[arg-type]
                relationship_boundary="；".join(boundary_notes[:2]),
            )
        )
    return sorted(alerts, key=lambda alert: alert.transmission_score, reverse=True)[:8]


def _path_relationship_evidence_grade(links: list[Any]) -> str:
    """Return the least authoritative evidence grade on a transmitted path."""
    if not links:
        return "unverified"
    ranks = {
        "unverified": 0,
        "scenario_proxy": 1,
        "document_referenced": 2,
        "contract_verified": 3,
    }
    return min(
        (str(link.evidence_grade) for link in links),
        key=lambda grade: ranks.get(grade, 0),
    )


def _chain_root_symbols(signal: ExternalRiskSignal, industry_tags: list[str] | None = None) -> list[str]:
    content = f"{signal.title} {signal.evidence}".lower()
    if signal.signal_type in {"news", "policy"}:
        disclosed_commodities = signal.metadata.get("commodity_symbols")
        if isinstance(disclosed_commodities, list):
            symbols = [str(symbol) for symbol in disclosed_commodities if str(symbol) in CATALOG_BY_SYMBOL]
            if symbols:
                return list(dict.fromkeys(symbols))
        if any(keyword in content for keyword in ("半导体", "芯片", "晶圆", "光刻", "semiconductor", "chip", "wafer")):
            return ["sh688146", "sh688106", "sh688268", "bk_BK1326", "sh688012", "sh688072"]
        if any(keyword in content for keyword in ("铜", "铝", "锡", "copper", "aluminum", "tin")):
            return ["hf_CAD", "hf_AHD", "hf_SND"]
        if any(keyword in content for keyword in ("原油", "油轮", "海运", "集运", "航运", "红海", "霍尔木兹", "oil", "tanker", "shipping", "freight", "hormuz")):
            return [symbol for tag in (industry_tags or ["maritime_logistics", "oil_transport", "energy"]) for symbol in CHAIN_SYMBOLS_BY_LINK.get(tag, ())]
        # Broad policy/news labels without a named industry are review context, not a propagation root.
        return []
    candidates = [signal.entity]
    group = signal.metadata.get("commodity_group")
    if group:
        candidates.append(str(group))
    candidates.extend(signal.affected_supply_links)
    expanded: list[str] = []
    for candidate in candidates:
        expanded.extend(CHAIN_SYMBOLS_BY_LINK.get(str(candidate), (str(candidate),)))
    return list(dict.fromkeys(expanded))


def _signal_industry_tags(signal: ExternalRiskSignal) -> list[str]:
    tags = signal.metadata.get("industry_tags")
    if isinstance(tags, list):
        return list(dict.fromkeys(str(tag) for tag in tags if str(tag).strip()))
    content = f"{signal.title} {signal.evidence}".lower()
    matched: list[str] = []
    for tag, keywords in {
        "maritime_logistics": ("海运", "航运", "油轮", "船舶", "red sea", "hormuz", "shipping", "tanker"),
        "oil_transport": ("原油", "油轮", "石油", "crude oil", "tanker"),
        "energy": ("原油", "石油", "能源", "oil", "energy"),
    }.items():
        if any(keyword in content for keyword in keywords):
            matched.append(tag)
    return matched


def _industry_related_node_ids(graph: ExternalRiskWorkflowGraph, tags: list[str]) -> list[str]:
    if not tags:
        return []
    tag_set = set(tags)
    return [node.id for node in graph.nodes if tag_set.intersection(NODE_INDUSTRY_TAGS.get(node.symbol, ()))]


def _external_instruments(
    signal: ExternalRiskSignal,
    root_symbols: list[str],
    node_ids_by_symbol: dict[str, list[str]],
) -> list[str]:
    disclosed = signal.metadata.get("affected_instruments")
    instruments = [str(item) for item in disclosed] if isinstance(disclosed, list) else []
    instruments.extend(_quote_name(symbol) for symbol in root_symbols if symbol not in node_ids_by_symbol)
    return list(dict.fromkeys(instruments))[:8]


def _propagate_chain_impact(
    node_id: str,
    strength: float,
    downstream: dict[str, list[str]],
    impacts: dict[str, tuple[float, list[str]]],
    path: list[str] | None = None,
    depth: int = 0,
) -> None:
    if depth > 3 or strength < 0.05:
        return
    current_path = [*(path or []), node_id]
    existing = impacts.get(node_id)
    if existing is None or strength > existing[0]:
        impacts[node_id] = (strength, current_path)
    for target in downstream.get(node_id, []):
        _propagate_chain_impact(target, strength * 0.68, downstream, impacts, current_path, depth + 1)


def _chain_severity(score: float) -> str:
    if score >= 0.55:
        return "high"
    if score >= 0.28:
        return "medium"
    return "low"


def _dedupe_signals(signals: list[ExternalRiskSignal]) -> list[ExternalRiskSignal]:
    seen: set[str] = set()
    deduped: list[ExternalRiskSignal] = []
    for signal in signals:
        if signal.signal_id in seen:
            continue
        seen.add(signal.signal_id)
        deduped.append(signal)
    return deduped


def _severity_rank(severity: str) -> int:
    return {
        "critical": 4,
        "high": 3,
        "medium": 2,
        "low": 1,
    }.get(severity, 0)


def _severity_intensity(severity: str) -> float:
    """Non-linear severity scale so a critical signal has a material effect."""
    return {
        "low": 0.20,
        "medium": 0.45,
        "high": 0.75,
        "critical": 1.00,
    }.get(severity, 0.0)


def _numeric_value(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace("%", "").strip())
    except (TypeError, ValueError):
        return None


def _signal_threshold_ratio(signal: ExternalRiskSignal) -> float | None:
    value = _numeric_value(signal.value)
    threshold = _numeric_value(signal.threshold)
    if value is None or threshold is None or threshold == 0:
        return None
    return abs(value) / abs(threshold)


def _risk_coefficient(
    signals: list[ExternalRiskSignal],
    *,
    legal_task_count: int = 0,
    chain_alerts: list[ExternalRiskChainAlert] | None = None,
) -> float:
    # legal_task_count remains accepted for backwards compatibility, but is deliberately not a score input.
    return _risk_coefficient_profile(signals, chain_alerts=chain_alerts)["score"]


def _risk_coefficient_profile(
    signals: list[ExternalRiskSignal],
    *,
    chain_alerts: list[ExternalRiskChainAlert] | None = None,
) -> dict[str, Any]:
    if not signals:
        return {
            "score": 0.0,
            "components": {
                "severity": 0.0,
                "materiality": 0.0,
                "threshold_pressure": 0.0,
                "chain_transmission": 0.0,
                "legal_exposure": 0.0,
                "persistence": 0.0,
            },
            "quality": 0.0,
        }

    scoring_signals = _risk_scoring_signals(signals)
    confidences = [_signal_evidence_weight(signal) for signal in scoring_signals]
    evidence_quality = sum(confidences) / len(confidences)
    severity_exposures = [
        min(0.95, _severity_intensity(signal.severity) * confidence)
        for signal, confidence in zip(scoring_signals, confidences)
    ]
    # Exposure aggregation is monotonic: an additional adverse observation cannot dilute an existing risk.
    severity_component = _combined_exposure(severity_exposures)

    ratios_by_signal = [
        _signal_threshold_ratio(signal) if _is_quantitative_signal(signal) else None
        for signal in scoring_signals
    ]
    materiality_exposures = [
        min(1.0, ratio / 2.0) * confidence if ratio is not None else 0.0
        for signal, ratio, confidence in zip(scoring_signals, ratios_by_signal, confidences)
    ]
    materiality_component = max(materiality_exposures, default=0.0)
    threshold_exposures = [
        min(0.95, 0.55 * max(0.0, ratio - 1.0) * confidence)
        if ratio is not None else 0.0
        for signal, ratio, confidence in zip(scoring_signals, ratios_by_signal, confidences)
    ]
    threshold_component = _combined_exposure(threshold_exposures)

    chain_component = _combined_exposure(
        [alert.transmission_score for alert in chain_alerts or []]
    )
    direct_legal_exposure = _combined_exposure(
        [
            min(0.95, 0.75 * confidence * _severity_intensity(signal.severity))
            if _has_direct_legal_exposure(signal)
            else 0.0
            for signal, confidence in zip(scoring_signals, confidences)
        ]
    )
    lookbacks = [
        _numeric_value(signal.metadata.get("lookback_days")) or 1.0
        for signal in scoring_signals
    ]
    entity_counts: dict[str, int] = {}
    for signal in scoring_signals:
        entity_counts[signal.entity] = entity_counts.get(signal.entity, 0) + 1
    repeat_component = min(max(entity_counts.values(), default=0) / 3.0, 1.0)
    persistence_component = min(
        1.0,
        0.60 * min(max(lookbacks, default=1.0) / 20.0, 1.0)
        + 0.40 * repeat_component,
    )
    components = {
        "severity": round(severity_component * 22, 1),
        "materiality": round(materiality_component * 20, 1),
        "threshold_pressure": round(threshold_component * 16, 1),
        "chain_transmission": round(chain_component * 16, 1),
        "legal_exposure": round(direct_legal_exposure * 14, 1),
        "persistence": round(persistence_component * 12, 1),
    }
    score = round(max(0.0, min(sum(components.values()), 100.0)), 1)
    source_count = len({signal.source for signal in scoring_signals if signal.source})
    source_diversity = min(source_count, 3) / 3
    quality = round(max(0.0, min(evidence_quality * (0.75 + 0.25 * source_diversity), 1.0)), 2)
    return {"score": score, "components": components, "quality": quality}


def _signal_evidence_weight(signal: ExternalRiskSignal) -> float:
    confidence = max(0.0, min(float(signal.confidence or 0.0), 1.0))
    relevance = _numeric_value(signal.metadata.get("risk_relevance"))
    relevance = 1.0 if relevance is None else max(0.0, min(relevance, 1.0))
    return confidence * relevance


def _is_quantitative_signal(signal: ExternalRiskSignal) -> bool:
    return signal.signal_type in {"market", "commodity_futures"} and signal.metric in {
        "intraday_return", "5d_return", "daily_return",
    }


def _has_direct_legal_exposure(signal: ExternalRiskSignal) -> bool:
    if signal.metadata.get("risk_scope") == "general_regulatory_environment":
        return False
    direct_domains = {"export_control", "data_compliance", "disclosure", "contract", "ip"}
    return bool(direct_domains.intersection(signal.affected_domains))


def _risk_scoring_signals(signals: list[ExternalRiskSignal]) -> list[ExternalRiskSignal]:
    """Cap repeated live headlines from one source/entity while retaining every item for review."""
    grouped: dict[tuple[str, str], ExternalRiskSignal] = {}
    selected: list[ExternalRiskSignal] = []
    for signal in signals:
        feed_id = str(signal.metadata.get("feed_id") or "").strip()
        if not feed_id:
            selected.append(signal)
            continue
        key = (feed_id, signal.entity)
        current = grouped.get(key)
        if current is None or _signal_priority(signal) > _signal_priority(current):
            grouped[key] = signal
    return [*selected, *grouped.values()]


def _signal_priority(signal: ExternalRiskSignal) -> tuple[int, float, str]:
    return (_severity_rank(signal.severity), float(signal.confidence or 0.0), signal.as_of)


def _dashboard_signal_priority(signal: ExternalRiskSignal) -> tuple[float, int, float, str]:
    """Sort the live watchlist by observation time, then risk importance."""
    return (
        _signal_as_of_epoch(signal.as_of),
        _severity_rank(signal.severity),
        float(signal.confidence or 0.0),
        signal.signal_id,
    )


def _signal_as_of_epoch(value: str) -> float:
    try:
        parsed = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.timestamp()
    except (TypeError, ValueError, OverflowError):
        return 0.0


def _combined_exposure(exposures: list[float]) -> float:
    remaining = 1.0
    for exposure in exposures:
        remaining *= 1.0 - max(0.0, min(float(exposure), 0.95))
    return 1.0 - remaining


def _risk_coefficient_level(score: float) -> str:
    if score >= 82:
        return "critical"
    if score >= 65:
        return "high"
    if score >= 38:
        return "medium"
    return "low"


def _dashboard_headline(signals: list[ExternalRiskSignal], live_signal_count: int) -> str:
    if not signals:
        return "实时外部市场与供应链信号暂不可用。"
    top = signals[0]
    return f"实时外部风险关注：{top.title}"


def _quote_display_metadata(
    *,
    symbol: str,
    name: str,
    points: list[Any],
    interval: str,
) -> dict[str, Any]:
    """Provide an explicit, provider-backed reference for quote display calculations."""
    normalized_symbol = str(symbol or "").strip().lower()
    normalized_name = re.sub(r"\s+", "", str(name or "").strip())
    board = _a_share_board(normalized_symbol)
    listing_marker = re.match(r"^([NC]).+", normalized_name, flags=re.IGNORECASE)
    is_new_listing = bool(board and listing_marker)
    is_st = bool(board and re.match(r"^\*?ST", normalized_name, flags=re.IGNORECASE))
    instrument_status = "new_listing" if is_new_listing else "st" if is_st else "normal"

    reference_price: float | None = None
    change_basis = "unavailable"
    if points:
        if interval == "intraday":
            reference_price = next(
                (
                    float(point.baseline_price)
                    for point in points
                    if getattr(point, "baseline_price", None) not in {None, 0}
                ),
                None,
            )
            if reference_price is not None:
                change_basis = "listing_reference" if listing_marker and listing_marker.group(1).upper() == "N" else "previous_close"
        if reference_price is None:
            first = points[0]
            reference_price = getattr(first, "open", None) or getattr(first, "close", None)
            reference_price = float(reference_price) if reference_price not in {None, 0} else None
            change_basis = "period_open" if interval != "intraday" else "first_available"

    latest_price = float(points[-1].close) if points and getattr(points[-1], "close", None) is not None else None
    change_rate = (
        (latest_price - reference_price) / reference_price
        if latest_price is not None and reference_price not in {None, 0}
        else None
    )
    price_limit_rate, price_limit_label = _a_share_price_limit(board, instrument_status)
    return {
        "reference_price": reference_price,
        "change_rate": change_rate,
        "change_basis": change_basis,
        "instrument_status": instrument_status if board else "unknown",
        "price_limit_rate": price_limit_rate,
        "price_limit_label": price_limit_label,
    }


def _a_share_board(symbol: str) -> str | None:
    if re.fullmatch(r"sh688\d{3}", symbol):
        return "star"
    if re.fullmatch(r"sz(?:300|301)\d{3}", symbol):
        return "chinext"
    if re.fullmatch(r"bj\d{6}", symbol):
        return "bse"
    if re.fullmatch(r"(?:sh|sz)\d{6}", symbol):
        return "main"
    return None


def _a_share_price_limit(board: str | None, instrument_status: str) -> tuple[float | None, str]:
    if board is None:
        return None, "not_applicable"
    if instrument_status == "new_listing":
        return None, "new_listing_initial_period"
    base_rates = {"main": 0.10, "star": 0.20, "chinext": 0.20, "bse": 0.30}
    rate = base_rates[board]
    suffix = "st" if instrument_status == "st" else "normal"
    return rate, f"{board}_{suffix}_{int(rate * 100)}pct"


def _quote_name(symbol: str) -> str:
    catalog_name = catalog_display_name(symbol)
    if catalog_name:
        return catalog_name
    quote_name_overrides = {
        "sh000001": "上证指数",
        "sz399001": "深证成指",
        "sz399006": "创业板指",
        "hf_CAD": "伦铜",
        "hf_AHD": "伦铝",
        "hf_SI": "白银",
        "hf_GC": "黄金",
        "hf_CL": "原油",
        "hf_NG": "天然气",
        "hf_ZSD": "伦锌",
        "hf_NID": "伦镍",
        "hf_PBD": "伦铅",
        "hf_SND": "伦锡",
        "hf_C": "玉米",
        "hf_S": "大豆",
        "hf_W": "小麦",
        "if_EC0": "欧线集运主连",
        "if_SC0": "原油主连",
        "if_SA0": "纯碱主连",
        "if_EG0": "乙二醇主连",
        "if_PP0": "聚丙烯主连",
        "if_MA0": "甲醇主连",
        "if_TA0": "PTA主连",
        "if_SH0": "烧碱主连",
        "if_FG0": "玻璃主连",
        "if_UR0": "尿素主连",
        "sh601857": "中国石油",
        "sh600028": "中国石化",
        "sh600938": "中国海油",
        "sh601919": "中远海控",
        "sh600026": "中远海能",
        "sh601872": "招商轮船",
        "sh601022": "宁波远洋",
        "us_NDX": "纳斯达克100",
        "us_SPX": "标普500",
        "us_AAPL": "苹果",
        "us_NVDA": "英伟达",
        "us_TSLA": "特斯拉",
        "us_MSFT": "微软",
        "us_BABA": "阿里巴巴",
        "us_GLW": "康宁",
        "us_MU": "美光科技",
        "us_WDC": "西部数据",
        "us_SNDK": "闪迪",
        "kr_005930": "三星电子",
        "kr_000660": "SK海力士",
        "sz000100": "TCL科技",
        "sz000725": "京东方A",
        "sh600552": "凯盛科技",
        "sh600707": "彩虹股份",
        "sh688146": "中船特气",
        "sh688106": "金宏气体",
        "sh688268": "华特气体",
        "sh688981": "中芯国际",
        "sh688012": "中微公司",
        "sh688072": "拓荆科技",
        "sh688008": "澜起科技",
        "sz300308": "中际旭创",
        "bk_BK1326": "半导体设备",
        "bk_BK0457": "电网设备",
        "bk_BK1215": "通信",
        "bk_BK1590": "通信设备",
        "bk_BK1203": "非银金融",
        "bk_BK1037": "消费电子",
        "bk_BK1128": "CPO概念",
        "bk_BK0877": "PCB",
        "bk_BK1178": "AI眼镜",
        "bk_BK1164": "AIPC",
        "bk_BK1162": "AI手机",
        "bond_000012": "国债指数",
    }
    if symbol in quote_name_overrides:
        return quote_name_overrides[symbol]
    return {
        "sh000001": "上证指数",
        "sz399001": "深证成指",
        "sz399006": "创业板指",
        "hf_CAD": "伦铜",
        "hf_AHD": "伦铝",
        "hf_SI": "白银",
        "hf_GC": "黄金",
        "hf_CL": "原油",
        "hf_NG": "天然气",
        "hf_ZSD": "伦锌",
        "hf_NID": "伦镍",
        "hf_PBD": "伦铅",
        "hf_SND": "伦锡",
        "hf_XPD": "钯金",
        "hf_XPT": "铂金",
        "hf_C": "玉米",
        "hf_S": "大豆",
        "hf_W": "小麦",
        "if_EC0": "欧线集运主连",
        "if_SC0": "原油主连",
        "if_SA0": "纯碱主连",
        "if_EG0": "乙二醇主连",
        "if_PP0": "聚丙烯主连",
        "if_MA0": "甲醇主连",
        "if_TA0": "PTA主连",
        "if_SH0": "烧碱主连",
        "if_FG0": "玻璃主连",
        "if_UR0": "尿素主连",
        "us_NDX": "纳斯达克100",
        "us_SPX": "标普500",
        "us_AAPL": "苹果",
        "us_NVDA": "英伟达",
        "us_TSLA": "特斯拉",
        "us_MSFT": "微软",
        "us_BABA": "阿里巴巴",
        "us_GLW": "康宁",
        "us_MU": "美光科技",
        "us_WDC": "西部数据",
        "us_SNDK": "闪迪",
        "kr_005930": "三星电子",
        "kr_000660": "SK海力士",
        "sz000100": "TCL科技",
        "sz000725": "京东方A",
        "sh600552": "凯盛科技",
        "sh600707": "彩虹股份",
        "sh688146": "中船特气",
        "sh688106": "金宏气体",
        "sh688268": "华特气体",
        "sh688981": "中芯国际",
        "sh688012": "中微公司",
        "sh688072": "拓荆科技",
        "sh688008": "澜起科技",
        "sz300308": "中际旭创",
        "bk_BK1326": "半导体设备",
        "bk_BK0457": "电网设备",
        "bk_BK1215": "通信",
        "bk_BK1590": "通信设备",
        "bk_BK1203": "非银金融",
        "bond_000012": "国债指数",
    }.get(symbol, symbol)


def _workflow_graph_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "external_risk" / "workflow_graph.json"
