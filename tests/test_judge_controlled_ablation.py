import unittest

from tools.judge_controlled_ablation import CONTROLLED_PROFILES, SWITCHES, judge


def make_definition(index: int) -> dict:
    definition = {key: False for key in SWITCHES}
    for key in SWITCHES[:index]:
        definition[key] = True
    return definition


def make_report() -> dict:
    summary = {
        "case_count": 2,
        "evidence_recall_at_k": 0.5,
        "mrr_at_k": 0.5,
        "ndcg_at_k": 0.5,
        "multi_source_coverage": 0.5,
        "retrieval_time_p50_ms": 1.0,
        "retrieval_time_p95_ms": 2.0,
    }
    return {
        "status": "completed",
        "case_file_sha256": "frozen",
        "collection_name": "legal_knowledge_test",
        "case_count": 2,
        "profiles": {
            name: {"definition": make_definition(index), "summary": dict(summary), "cases": [{}, {}]}
            for index, name in enumerate(CONTROLLED_PROFILES)
        },
    }


class ControlledAblationJudgeTest(unittest.TestCase):
    def test_accepts_single_variable_chain(self):
        result = judge(make_report())
        self.assertEqual(result["verdict"], "accepted")
        self.assertTrue(result["checks"]["single_variable_transitions"])

    def test_rejects_multi_variable_transition(self):
        report = make_report()
        report["profiles"]["C2_query_expansion"]["definition"]["enable_concept_anchors"] = True
        result = judge(report)
        self.assertEqual(result["verdict"], "needs_revision")
        self.assertFalse(result["checks"]["single_variable_transitions"])


if __name__ == "__main__":
    unittest.main()
