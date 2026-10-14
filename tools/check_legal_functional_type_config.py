"""Validate legal functional typing configuration.

This gate protects the offline functional typing foundation. It validates the
taxonomy and rule schema only; it does not classify documents or affect RAG.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools._shared.layout import legacy_report_path


DEFAULT_CONFIG_PATH = Path("config/legal_functional_types.json")
DEFAULT_REPORT_PATH = legacy_report_path("legal_functional_type_config_report.json")
ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
ALLOWED_CONFIDENCE_LEVELS = {"rule_high", "rule_medium", "rule_low"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def validate_functional_type_config(config: dict[str, Any]) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []

    functional_types = _as_list(config.get("functional_types"))
    rules = _as_list(config.get("rules"))
    operative_support_types = _as_list(config.get("operative_support_types"))

    if not isinstance(config.get("version"), str) or not config.get("version", "").strip():
        errors.append("version must be a non-empty string")
    if not isinstance(config.get("purpose"), str) or not config.get("purpose", "").strip():
        errors.append("purpose must be a non-empty string")
    if not functional_types:
        errors.append("functional_types must be a non-empty list")
    if not rules:
        errors.append("rules must be a non-empty list")
    if not operative_support_types:
        errors.append("operative_support_types must be a non-empty list")

    type_ids: list[str] = []
    for index, item in enumerate(functional_types):
        label = f"functional_types[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object")
            continue
        type_id = item.get("id")
        if not isinstance(type_id, str) or not type_id.strip():
            errors.append(f"{label}.id must be a non-empty string")
            continue
        if not ID_PATTERN.match(type_id):
            errors.append(f"{label}.id must use lowercase snake_case: {type_id}")
        type_ids.append(type_id)
        for field in ("label", "description"):
            if not isinstance(item.get(field), str) or not item.get(field, "").strip():
                errors.append(f"{label}.{field} must be a non-empty string")

    duplicate_type_ids = sorted(type_id for type_id, count in Counter(type_ids).items() if count > 1)
    for type_id in duplicate_type_ids:
        errors.append(f"duplicate functional type id: {type_id}")
    type_id_set = set(type_ids)

    required_type_ids = {"definition", "operative_rule", "procedural", "liability", "rights_remedy", "unclassified"}
    for type_id in sorted(required_type_ids - type_id_set):
        errors.append(f"missing required functional type: {type_id}")

    for support_type in operative_support_types:
        if not isinstance(support_type, str) or not support_type.strip():
            errors.append("operative_support_types must contain non-empty strings")
            continue
        if support_type not in type_id_set:
            errors.append(f"operative support type is not declared: {support_type}")
        if support_type in {"definition", "principle", "scope", "unclassified", "unrelated_or_contextual"}:
            warnings.append(f"operative support type may be too broad: {support_type}")

    priorities: list[int] = []
    rule_type_counts: Counter[str] = Counter()
    compiled_regex_count = 0
    contains_term_count = 0
    for index, rule in enumerate(rules):
        label = f"rules[{index}]"
        if not isinstance(rule, dict):
            errors.append(f"{label} must be an object")
            continue

        functional_type = rule.get("functional_type")
        if not isinstance(functional_type, str) or not functional_type.strip():
            errors.append(f"{label}.functional_type must be a non-empty string")
        elif functional_type not in type_id_set:
            errors.append(f"{label}.functional_type is not declared: {functional_type}")
        else:
            rule_type_counts[functional_type] += 1

        priority = rule.get("priority")
        if not isinstance(priority, int):
            errors.append(f"{label}.priority must be an integer")
        elif priority < 0 or priority > 1000:
            errors.append(f"{label}.priority must be between 0 and 1000")
        else:
            priorities.append(priority)

        confidence = rule.get("confidence")
        if confidence not in ALLOWED_CONFIDENCE_LEVELS:
            errors.append(f"{label}.confidence must be one of {sorted(ALLOWED_CONFIDENCE_LEVELS)}")

        contains = _as_list(rule.get("contains"))
        regexes = _as_list(rule.get("regex"))
        if not contains and not regexes:
            errors.append(f"{label} must include contains or regex cues")

        seen_terms: set[str] = set()
        for term_index, term in enumerate(contains):
            term_label = f"{label}.contains[{term_index}]"
            if not isinstance(term, str) or not term.strip():
                errors.append(f"{term_label} must be a non-empty string")
                continue
            contains_term_count += 1
            if term in seen_terms:
                warnings.append(f"{term_label} duplicates another term in the same rule: {term}")
            seen_terms.add(term)

        for regex_index, pattern in enumerate(regexes):
            pattern_label = f"{label}.regex[{regex_index}]"
            if not isinstance(pattern, str) or not pattern.strip():
                errors.append(f"{pattern_label} must be a non-empty string")
                continue
            try:
                re.compile(pattern)
                compiled_regex_count += 1
            except re.error as exc:
                errors.append(f"{pattern_label} is not a valid regex: {exc}")

    for type_id in sorted(type_id_set - {"technical_standard", "unclassified", "unrelated_or_contextual"}):
        if rule_type_counts[type_id] == 0:
            warnings.append(f"functional type has no rule coverage: {type_id}")

    summary = {
        "functional_type_count": len(type_id_set),
        "rule_count": len(rules),
        "operative_support_type_count": len(set(operative_support_types)),
        "contains_term_count": contains_term_count,
        "regex_count": compiled_regex_count,
        "priority_min": min(priorities) if priorities else None,
        "priority_max": max(priorities) if priorities else None,
        "rule_type_counts": dict(sorted(rule_type_counts.items())),
    }
    return errors, warnings, summary


def build_report(config_path: Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    config = load_json(config_path)
    errors, warnings, summary = validate_functional_type_config(config)
    return {
        "version": config.get("version") or "0.4.7.2.1",
        "scope": "legal functional type config gate",
        "input": str(config_path),
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "summary": summary,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate legal functional typing config.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.config)
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    status = "passed" if report["passed"] else "failed"
    print(
        "Legal functional type config gate "
        f"{status}: {len(report['errors'])} errors, {len(report['warnings'])} warnings"
    )
    summary = report["summary"]
    print(
        "Config summary: "
        f"{summary['functional_type_count']} functional types, "
        f"{summary['rule_count']} rules, "
        f"{summary['contains_term_count']} contains cues, "
        f"{summary['regex_count']} regex cues"
    )
    if report["errors"]:
        for error in report["errors"]:
            print(f"ERROR: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
