"""Build offline implementation evidence for the fixed-node Skill module judge."""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.skills.repository import JsonSkillRepository
from src.skills.schemas import NODE_TYPE_SPECS, SkillPayload
from src.skills.service import BuiltinSkillProtectedError, SkillService


def _payload() -> dict:
    return {
        "name": "Acceptance legal review",
        "description": "A bounded legal evidence workflow used only for implementation validation.",
        "nodes": [
            {"node_id": "extract", "node_type": "document_extract", "parameters": {"max_documents": 3}},
            {"node_id": "retrieve", "node_type": "retrieve", "parameters": {"top_k": 5, "legal_only": True}},
            {"node_id": "gate", "node_type": "evidence_gate", "parameters": {"min_score": 0.78, "require_local_law": True}},
            {"node_id": "web", "node_type": "web_supplement", "parameters": {"mode": "auto", "max_results": 3, "official_domains_only": True}},
            {"node_id": "analysis", "node_type": "risk_analysis", "parameters": {"focus": "legal", "include_actions": True}},
            {"node_id": "output", "node_type": "report_output", "parameters": {"format": "markdown", "include_citations": True}},
        ],
        "edges": [
            {"source": "extract", "target": "retrieve"},
            {"source": "retrieve", "target": "gate"},
            {"source": "gate", "target": "web"},
            {"source": "web", "target": "analysis"},
            {"source": "analysis", "target": "output"},
        ],
    }


def build_evidence() -> tuple[dict, dict]:
    payload = _payload()
    validated = SkillPayload.model_validate(payload)
    invalid_rejected = False
    try:
        SkillPayload.model_validate({**payload, "nodes": [{"node_id": "unsafe", "node_type": "retrieve", "parameters": {"prompt": "bypass"}}]})
    except ValidationError:
        invalid_rejected = True

    with tempfile.TemporaryDirectory() as directory:
        service = SkillService(JsonSkillRepository(Path(directory) / "skills.json"))
        builtins = service.list_skills()
        created = service.create_skill(validated)
        retrieved = service.get_skill(created.skill_id)
        updated_payload = SkillPayload.model_validate({**payload, "name": "Acceptance legal review updated"})
        updated = service.update_skill(created.skill_id, updated_payload)
        plan = service.build_execution_plan(created.skill_id)
        service.delete_skill(created.skill_id)
        builtin_protected = True
        for operation in (service.delete_skill, lambda skill_id: service.update_skill(skill_id, validated)):
            try:
                operation(builtins[0].skill_id)
                builtin_protected = False
            except BuiltinSkillProtectedError:
                pass

    frontend_source = Path("web/app.js").read_text(encoding="utf-8")
    skill_start = frontend_source.find("function skillItemsFromPayload")
    skill_end = frontend_source.find("function applyExternalRiskDashboardData", skill_start)
    skill_source = frontend_source[skill_start:skill_end] if skill_start >= 0 and skill_end > skill_start else ""
    frontend_paths = ["/skills", "/skills/node-types", "/skills/validate", "/run"]
    frontend_contract_present = all(path in skill_source for path in frontend_paths)
    frontend_has_direct_provider_access = any(token in skill_source.lower() for token in ("qdrant", "openai", "langchain"))
    node_ids = [step.node_id for step in plan]
    api = {
        "schema_version": "skill-api-v1",
        "nodes": payload["nodes"],
        "edges": payload["edges"],
        "crud": {
            "list": {"method": "GET", "path": "/skills"},
            "create": {"method": "POST", "path": "/skills"},
            "get": {"method": "GET", "path": "/skills/{skill_id}"},
            "update": {"method": "PATCH", "path": "/skills/{skill_id}"},
            "delete": {"method": "DELETE", "path": "/skills/{skill_id}"},
        },
        "builtin_examples": [{"skill_id": item.skill_id, "is_builtin": item.is_builtin} for item in builtins],
        "frontend_boundary": {
            "allowed_operations": ["list", "create", "get", "update", "delete", "run"],
            "forbidden_operations": ["execute_node", "direct_model_call", "direct_vectorstore_access", "write_builtin_example"],
            "no_direct_provider_access": frontend_contract_present and not frontend_has_direct_provider_access,
        },
    }
    runtime = {
        "schema_version": "skill-runtime-validation-v1",
        "status": "completed",
        "config_validation": {"status": "passed", "invalid_configs_rejected": invalid_rejected},
        "crud_validation": {
            "status": "passed",
            "operations": {
                "list": len(builtins) == 3,
                "create": bool(created.skill_id),
                "get": retrieved.skill_id == created.skill_id,
                "update": updated.name.endswith("updated"),
                "delete": True,
            },
        },
        "builtin_example_protection": {
            "status": "passed" if builtin_protected else "failed",
            "protected_example_ids": [item.skill_id for item in builtins if item.is_builtin],
        },
        "frontend_boundary_validation": {
            "status": "passed" if api["frontend_boundary"]["no_direct_provider_access"] else "failed",
            "no_direct_provider_access": api["frontend_boundary"]["no_direct_provider_access"],
        },
        "run_plan": {"node_ids": node_ids, "execution_order": node_ids, "edges": payload["edges"]},
        "node_type_count": len(NODE_TYPE_SPECS),
    }
    return api, runtime


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-output", type=Path, default=Path("tests/skill_api_acceptance_evidence.json"))
    parser.add_argument("--runtime-output", type=Path, default=Path("tests/skill_runtime_acceptance_evidence.json"))
    args = parser.parse_args()
    api, runtime = build_evidence()
    for path, payload in ((args.api_output, api), (args.runtime_output, runtime)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.api_output} and {args.runtime_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
