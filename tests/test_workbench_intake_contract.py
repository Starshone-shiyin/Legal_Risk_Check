import unittest

from tools.build_workbench_intake_contract import (
    IMPORTABLE_REVIEWER_FIELDS,
    READ_ONLY_CONTEXT_FIELDS,
    build_report,
)


class WorkbenchIntakeContractTest(unittest.TestCase):
    def test_contract_separates_importable_and_read_only_fields(self):
        report = build_report()
        contract = report["contract"]

        self.assertEqual(report["version"], "0.4.7.7.0")
        self.assertIn("case_id", contract["field_policy"]["read_only_context_fields"])
        self.assertIn("decision", contract["field_policy"]["importable_reviewer_fields"])
        self.assertNotIn("decision", READ_ONLY_CONTEXT_FIELDS)
        self.assertNotIn("case_id", IMPORTABLE_REVIEWER_FIELDS)

    def test_contract_disallows_overwrite_and_main_flow_mutation(self):
        write_policy = build_report()["contract"]["write_policy"]

        self.assertEqual(write_policy["overwrite_original_decision_schema"], "disallowed")
        self.assertEqual(write_policy["main_flow_mutation"], "disallowed")
        self.assertEqual(write_policy["eval_case_mutation"], "disallowed")


if __name__ == "__main__":
    unittest.main()
