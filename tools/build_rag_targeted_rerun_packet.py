"""Build a saved-report-only targeted rerun packet for RAG dependency hotspots.

This tool reads the v0.4.17.1 evidence-independence baseline and turns it into
small, runnable case groups. It does not run eval, call rag_query, contact
Qdrant or an LLM, or mutate runtime configuration.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "0.4.17.2"

DEFAULT_INPUT_PATH = Path("tests/rag_evidence_independence_baseline_v0.4.17.1_report.json")
DEFAULT_OUTPUT_PATH = Path("tests/rag_targeted_rerun_packet_v0.4.17.2_report.json")
DEFAULT_TARGETED_OUTPUT_PATH = Path("tests/targeted_rag_evidence_independence_v0.4.17.2_report.json")
DEFAULT_CASES_PATH = Path("tests/rag_eval_cases.json")

GUARDRAILS = {
    "saved_reports_only": True,
    "runs_eval": "disallowed",
    "rag_query_call": "disallowed",
    "qdrant_access": "disallowed",
    "qdrant_write": "disallowed",
    "llm_access": "disallowed",
    "runtime_mutation": "disallowed",
    "anchor_mutation": "disallowed",
    "prompt_mutation": "disallowed",
    "rerank_mutation": "disallowed",
    "risk_supplement_mutation": "disallowed",
    "term_preservation_rule_mutation": "disallowed",
    "taxonomy_mutation": "disallowed",
    "scenario_registry_mutation": "disallowed",
    "eval_case_mutation": "disallowed",
    "hidden_seed_mutation": "disallowed",
    "fixture_mutation": "disallowed",
}


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def row_id(row: dict[str, Any]) -> str:
    return str(row.get("id") or row.get("case_id") or "")


def row_map(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row_id(row): row for row in rows if row_id(row)}


def unique_case_ids(case_ids: list[Any], rows_by_id: dict[str, dict[str, Any]]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in case_ids:
        case_id = str(value or "")
        if not case_id or case_id in seen or case_id not in rows_by_id:
            continue
        seen.add(case_id)
        result.append(case_id)
    return result


def case_rank(row: dict[str, Any]) -> tuple[int, int, str]:
    return (
        int(row.get("passed") is True),
        int(row.get("independence_score") or 0),
        row_id(row),
    )


def build_case_entry(case_id: str, rows_by_id: dict[str, dict[str, Any]], group: str, reason: str) -> dict[str, Any]:
    row = rows_by_id[case_id]
    layers = as_dict(row.get("retrieval_layers"))
    return {
        "case_id": case_id,
        "group": group,
        "reason": reason,
        "category": row.get("category") or "uncategorized",
        "passed": bool(row.get("passed")),
        "dependency_bucket": row.get("dependency_bucket"),
        "independence_score": row.get("independence_score"),
        "next_action": row.get("next_action"),
        "contribution_labels": as_list(row.get("contribution_labels")),
        "retrieval_layers": {
            name: as_dict(layers.get(name))
            for name in ["dense", "sparse", "union", "anchor", "final"]
            if name in layers
        },
    }


def command_for(case_ids: list[str], output_path: Path, cases_path: Path, repeat: int) -> str:
    ids = " ".join(f"--case-id {case_id}" for case_id in case_ids)
    return (
        f".\\venv\\Scripts\\python.exe tools\\run_rag_eval.py "
        f"--cases {cases_path.as_posix()} --check-risk --compact-report --repeat {repeat} "
        f"{ids} --output {output_path.as_posix()}"
    )


def ranked_candidates(rows: list[dict[str, Any]], next_action: str) -> list[str]:
    candidates = [
        row
        for row in rows
        if row.get("next_action") == next_action and row_id(row)
    ]
    return [row_id(row) for row in sorted(candidates, key=case_rank)]


def pure_control_candidates(rows: list[dict[str, Any]]) -> list[str]:
    candidates = [
        row
        for row in rows
        if row.get("next_action") == "candidate_stable_baseline" and row_id(row)
    ]
    return [row_id(row) for row in sorted(candidates, key=lambda row: (-int(row.get("independence_score") or 0), row_id(row)))]


def failed_candidates(rows: list[dict[str, Any]]) -> list[str]:
    candidates = [row for row in rows if not row.get("passed") and row_id(row)]
    return [row_id(row) for row in sorted(candidates, key=lambda row: row_id(row))]


def add_group(
    groups: list[dict[str, Any]],
    rows_by_id: dict[str, dict[str, Any]],
    *,
    group_id: str,
    title: str,
    reason: str,
    case_ids: list[str],
    output_path: Path,
    cases_path: Path,
    repeat: int,
) -> None:
    entries = [build_case_entry(case_id, rows_by_id, group_id, reason) for case_id in case_ids]
    groups.append({
        "group_id": group_id,
        "title": title,
        "reason": reason,
        "case_count": len(entries),
        "case_ids": case_ids,
        "cases": entries,
        "suggested_command": command_for(case_ids, output_path, cases_path, repeat) if case_ids else "",
    })


def build_report(
    input_path: Path = DEFAULT_INPUT_PATH,
    *,
    output_eval_path: Path = DEFAULT_TARGETED_OUTPUT_PATH,
    cases_path: Path = DEFAULT_CASES_PATH,
    max_base_triage: int = 8,
    max_output_rule: int = 5,
    max_control: int = 3,
    repeat: int = 3,
) -> dict[str, Any]:
    source = load_json(input_path)
    rows = [row for row in as_list(source.get("case_rows")) if isinstance(row, dict)]
    rows_by_id = row_map(rows)

    base_ids = unique_case_ids(
        ranked_candidates(rows, "inspect_base_retrieval_query_lexical_coverage")[:max_base_triage],
        rows_by_id,
    )
    output_rule_ids = unique_case_ids(
        ranked_candidates(rows, "inspect_output_rule_dependency")[:max_output_rule],
        rows_by_id,
    )
    failed_ids = unique_case_ids(failed_candidates(rows), rows_by_id)
    control_ids = unique_case_ids(pure_control_candidates(rows)[:max_control], rows_by_id)

    groups: list[dict[str, Any]] = []
    add_group(
        groups,
        rows_by_id,
        group_id="base_retrieval_query_lexical_triage",
        title="Base retrieval lexical coverage rerun candidates",
        reason="Saved report shows union/sparse gaps while anchor or final layer still passes.",
        case_ids=base_ids,
        output_path=output_eval_path,
        cases_path=cases_path,
        repeat=repeat,
    )
    add_group(
        groups,
        rows_by_id,
        group_id="output_rule_dependency_review",
        title="Output rule dependency rerun candidates",
        reason="Saved report shows risk supplement dependency without base retrieval failure.",
        case_ids=output_rule_ids,
        output_path=output_eval_path,
        cases_path=cases_path,
        repeat=repeat,
    )
    add_group(
        groups,
        rows_by_id,
        group_id="failed_or_expected_level_review",
        title="Failed or expected-level review candidates",
        reason="Saved report keeps strict failures separate from runtime patch recommendations.",
        case_ids=failed_ids,
        output_path=output_eval_path,
        cases_path=cases_path,
        repeat=repeat,
    )
    add_group(
        groups,
        rows_by_id,
        group_id="pure_llm_control",
        title="Pure LLM / low-rule-dependency control candidates",
        reason="Control cases help compare whether rerun variance is specific to rule-heavy samples.",
        case_ids=control_ids,
        output_path=output_eval_path,
        cases_path=cases_path,
        repeat=repeat,
    )

    ordered_selected: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for case_id in as_list(group.get("case_ids")):
            if case_id not in seen:
                ordered_selected.append(case_id)
                seen.add(case_id)

    bucket_counts: Counter[str] = Counter()
    next_action_counts: Counter[str] = Counter()
    for case_id in ordered_selected:
        row = rows_by_id[case_id]
        bucket_counts[str(row.get("dependency_bucket"))] += 1
        next_action_counts[str(row.get("next_action"))] += 1

    combined_command = command_for(ordered_selected, output_eval_path, cases_path, repeat) if ordered_selected else ""
    status = "targeted_rerun_packet_ready" if ordered_selected else "no_targeted_rerun_candidates"

    return {
        "version": VERSION,
        "schema_kind": "rag_targeted_rerun_packet",
        "scope": "saved-report-only packet for bounded targeted rerun planning",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "evidence_independence_baseline": str(input_path),
            "targeted_eval_output": str(output_eval_path),
            "cases_path": str(cases_path),
        },
        "guardrails": GUARDRAILS,
        "selection_policy": {
            "max_base_triage": max_base_triage,
            "max_output_rule": max_output_rule,
            "max_control": max_control,
            "repeat": repeat,
            "case_id_hardcoding": "disallowed",
            "selection_source": "case_rows.next_action and saved dependency metadata",
        },
        "summary": {
            "status": status,
            "source_total_cases": len(rows),
            "selected_case_count": len(ordered_selected),
            "selected_case_ids": ordered_selected,
            "selected_dependency_bucket_counts": dict(sorted(bucket_counts.items())),
            "selected_next_action_counts": dict(sorted(next_action_counts.items())),
            "group_counts": {str(group["group_id"]): int(group["case_count"]) for group in groups},
            "runtime_patch_recommendation": "not_recommended_by_this_packet",
        },
        "suggested_commands": {
            "combined_targeted_repeat": combined_command,
            "note": "Commands are suggestions only; this tool itself does not run eval.",
        },
        "groups": groups,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build saved-report-only RAG targeted rerun packet.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--targeted-output", type=Path, default=DEFAULT_TARGETED_OUTPUT_PATH)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH)
    parser.add_argument("--max-base-triage", type=int, default=8)
    parser.add_argument("--max-output-rule", type=int, default=5)
    parser.add_argument("--max-control", type=int, default=3)
    parser.add_argument("--repeat", type=int, default=3)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(
        args.input,
        output_eval_path=args.targeted_output,
        cases_path=args.cases,
        max_base_triage=args.max_base_triage,
        max_output_rule=args.max_output_rule,
        max_control=args.max_control,
        repeat=args.repeat,
    )
    write_json(args.output, report)
    summary = report["summary"]
    print(
        "RAG targeted rerun packet completed: "
        f"{summary['status']}, selected_case_count={summary['selected_case_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
