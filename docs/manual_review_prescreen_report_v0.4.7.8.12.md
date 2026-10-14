# v0.4.7.8.12 Manual Review Prescreen Report

本报告是离线预筛建议，只帮助 reviewer 快速理解哪些 case 更值得优先看、哪些需要人工拍板。它不是最终人工复核结论，也不会写入 proposed decision schema。

## 边界

- 只读取现有 workbench、alignment、coverage、rag_eval 与 rag_eval_cases 报告。
- 不调用 LLM、Qdrant、rag_query、后端 API 或任何联网能力。
- 不修改 hidden seed、anchor、rerank、prompt、risk supplement、eval case 或 RAG 主流程。
- 不自动导入 reviewer decision；导入前仍需人工确认。

## 总览

- 待预筛 case：36
- 需要你拍板：32
- 高置信度建议：12
- 中置信度建议：22
- 低置信度建议：2
- 建议分类：`{"likely_confirm_diagnostic_issue": 33, "retrieval_infrastructure_review": 3}`

## 需要优先人工拍板

| case | 风险 | 预筛分类 | 置信度 | 问题 | 主要原因 |
| --- | --- | --- | --- | --- | --- |
| `risk_employee_data_export_001` | high | 建议优先确认诊断成立 | high | 某公司员工私自将100万条客户名单（包含联系方式）导出并出售给竞争对手，公司应承担什么风险？ | 最终证据缺少 2 个预期主要条文。；场景核心条文缺少 1 个，可能需要校准案由/场景登记。；有 2 个条文曾在候选层出现但未进入最终 evidence_chain。；基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；存在 legal functional typing 或定义条款替代… |
| `pipl_data_export_conditions_001` | high | 建议优先确认诊断成立 | high | 个人信息出境需要具备哪些条件？ | 最终证据缺少 1 个预期主要条文。；场景核心条文缺少 1 个，可能需要校准案由/场景登记。；有 1 个条文曾在候选层出现但未进入最终 evidence_chain。；存在 legal functional typing 或定义条款替代规范条款的复核信号。；Alignment: One or more primary expected legal issue… |
| `risk_ai_medical_training_export_001` | high | 建议优先确认诊断成立 | high | 某AI医疗公司使用包含患者病历的数据训练模型，并将训练数据同步至境外服务器进行计算，已取得用户一般同意但未单独告知出境，是否合规？ | 最终证据缺少 1 个预期主要条文。；场景核心条文缺少 1 个，可能需要校准案由/场景登记。；有 1 个条文曾在候选层出现但未进入最终 evidence_chain。；基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；存在 legal functional typing 或定义条款替代… |
| `risk_employee_facial_001` | high | 建议优先确认诊断成立 | high | 某公司在员工入口处安装人脸识别考勤机，未告知员工人脸信息用途和存储期限，是否存在法律风险？ | 最终证据缺少 1 个预期主要条文。；场景核心条文缺少 1 个，可能需要校准案由/场景登记。；有 1 个条文曾在候选层出现但未进入最终 evidence_chain。；基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；存在 legal functional typing 或定义条款替代… |
| `risk_app_location_ads_002` | high | 建议优先确认诊断成立 | high | 某APP在未弹窗告知用户的情况下收集精准定位信息，并将该信息用于广告推荐，是否存在个人信息合规风险？ | 最终证据缺少 1 个预期主要条文。；有 1 个条文曾在候选层出现但未进入最终 evidence_chain。；基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；存在 legal functional typing 或定义条款替代规范条款的复核信号。；Alignment: One or… |
| `risk_unfair_competition_trade_secret_001` | high | 建议优先确认诊断成立 | high | 员工离职后将原公司客户名单带至新公司使用，是否构成违法？ | 场景核心条文缺少 2 个，可能需要校准案由/场景登记。；Alignment: One or more primary expected legal issues lack matching evidence.；Alignment: Risk outputs include terms or actions not visibly supported by… |
| `risk_data_export_overseas_001` | high | 建议优先确认诊断成立 | high | 某跨境电商平台处理超过100万用户个人信息，并将用户订单数据（包含姓名、电话、地址）传输给境外云服务商用于订单处理，未申报数据出境安全评估，是否合规？ | 场景核心条文缺少 1 个，可能需要校准案由/场景登记。；基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: One or more primary expected legal issues lack matching evidence.；Alignment: R… |
| `risk_privacy_policy_sharing_001` | high | 建议优先确认诊断成立 | high | 某APP隐私政策中未写明会向第三方广告平台共享用户信息，但实际发生了共享，是否违规？ | 场景核心条文缺少 1 个，可能需要校准案由/场景登记。；基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: One or more primary expected legal issues lack matching evidence.；Alignment: R… |
| `risk_algorithm_bias_001` | high | 建议优先确认诊断成立 | medium | 某招聘平台使用AI算法筛选简历，系统对特定地区求职者给出明显更低的评分，是否涉及算法歧视风险？ | 基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: Risk outputs include terms or actions not visibly supported by evidence text.；Coverage: Expected coverage… |
| `risk_antitrust_price_fixing_001` | high | 建议优先确认诊断成立 | medium | 多家同行企业通过行业会议约定统一提高产品价格，该行为是否合法？ | 基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: Risk outputs include terms or actions not visibly supported by evidence text.；Coverage: Expected coverage… |
| `risk_chatbot_training_001` | high | 建议优先确认诊断成立 | medium | 某公司用客服聊天记录（包含用户姓名、手机号、咨询内容）训练AI客服模型，未获得用户明确同意，是否违规？ | 基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: Risk outputs include terms or actions not visibly supported by evidence text.；Coverage: Expected coverage… |
| `risk_children_data_001` | high | 建议优先确认诊断成立 | medium | 某儿童游戏APP收集儿童（8-12岁）的位置、设备信息，仅用普通用户协议征得家长同意，是否合规？ | 基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: Risk outputs include terms or actions not visibly supported by evidence text.；Coverage: Expected coverage… |
| `risk_company_related_transaction_001` | high | 建议优先确认诊断成立 | medium | 公司董事未经批准与公司进行交易并从中获利，该行为是否合法？ | 基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: Risk outputs include terms or actions not visibly supported by evidence text.；Coverage: Expected coverage… |
| `risk_contract_auto_renewal_001` | high | 建议优先确认诊断成立 | medium | 某视频平台在会员协议中约定自动续费，但未在扣费前以显著方式提醒用户，该条款是否有效？ | 基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: Risk outputs include terms or actions not visibly supported by evidence text.；Coverage: Expected coverage… |
| `risk_data_breach_notification_001` | high | 建议优先确认诊断成立 | medium | 某公司服务器被攻击，100万条用户个人信息泄露，公司未及时通知用户，是否存在违规风险？ | 基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: Risk outputs include terms or actions not visibly supported by evidence text.；Coverage: Expected coverage… |
| `risk_data_leak_contract_001` | high | 建议优先确认诊断成立 | medium | 某企业与第三方签订数据处理协议，但未约定数据泄露责任分配，发生泄露后责任如何认定？ | 基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: Risk outputs include terms or actions not visibly supported by evidence text.；Coverage: Expected coverage… |
| `risk_data_minimization_violation_001` | high | 建议优先确认诊断成立 | medium | 某APP在注册时要求用户填写职业、收入、婚姻状况等信息，但其核心功能仅为天气查询，该行为是否合规？ | 基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: Risk outputs include terms or actions not visibly supported by evidence text.；Coverage: Expected coverage… |
| `risk_gray_area_ai_training_001` | high | 建议优先确认诊断成立 | medium | 某公司使用已匿名化的用户行为数据训练推荐算法，但未明确说明是否可被重新识别，该行为是否存在风险？ | 基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: Risk outputs include terms or actions not visibly supported by evidence text.；Coverage: Expected coverage… |
| `risk_labor_dispatch_001` | high | 建议优先确认诊断成立 | medium | 某公司长期通过劳务派遣形式使用员工从事核心岗位工作，该做法是否合法？ | 基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: Risk outputs include terms or actions not visibly supported by evidence text.；Coverage: Expected coverage… |
| `risk_patent_invalid_001` | high | 建议优先确认诊断成立 | medium | 某企业申请的专利技术在申请日前已被公开，该专利是否存在被宣告无效的风险？ | 基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: Risk outputs include terms or actions not visibly supported by evidence text.；Coverage: Expected coverage… |

## 全量预筛清单

| case | 风险 | 预筛分类 | 置信度 | 问题 | 主要原因 |
| --- | --- | --- | --- | --- | --- |
| `risk_employee_data_export_001` | high | 建议优先确认诊断成立 | high | 某公司员工私自将100万条客户名单（包含联系方式）导出并出售给竞争对手，公司应承担什么风险？ | 最终证据缺少 2 个预期主要条文。；场景核心条文缺少 1 个，可能需要校准案由/场景登记。；有 2 个条文曾在候选层出现但未进入最终 evidence_chain。；基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；存在 legal functional typing 或定义条款替代… |
| `pipl_data_export_conditions_001` | high | 建议优先确认诊断成立 | high | 个人信息出境需要具备哪些条件？ | 最终证据缺少 1 个预期主要条文。；场景核心条文缺少 1 个，可能需要校准案由/场景登记。；有 1 个条文曾在候选层出现但未进入最终 evidence_chain。；存在 legal functional typing 或定义条款替代规范条款的复核信号。；Alignment: One or more primary expected legal issue… |
| `risk_ai_medical_training_export_001` | high | 建议优先确认诊断成立 | high | 某AI医疗公司使用包含患者病历的数据训练模型，并将训练数据同步至境外服务器进行计算，已取得用户一般同意但未单独告知出境，是否合规？ | 最终证据缺少 1 个预期主要条文。；场景核心条文缺少 1 个，可能需要校准案由/场景登记。；有 1 个条文曾在候选层出现但未进入最终 evidence_chain。；基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；存在 legal functional typing 或定义条款替代… |
| `risk_employee_facial_001` | high | 建议优先确认诊断成立 | high | 某公司在员工入口处安装人脸识别考勤机，未告知员工人脸信息用途和存储期限，是否存在法律风险？ | 最终证据缺少 1 个预期主要条文。；场景核心条文缺少 1 个，可能需要校准案由/场景登记。；有 1 个条文曾在候选层出现但未进入最终 evidence_chain。；基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；存在 legal functional typing 或定义条款替代… |
| `risk_app_location_ads_002` | high | 建议优先确认诊断成立 | high | 某APP在未弹窗告知用户的情况下收集精准定位信息，并将该信息用于广告推荐，是否存在个人信息合规风险？ | 最终证据缺少 1 个预期主要条文。；有 1 个条文曾在候选层出现但未进入最终 evidence_chain。；基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；存在 legal functional typing 或定义条款替代规范条款的复核信号。；Alignment: One or… |
| `risk_unfair_competition_trade_secret_001` | high | 建议优先确认诊断成立 | high | 员工离职后将原公司客户名单带至新公司使用，是否构成违法？ | 场景核心条文缺少 2 个，可能需要校准案由/场景登记。；Alignment: One or more primary expected legal issues lack matching evidence.；Alignment: Risk outputs include terms or actions not visibly supported by… |
| `risk_data_export_overseas_001` | high | 建议优先确认诊断成立 | high | 某跨境电商平台处理超过100万用户个人信息，并将用户订单数据（包含姓名、电话、地址）传输给境外云服务商用于订单处理，未申报数据出境安全评估，是否合规？ | 场景核心条文缺少 1 个，可能需要校准案由/场景登记。；基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: One or more primary expected legal issues lack matching evidence.；Alignment: R… |
| `risk_privacy_policy_sharing_001` | high | 建议优先确认诊断成立 | high | 某APP隐私政策中未写明会向第三方广告平台共享用户信息，但实际发生了共享，是否违规？ | 场景核心条文缺少 1 个，可能需要校准案由/场景登记。；基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: One or more primary expected legal issues lack matching evidence.；Alignment: R… |
| `risk_algorithm_bias_001` | high | 建议优先确认诊断成立 | medium | 某招聘平台使用AI算法筛选简历，系统对特定地区求职者给出明显更低的评分，是否涉及算法歧视风险？ | 基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: Risk outputs include terms or actions not visibly supported by evidence text.；Coverage: Expected coverage… |
| `risk_antitrust_price_fixing_001` | high | 建议优先确认诊断成立 | medium | 多家同行企业通过行业会议约定统一提高产品价格，该行为是否合法？ | 基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: Risk outputs include terms or actions not visibly supported by evidence text.；Coverage: Expected coverage… |
| `risk_chatbot_training_001` | high | 建议优先确认诊断成立 | medium | 某公司用客服聊天记录（包含用户姓名、手机号、咨询内容）训练AI客服模型，未获得用户明确同意，是否违规？ | 基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: Risk outputs include terms or actions not visibly supported by evidence text.；Coverage: Expected coverage… |
| `risk_children_data_001` | high | 建议优先确认诊断成立 | medium | 某儿童游戏APP收集儿童（8-12岁）的位置、设备信息，仅用普通用户协议征得家长同意，是否合规？ | 基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: Risk outputs include terms or actions not visibly supported by evidence text.；Coverage: Expected coverage… |
| `risk_company_related_transaction_001` | high | 建议优先确认诊断成立 | medium | 公司董事未经批准与公司进行交易并从中获利，该行为是否合法？ | 基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: Risk outputs include terms or actions not visibly supported by evidence text.；Coverage: Expected coverage… |
| `risk_contract_auto_renewal_001` | high | 建议优先确认诊断成立 | medium | 某视频平台在会员协议中约定自动续费，但未在扣费前以显著方式提醒用户，该条款是否有效？ | 基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: Risk outputs include terms or actions not visibly supported by evidence text.；Coverage: Expected coverage… |
| `risk_data_breach_notification_001` | high | 建议优先确认诊断成立 | medium | 某公司服务器被攻击，100万条用户个人信息泄露，公司未及时通知用户，是否存在违规风险？ | 基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: Risk outputs include terms or actions not visibly supported by evidence text.；Coverage: Expected coverage… |
| `risk_data_leak_contract_001` | high | 建议优先确认诊断成立 | medium | 某企业与第三方签订数据处理协议，但未约定数据泄露责任分配，发生泄露后责任如何认定？ | 基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: Risk outputs include terms or actions not visibly supported by evidence text.；Coverage: Expected coverage… |
| `risk_data_minimization_violation_001` | high | 建议优先确认诊断成立 | medium | 某APP在注册时要求用户填写职业、收入、婚姻状况等信息，但其核心功能仅为天气查询，该行为是否合规？ | 基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: Risk outputs include terms or actions not visibly supported by evidence text.；Coverage: Expected coverage… |
| `risk_gray_area_ai_training_001` | high | 建议优先确认诊断成立 | medium | 某公司使用已匿名化的用户行为数据训练推荐算法，但未明确说明是否可被重新识别，该行为是否存在风险？ | 基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: Risk outputs include terms or actions not visibly supported by evidence text.；Coverage: Expected coverage… |
| `risk_labor_dispatch_001` | high | 建议优先确认诊断成立 | medium | 某公司长期通过劳务派遣形式使用员工从事核心岗位工作，该做法是否合法？ | 基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: Risk outputs include terms or actions not visibly supported by evidence text.；Coverage: Expected coverage… |
| `risk_patent_invalid_001` | high | 建议优先确认诊断成立 | medium | 某企业申请的专利技术在申请日前已被公开，该专利是否存在被宣告无效的风险？ | 基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: Risk outputs include terms or actions not visibly supported by evidence text.；Coverage: Expected coverage… |
| `risk_property_management_001` | high | 建议优先确认诊断成立 | medium | 物业公司未经业主同意，将小区公共区域出租用于广告经营，是否合法？ | 基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: Risk outputs include terms or actions not visibly supported by evidence text.；Coverage: Expected coverage… |
| `risk_third_party_marketing_001` | high | 建议优先确认诊断成立 | medium | 某公司将用户手机号（未脱敏）提供给营销公司用于电话推销，未获得用户明示同意，是否违法？ | 基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: Risk outputs include terms or actions not visibly supported by evidence text.；Coverage: Expected coverage… |
| `risk_trademark_infringement_001` | high | 建议优先确认诊断成立 | medium | 某企业在未获得授权的情况下，在其产品包装上使用与知名品牌高度相似的商标标识，是否构成侵权？ | 基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: Risk outputs include terms or actions not visibly supported by evidence text.；Coverage: Expected coverage… |
| `risk_user_profile_overuse_001` | high | 建议优先确认诊断成立 | medium | 某电商平台基于用户浏览记录分析消费能力，并将该结果用于差异化定价（价格歧视），是否存在法律风险？ | 基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: Risk outputs include terms or actions not visibly supported by evidence text.；Coverage: Expected coverage… |
| `risk_vat_export_refund_001` | high | 建议优先确认诊断成立 | medium | 企业在出口退税中虚报出口金额以获取更多退税，是否合法？ | 基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: Risk outputs include terms or actions not visibly supported by evidence text.；Coverage: Expected coverage… |
| `risk_vat_false_invoice_001` | high | 建议优先确认诊断成立 | medium | 某企业通过虚开发票抵扣增值税进项税额，该行为是否合法？ | 基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: Risk outputs include terms or actions not visibly supported by evidence text.；Coverage: Expected coverage… |
| `risk_vat_no_invoice_income_001` | high | 建议优先确认诊断成立 | medium | 企业取得收入但未开具发票，也未申报纳税，该行为是否合法？ | 基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: Risk outputs include terms or actions not visibly supported by evidence text.；Coverage: Expected coverage… |
| `risk_company_information_disclosure_001` | medium | 建议优先确认诊断成立 | low | 公司拒绝向股东提供财务报表等资料，是否合法？ | 基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: Risk outputs include terms or actions not visibly supported by evidence text.；Coverage: Expected coverage… |
| `risk_vat_mixed_sales_001` | medium | 建议优先确认诊断成立 | low | 企业同时销售货物并提供安装服务，但未区分收入统一按低税率纳税，是否存在风险？ | 基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: Risk outputs include terms or actions not visibly supported by evidence text.；Coverage: Expected coverage… |
| `pipl_sensitive_definition_001` | unknown | 检索基建稳定性复核 | medium | 什么是敏感个人信息？请举例。 | 基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Coverage: Expected coverage improves only after anchor layer; review retrieval coverage dependency. |
| `positive_antitrust_independent_pricing_001` | low | 检索基建稳定性复核 | medium | 企业根据自身成本和市场情况独立制定产品价格，未与竞争对手协商，是否合法？ | 基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Coverage: Expected coverage improves only after anchor layer; review retrieval coverage dependency. |
| `standard_personal_info_scope_001` | unknown | 检索基建稳定性复核 | medium | 根据国家标准，个人信息控制者应当保护哪些信息？ | 基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Coverage: Expected coverage improves only after anchor layer; review retrieval coverage dependency. |
| `risk_compliant_case_001` | low | 建议优先确认诊断成立 | high | 某APP明确告知用户收集位置信息用于导航服务，并取得单独同意，且用户可随时关闭定位权限，该行为是否合规？ | 最终证据缺少 1 个预期主要条文。；有 1 个条文曾在候选层出现但未进入最终 evidence_chain。；基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；存在 legal functional typing 或定义条款替代规范条款的复核信号。；Alignment: One or… |
| `pipl_principles_001` | low | 建议优先确认诊断成立 | high | 个人信息保护的核心原则是什么？ | 最终证据缺少 1 个预期主要条文。；有 1 个条文曾在候选层出现但未进入最终 evidence_chain。；基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；存在 legal functional typing 或定义条款替代规范条款的复核信号。；Alignment: One or… |
| `cross_law_export_assessment_001` | low | 建议优先确认诊断成立 | high | 数据出境安全评估应当重点评估哪些内容？ | 场景核心条文缺少 2 个，可能需要校准案由/场景登记。；基础检索层存在缺口，说明不应只依赖 anchor 补救。；证据覆盖对 anchor 依赖较强，法律库扩大后稳定性风险较高。；Alignment: One or more primary expected legal issues lack matching evidence.；Coverage: Fi… |
| `positive_vat_compliance_001` | low | 建议优先确认诊断成立 | high | 企业如实申报收入并依法开具增值税发票，是否存在税务风险？ | 最终证据缺少 1 个预期主要条文。；基础检索层存在缺口，说明不应只依赖 anchor 补救。；Alignment: One or more primary expected legal issues lack matching evidence.；Alignment: Risk outputs include terms or actions not vi… |

## 使用建议

1. 先看“需要优先人工拍板”的高风险 case。
2. 对高置信度且证据缺口明确的 case，可在视觉复核台里核对后填写人工结论。
3. 对“检索基建稳定性复核”类 case，不要理解成原答案一定错误；它更像是在提醒检索底座过度依赖 anchor 或基础召回不稳。
4. 导入任何 reviewer decision 前，仍需由人工确认案由、证据链和理由。
