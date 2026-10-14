"""Compare saved full RAG eval reports before and after alignment retention."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "0.4.14.33"
DEFAULT_BEFORE_PATH = Path("tests/post_rebuild_rag_eval_report.json")
DEFAULT_AFTER_PATH = Path("tests/post_rebuild_rag_eval_after_alignment_retention_report.json")
DEFAULT_EVAL_CASES_PATH = Path("tests/rag_eval_cases.json")
DEFAULT_OUTPUT_PATH = Path("tests/post_rebuild_alignment_retention_delta_report.json")
DEFAULT_SUMMARY_PATH = Path("docs/post_rebuild_alignment_retention_delta_v0.4.14.33.md")


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def reports_by_id(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item["id"]: item
        for item in report.get("reports") or []
        if isinstance(item, dict) and item.get("id")
    }


def eval_cases_by_id(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item["id"]: item
        for item in payload.get("cases") or []
        if isinstance(item, dict) and item.get("id")
    }


def evidence_identity(evidence: dict[str, Any]) -> dict[str, Any]:
    source = evidence.get("source") or evidence.get("law_name") or ""
    return {
        "rank": evidence.get("rank"),
        "evidence_key": canonical_key_string(evidence),
        "source": source,
        "law_name": evidence.get("law_name") or source,
        "article_no": evidence.get("article_no"),
        "section_no": evidence.get("section_no") or "",
        "citation": evidence.get("citation") or "",
        "rerank_score": evidence.get("rerank_score"),
    }


def identity_key(evidence: dict[str, Any]) -> tuple[Any, ...]:
    return (
        evidence.get("source") or evidence.get("law_name") or "",
        evidence.get("article_no"),
        evidence.get("section_no") or "",
    )


def canonical_key_string(evidence: dict[str, Any]) -> str:
    source, article_no, section_no = identity_key(evidence)
    article = "" if article_no is None else str(article_no)
    return f"{source}::{article}::{section_no or ''}"


def evidence_rows(case_report: dict[str, Any]) -> list[dict[str, Any]]:
    return [evidence_identity(item) for item in case_report.get("evidence") or []]


def expected_evidence_rows(eval_case: dict[str, Any] | None) -> list[dict[str, Any]]:
    rows = []
    for item in (eval_case or {}).get("expected_evidence") or []:
        if not isinstance(item, dict):
            continue
        rows.append({
            "source": item.get("source") or "",
            "article_no": item.get("article_no"),
            "section_no": item.get("section_no") or "",
        })
    return rows


def evidence_matches_expected(evidence: dict[str, Any], expected: dict[str, Any]) -> bool:
    if expected.get("source") and evidence.get("source") != expected.get("source"):
        return False
    if expected.get("article_no") is not None and evidence.get("article_no") != expected.get("article_no"):
        return False
    if expected.get("section_no") and evidence.get("section_no") != expected.get("section_no"):
        return False
    return True


def expected_matches(evidence: list[dict[str, Any]], expected_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        item
        for item in evidence
        if any(evidence_matches_expected(item, expected) for expected in expected_rows)
    ]


def failed_checks(case_report: dict[str, Any]) -> list[dict[str, Any]]:
    failures = []
    for check in case_report.get("checks") or []:
        if isinstance(check, dict) and not check.get("passed"):
            failures.append({
                "name": check.get("name"),
                "message": check.get("message"),
            })
    return failures


def pass_status_delta(before_case: dict[str, Any], after_case: dict[str, Any]) -> str:
    before_passed = bool(before_case.get("passed"))
    after_passed = bool(after_case.get("passed"))
    if before_passed and after_passed:
        return "unchanged_passed"
    if not before_passed and after_passed:
        return "improved"
    if before_passed and not after_passed:
        return "regressed"
    return "unchanged_failed"


def build_evidence_delta(
    before_case: dict[str, Any],
    after_case: dict[str, Any],
    expected_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    before_rows = evidence_rows(before_case)
    after_rows = evidence_rows(after_case)
    before_keys = [identity_key(item) for item in before_rows]
    after_keys = [identity_key(item) for item in after_rows]
    before_key_set = set(before_keys)
    after_key_set = set(after_keys)
    before_by_key = {identity_key(item): item for item in before_rows}
    after_by_key = {identity_key(item): item for item in after_rows}
    before_rank = {key: index + 1 for index, key in enumerate(before_keys)}
    after_rank = {key: index + 1 for index, key in enumerate(after_keys)}

    retained = [row for row in after_rows if identity_key(row) in before_key_set]
    added = [row for row in after_rows if identity_key(row) not in before_key_set]
    removed = [row for row in before_rows if identity_key(row) not in after_key_set]

    rank_changes = []
    citation_changes = []
    score_changes = []
    for key in sorted(before_key_set & after_key_set, key=str):
        if before_rank[key] != after_rank[key]:
            rank_changes.append({
                "evidence_key": canonical_key_string(before_by_key[key]),
                "before_rank": before_rank[key],
                "after_rank": after_rank[key],
            })
        before_citation = before_by_key[key].get("citation") or ""
        after_citation = after_by_key[key].get("citation") or ""
        if before_citation != after_citation:
            citation_changes.append({
                "evidence_key": canonical_key_string(before_by_key[key]),
                "before_citation": before_citation,
                "after_citation": after_citation,
            })
        before_score = before_by_key[key].get("rerank_score")
        after_score = after_by_key[key].get("rerank_score")
        if before_score != after_score:
            score_changes.append({
                "evidence_key": canonical_key_string(before_by_key[key]),
                "before_rerank_score": before_score,
                "after_rerank_score": after_score,
            })

    identity_changed = before_keys != after_keys
    citation_only = bool(citation_changes) and not identity_changed
    score_only = bool(score_changes) and not identity_changed and not citation_changes and not rank_changes
    if identity_changed and citation_changes:
        delta_kind = "mixed"
    elif identity_changed:
        delta_kind = "replacement"
    elif citation_only:
        delta_kind = "citation_only"
    elif score_only:
        delta_kind = "score_only"
    else:
        delta_kind = "none"

    before_expected = expected_matches(before_rows, expected_rows)
    after_expected = expected_matches(after_rows, expected_rows)
    return {
        "final_evidence_before": before_rows,
        "final_evidence_after": after_rows,
        "retained_evidence": retained,
        "added_evidence": added,
        "removed_evidence": removed,
        "citation_changes": citation_changes,
        "rank_changes": rank_changes,
        "score_changes": score_changes,
        "evidence_delta_kind": delta_kind,
        "identity_changed": identity_changed,
        "expected_evidence_delta": {
            "added_expected": expected_matches(added, expected_rows),
            "removed_expected": expected_matches(removed, expected_rows),
            "before_final_satisfied": bool(before_expected) if expected_rows else None,
            "after_final_satisfied": bool(after_expected) if expected_rows else None,
        },
    }


def build_risk_flags(
    pass_delta: str,
    evidence_delta: dict[str, Any],
    after_failed: list[dict[str, Any]],
) -> list[dict[str, str]]:
    flags = []
    if pass_delta == "regressed":
        flags.append({
            "flag": "regressed_with_evidence_change" if evidence_delta["identity_changed"] else "regressed",
            "severity": "block",
            "reason": "修复后 case 从通过变为失败。",
        })
    if evidence_delta["expected_evidence_delta"]["removed_expected"]:
        flags.append({
            "flag": "removed_expected_evidence",
            "severity": "block",
            "reason": "修复后 final evidence 移除了 eval case 期望证据。",
        })
    if pass_delta == "unchanged_passed" and evidence_delta["identity_changed"]:
        flags.append({
            "flag": "unexplained_replacement_in_unchanged_pass",
            "severity": "warn",
            "reason": "case 修复前后均通过，但 final evidence 法条发生替换。",
        })
    if after_failed:
        names = [item.get("name") for item in after_failed]
        flags.append({
            "flag": "after_failed_checks_present",
            "severity": "warn",
            "reason": f"修复后仍存在失败检查：{names}",
        })
    if pass_delta == "improved" and evidence_delta["expected_evidence_delta"]["added_expected"]:
        flags.append({
            "flag": "added_expected_evidence",
            "severity": "info",
            "reason": "修复后新增了 eval case 期望证据，属于可解释改善。",
        })
    elif pass_delta == "improved" and evidence_delta["identity_changed"]:
        flags.append({
            "flag": "improved_with_non_expected_replacement",
            "severity": "warn",
            "reason": "case 从失败变为通过，但新增证据不是显式 expected evidence。",
        })
    return flags


def classify_case_delta(pass_delta: str, evidence_delta: dict[str, Any], risk_flags: list[dict[str, str]]) -> str:
    if any(flag["severity"] == "block" for flag in risk_flags):
        return "regression_needs_triage"
    if pass_delta == "improved" and evidence_delta["expected_evidence_delta"]["added_expected"]:
        return "explained_improvement"
    if pass_delta == "improved":
        return "improvement_needs_review"
    if evidence_delta["evidence_delta_kind"] == "citation_only":
        return "harmless_citation_normalization"
    if pass_delta == "unchanged_passed" and evidence_delta["identity_changed"]:
        return "unchanged_pass_with_replacement_needs_review"
    if evidence_delta["evidence_delta_kind"] == "score_only":
        return "score_only_change"
    return "unchanged"


def recommended_triage(classification: str, risk_flags: list[dict[str, str]]) -> str:
    if any(flag["severity"] == "block" for flag in risk_flags):
        return "block_runtime_progress_and_triage_delta"
    recommendations = {
        "explained_improvement": "accept_after_human_readable_spot_check",
        "improvement_needs_review": "inspect_improved_case_non_expected_replacement",
        "harmless_citation_normalization": "no_action_unless_citation_format_policy_changes",
        "unchanged_pass_with_replacement_needs_review": "sample_review_replacement_before_series_closeout",
        "score_only_change": "ignore_for_evidence_identity_delta",
        "unchanged": "no_action",
    }
    return recommendations.get(classification, "manual_triage_required")


def build_case_set_change_row(case_id: str, before_case: dict[str, Any] | None, after_case: dict[str, Any] | None) -> dict[str, Any]:
    case = after_case or before_case or {}
    risk_flags = [{
        "flag": "case_set_changed",
        "severity": "block",
        "reason": "before/after reports do not contain the same case ids.",
    }]
    return {
        "case_id": case_id,
        "category": case.get("category", ""),
        "question": case.get("question", ""),
        "pass_status": {
            "before_passed": before_case.get("passed") if before_case else None,
            "after_passed": after_case.get("passed") if after_case else None,
            "delta": "case_set_changed",
        },
        "failed_checks": {
            "before": failed_checks(before_case or {}),
            "after": failed_checks(after_case or {}),
        },
        "expected_evidence": [],
        "evidence_changed": True,
        "evidence_delta_kind": "replacement",
        "evidence_delta": {
            "final_evidence_before": evidence_rows(before_case or {}),
            "final_evidence_after": evidence_rows(after_case or {}),
            "retained_evidence": [],
            "added_evidence": evidence_rows(after_case or {}),
            "removed_evidence": evidence_rows(before_case or {}),
            "citation_changes": [],
            "rank_changes": [],
            "score_changes": [],
            "evidence_delta_kind": "replacement",
            "identity_changed": True,
            "expected_evidence_delta": {
                "added_expected": [],
                "removed_expected": [],
                "before_final_satisfied": None,
                "after_final_satisfied": None,
            },
        },
        "risk_flags": risk_flags,
        "classification": "regression_needs_triage",
        "recommended_triage": "block_runtime_progress_and_triage_delta",
    }


def build_delta_report(
    before_path: Path = DEFAULT_BEFORE_PATH,
    after_path: Path = DEFAULT_AFTER_PATH,
    eval_cases_path: Path = DEFAULT_EVAL_CASES_PATH,
) -> dict[str, Any]:
    before_report = load_json(before_path)
    after_report = load_json(after_path)
    eval_cases = eval_cases_by_id(load_json(eval_cases_path))
    before_cases = reports_by_id(before_report)
    after_cases = reports_by_id(after_report)
    all_case_ids = sorted(set(before_cases) | set(after_cases))

    rows = []
    classifications: Counter[str] = Counter()
    pass_statuses: Counter[str] = Counter()
    delta_kinds: Counter[str] = Counter()
    high_risk_rows = []
    cases_with_evidence_delta = 0
    cases_with_replacement_delta = 0
    cases_with_citation_only_delta = 0
    added_expected_count = 0
    removed_expected_count = 0
    risky_unexplained_count = 0

    for case_id in all_case_ids:
        before_case = before_cases.get(case_id)
        after_case = after_cases.get(case_id)
        if before_case is None or after_case is None:
            row = build_case_set_change_row(case_id, before_case, after_case)
        else:
            expected_rows = expected_evidence_rows(eval_cases.get(case_id))
            evidence_delta = build_evidence_delta(before_case, after_case, expected_rows)
            pass_delta = pass_status_delta(before_case, after_case)
            before_failed = failed_checks(before_case)
            after_failed = failed_checks(after_case)
            risk_flags = build_risk_flags(pass_delta, evidence_delta, after_failed)
            classification = classify_case_delta(pass_delta, evidence_delta, risk_flags)
            row = {
                "case_id": case_id,
                "category": after_case.get("category") or before_case.get("category") or "",
                "question": after_case.get("question") or before_case.get("question") or "",
                "pass_status": {
                    "before_passed": bool(before_case.get("passed")),
                    "after_passed": bool(after_case.get("passed")),
                    "delta": pass_delta,
                },
                "failed_checks": {
                    "before": before_failed,
                    "after": after_failed,
                },
                "expected_evidence": expected_rows,
                "evidence_changed": bool(evidence_delta["identity_changed"] or evidence_delta["citation_changes"]),
                "evidence_delta_kind": evidence_delta["evidence_delta_kind"],
                "evidence_delta": evidence_delta,
                "risk_flags": risk_flags,
                "classification": classification,
                "recommended_triage": recommended_triage(classification, risk_flags),
            }

        rows.append(row)
        classifications[row["classification"]] += 1
        pass_statuses[row["pass_status"]["delta"]] += 1
        delta_kinds[row["evidence_delta_kind"]] += 1
        if row["evidence_changed"]:
            cases_with_evidence_delta += 1
        if row["evidence_delta_kind"] in {"replacement", "mixed"}:
            cases_with_replacement_delta += 1
        if row["evidence_delta_kind"] == "citation_only":
            cases_with_citation_only_delta += 1
        expected_delta = row["evidence_delta"]["expected_evidence_delta"]
        added_expected_count += len(expected_delta["added_expected"])
        removed_expected_count += len(expected_delta["removed_expected"])
        if any(flag["flag"] == "unexplained_replacement_in_unchanged_pass" for flag in row["risk_flags"]):
            risky_unexplained_count += 1
        if row["risk_flags"]:
            high_risk_rows.append({
                "case_id": row["case_id"],
                "category": row["category"],
                "classification": row["classification"],
                "pass_status_delta": row["pass_status"]["delta"],
                "risk_flags": row["risk_flags"],
                "recommended_triage": row["recommended_triage"],
                "added_evidence": row["evidence_delta"]["added_evidence"],
                "removed_evidence": row["evidence_delta"]["removed_evidence"],
            })

    blockers = []
    if pass_statuses.get("regressed", 0):
        blockers.append("post_fix_eval_regression_detected")
    if removed_expected_count:
        blockers.append("expected_evidence_removed")
    if set(before_cases) != set(after_cases):
        blockers.append("case_set_changed")
    if after_report.get("passed") != after_report.get("total"):
        blockers.append("after_report_not_full_pass")

    return {
        "version": VERSION,
        "schema_kind": "post_rebuild_rag_eval_evidence_delta_report",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "before_report": str(before_path),
            "after_report": str(after_path),
            "eval_cases": str(eval_cases_path),
            "saved_reports_only": True,
        },
        "comparison_summary": {
            "before_total": before_report.get("total"),
            "before_passed": before_report.get("passed"),
            "before_failed": before_report.get("failed"),
            "after_total": after_report.get("total"),
            "after_passed": after_report.get("passed"),
            "after_failed": after_report.get("failed"),
            "missing_from_after": sorted(set(before_cases) - set(after_cases)),
            "new_in_after": sorted(set(after_cases) - set(before_cases)),
            "pass_status_summary": dict(pass_statuses),
        },
        "evidence_delta_summary": {
            "cases_with_evidence_delta": cases_with_evidence_delta,
            "cases_with_replacement_delta": cases_with_replacement_delta,
            "cases_with_citation_only_delta": cases_with_citation_only_delta,
            "added_expected_evidence_count": added_expected_count,
            "removed_expected_evidence_count": removed_expected_count,
            "risky_unexplained_replacement_count": risky_unexplained_count,
            "evidence_delta_kind_summary": dict(delta_kinds),
        },
        "cases": rows,
        "changed_cases": [
            row
            for row in rows
            if row["evidence_changed"] or row["pass_status"]["delta"] != "unchanged_passed"
        ],
        "high_risk_manual_review": high_risk_rows,
        "summary": {
            "status": "passed" if not blockers else "needs_triage",
            "blockers": blockers,
            "case_count": len(all_case_ids),
            "manual_review_case_count": len(high_risk_rows),
            "classification_summary": dict(classifications),
            "runtime_changes": "not_performed",
            "qdrant_access": "not_called_by_delta_builder",
            "llm_access": "not_called_by_delta_builder",
            "recommended_next_step": (
                "tighten_alignment_retention_before_more_runtime_work"
                if blockers
                else "review_changed_evidence_then_close_post_rebuild_stabilization"
            ),
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    comparison = report["comparison_summary"]
    evidence = report["evidence_delta_summary"]
    summary = report["summary"]
    lines = [
        "# v0.4.14.33 Post-Rebuild Alignment Retention Delta",
        "",
        "## 结论",
        "",
        f"- 状态：`{summary['status']}`",
        f"- 修复前 full RAG eval：`{comparison['before_passed']}/{comparison['before_total']}`",
        f"- 修复后 full RAG eval：`{comparison['after_passed']}/{comparison['after_total']}`",
        f"- evidence changed cases：`{evidence['cases_with_evidence_delta']}`",
        f"- replacement delta cases：`{evidence['cases_with_replacement_delta']}`",
        f"- citation-only delta cases：`{evidence['cases_with_citation_only_delta']}`",
        f"- added expected evidence：`{evidence['added_expected_evidence_count']}`",
        f"- removed expected evidence：`{evidence['removed_expected_evidence_count']}`",
        f"- risky unexplained replacement：`{evidence['risky_unexplained_replacement_count']}`",
        f"- classification summary：`{summary['classification_summary']}`",
        "",
        "## 需要关注的变化",
        "",
    ]
    if not report["high_risk_manual_review"]:
        lines.append("- 无 high-risk manual review item。")
    for item in report["high_risk_manual_review"]:
        lines.extend([
            f"- `{item['case_id']}`",
            f"  - 分类：`{item['classification']}`",
            f"  - 状态变化：`{item['pass_status_delta']}`",
            f"  - 风险标记：`{item['risk_flags']}`",
            f"  - 建议：`{item['recommended_triage']}`",
            f"  - 新增证据：`{item['added_evidence']}`",
            f"  - 移除证据：`{item['removed_evidence']}`",
        ])
    lines.extend([
        "",
        "## 边界",
        "",
        "- 本工具只读取已保存的 full RAG eval JSON 报告和 eval case metadata。",
        "- 不调用 RAG、Qdrant、LLM，不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。",
        "- 本报告用于 post-fix stabilization；它不是新的运行时策略，也不是人工最终结论。",
        "",
        "## 下一步",
        "",
        f"- `{summary['recommended_next_step']}`",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare post-rebuild RAG evidence before and after retention.")
    parser.add_argument("--before", type=Path, default=DEFAULT_BEFORE_PATH)
    parser.add_argument("--after", type=Path, default=DEFAULT_AFTER_PATH)
    parser.add_argument("--eval-cases", type=Path, default=DEFAULT_EVAL_CASES_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY_PATH)
    args = parser.parse_args()

    report = build_delta_report(
        before_path=args.before,
        after_path=args.after,
        eval_cases_path=args.eval_cases,
    )
    write_json(args.output, report)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(render_markdown(report), encoding="utf-8")
    print(
        "Post-rebuild alignment retention delta: "
        f"{report['summary']['status']}, "
        f"changed={report['evidence_delta_summary']['cases_with_evidence_delta']}, "
        f"improved={report['comparison_summary']['pass_status_summary'].get('improved', 0)}, "
        f"regressed={report['comparison_summary']['pass_status_summary'].get('regressed', 0)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
