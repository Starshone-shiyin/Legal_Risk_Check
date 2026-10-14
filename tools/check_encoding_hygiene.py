"""Scan repository text files for encoding hygiene issues.

This is an offline maintenance diagnostic. It does not run eval, call RAG,
contact Qdrant or an LLM, delete files, move files, or rewrite scanned files.
The CLI only writes the requested JSON report.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "0.5.4"

DEFAULT_OUTPUT_PATH = Path("tests/encoding_hygiene_report.json")

DEFAULT_SKIP_DIRS = {
    ".git",
    ".claude",
    "backup",
    ".review_tmp",
    "venv",
    "__pycache__",
}

TEXT_SUFFIXES = {
    ".csv",
    ".html",
    ".json",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}

DEFAULT_SKIP_FILES = {
    "tests/encoding_hygiene_report.json",
}

TEMP_DIR_PATTERN = re.compile(r"^(?:tmp|temp)[A-Za-z0-9_.-]*$", re.IGNORECASE)

SUSPICIOUS_QUESTION_SEPARATOR_PATTERN = re.compile(
    r"[\u4e00-\u9fff][\u3002\uff1b\uff0c\u3001]?\?[\u4e00-\u9fffA-Z]"
)


@dataclass(frozen=True)
class Marker:
    label: str
    text: str
    severity: str


MOJIBAKE_MARKERS = [
    Marker("replacement_char", "\ufffd", "error"),
    Marker("mojibake_replacement_utf8", "\u00ef\u00bf\u00bd", "error"),
    Marker("gbk_mojibake_replacement", "\u951f\u65a4\u62f7", "error"),
    Marker("latin1_mojibake_c3", "\u00c3", "warning"),
    Marker("latin1_mojibake_c2", "\u00c2", "warning"),
    Marker("windows_quote_mojibake", "\u00e2\u20ac", "warning"),
    Marker("cjk_mojibake_guo", "\u9365", "warning"),
    Marker("cjk_mojibake_wo", "\u93b4", "warning"),
    Marker("cjk_mojibake_di", "\u7ed7", "warning"),
    Marker("cjk_mojibake_yi", "\u6d93\u20ac", "warning"),
    Marker("cjk_mojibake_ying", "\u7039", "warning"),
    Marker("cjk_mojibake_shu", "\u93c1", "warning"),
    Marker("cjk_mojibake_de", "\u9428", "warning"),
    Marker("cjk_mojibake_period", "\u9286", "warning"),
    Marker("cjk_mojibake_dian", "\u9422", "warning"),
]


def normalize_rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def should_skip(path: Path, root: Path, skip_dirs: set[str]) -> bool:
    rel_parts = path.resolve().relative_to(root.resolve()).parts
    return any(part in skip_dirs for part in rel_parts)


def iter_text_files(root: Path, suffixes: set[str], skip_dirs: set[str], skip_files: set[str]) -> list[Path]:
    files = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if should_skip(path, root, skip_dirs):
            continue
        if normalize_rel(path, root) in skip_files:
            continue
        if path.suffix.lower() not in suffixes:
            continue
        files.append(path)
    return sorted(files, key=lambda item: normalize_rel(item, root))


def line_preview(line: str, limit: int = 220) -> str:
    compact = line.strip()
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def is_intentional_marker_usage(rel_path: str, line: str) -> bool:
    if rel_path != "tools/check_ingestion_quality.py":
        return False
    return (
        "contains_replacement_char" in line
        or "\\ufffd" in line
        or chr(0xFFFD) in line
        or "possible_mojibake" in line
        or "re.search" in line
    )


def marker_hits_for_file(root: Path, path: Path, text: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rel_path = normalize_rel(path, root)
    hits: list[dict[str, Any]] = []
    allowed_hits: list[dict[str, Any]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for marker in MOJIBAKE_MARKERS:
            if marker.text not in line:
                continue
            row = {
                "path": rel_path,
                "line": line_no,
                "marker": marker.label,
                "severity": marker.severity,
                "preview": line_preview(line),
            }
            if is_intentional_marker_usage(rel_path, line):
                allowed_hits.append(row)
            else:
                hits.append(row)
    return hits, allowed_hits


def suspicious_question_separator_hits(root: Path, path: Path, text: str) -> list[dict[str, Any]]:
    rel_path = normalize_rel(path, root)
    hits = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if SUSPICIOUS_QUESTION_SEPARATOR_PATTERN.search(line):
            hits.append({
                "path": rel_path,
                "line": line_no,
                "marker": "suspicious_question_mark_separator",
                "severity": "advisory",
                "preview": line_preview(line),
            })
    return hits


def temp_directory_hits(root: Path, skip_dirs: set[str]) -> list[dict[str, Any]]:
    hits = []
    for path in sorted(root.rglob("*")):
        if not path.is_dir():
            continue
        if should_skip(path, root, skip_dirs):
            continue
        if not TEMP_DIR_PATTERN.match(path.name):
            continue
        try:
            is_empty = not any(path.iterdir())
        except OSError:
            is_empty = False
        hits.append({
            "path": normalize_rel(path, root),
            "severity": "advisory",
            "empty": is_empty,
        })
    return hits


def build_report(
    root: Path,
    suffixes: set[str] | None = None,
    skip_dirs: set[str] | None = None,
    skip_files: set[str] | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    suffixes = suffixes or TEXT_SUFFIXES
    skip_dirs = skip_dirs or DEFAULT_SKIP_DIRS
    skip_files = skip_files or DEFAULT_SKIP_FILES
    utf8_errors = []
    mojibake_hits = []
    allowed_mojibake_hits = []
    question_separator_hits = []
    files_checked = []

    for path in iter_text_files(root, suffixes, skip_dirs, skip_files):
        rel_path = normalize_rel(path, root)
        files_checked.append(rel_path)
        data = path.read_bytes()
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            utf8_errors.append({
                "path": rel_path,
                "severity": "error",
                "error": str(exc),
            })
            continue

        file_hits, file_allowed_hits = marker_hits_for_file(root, path, text)
        mojibake_hits.extend(file_hits)
        allowed_mojibake_hits.extend(file_allowed_hits)
        question_separator_hits.extend(suspicious_question_separator_hits(root, path, text))

    temp_dirs = temp_directory_hits(root, skip_dirs)
    error_count = len(utf8_errors) + sum(1 for hit in mojibake_hits if hit["severity"] == "error")
    warning_count = (
        sum(1 for hit in mojibake_hits if hit["severity"] != "error")
        + len(question_separator_hits)
        + len(temp_dirs)
    )
    sections = {
        "utf8_errors": utf8_errors,
        "mojibake_hits": mojibake_hits,
        "allowed_mojibake_hits": allowed_mojibake_hits,
        "suspicious_question_separator_hits": question_separator_hits,
        "temporary_directory_hits": temp_dirs,
    }
    return {
        "version": VERSION,
        "scope": "offline encoding and temporary artifact hygiene diagnostic",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "guardrails": {
            "scanned_files_are_not_modified": True,
            "writes_report_only": True,
            "full_eval": "not_run",
            "rag_query": "not_called",
            "qdrant_access": "not_called",
            "llm_access": "not_called",
            "file_delete_or_move": "not_performed",
        },
        "summary": {
            "status": "passed" if error_count == 0 else "failed",
            "files_checked": len(files_checked),
            "utf8_error_count": len(utf8_errors),
            "mojibake_hit_count": len(mojibake_hits),
            "allowed_mojibake_hit_count": len(allowed_mojibake_hits),
            "suspicious_question_separator_count": len(question_separator_hits),
            "temporary_directory_count": len(temp_dirs),
            "error_count": error_count,
            "warning_count": warning_count,
        },
        "files_checked": files_checked,
        **sections,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan repository text files for encoding hygiene issues.")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--fail-on-error", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.root)
    write_json(args.output, report)
    summary = report["summary"]
    print(
        "Encoding hygiene check completed: "
        f"{summary['status']}, "
        f"{summary['files_checked']} files, "
        f"{summary['error_count']} errors, "
        f"{summary['warning_count']} warnings"
    )
    return 1 if args.fail_on_error and summary["status"] != "passed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
