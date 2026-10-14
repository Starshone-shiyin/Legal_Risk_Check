import json
import unittest
from collections import Counter
from pathlib import Path

from tools.summarize_robustness_perturbations import REQUIRED_TYPES


class RobustnessPerturbationCaseTest(unittest.TestCase):
    def test_paired_robustness_set_has_three_balanced_perturbations(self):
        path = Path("tests/rag_robustness_perturbation_cases_20260815.json")
        payload = json.loads(path.read_text(encoding="utf-8"))
        cases = payload["cases"]
        type_counts = Counter(case["metadata"]["perturbation_type"] for case in cases)

        self.assertEqual(len(cases), 24)
        self.assertEqual(set(type_counts), set(REQUIRED_TYPES))
        self.assertTrue(all(type_counts[item] == 8 for item in REQUIRED_TYPES))
        self.assertTrue(all(case["expected_evidence"] for case in cases))
        self.assertTrue(all(case["metadata"].get("reference_case_id") for case in cases))


if __name__ == "__main__":
    unittest.main()
