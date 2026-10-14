"""Build the v0.4.13.18 ingestion metadata rebuild planning series closeout."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools._shared.layout import legacy_report_path


VERSION = "0.4.13.18"

DEFAULT_AUTH_DESIGN_PATH = legacy_report_path("rebuild_authorization_design_report.json")
DEFAULT_AUTH_GATE_PATH = legacy_report_path("rebuild_authorization_design_gate_report.json")
DEFAULT_WORKSHEET_PATH = legacy_report_path("human_rebuild_authorization_worksheet_report.json")
DEFAULT_WORKSHEET_GATE_PATH = legacy_report_path("human_rebuild_authorization_worksheet_gate_report.json")
DEFAULT_RUNBOOK_PATH = legacy_report_path("rebuild_runbook_preflight_contract_report.json")
DEFAULT_OUTPUT_PATH = legacy_report_path("ingestion_metadata_rebuild_planning_series_closeout_report.json")
DEFAULT_MARKDOWN_OUTPUT_PATH = Path("docs/ingestion_metadata_rebuild_planning_series_closeout_v0.4.13.18.md")

GUARDRAILS = {
    "closeout_only": True,
    "saved_reports_only": True,
    "production_rebuild_executed": False,
    "live_preflight_run": False,
    "authorization_granted": False,
    "qdrant_access": "disallowed",
    "qdrant_write": "disallowed",
    "collection_rebuild": "disallowed",
    "rag_query_integration": "disallowed",
    "embedding_call": "disallowed",
    "llm_access": "disallowed",
    "full_eval": "not_run",
    "runtime_mutation": "disallowed",
    "ingestion_source_mutation": "disallowed",
    "retriever_mutation": "disallowed",
    "rerank_mutation": "disallowed",
    "prompt_mutation": "disallowed",
    "anchor_mutation": "disallowed",
    "risk_rule_mutation": "disallowed",
    "risk_supplement_mutation": "disallowed",
    "term_preservation_rule_mutation": "disallowed",
    "scenario_registry_mutation": "disallowed",
    "eval_case_mutation": "disallowed",
    "fixture_mutation": "disallowed",
}

SOURCE_EXPECTATIONS = {
    "authorization_design": {
        "version": "0.4.13.13",
        "schema_kind": "rebuild_authorization_design",
        "status": "ready_for_rebuild_authorization_design_gate",
        "allowed_next_step": "rebuild_authorization_design_gate",
    },
    "authorization_gate": {
        "version": "0.4.13.14",
        "schema_kind": "rebuild_authorization_design_gate",
        "status": "passed",
        "allowed_next_step": "human_rebuild_authorization_worksheet",
    },
    "worksheet": {
        "version": "0.4.13.15",
        "schema_kind": "human_rebuild_authorization_worksheet",
        "status": "ready_for_human_rebuild_authorization_review",
        "allowed_next_step": "human_rebuild_authorization_worksheet_gate",
    },
    "worksheet_gate": {
        "version": "0.4.13.16",
        "schema_kind": "human_rebuild_authorization_worksheet_gate",
        "status": "passed",
        "allowed_next_step": "rebuild_runbook_preflight_contract",
    },
    "runbook_contract": {
        "version": "0.4.13.17",
        "schema_kind": "rebuild_runbook_preflight_contract",
        "status": "ready_for_series_closeout",
        "allowed_next_step": "v0.4.13_series_closeout",
    },
}

SUMMARY_BOUNDARIES = {
    "authorization_granted": False,
    "rebuild_allowed": False,
    "qdrant_write_allowed": False,
    "full_eval": "not_run",
}

GUARDRAIL_BOUNDARIES = {
    "authorization_granted": False,
    "human_authorization_record_created": False,
    "human_values_collected": False,
    "captures_formal_authorization_outcome": False,
    "live_preflight_run": False,
    "qdrant_access": "disallowed",
    "qdrant_write": "disallowed",
    "collection_rebuild": "disallowed",
    "rag_query_integration": "disallowed",
    "embedding_call": "disallowed",
    "llm_access": "disallowed",
    "full_eval": "not_run",
    "runtime_mutation": "disallowed",
    "ingestion_source_mutation": "disallowed",
    "eval_case_mutation": "disallowed",
    "fixture_mutation": "disallowed",
}


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return data if isinstance(data, dict) else {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def source_meta(path: Path, data: dict[str, Any]) -> dict[str, Any]:
    summary = as_dict(data.get("summary"))
    return {
        "path": str(path),
        "present": path.exists(),
        "version": data.get("version"),
        "schema_kind": data.get("schema_kind"),
        "status": summary.get("status"),
        "allowed_next_step": summary.get("allowed_next_step"),
    }


def source_blockers(reports: dict[str, dict[str, Any]]) -> list[str]:
    blockers: list[str] = []
    for key, expectation in SOURCE_EXPECTATIONS.items():
        report = reports[key]
        summary = as_dict(report.get("summary"))
        gate = as_dict(report.get("worksheet_gate"))
        actual_status = gate.get("status") if key == "worksheet" else summary.get("status")
        if not report:
            blockers.append(f"{key}_missing")
        if report.get("version") != expectation["version"]:
            blockers.append(f"{key}_version_mismatch")
        if report.get("schema_kind") != expectation["schema_kind"]:
            blockers.append(f"{key}_schema_mismatch")
        if actual_status != expectation["status"]:
            blockers.append(f"{key}_status_mismatch")
        if summary.get("allowed_next_step") != expectation["allowed_next_step"]:
            blockers.append(f"{key}_allowed_next_step_mismatch")
        for field, expected in SUMMARY_BOUNDARIES.items():
            if summary.get(field) != expected:
                blockers.append(f"{key}_{field}_mismatch")
        if gate:
            for field, expected in SUMMARY_BOUNDARIES.items():
                if field in gate and gate.get(field) != expected:
                    blockers.append(f"{key}_worksheet_gate_{field}_mismatch")
        guardrails = as_dict(report.get("guardrails"))
        for field, expected in GUARDRAIL_BOUNDARIES.items():
            if field in guardrails and guardrails.get(field) != expected:
                blockers.append(f"{key}_guardrail_{field}_mismatch")
    return blockers


def build_report(
    auth_design_path: Path = DEFAULT_AUTH_DESIGN_PATH,
    auth_gate_path: Path = DEFAULT_AUTH_GATE_PATH,
    worksheet_path: Path = DEFAULT_WORKSHEET_PATH,
    worksheet_gate_path: Path = DEFAULT_WORKSHEET_GATE_PATH,
    runbook_path: Path = DEFAULT_RUNBOOK_PATH,
) -> dict[str, Any]:
    reports = {
        "authorization_design": load_json(auth_design_path),
        "authorization_gate": load_json(auth_gate_path),
        "worksheet": load_json(worksheet_path),
        "worksheet_gate": load_json(worksheet_gate_path),
        "runbook_contract": load_json(runbook_path),
    }
    blockers = source_blockers(reports)
    status = "closed_for_execution_design_handoff" if not blockers else "blocked"
    return {
        "version": VERSION,
        "schema_kind": "ingestion_metadata_rebuild_planning_series_closeout",
        "scope": "v0.4.13 rebuild planning series closeout only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "authorization_design": source_meta(auth_design_path, reports["authorization_design"]),
            "authorization_gate": source_meta(auth_gate_path, reports["authorization_gate"]),
            "worksheet": source_meta(worksheet_path, reports["worksheet"]),
            "worksheet_gate": source_meta(worksheet_gate_path, reports["worksheet_gate"]),
            "runbook_contract": source_meta(runbook_path, reports["runbook_contract"]),
        },
        "guardrails": GUARDRAILS,
        "summary": {
            "status": status,
            "completed_report_count": 5 if not blockers else 0,
            "allowed_next_step": "production_rebuild_execution_design" if not blockers else "blocked",
            "production_rebuild_executed": False,
            "live_preflight_run": False,
            "authorization_granted": False,
            "qdrant_write_allowed": False,
            "rebuild_allowed": False,
            "full_eval": "not_run",
            "blockers": blockers,
        },
        "completed_chain": [
            "v0.4.13.0-v0.4.13.7 ingestion metadata patch contract/design/gates",
            "v0.4.13.8 minimal ingestion metadata source patch",
            "v0.4.13.9-v0.4.13.12 post-patch rebuild dry-run design/runner/gates",
            "v0.4.13.13 rebuild authorization design",
            "v0.4.13.14 rebuild authorization design gate",
            "v0.4.13.15 human rebuild authorization worksheet",
            "v0.4.13.16 human rebuild authorization worksheet gate",
            "v0.4.13.17 rebuild runbook/preflight contract",
        ],
        "handoff": {
            "next_allowed_step": "design a separate production rebuild execution series" if not blockers else "resolve closeout blockers",
            "not_allowed_yet": [
                "run live preflight",
                "write Qdrant",
                "rebuild collection",
                "call rag_query",
                "run full eval",
                "modify runtime or eval artifacts",
                "modify prompt, rerank, anchors, risk rules, scenario registry, fixtures, or eval cases",
            ],
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        "# v0.4.13.18 Ingestion Metadata Rebuild Planning Series Closeout",
        "",
        "本 closeout 关闭 v0.4.13 ingestion metadata patch and rebuild planning series，并只把后续工作移交到单独的 `production_rebuild_execution_design`。它不执行 rebuild，不运行 live preflight，不访问 Qdrant。",
        "",
        "## 摘要",
        "",
        f"- 状态: `{summary.get('status')}`",
        f"- 完成报告数: `{summary.get('completed_report_count')}`",
        f"- 允许的下一步: `{summary.get('allowed_next_step')}`",
        f"- 是否已执行生产 rebuild: `{summary.get('production_rebuild_executed')}`",
        f"- 是否允许 rebuild: `{summary.get('rebuild_allowed')}`",
        "",
        "## 已完成链路",
        "",
    ]
    for item in report.get("completed_chain", []):
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## 边界",
        "",
        "通过本 closeout 只允许进入 `production_rebuild_execution_design`，仍不代表已经允许生产 Qdrant rebuild。下一系列也必须先做执行设计，不能直接运行 live preflight、写入 Qdrant 或 rebuild collection。",
    ])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the v0.4.13.18 rebuild planning series closeout.")
    parser.add_argument("--authorization-design", type=Path, default=DEFAULT_AUTH_DESIGN_PATH)
    parser.add_argument("--authorization-gate", type=Path, default=DEFAULT_AUTH_GATE_PATH)
    parser.add_argument("--worksheet", type=Path, default=DEFAULT_WORKSHEET_PATH)
    parser.add_argument("--worksheet-gate", type=Path, default=DEFAULT_WORKSHEET_GATE_PATH)
    parser.add_argument("--runbook", type=Path, default=DEFAULT_RUNBOOK_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_MARKDOWN_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(
        args.authorization_design,
        args.authorization_gate,
        args.worksheet,
        args.worksheet_gate,
        args.runbook,
    )
    write_json(args.output, report)
    write_text(args.summary, render_markdown(report))
    summary = as_dict(report.get("summary"))
    print(
        "Ingestion metadata rebuild planning closeout: "
        f"{summary.get('status')}, next={summary.get('allowed_next_step')}"
    )
    return 0 if summary.get("status") != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
