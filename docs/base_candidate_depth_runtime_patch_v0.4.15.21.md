# v0.4.15.21 Base Candidate Depth Runtime Patch

## 定位

本版本是 v0.4.15.19-v0.4.15.20 live probe 之后的最小主链路修复。前序 probe 已确认：14/14 missing final refs 存在于 `legal_knowledge`，且可通过 runtime metadata filter；主要问题集中在 base retrieval candidate cutoff，而不是 Qdrant payload 缺失或 metadata filter 错误。

## 实施内容

- `BASE_SPARSE_CANDIDATE_K=20`：将 sparse retrieval 候选深度从 10 保守提升到 20。
- `BASE_DENSE_CANDIDATE_K=5`：dense 候选数保持不变。
- `BASE_UNION_CANDIDATE_LIMIT=15`：base union 总预算保持不变。
- `RERANK_INPUT_CANDIDATE_LIMIT=15`：rerank 输入总预算保持不变。
- `RERANK_BASE_CANDIDATE_QUOTA=5`、`RERANK_ANCHOR_CANDIDATE_QUOTA=10`：base/anchor 配额保持不变。
- sparse、union、rerank input 的 debug summary 使用对应常量，便于后续诊断候选来源。

## 为什么不采用激进扩张

验证过程中曾尝试扩大 sparse depth、base union、rerank input 和 base quota。该方案能改善部分 base recall，但 full eval 退到 58/60，并造成 IP 类用例回归：

- `risk_trademark_non_use_001` 缺《商标法》第 49 条。
- `risk_patent_invalid_001` 缺《专利法》第 22 条。

因此最终版本只保留 sparse depth 的保守扩张，不扩大 rerank 输入规模，不改变 anchor 配额，不修改 rerank 算法。

## 验证结果

- `tests/targeted_base_candidate_depth_patch_v0.4.15.21_report.json`：7/7 passed。
- `tests/post_candidate_depth_patch_full_rag_eval_v0.4.15.21_report.json`：60/60 passed，`retrieval_failure_stage_summary={"PASS": 60}`。
- `tests.test_candidate_budget` 与 `tests.test_retriever_contract`：58 tests passed。

## 边界

- 不修改 hidden seed、anchor、prompt、rerank 算法、risk supplement、term preservation、scenario registry、fixtures 或 eval cases。
- 不写 Qdrant，不 rebuild，不新增法规，不新增 anchor。
- 本版本是通用 base retrieval 候选收集修复，不是样本修补工具，也不是新增 gate。

## 后续观察

当前 full eval 仍有若干 case 的风险等级输出与 expected risk level 不完全一致，但 eval 接受逻辑判定通过。本版本不修改 risk taxonomy 或 risk supplement；后续应单独审查 risk-level acceptance policy，避免把评测宽容误读为风险判断已经完全稳定。
