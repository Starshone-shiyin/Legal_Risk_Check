"""Import filled manual-review workbench data into a proposed schema.

The importer reads filled visual workbench JSON input and writes a proposed
decision schema. CSV files are view-only artifacts and are rejected as formal
input. It never overwrites the original decision schema and does not modify
retrieval, rerank, prompts, anchors, risk rules, eval cases, hidden seeds, or
the RAG main flow.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.build_workbench_intake_contract import IMPORTABLE_REVIEWER_FIELDS, LIST_FIELDS, REQUIRED_FOR_COMPLETED
from tools.check_evidence_alignment import normalize_text
from tools._shared.layout import legacy_report_path


VERSION = "0.4.7.7.1"

DEFAULT_DECISION_SCHEMA_PATH = Path("tests/evidence_manual_review_decision_schema.json")
DEFAULT_WORKBENCH_INPUT_PATH = Path("tests/evidence_manual_review_workbench.csv")
DEFAULT_OUTPUT_PATH = Path("tests/proposed_manual_review_decision_schema.json")
DEFAULT_REPORT_PATH = legacy_report_path("manual_review_workbench_import_report.json")

LIST_DELIMITER = "|"

ERROR_MISSING_CASE_ID = "missing_case_id"
ERROR_UNKNOWN_CASE_ID = "unknown_case_id"
ERROR_DUPLICATE_CASE_ID = "duplicate_case_id"
ERROR_EMPTY_IMPORTABLE_CONTENT = "empty_importable_content"
ERROR_INVALID_JSON_WORKBENCH_EXPORT = "invalid_json_workbench_export"
ERROR_INCOMPLETE_COMPLETED_REVIEWER_FIELDS = "incomplete_completed_reviewer_fields"
ERROR_UNSUPPORTED_WORKBENCH_INPUT = "unsupported_workbench_input"
ERROR_ADVISORY_REVIEW_MARKER = "advisory_review_marker"
ERROR_EXPORT_METADATA_MISMATCH = "export_metadata_mismatch"

FILLED_WORKBENCH_EXPORT_SCOPE = "filled visual manual review workbench export"
READY_HUMAN_DRAFTS_EXPORT_POLICY = "ready_human_drafts_only"
COMPLETED_DECISIONS = {"confirm_diagnostic_issue", "confirm_scope_adjustment_needed", "reject_diagnostic_issue"}


def load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def parse_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [normalize_text(item) for item in value if normalize_text(item)]
    text = normalize_text(value)
    if not text:
        return []
    return [part.strip() for part in text.split(LIST_DELIMITER) if part.strip()]


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return normalize_text(value).lower() in {"true", "1", "yes", "y"}


def has_importable_content(row: dict[str, Any]) -> bool:
    for field in IMPORTABLE_REVIEWER_FIELDS:
        value = row.get(field)
        if field in LIST_FIELDS:
            if parse_list(value):
                return True
        elif field == "fixture_candidate":
            if parse_bool(value):
                return True
        elif normalize_text(value):
            return True
    return False


def missing_completed_required_fields(row: dict[str, Any]) -> list[str]:
    return [field for field in REQUIRED_FOR_COMPLETED if not normalize_text(row.get(field))]


def normalize_reviewer_decision(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "reviewer": normalize_text(row.get("reviewer")),
        "reviewed_at": normalize_text(row.get("reviewed_at")),
        "decision": normalize_text(row.get("decision")),
        "confirmed_root_causes": parse_list(row.get("confirmed_root_causes")),
        "rejected_root_causes": parse_list(row.get("rejected_root_causes")),
        "confirmed_follow_up_actions": parse_list(row.get("confirmed_follow_up_actions")),
        "proposed_change_targets": parse_list(row.get("proposed_change_targets")),
        "fixture_candidate": parse_bool(row.get("fixture_candidate")),
        "rationale": normalize_text(row.get("rationale")),
        "notes": normalize_text(row.get("notes")),
    }


def read_csv_rows(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        row_count = max(sum(1 for _ in file) - 1, 1)
    return [
        {
            "case_id": "",
            "_import_errors": [ERROR_UNSUPPORTED_WORKBENCH_INPUT],
        }
        for _ in range(row_count)
    ]


def read_json_rows(path: Path) -> list[dict[str, Any]]:
    data = load_json(path)
    if not is_filled_workbench_export(data):
        return invalid_json_rows(data)
    export_errors = export_metadata_errors(data)
    rows = []
    for item in data.get("workbench_items") or []:
        if not isinstance(item, dict):
            continue
        errors = [*export_errors, *import_contract_errors_for_item(item)]
        template = item.get("reviewer_input_template") if isinstance(item.get("reviewer_input_template"), dict) else {}
        rows.append({"case_id": item.get("case_id"), **template, "_import_errors": errors})
    return rows


def is_filled_workbench_export(data: Any) -> bool:
    if not isinstance(data, dict):
        return False
    summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
    return (
        data.get("scope") == FILLED_WORKBENCH_EXPORT_SCOPE
        and summary.get("export_policy") == READY_HUMAN_DRAFTS_EXPORT_POLICY
        and isinstance(data.get("workbench_items"), list)
        and data.get("advisory_packet_only") is not True
        and data.get("contains_completed_manual_decisions") is not False
    )


def export_metadata_errors(data: dict[str, Any]) -> list[str]:
    summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
    items = [item for item in data.get("workbench_items") or [] if isinstance(item, dict)]
    item_ids = [normalize_text(item.get("case_id")) for item in items]
    exported_ids = [normalize_text(case_id) for case_id in summary.get("exported_case_ids") or []]
    errors = []
    if not exported_ids:
        # Legacy cleaned exports created before export_case_ids are still accepted,
        # but new browser exports include the field for stronger provenance checks.
        return errors
    if len(exported_ids) != len(items):
        errors.append(ERROR_EXPORT_METADATA_MISMATCH)
    if sorted(exported_ids) != sorted(item_ids):
        errors.append(ERROR_EXPORT_METADATA_MISMATCH)
    if summary.get("exported_draft_items") not in (None, len(items)):
        errors.append(ERROR_EXPORT_METADATA_MISMATCH)
    if summary.get("total_workbench_items") not in (None, len(items)):
        errors.append(ERROR_EXPORT_METADATA_MISMATCH)
    return list(dict.fromkeys(errors))


def import_contract_errors_for_item(item: dict[str, Any]) -> list[str]:
    errors = []
    template = item.get("reviewer_input_template") if isinstance(item.get("reviewer_input_template"), dict) else {}
    marker_sources = [item, template]
    if isinstance(item.get("ai_review_suggestion"), dict):
        marker_sources.append(item["ai_review_suggestion"])
    for source in marker_sources:
        if source.get("advisory_only") is True:
            errors.append(ERROR_ADVISORY_REVIEW_MARKER)
        if source.get("human_confirmation_required") is True:
            errors.append(ERROR_ADVISORY_REVIEW_MARKER)
        if source.get("ai_suggestion") is True:
            errors.append(ERROR_ADVISORY_REVIEW_MARKER)
        if source.get("suggestion_type") == "ai_assisted_manual_review_prefill":
            errors.append(ERROR_ADVISORY_REVIEW_MARKER)
    marker_text = " ".join(
        normalize_text(value).lower()
        for value in [template.get("reviewer"), template.get("rationale"), template.get("notes")]
    )
    if any(marker in marker_text for marker in ["ai-assisted", "ai assisted", "ai辅助", "辅助预填", "待人工确认"]):
        errors.append(ERROR_ADVISORY_REVIEW_MARKER)
    return list(dict.fromkeys(errors))


def invalid_json_rows(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, dict) and isinstance(data.get("workbench_items"), list):
        rows = []
        for item in data.get("workbench_items") or []:
            rows.append({
                "case_id": item.get("case_id") if isinstance(item, dict) else "",
                "_import_errors": [ERROR_INVALID_JSON_WORKBENCH_EXPORT],
            })
        return rows or [{"case_id": "", "_import_errors": [ERROR_INVALID_JSON_WORKBENCH_EXPORT]}]
    if isinstance(data, list):
        rows = []
        for item in data:
            rows.append({
                "case_id": item.get("case_id") if isinstance(item, dict) else "",
                "_import_errors": [ERROR_INVALID_JSON_WORKBENCH_EXPORT],
            })
        return rows or [{"case_id": "", "_import_errors": [ERROR_INVALID_JSON_WORKBENCH_EXPORT]}]
    return [{"case_id": "", "_import_errors": [ERROR_INVALID_JSON_WORKBENCH_EXPORT]}]


def read_input_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".json":
        return read_json_rows(path)
    if path.suffix.lower() == ".csv":
        return read_csv_rows(path)
    return [{"case_id": "", "_import_errors": [ERROR_UNSUPPORTED_WORKBENCH_INPUT]}]


def schema_records_by_case(decision_schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        normalize_text(record.get("case_id")): record
        for record in decision_schema.get("decision_records") or []
        if isinstance(record, dict) and normalize_text(record.get("case_id"))
    }


def import_rows(decision_schema: dict[str, Any], rows: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    proposed = copy.deepcopy(decision_schema)
    proposed["version"] = VERSION
    proposed["scope"] = "proposed manual review decision schema"
    proposed.setdefault("inputs", {})["source_decision_schema_version"] = decision_schema.get("version")

    by_case = schema_records_by_case(proposed)
    seen = Counter(normalize_text(row.get("case_id")) for row in rows if normalize_text(row.get("case_id")))
    import_results = []
    summary = Counter()

    for row_index, row in enumerate(rows, start=1):
        cid = normalize_text(row.get("case_id"))
        errors = list(dict.fromkeys(row.get("_import_errors") or []))
        if not cid:
            errors.append(ERROR_MISSING_CASE_ID)
        elif cid not in by_case:
            errors.append(ERROR_UNKNOWN_CASE_ID)
        elif seen[cid] > 1:
            errors.append(ERROR_DUPLICATE_CASE_ID)
        if not has_importable_content(row):
            errors.append(ERROR_EMPTY_IMPORTABLE_CONTENT)
        decision = normalize_text(row.get("decision"))
        if decision in COMPLETED_DECISIONS and missing_completed_required_fields(row):
            errors.append(ERROR_INCOMPLETE_COMPLETED_REVIEWER_FIELDS)

        if errors:
            summary["rejected_rows"] += 1
            for error in errors:
                summary[error] += 1
            import_results.append({
                "row_index": row_index,
                "case_id": cid,
                "import_status": "rejected",
                "errors": list(dict.fromkeys(errors)),
            })
            continue

        record = by_case[cid]
        reviewer_decision = normalize_reviewer_decision(row)
        record["reviewer_decision"] = reviewer_decision
        decision = reviewer_decision.get("decision")
        if decision in {"confirm_diagnostic_issue", "confirm_scope_adjustment_needed", "reject_diagnostic_issue"}:
            record["decision_status"] = "completed"
        elif decision in {"defer", "insufficient_information"}:
            record["decision_status"] = "deferred"
        else:
            record["decision_status"] = "pending"
        summary["imported_rows"] += 1
        import_results.append({
            "row_index": row_index,
            "case_id": cid,
            "import_status": "imported",
            "decision_status": record["decision_status"],
            "decision": decision,
        })

    proposed["summary"] = {
        **(proposed.get("summary") or {}),
        "imported_decisions": summary.get("imported_rows", 0),
        "import_rejected_rows": summary.get("rejected_rows", 0),
    }
    report = {
        "version": VERSION,
        "scope": "offline workbench import report",
        "summary": {
            "input_rows": len(rows),
            "imported_rows": summary.get("imported_rows", 0),
            "rejected_rows": summary.get("rejected_rows", 0),
            "missing_case_id": summary.get(ERROR_MISSING_CASE_ID, 0),
            "unknown_case_id": summary.get(ERROR_UNKNOWN_CASE_ID, 0),
            "duplicate_case_id": summary.get(ERROR_DUPLICATE_CASE_ID, 0),
            "empty_importable_content": summary.get(ERROR_EMPTY_IMPORTABLE_CONTENT, 0),
            "invalid_json_workbench_export": summary.get(ERROR_INVALID_JSON_WORKBENCH_EXPORT, 0),
            "incomplete_completed_reviewer_fields": summary.get(ERROR_INCOMPLETE_COMPLETED_REVIEWER_FIELDS, 0),
            "unsupported_workbench_input": summary.get(ERROR_UNSUPPORTED_WORKBENCH_INPUT, 0),
            "advisory_review_marker": summary.get(ERROR_ADVISORY_REVIEW_MARKER, 0),
            "export_metadata_mismatch": summary.get(ERROR_EXPORT_METADATA_MISMATCH, 0),
        },
        "import_results": import_results,
    }
    return proposed, report


def build_outputs(decision_schema_path: Path, workbench_input_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    decision_schema = load_json(decision_schema_path)
    rows = read_input_rows(workbench_input_path)
    proposed, report = import_rows(decision_schema, rows)
    report["inputs"] = {
        "decision_schema": str(decision_schema_path),
        "decision_schema_version": decision_schema.get("version"),
        "workbench_input": str(workbench_input_path),
    }
    proposed.setdefault("inputs", {})["workbench_input"] = str(workbench_input_path)
    return proposed, report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import filled manual-review workbench into proposed schema.")
    parser.add_argument("--decision-schema", type=Path, default=DEFAULT_DECISION_SCHEMA_PATH)
    parser.add_argument("--workbench-input", type=Path, default=DEFAULT_WORKBENCH_INPUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    proposed, report = build_outputs(args.decision_schema, args.workbench_input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(proposed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.report_output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = report["summary"]
    print(
        "Manual review workbench imported: "
        f"{summary['imported_rows']} imported, "
        f"{summary['rejected_rows']} rejected"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
