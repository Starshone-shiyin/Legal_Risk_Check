import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


DEFAULT_ANCHOR_RULES = Path("config/rag_anchor_rules.json")
DEFAULT_RISK_RULES = Path("config/risk_payload_supplement_rules.json")
DEFAULT_STABILITY_REPORT = Path("tests/rag_stability_report.json")
DEFAULT_JSON_OUTPUT = Path("tests/rule_debt_report.json")
DEFAULT_MD_OUTPUT = Path("docs/rule_debt_report_v0.4.5.16.md")


GENERIC_TERMS = {
    "公司",
    "企业",
    "用户",
    "个人",
    "信息",
    "数据",
    "处理",
    "使用",
    "行为",
    "风险",
    "违规",
    "违法",
    "合法",
    "合规",
    "是否",
    "是否合法",
    "是否合规",
    "该行为是否合法",
    "该行为是否合规",
    "责任",
    "义务",
    "管理",
    "措施",
    "要求",
    "规定",
    "相关",
}


TRIGGER_FIELDS = {
    "anchor": ["triggers", "context_any"],
    "risk": ["question_all", "question_any", "question_not_any"],
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_term(term: Any) -> str:
    if not isinstance(term, str):
        return ""
    return "".join(term.lower().split())


def is_useful_term(term: str) -> bool:
    return bool(term) and term not in GENERIC_TERMS and len(term) >= 2


def flatten_string_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        values: list[str] = []
        for item in value:
            values.extend(flatten_string_values(item))
        return values
    return []


def normalize_terms(values: list[str]) -> list[str]:
    seen = set()
    terms = []
    for value in values:
        term = normalize_term(value)
        if not is_useful_term(term) or term in seen:
            continue
        seen.add(term)
        terms.append(term)
    return terms


def extract_anchor_rules(anchor_config: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for domain, domain_config in anchor_config.get("domains", {}).items():
        for index, rule in enumerate(domain_config.get("scene_anchors", [])):
            trigger_values = []
            for field in TRIGGER_FIELDS["anchor"]:
                trigger_values.extend(flatten_string_values(rule.get(field, [])))
            records.append({
                "kind": "anchor",
                "index": index,
                "id": rule.get("id", f"{domain}:{index}"),
                "scenario_id": rule.get("scenario_id"),
                "domain": domain,
                "trigger_terms": normalize_terms(trigger_values),
                "risk_terms": normalize_terms(flatten_string_values(rule.get("risk_types", []))),
                "action_terms": normalize_terms(flatten_string_values(rule.get("actions", []))),
                "raw": rule,
            })
    return records


def extract_risk_rules(risk_config: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for index, rule in enumerate(risk_config.get("rules", [])):
        trigger_values = []
        for field in TRIGGER_FIELDS["risk"]:
            trigger_values.extend(flatten_string_values(rule.get(field, [])))
        trigger_values.extend(flatten_string_values(rule.get("question_any_groups", [])))
        risk_terms = flatten_string_values(rule.get("risk_types", []))
        risk_terms.extend(flatten_string_values(rule.get("exact_risk_types", [])))
        records.append({
            "kind": "risk",
            "index": index,
            "id": rule.get("id") or f"risk_rule_{index}",
            "scenario_id": rule.get("scenario_id"),
            "domain": "",
            "trigger_terms": normalize_terms(trigger_values),
            "risk_terms": normalize_terms(risk_terms),
            "action_terms": normalize_terms(flatten_string_values(rule.get("actions", []))),
            "raw": rule,
        })
    return records


def term_occurrences(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    occurrences: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        for term in record["trigger_terms"]:
            occurrences[term].append({
                "kind": record["kind"],
                "id": record["id"],
                "index": record["index"],
                "domain": record.get("domain", ""),
            })
    return dict(occurrences)


def duplicate_triggers(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items = []
    for term, occurrences in term_occurrences(records).items():
        rule_ids = sorted({f"{item['kind']}:{item['id']}" for item in occurrences})
        if len(rule_ids) < 2:
            continue
        kinds = sorted({item["kind"] for item in occurrences})
        items.append({
            "term": term,
            "count": len(rule_ids),
            "kinds": kinds,
            "rules": rule_ids,
        })
    return sorted(items, key=lambda item: (-item["count"], item["term"]))


def cross_config_trigger_overlaps(anchor_records: list[dict[str, Any]], risk_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    anchor_occurrences = term_occurrences(anchor_records)
    risk_occurrences = term_occurrences(risk_records)
    overlaps = []
    for term in sorted(set(anchor_occurrences) & set(risk_occurrences)):
        overlaps.append({
            "term": term,
            "anchor_rules": sorted({item["id"] for item in anchor_occurrences[term]}),
            "risk_rules": sorted({item["id"] for item in risk_occurrences[term]}),
        })
    return sorted(overlaps, key=lambda item: (-(len(item["anchor_rules"]) + len(item["risk_rules"])), item["term"]))


def suspicious_same_scene_pairs(anchor_records: list[dict[str, Any]], risk_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pairs = []
    for anchor in anchor_records:
        anchor_terms = set(anchor["trigger_terms"])
        anchor_effects = set(anchor["risk_terms"] + anchor["action_terms"])
        for risk in risk_records:
            shared_triggers = sorted(anchor_terms & set(risk["trigger_terms"]))
            shared_effects = sorted(anchor_effects & set(risk["risk_terms"] + risk["action_terms"]))
            if len(shared_triggers) < 2 and not (shared_triggers and shared_effects):
                continue
            pairs.append({
                "anchor_id": anchor["id"],
                "anchor_domain": anchor.get("domain", ""),
                "risk_rule": risk["id"],
                "risk_index": risk["index"],
                "shared_triggers": shared_triggers,
                "shared_effect_terms": shared_effects,
                "score": len(shared_triggers) * 2 + len(shared_effects),
            })
    return sorted(pairs, key=lambda item: (-item["score"], item["anchor_id"], item["risk_rule"]))


def missing_scenario_ids(anchor_records: list[dict[str, Any]], risk_records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    return {
        "anchor_rules_without_shared_scenario_id": [
            {"id": record["id"], "domain": record.get("domain", "")}
            for record in anchor_records
            if not record.get("scenario_id")
        ],
        "risk_rules_without_scenario_id": [
            {"id": record["id"], "index": record["index"], "trigger_terms": record["trigger_terms"]}
            for record in risk_records
            if not record.get("scenario_id")
        ],
    }


def high_dependency_cases(stability_report: dict[str, Any]) -> list[dict[str, Any]]:
    cases: dict[str, dict[str, Any]] = {}
    for run in stability_report.get("runs", []):
        run_no = run.get("run")
        for report in run.get("reports", []):
            labels = set(report.get("contribution_labels", []))
            if not {"ANCHOR_PASS", "RISK_SUPPLEMENT_PASS"}.issubset(labels):
                continue
            case_id = report.get("id", "")
            item = cases.setdefault(
                case_id,
                {
                    "id": case_id,
                    "question": report.get("question", ""),
                    "runs": [],
                    "labels": set(),
                },
            )
            item["runs"].append(run_no)
            item["labels"].update(labels)
    result = []
    for item in cases.values():
        result.append({
            "id": item["id"],
            "question": item["question"],
            "runs": item["runs"],
            "labels": sorted(item["labels"]),
        })
    return sorted(result, key=lambda item: (-len(item["runs"]), item["id"]))


def matched_rule_ids(question: str, records: list[dict[str, Any]]) -> list[str]:
    normalized_question = normalize_term(question)
    matches = []
    for record in records:
        matched_terms = [term for term in record["trigger_terms"] if term in normalized_question]
        if not matched_terms:
            continue
        matches.append({
            "id": record["id"],
            "kind": record["kind"],
            "domain": record.get("domain", ""),
            "matched_terms": matched_terms,
        })
    return sorted(matches, key=lambda item: (-len(item["matched_terms"]), item["id"]))


def map_high_dependency_cases(
    cases: list[dict[str, Any]],
    anchor_records: list[dict[str, Any]],
    risk_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    mapped = []
    for case in cases:
        mapped.append({
            **case,
            "matched_anchor_rules": matched_rule_ids(case["question"], anchor_records),
            "matched_risk_rules": matched_rule_ids(case["question"], risk_records),
        })
    return mapped


def build_report(
    anchor_config: dict[str, Any],
    risk_config: dict[str, Any],
    stability_report: dict[str, Any],
    report_version: str = "0.4.5.16",
) -> dict[str, Any]:
    anchor_records = extract_anchor_rules(anchor_config)
    risk_records = extract_risk_rules(risk_config)
    all_records = anchor_records + risk_records
    high_cases = high_dependency_cases(stability_report)
    duplicate_items = duplicate_triggers(all_records)
    overlap_items = cross_config_trigger_overlaps(anchor_records, risk_records)
    suspicious_pairs = suspicious_same_scene_pairs(anchor_records, risk_records)
    missing_ids = missing_scenario_ids(anchor_records, risk_records)
    mapped_cases = map_high_dependency_cases(high_cases, anchor_records, risk_records)
    return {
        "version": report_version,
        "scope": "audit only; no rule merge and no retriever.py changes",
        "summary": {
            "anchor_rule_count": len(anchor_records),
            "risk_rule_count": len(risk_records),
            "duplicate_trigger_count": len(duplicate_items),
            "cross_config_trigger_overlap_count": len(overlap_items),
            "suspicious_same_scene_pair_count": len(suspicious_pairs),
            "anchor_rules_without_shared_scenario_id": len(missing_ids["anchor_rules_without_shared_scenario_id"]),
            "risk_rules_without_scenario_id": len(missing_ids["risk_rules_without_scenario_id"]),
            "high_dependency_case_count": len(high_cases),
        },
        "duplicate_triggers": duplicate_items,
        "cross_config_trigger_overlaps": overlap_items,
        "suspicious_same_scene_pairs": suspicious_pairs,
        "missing_scenario_ids": missing_ids,
        "high_dependency_case_mappings": mapped_cases,
    }


def format_list(values: list[Any], limit: int | None = None) -> str:
    selected = values if limit is None else values[:limit]
    text = ", ".join(str(value) for value in selected)
    if limit is not None and len(values) > limit:
        text += f", ...(+{len(values) - limit})"
    return text


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        f"# v{report.get('version', '')} 规则债盘点报告",
        "",
        "范围：只扫描并输出报告，不合并规则，不修改 `src/rag/retriever.py`。",
        "",
        "## 摘要",
        "",
        f"- Anchor rules：`{summary['anchor_rule_count']}`",
        f"- Risk supplement rules：`{summary['risk_rule_count']}`",
        f"- 重复 trigger：`{summary['duplicate_trigger_count']}`",
        f"- 跨配置 trigger 重叠：`{summary['cross_config_trigger_overlap_count']}`",
        f"- 疑似同场景多处维护：`{summary['suspicious_same_scene_pair_count']}`",
        f"- Anchor 缺共享 scenario_id：`{summary['anchor_rules_without_shared_scenario_id']}`",
        f"- Risk 缺 scenario_id：`{summary['risk_rules_without_scenario_id']}`",
        f"- 高规则依赖 case：`{summary['high_dependency_case_count']}`",
        "",
        "## 重复 Trigger Top 30",
        "",
        "| trigger | count | kinds | rules |",
        "|---|---:|---|---|",
    ]
    for item in report["duplicate_triggers"][:30]:
        lines.append(
            f"| {item['term']} | {item['count']} | {format_list(item['kinds'])} | {format_list(item['rules'], 8)} |"
        )

    lines.extend([
        "",
        "## 跨配置 Trigger 重叠 Top 30",
        "",
        "| trigger | anchor rules | risk rules |",
        "|---|---|---|",
    ])
    for item in report["cross_config_trigger_overlaps"][:30]:
        lines.append(
            f"| {item['term']} | {format_list(item['anchor_rules'], 8)} | {format_list(item['risk_rules'], 8)} |"
        )

    lines.extend([
        "",
        "## 疑似同场景多处维护 Top 30",
        "",
        "| anchor | risk rule | shared triggers | shared effects | score |",
        "|---|---|---|---|---:|",
    ])
    for item in report["suspicious_same_scene_pairs"][:30]:
        lines.append(
            "| {anchor} | {risk} | {triggers} | {effects} | {score} |".format(
                anchor=item["anchor_id"],
                risk=item["risk_rule"],
                triggers=format_list(item["shared_triggers"]),
                effects=format_list(item["shared_effect_terms"]),
                score=item["score"],
            )
        )

    lines.extend([
        "",
        "## 缺失 Scenario ID",
        "",
        "说明：Anchor 规则已有 `id`，但缺少可与风险补全配置共享的 `scenario_id`；Risk 规则目前多数只能通过 index 或触发词定位。",
        "",
        f"- Anchor 缺共享 scenario_id：`{summary['anchor_rules_without_shared_scenario_id']}`",
        f"- Risk 缺 scenario_id：`{summary['risk_rules_without_scenario_id']}`",
        "",
        "## 高规则依赖 Case 映射",
        "",
        "口径：稳定性报告中同时带有 `ANCHOR_PASS` 与 `RISK_SUPPLEMENT_PASS` 的 case。",
        "",
        "| case | runs | matched anchors | matched risk rules | question |",
        "|---|---:|---|---|---|",
    ])
    for item in report["high_dependency_case_mappings"]:
        anchor_ids = [rule["id"] for rule in item["matched_anchor_rules"]]
        risk_ids = [rule["id"] for rule in item["matched_risk_rules"]]
        question = item["question"].replace("|", "\\|")
        lines.append(
            f"| {item['id']} | {format_list(item['runs'])} | {format_list(anchor_ids, 6)} | {format_list(risk_ids, 6)} | {question} |"
        )
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit rule debt between anchor and risk supplement configs.")
    parser.add_argument("--anchor-rules", type=Path, default=DEFAULT_ANCHOR_RULES)
    parser.add_argument("--risk-rules", type=Path, default=DEFAULT_RISK_RULES)
    parser.add_argument("--stability-report", type=Path, default=DEFAULT_STABILITY_REPORT)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--md-output", type=Path, default=DEFAULT_MD_OUTPUT)
    parser.add_argument("--report-version", type=str, default="0.4.5.16")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(
        load_json(args.anchor_rules),
        load_json(args.risk_rules),
        load_json(args.stability_report),
        report_version=args.report_version,
    )
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.md_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    args.md_output.write_text(render_markdown(report), encoding="utf-8")
    print(f"rule debt json written: {args.json_output}")
    print(f"rule debt markdown written: {args.md_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
