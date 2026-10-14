# v0.4.14.34 Post-Rebuild Alignment Retention Tightening

## 版本定位

v0.4.14.34 是生产重建后 RAG 主链路的 selector 收紧版本。它承接 v0.4.14.33 的 evidence delta 复核结论：v0.4.14.32 的保留机制能修复商标法第 49 条掉出 final evidence 的问题，但仍需要避免远距离泛化条文替换、弱片段误判和同源近邻核心争点条文掉出 final evidence。

本版本不是新增 gate，也不是通过新增 anchor、修改 prompt、修改 rerank、修改 risk supplement 或修改 eval case 来补结果。所有改动都限制在 final evidence selector 的通用 runtime 质量规则内。

## 修复内容

- 收紧 evidence alignment consequence 识别：
  - 不再把“有限责任公司”中的“责任”误判为法律后果信号。
  - 仅在“承担责任、法律责任、赔偿责任、侵权责任”等短语中识别责任后果。
- 增加同源远距离条文 outlier 防护：
  - 当 final evidence 已形成窄条文簇时，阻止远距离泛化条文替换核心证据。
  - 若已选条文本身跨度过大，不把它误当作稳定条文簇。
- 增加同源近邻争点覆盖补齐：
  - 当候选来自同一法源近邻条文，并明显覆盖更多问题争点短语时，可替换 final evidence 中的弱片段。
  - 仍保持 final evidence top-3 数量不变。
  - selector 不消费 rerank query 中的“场景锚点法条”提示行；判断只使用候选文档 metadata、证据正文、query 争点短语和同源近邻关系。
- 增加 protected evidence 硬保护：
  - 当已选证据被识别为同源近邻核心争点条文时，后续 `issue_candidate` 替换分支不得绕过 `protected_indexes`。
  - replacement index 在最终替换前再次过滤 protected index，避免核心证据被二级程序材料或同组后序条文挤出。

## 关键结果

- 离线 selector 单测已覆盖个人信息出境告知/单独同意、公司股权转让、商标连续三年不使用、产品责任远距离泛化条文等关键模式。
- `protected_indexes` 已作为最终替换前的硬边界，不再允许 `issue_candidate` 分支替换受保护核心证据。
- `risk_data_export_overseas_001`：final evidence 保留个人信息保护法第 38 条、第 39 条与数据出境安全评估办法第 4 条。
- `risk_company_share_transfer_001`：final evidence 保留公司法第 85 条、第 86 条与第 84 条第一款，避免弱片段占位。
- `risk_vat_mixed_sales_001`：final evidence 保留增值税法第 12 条、第 13 条。
- `risk_tort_product_liability_001`：final evidence 保持民法典第 1203 条、第 1204 条、第 1207 条，未再引入远距离泛化条文。
- `tests/post_rebuild_rag_eval_after_alignment_retention_tightened_report.json` 已覆盖复跑为 60/60 passed，`retrieval_failure_stage_summary={"PASS": 60}`。

## 验证结果

- `.\venv\Scripts\python.exe -m py_compile src\rag\retriever.py tests\test_candidate_budget.py`：通过。
- `.\venv\Scripts\python.exe -m unittest tests.test_candidate_budget`：30/30 passed。
- targeted RAG eval：
  - `risk_data_export_overseas_001`：通过。
  - `risk_tort_product_liability_001`：通过。
- full RAG eval：
  - `tests/post_rebuild_rag_eval_after_alignment_retention_tightened_report.json`
  - 60/60 passed。
  - `retrieval_failure_stage_summary={"PASS": 60}`。

## 边界

- 未修改 hidden seed。
- 未新增、修改或消费 anchor 提示。
- 未修改 rerank model、rerank score、rerank prompt 或 rerank API 调用。
- 未修改 prompt。
- 未修改 risk supplement / term preservation 规则。
- 未修改 eval case、fixture 或 scenario registry。
- 未扩大 evidence_chain top_k。

## 下一步

v0.4.14.34 已把 post-rebuild selector 修复从单点保留推进为更稳的 evidence group retention，并补上 protected evidence 硬保护。下一步不应继续堆 gate；应进入 v0.4.14 系列收口，随后转入下一轮真实 RAG 质量任务，例如检索输入质量、证据排序可解释性或法规扩容前 targeted smoke。
