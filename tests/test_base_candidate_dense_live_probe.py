import unittest
from pathlib import Path
from unittest.mock import patch

from tools.build_base_candidate_dense_live_probe import VERSION, build_dense_report


class BaseCandidateDenseLiveProbeTest(unittest.TestCase):
    def test_build_dense_report_forces_dense_probe_and_version(self):
        captured = {}

        def fake_build_report(**kwargs):
            captured.update(kwargs)
            return {
                "version": "0.4.15.19",
                "schema_kind": "base_candidate_live_readonly_probe",
                "scope": "old",
                "guardrails": {},
                "collection_probe": {"reachable": True},
                "summary": {
                    "status": "completed_with_dense_probe",
                    "missing_ref_count": 1,
                    "attribution_counts": {"dense_rank_cutoff_loss": 1},
                    "dense_probe_enabled": False,
                },
            }

        with patch("tools.build_base_candidate_dense_live_probe.build_live_readonly_report", side_effect=fake_build_report):
            report = build_dense_report(
                mismatch_path=Path("mismatch.json"),
                trace_path=Path("trace.json"),
                collection_name="legal_knowledge",
            )

        self.assertTrue(captured["enable_dense_probe"])
        self.assertEqual(report["version"], VERSION)
        self.assertEqual(report["schema_kind"], "base_candidate_dense_live_probe")
        self.assertTrue(report["summary"]["dense_probe_enabled"])
        self.assertEqual(report["guardrails"]["dense_probe"], "explicit_opt_in_embedding_service_call")


if __name__ == "__main__":
    unittest.main()
