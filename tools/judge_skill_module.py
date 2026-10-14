"""Offline acceptance judge for the fixed-node Skill module contract.

The judge consumes a Skill API contract JSON and a runtime-validation JSON. It
does not import application services or call databases, models, or the network.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


NODE_WHITELIST = {
    "document_extract",
    "retrieve",
    "evidence_gate",
    "web_supplement",
    "risk_analysis",
    "human_review",
    "report_output",
}
CRUD_METHODS = {"list": "GET", "create": "POST", "get": "GET", "update": "PATCH", "delete": "DELETE"}
FRONTEND_ALLOWED_OPERATIONS = {"list", "create", "get", "update", "delete", "run", "read_run"}
FRONTEND_FORBIDDEN_OPERATIONS = {"execute_node", "direct_model_call", "direct_vectorstore_access", "write_builtin_example"}


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _add_check(report: dict[str, Any], name: str, passed: bool, details: list[str] | None = None) -> None:
    report["checks"][name] = {"passed": passed, "details": details or []}


def _validate_node_config(node: dict[str, Any]) -> list[str]:
    node_id = node.get("node_id", "<unknown>")
    node_type = node.get("node_type")
    config = node.get("parameters")
    errors: list[str] = []
    if not isinstance(config, dict):
        return [f"node {node_id} parameters must be an object"]
    if node_type == "retrieve" and "top_k" in config:
        if not isinstance(config["top_k"], int) or not 1 <= config["top_k"] <= 20:
            errors.append(f"node {node_id} retrieve top_k must be an integer from 1 to 20")
    if node_type == "evidence_gate" and "min_score" in config:
        if not isinstance(config["min_score"], (int, float)) or not 0 <= float(config["min_score"]) <= 1:
            errors.append(f"node {node_id} evidence min_score must be within [0, 1]")
    if node_type == "web_supplement" and "max_results" in config:
        if not isinstance(config["max_results"], int) or not 1 <= config["max_results"] <= 5:
            errors.append(f"node {node_id} web_supplement max_results must be an integer from 1 to 5")
    if node_type == "report_output" and "format" in config:
        if config["format"] not in {"markdown", "json"}:
            errors.append(f"node {node_id} report_output format must be markdown or json")
    if node_type == "document_extract" and "max_documents" in config:
        if not isinstance(config["max_documents"], int) or not 1 <= config["max_documents"] <= 3:
            errors.append(f"node {node_id} document_extract max_documents must be an integer from 1 to 3")
    if node_type == "human_review" and "on_insufficient_evidence" in config:
        if not isinstance(config["on_insufficient_evidence"], bool):
            errors.append(f"node {node_id} human_review on_insufficient_evidence must be boolean")
    if node_type == "evidence_gate" and "threshold" in config:
        if not isinstance(config["threshold"], (int, float)) or not 0 <= float(config["threshold"]) <= 1:
            errors.append(f"node {node_id} evidence threshold must be within [0, 1]")
    return errors


def _graph_errors(nodes: list[dict[str, Any]], edges: list[Any]) -> list[str]:
    errors: list[str] = []
    node_ids = [node.get("node_id") for node in nodes]
    valid_ids = {node_id for node_id in node_ids if isinstance(node_id, str) and node_id}
    if len(valid_ids) != len(nodes):
        errors.append("node ids must be non-empty and unique")

    adjacency = {node_id: [] for node_id in valid_ids}
    for edge in edges:
        if not isinstance(edge, dict):
            errors.append("every edge must be an object")
            continue
        source, target = edge.get("source"), edge.get("target")
        if source not in valid_ids or target not in valid_ids:
            errors.append("edges must reference declared node ids")
            continue
        adjacency[source].append(target)

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node_id: str) -> bool:
        if node_id in visiting:
            return True
        if node_id in visited:
            return False
        visiting.add(node_id)
        cycle = any(visit(next_id) for next_id in adjacency[node_id])
        visiting.remove(node_id)
        visited.add(node_id)
        return cycle

    if any(visit(node_id) for node_id in adjacency):
        errors.append("workflow graph must be acyclic")
    return errors


def judge_payloads(skill_api: dict[str, Any], runtime: dict[str, Any]) -> dict[str, Any]:
    """Judge two JSON payloads and return a JSON-serializable acceptance report."""
    report: dict[str, Any] = {
        "schema_version": "skill-module-judge-v1",
        "verdict": "needs_revision",
        "checks": {},
        "findings": [],
    }
    api_nodes = [node for node in _as_list(skill_api.get("nodes")) if isinstance(node, dict)]
    api_edges = _as_list(skill_api.get("edges"))
    schema_ok = skill_api.get("schema_version") == "skill-api-v1" and runtime.get("schema_version") == "skill-runtime-validation-v1"
    _add_check(report, "schema_versions", schema_ok, [] if schema_ok else ["expected skill-api-v1 and skill-runtime-validation-v1"])

    unknown_nodes = sorted({node.get("node_type") for node in api_nodes if node.get("node_type") not in NODE_WHITELIST})
    missing_node_shape = [node.get("node_id", "<unknown>") for node in api_nodes if not isinstance(node.get("node_id"), str) or not node["node_id"].strip()]
    node_ok = bool(api_nodes) and not unknown_nodes and not missing_node_shape
    node_details = []
    if not api_nodes:
        node_details.append("workflow must contain at least one node")
    if unknown_nodes:
        node_details.append(f"unapproved node types: {unknown_nodes}")
    if missing_node_shape:
        node_details.append(f"nodes with invalid ids: {missing_node_shape}")
    _add_check(report, "node_whitelist", node_ok, node_details)

    graph_errors = _graph_errors(api_nodes, api_edges)
    _add_check(report, "acyclic_graph", not graph_errors, graph_errors)

    config_errors = [error for node in api_nodes for error in _validate_node_config(node)]
    runtime_config = _as_dict(runtime.get("config_validation"))
    config_ok = not config_errors and runtime_config.get("status") == "passed" and runtime_config.get("invalid_configs_rejected") is True
    config_details = config_errors + ([] if runtime_config else ["runtime config_validation is required"])
    if runtime_config and runtime_config.get("status") != "passed":
        config_details.append("runtime config validation did not pass")
    if runtime_config and runtime_config.get("invalid_configs_rejected") is not True:
        config_details.append("runtime validation must confirm invalid configurations are rejected")
    _add_check(report, "configuration_validation", config_ok, config_details)

    crud = _as_dict(skill_api.get("crud"))
    crud_errors = []
    for operation, method in CRUD_METHODS.items():
        endpoint = _as_dict(crud.get(operation))
        if endpoint.get("method") != method or not isinstance(endpoint.get("path"), str) or not endpoint["path"].startswith("/"):
            crud_errors.append(f"CRUD {operation} requires {method} and an absolute path")
    runtime_crud = _as_dict(runtime.get("crud_validation"))
    runtime_operations = _as_dict(runtime_crud.get("operations"))
    if runtime_crud.get("status") != "passed":
        crud_errors.append("runtime CRUD validation did not pass")
    for operation in CRUD_METHODS:
        if runtime_operations.get(operation) is not True:
            crud_errors.append(f"runtime CRUD validation missing success for {operation}")
    _add_check(report, "crud", not crud_errors, crud_errors)

    examples = _as_list(skill_api.get("builtin_examples"))
    example_errors = []
    if not examples:
        example_errors.append("at least one built-in example is required")
    for example in examples:
        if not isinstance(example, dict) or not isinstance(example.get("skill_id"), str) or not example.get("skill_id"):
            example_errors.append("built-in examples require an id")
        elif example.get("is_builtin") is not True:
            example_errors.append(f"built-in example {example['skill_id']} must be protected and immutable")
    runtime_examples = _as_dict(runtime.get("builtin_example_protection"))
    api_example_ids = {example.get("skill_id") for example in examples if isinstance(example, dict)}
    protected_ids = set(_as_list(runtime_examples.get("protected_example_ids")))
    if runtime_examples.get("status") != "passed":
        example_errors.append("runtime example-protection validation did not pass")
    if not api_example_ids.issubset(protected_ids):
        example_errors.append("runtime protected_example_ids must cover all built-in examples")
    _add_check(report, "builtin_example_protection", not example_errors, example_errors)

    api_boundary = _as_dict(skill_api.get("frontend_boundary"))
    runtime_boundary = _as_dict(runtime.get("frontend_boundary_validation"))
    allowed = set(_as_list(api_boundary.get("allowed_operations")))
    forbidden = set(_as_list(api_boundary.get("forbidden_operations")))
    boundary_errors = []
    if not allowed or not allowed.issubset(FRONTEND_ALLOWED_OPERATIONS):
        boundary_errors.append("frontend allowed_operations must be a non-empty subset of the public operation set")
    if not FRONTEND_FORBIDDEN_OPERATIONS.issubset(forbidden):
        boundary_errors.append("frontend boundary must explicitly forbid direct execution/provider/store/example writes")
    if api_boundary.get("no_direct_provider_access") is not True:
        boundary_errors.append("frontend boundary must disable direct provider access")
    if runtime_boundary.get("status") != "passed" or runtime_boundary.get("no_direct_provider_access") is not True:
        boundary_errors.append("runtime frontend-boundary validation did not pass")
    _add_check(report, "frontend_interface_boundary", not boundary_errors, boundary_errors)

    plan = _as_dict(runtime.get("run_plan"))
    api_ids = {node.get("node_id") for node in api_nodes}
    plan_ids = _as_list(plan.get("node_ids"))
    run_errors = []
    if runtime.get("status") not in {"passed", "completed"}:
        run_errors.append("runtime status must be passed or completed")
    if not plan_ids or set(plan_ids) != api_ids or len(plan_ids) != len(api_ids):
        run_errors.append("run plan node_ids must contain each API node exactly once")
    if plan.get("execution_order") != plan_ids:
        run_errors.append("run plan execution_order must match its node_ids")
    run_errors.extend(_graph_errors(api_nodes, _as_list(plan.get("edges"))))
    _add_check(report, "run_plan", not run_errors, run_errors)

    failed_checks = [name for name, value in report["checks"].items() if not value["passed"]]
    report["findings"] = [detail for value in report["checks"].values() for detail in value["details"]]
    report["verdict"] = "accepted" if not failed_checks else "needs_revision"
    report["summary"] = {"failed_checks": failed_checks, "passed_check_count": len(report["checks"]) - len(failed_checks)}
    return report


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-api", required=True, type=Path)
    parser.add_argument("--runtime", required=True, type=Path)
    parser.add_argument("--output", type=Path, help="Optional path for the JSON judge report.")
    args = parser.parse_args()
    report = judge_payloads(_load_json(args.skill_api), _load_json(args.runtime))
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report["verdict"] == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
