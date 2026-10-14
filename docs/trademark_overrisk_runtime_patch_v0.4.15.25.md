# v0.4.15.25 Trademark Over-Risk Runtime Patch

## 定位

本版本是 RAG 主链路的窄口径风险等级修复，用于处理 strict risk-level eval 暴露出的两个明显商标过高定级 case：

- `risk_trademark_generic_name_001`
- `risk_trademark_non_use_001`

修复目标不是新增诊断 gate，也不是样本修补；目标是在现有 `enrich_risk_payload` 后处理阶段增加通用、可解释、可回归验证的商标撤销/无效中风险校准。

## 修复内容

- 新增 `cap_risk_level(payload, maximum)`，允许在明确边界内把 LLM 已给出的过高 `risk_level` 收敛到指定上限。
- 新增 `is_trademark_invalid_or_cancellation_medium_case(question, payload)`，识别商标通用名称注册/独占使用、连续三年不使用/撤销风险这类偏权利稳定性或注册合规场景。
- 对命中的纯商标无效/撤销场景设置 medium 上限，并保留 `confidence_score >= 0.85`。
- contribution trace 记录 `runtime_calibration=trademark_invalid_or_cancellation_medium_cap`、`risk_level_changed` 和 `risk_level_capped`，便于后续复核。

## 误伤防护

本版本显式排除商标侵权、混淆、假冒、仿冒、伪造标识、反向假冒、停止侵权、侵权赔偿等高风险事实。判断同时读取 question、answer、risk_types 和 recommended_actions，避免问题中出现“通用名称”抗辩词时误把实际侵权场景降级。

因此，以下场景仍应保持 high：

- 未经许可在同类商品上使用相同或近似商标并造成混淆。
- 销售假冒注册商标商品。
- 伪造或擅自制造注册商标标识。
- 仿冒、冒用、山寨知名品牌标识。
- 反向假冒或已经触发停止侵权、侵权赔偿语义的场景。

## 结果

- targeted trace 修复前：2/2 case 均为 `over_risk`，retrieval stage 均为 `PASS`。
- targeted patch 验证后：2/2 passed，两个商标 case 的 `risk_level` 均校准为 expected `medium`。
- compact full RAG eval：56/60 passed，retrieval stage 仍为 `PASS=60`。
- strict risk-level 剩余失败从 5 个降为 4 个，剩余均为 `over_risk`：`risk_property_management_001`、`risk_company_share_transfer_001`、`risk_vat_mixed_sales_001`、`risk_unfair_competition_confusion_001`。

## 边界

- 修改 `src/rag/retriever.py` 的风险 payload 后处理逻辑。
- 扩展 `tests/test_retriever_contract.py` 的契约测试。
- 不修改 hidden seed、anchor、prompt、rerank、risk supplement、term preservation、taxonomy、scenario registry、fixtures、eval cases 或 Qdrant。
- 不新增 CLI gate，不新增 anchor，不扩大候选召回，不改变 evidence selector。

## 验证

- `./venv/Scripts/python.exe -m py_compile src/rag/retriever.py tests/test_retriever_contract.py`
- `./venv/Scripts/python.exe -m unittest tests.test_retriever_contract`
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/targeted_trademark_overrisk_patch_v0.4.15.25_report.json --check-risk --case-id risk_trademark_generic_name_001 --case-id risk_trademark_non_use_001`
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/post_trademark_overrisk_patch_full_rag_eval_v0.4.15.25_report.json --check-risk --compact-report`

