from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import secrets
from typing import Any, Callable
from uuid import uuid4

from src.external_risk.intelligence import NewsPolicyRssExternalRiskProvider
from src.external_risk.service import ExternalRiskService, _risk_coefficient_level, _risk_coefficient_profile
from src.supply_chain.repository import SupplyChainRepository
from src.supply_chain.schemas import SupplierRecord
from src.supply_chain.service import SupplyChainService
from src.external_risk.schemas import ExternalRiskSignal
from src.external_risk.commodity_catalog import CATALOG_BY_SYMBOL, COMMODITY_FUTURES, alias_in_text, normalize_symbol, symbols_from_text
from src.internal_risk.schemas import RiskEventAssessmentRequest, RiskEventConfirmationUpdate
from src.internal_risk.service import InternalRiskWorkflowService
from src.risk_intake.schemas import ExternalIntakeTriageUpdate
from src.risk_intake.service import RiskIntakeService


DEBUG_ENABLED_ENV = "RISK_DEVELOPER_DEBUG_ENABLED"
DEFAULT_MANIFEST_PATH = Path("config/developer_debug_scenarios.json")
DEFAULT_RUN_ROOT = Path("output/developer_debug_runs")
VALID_DEBUG_BUSINESS_STAGES = {"formation", "research", "product", "operation", "growth", "transition"}
VALID_DEBUG_CONTROL_STAGES = {"project_initiation", "data_access", "model_training", "product_launch", "commercialization", "cross_border"}


class DeveloperDebugDisabledError(PermissionError):
    pass


class DebugScenarioNotFoundError(LookupError):
    pass


class DebugRunNotFoundError(LookupError):
    pass


def developer_debug_enabled() -> bool:
    return os.getenv(DEBUG_ENABLED_ENV, "false").strip().lower() in {"1", "true", "yes", "on"}


def _debug_business_stage(value: object) -> str:
    candidate = str(value or "").strip()
    return candidate if candidate in VALID_DEBUG_BUSINESS_STAGES else "operation"


def _debug_control_stage(value: object) -> str:
    candidate = str(value or "").strip()
    return candidate if candidate in VALID_DEBUG_CONTROL_STAGES else "commercialization"


class DeveloperDebugService:
    """Creates scenario-local file stores without changing workspace data files."""

    def __init__(
        self,
        manifest_path: Path = DEFAULT_MANIFEST_PATH,
        run_root: Path = DEFAULT_RUN_ROOT,
        subject_selector: Callable[[list[dict[str, Any]]], dict[str, Any]] | None = None,
        rss_provider_factory: Callable[[Path], Any] | None = None,
        quote_series_loader: Callable[[str], Any] | None = None,
        now_provider: Callable[[], datetime] | None = None,
    ) -> None:
        self.manifest_path = manifest_path
        self.run_root = run_root
        self._subject_selector = subject_selector or secrets.choice
        self._rss_provider_factory = rss_provider_factory
        self._quote_series_loader = quote_series_loader
        self._now_provider = now_provider or (lambda: datetime.now(timezone.utc))

    def status(self) -> dict:
        self._require_enabled()
        return {
            "enabled": developer_debug_enabled(),
            "environment_variable": DEBUG_ENABLED_ENV,
            "isolation": "Each run has its own supply_chain.json under output/developer_debug_runs.",
            "scenarios": self.list_scenarios() if self.manifest_path.exists() else [],
        }

    def list_scenarios(self) -> list[dict]:
        manifest = self._load_manifest()
        return [
            {
                "scenario_id": item["scenario_id"],
                "title": item["title"],
                "industry": item["industry"],
                "fixture_path": item["fixture_path"],
                "disclaimer": item["disclaimer"],
            }
            for item in manifest["scenarios"]
        ]

    def create_run(self, scenario_id: str) -> dict:
        self._require_enabled()
        scenario = self._scenario(scenario_id)
        now = datetime.now(timezone.utc)
        timestamp = now.strftime("%Y%m%d") + "t" + now.strftime("%H%M%S") + "z"
        run_id = f"{scenario_id}-{timestamp}-{uuid4().hex[:8]}"
        run_path = self.run_root / run_id
        run_path.mkdir(parents=True, exist_ok=False)
        self._write_run_files(run_path, scenario)
        metadata = self._load_json(run_path / "run.json")
        return self._run_summary(run_id, scenario, reset_at=datetime.now(timezone.utc).isoformat(), test_subject=metadata.get("test_subject"))

    def reset_run(self, run_id: str) -> dict:
        self._require_enabled()
        run_path = self._run_path(run_id)
        metadata = self._load_json(run_path / "run.json")
        scenario = self._scenario(metadata["scenario_id"])
        self._write_run_files(run_path, scenario, test_subject=metadata.get("test_subject"))
        return self._run_summary(run_id, scenario, reset_at=datetime.now(timezone.utc).isoformat(), test_subject=metadata.get("test_subject"))

    def suppliers(self, run_id: str) -> list[SupplierRecord]:
        self._require_enabled()
        run_path = self._run_path(run_id)
        return [SupplierRecord.model_validate(item) for item in SupplyChainRepository(run_path / "supply_chain.json").load()]

    def run_metadata(self, run_id: str) -> dict:
        self._require_enabled()
        run_path = self._run_path(run_id)
        return self._load_json(run_path / "run.json")

    def scenario_context(self, run_id: str) -> dict:
        """Compile one scenario into every front-end risk view without touching live stores."""
        self._require_enabled()
        run_path = self._run_path(run_id)
        metadata = self._load_json(run_path / "run.json")
        fixture = self._load_json(Path(metadata["fixture_path"]))
        suppliers = [item.model_dump(mode="json") for item in self.suppliers(run_id)]
        return _compile_scenario_context(metadata, fixture, suppliers)

    def live_snapshot(self, run_id: str) -> dict:
        """Capture RSS and quote data in the run directory for one selected test subject."""
        self._require_enabled()
        run_path = self._run_path(run_id)
        snapshot_path = run_path / "live_snapshot.json"
        if snapshot_path.exists():
            return self._load_json(snapshot_path)

        metadata = self._load_json(run_path / "run.json")
        fixture = self._load_json(Path(metadata["fixture_path"]))
        suppliers = [item.model_dump(mode="json") for item in self.suppliers(run_id)]
        selection = self._resolve_test_subject(metadata, fixture, suppliers)
        rss_provider = self._rss_provider_factory(run_path) if self._rss_provider_factory else NewsPolicyRssExternalRiskProvider(
            cache_path=run_path / "intelligence_feed_cache.json"
        )
        rss_signals = [_model_payload(signal) for signal in rss_provider.refresh()]
        scope_terms = _industry_scope_terms(metadata, fixture, suppliers)
        reference_time = self._now_provider()
        scoped_rss_signals = [
            signal for signal in rss_signals
            if _is_recent_market_or_industry_signal(
                signal,
                scope_terms,
                reference_time=reference_time,
            )
        ][:24]
        market_symbol = _market_symbol_for_scope(scope_terms)
        quote_payload = _load_quote_payload(
            self._quote_series_loader,
            symbol=market_symbol,
        )
        rss_live_signals = [
            {
                **signal,
                "metadata": {
                    **(signal.get("metadata") or {}),
                    "scenario_run_id": run_id,
                    "risk_scope": "industry_or_market_observation",
                    "subject_match": False,
                    "subject_node_id": None,
                },
            }
            for signal in scoped_rss_signals
        ]
        commodity_links = _commodity_links_for_chain(fixture, suppliers)
        commodity_signals = _commodity_futures_signals(
            rss_live_signals,
            quote_loader=self._quote_series_loader,
            chain_links=commodity_links or None,
        )
        chain_alerts = _live_chain_alerts(
            [*rss_live_signals, *commodity_signals],
            node_ids=[str(node.get("node_id")) for node in fixture.get("nodes", []) if node.get("node_id")],
            edges=fixture.get("edges", []),
        )
        live_signals = [*rss_live_signals, *commodity_signals]
        snapshot = {
            "run_id": run_id,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "selection": selection,
            "rss": {
                "signals": rss_live_signals,
                "matched_signal_ids": [],
                "industry_signal_ids": [signal["signal_id"] for signal in scoped_rss_signals],
                "scope_terms": scope_terms,
                "provider": _model_payload(rss_provider.status()),
                "cache_path": str(run_path / "intelligence_feed_cache.json"),
            },
            "quote": quote_payload,
            "commodity_links": commodity_links,
            "external_risk": _live_external_risk_context(
                metadata=metadata,
                selection=selection,
                signals=live_signals,
                chain_alerts=chain_alerts,
                provider_status=_model_payload(rss_provider.status()),
                quote=quote_payload,
            ),
            "market_canvas": _debug_market_canvas(fixture, suppliers),
        }
        snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
        return snapshot

    def execute_run(self, run_id: str) -> dict:
        """Exercise a local signal -> triage -> assessment -> confirmed-risk loop."""
        self._require_enabled()
        run_path = self._run_path(run_id)
        supply_service = SupplyChainService(SupplyChainRepository(run_path / "supply_chain.json"))
        internal_service = InternalRiskWorkflowService(
            run_path / "internal_risk_workflow.json",
            report_generator=_debug_assessment_report,
        )
        intake_service = RiskIntakeService(run_path / "risk_intake.json", internal_service=internal_service)
        metadata = self._load_json(run_path / "run.json")
        fixture = self._load_json(Path(metadata["fixture_path"]))
        profiles = fixture.get("scenario", {}).get("risk_profiles", [])
        suppliers = [item.model_dump(mode="json") for item in supply_service.list_suppliers()]
        subject = self._resolve_test_subject(metadata, fixture, suppliers)
        node = next((item for item in fixture.get("nodes", []) if item.get("node_id") == subject["node_id"]), None)
        if not node:
            raise RuntimeError("debug run subject references an unknown scenario node")
        profile = next((item for item in profiles if item.get("node_id") == node["node_id"]), {
            "node_id": node["node_id"],
            "severity": "medium",
            "title": f"{node.get('stage', '产业链节点')}实时核验",
            "summary": "随机选取的产业链节点需要结合真实 RSS、行情和交易材料进行人工核验。",
        })
        supplier = next(item for item in supply_service.list_suppliers() if item.supplier_id == node["supplier_id"])
        lifecycle = node.get("lifecycle", {})
        company_id = str(fixture.get("scenario", {}).get("company", {}).get("company_id") or "developer-debug-company")
        signal = ExternalRiskSignal(
            signal_id=f"debug-execute-{node['node_id']}-001", signal_type=profile.get("signal_type", "supply_chain"),
            title=profile.get("title") or f"调试：{supplier.name}风险待核验", severity=profile.get("severity", "medium"), direction="negative",
            as_of=str(fixture.get("scenario", {}).get("as_of") or "2026-08-02")[:10], entity=supplier.name,
            metric=profile.get("metric", "scenario_risk"), value=profile.get("value", "review_required"),
            affected_domains=[profile.get("external_domain", "supply_chain")], affected_supply_links=[supplier.supplier_id],
            evidence=profile.get("summary") or "开发者调试信号，需要人工核验。", source="https://example.invalid/developer-debug/signal",
            confidence=float(profile.get("confidence", 0.9)), metadata={"security_code": supplier.security_code, "supplier_id": supplier.supplier_id, "regions": [supplier.province]},
        )
        cases = intake_service.sync_external_cases(company_id, [signal])
        if len(cases) != 1:
            raise RuntimeError("debug scenario did not produce exactly one intake case")
        promoted = intake_service.triage_case(cases[0].intake_id, ExternalIntakeTriageUpdate(
            decision="promote", reviewer="developer-debug-operator",
            conclusion="关键节点命中证券代码和供应商标识，转入风险事件评估。",
            project_id=f"debug-project-{node['node_id']}",
        ))
        assessed = internal_service.assess_risk_event(promoted.internal_event_id, RiskEventAssessmentRequest(input_filters={}))
        confirmed = internal_service.confirm_risk_event(assessed.event_id, RiskEventConfirmationUpdate(
            decision="confirmed", reviewer="developer-debug-reviewer",
            conclusion="开发者测试确认：保留为高风险供应链情景，需人工复核真实商业关系。",
        ))
        result = {
            "signal_id": signal.signal_id, "intake_id": promoted.intake_id, "intake_status": promoted.status,
            "test_subject": subject,
            "matched_object_ids": [match.object_id for match in promoted.matched_objects],
            "event_id": confirmed.event_id, "event_status": confirmed.status,
            "confirmed_risk_id": confirmed.confirmed_risk_id,
            "risk_count": len(internal_service.risk_items(company_id=company_id)),
            "storage": {"supply_chain": str(run_path / "supply_chain.json"), "risk_intake": str(run_path / "risk_intake.json"), "internal_risk": str(run_path / "internal_risk_workflow.json")},
        }
        (run_path / "execution_report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return result

    def _require_enabled(self) -> None:
        if not developer_debug_enabled():
            raise DeveloperDebugDisabledError(
                f"Developer debug mode is disabled. Set {DEBUG_ENABLED_ENV}=true only in a local test environment."
            )

    def _scenario(self, scenario_id: str) -> dict:
        for scenario in self._load_manifest()["scenarios"]:
            if scenario["scenario_id"] == scenario_id:
                return scenario
        raise DebugScenarioNotFoundError(scenario_id)

    def _load_manifest(self) -> dict:
        return self._load_json(self.manifest_path)

    @staticmethod
    def _load_json(path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def _run_path(self, run_id: str) -> Path:
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,120}", run_id):
            raise DebugRunNotFoundError(run_id)
        run_path = self.run_root / run_id
        if not (run_path / "run.json").exists():
            raise DebugRunNotFoundError(run_id)
        return run_path

    def _write_run_files(self, run_path: Path, scenario: dict, test_subject: dict | None = None) -> None:
        fixture_path = Path(scenario["fixture_path"])
        fixture = self._load_json(fixture_path)
        suppliers = fixture.get("suppliers", [])
        # Validate at seed time so broken fixtures cannot be mistaken for completed tests.
        normalized = [SupplierRecord.model_validate(item).model_dump(mode="json") for item in suppliers]
        (run_path / "supply_chain.json").write_text(
            json.dumps({"version": 1, "suppliers": normalized}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        test_subject = self._resolve_test_subject({"test_subject": test_subject}, fixture, normalized)
        (run_path / "run.json").write_text(
            json.dumps(
                {
                    "run_id": run_path.name,
                    "scenario_id": scenario["scenario_id"],
                    "title": scenario["title"],
                    "industry": scenario["industry"],
                    "fixture_path": scenario["fixture_path"],
                    "internal_fixture_path": scenario["internal_fixture_path"],
                    "intake_fixture_path": scenario["intake_fixture_path"],
                    "disclaimer": scenario["disclaimer"],
                    "test_subject": test_subject,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        metadata = self._load_json(run_path / "run.json")
        context = _compile_scenario_context(metadata, fixture, normalized)
        workflow = dict(context["internal_risk"])
        workflow.pop("management_assistance", None)
        (run_path / "internal_risk_workflow.json").write_text(
            json.dumps({"version": "0.1.0", "scope": "developer-debug generated workflow", "workflow": workflow}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        scope = context["risk_intake"]["scope"]
        (run_path / "risk_intake.json").write_text(
            json.dumps({"version": "0.1.0", "scopes": {scope["company_id"]: scope}, "cases": [], "sync_batches": []}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _run_summary(run_id: str, scenario: dict, reset_at: str, test_subject: dict | None = None) -> dict:
        return {
            "run_id": run_id,
            "scenario_id": scenario["scenario_id"],
            "title": scenario["title"],
            "industry": scenario["industry"],
            "reset_at": reset_at,
            "disclaimer": scenario["disclaimer"],
            "test_subject": test_subject,
        }

    def _resolve_test_subject(self, metadata: dict, fixture: dict, suppliers: list[dict]) -> dict:
        existing = metadata.get("test_subject") if isinstance(metadata, dict) else None
        if isinstance(existing, dict) and existing.get("node_id") and existing.get("supplier_id") and existing.get("security_code"):
            return existing
        supplier_by_id = {str(item.get("supplier_id")): item for item in suppliers}
        candidates = []
        for node in fixture.get("nodes", []):
            supplier = supplier_by_id.get(str(node.get("supplier_id")))
            if not supplier or not supplier.get("security_code"):
                continue
            candidates.append({
                "node_id": node["node_id"],
                "supplier_id": supplier["supplier_id"],
                "name": supplier["name"],
                "security_code": supplier["security_code"],
                "stage": node.get("stage") or supplier.get("category") or "产业链节点",
                "selected_at": datetime.now(timezone.utc).isoformat(),
            })
        if not candidates:
            raise RuntimeError("debug scenario requires at least one node with a security code")
        return dict(self._subject_selector(candidates))


def _model_payload(value: Any) -> dict:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "dict"):
        return value.dict()
    if isinstance(value, dict):
        return value
    raise TypeError(f"unsupported debug snapshot payload: {type(value)!r}")


def _signal_matches_subject(signal: dict, selection: dict) -> bool:
    text = " ".join(str(signal.get(key) or "") for key in ("title", "entity", "evidence")).casefold()
    terms = [str(selection.get("name") or "").strip(), str(selection.get("security_code") or "").strip()]
    return any(len(term) >= 2 and term.casefold() in text for term in terms)


def _legacy_subject_chain_alerts(
    signals: list[dict],
    *,
    selected_node_id: str,
    selected_symbol: str,
    edges: list[dict],
) -> list[dict]:
    downstream: dict[str, list[str]] = {}
    for edge in edges:
        source, target = edge.get("from"), edge.get("to")
        if source and target:
            downstream.setdefault(str(source), []).append(str(target))
    path = [selected_node_id]
    queue = [selected_node_id]
    while queue:
        source = queue.pop(0)
        for target in downstream.get(source, []):
            if target not in path:
                path.append(target)
                queue.append(target)
    alerts = []
    for signal in signals:
        alerts.append({
            "alert_id": f"live-alert-{signal['signal_id']}",
            "signal_id": signal["signal_id"],
            "severity": signal.get("severity", "medium"),
            "affected_node_ids": path,
            "affected_symbols": [selected_symbol],
            "path_node_ids": path,
            "association_type": "industry",
            "association_tags": ["rss_subject_match"],
            "transmission_score": min(0.95, 0.45 + 0.08 * max(0, len(path) - 1)),
            "summary": f"RSS 信息命中测试主体，按场景定义的上游至下游关系展示潜在传导，仍需人工核验。{signal.get('title', '')}",
            "evidence_refs": [str(signal.get("source") or "")],
        })
    return alerts


def _legacy_subject_external_risk_context(
    *,
    metadata: dict,
    selection: dict,
    signals: list[dict],
    chain_alerts: list[dict],
    provider_status: dict,
    quote: dict,
) -> dict:
    risk_rank = {"low": 18, "medium": 42, "high": 70, "critical": 92}
    matched_signals = [signal for signal in signals if (signal.get("metadata") or {}).get("subject_match")]
    coefficient = round(sum(risk_rank.get(str(signal.get("severity")), 42) for signal in matched_signals) / max(1, len(matched_signals)))
    quote_available = bool(quote.get("points")) and quote.get("source") != "provider_unavailable"
    live_available = bool(signals) or quote_available
    return {
        "company": {
            "company_id": selection["supplier_id"],
            "name": selection["name"],
            "tech_sector": metadata["industry"],
            "lifecycle_stage": "operation",
            "core_products": [selection["stage"]],
            "key_regions": [],
            "sensitive_domains": sorted({domain for signal in signals for domain in signal.get("affected_domains", [])}),
        },
        "as_of": quote.get("as_of") or datetime.now(timezone.utc).isoformat(),
        "summary": {
            "headline": f"{selection['name']}实时 RSS 与行情监测",
            "signal_count": len(signals),
            "live_signal_count": len(signals),
            "high_or_above_count": len([signal for signal in matched_signals if signal.get("severity") in {"high", "critical"}]),
            "legal_task_count": 0,
            "risk_coefficient": coefficient if matched_signals else 0,
            "risk_coefficient_level": "high" if coefficient >= 67 else "medium" if coefficient >= 34 else "low",
            "risk_coefficient_formula": "R=已读取 RSS 信号的严重度聚合；未命中主体的信息不作为企业风险。",
            "risk_coefficient_components": {"severity": coefficient / 100 if matched_signals else 0, "chain_transmission": 0.0, "legal_exposure": 0.0},
            "risk_coefficient_quality": 1.0 if live_available else 0.0,
            "provider_mode": "live" if live_available else "disabled",
            "data_mode": "live_provider" if live_available else "unavailable_live_provider",
        },
        "signals": signals,
        "chain_alerts": chain_alerts,
        "findings": [],
        "legal_query_tasks": [],
        "provider_statuses": [provider_status],
        "guardrails": [
            "RSS 和行情均为实时事实来源；未命中测试主体的 RSS 信息仅作外部观察，不构成企业风险。",
            "产业链连线描述的是调试场景位置，不代表已核实交易或控制关系。",
        ],
    }


_MARKET_RELEVANCE_TERMS = {
    "半导体", "芯片", "晶圆", "封装", "光刻", "集成电路", "人工智能", "ai", "算力", "服务器",
    "新能源", "储能", "电池", "光伏", "风电", "电网", "铜", "铝", "锡", "镍", "锌",
    "原油", "天然气", "能源", "海运", "航运", "运价", "集运", "物流", "供应链", "关税",
    "贸易", "出口管制", "出口限制", "市场", "经济", "利率", "汇率", "通胀", "价格",
}
_COMMODITY_TERMS = tuple((item.aliases, item.symbol) for item in COMMODITY_FUTURES)


def _industry_scope_terms(metadata: dict, fixture: dict, suppliers: list[dict]) -> list[str]:
    """Derive reusable scope vocabulary from the loaded scenario, not its test subject."""
    values = [str(metadata.get("industry") or "")]
    values.extend(str(node.get("stage") or "") for node in fixture.get("nodes", []))
    for supplier in suppliers:
        values.extend([str(supplier.get("category") or ""), *[str(tag) for tag in supplier.get("external_tags", [])]])
    scope_text = " ".join(values).casefold()
    terms = {term for term in _MARKET_RELEVANCE_TERMS if term.casefold() in scope_text}
    # Preserve distinct industry names for fixtures outside the built-in vocabulary.
    terms.update(match for match in re.findall(r"[\u4e00-\u9fff]{3,12}|[A-Za-z][A-Za-z0-9 _-]{2,24}", values[0]) if match.strip())
    return sorted(terms, key=len, reverse=True)


def _signal_datetime(value: object) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.replace(tzinfo=parsed.tzinfo or timezone.utc).astimezone(timezone.utc)


def _is_recent_market_or_industry_signal(
    signal: dict,
    scope_terms: list[str],
    *,
    reference_time: datetime | None = None,
) -> bool:
    observed_at = _signal_datetime(signal.get("as_of"))
    now = reference_time or datetime.now(timezone.utc)
    now = now.replace(tzinfo=now.tzinfo or timezone.utc).astimezone(timezone.utc)
    if observed_at is None or observed_at < now - timedelta(days=14) or observed_at > now + timedelta(days=1):
        return False
    content = " ".join(str(signal.get(key) or "") for key in ("title", "entity", "evidence")).casefold()
    domains = {str(item) for item in signal.get("affected_domains", [])}
    scope_match = any(term.casefold() in content for term in scope_terms if len(term.strip()) >= 2)
    # A generic contract or export-control notice is not sufficient by itself:
    # it must mention the configured industry.  This keeps unrelated sector
    # notices out of the market/industry observation stream.
    market_domain = bool(domains & {"market", "supply_chain"})
    return scope_match or market_domain


def _market_symbol_for_scope(scope_terms: list[str]) -> str:
    scope = " ".join(scope_terms).casefold()
    if any(term in scope for term in ("半导体", "芯片", "晶圆", "集成电路")):
        return "bk_BK1326"
    if any(term in scope for term in ("电网", "储能", "新能源", "电池", "光伏", "风电")):
        return "bk_BK0457"
    return "sh000001"


def _unavailable_quote_payload(symbol: str, reason: str) -> dict:
    return {
        "symbol": symbol,
        "name": symbol,
        "provider": "live_quote_service",
        "interval": "intraday",
        "source": "provider_unavailable",
        "as_of": "",
        "points": [],
        "reference_price": None,
        "change_rate": None,
        "change_basis": "unavailable",
        "instrument_status": "unknown",
        "price_limit_rate": None,
        "price_limit_label": reason,
    }


def _load_quote_payload(quote_loader: Callable[[str], Any] | None, *, symbol: str) -> dict:
    try:
        quote = quote_loader(symbol) if quote_loader else ExternalRiskService().quote_series(symbol=symbol, interval="intraday")
        return _model_payload(quote)
    except Exception as exc:
        return _unavailable_quote_payload(symbol, f"quote request failed: {type(exc).__name__}")


def _latest_quote_value(quote: dict) -> float | None:
    points = quote.get("points") or []
    if not points:
        return None
    value = points[-1].get("close") if isinstance(points[-1], dict) else None
    return float(value) if isinstance(value, (int, float)) else None


def _commodity_links_for_chain(fixture: dict, suppliers: list[dict]) -> dict[str, dict[str, Any]]:
    """Read scenario-declared commodity exposures without selecting one industry in code."""
    links: dict[str, dict[str, Any]] = {}
    raw_links = fixture.get("commodity_links") or fixture.get("scenario", {}).get("commodity_links") or []
    if isinstance(raw_links, dict):
        raw_links = [{"symbol": symbol, **(value if isinstance(value, dict) else {})} for symbol, value in raw_links.items()]
    for raw in raw_links:
        if isinstance(raw, str):
            raw = {"symbol": raw}
        if not isinstance(raw, dict):
            continue
        symbol = normalize_symbol(raw.get("symbol"))
        if not symbol:
            continue
        links[symbol] = {
            "symbol": symbol,
            "name": CATALOG_BY_SYMBOL[symbol].name,
            "relation": str(raw.get("relation") or "scenario_declared_cost_or_supply_link"),
            "node_ids": [str(item) for item in raw.get("node_ids", raw.get("nodeIds", [])) if str(item).strip()],
            "source_ids": [str(item) for item in raw.get("source_ids", raw.get("sourceIds", [])) if str(item).strip()],
        }
    supplier_by_id = {item.get("supplier_id"): item for item in suppliers}
    for node in fixture.get("nodes", []):
        for value in node.get("commodity_symbols", node.get("commoditySymbols", [])) or []:
            symbol = normalize_symbol(value)
            if not symbol:
                continue
            links.setdefault(symbol, {
                "symbol": symbol,
                "name": CATALOG_BY_SYMBOL[symbol].name,
                "relation": "node_declared_cost_or_supply_link",
                "node_ids": [],
                "source_ids": [],
            })["node_ids"].append(str(node.get("node_id")))
    # A scenario may declare aliases on a supplier instead of repeating symbols.
    for node in fixture.get("nodes", []):
        supplier = supplier_by_id.get(node.get("supplier_id"), {})
        text = " ".join(str(value or "") for value in [node.get("stage"), supplier.get("category"), *supplier.get("external_tags", [])])
        for symbol in symbols_from_text(text):
            links.setdefault(symbol, {
                "symbol": symbol,
                "name": CATALOG_BY_SYMBOL[symbol].name,
                "relation": "catalog_resolved_material_link",
                "node_ids": [],
                "source_ids": [],
            })["node_ids"].append(str(node.get("node_id")))
    for item in links.values():
        item["node_ids"] = list(dict.fromkeys(item["node_ids"]))
    return links


def _commodity_futures_signals(
    signals: list[dict],
    *,
    quote_loader: Callable[[str], Any] | None,
    chain_links: dict[str, dict[str, Any]] | None = None,
) -> list[dict]:
    """Create reviewable commodity signals only where the source states a commodity linkage."""
    results: list[dict] = []
    requested: dict[str, dict] = {}
    for signal in signals:
        if signal.get("severity") not in {"medium", "high", "critical"}:
            continue
        content = " ".join(str(signal.get(key) or "") for key in ("title", "entity", "evidence")).casefold()
        matches = [(terms, symbol) for terms, symbol in _COMMODITY_TERMS if any(alias_in_text(term, content) for term in terms)]
        if chain_links is not None:
            matches = [match for match in matches if match[1] in chain_links]
        match = matches[0] if matches else None
        if match is None:
            continue
        requested.setdefault(match[1], {"terms": match[0], "trigger": signal})
    for symbol, request in requested.items():
        quote = _load_quote_payload(quote_loader, symbol=symbol)
        trigger = request["trigger"]
        link = (chain_links or {}).get(symbol, {})
        latest = _latest_quote_value(quote)
        points = quote.get("points") or []
        previous = quote.get("reference_price")
        if previous is None and points and isinstance(points[0], dict):
            previous = points[0].get("baseline_price")
        available = bool(points) and quote.get("source") != "provider_unavailable"
        results.append({
            "signal_id": f"commodity-link-{trigger['signal_id']}-{symbol}", "signal_type": "commodity_futures",
            "title": f"商品期货联动：{quote.get('name') or symbol}", "severity": trigger["severity"],
            "direction": trigger.get("direction", "neutral"), "as_of": quote.get("as_of") or trigger["as_of"],
            "entity": quote.get("name") or symbol, "metric": "intraday_quote", "value": latest,
            "threshold": None, "affected_domains": ["market", "supply_chain", "contract"],
            "evidence": f"原始事件包含关联线索“{next(term for term in request['terms'] if term in (' '.join(str(trigger.get(key) or '') for key in ('title', 'entity', 'evidence'))).casefold())}”；商品报价由 {quote.get('source')} 提供。",
            "source": f"{trigger['source']} | quote:{quote.get('source')}", "confidence": trigger.get("confidence", 0.7),
            "metadata": {
                "linkage_status": "available" if available else "unavailable", "trigger_signal_id": trigger["signal_id"],
                "contracts": [symbol], "instrument_code": symbol, "latest_price": latest,
                "previous_close": previous, "change_rate": quote.get("change_rate"),
                "quote_source": quote.get("source"), "quote_as_of": quote.get("as_of"),
                "chain_linked": bool(link), "linked_node_ids": link.get("node_ids", []),
                "chain_link_relation": link.get("relation", "rss_explicit_commodity_link"),
            },
        })
    return results


def _live_chain_alerts(signals: list[dict], *, node_ids: list[str], edges: list[dict]) -> list[dict]:
    return [{
        "alert_id": f"live-alert-{signal['signal_id']}", "signal_id": signal["signal_id"],
        "severity": signal.get("severity", "medium"), "affected_node_ids": node_ids,
        "affected_symbols": [], "path_node_ids": [], "association_type": "industry_scope",
        "association_tags": ["industry_or_market_observation"], "transmission_score": 0.0,
        "summary": f"行业或全市场外部观察：{signal.get('title', '')}。仅表示场景产业链可能受影响，不指向单一企业或已核实传导路径。",
        "evidence_refs": [str(signal.get("source") or "")],
    } for signal in signals]


def _live_external_risk_context(*, metadata: dict, selection: dict, signals: list[dict], chain_alerts: list[dict], provider_status: dict, quote: dict) -> dict:
    market_signals = [ExternalRiskSignal.model_validate(signal) for signal in signals]
    risk_profile = _risk_coefficient_profile(market_signals, chain_alerts=[])
    coefficient = risk_profile["score"]
    quote_available = bool(quote.get("points")) and quote.get("source") != "provider_unavailable"
    live_available = bool(signals) or quote_available
    return {
        "company": {"company_id": f"{metadata['scenario_id']}-market-context", "name": f"{metadata['industry']}市场与产业链", "tech_sector": metadata["industry"], "lifecycle_stage": "operation", "core_products": ["全市场", "产业链"], "key_regions": [], "sensitive_domains": sorted({domain for signal in signals for domain in signal.get("affected_domains", [])})},
        "as_of": quote.get("as_of") or datetime.now(timezone.utc).isoformat(),
        "summary": {"headline": f"{metadata['industry']}市场与产业链实时 RSS 与行情监测", "signal_count": len(signals), "live_signal_count": len(signals), "high_or_above_count": len([signal for signal in market_signals if signal.severity in {"high", "critical"}]), "legal_task_count": 0, "risk_coefficient": coefficient, "risk_coefficient_level": _risk_coefficient_level(coefficient), "risk_coefficient_formula": r"R=100\left(0.22S+0.20M+0.16T+0.16C+0.14L+0.12P\right),\quad S=1-\prod_i\left(1-c_ir_i s_i\right),\quad C=1-\prod_j\left(1-a_j\right)", "risk_coefficient_components": risk_profile["components"], "risk_coefficient_quality": risk_profile["quality"] if live_available else 0.0, "provider_mode": "live" if live_available else "disabled", "data_mode": "live_provider" if live_available else "unavailable_live_provider"},
        "signals": signals, "chain_alerts": chain_alerts, "findings": [], "legal_query_tasks": [], "provider_statuses": [provider_status],
        "guardrails": ["外部风险只显示近期的全市场或产业链事实观察，不将随机选择的测试企业作为外部风险归因对象。", "中高风险事件的商品期货联动仅在标题或证据出现明确商品、能源或物流线索时展示；无可验证线索会明确标记为不适用。", "产业链连线描述的是调试场景位置，不代表已核实交易或控制关系。"],
    }


def _debug_market_canvas(fixture: dict, suppliers: list[dict]) -> dict:
    suppliers_by_id = {item["supplier_id"]: item for item in suppliers}
    nodes = []
    for node in fixture.get("nodes", []):
        supplier = suppliers_by_id.get(node.get("supplier_id"))
        if not supplier or not supplier.get("security_code"):
            continue
        nodes.append({
            "id": node["node_id"],
            "symbol": supplier["security_code"],
            "name": supplier["name"],
            "node_kind": "supplier",
            "supplier_id": supplier["supplier_id"],
            "lane": "产业链节点",
            "group": node.get("stage") or supplier.get("category"),
        })
    node_ids = {node["id"] for node in nodes}
    links = [
        {"source": edge["from"], "target": edge["to"], "relation": edge.get("relation_type") or "产业链关系"}
        for edge in fixture.get("edges", [])
        if edge.get("from") in node_ids and edge.get("to") in node_ids
    ]
    return {"version": "developer-debug", "nodes": nodes, "links": links, "read_only": True}


def _debug_assessment_report(scenario: str, **_: object) -> dict:
    return {
        "risk_level": "high",
        "executive_summary": "开发者调试评估：关键供应链节点的政策变化需要人工复核。",
        "review_reasons": ["本场景的企业关系为公开信息模拟，必须核验真实交易关系。"],
        "evidence_chain": [],
        "source_analysis": {"missing_evidence": ["企业交易关系及受限技术的当前证据"]},
        "scenario": scenario,
    }


def _compile_scenario_context(metadata: dict, fixture: dict, suppliers: list[dict]) -> dict:
    """Data-driven adapter shared by every debug industry; no industry name is special-cased."""
    scenario = fixture.get("scenario", {})
    company = scenario.get("company", {})
    profiles = scenario.get("risk_profiles", [])
    nodes = fixture.get("nodes", [])
    edges = fixture.get("edges", [])
    sources = fixture.get("sources", [])
    supplier_by_id = {item["supplier_id"]: item for item in suppliers}
    node_by_id = {item["node_id"]: item for item in nodes}
    source_by_id = {item["source_id"]: item for item in sources}
    company_id = str(company.get("company_id") or "developer-debug-company")
    as_of = str(scenario.get("as_of") or "2026-08-02T00:00:00Z")

    lifecycle_states = []
    objects = []
    for node in nodes:
        supplier = supplier_by_id.get(node.get("supplier_id"))
        if not supplier:
            continue
        lifecycle = node.get("lifecycle", {})
        state_id = f"debug-state-{node['node_id']}"
        project_id = f"debug-project-{node['node_id']}"
        lifecycle_states.append({
            "state_id": state_id, "scope_id": project_id, "scope_type": "supplier",
            "business_stage": _debug_business_stage(lifecycle.get("business_stage")),
            "control_stage": _debug_control_stage(lifecycle.get("control_stage")), "status": "active",
            "scenario_stage_id": lifecycle.get("stage_id") or lifecycle.get("scenario_stage_id") or node["node_id"],
            "effective_from": as_of, "owner": lifecycle.get("owner", "开发者调试负责人"),
            "basis": f"产业链阶段：{node.get('stage', supplier['category'])}",
        })
        objects.append({
            "object_id": f"debug-object-{node['node_id']}", "object_type": "supplier", "name": supplier["name"],
            "aliases": [supplier["name"]], "external_tags": supplier.get("external_tags", []),
            "security_codes": [supplier["security_code"]] if supplier.get("security_code") else [],
            "regions": [value for value in [supplier.get("province"), supplier.get("country")] if value],
            "supplier_id": supplier["supplier_id"], "project_id": project_id,
            "lifecycle_state_ids": [state_id], "active": True,
        })

    signals = []
    risk_items = []
    tasks = []
    gates = []
    cases = []
    chain_alerts = []
    legal_tasks = []
    profile_records = []
    for index, profile in enumerate(profiles, start=1):
        node = node_by_id.get(profile.get("node_id"))
        if not node or node.get("supplier_id") not in supplier_by_id:
            continue
        supplier = supplier_by_id[node["supplier_id"]]
        lifecycle = node.get("lifecycle", {})
        control_stage = _debug_control_stage(lifecycle.get("control_stage"))
        source_ids = [*node.get("source_ids", []), *profile.get("source_ids", [])]
        evidence_refs = [source_by_id[item]["url"] for item in source_ids if item in source_by_id]
        risk_id = f"debug-risk-{node['node_id']}-{index:02d}"
        signal_id = f"debug-signal-{node['node_id']}-{index:02d}"
        severity = profile.get("severity", "medium")
        domain = profile.get("risk_domain", "cross_border_supply_chain")
        external_domain = profile.get("external_domain", "supply_chain")
        title = profile.get("title") or f"{supplier['name']}：{node.get('stage', supplier['category'])}风险待核验"
        summary = profile.get("summary") or f"产业链节点“{node.get('stage', supplier['category'])}”需要核验供应连续性与合规边界。"
        signal = {
            "signal_id": signal_id, "signal_type": profile.get("signal_type", "supply_chain"),
            "title": title, "severity": severity, "direction": "negative", "as_of": as_of[:10],
            "entity": supplier["name"], "metric": profile.get("metric", "scenario_risk"),
            "value": profile.get("value", None), "affected_domains": [external_domain],
            "affected_supply_links": [supplier["supplier_id"]], "evidence": summary,
            "source": evidence_refs[0] if evidence_refs else "https://example.invalid/developer-debug/source",
            "confidence": float(profile.get("confidence", 0.8)),
            "metadata": {"security_code": supplier.get("security_code"), "supplier_id": supplier["supplier_id"], "scenario_run_id": metadata["run_id"]},
        }
        signals.append(signal)
        risk_items.append({
            "risk_id": risk_id, "company_id": company_id, "project_id": f"debug-project-{node['node_id']}",
            "title": title, "lifecycle_stage": control_stage,
            "risk_domain": domain, "risk_level": severity, "status": "open", "trigger_facts": [summary],
            "evidence_refs": evidence_refs, "legal_query_seeds": [profile.get("legal_query") or f"{title} 的合规核验要点"],
            "missing_materials": profile.get("missing_materials", ["真实交易关系与合同条款证据"]),
            "task_ids": [f"debug-task-{node['node_id']}-{index:02d}"], "origin": "external_signal",
            "external_intake_id": f"debug-intake-{node['node_id']}-{index:02d}",
            "matched_object_ids": [f"debug-object-{node['node_id']}"], "signal_snapshot": signal,
        })
        tasks.append({
            "task_id": f"debug-task-{node['node_id']}-{index:02d}", "company_id": company_id,
            "project_id": f"debug-project-{node['node_id']}", "risk_id": risk_id,
            "title": profile.get("action") or f"核验{supplier['name']}相关风险证据", "owner": lifecycle.get("owner", "开发者调试负责人"),
            "due_date": "2026-08-16", "status": "not_started", "evidence_refs": evidence_refs,
            "requires_manual_review": True, "updated_at": as_of, "status_history": [],
        })
        gates.append({
            "gate_id": f"debug-gate-{node['node_id']}-{index:02d}", "company_id": company_id,
            "project_id": f"debug-project-{node['node_id']}", "title": f"{node.get('stage', supplier['category'])}风险核验门禁",
            "lifecycle_stage": control_stage, "decision": "rectification_required",
            "owner": lifecycle.get("owner", "开发者调试负责人"), "risk_item_ids": [risk_id],
            "checks": [{"check_id": f"debug-check-{node['node_id']}-{index:02d}", "title": "交易与合规证据核验", "status": "missing", "evidence_refs": evidence_refs}],
            "decision_history": [],
        })
        cases.append({
            "intake_id": f"debug-intake-{node['node_id']}-{index:02d}", "company_id": company_id,
            "signal": {**signal, "observed_at": as_of},
            "matched_objects": [{"object_id": f"debug-object-{node['node_id']}", "match_type": "supplier_id", "matched_values": [supplier["supplier_id"]], "score": 1.0, "rule_id": "debug_scenario_node"}],
            "risk_domain": domain, "lifecycle_state_ids": [f"debug-state-{node['node_id']}"],
            "target_lifecycle_stage": control_stage, "status": "pending_triage",
        })
        chain_alerts.append({
            "alert_id": f"debug-alert-{node['node_id']}-{index:02d}", "signal_id": signal_id, "severity": severity,
            "affected_node_ids": [node["node_id"]], "affected_symbols": [supplier.get("security_code")],
            "path_node_ids": [edge["from"] for edge in edges if edge.get("to") == node["node_id"]] + [node["node_id"]],
            "association_type": "industry", "association_tags": [node.get("stage", "产业链")],
            "transmission_score": float(profile.get("transmission_score", 0.7)), "summary": summary, "evidence_refs": evidence_refs,
        })
        legal_tasks.append({
            "task_id": f"debug-legal-{node['node_id']}-{index:02d}", "finding_id": risk_id,
            "risk_domain": external_domain, "severity": severity,
            "query": profile.get("legal_query") or f"{title} 的合同与合规核验要点",
            "fact_background": summary, "triggering_signal_ids": [signal_id], "evidence_refs": evidence_refs,
            "metadata": {"origin": "developer_debug_scenario", "signal_source": signal["source"]},
        })
        profile_records.append({
            "node_id": node["node_id"],
            "signal_id": signal_id,
            "risk_id": risk_id,
            "severity": severity,
            "evidence_refs": evidence_refs,
            "recommended_action": profile.get("action") or f"核验{supplier['name']}相关风险证据",
            "title": title,
            "summary": summary,
        })

    risk_score = min(100, round(sum({"low": 18, "medium": 42, "high": 70, "critical": 92}.get(item["severity"], 42) for item in signals) / max(len(signals), 1)))
    severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    configured_stages = scenario.get("lifecycle_stages") or []
    stage_specs = []
    if configured_stages:
        assigned_node_ids = set()
        for index, configured in enumerate(configured_stages, start=1):
            stage_id = str(configured.get("id") or configured.get("stage_id") or f"scenario-stage-{index}")
            configured_node_ids = configured.get("node_ids") or configured.get("nodeIds") or configured.get("nodes") or []
            configured_node_ids = [str(value) for value in configured_node_ids]
            if not configured_node_ids:
                configured_node_ids = [
                    node["node_id"] for node in nodes
                    if (node.get("lifecycle", {}).get("stage_id") or node.get("lifecycle", {}).get("scenario_stage_id")) == stage_id
                ]
            assigned_node_ids.update(configured_node_ids)
            stage_specs.append({"config": configured, "stage_id": stage_id, "phase_order": configured.get("order", configured.get("phase_order", index)), "node_ids": configured_node_ids})
        # A fixture may define a lifecycle directory and add nodes without editing that directory.
        for node in nodes:
            if node["node_id"] not in assigned_node_ids:
                stage_specs.append({"config": {}, "stage_id": f"debug-stage-{node['node_id']}", "phase_order": len(stage_specs) + 1, "node_ids": [node["node_id"]]})
    else:
        stage_specs = [
            {"config": {}, "stage_id": f"debug-stage-{node['node_id']}", "phase_order": index, "node_ids": [node["node_id"]]}
            for index, node in enumerate(nodes, start=1)
        ]

    lifecycle_product_stages = []
    for phase_order, stage_spec in enumerate(sorted(stage_specs, key=lambda item: (float(item["phase_order"]) if str(item["phase_order"]).replace('.', '', 1).isdigit() else 0, item["stage_id"])), start=1):
        configured = stage_spec["config"]
        stage_nodes = [node for node in nodes if node["node_id"] in set(stage_spec["node_ids"])]
        if not stage_nodes:
            continue
        suppliers_for_stage = [supplier_by_id[node.get("supplier_id")] for node in stage_nodes if node.get("supplier_id") in supplier_by_id]
        if not suppliers_for_stage:
            continue
        node_profiles = [item for item in profile_records if item["node_id"] in {node["node_id"] for node in stage_nodes}]
        risk_level = max(
            (item["severity"] for item in node_profiles),
            key=lambda value: severity_order.get(value, 0),
            default="low",
        )
        stage_label = str(configured.get("label") or configured.get("name") or stage_nodes[0].get("stage") or suppliers_for_stage[0].get("category") or suppliers_for_stage[0]["name"])
        stage_business = configured.get("business_stage") or configured.get("businessStage") or stage_nodes[0].get("lifecycle", {}).get("business_stage") or "operation"
        stage_control = configured.get("control_stage") or configured.get("controlStage") or stage_nodes[0].get("lifecycle", {}).get("control_stage") or "cross_border"
        project_ids = [f"debug-project-{node['node_id']}" for node in stage_nodes]
        state_ids = [f"debug-state-{node['node_id']}" for node in stage_nodes]
        lifecycle_product_stages.append({
            "stage_id": stage_spec["stage_id"],
            "label": stage_label,
            "scope": str(configured.get("scope") or f"{stage_label}节点：{'、'.join(item['name'] for item in suppliers_for_stage)}；按场景配置连接的内外部风险、证据和控制动作。"),
            "phase_order": phase_order,
            "risk_level": risk_level,
            "risk_ids": [item["risk_id"] for item in node_profiles],
            "evidence_refs": sorted({ref for item in node_profiles for ref in item["evidence_refs"]}),
            "recommended_actions": list(dict.fromkeys(item["recommended_action"] for item in node_profiles)),
            "business_stage": _debug_business_stage(stage_business),
            "control_stage": _debug_control_stage(stage_control),
            "project_ids": project_ids,
            "state_ids": state_ids,
            "node_ids": [node["node_id"] for node in stage_nodes],
            "supplier_ids": [supplier["supplier_id"] for supplier in suppliers_for_stage],
            "external_domains": list(dict.fromkeys(
                value for value in (
                    configured.get("external_domains") or configured.get("externalDomains") or []
                )
            )) or list(dict.fromkeys(
                value for node in stage_nodes for value in node.get("external_domains", [])
            )),
            "scenario_driven": True,
        })
    node_to_stage_id = {
        node_id: stage["stage_id"]
        for stage in lifecycle_product_stages
        for node_id in stage["node_ids"]
    }
    for record in profile_records:
        stage_id = node_to_stage_id.get(record["node_id"])
        if not stage_id:
            continue
        signal = next((item for item in signals if item["signal_id"] == record["signal_id"]), None)
        if signal:
            signal["lifecycle_stage_ids"] = [stage_id]
            signal.setdefault("metadata", {})["lifecycle_stage_id"] = stage_id
    lifecycle_product = {
        "company_id": company_id,
        "company_name": company.get("name", metadata["title"]),
        "title": f"{metadata['industry']}全生命周期",
        "description": "生命周期阶段、风险、门禁、任务和证据均由当前调试场景的产业链节点生成。",
        "scenario_driven": True,
        "source": "developer_debug_scenario",
        "stage_count": len(lifecycle_product_stages),
        "risk_count": len(risk_items),
        "stages": lifecycle_product_stages,
    }
    context = {
        "run": metadata,
        "supply_chain": {"suppliers": suppliers, "nodes": nodes, "edges": edges, "sources": sources},
        "risk_intake": {"scope": {"company_id": company_id, "name": company.get("name", metadata["title"]), "profile_version": "debug-1", "industry_package": metadata["industry"], "objects": objects, "lifecycle_states": lifecycle_states, "lifecycle_state_history": [], "updated_at": as_of}, "cases": cases, "sync_batches": []},
        "internal_risk": {"company_id": company_id, "as_of": as_of, "risk_items": risk_items, "risk_events": [], "gates": gates, "remediation_tasks": tasks, "manual_reviews": [], "remediation_suggestions": [], "reminders": [], "risk_acceptances": [], "guardrails": [metadata["disclaimer"]], "management_assistance": {"suggestions": [], "reminders": []}},
        "external_risk": {"company": {"company_id": company_id, "name": company.get("name", metadata["title"]), "tech_sector": metadata["industry"], "lifecycle_stage": "operation", "core_products": [node.get("stage") for node in nodes], "key_regions": sorted({item.get("province") for item in suppliers if item.get("province")}), "sensitive_domains": sorted({domain for signal in signals for domain in signal["affected_domains"]})}, "as_of": as_of, "summary": {"headline": f"{metadata['industry']}产业链调试信号", "signal_count": len(signals), "live_signal_count": 0, "high_or_above_count": len([item for item in signals if item["severity"] in {"high", "critical"}]), "legal_task_count": len(legal_tasks), "risk_coefficient": risk_score, "risk_coefficient_level": "high" if risk_score >= 67 else "medium" if risk_score >= 34 else "low", "risk_coefficient_formula": "R=场景节点风险聚合分", "risk_coefficient_components": {"severity": risk_score / 4, "chain_transmission": min(24, len(edges) * 3), "legal_exposure": min(24, len(legal_tasks) * 4)}, "risk_coefficient_quality": 1.0, "provider_mode": "fixture", "data_mode": "fixture_sample"}, "signals": signals, "chain_alerts": chain_alerts, "findings": [], "legal_query_tasks": legal_tasks, "provider_statuses": [{"provider_id": "developer-debug-scenario", "provider_type": "supply_chain", "status": "fixture_only", "mode": "fixture", "message": "由场景节点、边和风险配置生成", "runtime_access": "fixture_only"}], "guardrails": [metadata["disclaimer"]]},
        "lifecycle_product": lifecycle_product,
        "lifecycle": {
            "chain_stages": scenario.get("chain_stages", []),
            "stage_count": len(lifecycle_product_stages),
            "risk_count": len(risk_items),
            "scenario_driven": True,
            "stages": lifecycle_product_stages,
            "product": lifecycle_product,
        },
    }
    return context
