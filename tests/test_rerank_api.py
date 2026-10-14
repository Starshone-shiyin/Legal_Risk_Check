import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from src.rag.retriever import _call_siliconflow_rerank


class RerankApiTest(unittest.TestCase):
    def test_scores_are_mapped_back_by_result_index(self):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "results": [
                {"index": 2, "relevance_score": 0.91},
                {"index": 0, "relevance_score": 0.42},
                {"index": 1, "relevance_score": 0.13},
            ]
        }

        settings = SimpleNamespace(
            siliconflow_base_url="https://example.test",
            siliconflow_api_key="test-key",
        )
        with patch("src.config.get_settings", return_value=settings), patch("requests.post", return_value=response):
            scores = _call_siliconflow_rerank("query", ["a", "b", "c"])

        self.assertEqual(scores, [0.42, 0.13, 0.91])


if __name__ == "__main__":
    unittest.main()
