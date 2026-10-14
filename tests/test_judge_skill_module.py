import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.judge_skill_module import judge_payloads, main


def valid_skill_api():
    return {
        "schema_version": "skill-api-v1",
        "nodes": [
            {"node_id": "retrieve", "node_type": "retrieve", "parameters": {"top_k": 5}},
            {"node_id": "gate", "node_type": "evidence_gate", "parameters": {"min_score": 0.78}},
            {"node_id": "review", "node_type": "human_review", "parameters": {"on_insufficient_evidence": True}},
            {"node_id": "output", "node_type": "report_output", "parameters": {"format": "markdown"}},
        ],
        "edges": [
            {"source": "retrieve", "target": "gate"},
            {"source": "gate", "target": "review"},
            {"source": "review", "target": "output"},
        ],
        "crud": {
            "list": {"method": "GET", "path": "/skills"},
            "create": {"method": "POST", "path": "/skills"},
            "get": {"method": "GET", "path": "/skills/{skill_id}"},
            "update": {"method": "PATCH", "path": "/skills/{skill_id}"},
            "delete": {"method": "DELETE", "path": "/skills/{skill_id}"},
        },
        "builtin_examples": [{"skill_id": "builtin-legal-baseline", "is_builtin": True}],
        "frontend_boundary": {
            "allowed_operations": ["list", "create", "get", "update", "delete", "run", "read_run"],
            "forbidden_operations": ["execute_node", "direct_model_call", "direct_vectorstore_access", "write_builtin_example"],
            "no_direct_provider_access": True,
        },
    }


def valid_runtime(skill_api):
    node_ids = [node["node_id"] for node in skill_api["nodes"]]
    return {
        "schema_version": "skill-runtime-validation-v1",
        "status": "passed",
        "config_validation": {"status": "passed", "invalid_configs_rejected": True},
        "crud_validation": {"status": "passed", "operations": {operation: True for operation in skill_api["crud"]}},
        "builtin_example_protection": {"status": "passed", "protected_example_ids": ["builtin-legal-baseline"]},
        "frontend_boundary_validation": {"status": "passed", "no_direct_provider_access": True},
        "run_plan": {"node_ids": node_ids, "execution_order": node_ids, "edges": skill_api["edges"]},
    }


class JudgeSkillModuleTest(unittest.TestCase):
    def test_accepts_minimal_fixed_node_fixture(self):
        skill_api = valid_skill_api()
        report = judge_payloads(skill_api, valid_runtime(skill_api))

        self.assertEqual(report["verdict"], "accepted")
        self.assertEqual(report["summary"]["failed_checks"], [])

    def test_rejects_cycle_unknown_node_and_unprotected_example(self):
        skill_api = valid_skill_api()
        skill_api["nodes"].append({"node_id": "unsafe", "node_type": "arbitrary_python", "parameters": {}})
        skill_api["edges"].extend([
            {"source": "output", "target": "retrieve"},
            {"source": "review", "target": "unsafe"},
        ])
        skill_api["builtin_examples"][0]["is_builtin"] = False
        runtime = valid_runtime(skill_api)
        report = judge_payloads(skill_api, runtime)

        self.assertEqual(report["verdict"], "needs_revision")
        self.assertFalse(report["checks"]["node_whitelist"]["passed"])
        self.assertFalse(report["checks"]["acyclic_graph"]["passed"])
        self.assertFalse(report["checks"]["builtin_example_protection"]["passed"])

    def test_cli_writes_a_json_report_from_fixture_files(self):
        skill_api = valid_skill_api()
        runtime = valid_runtime(skill_api)
        with tempfile.TemporaryDirectory() as tmpdir:
            directory = Path(tmpdir)
            api_path = directory / "skill_api.json"
            runtime_path = directory / "runtime.json"
            output_path = directory / "judge.json"
            api_path.write_text(json.dumps(skill_api), encoding="utf-8")
            runtime_path.write_text(json.dumps(runtime), encoding="utf-8")

            with mock.patch("sys.argv", ["judge_skill_module", "--skill-api", str(api_path), "--runtime", str(runtime_path), "--output", str(output_path)]):
                self.assertEqual(main(), 0)

            saved = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(saved["verdict"], "accepted")


if __name__ == "__main__":
    unittest.main()
