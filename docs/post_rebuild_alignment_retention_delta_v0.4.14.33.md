# v0.4.14.33 Post-Rebuild Alignment Retention Delta

## 结论

- 状态：`passed`
- 修复前 full RAG eval：`58/60`
- 修复后 full RAG eval：`60/60`
- evidence changed cases：`9`
- replacement delta cases：`7`
- citation-only delta cases：`2`
- added expected evidence：`1`
- removed expected evidence：`0`
- risky unexplained replacement：`5`
- classification summary：`{'unchanged': 9, 'score_only_change': 42, 'unchanged_pass_with_replacement_needs_review': 5, 'harmless_citation_normalization': 2, 'improvement_needs_review': 1, 'explained_improvement': 1}`

## 需要关注的变化

- `positive_unfair_competition_true_ad_001`
  - 分类：`unchanged_pass_with_replacement_needs_review`
  - 状态变化：`unchanged_passed`
  - 风险标记：`[{'flag': 'unexplained_replacement_in_unchanged_pass', 'severity': 'warn', 'reason': 'case 修复前后均通过，但 final evidence 法条发生替换。'}]`
  - 建议：`sample_review_replacement_before_series_closeout`
  - 新增证据：`[{'rank': 3, 'evidence_key': '中华人民共和国反不正当竞争法::10::', 'source': '中华人民共和国反不正当竞争法', 'law_name': '中华人民共和国反不正当竞争法', 'article_no': 10, 'section_no': '', 'citation': '[《中华人民共和国反不正当竞争法》第十条第四款]', 'rerank_score': 0.9960353970527649}]`
  - 移除证据：`[{'rank': 3, 'evidence_key': '中华人民共和国反垄断法::56::', 'source': '中华人民共和国反垄断法', 'law_name': '中华人民共和国反垄断法', 'article_no': 56, 'section_no': '', 'citation': '[《中华人民共和国反垄断法》第五十六条第二款]', 'rerank_score': 0.9144490957260132}]`
- `risk_company_capital_contribution_001`
  - 分类：`unchanged_pass_with_replacement_needs_review`
  - 状态变化：`unchanged_passed`
  - 风险标记：`[{'flag': 'unexplained_replacement_in_unchanged_pass', 'severity': 'warn', 'reason': 'case 修复前后均通过，但 final evidence 法条发生替换。'}]`
  - 建议：`sample_review_replacement_before_series_closeout`
  - 新增证据：`[{'rank': 3, 'evidence_key': '中华人民共和国公司法::88::', 'source': '中华人民共和国公司法', 'law_name': '中华人民共和国公司法', 'article_no': 88, 'section_no': '', 'citation': '[《中华人民共和国公司法》第八十八条第一款]', 'rerank_score': 0.9999697208404541}]`
  - 移除证据：`[{'rank': 3, 'evidence_key': '中华人民共和国公司法::98::', 'source': '中华人民共和国公司法', 'law_name': '中华人民共和国公司法', 'article_no': 98, 'section_no': '', 'citation': '[《中华人民共和国公司法》第九十八条第二款]', 'rerank_score': 0.9998358488082886}]`
- `risk_company_share_transfer_001`
  - 分类：`unchanged_pass_with_replacement_needs_review`
  - 状态变化：`unchanged_passed`
  - 风险标记：`[{'flag': 'unexplained_replacement_in_unchanged_pass', 'severity': 'warn', 'reason': 'case 修复前后均通过，但 final evidence 法条发生替换。'}]`
  - 建议：`sample_review_replacement_before_series_closeout`
  - 新增证据：`[{'rank': 1, 'evidence_key': '中华人民共和国公司法::84::', 'source': '中华人民共和国公司法', 'law_name': '中华人民共和国公司法', 'article_no': 84, 'section_no': '', 'citation': '[《中华人民共和国公司法》第八十四条第一款]', 'rerank_score': 0.9999676942825317}]`
  - 移除证据：`[{'rank': 1, 'evidence_key': '中华人民共和国公司法::85::', 'source': '中华人民共和国公司法', 'law_name': '中华人民共和国公司法', 'article_no': 85, 'section_no': '', 'citation': '[《中华人民共和国公司法》第八十五条]', 'rerank_score': 0.9999430179595947}]`
- `risk_tort_product_liability_001`
  - 分类：`improvement_needs_review`
  - 状态变化：`improved`
  - 风险标记：`[{'flag': 'improved_with_non_expected_replacement', 'severity': 'warn', 'reason': 'case 从失败变为通过，但新增证据不是显式 expected evidence。'}]`
  - 建议：`inspect_improved_case_non_expected_replacement`
  - 新增证据：`[{'rank': 3, 'evidence_key': '中华人民共和国民法典::1252::', 'source': '中华人民共和国民法典', 'law_name': '中华人民共和国民法典', 'article_no': 1252, 'section_no': '', 'citation': '[《中华人民共和国民法典》第一千二百五十二条第一款]', 'rerank_score': 0.9489107131958008}]`
  - 移除证据：`[{'rank': 3, 'evidence_key': '中华人民共和国民法典::1207::', 'source': '中华人民共和国民法典', 'law_name': '中华人民共和国民法典', 'article_no': 1207, 'section_no': '', 'citation': '[《中华人民共和国民法典》第一千二百零七条]', 'rerank_score': 0.9967421889305115}]`
- `risk_trademark_non_use_001`
  - 分类：`explained_improvement`
  - 状态变化：`improved`
  - 风险标记：`[{'flag': 'added_expected_evidence', 'severity': 'info', 'reason': '修复后新增了 eval case 期望证据，属于可解释改善。'}]`
  - 建议：`accept_after_human_readable_spot_check`
  - 新增证据：`[{'rank': 3, 'evidence_key': '中华人民共和国商标法::49::', 'source': '中华人民共和国商标法', 'law_name': '中华人民共和国商标法', 'article_no': 49, 'section_no': '', 'citation': '[《中华人民共和国商标法》第四十九条第一款]', 'rerank_score': 0.998891294002533}]`
  - 移除证据：`[{'rank': 3, 'evidence_key': '中华人民共和国商标法::11::', 'source': '中华人民共和国商标法', 'law_name': '中华人民共和国商标法', 'article_no': 11, 'section_no': '', 'citation': '[《中华人民共和国商标法》第十一条]', 'rerank_score': 0.9160342812538147}]`
- `risk_unfair_competition_confusion_001`
  - 分类：`unchanged_pass_with_replacement_needs_review`
  - 状态变化：`unchanged_passed`
  - 风险标记：`[{'flag': 'unexplained_replacement_in_unchanged_pass', 'severity': 'warn', 'reason': 'case 修复前后均通过，但 final evidence 法条发生替换。'}]`
  - 建议：`sample_review_replacement_before_series_closeout`
  - 新增证据：`[{'rank': 3, 'evidence_key': '中华人民共和国反不正当竞争法::40::', 'source': '中华人民共和国反不正当竞争法', 'law_name': '中华人民共和国反不正当竞争法', 'article_no': 40, 'section_no': '', 'citation': '[《中华人民共和国反不正当竞争法》第四十条]', 'rerank_score': 0.7783817052841187}]`
  - 移除证据：`[{'rank': 3, 'evidence_key': '中华人民共和国反不正当竞争法::1::', 'source': '中华人民共和国反不正当竞争法', 'law_name': '中华人民共和国反不正当竞争法', 'article_no': 1, 'section_no': '', 'citation': '[《中华人民共和国反不正当竞争法》第一条第一款]', 'rerank_score': 0.7175070643424988}]`
- `risk_vat_tax_rate_misapply_001`
  - 分类：`unchanged_pass_with_replacement_needs_review`
  - 状态变化：`unchanged_passed`
  - 风险标记：`[{'flag': 'unexplained_replacement_in_unchanged_pass', 'severity': 'warn', 'reason': 'case 修复前后均通过，但 final evidence 法条发生替换。'}]`
  - 建议：`sample_review_replacement_before_series_closeout`
  - 新增证据：`[{'rank': 2, 'evidence_key': '中华人民共和国增值税法::13::', 'source': '中华人民共和国增值税法', 'law_name': '中华人民共和国增值税法', 'article_no': 13, 'section_no': '', 'citation': '[《中华人民共和国增值税法》第十三条]', 'rerank_score': 0.9647648334503174}]`
  - 移除证据：`[{'rank': 3, 'evidence_key': '中华人民共和国增值税法::34::', 'source': '中华人民共和国增值税法', 'law_name': '中华人民共和国增值税法', 'article_no': 34, 'section_no': '', 'citation': '[《中华人民共和国增值税法》第三十四条]', 'rerank_score': 0.9411949515342712}]`

## 边界

- 本工具只读取已保存的 full RAG eval JSON 报告和 eval case metadata。
- 不调用 RAG、Qdrant、LLM，不修改 retriever、rerank、prompt、anchor、risk rules、scenario registry、fixtures 或 eval cases。
- 本报告用于 post-fix stabilization；它不是新的运行时策略，也不是人工最终结论。

## 下一步

- `review_changed_evidence_then_close_post_rebuild_stabilization`
