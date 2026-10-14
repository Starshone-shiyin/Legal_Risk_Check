import unittest

from tools.check_qdrant_index_integrity import build_report


class QdrantIndexIntegrityTest(unittest.TestCase):
    def test_build_report_flags_count_mismatch(self):
        def fake_scan(_collection_name):
            return {
                "total_scanned": 1,
                "empty_payload": 0,
                "missing_metadata": 0,
                "missing_source": 0,
                "missing_chunk_id": 0,
                "missing_qdrant_point_id": 0,
                "missing_bm25_vector": 0,
                "unindexable_bm25_chunks": 0,
                "duplicate_chunk_id_count": 0,
                "source_counts": {"Law A": 1},
                "sample_failures": [],
                "sample_warnings": [],
            }

        def fake_expected(_manifest_path):
            return {"Law A": 2}

        import tools.check_qdrant_index_integrity as module

        original_scan = module.scan_collection
        original_expected = module.expected_counts_from_manifest
        try:
            module.scan_collection = fake_scan
            module.expected_counts_from_manifest = fake_expected

            report = build_report("legal_knowledge", "manifest.json")
        finally:
            module.scan_collection = original_scan
            module.expected_counts_from_manifest = original_expected

        self.assertFalse(report["passed"])
        self.assertEqual(report["count_mismatches"]["Law A"], {"expected": 2, "actual": 1})

    def test_build_report_flags_missing_bm25_vector(self):
        def fake_scan(_collection_name):
            return {
                "total_scanned": 1,
                "empty_payload": 0,
                "missing_metadata": 0,
                "missing_source": 0,
                "missing_chunk_id": 0,
                "missing_qdrant_point_id": 0,
                "missing_bm25_vector": 1,
                "unindexable_bm25_chunks": 0,
                "duplicate_chunk_id_count": 0,
                "source_counts": {"Law A": 1},
                "sample_failures": [],
                "sample_warnings": [],
            }

        import tools.check_qdrant_index_integrity as module

        original_scan = module.scan_collection
        original_expected = module.expected_counts_from_manifest
        try:
            module.scan_collection = fake_scan
            module.expected_counts_from_manifest = lambda _manifest_path: {"Law A": 1}

            report = build_report("legal_knowledge", "manifest.json")
        finally:
            module.scan_collection = original_scan
            module.expected_counts_from_manifest = original_expected

        self.assertFalse(report["passed"])
        self.assertIn("missing_bm25_vector: 1", report["failures"])


if __name__ == "__main__":
    unittest.main()
