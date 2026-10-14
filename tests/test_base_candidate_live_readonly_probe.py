import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from langchain_core.documents import Document

from tools.build_base_candidate_live_readonly_probe import (
    build_report,
    write_json,
)


def point(source="Law A", article_no=1, category="demo"):
    class FakePoint:
        id = "point-1"
        payload = {
            "page_content": "sample content",
            "metadata": {
                "source": source,
                "law_name": source,
                "article_no": article_no,
                "type": "article",
                "category": category,
                "chunk_id": f"{source}-{article_no}",
                "citation": f"{source}::{article_no}",
            },
        }

    return FakePoint()


def doc(source="Law A", article_no=1, category="demo"):
    return Document(
        page_content="sample content",
        metadata={
            "source": source,
            "law_name": source,
            "article_no": article_no,
            "type": "article",
            "category": category,
            "chunk_id": f"{source}-{article_no}",
            "citation": f"{source}::{article_no}",
        },
    )


class FakeCount:
    count = 10


class FakeClient:
    def __init__(self, *, payload_points=None, filtered_points=None):
        self.payload_points = payload_points if payload_points is not None else [point()]
        self.filtered_points = filtered_points if filtered_points is not None else [point()]
        self.calls = []

    def get_collection(self, collection_name):
        self.calls.append(("get_collection", collection_name))
        return object()

    def count(self, collection_name, exact=False):
        self.calls.append(("count", collection_name, exact))
        return FakeCount()

    def scroll(self, collection_name, scroll_filter, limit, with_payload, with_vectors):
        self.calls.append(("scroll", collection_name, limit, with_payload, with_vectors))
        must = getattr(scroll_filter, "must", []) or []
        has_category = any(getattr(condition, "key", "") == "metadata.category" for condition in must)
        return (self.filtered_points if has_category else self.payload_points), None

    def upsert(self, *args, **kwargs):
        raise AssertionError("probe must not write qdrant")

    def delete(self, *args, **kwargs):
        raise AssertionError("probe must not delete qdrant")


def write_inputs(tmp: Path):
    mismatch = tmp / "mismatch.json"
    trace = tmp / "trace.json"
    write_json(
        mismatch,
        {
            "case_rows": [
                {
                    "id": "case-1",
                    "missing_final_refs_from_union": [
                        {"source": "Law A", "article_no": 1, "section_no": "", "citation": "Law A::1"}
                    ],
                }
            ]
        },
    )
    write_json(
        trace,
        {
            "reports": [
                {
                    "id": "case-1",
                    "question": "question",
                    "debug_info": {
                        "filters": {
                            "doc_type": "article",
                            "category": "demo",
                            "score_threshold": None,
                        }
                    },
                }
            ]
        },
    )
    return mismatch, trace


class BaseCandidateLiveReadonlyProbeTest(unittest.TestCase):
    def test_payload_absence_is_attributed_without_dense_probe(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mismatch, trace = write_inputs(Path(tmpdir))
            client = FakeClient(payload_points=[], filtered_points=[])

            with patch("tools.build_base_candidate_live_readonly_probe.get_qdrant_client", return_value=client), \
                patch("tools.build_base_candidate_live_readonly_probe.retrieve_with_sparse", return_value=[]), \
                patch("tools.build_base_candidate_live_readonly_probe.get_vectorstore") as vectorstore:
                report = build_report(mismatch_path=mismatch, trace_path=trace)

        self.assertEqual(report["summary"]["status"], "completed_requires_dense_probe")
        self.assertEqual(report["ref_rows"][0]["attribution"], "absent_from_qdrant_payload")
        vectorstore.assert_not_called()
        self.assertFalse(report["summary"]["dense_probe_enabled"])

    def test_metadata_filter_exclusion_is_attributed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mismatch, trace = write_inputs(Path(tmpdir))
            client = FakeClient(payload_points=[point()], filtered_points=[])

            with patch("tools.build_base_candidate_live_readonly_probe.get_qdrant_client", return_value=client), \
                patch("tools.build_base_candidate_live_readonly_probe.retrieve_with_sparse", return_value=[]):
                report = build_report(mismatch_path=mismatch, trace_path=trace)

        row = report["ref_rows"][0]
        self.assertEqual(row["qdrant_payload"]["found_count"], 1)
        self.assertEqual(row["runtime_filter_probe"]["found_count"], 0)
        self.assertEqual(row["attribution"], "metadata_filter_exclusion")

    def test_sparse_high_k_presence_without_runtime_k_points_to_rank_cutoff(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mismatch, trace = write_inputs(Path(tmpdir))
            client = FakeClient(payload_points=[point()], filtered_points=[point()])

            def fake_sparse(_question, collection_name, k, filters):
                if k == 10:
                    return []
                return [(doc(), 0.5)]

            with patch("tools.build_base_candidate_live_readonly_probe.get_qdrant_client", return_value=client), \
                patch("tools.build_base_candidate_live_readonly_probe.retrieve_with_sparse", side_effect=fake_sparse):
                report = build_report(mismatch_path=mismatch, trace_path=trace)

        row = report["ref_rows"][0]
        self.assertTrue(row["sparse_probe"]["high_k"]["present"])
        self.assertEqual(row["attribution"], "sparse_rank_cutoff_loss")


if __name__ == "__main__":
    unittest.main()
