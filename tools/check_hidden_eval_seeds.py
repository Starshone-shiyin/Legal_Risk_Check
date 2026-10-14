"""Validate hidden eval seed annotations for offline evidence-alignment work."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


DEFAULT_SEEDS_PATH = Path("config/hidden_eval_seed_cases.json")
REQUIRED_CASE_IDS = {
    "seed_001_pipl_facial_attendance_complex",
    "seed_002_employee_monitoring_software_complex",
    "seed_003_algorithmic_price_discrimination_complex",
    "seed_004_online_education_ai_participation_scoring",
    "seed_005_supply_chain_cross_border_data_platform",
    "seed_006_fintech_cross_border_antifraud_scoring",
    "seed_007_cross_border_ecommerce_after_sales_scoring",
}
REF_PATTERN = re.compile(r"^[a-z0-9_]+::[a-z0-9_]+$")


def load_hidden_eval_seeds(path: Path = DEFAULT_SEEDS_PATH) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("hidden eval seed file must be a JSON object")
    return payload


def _require_string(value: Any, label: str, errors: list[str]) -> str | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label} must be a non-empty string")
        return None
    return value


def _require_string_list(value: Any, label: str, errors: list[str], allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list):
        errors.append(f"{label} must be a list")
        return []
    if not allow_empty and not value:
        errors.append(f"{label} must not be empty")
    result: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{label}[{index}] must be a non-empty string")
            continue
        if item in seen:
            errors.append(f"{label} contains duplicate value: {item}")
        seen.add(item)
        result.append(item)
    return result


def _validate_ref(ref: Any, label: str, errors: list[str]) -> str | None:
    value = _require_string(ref, label, errors)
    if value and not REF_PATTERN.match(value):
        errors.append(f"{label} must match <source>::<article_or_section>, got {value}")
    return value


def _validate_expected_statutes(
    case_id: str,
    statutes: Any,
    allowed_functional_types: set[str],
    known_issues: set[str],
    errors: list[str],
) -> None:
    if not isinstance(statutes, list):
        errors.append(f"{case_id}.expected_statutes must be a list")
        return
    if not statutes:
        errors.append(f"{case_id}.expected_statutes must not be empty")
        return

    refs: set[str] = set()
    operative_count = 0
    for index, statute in enumerate(statutes):
        label = f"{case_id}.expected_statutes[{index}]"
        if not isinstance(statute, dict):
            errors.append(f"{label} must be an object")
            continue

        ref = _validate_ref(statute.get("ref"), f"{label}.ref", errors)
        if ref:
            if ref in refs:
                errors.append(f"{case_id}.expected_statutes contains duplicate ref: {ref}")
            refs.add(ref)

        functional_type = _require_string(statute.get("functional_type"), f"{label}.functional_type", errors)
        if functional_type:
            if functional_type not in allowed_functional_types:
                errors.append(f"{label}.functional_type is not allowed: {functional_type}")
            if functional_type == "operative_rule":
                operative_count += 1

        supports = _require_string_list(statute.get("supports"), f"{label}.supports", errors)
        for issue in supports:
            if issue not in known_issues:
                errors.append(f"{label}.supports references unknown issue: {issue}")

    if operative_count == 0:
        errors.append(f"{case_id}.expected_statutes must include at least one operative_rule")


def _validate_known_bad_evidence(case_id: str, known_bad_evidence: Any, errors: list[str]) -> None:
    if not isinstance(known_bad_evidence, list):
        errors.append(f"{case_id}.known_bad_evidence must be a list")
        return
    refs: set[str] = set()
    for index, item in enumerate(known_bad_evidence):
        label = f"{case_id}.known_bad_evidence[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object")
            continue
        ref = _validate_ref(item.get("ref"), f"{label}.ref", errors)
        if ref:
            if ref in refs:
                errors.append(f"{case_id}.known_bad_evidence contains duplicate ref: {ref}")
            refs.add(ref)
        _require_string(item.get("reason"), f"{label}.reason", errors)


def validate_hidden_eval_seeds(payload: dict[str, Any], required_case_ids: set[str] | None = None) -> list[str]:
    errors: list[str] = []

    allowed_domains = set(_require_string_list(payload.get("legal_domains"), "legal_domains", errors))
    allowed_functional_types = set(
        _require_string_list(payload.get("functional_types"), "functional_types", errors)
    )
    _require_string_list(payload.get("issue_levels"), "issue_levels", errors)

    cases = payload.get("cases")
    if not isinstance(cases, list):
        errors.append("cases must be a list")
        return errors
    if not cases:
        errors.append("cases must not be empty")
        return errors

    seen_case_ids: set[str] = set()
    for index, case in enumerate(cases):
        label = f"cases[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{label} must be an object")
            continue

        case_id = _require_string(case.get("case_id"), f"{label}.case_id", errors) or label
        if case_id in seen_case_ids:
            errors.append(f"duplicate case_id: {case_id}")
        seen_case_ids.add(case_id)

        _require_string(case.get("scenario_label"), f"{case_id}.scenario_label", errors)
        expected_domains = _require_string_list(case.get("expected_domains"), f"{case_id}.expected_domains", errors)
        contaminating_domains = _require_string_list(
            case.get("contaminating_domains"),
            f"{case_id}.contaminating_domains",
            errors,
            allow_empty=True,
        )
        for domain in expected_domains + contaminating_domains:
            if domain not in allowed_domains:
                errors.append(f"{case_id} references unknown domain: {domain}")
        overlap = set(expected_domains).intersection(contaminating_domains)
        if overlap:
            errors.append(f"{case_id}.contaminating_domains overlaps expected_domains: {sorted(overlap)}")

        primary_issues = _require_string_list(case.get("primary_issues"), f"{case_id}.primary_issues", errors)
        secondary_issues = _require_string_list(
            case.get("secondary_issues"),
            f"{case_id}.secondary_issues",
            errors,
            allow_empty=True,
        )
        peripheral_issues = _require_string_list(
            case.get("peripheral_issues"),
            f"{case_id}.peripheral_issues",
            errors,
            allow_empty=True,
        )
        known_issues = set(primary_issues + secondary_issues + peripheral_issues)
        if len(known_issues) != len(primary_issues + secondary_issues + peripheral_issues):
            errors.append(f"{case_id} has duplicate issue ids across issue levels")

        _validate_expected_statutes(
            case_id,
            case.get("expected_statutes"),
            allowed_functional_types,
            known_issues,
            errors,
        )
        _validate_known_bad_evidence(case_id, case.get("known_bad_evidence"), errors)
        _require_string(case.get("notes"), f"{case_id}.notes", errors)

    required = REQUIRED_CASE_IDS if required_case_ids is None else required_case_ids
    missing = sorted(required.difference(seen_case_ids))
    if missing:
        errors.append(f"missing required hidden seed case ids: {missing}")
    extra = sorted(seen_case_ids.difference(required))
    if required_case_ids is not None and extra:
        errors.append(f"unexpected hidden seed case ids: {extra}")

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate config/hidden_eval_seed_cases.json.")
    parser.add_argument("--seeds", type=Path, default=DEFAULT_SEEDS_PATH)
    parser.add_argument("--allow-extra-cases", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        payload = load_hidden_eval_seeds(args.seeds)
    except Exception as exc:
        print(f"Hidden eval seed check failed: could not load seeds: {exc}")
        return 1

    required = None if args.allow_extra_cases else REQUIRED_CASE_IDS
    errors = validate_hidden_eval_seeds(payload, required_case_ids=required)
    if errors:
        print("Hidden eval seed check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    cases = payload.get("cases", [])
    print(f"Hidden eval seed check passed: {len(cases)} cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
