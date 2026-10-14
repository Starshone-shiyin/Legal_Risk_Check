from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

from tools.check_scenario_registry import load_json, validate_scenario_registry


DEFAULT_REGISTRY_PATH = Path("config/scenario_registry.json")
DEFAULT_ANCHOR_RULES_PATH = Path("config/rag_anchor_rules.json")
DEFAULT_RISK_RULES_PATH = Path("config/risk_payload_supplement_rules.json")
DEFAULT_EVAL_CASES_PATH = Path("tests/rag_eval_cases.json")


class ScenarioRegistryError(RuntimeError):
    """Raised when the read-only scenario registry cannot be loaded or validated."""


def _normalize_path(path: str | Path) -> str:
    return str(Path(path))


@lru_cache(maxsize=8)
def _load_validated_registry(
    registry_path: str,
    anchor_rules_path: str,
    risk_rules_path: str,
    eval_cases_path: str,
) -> dict[str, Any]:
    try:
        registry = load_json(registry_path)
        anchor_config = load_json(anchor_rules_path)
        risk_config = load_json(risk_rules_path)
        eval_path = Path(eval_cases_path)
        eval_config = load_json(eval_path) if eval_path.exists() else {}
    except Exception as exc:
        raise ScenarioRegistryError(f"failed to load scenario registry inputs: {exc}") from exc

    errors, _audit = validate_scenario_registry(registry, anchor_config, risk_config, eval_config)
    if errors:
        message = "; ".join(errors)
        raise ScenarioRegistryError(f"scenario registry validation failed: {message}")

    return registry


def load_scenario_registry(path: str | Path = DEFAULT_REGISTRY_PATH) -> dict[str, Any]:
    registry = _load_validated_registry(
        _normalize_path(path),
        _normalize_path(DEFAULT_ANCHOR_RULES_PATH),
        _normalize_path(DEFAULT_RISK_RULES_PATH),
        _normalize_path(DEFAULT_EVAL_CASES_PATH),
    )
    return deepcopy(registry)


def _list_raw_scenarios(path: str | Path = DEFAULT_REGISTRY_PATH) -> list[dict[str, Any]]:
    registry = _load_validated_registry(
        _normalize_path(path),
        _normalize_path(DEFAULT_ANCHOR_RULES_PATH),
        _normalize_path(DEFAULT_RISK_RULES_PATH),
        _normalize_path(DEFAULT_EVAL_CASES_PATH),
    )
    scenarios = registry.get("scenarios") or []
    return [scenario for scenario in scenarios if isinstance(scenario, dict)]


def get_scenario_by_id(scenario_id: str) -> dict[str, Any] | None:
    for scenario in _list_raw_scenarios():
        if scenario.get("scenario_id") == scenario_id:
            return deepcopy(scenario)
    return None


def list_scenarios(domain: str | None = None) -> list[dict[str, Any]]:
    scenarios = _list_raw_scenarios()
    if domain is not None:
        scenarios = [scenario for scenario in scenarios if scenario.get("domain") == domain]
    return deepcopy(scenarios)


def get_scenarios_by_anchor_rule(rule_id: str) -> list[dict[str, Any]]:
    scenarios = [
        scenario
        for scenario in _list_raw_scenarios()
        if rule_id in (scenario.get("linked_anchor_rule_ids") or [])
    ]
    return deepcopy(scenarios)


def get_scenarios_by_risk_rule(rule_id: str) -> list[dict[str, Any]]:
    scenarios = [
        scenario
        for scenario in _list_raw_scenarios()
        if rule_id in (scenario.get("linked_risk_rule_ids") or [])
    ]
    return deepcopy(scenarios)


def get_core_articles_for_scenario(scenario_id: str) -> list[dict[str, Any]]:
    scenario = get_scenario_by_id(scenario_id)
    if scenario is None:
        return []
    return deepcopy(scenario.get("core_articles") or [])


def get_required_actions_for_scenario(scenario_id: str) -> list[str]:
    scenario = get_scenario_by_id(scenario_id)
    if scenario is None:
        return []
    return deepcopy(scenario.get("required_actions") or [])


def clear_scenario_registry_cache() -> None:
    _load_validated_registry.cache_clear()
