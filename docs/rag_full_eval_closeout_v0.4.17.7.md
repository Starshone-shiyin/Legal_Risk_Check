# v0.4.17.7 RAG Full Eval Closeout

## 目的

本版本用于收口 v0.4.17.x RAG evidence independence / retrieval quality hardening 系列：在 v0.4.17.6 修正旧条文编号说明后，重新运行当前 RAG 主链路 full eval，确认是否还存在新的 retrieval、evidence-chain 或主链路回归。

## 运行结果

- 报告文件：`tests/rag_eval_report_v0.4.17.7.json`
- 运行命令：`./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/rag_eval_report_v0.4.17.7.json --check-risk`
- 总结果：`59/60` passed。
- 检索阶段：`retrieval_failure_stage_summary={"PASS": 60}`。
- 风险等级差异：`exact_match=49`，`over_risk=1`。
- 唯一失败：`risk_unfair_competition_confusion_001`。

唯一失败项仍为 `expected_risk_level`：系统输出 `high`，预期为 `medium`，差异类型为 `over_risk`。该 case 的 expected evidence、answer keywords、confidence score、expected risk types 和 expected actions 均通过，证据命中《中华人民共和国反不正当竞争法》第七条，与 v0.4.17.5-v0.4.17.6 的法律文本版本核验结论一致。

## 工程结论

本轮 full eval 没有发现新的 retrieval 或 evidence-chain 回归。v0.4.17.x 可以收口为：RAG 主链路当前稳定在 `59/60`，检索阶段 `PASS=60`；剩余失败是 expected-level / fact-strength 复核项，不是需要继续硬修的 runtime 缺陷。

后续如要追求 `60/60`，应先由人工法律复核决定 `risk_unfair_competition_confusion_001` 的事实强度和预期风险等级是否应调整；在没有该结论前，不应通过主链路补丁掩盖该差异。

## 边界

- 不修改 `hidden seed`。
- 不新增或修改 anchor。
- 不修改 prompt。
- 不修改 rerank。
- 不修改 risk supplement、term preservation、taxonomy 或 scenario registry。
- 不修改 Qdrant 数据。
- 不修改 eval case、expected evidence 或 expected risk level。
- 不把本版本写成新的 gate；它是一次主链路收口确认。

## 下一步建议

停止围绕 `risk_unfair_competition_confusion_001` 继续堆诊断。下一阶段应转向新的真实工程任务，例如法规扩容前的 ingestion quality / source integrity / targeted smoke 链路，或前后端接入前的最小 mock service 与 UI handoff。
