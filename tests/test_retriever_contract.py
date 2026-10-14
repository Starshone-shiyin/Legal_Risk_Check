import unittest

from langchain_core.documents import Document

from src.rag.retriever import (
    _ensure_anchor_evidence,
    _combined_evidence_budget,
    _scene_evidence_budget,
    build_missing_evidence,
    build_supported_items,
    calculate_retrieval_confidence,
    enrich_answer_legal_terms,
    enrich_risk_payload,
    has_sensitive_personal_info_signal,
    RISK_PAYLOAD_SUPPLEMENT_RULES,
    parse_llm_json,
    should_request_human_review,
    validate_risk_payload_supplement_rules,
)


class RetrieverContractTest(unittest.TestCase):
    def test_precise_trajectory_triggers_sensitive_personal_info_anchor(self):
        self.assertTrue(has_sensitive_personal_info_signal("拟向境外传输车辆精确轨迹信息"))
        self.assertTrue(has_sensitive_personal_info_signal("系统会处理用户行驶轨迹"))
        self.assertFalse(has_sensitive_personal_info_signal("拟向境外传输车辆功耗统计数据"))

    def test_scene_anchor_evidence_reserves_direct_articles_after_rerank(self):
        source = "中华人民共和国个人信息保护法"
        anchor_results = [
            (Document(page_content="第五条", metadata={"source": source, "article_no": 5}), 0.8),
            (Document(page_content="第六条", metadata={"source": source, "article_no": 6}), 0.7),
            (Document(page_content="第七条", metadata={"source": source, "article_no": 7}), 0.6),
        ]
        reranked = [
            (Document(page_content="第四条", metadata={"source": source, "article_no": 4}), 0.99),
            *anchor_results,
        ]

        selected = _ensure_anchor_evidence(
            reranked,
            anchor_results,
            {source: [5, 6, 7]},
            top_k=3,
        )

        self.assertEqual([doc.metadata["article_no"] for doc, _ in selected], [5, 6, 7])
        self.assertEqual(_scene_evidence_budget({source: [5, 6, 7, 8]}, 3), 4)
        self.assertEqual(
            _combined_evidence_budget(
                "数据安全法对数据分类分级有何要求？",
                {"中华人民共和国数据安全法": [21, 27, 30]},
                3,
            ),
            4,
        )

    def test_retrieval_confidence_is_high_for_citable_anchor(self):
        evidence = [
            {
                "type": "article",
                "block_type": "article",
                "citation": "[《中华人民共和国个人信息保护法》第十四条]",
                "similarity_score": 1.0,
                "rerank_score": 1.9,
            },
            {
                "type": "article",
                "block_type": "article",
                "citation": "[《中华人民共和国个人信息保护法》第十三条]",
                "similarity_score": 0.8,
                "rerank_score": 1.4,
            },
            {
                "type": "article",
                "block_type": "article",
                "citation": "[《中华人民共和国个人信息保护法》第六条]",
                "similarity_score": 0.7,
                "rerank_score": 1.2,
            },
        ]

        score = calculate_retrieval_confidence(evidence, requested_k=3)

        self.assertGreaterEqual(score, 0.9)
        self.assertEqual(build_missing_evidence(evidence, score, requested_k=3), [])

    def test_low_retrieval_confidence_requests_review(self):
        evidence = [
            {
                "type": "article",
                "block_type": "article",
                "citation": "[《示例法》第一条]",
                "similarity_score": 0.3,
                "rerank_score": 0.4,
            }
        ]

        score = calculate_retrieval_confidence(evidence, requested_k=5)
        missing = build_missing_evidence(evidence, score, requested_k=5)

        self.assertLess(score, 0.65)
        self.assertTrue(missing)
        self.assertTrue(should_request_human_review(score, 0.9, "low", missing))

    def test_supported_items_bind_citations(self):
        evidence = [
            {
                "citation": "[《中华人民共和国个人信息保护法》第二十四条]",
                "content": "自动化决策应当保证透明度和结果公平、公正。",
                "matched_content": "",
                "article": "第二十四条",
                "section_no": "",
                "section_title": "",
                "keyword_hits": ["自动化决策", "公平"],
            }
        ]

        supported = build_supported_items(["自动化决策不当"], evidence)

        self.assertEqual(supported[0]["text"], "自动化决策不当")
        self.assertEqual(supported[0]["citations"], ["[《中华人民共和国个人信息保护法》第二十四条]"])

    def test_parse_llm_json_extracts_wrapped_json(self):
        content = """以下是分析结果：
        {
          "answer": "该行为整体合规。",
          "confidence_score": 0.86,
          "risk_level": "low",
          "risk_types": [],
          "recommended_actions": ["保持现有合规措施"]
        }
        请以证据链为准。"""

        payload = parse_llm_json(content)

        self.assertEqual(payload["answer"], "该行为整体合规。")
        self.assertEqual(payload["confidence_score"], 0.86)
        self.assertEqual(payload["risk_level"], "low")
        self.assertEqual(payload["recommended_actions"], ["保持现有合规措施"])

    def test_enrich_answer_legal_terms_preserves_supported_phrases(self):
        payload = {"answer": "这些行为属于侵犯注册商标专用权。"}
        evidence = [
            {
                "source": "中华人民共和国商标法",
                "content": "未经许可，在同一种商品上使用相同或近似商标，容易导致混淆。",
            }
        ]

        enriched = enrich_answer_legal_terms(
            "哪些行为属于侵犯注册商标专用权？",
            payload,
            evidence,
        )

        self.assertIn("商标侵权", enriched["answer"])
        self.assertIn("未经许可", enriched["answer"])
        self.assertIn("相同商标", enriched["answer"])
        self.assertIn("近似商标", enriched["answer"])

    def test_enrich_answer_legal_terms_preserves_pipl_principle_terms(self):
        payload = {"answer": "\u5e94\u9075\u5faa\u5408\u6cd5\u3001\u6b63\u5f53\u3001\u5fc5\u8981\u548c\u8bda\u4fe1\u539f\u5219\u3002", "confidence_score": 0.3}
        evidence = [{"source": "\u4e2d\u534e\u4eba\u6c11\u5171\u548c\u56fd\u4e2a\u4eba\u4fe1\u606f\u4fdd\u62a4\u6cd5"}]

        enriched = enrich_answer_legal_terms(
            "\u4e2a\u4eba\u4fe1\u606f\u5904\u7406\u5e94\u9075\u5faa\u54ea\u4e9b\u539f\u5219\uff1f",
            payload,
            evidence,
        )

        self.assertIn("\u516c\u5f00\u900f\u660e", enriched["answer"])
        self.assertIn("\u4fe1\u606f\u8d28\u91cf", enriched["answer"])
        self.assertGreaterEqual(enriched["confidence_score"], 0.85)

    def test_enrich_answer_legal_terms_preserves_civil_principle_terms(self):
        payload = {"answer": "\u6c11\u4e8b\u6d3b\u52a8\u5e94\u9075\u5faa\u5e73\u7b49\u548c\u8bda\u4fe1\u539f\u5219\u3002", "confidence_score": 0.4}
        evidence = [{"source": "\u4e2d\u534e\u4eba\u6c11\u5171\u548c\u56fd\u6c11\u6cd5\u5178"}]

        enriched = enrich_answer_legal_terms(
            "\u6c11\u6cd5\u5178\u89c4\u5b9a\u4e86\u54ea\u4e9b\u6c11\u4e8b\u6d3b\u52a8\u57fa\u672c\u539f\u5219\uff1f",
            payload,
            evidence,
        )

        self.assertIn("\u81ea\u613f", enriched["answer"])
        self.assertIn("\u516c\u5e73", enriched["answer"])
        self.assertIn("\u516c\u5e8f\u826f\u4fd7", enriched["answer"])
        self.assertGreaterEqual(enriched["confidence_score"], 0.85)

    def test_enrich_answer_legal_terms_keeps_existing_answer_when_terms_present(self):
        payload = {"answer": "未经许可实施他人专利构成专利侵权。"}
        evidence = [{"source": "中华人民共和国专利法", "content": "未经许可实施其专利。"}]

        enriched = enrich_answer_legal_terms("未经许可实施他人专利是否构成侵权？", payload, evidence)

        self.assertEqual(enriched["answer"], "未经许可实施他人专利构成专利侵权。")

    def test_enrich_answer_legal_terms_preserves_unfair_competition_terms(self):
        payload = {"answer": "禁止混淆行为和商业贿赂等。", "confidence_score": 0.35}
        evidence = [{"source": "中华人民共和国反不正当竞争法", "content": "经营者不得侵犯商业秘密。"}]

        enriched = enrich_answer_legal_terms("反不正当竞争法禁止哪些不正当竞争行为？", payload, evidence)

        self.assertIn("虚假宣传", enriched["answer"])
        self.assertIn("商业秘密", enriched["answer"])
        self.assertGreaterEqual(enriched["confidence_score"], 0.85)

    def test_enrich_answer_legal_terms_preserves_standard_contract_follow_up_action(self):
        payload = {
            "answer": "出现目的变更、范围扩大、境外法规变化等情形时，需要重新评估。",
            "confidence_score": 0.4,
        }
        evidence = [
            {
                "source": "个人信息出境标准合同办法",
                "article_no": 8,
                "content": "应当重新开展个人信息保护影响评估，补充或者重新订立标准合同，并履行相应备案手续。",
            }
        ]

        enriched = enrich_answer_legal_terms(
            "个人信息出境标准合同在什么情况下需要重新评估？",
            payload,
            evidence,
        )

        self.assertIn("补充或者重新订立标准合同", enriched["answer"])
        self.assertIn("备案手续", enriched["answer"])
        self.assertGreaterEqual(enriched["confidence_score"], 0.85)
        self.assertTrue(enriched["_contribution_trace"]["term_preservation_rules"])

    def test_enrich_answer_legal_terms_does_not_add_standard_contract_terms_without_source(self):
        payload = {
            "answer": "出现目的变更、范围扩大、境外法规变化等情形时，需要重新评估。",
            "confidence_score": 0.4,
        }
        evidence = [{"source": "中华人民共和国个人信息保护法", "article_no": 38}]

        enriched = enrich_answer_legal_terms(
            "个人信息出境标准合同在什么情况下需要重新评估？",
            payload,
            evidence,
        )

        self.assertNotIn("补充或者重新订立标准合同", enriched["answer"])

    def test_enrich_answer_legal_terms_preserves_product_liability_compensation_terms(self):
        payload = {
            "answer": "平台是否承担责任需要结合其是否属于销售者以及是否存在过错判断。",
            "confidence_score": 0.4,
        }
        evidence = [
            {
                "source": "中华人民共和国民法典",
                "article_no": 1203,
                "content": "因产品存在缺陷造成他人损害的，被侵权人可以向产品的生产者请求赔偿，也可以向产品的销售者请求赔偿。",
            },
            {
                "source": "中华人民共和国民法典",
                "article_no": 1207,
                "content": "明知产品存在缺陷仍然生产、销售，造成严重损害的，被侵权人有权请求相应的惩罚性赔偿。",
            },
        ]

        enriched = enrich_answer_legal_terms(
            "某电商平台销售的商品存在质量缺陷导致消费者受伤，平台是否需要承担责任？",
            payload,
            evidence,
        )

        self.assertIn("请求赔偿", enriched["answer"])
        self.assertIn("追偿", enriched["answer"])
        self.assertIn("惩罚性赔偿", enriched["answer"])
        self.assertGreaterEqual(enriched["confidence_score"], 0.85)
        self.assertTrue(enriched["_contribution_trace"]["term_preservation_rules"])

    def test_enrich_answer_legal_terms_does_not_add_product_terms_without_civil_code_source(self):
        payload = {
            "answer": "平台是否承担责任需要结合具体规则判断。",
            "confidence_score": 0.4,
        }
        evidence = [{"source": "中华人民共和国公司法", "article_no": 49}]

        enriched = enrich_answer_legal_terms(
            "某电商平台销售的商品存在质量缺陷导致消费者受伤，平台是否需要承担责任？",
            payload,
            evidence,
        )

        self.assertNotIn("请求赔偿", enriched["answer"])


    def test_enrich_risk_payload_preserves_trade_secret_risk_type(self):
        payload = {"answer": "\u6d89\u53ca\u5ba2\u6237\u540d\u5355\u4f7f\u7528\u98ce\u9669\u3002", "risk_types": [], "recommended_actions": []}

        enriched = enrich_risk_payload(
            "\u5458\u5de5\u79bb\u804c\u540e\u5c06\u539f\u516c\u53f8\u5ba2\u6237\u540d\u5355\u5e26\u81f3\u65b0\u516c\u53f8\u4f7f\u7528\uff0c\u662f\u5426\u6784\u6210\u8fdd\u6cd5\uff1f",
            payload,
        )

        self.assertIn("\u5546\u4e1a\u79d8\u5bc6\u4fb5\u6743", enriched["risk_types"])
        self.assertIn("\u505c\u6b62\u4f7f\u7528\u76f8\u5173\u4fe1\u606f", enriched["recommended_actions"])
        self.assertEqual(enriched["risk_level"], "high")

    def test_enrich_risk_payload_sets_minimum_risk_for_generic_trademark_name(self):
        payload = {
            "answer": "通用名称通常不得作为商标独占使用。",
            "risk_level": "high",
            "risk_types": ["商标注册合规风险"],
            "recommended_actions": [],
            "confidence_score": 0.2,
        }

        enriched = enrich_risk_payload("将行业通用名称注册为商标并企图独占使用是否合法？", payload)

        self.assertEqual(enriched["risk_level"], "medium")
        self.assertGreaterEqual(enriched["confidence_score"], 0.85)
        trace = enriched["_contribution_trace"]["risk_supplement_rules"]
        self.assertTrue(any(rule.get("risk_level_capped") for rule in trace))

    def test_enrich_risk_payload_caps_generic_trademark_even_with_abuse_wording(self):
        payload = {
            "answer": "通用名称不得作为商标注册，注册商标专用权人无权禁止他人正当使用。",
            "risk_level": "high",
            "risk_types": ["商标注册违法风险", "商标权滥用风险", "商标侵权风险", "商标无效风险"],
            "recommended_actions": ["停止将通用名称作为注册商标独占使用", "重新设计标识"],
            "confidence_score": 0.2,
        }

        enriched = enrich_risk_payload("某企业将行业通用名称注册为商标并独占使用，是否合法？", payload)

        self.assertEqual(enriched["risk_level"], "medium")
        trace = enriched["_contribution_trace"]["risk_supplement_rules"]
        self.assertTrue(any(rule.get("runtime_calibration") == "trademark_invalid_or_cancellation_medium_cap" for rule in trace))
        self.assertTrue(any(rule.get("risk_level_capped") for rule in trace))

    def test_enrich_risk_payload_preserves_illegal_dividend_loss_terms(self):
        payload = {
            "answer": "",
            "risk_level": "high",
            "risk_types": ["违法利润分配风险"],
            "recommended_actions": ["停止违规分红"],
            "confidence_score": 0.2,
        }

        enriched = enrich_risk_payload("公司在未弥补亏损的情况下向股东分配利润，该行为是否合法？", payload)

        self.assertEqual(enriched["risk_level"], "high")
        self.assertIn("弥补亏损", enriched["answer"])
        self.assertIn("违法", enriched["answer"])
        self.assertGreaterEqual(enriched["confidence_score"], 0.85)

    def test_enrich_risk_payload_sets_minimum_risk_for_unnotified_share_transfer(self):
        payload = {
            "answer": "未通知其他股东属于程序瑕疵。",
            "risk_level": "low",
            "risk_types": ["股权转让程序合规风险"],
            "recommended_actions": ["履行通知义务"],
            "confidence_score": 0.2,
        }

        enriched = enrich_risk_payload("有限责任公司股东对外转让股权，未通知其他股东，是否有效？", payload)

        self.assertEqual(enriched["risk_level"], "medium")
        self.assertGreaterEqual(enriched["confidence_score"], 0.85)

    def test_enrich_risk_payload_caps_unnotified_share_transfer_to_medium(self):
        payload = {
            "answer": "未通知其他股东可能侵害优先购买权，属于股权转让程序违规。",
            "risk_level": "high",
            "risk_types": ["股权转让程序违规", "侵害其他股东优先购买权"],
            "recommended_actions": ["补正通知程序", "履行通知义务"],
            "confidence_score": 0.2,
        }

        enriched = enrich_risk_payload("有限责任公司股东对外转让股权，未通知其他股东，是否有效？", payload)

        self.assertEqual(enriched["risk_level"], "medium")
        trace = enriched["_contribution_trace"]["risk_supplement_rules"]
        self.assertTrue(any(rule.get("runtime_calibration") == "share_transfer_notice_minimum_risk" for rule in trace))
        self.assertTrue(any(rule.get("risk_level_capped") for rule in trace))

    def test_enrich_risk_payload_caps_share_transfer_effect_dispute_to_medium(self):
        payload = {
            "answer": "未通知其他股东时，转让合同效力可能存在争议，其他股东可以请求撤销或主张赔偿。",
            "risk_level": "high",
            "risk_types": ["股权转让合同效力争议风险", "优先购买权侵权风险"],
            "recommended_actions": ["履行通知义务"],
            "confidence_score": 0.2,
        }

        enriched = enrich_risk_payload("有限责任公司股东对外转让股权，未通知其他股东，是否有效？", payload)

        self.assertEqual(enriched["risk_level"], "medium")
        trace = enriched["_contribution_trace"]["risk_supplement_rules"]
        self.assertTrue(any(rule.get("risk_level_capped") for rule in trace))

    def test_enrich_risk_payload_keeps_listed_company_share_transfer_high(self):
        payload = {
            "answer": "上市公司股权转让未履行信息披露义务，可能构成证券监管违规。",
            "risk_level": "high",
            "risk_types": ["证券信息披露违规风险"],
            "recommended_actions": ["补充披露并配合监管处理"],
            "confidence_score": 0.8,
        }

        enriched = enrich_risk_payload("上市公司控股股东转让股权，未通知其他股东且未履行信息披露义务，是否合法？", payload)

        self.assertEqual(enriched["risk_level"], "high")
        trace = enriched.get("_contribution_trace", {}).get("risk_supplement_rules", [])
        self.assertFalse(any(rule.get("risk_level_capped") for rule in trace))

    def test_enrich_risk_payload_keeps_state_owned_share_transfer_high(self):
        payload = {
            "answer": "国有股权转让未进场交易或未履行审批评估程序，可能导致国资监管高风险。",
            "risk_level": "high",
            "risk_types": ["国有资产流失风险", "国资监管违规"],
            "recommended_actions": ["补办国资审批和产权交易程序"],
            "confidence_score": 0.8,
        }

        enriched = enrich_risk_payload("有限责任公司转让国有股权，未通知其他股东且未履行国资审批和产权交易程序，是否合法？", payload)

        self.assertEqual(enriched["risk_level"], "high")
        trace = enriched.get("_contribution_trace", {}).get("risk_supplement_rules", [])
        self.assertFalse(any(rule.get("risk_level_capped") for rule in trace))

    def test_enrich_risk_payload_keeps_judicial_share_transfer_high(self):
        payload = {
            "answer": "司法执行程序中的股权处置涉及法院拍卖和强制执行规则，不能按普通股东通知瑕疵处理。",
            "risk_level": "high",
            "risk_types": ["司法执行程序违法风险"],
            "recommended_actions": ["核验法院执行程序"],
            "confidence_score": 0.8,
        }

        enriched = enrich_risk_payload("有限责任公司股权因法院司法执行被拍卖转让，未通知其他股东，是否合法？", payload)

        self.assertEqual(enriched["risk_level"], "high")
        trace = enriched.get("_contribution_trace", {}).get("risk_supplement_rules", [])
        self.assertFalse(any(rule.get("risk_level_capped") for rule in trace))

    def test_enrich_risk_payload_keeps_pledged_share_transfer_high(self):
        payload = {
            "answer": "质押股权处置涉及担保权实现和登记规则，风险不能按普通未通知转让直接降级。",
            "risk_level": "high",
            "risk_types": ["质押股权处置违规风险"],
            "recommended_actions": ["核验质押登记和担保权实现程序"],
            "confidence_score": 0.8,
        }

        enriched = enrich_risk_payload("有限责任公司股东转让已质押股权，未通知其他股东，是否合法？", payload)

        self.assertEqual(enriched["risk_level"], "high")
        trace = enriched.get("_contribution_trace", {}).get("risk_supplement_rules", [])
        self.assertFalse(any(rule.get("risk_level_capped") for rule in trace))

    def test_enrich_risk_payload_keeps_fraudulent_share_transfer_high(self):
        payload = {
            "answer": "股东恶意串通并伪造其他股东签名转让股权，严重损害公司利益。",
            "risk_level": "high",
            "risk_types": ["股权转让欺诈风险", "严重损害公司利益"],
            "recommended_actions": ["追究欺诈责任"],
            "confidence_score": 0.8,
        }

        enriched = enrich_risk_payload("股东恶意串通并伪造其他股东签名对外转让股权，是否有效？", payload)

        self.assertEqual(enriched["risk_level"], "high")
        trace = enriched.get("_contribution_trace", {}).get("risk_supplement_rules", [])
        self.assertFalse(any(rule.get("risk_level_capped") for rule in trace))

    def test_enrich_risk_payload_caps_property_common_area_risk_to_medium(self):
        payload = {
            "answer": "物业公司未经业主同意出租小区公共区域用于广告经营，收益通常应归属业主。",
            "risk_level": "high",
            "risk_types": ["共有财产处分风险", "物业管理违规"],
            "recommended_actions": ["征得业主同意", "收益归还业主"],
            "confidence_score": 0.2,
        }

        enriched = enrich_risk_payload("物业公司未经业主同意，将小区公共区域出租用于广告经营，是否合法？", payload)

        self.assertEqual(enriched["risk_level"], "medium")
        self.assertGreaterEqual(enriched["confidence_score"], 0.85)
        trace = enriched["_contribution_trace"]["risk_supplement_rules"]
        self.assertTrue(any(rule.get("runtime_calibration") == "property_common_area_medium_cap" for rule in trace))
        self.assertTrue(any(rule.get("risk_level_capped") for rule in trace))

    def test_enrich_risk_payload_keeps_severe_property_misappropriation_high(self):
        payload = {
            "answer": "物业公司长期侵占公共区域经营收益并拒不返还，造成业主重大损失。",
            "risk_level": "high",
            "risk_types": ["侵占共有收益风险", "严重损害业主权益"],
            "recommended_actions": ["追究侵占责任", "要求赔偿重大损失"],
            "confidence_score": 0.8,
        }

        enriched = enrich_risk_payload("物业公司长期侵占小区公共区域广告经营收益并拒不返还，是否合法？", payload)

        self.assertEqual(enriched["risk_level"], "high")

    def test_enrich_risk_payload_caps_isolated_unfair_competition_confusion_to_medium(self):
        payload = {
            "answer": "该行为可能构成混淆行为。",
            "risk_level": "high",
            "risk_types": ["不正当竞争风险"],
            "recommended_actions": ["停止使用近似标识"],
            "confidence_score": 0.8,
        }

        enriched = enrich_risk_payload(
            "某商家使用与知名品牌近似的店铺名称和装修风格，导致消费者误认，该行为是否合法？",
            payload,
            category="市场秩序",
        )

        self.assertEqual(enriched["risk_level"], "medium")
        trace = enriched.get("_contribution_trace", {}).get("risk_supplement_rules", [])
        self.assertTrue(any(rule.get("runtime_calibration") == "unfair_competition_confusion_medium_cap" for rule in trace))

    def test_enrich_risk_payload_keeps_aggravated_unfair_competition_confusion_high(self):
        payload = {
            "answer": "该行为可能构成混淆行为。",
            "risk_level": "high",
            "risk_types": ["不正当竞争风险"],
            "recommended_actions": ["停止使用近似标识"],
            "confidence_score": 0.8,
        }

        enriched = enrich_risk_payload(
            "某商家恶意多次使用近似标识并造成重大损失，导致消费者误认，是否构成不正当竞争？",
            payload,
            category="市场秩序",
        )

        self.assertEqual(enriched["risk_level"], "high")
        trace = enriched.get("_contribution_trace", {}).get("risk_supplement_rules", [])
        self.assertFalse(any(rule.get("runtime_calibration") == "unfair_competition_confusion_medium_cap" for rule in trace))
        trace = enriched.get("_contribution_trace", {}).get("risk_supplement_rules", [])
        self.assertFalse(any(rule.get("runtime_calibration") == "property_common_area_medium_cap" for rule in trace))

    def test_enrich_risk_payload_does_not_cap_property_income_without_owner_consent_gap(self):
        payload = {
            "answer": "物业服务合同项下经营收益分配争议需要结合合同和业主大会决议判断。",
            "risk_level": "high",
            "risk_types": ["物业收益分配争议风险"],
            "recommended_actions": ["核验合同约定和业主大会决议"],
            "confidence_score": 0.8,
        }

        enriched = enrich_risk_payload("物业公司与业主就小区公共区域广告经营收益分配发生争议，是否合法？", payload)

        self.assertEqual(enriched["risk_level"], "high")
        trace = enriched.get("_contribution_trace", {}).get("risk_supplement_rules", [])
        self.assertFalse(any(rule.get("runtime_calibration") == "property_common_area_medium_cap" for rule in trace))

    def test_enrich_risk_payload_caps_vat_mixed_sales_accounting_to_medium(self):
        payload = {
            "answer": "不同税率的应税交易应分别核算，未分别核算的从高适用税率。",
            "risk_level": "high",
            "risk_types": ["混合销售核算风险", "税率适用错误风险", "少缴税款风险"],
            "recommended_actions": ["分别核算不同业务收入", "正确适用税率", "完善财务核算体系"],
            "confidence_score": 0.8,
        }

        enriched = enrich_risk_payload("企业同时销售货物并提供安装服务，但未区分收入统一按低税率纳税，是否存在风险？", payload)

        self.assertEqual(enriched["risk_level"], "medium")
        self.assertGreaterEqual(enriched["confidence_score"], 0.85)
        trace = enriched["_contribution_trace"]["risk_supplement_rules"]
        self.assertTrue(any(rule.get("runtime_calibration") == "vat_mixed_sales_rate_accounting_medium_cap" for rule in trace))
        self.assertTrue(any(rule.get("risk_level_capped") for rule in trace))

    def test_enrich_risk_payload_keeps_false_invoice_vat_high(self):
        payload = {
            "answer": "通过虚开发票抵扣进项税额属于违法行为，可能引发行政处罚或刑事责任。",
            "risk_level": "high",
            "risk_types": ["虚开发票风险", "进项抵扣违规风险"],
            "recommended_actions": ["停止违规抵扣", "补缴税款及滞纳金"],
            "confidence_score": 0.8,
        }

        enriched = enrich_risk_payload("企业通过虚开发票将货物销售和安装服务按低税率处理，是否存在风险？", payload)

        self.assertEqual(enriched["risk_level"], "high")
        trace = enriched.get("_contribution_trace", {}).get("risk_supplement_rules", [])
        self.assertFalse(any(rule.get("runtime_calibration") == "vat_mixed_sales_rate_accounting_medium_cap" for rule in trace))

    def test_enrich_risk_payload_keeps_intentional_vat_evasion_high(self):
        payload = {
            "answer": "企业故意隐匿收入并拒不补缴税款，属于严重税务违法风险。",
            "risk_level": "high",
            "risk_types": ["偷逃税风险", "严重税务违法风险"],
            "recommended_actions": ["补缴税款并配合税务机关处理"],
            "confidence_score": 0.8,
        }

        enriched = enrich_risk_payload("企业故意未区分收入并统一按低税率纳税，税务机关要求补缴后仍拒不补缴，是否存在风险？", payload)

        self.assertEqual(enriched["risk_level"], "high")
        trace = enriched.get("_contribution_trace", {}).get("risk_supplement_rules", [])
        self.assertFalse(any(rule.get("runtime_calibration") == "vat_mixed_sales_rate_accounting_medium_cap" for rule in trace))

    def test_risk_payload_supplement_rules_config_is_valid(self):
        validated = validate_risk_payload_supplement_rules(RISK_PAYLOAD_SUPPLEMENT_RULES)

        self.assertGreaterEqual(len(validated), 30)
        self.assertTrue(any("儿童个人信息" in rule.get("answer_note", "") for rule in validated))
        self.assertTrue(any(rule.get("scenario_id") == "trade_secret_customer_list_leak" for rule in validated))

    def test_risk_payload_supplement_rules_reject_unknown_keys(self):
        invalid_rules = [{"question_all": ["测试"], "answer_note": "测试", "unknown": True}]

        with self.assertRaises(ValueError):
            validate_risk_payload_supplement_rules(invalid_rules)

    def test_enrich_risk_payload_uses_externalized_children_rule(self):
        payload = {
            "answer": "该处理涉及未成年人信息。",
            "risk_types": [],
            "recommended_actions": [],
            "confidence_score": 0.2,
        }

        enriched = enrich_risk_payload(
            "某儿童游戏APP收集儿童（8-12岁）的位置、设备信息，仅用普通用户协议征得家长同意，是否合规？",
            payload,
        )

        self.assertEqual(enriched["risk_level"], "high")
        self.assertIn("儿童信息保护不力", enriched["risk_types"])
        self.assertIn("制定专门的儿童个人信息处理规则", enriched["recommended_actions"])
        self.assertIn("违规风险", enriched["answer"])
        self.assertGreaterEqual(enriched["confidence_score"], 0.85)

    def test_enrich_risk_payload_uses_externalized_false_promotion_rule(self):
        payload = {
            "answer": "该行为可能构成虚假宣传和不正当竞争。",
            "risk_types": [],
            "recommended_actions": [],
            "confidence_score": 0.2,
        }

        enriched = enrich_risk_payload(
            "某企业在广告中虚构产品功能和效果以吸引消费者，该行为是否合法？",
            payload,
        )

        self.assertEqual(enriched["risk_level"], "high")
        self.assertTrue(any("虚假宣传" in risk_type for risk_type in enriched["risk_types"]))
        self.assertIn("停止虚假宣传", enriched["recommended_actions"])
        self.assertIn("误导消费者", enriched["answer"])
        self.assertGreaterEqual(enriched["confidence_score"], 0.85)

    def test_enrich_risk_payload_stabilizes_trademark_non_use_terms(self):
        payload = {
            "answer": "该商标存在撤销可能。",
            "risk_level": "high",
            "risk_types": [],
            "recommended_actions": [],
            "confidence_score": 0.2,
        }

        enriched = enrich_risk_payload(
            "某公司注册商标后连续三年未实际使用，该商标是否存在被撤销风险？",
            payload,
        )

        self.assertEqual(enriched["risk_level"], "medium")
        self.assertIn("商标撤销风险", enriched["risk_types"])
        self.assertIn("保留使用证据", enriched["recommended_actions"])
        self.assertIn("连续三年不使用", enriched["answer"])
        self.assertGreaterEqual(enriched["confidence_score"], 0.85)

    def test_enrich_risk_payload_keeps_trademark_infringement_high(self):
        payload = {
            "answer": "未经许可使用近似商标，可能造成混淆，不能仅以通用名称抗辩排除侵权风险。",
            "risk_level": "high",
            "risk_types": ["商标侵权风险"],
            "recommended_actions": ["停止使用相关标识"],
            "confidence_score": 0.8,
        }

        enriched = enrich_risk_payload(
            "某企业主张相关标识属于通用名称，但其未经许可在同类商品上使用近似商标并造成消费者混淆，是否构成侵权？",
            payload,
        )

        self.assertEqual(enriched["risk_level"], "high")
        trace = enriched.get("_contribution_trace", {}).get("risk_supplement_rules", [])
        self.assertFalse(any(rule.get("risk_level_capped") for rule in trace))


if __name__ == "__main__":
    unittest.main()
