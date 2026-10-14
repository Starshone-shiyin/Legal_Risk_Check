import unittest

from tools.build_skill_acceptance_evidence import build_evidence
from tools.judge_skill_module import judge_payloads


class SkillAcceptanceEvidenceTest(unittest.TestCase):
    def test_offline_implementation_evidence_is_accepted(self):
        skill_api, runtime = build_evidence()
        report = judge_payloads(skill_api, runtime)

        self.assertEqual(report["verdict"], "accepted")
        self.assertEqual(runtime["node_type_count"], 7)


if __name__ == "__main__":
    unittest.main()
