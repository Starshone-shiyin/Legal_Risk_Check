"""Pydantic contracts and deterministic validation for custom Skills."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


NodeType = Literal[
    "document_extract",
    "retrieve",
    "evidence_gate",
    "web_supplement",
    "risk_analysis",
    "human_review",
    "report_output",
]
MAX_SKILL_NODES = 6
MAX_SKILL_EDGES = MAX_SKILL_NODES * (MAX_SKILL_NODES - 1) // 2

NODE_TYPE_SPECS: dict[str, dict[str, Any]] = {
    "document_extract": {
        "name": "材料提取",
        "description": "仅使用用户明确选择且已完成解析的材料，不访问未授权文件。",
        "parameters": {"max_documents": "整数，1 至 3"},
    },
    "retrieve": {
        "name": "本地检索",
        "description": "从本地知识库召回证据，不在该阶段生成结论。",
        "parameters": {"top_k": "整数，1 至 20", "legal_only": "布尔值"},
    },
    "evidence_gate": {
        "name": "证据门控",
        "description": "在进入下一环节前评估证据充分性，并检查是否命中本地法源。",
        "parameters": {"min_score": "数值，0 至 1", "require_local_law": "布尔值"},
    },
    "web_supplement": {
        "name": "联网补证",
        "description": "请求受控的在线证据补充，可限制为官方域名来源。",
        "parameters": {"mode": "auto 或 force", "max_results": "整数，1 至 5", "official_domains_only": "布尔值"},
    },
    "risk_analysis": {
        "name": "风险分析",
        "description": "在已获证据范围内形成法律、合规或市场风险分析。",
        "parameters": {"focus": "legal、compliance 或 market", "include_actions": "布尔值"},
    },
    "human_review": {
        "name": "人工复核",
        "description": "对证据不足或问题复杂的结果标记为需要人工复核。",
        "parameters": {"on_insufficient_evidence": "布尔值"},
    },
    "report_output": {
        "name": "报告输出",
        "description": "组织最终问答或报告的呈现结果，并可附带引文。",
        "parameters": {"format": "markdown 或 json", "include_citations": "布尔值"},
    },
}


class SkillNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,31}$")
    node_type: NodeType
    parameters: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_parameters(self) -> "SkillNode":
        _validate_node_parameters(self.node_type, self.parameters)
        return self


class SkillEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,31}$")
    target: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,31}$")


class SkillPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=500)
    nodes: list[SkillNode] = Field(min_length=1, max_length=MAX_SKILL_NODES)
    edges: list[SkillEdge] = Field(default_factory=list, max_length=MAX_SKILL_EDGES)

    @model_validator(mode="after")
    def validate_graph(self) -> "SkillPayload":
        node_ids = [node.node_id for node in self.nodes]
        if len(set(node_ids)) != len(node_ids):
            raise ValueError("Skill node_id values must be unique")
        node_types = [node.node_type for node in self.nodes]
        if len(set(node_types)) != len(node_types):
            raise ValueError("Each node type can appear at most once in a Skill")

        known_nodes = set(node_ids)
        edge_pairs: set[tuple[str, str]] = set()
        for edge in self.edges:
            if edge.source not in known_nodes or edge.target not in known_nodes:
                raise ValueError("Skill edges must reference existing nodes")
            if edge.source == edge.target:
                raise ValueError("Skill edges cannot be self-referential")
            pair = (edge.source, edge.target)
            if pair in edge_pairs:
                raise ValueError("Skill edges must be unique")
            edge_pairs.add(pair)
        if _has_cycle(node_ids, self.edges):
            raise ValueError("Skill graph must be acyclic")
        return self


class SkillRecord(SkillPayload):
    skill_id: str = Field(pattern=r"^(builtin|skill)-[a-z0-9-]{3,80}$")
    is_builtin: bool = False
    created_at: datetime
    updated_at: datetime


class SkillListResponse(BaseModel):
    status: Literal["ok"] = "ok"
    items: list[SkillRecord] = Field(default_factory=list)


class SkillResponse(BaseModel):
    status: Literal["ok"] = "ok"
    data: SkillRecord


class DeleteSkillResponse(BaseModel):
    status: Literal["ok"] = "ok"
    deleted_id: str


class SkillNodeTypesResponse(BaseModel):
    status: Literal["ok"] = "ok"
    node_types: dict[str, dict[str, Any]]


class SkillValidationResponse(BaseModel):
    status: Literal["ok"] = "ok"
    valid: bool = True
    node_count: int
    edge_count: int
    topological_order: list[str]


class SkillExecutionStep(BaseModel):
    sequence: int = Field(ge=1)
    node_id: str
    node_type: NodeType
    parameters: dict[str, Any]


class SkillRunResponse(BaseModel):
    status: Literal["completed", "blocked"] = "blocked"
    skill_id: str
    execution_plan: list[SkillExecutionStep]
    blocked_rationale: str | None = None
    result: dict[str, Any] | None = None
    run_metadata: dict[str, Any] = Field(default_factory=dict)


class SkillRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=4000)
    document_task_ids: list[str] = Field(default_factory=list, max_length=3)
    debug: bool = False


def topological_order(nodes: list[SkillNode], edges: list[SkillEdge]) -> list[str]:
    """Return a stable execution order after payload validation has accepted the graph."""
    node_ids = [node.node_id for node in nodes]
    outgoing = {node_id: [] for node_id in node_ids}
    incoming = {node_id: 0 for node_id in node_ids}
    for edge in edges:
        outgoing[edge.source].append(edge.target)
        incoming[edge.target] += 1
    ready = [node_id for node_id in node_ids if incoming[node_id] == 0]
    order: list[str] = []
    while ready:
        current = ready.pop(0)
        order.append(current)
        for target in outgoing[current]:
            incoming[target] -= 1
            if incoming[target] == 0:
                ready.append(target)
    return order


def _has_cycle(node_ids: list[str], edges: list[SkillEdge]) -> bool:
    return len(topological_order([SkillNode(node_id=node_id, node_type="retrieve") for node_id in node_ids], edges)) != len(node_ids)


def _validate_node_parameters(node_type: NodeType, parameters: dict[str, Any]) -> None:
    validators = {
        "document_extract": {"max_documents": _integer_between(1, 3)},
        "retrieve": {"top_k": _integer_between(1, 20), "legal_only": _is_bool},
        "evidence_gate": {"min_score": _number_between(0, 1), "require_local_law": _is_bool},
        "web_supplement": {
            "mode": lambda value: value in {"auto", "force"},
            "max_results": _integer_between(1, 5),
            "official_domains_only": _is_bool,
        },
        "risk_analysis": {"focus": lambda value: value in {"legal", "compliance", "market"}, "include_actions": _is_bool},
        "human_review": {"on_insufficient_evidence": _is_bool},
        "report_output": {"format": lambda value: value in {"markdown", "json"}, "include_citations": _is_bool},
    }[node_type]
    unexpected = sorted(set(parameters) - set(validators))
    if unexpected:
        raise ValueError(f"Unsupported parameters for {node_type}: {', '.join(unexpected)}")
    invalid = sorted(name for name, value in parameters.items() if not validators[name](value))
    if invalid:
        raise ValueError(f"Invalid parameters for {node_type}: {', '.join(invalid)}")


def _integer_between(minimum: int, maximum: int):
    return lambda value: isinstance(value, int) and not isinstance(value, bool) and minimum <= value <= maximum


def _number_between(minimum: float, maximum: float):
    return lambda value: isinstance(value, (int, float)) and not isinstance(value, bool) and minimum <= float(value) <= maximum


def _is_bool(value: Any) -> bool:
    return isinstance(value, bool)
