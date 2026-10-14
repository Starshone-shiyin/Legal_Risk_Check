"""File-backed storage for user-defined Skill records."""
from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any


DEFAULT_SKILLS_PATH = Path("data/user_skills.json")


class SkillRepositoryDataError(ValueError):
    pass


class JsonSkillRepository:
    """Atomic JSON repository with durable, restored built-in examples."""

    def __init__(self, path: Path = DEFAULT_SKILLS_PATH) -> None:
        self.path = path
        self._lock = threading.RLock()

    def load(self) -> list[dict[str, Any]]:
        with self._lock:
            if not self.path.exists():
                records = builtin_skill_records()
                self._write(records)
                return records
            try:
                payload = json.loads(self.path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise SkillRepositoryDataError("skills repository contains invalid JSON") from exc
            if not isinstance(payload, dict) or not isinstance(payload.get("skills"), list):
                raise SkillRepositoryDataError("skills repository must contain a skills list")
            records = payload["skills"]
            builtin_records = builtin_skill_records()
            builtin_ids = {item["skill_id"] for item in builtin_records}
            # Built-ins are immutable examples, so also refresh their user-facing
            # copy when the application ships an updated official definition.
            # User-created Skills remain byte-for-byte untouched.
            user_records = [
                item
                for item in records
                if not isinstance(item, dict) or item.get("skill_id") not in builtin_ids
            ]
            refreshed_records = [*builtin_records, *user_records]
            if records != refreshed_records:
                records = refreshed_records
                self._write(records)
            if not builtin_ids.issubset({item.get("skill_id") for item in records if isinstance(item, dict)}):
                raise SkillRepositoryDataError("built-in Skills could not be restored")
            return records

    def save(self, records: list[dict[str, Any]]) -> None:
        with self._lock:
            self._write(records)

    def _write(self, records: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps({"version": 1, "skills": records}, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.path)


def builtin_skill_records() -> list[dict[str, Any]]:
    """Return stable examples; timestamps are fixed so bootstrapping is reproducible."""
    timestamp = "2026-08-10T00:00:00+00:00"
    return [
        {
            "skill_id": "builtin-legal-baseline",
            "name": "法律风险基础审查",
            "description": "检索本地法源并进行证据把关，再完成风险分析与带引文的报告输出。",
            "is_builtin": True,
            "created_at": timestamp,
            "updated_at": timestamp,
            "nodes": [
                {"node_id": "retrieve", "node_type": "retrieve", "parameters": {"top_k": 5, "legal_only": True}},
                {"node_id": "evidence", "node_type": "evidence_gate", "parameters": {"min_score": 0.78, "require_local_law": True}},
                {"node_id": "analysis", "node_type": "risk_analysis", "parameters": {"focus": "legal", "include_actions": True}},
                {"node_id": "output", "node_type": "report_output", "parameters": {"format": "markdown", "include_citations": True}},
            ],
            "edges": [
                {"source": "retrieve", "target": "evidence"},
                {"source": "evidence", "target": "analysis"},
                {"source": "analysis", "target": "output"},
            ],
        },
        {
            "skill_id": "builtin-current-law-supplement",
            "name": "现行法源补充核验",
            "description": "先检索本地法源；证据不足或问题涉及更新时，再受控补充在线权威来源。",
            "is_builtin": True,
            "created_at": timestamp,
            "updated_at": timestamp,
            "nodes": [
                {"node_id": "retrieve", "node_type": "retrieve", "parameters": {"top_k": 5, "legal_only": True}},
                {"node_id": "evidence", "node_type": "evidence_gate", "parameters": {"min_score": 0.78, "require_local_law": True}},
                {"node_id": "web", "node_type": "web_supplement", "parameters": {"mode": "auto", "max_results": 3, "official_domains_only": True}},
                {"node_id": "output", "node_type": "report_output", "parameters": {"format": "markdown", "include_citations": True}},
            ],
            "edges": [
                {"source": "retrieve", "target": "evidence"},
                {"source": "evidence", "target": "web"},
                {"source": "web", "target": "output"},
            ],
        },
        {
            "skill_id": "builtin-evidence-review",
            "name": "证据充分性复核",
            "description": "仅检查本地检索证据是否足以支撑回答，不输出风险结论。",
            "is_builtin": True,
            "created_at": timestamp,
            "updated_at": timestamp,
            "nodes": [
                {"node_id": "retrieve", "node_type": "retrieve", "parameters": {"top_k": 3, "legal_only": True}},
                {"node_id": "evidence", "node_type": "evidence_gate", "parameters": {"min_score": 0.8, "require_local_law": True}},
                {"node_id": "output", "node_type": "report_output", "parameters": {"format": "markdown", "include_citations": True}},
            ],
            "edges": [
                {"source": "retrieve", "target": "evidence"},
                {"source": "evidence", "target": "output"},
            ],
        },
    ]
