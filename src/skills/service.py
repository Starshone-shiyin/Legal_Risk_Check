"""CRUD service and non-executing run contract for custom Skills."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from src.skills.repository import JsonSkillRepository
from src.skills.schemas import (
    SkillExecutionStep,
    SkillPayload,
    SkillRecord,
    SkillRunResponse,
    SkillValidationResponse,
    topological_order,
)


class SkillNotFoundError(LookupError):
    pass


class BuiltinSkillProtectedError(ValueError):
    pass


class SkillService:
    def __init__(self, repository: JsonSkillRepository | Path | None = None) -> None:
        if repository is None:
            self.repository = JsonSkillRepository()
        elif isinstance(repository, Path):
            self.repository = JsonSkillRepository(repository)
        else:
            self.repository = repository

    def list_skills(self) -> list[SkillRecord]:
        return [SkillRecord.model_validate(item) for item in self.repository.load()]

    def get_skill(self, skill_id: str) -> SkillRecord:
        for item in self.repository.load():
            if item.get("skill_id") == skill_id:
                return SkillRecord.model_validate(item)
        raise SkillNotFoundError(skill_id)

    def create_skill(self, payload: SkillPayload) -> SkillRecord:
        now = datetime.now(timezone.utc)
        record = SkillRecord(
            skill_id=f"skill-{uuid4().hex}",
            is_builtin=False,
            created_at=now,
            updated_at=now,
            **payload.model_dump(),
        )
        records = self.repository.load()
        records.append(record.model_dump(mode="json"))
        self.repository.save(records)
        return record

    def update_skill(self, skill_id: str, payload: SkillPayload) -> SkillRecord:
        records = self.repository.load()
        for index, item in enumerate(records):
            if item.get("skill_id") != skill_id:
                continue
            if item.get("is_builtin"):
                raise BuiltinSkillProtectedError(skill_id)
            record = SkillRecord(
                skill_id=skill_id,
                is_builtin=bool(item.get("is_builtin")),
                created_at=item["created_at"],
                updated_at=datetime.now(timezone.utc),
                **payload.model_dump(),
            )
            records[index] = record.model_dump(mode="json")
            self.repository.save(records)
            return record
        raise SkillNotFoundError(skill_id)

    def delete_skill(self, skill_id: str) -> None:
        records = self.repository.load()
        for item in records:
            if item.get("skill_id") == skill_id and item.get("is_builtin"):
                raise BuiltinSkillProtectedError(skill_id)
        remaining = [item for item in records if item.get("skill_id") != skill_id]
        if len(remaining) == len(records):
            raise SkillNotFoundError(skill_id)
        self.repository.save(remaining)

    def validate_skill(self, payload: SkillPayload) -> SkillValidationResponse:
        return SkillValidationResponse(
            node_count=len(payload.nodes),
            edge_count=len(payload.edges),
            topological_order=topological_order(payload.nodes, payload.edges),
        )

    def run_skill(self, skill_id: str) -> SkillRunResponse:
        return SkillRunResponse(
            skill_id=skill_id,
            execution_plan=self.build_execution_plan(skill_id),
            blocked_rationale="Skill execution handler is not configured.",
        )

    def build_execution_plan(self, skill_id: str) -> list[SkillExecutionStep]:
        skill = self.get_skill(skill_id)
        by_id = {node.node_id: node for node in skill.nodes}
        return [
            SkillExecutionStep(
                sequence=index,
                node_id=node_id,
                node_type=by_id[node_id].node_type,
                parameters=by_id[node_id].parameters,
            )
            for index, node_id in enumerate(topological_order(skill.nodes, skill.edges), start=1)
        ]
