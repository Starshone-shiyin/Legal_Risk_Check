# v0.4.15.26 Process Over-Risk Runtime Hardening

## 定位

本版本是 strict risk-level over-risk 的窄口径 runtime hardening，处理两类更像中风险的程序/民事管理类场景：

- 物业公司未经业主同意出租小区公共区域用于广告经营。
- 有限责任公司股东对外转让股权，未通知其他股东，且问题落在优先购买权/对外转让通知程序语境。
- 普通增值税混合销售/不同税率交易未分别核算、统一按低税率处理，但不存在虚开、偷逃税、拒不补缴或刑事/行政升级事实。

本版本同时加固 v0.4.15.25 商标通用名称校准，避免 “商标权滥用风险” 这类评价性措辞误触发高风险侵权排除。

## 修复内容

- 新增 `is_property_common_area_medium_case()`，只对问题事实同时包含“物业/小区”“公共区域/共有部分”“出租/广告经营/收益”和“未经业主同意/未经业主大会或共同决定”的民事管理类场景设置 medium 上限。
- 新增 `is_share_transfer_notice_medium_case()`，只对问题事实同时包含“有限责任公司/有限公司”“股权转让”“其他股东通知缺口”和“优先购买权/对外转让”的程序型公司治理场景设置 medium 上限。
- 新增 `is_vat_mixed_sales_rate_accounting_medium_case()`，只对普通“混合销售/兼营/两项以上应税交易 + 未区分收入/未分别核算/统一按低税率 + 税率/纳税/增值税”场景设置 medium 上限。
- 股权转让 cap 只依赖问题事实和严重排除词，不依赖 LLM 答案是否写出“程序违规”等固定措辞，降低 full eval 输出波动。
- 商标通用名称 cap 排除 “商标权滥用” 这种评价性措辞对侵权排除词的误伤；真正侵权、混淆、假冒、未经许可等场景仍保持 high。

## 高风险排除

以下场景不被本版本降级：

- 物业场景中出现侵占、挪用、拒不返还、重大损失、刑事、欺诈、伪造等严重事实；或只是收益分配争议、合同争议，问题事实没有“未经业主同意”缺口。
- 股权转让场景中出现恶意串通、伪造、欺诈、抽逃出资、重大损失、刑事等严重事实；或涉及上市公司信息披露、证券监管、国资转让、产权交易、司法执行、质押、代持、债权人、监管审批/登记等非普通有限责任公司内部通知程序问题。
- VAT 场景中出现虚开、骗取出口退税、偷逃税、隐匿收入、未申报/不申报、拒不补缴、重大/巨额、多次/反复、故意/恶意、行政处罚、刑事或犯罪事实。
- 商标场景中出现未经许可、混淆、假冒、仿冒、侵权赔偿、停止侵权等实质侵权事实。

## 结果

- `tests/targeted_process_overrisk_trace_v0.4.15.26_report.json`：修复前定位两个程序/民事管理 over-risk 目标 case。
- `tests/targeted_process_overrisk_patch_v0.4.15.26_report.json`：2/2 passed。
- `tests/targeted_trademark_overrisk_patch_v0.4.15.26_report.json`：2/2 passed。
- `tests/targeted_vat_mixed_sales_patch_v0.4.15.26_report.json`：5/5 passed。
- `tests/post_process_overrisk_patch_full_rag_eval_v0.4.15.26_report.json`：compact full RAG eval 59/60，retrieval stage 仍为 `PASS=60`。
- 剩余唯一 strict risk-level failure 为 `risk_unfair_competition_confusion_001`。该 case 涉及知名品牌近似和消费者误认，法律上 high 具有可辩护性，本版本不硬性压低。

## 边界

- 修改 `src/rag/retriever.py` 中风险 payload 后处理逻辑。
- 扩展 `tests/test_retriever_contract.py` 契约测试。
- 不修改 hidden seed、anchor、prompt、rerank、risk supplement 配置、term preservation、taxonomy、scenario registry、fixtures、eval cases 或 Qdrant。
- 不新增 gate，不接入新的离线治理链。

## 验证

- `./venv/Scripts/python.exe -m py_compile src/rag/retriever.py tests/test_retriever_contract.py`
- `./venv/Scripts/python.exe -m unittest tests.test_retriever_contract`
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/targeted_process_overrisk_patch_v0.4.15.26_report.json --check-risk --case-id risk_property_management_001 --case-id risk_company_share_transfer_001`
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/targeted_trademark_overrisk_patch_v0.4.15.26_report.json --check-risk --case-id risk_trademark_generic_name_001 --case-id risk_trademark_non_use_001`
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/targeted_vat_mixed_sales_patch_v0.4.15.26_report.json --check-risk --case-id risk_vat_mixed_sales_001 --case-id risk_vat_false_invoice_001 --case-id risk_vat_export_refund_001 --case-id risk_vat_no_invoice_income_001 --case-id positive_vat_compliance_001`
- `./venv/Scripts/python.exe tools/run_rag_eval.py --cases tests/rag_eval_cases.json --output tests/post_process_overrisk_patch_full_rag_eval_v0.4.15.26_report.json --check-risk --compact-report`
