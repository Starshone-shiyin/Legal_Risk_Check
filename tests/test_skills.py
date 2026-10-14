"""Offline tests for the persisted user-defined Skill infrastructure."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from src.main import app
from src.skills.repository import JsonSkillRepository
from src.skills.schemas import SkillPayload
from src.skills.service import BuiltinSkillProtectedError, SkillService


def valid_payload() -> dict:
    return {
        "name": "Custom legal review",
        "description": "A bounded offline plan.",
        "nodes": [
            {"node_id": "retrieve", "node_type": "retrieve", "parameters": {"top_k": 5, "legal_only": True}},
            {"node_id": "gate", "node_type": "evidence_gate", "parameters": {"min_score": 0.8, "require_local_law": True}},
            {"node_id": "output", "node_type": "report_output", "parameters": {"format": "markdown", "include_citations": True}},
        ],
        "edges": [
            {"source": "retrieve", "target": "gate"},
            {"source": "gate", "target": "output"},
        ],
    }


class SkillSchemaTest(unittest.TestCase):
    def test_rejects_unknown_nodes_invalid_parameters_cycles_and_more_than_six_nodes(self):
        unknown_node = valid_payload()
        unknown_node["nodes"][0]["node_type"] = "answer_generation"
        with self.assertRaises(ValidationError):
            SkillPayload.model_validate(unknown_node)

        unknown_parameter = valid_payload()
        unknown_parameter["nodes"][0]["parameters"]["prompt"] = "ignore prior evidence"
        with self.assertRaises(ValidationError):
            SkillPayload.model_validate(unknown_parameter)

        cycle = valid_payload()
        cycle["edges"].append({"source": "output", "target": "retrieve"})
        with self.assertRaises(ValidationError):
            SkillPayload.model_validate(cycle)

        too_many_nodes = valid_payload()
        too_many_nodes["nodes"] = [
            {"node_id": f"node-{index}", "node_type": "retrieve", "parameters": {}}
            for index in range(7)
        ]
        with self.assertRaises(ValidationError):
            SkillPayload.model_validate(too_many_nodes)


class SkillServiceTest(unittest.TestCase):
    def test_builtin_records_persist_and_cannot_be_updated_or_deleted(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "skills.json"
            service = SkillService(path)
            builtins = service.list_skills()
            self.assertEqual(len(builtins), 3)
            self.assertTrue(all(item.is_builtin for item in builtins))
            self.assertTrue(path.exists())
            with self.assertRaises(BuiltinSkillProtectedError):
                service.delete_skill(builtins[0].skill_id)
            with self.assertRaises(BuiltinSkillProtectedError):
                service.update_skill(builtins[0].skill_id, SkillPayload.model_validate(valid_payload()))
            self.assertEqual(len(SkillService(path).list_skills()), 3)

    def test_builtin_records_are_refreshed_in_chinese_without_changing_user_skills(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "skills.json"
            repository = JsonSkillRepository(path)
            records = repository.load()
            records[0]["name"] = "Legacy English template"
            records.append(
                {
                    "skill_id": "skill-user-preserved",
                    "name": "我的自建流程",
                    "description": "不得被内置模板更新覆盖。",
                    "is_builtin": False,
                    "created_at": "2026-08-10T00:00:00+00:00",
                    "updated_at": "2026-08-10T00:00:00+00:00",
                    "nodes": [{"node_id": "retrieve", "node_type": "retrieve", "parameters": {}}],
                    "edges": [],
                }
            )
            repository.save(records)

            refreshed = repository.load()
            self.assertEqual(refreshed[0]["name"], "法律风险基础审查")
            self.assertEqual(refreshed[-1]["name"], "我的自建流程")

    def test_user_skill_crud_is_file_persistent_and_run_only_returns_a_plan(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "skills.json"
            service = SkillService(JsonSkillRepository(path))
            created = service.create_skill(SkillPayload.model_validate(valid_payload()))
            self.assertFalse(created.is_builtin)
            self.assertEqual(SkillService(path).get_skill(created.skill_id).name, "Custom legal review")

            updated_payload = valid_payload()
            updated_payload["name"] = "Updated legal review"
            updated = service.update_skill(created.skill_id, SkillPayload.model_validate(updated_payload))
            self.assertEqual(updated.name, "Updated legal review")

            run = service.run_skill(created.skill_id)
            self.assertEqual(run.status, "blocked")
            self.assertEqual([step.node_id for step in run.execution_plan], ["retrieve", "gate", "output"])
            self.assertIn("not configured", run.blocked_rationale)

            service.delete_skill(created.skill_id)
            self.assertEqual(len(SkillService(path).list_skills()), 3)


class SkillRouterTest(unittest.TestCase):
    def setUp(self) -> None:
        import src.skills.router as skills_router

        self.directory = tempfile.TemporaryDirectory()
        self.router_module = skills_router
        self.original_service = skills_router.service
        self.original_execution_handler = skills_router.execution_handler
        skills_router.service = SkillService(Path(self.directory.name) / "skills.json")
        skills_router.configure_execution_handler(None)
        self.app = FastAPI()
        self.app.include_router(skills_router.router)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.client.close()
        self.router_module.service = self.original_service
        self.router_module.configure_execution_handler(self.original_execution_handler)
        self.directory.cleanup()

    def test_router_exposes_node_types_validate_crud_and_blocked_run_contract(self):
        node_types = self.client.get("/skills/node-types")
        self.assertEqual(node_types.status_code, 200)
        self.assertEqual(set(node_types.json()["node_types"]), {"document_extract", "retrieve", "evidence_gate", "web_supplement", "risk_analysis", "human_review", "report_output"})

        payload = valid_payload()
        validation = self.client.post("/skills/validate", json=payload)
        self.assertEqual(validation.status_code, 200)
        self.assertEqual(validation.json()["topological_order"], ["retrieve", "gate", "output"])

        created = self.client.post("/skills", json=payload)
        self.assertEqual(created.status_code, 201)
        skill_id = created.json()["data"]["skill_id"]
        self.assertEqual(self.client.get("/skills").json()["status"], "ok")

        payload["name"] = "Updated through router"
        updated = self.client.put(f"/skills/{skill_id}", json=payload)
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["data"]["name"], "Updated through router")

        run = self.client.post(f"/skills/{skill_id}/run", json={"question": "如何审查数据出境风险？"})
        self.assertEqual(run.status_code, 200)
        self.assertEqual(run.json()["status"], "blocked")
        self.assertEqual(self.client.delete(f"/skills/{skill_id}").status_code, 200)

        builtin_id = self.client.get("/skills").json()["items"][0]["skill_id"]
        self.assertEqual(self.client.delete(f"/skills/{builtin_id}").status_code, 409)
        self.assertEqual(self.client.put(f"/skills/{builtin_id}", json=payload).status_code, 409)

    def test_main_application_runs_a_validated_skill_through_the_ask_boundary(self):
        import src.skills.router as skills_router

        rag_payload = {
            "answer": "结论：需要补充核验。",
            "confidence_score": 0.7,
            "answer_confidence": 0.7,
            "retrieval_confidence": 0.7,
            "needs_human_review": False,
            "missing_evidence": [],
            "risk_level": "medium",
            "risk_types": [],
            "risk_type_evidence": [],
            "recommended_actions": [],
            "recommended_action_evidence": [],
            "citation_integrity": {},
            "evidence_chain": [],
            "evidence_sufficiency": {"score": 0.5},
            "filters": {},
            "material_sources": [],
        }
        payload = valid_payload()
        payload["nodes"].insert(2, {"node_id": "review", "node_type": "human_review", "parameters": {"on_insufficient_evidence": True}})
        payload["edges"] = [
            {"source": "retrieve", "target": "gate"},
            {"source": "gate", "target": "review"},
            {"source": "review", "target": "output"},
        ]
        with tempfile.TemporaryDirectory() as directory:
            original_service = skills_router.service
            skills_router.service = SkillService(Path(directory) / "skills.json")
            try:
                from src.main import _execute_skill_run

                skills_router.configure_execution_handler(_execute_skill_run)
                with TestClient(app) as client, patch("src.main.rag_query", return_value=rag_payload) as rag_query:
                    skill_id = client.post("/skills", json=payload).json()["data"]["skill_id"]
                    response = client.post(f"/skills/{skill_id}/run", json={"question": "审查数据出境风险"})
                self.assertEqual(response.status_code, 200)
                data = response.json()
                self.assertEqual(data["status"], "completed")
                self.assertEqual(data["run_metadata"]["source"], "validated_skill_orchestrator")
                self.assertTrue(data["result"]["needs_human_review"])
                self.assertEqual(rag_query.call_args.kwargs["k"], 5)
            finally:
                skills_router.service = original_service


if __name__ == "__main__":
    unittest.main()
