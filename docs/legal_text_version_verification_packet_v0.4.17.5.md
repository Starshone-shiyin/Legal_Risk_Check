# v0.4.17.5 Legal Text Version Verification Packet

本版本联网核验《中华人民共和国反不正当竞争法》的现行文本与历史文本编号差异，并将核验结果固化为离线快照和只读诊断报告。它不修改知识库、anchor、prompt、rerank、risk supplement、taxonomy、scenario registry、eval case 或 hidden seed。

## 核验结论

- 2025 年第二次修订后的现行《反不正当竞争法》自 2025-10-15 起施行。
- 现行法中，混淆行为条款为第七条。
- 现行法第六条是社会监督、国家机关不得支持包庇、行业自律条款。
- 2019 年修正文本中，混淆行为条款为第六条。
- `risk_unfair_competition_confusion_001` 的 expected evidence 和三轮最终证据链均使用第七条，符合现行法。
- 该 case 的 `legal_reasoning` 中提到第6条，属于历史编号/元数据表述漂移，不是检索或证据链错误。

## 产物

- 新增 `tests/legal_text_version_snapshot_v0.4.17.5.json`
- 新增 `tools/build_legal_text_version_verification_packet.py`
- 新增 `tests/test_legal_text_version_verification_packet.py`
- 新增 `tests/legal_text_version_verification_packet_v0.4.17.5_report.json`
- 新增本文档

## 来源

- 最高人民检察院门户网转载新华社全文：`https://www.spp.gov.cn/spp/fl/202506/t20250627_699862.shtml`
- 中国国际贸易促进委员会转载全国人大网来源全文：`https://www.ccpit.org/a/20250701/20250701z42m.html`
- 国家知识产权局 2019 年修正文本：`https://www.cnipa.gov.cn/art/2024/1/30/art_104_190080.html`

## 工程判断

本版本不建议 runtime patch、anchor change 或未经人工复核的 eval case change。若要追求严格全绿，应先人工确认该 case 的 expected risk level 和 `legal_reasoning` 条文编号口径；当前证据链使用现行法第七条是合理的。

## 验证

- `./venv/Scripts/python.exe -m py_compile tools/build_legal_text_version_verification_packet.py tests/test_legal_text_version_verification_packet.py src/main.py tools/run_project_health_check.py`
- `./venv/Scripts/python.exe -m unittest tests.test_legal_text_version_verification_packet tests.test_rag_expected_level_review_packet tests.test_rag_targeted_rerun_packet tests.test_rag_evidence_independence_baseline tests.test_project_health_check tests.test_roadmap_hygiene`
- `./venv/Scripts/python.exe tools/build_legal_text_version_verification_packet.py --review-packet tests/rag_expected_level_review_packet_v0.4.17.4_report.json --snapshot tests/legal_text_version_snapshot_v0.4.17.5.json --output tests/legal_text_version_verification_packet_v0.4.17.5_report.json`
- `./venv/Scripts/python.exe tools/check_test_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_artifact_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_tool_index_consistency.py`
- `./venv/Scripts/python.exe tools/check_encoding_hygiene.py`
- `./venv/Scripts/python.exe tools/run_project_health_check.py --output tests/project_health_check_report.json --fail-on-error`
- `git diff --check`
