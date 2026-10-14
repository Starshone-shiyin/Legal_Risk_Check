import argparse
import json
import re
from pathlib import Path
from typing import Any


VALID_RISK_LEVELS = {"low", "medium", "high"}
SCENARIO_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
REQUIRED_NON_EMPTY_LIST_FIELDS = (
    "core_articles",
    "risk_types",
    "required_actions",
    "legal_terms",
)


def load_json(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def existing_domains(anchor_config: dict[str, Any]) -> set[str]:
    return set((anchor_config.get("domains") or {}).keys())


def anchor_rule_ids(anchor_config: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for domain in (anchor_config.get("domains") or {}).values():
        for rule in domain.get("scene_anchors") or []:
            rule_id = rule.get("id")
            if rule_id:
                ids.add(rule_id)
    return ids


def risk_rule_ids(risk_config: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for index, rule in enumerate(risk_config.get("rules") or []):
        ids.add(rule.get("id") or f"risk_rule_{index}")
    return ids


def eval_case_ids(eval_config: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for case in eval_config.get("cases") or []:
        case_id = case.get("id")
        if case_id:
            ids.add(case_id)
    return ids


def anchor_scenario_links(anchor_config: dict[str, Any]) -> dict[str, list[str]]:
    links: dict[str, list[str]] = {}
    for domain in (anchor_config.get("domains") or {}).values():
        for rule in domain.get("scene_anchors") or []:
            scenario_id = rule.get("scenario_id")
            rule_id = rule.get("id")
            if scenario_id and rule_id:
                links.setdefault(scenario_id, []).append(rule_id)
    return links


def risk_scenario_links(risk_config: dict[str, Any]) -> dict[str, list[str]]:
    links: dict[str, list[str]] = {}
    for index, rule in enumerate(risk_config.get("rules") or []):
        scenario_id = rule.get("scenario_id")
        if scenario_id:
            links.setdefault(scenario_id, []).append(rule.get("id") or f"risk_rule_{index}")
    return links


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def validate_scenario_registry(
    registry: dict[str, Any],
    anchor_config: dict[str, Any],
    risk_config: dict[str, Any],
    eval_config: dict[str, Any] | None = None,
) -> tuple[list[str], dict[str, list[str]]]:
    errors: list[str] = []
    scenarios = registry.get("scenarios")
    if not isinstance(scenarios, list):
        return ["registry.scenarios must be a list"], coverage_audit([], {}, {})

    domains = existing_domains(anchor_config)
    anchors = anchor_rule_ids(anchor_config)
    risks = risk_rule_ids(risk_config)
    evals = eval_case_ids(eval_config or {})
    anchor_links = anchor_scenario_links(anchor_config)
    risk_links = risk_scenario_links(risk_config)

    seen: set[str] = set()
    scenario_by_id: dict[str, dict[str, Any]] = {}
    for index, scenario in enumerate(scenarios):
        if not isinstance(scenario, dict):
            errors.append(f"scenarios[{index}] must be an object")
            continue

        scenario_id = scenario.get("scenario_id")
        label = scenario_id or f"scenarios[{index}]"
        if not isinstance(scenario_id, str) or not scenario_id.strip():
            errors.append(f"{label}: scenario_id must be a non-empty string")
            continue
        if not SCENARIO_ID_PATTERN.match(scenario_id):
            errors.append(f"{label}: scenario_id must use lowercase snake_case")
        if scenario_id in seen:
            errors.append(f"{label}: duplicate scenario_id")
        seen.add(scenario_id)
        scenario_by_id[scenario_id] = scenario

        if scenario.get("domain") not in domains:
            errors.append(f"{label}: domain {scenario.get('domain')!r} is not in existing anchor domains")
        if scenario.get("risk_level") not in VALID_RISK_LEVELS:
            errors.append(f"{label}: risk_level must be one of {sorted(VALID_RISK_LEVELS)}")

        for field in REQUIRED_NON_EMPTY_LIST_FIELDS:
            value = scenario.get(field)
            if not isinstance(value, list) or not value:
                errors.append(f"{label}: {field} must be a non-empty list")

        linked_anchor_ids = _as_list(scenario.get("linked_anchor_rule_ids"))
        linked_risk_ids = _as_list(scenario.get("linked_risk_rule_ids"))
        linked_eval_ids = _as_list(scenario.get("eval_case_ids"))

        for rule_id in linked_anchor_ids:
            if rule_id not in anchors:
                errors.append(f"{label}: linked anchor rule {rule_id!r} was not found")
        for rule_id in linked_risk_ids:
            if rule_id not in risks:
                errors.append(f"{label}: linked risk rule {rule_id!r} was not found")
        if evals:
            for case_id in linked_eval_ids:
                if case_id not in evals:
                    errors.append(f"{label}: linked eval case {case_id!r} was not found")

    for scenario_id, rule_ids in anchor_links.items():
        scenario = scenario_by_id.get(scenario_id)
        if scenario is None:
            errors.append(f"anchor scenario_id {scenario_id!r} is missing from registry")
            continue
        linked_anchor_ids = set(_as_list(scenario.get("linked_anchor_rule_ids")))
        for rule_id in rule_ids:
            if rule_id not in linked_anchor_ids:
                errors.append(f"{scenario_id}: anchor rule {rule_id!r} must be reverse-linked in registry")

    for scenario_id, rule_ids in risk_links.items():
        scenario = scenario_by_id.get(scenario_id)
        if scenario is None:
            errors.append(f"risk scenario_id {scenario_id!r} is missing from registry")
            continue
        linked_risk_ids = set(_as_list(scenario.get("linked_risk_rule_ids")))
        for rule_id in rule_ids:
            if rule_id not in linked_risk_ids:
                errors.append(f"{scenario_id}: risk rule {rule_id!r} must be reverse-linked in registry")

    return errors, coverage_audit(scenarios, anchor_links, risk_links)


def coverage_audit(
    scenarios: list[dict[str, Any]],
    anchor_links: dict[str, list[str]],
    risk_links: dict[str, list[str]],
) -> dict[str, list[str]]:
    scenario_ids = {
        scenario.get("scenario_id")
        for scenario in scenarios
        if isinstance(scenario, dict) and isinstance(scenario.get("scenario_id"), str)
    }
    rule_scenario_ids = set(anchor_links) | set(risk_links)

    return {
        "scenarios_missing_anchor_link": [
            scenario["scenario_id"]
            for scenario in scenarios
            if isinstance(scenario, dict)
            and scenario.get("scenario_id")
            and not scenario.get("linked_anchor_rule_ids")
        ],
        "scenarios_missing_risk_supplement_link": [
            scenario["scenario_id"]
            for scenario in scenarios
            if isinstance(scenario, dict)
            and scenario.get("scenario_id")
            and not scenario.get("linked_risk_rule_ids")
        ],
        "scenarios_missing_eval_case": [
            scenario["scenario_id"]
            for scenario in scenarios
            if isinstance(scenario, dict)
            and scenario.get("scenario_id")
            and not scenario.get("eval_case_ids")
        ],
        "rule_scenario_ids_missing_registry": sorted(rule_scenario_ids - scenario_ids),
    }


def format_audit(audit: dict[str, list[str]]) -> str:
    lines = ["Coverage audit:"]
    for key in (
        "scenarios_missing_anchor_link",
        "scenarios_missing_risk_supplement_link",
        "scenarios_missing_eval_case",
        "rule_scenario_ids_missing_registry",
    ):
        values = audit.get(key) or []
        lines.append(f"- {key}: {len(values)}")
        if values:
            lines.append(f"  {', '.join(values)}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate scenario_registry.json and print coverage audit.")
    parser.add_argument("--registry", type=Path, default=Path("config/scenario_registry.json"))
    parser.add_argument("--anchor-rules", type=Path, default=Path("config/rag_anchor_rules.json"))
    parser.add_argument("--risk-rules", type=Path, default=Path("config/risk_payload_supplement_rules.json"))
    parser.add_argument("--eval-cases", type=Path, default=Path("tests/rag_eval_cases.json"))
    parser.add_argument("--audit-output", type=Path)
    args = parser.parse_args()

    registry = load_json(args.registry)
    anchor_config = load_json(args.anchor_rules)
    risk_config = load_json(args.risk_rules)
    eval_config = load_json(args.eval_cases) if args.eval_cases.exists() else {}

    errors, audit = validate_scenario_registry(registry, anchor_config, risk_config, eval_config)
    if args.audit_output:
        args.audit_output.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if errors:
        print("Scenario registry check failed:")
        for error in errors:
            print(f"- {error}")
        print(format_audit(audit))
        return 1

    print("Scenario registry check passed.")
    print(format_audit(audit))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
