"""Check that the human-readable tool index covers current CLI entrypoints.

This is an offline documentation-maintenance diagnostic. It does not run eval,
call RAG, contact Qdrant or an LLM, move tools, or rewrite the index. The CLI
only writes the requested JSON report.
"""

from __future__ import annotations

import argparse
import ast
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "0.4.7.8.20-maintenance"

DEFAULT_TOOL_DIR = Path("tools")
DEFAULT_INDEX_PATH = Path("docs/indexes/project_tool_index.md")
DEFAULT_OUTPUT_PATH = Path("tests/tool_index_consistency_report.json")

BOUNDARY_ANCHORS = [
    "root-level `tools/*.py`",
    "可能调用 RAG/Qdrant/LLM",
    "离线诊断工具不得接入",
]


@dataclass(frozen=True)
class Pattern:
    key: str
    kind: str
    module: str | None = None
    name: str | None = None


SENSITIVE_PATTERNS = [
    Pattern("direct_rag_query", "import", "src.rag.retriever", "rag_query"),
    Pattern("direct_qdrant_client_factory", "import", "src.core.qdrant", "get_qdrant_client"),
    Pattern("direct_vectorstore_qdrant_client_factory", "import", "src.core.vectorstore", "get_qdrant_client"),
    Pattern("direct_qdrant_http_models", "import_module_prefix", "qdrant_client"),
    Pattern("direct_chat_openai", "import_module_prefix", "langchain_openai"),
    Pattern("direct_openai_sdk", "import_module_prefix", "openai"),
    Pattern("risk_analyzer_chain", "import", "src.risk.analyzer", "analyze_risk"),
    Pattern("risk_report_chain", "import", "src.risk.report", "generate_risk_report"),
    Pattern("risk_report_export_chain", "import", "src.risk.report", "generate_risk_report_export"),
    Pattern("rag_eval_runner_chain", "import", "tools.run_rag_eval", "run_case"),
    Pattern("impact_risk_runner_chain", "import", "tools.run_risk_eval", "run_case"),
    Pattern("impact_report_runner_chain", "import", "tools.run_report_eval", "run_case"),
]


def normalize_rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def root_level_tools(tool_dir: Path) -> list[Path]:
    if not tool_dir.exists():
        return []
    return sorted(path for path in tool_dir.glob("*.py") if path.is_file())


def import_aliases(node: ast.Import | ast.ImportFrom) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    module = node.module or ""
    return [f"{module}.{alias.name}" if module else alias.name for alias in node.names]


def import_matches_pattern(node: ast.Import | ast.ImportFrom, pattern: Pattern) -> bool:
    if pattern.kind == "import_module_prefix":
        return any(alias == pattern.module or alias.startswith(f"{pattern.module}.") for alias in import_aliases(node))

    if pattern.kind != "import":
        return False

    if isinstance(node, ast.ImportFrom):
        return node.module == pattern.module and any(alias.name == pattern.name for alias in node.names)

    expected = f"{pattern.module}.{pattern.name}"
    return any(alias == expected for alias in import_aliases(node))


def sensitive_hits_for_tool(path: Path) -> list[dict[str, Any]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    except SyntaxError as exc:
        return [{"key": "syntax_error", "line": exc.lineno, "detail": str(exc)}]

    hits = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        for pattern in SENSITIVE_PATTERNS:
            if import_matches_pattern(node, pattern):
                hits.append({
                    "key": pattern.key,
                    "line": getattr(node, "lineno", None),
                    "module": pattern.module,
                    "name": pattern.name,
                })
    return hits


def index_tokens(content: str) -> set[str]:
    tokens = set()
    for token in content.replace("`", " ").split():
        cleaned = token.strip(".,;:()[]{}，。；：（）【】")
        if cleaned.startswith("tools/") and cleaned.endswith(".py"):
            tokens.add(cleaned)
    return tokens


def build_report(root: Path, tool_dir: Path, index_path: Path) -> dict[str, Any]:
    root = root.resolve()
    tool_dir = (root / tool_dir).resolve() if not tool_dir.is_absolute() else tool_dir.resolve()
    index_path = (root / index_path).resolve() if not index_path.is_absolute() else index_path.resolve()

    tools = root_level_tools(tool_dir)
    root_tool_tokens = [normalize_rel(path, root) for path in tools]
    content = index_path.read_text(encoding="utf-8") if index_path.exists() else ""
    covered_tokens = index_tokens(content)
    missing_tools = [token for token in root_tool_tokens if token not in covered_tokens]
    stale_index_tokens = sorted(
        token
        for token in covered_tokens
        if token.startswith("tools/") and "*" not in token and token not in root_tool_tokens
    )
    missing_boundary_anchors = [anchor for anchor in BOUNDARY_ANCHORS if anchor not in content]

    sensitive_tools = []
    for path in tools:
        hits = sensitive_hits_for_tool(path)
        if hits:
            sensitive_tools.append({
                "path": normalize_rel(path, root),
                "signals": hits,
                "indexed": normalize_rel(path, root) in covered_tokens,
            })

    errors = []
    if not index_path.exists():
        errors.append("missing_tool_index")
    if missing_tools:
        errors.append("root_level_tool_missing_from_index")
    if missing_boundary_anchors:
        errors.append("missing_boundary_anchors")
    if any(not item["indexed"] for item in sensitive_tools):
        errors.append("sensitive_tool_missing_from_index")

    return {
        "version": VERSION,
        "scope": "offline tool index coverage and sensitive entrypoint diagnostic",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "tool_dir": normalize_rel(tool_dir, root) if tool_dir.is_relative_to(root) else str(tool_dir),
        "index_path": normalize_rel(index_path, root) if index_path.is_relative_to(root) else str(index_path),
        "guardrails": {
            "scanned_files_are_not_modified": True,
            "writes_report_only": True,
            "tool_move_or_rename": "not_performed",
            "default_path_change": "not_performed",
            "full_eval": "not_run",
            "rag_query": "not_called",
            "qdrant_access": "not_called",
            "llm_access": "not_called",
        },
        "summary": {
            "status": "passed" if not errors else "failed",
            "root_level_tool_count": len(root_tool_tokens),
            "indexed_root_level_tool_count": len(root_tool_tokens) - len(missing_tools),
            "missing_tool_count": len(missing_tools),
            "sensitive_tool_count": len(sensitive_tools),
            "missing_boundary_anchor_count": len(missing_boundary_anchors),
            "stale_index_token_count": len(stale_index_tokens),
            "error_count": len(errors),
        },
        "errors": errors,
        "root_level_tools": root_tool_tokens,
        "missing_tools": missing_tools,
        "stale_index_tokens": stale_index_tokens,
        "missing_boundary_anchors": missing_boundary_anchors,
        "sensitive_tools": sensitive_tools,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check project_tool_index.md coverage for root-level tools.")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--tool-dir", type=Path, default=DEFAULT_TOOL_DIR)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--fail-on-error", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.root, args.tool_dir, args.index)
    write_json(args.output, report)
    summary = report["summary"]
    print(
        "Tool index consistency check completed: "
        f"{summary['status']}, "
        f"{summary['root_level_tool_count']} root-level tools, "
        f"{summary['missing_tool_count']} missing, "
        f"{summary['sensitive_tool_count']} sensitive"
    )
    return 1 if args.fail_on_error and summary["status"] != "passed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
