from __future__ import annotations

import unittest
from unittest.mock import patch

from src.main import AskRequest, _run_ask_request


class GeneralChatRouteTest(unittest.TestCase):
    def test_ordinary_chat_does_not_call_rag(self) -> None:
        chat_payload = {
            "answer": "当然可以。",
            "confidence_score": None,
            "answer_confidence": None,
            "retrieval_confidence": None,
            "needs_human_review": False,
            "missing_evidence": [],
            "risk_level": None,
            "risk_types": [],
            "risk_type_evidence": [],
            "recommended_actions": [],
            "recommended_action_evidence": [],
            "citation_integrity": {},
            "evidence_chain": [],
            "evidence_sufficiency": {},
            "material_sources": [],
            "filters": {"answer_status": "general_chat"},
            "debug_info": {},
        }
        with patch("src.main.rag_query") as rag_mock:
            with patch("src.main.answer_general_chat", return_value=chat_payload) as chat_mock:
                result = _run_ask_request(AskRequest(question="帮我写得更礼貌一些"))

        rag_mock.assert_not_called()
        chat_mock.assert_called_once()
        self.assertEqual(result["filters"]["answer_status"], "general_chat")


if __name__ == "__main__":
    unittest.main()
