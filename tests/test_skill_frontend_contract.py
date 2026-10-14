import unittest
from pathlib import Path


class SkillFrontendContractTest(unittest.TestCase):
    def setUp(self):
        self.html = Path("web/website.html").read_text(encoding="utf-8")
        self.script = Path("web/app.js").read_text(encoding="utf-8")

    def test_skill_workbench_is_exposed_through_navigation_and_editor(self):
        self.assertIn('data-tab="skills"', self.html)
        self.assertIn('id="view-skills"', self.html)
        self.assertIn('id="skill-editor-dialog"', self.html)
        self.assertIn('id="skills-detail"', self.html)
        self.assertIn('id="skill-run-form"', self.script)

    def test_skill_frontend_uses_the_public_api_and_current_node_contract(self):
        for endpoint in ("/skills", "/skills/node-types", "/skills/validate", "/run"):
            self.assertIn(endpoint, self.script)
        for field in ("node_id", "node_type", "parameters"):
            self.assertIn(field, self.script)
        self.assertIn("const MAX_SKILL_NODES = 6", self.script)
        self.assertIn('method: skillState.editingId ? "PATCH" : "POST"', self.script)
        self.assertNotIn('"skill_input", "legal_retrieval", "evidence_sufficiency_gate", "answer_generation", "skill_output"', self.script)


if __name__ == "__main__":
    unittest.main()
