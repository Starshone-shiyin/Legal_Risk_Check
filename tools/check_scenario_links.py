import argparse
import json
import re
from pathlib import Path
from typing import Any


DEFAULT_ANCHOR_RULES = Path("config/rag_anchor_rules.json")
DEFAULT_RISK_RULES = Path("config/risk_payload_supplement_rules.json")
SCENARIO_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def anchor_scenario_map(anchor_config: dict[str, Any]) -> dict[str, list[str]]:
    scenarios: dict[str, list[str]] = {}
    for domain_config in anchor_config.get("domains", {}).values():
        for rule in domain_config.get("scene_anchors", []):
            scenario_id = rule.get("scenario_id")
            if scenario_id:
                scenarios.setdefault(scenario_id, []).append(rule.get("id", ""))
    return scenarios


def risk_scenario_map(risk_config: dict[str, Any]) -> dict[str, list[str]]:
    scenarios: dict[str, list[str]] = {}
    for index, rule in enumerate(risk_config.get("rules", [])):
        scenario_id = rule.get("scenario_id")
        if scenario_id:
            scenarios.setdefault(scenario_id, []).append(rule.get("id") or f"risk_rule_{index}")
    return scenarios


def validate_scenario_links(
    anchor_config: dict[str, Any],
    risk_config: dict[str, Any],
    required_scenario: str | None = None,
    required_anchor_rules: list[str] | None = None,
    required_risk_rules: list[str] | None = None,
    allowed_missing_risk_scenarios: list[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    allowed_missing_risk = set(allowed_missing_risk_scenarios or [])
    anchor_scenarios = anchor_scenario_map(anchor_config)
    risk_scenarios = risk_scenario_map(risk_config)
    all_scenarios = sorted(set(anchor_scenarios) | set(risk_scenarios))

    for scenario_id in all_scenarios:
        if not SCENARIO_ID_RE.match(scenario_id):
            errors.append(f"invalid scenario_id: {scenario_id}")
        if scenario_id not in anchor_scenarios:
            errors.append(f"{scenario_id} is missing anchor rules")
        if scenario_id not in risk_scenarios and scenario_id not in allowed_missing_risk:
            errors.append(f"{scenario_id} is missing risk supplement rules")

    if required_scenario:
        anchor_rules = anchor_scenarios.get(required_scenario, [])
        risk_rules = risk_scenarios.get(required_scenario, [])
        if required_scenario not in anchor_scenarios:
            errors.append(f"required scenario {required_scenario} is missing anchor rules")
        if required_scenario not in risk_scenarios:
            errors.append(f"required scenario {required_scenario} is missing risk supplement rules")
        for rule_id in required_anchor_rules or []:
            if rule_id not in anchor_rules:
                errors.append(f"required scenario {required_scenario} is missing anchor rule {rule_id}")
        for rule_id in required_risk_rules or []:
            if rule_id not in risk_rules:
                errors.append(f"required scenario {required_scenario} is missing risk rule {rule_id}")

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate scenario_id links across anchor and risk supplement configs.")
    parser.add_argument("--anchor-rules", type=Path, default=DEFAULT_ANCHOR_RULES)
    parser.add_argument("--risk-rules", type=Path, default=DEFAULT_RISK_RULES)
    parser.add_argument("--required-scenario", type=str, default=None)
    parser.add_argument("--required-anchor-rule", action="append", default=[])
    parser.add_argument("--required-risk-rule", action="append", default=[])
    parser.add_argument("--allow-missing-risk-scenario", action="append", default=[])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors = validate_scenario_links(
        load_json(args.anchor_rules),
        load_json(args.risk_rules),
        required_scenario=args.required_scenario,
        required_anchor_rules=args.required_anchor_rule,
        required_risk_rules=args.required_risk_rule,
        allowed_missing_risk_scenarios=args.allow_missing_risk_scenario,
    )
    if errors:
        print("Scenario link check failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Scenario link check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
