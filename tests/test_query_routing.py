from __future__ import annotations

import unittest

from src.rag.query_routing import decide_ask_route


class QueryRoutingTest(unittest.TestCase):
    def test_broad_current_risk_question_uses_external_observation_route(self) -> None:
        route = decide_ask_route("最近有没有需要注意的风险事项")
        self.assertEqual(route.name, "recent_risk_observation")

    def test_current_legal_question_keeps_legal_rag_and_web_supplement(self) -> None:
        route = decide_ask_route("最近个人信息保护法的合规要求有什么变化？")
        self.assertEqual(route.name, "legal_rag_with_web")

    def test_uploaded_materials_keep_case_question_on_legal_rag_path(self) -> None:
        route = decide_ask_route("最近有没有需要注意的风险事项", has_uploaded_materials=True)
        self.assertEqual(route.name, "legal_rag")

    def test_ordinary_conversation_bypasses_legal_rag(self) -> None:
        route = decide_ask_route("帮我把这段话写得更礼貌一些")
        self.assertEqual(route.name, "general_chat")

    def test_configured_legal_concept_stays_on_rag(self) -> None:
        route = decide_ask_route("什么是附随义务？")
        self.assertEqual(route.name, "legal_rag")

    def test_business_risk_decision_stays_on_evidence_path(self) -> None:
        route = decide_ask_route("半导体上游企业面临铜价上涨，是否应调整采购与套保策略？")
        self.assertEqual(route.name, "legal_rag")
        self.assertEqual(route.reason, "business_risk_decision_requires_evidence")

    def test_employee_customer_list_question_stays_on_evidence_path(self) -> None:
        route = decide_ask_route("员工离职后私自导出客户名单，企业应如何处置？")
        self.assertEqual(route.name, "legal_rag")


if __name__ == "__main__":
    unittest.main()
