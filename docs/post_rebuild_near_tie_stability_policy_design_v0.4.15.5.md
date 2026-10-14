# v0.4.15.5 Near-Tie Stability Policy Design

## 结论

- status: `ready_for_near_tie_policy_review`
- blockers: `[]`
- runtime patch authorized: `False`
- recommended next step: `implement_minimal_same_bucket_stabilization_only_after_authorization`

## 输入依据

- v0.4.15.4 classification: `raw_rerank_order_boundary_drift_not_selector_replacement`
- v0.4.15.4 selected alternate counts: `{'中华人民共和国个人信息保护法|56': 2, '中华人民共和国网络安全法|20': 3}`

## 设计口径

- policy: `deterministic_same_bucket_order_stabilization`
- 只允许未来在既有 Cross-Encoder stable-score bucket 内做 deterministic ordering。
- 不改变 Cross-Encoder 分数、模型、query、`score_epsilon`、top_k、anchor、prompt 或 eval case。
- 不写 case id 分支，不硬编码某部法律或某个条文为赢家。
- 任何 runtime patch 都必须另开版本、重新授权，并跑 targeted repeat trace 与完整健康检查。

## 边界

本报告是 design-only，不是 runtime patch。
本版本不修改 hidden seed、anchor、prompt、rerank score、risk supplement、term preservation、scenario registry、fixtures 或 eval cases。
