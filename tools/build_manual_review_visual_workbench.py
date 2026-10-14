"""Build a standalone visual manual-review workbench.

The generated HTML is self-contained: it embeds existing offline governance
reports and lets reviewers inspect cases, fill reviewer fields in browser
local state, export a filled workbench JSON plus a view-only CSV, and import
the JSON export back into matching case drafts for continued review. It never calls the
RAG main flow, backend APIs, Qdrant, an LLM, rerank, prompts, anchors, risk
rules, eval cases, or hidden seeds.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools._shared.layout import legacy_report_path


VERSION = "0.4.7.8.23"

DEFAULT_CONTRACT_REPORT_PATH = legacy_report_path("manual_review_visual_workbench_contract_report.json")
DEFAULT_WORKBENCH_PATH = Path("tests/evidence_manual_review_workbench.json")
DEFAULT_INTAKE_CONTRACT_PATH = legacy_report_path("manual_review_intake_contract_report.json")
DEFAULT_PROGRESS_REPORT_PATH = legacy_report_path("evidence_manual_review_progress_report.json")
DEFAULT_GOVERNANCE_REPORT_PATH = legacy_report_path("evidence_manual_review_governance_report.json")
DEFAULT_IMPORT_REPORT_PATH = legacy_report_path("manual_review_workbench_import_report.json")
DEFAULT_DIFF_REPORT_PATH = legacy_report_path("manual_review_decision_diff_report.json")
DEFAULT_VALIDATION_REPORT_PATH = legacy_report_path("proposed_manual_review_decision_validation_report.json")
DEFAULT_PROMOTION_REPORT_PATH = legacy_report_path("validated_decision_promotion_dry_run_report.json")
DEFAULT_CLOSEOUT_REPORT_PATH = legacy_report_path("manual_review_intake_gate_closeout_report.json")
DEFAULT_PILOT_BATCH_REPORT_PATH = legacy_report_path("manual_review_pilot_batch_report.json")
DEFAULT_PILOT_REVIEW_ASSIST_REPORT_PATH = legacy_report_path("manual_review_pilot_case_review_assist_report.json")
DEFAULT_RAG_EVAL_REPORT_PATH = Path("tests/rag_eval_report.json")
DEFAULT_RAG_EVAL_CASES_PATH = Path("tests/rag_eval_cases.json")
DEFAULT_SCENARIO_REGISTRY_PATH = Path("config/scenario_registry.json")
DEFAULT_OUTPUT_PATH = Path("tools/manual_review_visual_workbench/index.html")
DEFAULT_REPORT_OUTPUT_PATH = legacy_report_path("manual_review_visual_workbench_build_report.json")

READ_ONLY_REPORT_DANGEROUS_KEYS = {
    "reviewer_input_template",
    "reviewer_decision",
    "workbench_items",
    "decision_status",
}

GUARDRAILS = {
    "standalone_offline_html": True,
    "rag_query_integration": "disallowed",
    "backend_api_write": "disallowed",
    "qdrant_access": "disallowed",
    "llm_access": "disallowed",
    "overwrite_original_decision_schema": "disallowed",
    "hidden_seed_mutation": "disallowed",
    "anchor_mutation": "disallowed",
    "rerank_mutation": "disallowed",
    "prompt_mutation": "disallowed",
    "risk_rule_mutation": "disallowed",
    "eval_case_mutation": "disallowed",
}

UI_CONFIG: dict[str, Any] = {
    "default_language": "zh-CN",
    "supported_languages": [
        {"code": "zh-CN", "label": "简体中文"},
        {"code": "en-US", "label": "English"},
    ],
    "guide_steps": [
        "先在左侧选择队列，例如高优先级、待人工复核或本地草稿。",
        "在案例列表选择一个 case，查看右侧概览、证据、问题和标签说明；整份导出的处理结果看左侧面板。",
        "进入决策页填写复核人、复核日期、复核结论和理由。",
        "确认根因、治理动作、后续排查目标，以及是否标记为回归测试样本候选。",
        "后续处理流程只使用 JSON；CSV 只是给人打开表格查看和核对。",
    ],
    "messages": {
        "zh-CN": {
            "documentTitle": "法律风控人工复核台",
            "brand": {
                "kicker": "Harvey 风格 RAG 治理",
                "title": "法律风控人工复核台",
                "subtitle": "用于查看证据支撑诊断、填写人工复核记录，并查看整份复核导出的处理结果。",
            },
            "sections": {"queues": "队列", "status": "整批概况", "globalPipeline": "整份导出处理结果", "guide": "操作指南"},
            "topbar": {
                "title": "人工证据复核",
                "subtitle": "从已保存诊断报告生成的离线工作台。",
            },
            "language": {"label": "语言", "selectTitle": "切换界面语言"},
            "queues": {
                "all_cases": "全部案例",
                "high_priority": "高优先级",
                "pilot_batch": "参考：优先复核",
                "awaiting_manual_review": "待人工复核",
                "blocked_intake_gate": "准入未通过",
                "with_local_draft": "本浏览器草稿",
                "ready_for_export": "可导出记录",
            },
            "tabs": {
                "overview": "概览",
                "evidence": "证据",
                "questions": "问题",
                "decision": "决策",
                "glossary": "标签说明",
            },
            "sideStatus": {
                "gate": "准入检查",
                "gateBlockers": "阻断原因",
                "noGateBlockers": "无阻断",
                "imported": "已导入",
                "rejected": "已拒绝",
                "readyActions": "待治理动作",
                "localDrafts": "本浏览器草稿",
            },
            "badges": {
                "gate": "准入检查",
                "staticData": "静态数据",
                "version": "版本",
                "ready": "就绪",
                "missing": "缺失",
            },
            "statusCodes": {
                "blocked": "阻断",
                "open": "开放",
                "pending": "待处理",
                "ready": "就绪",
                "unknown": "未知",
                "high": "高",
                "medium": "中",
                "low": "低",
                "disallowed": "禁止",
            },
            "kpis": {
                "cases": "案例总数",
                "pending": "待处理",
                "highPriority": "高优先级",
                "imported": "已导入",
                "validProposed": "有效提案",
                "readyActions": "待治理动作",
            },
            "caseQueue": {
                "title": "案例队列",
                "searchPlaceholder": "搜索 case、案由、问题、争点、队列或领域",
                "count": "{visible} 可见 / {total} 总计",
                "empty": "没有匹配的案例",
            },
            "common": {"unknown": "未知", "rootCauses": "根因", "true": "是", "false": "否"},
            "caseContext": {
                "caseTopic": "案由线索",
                "question": "待审问题",
                "scenario": "风险场景",
                "domains": "涉及领域",
                "expectedRiskTypes": "预期风险类型",
                "expectedActions": "预期整改动作",
                "source": "来源",
                "notAvailable": "现有离线报告没有提供案由线索。",
                "sourceRagEvalReport": "RAG 评测报告",
                "sourceRagEvalCases": "评测用例",
                "sourceScenarioRegistry": "场景登记",
            },
            "caseBadges": {
                "priority": "优先级",
                "draftReady": "记录可导出",
                "draftNeedsReview": "记录待补齐",
                "exportReady": "可导出",
                "reviewPending": "待复核",
            },
            "exportStatus": {
                "never": "尚未导出",
                "clean": "已导出",
                "dirty": "有未导出的更新",
                "lastExportedAt": "上次导出",
                "updatedAt": "上次更新",
            },
            "detail": {"noCaseSelected": "未选择案例", "noCaseData": "暂无案例数据"},
            "actions": {
                "clearDraft": "清空本案草稿",
                "saveDraft": "保存本案草稿",
                "applyAiSuggestion": "引用 AI 参考到草稿",
                "clearAiSuggestion": "清除 AI 参考",
                "exportJson": "导出复核记录 JSON",
                "exportCsv": "下载 CSV",
                "importReviewFile": "导入复核 JSON",
            },
            "draftSave": {
                "never": "尚未点击保存",
                "saved": "已手动保存",
                "dirty": "有未手动保存的更新",
                "savedAt": "上次保存 {time}",
                "autoSavedHint": "输入会自动暂存在本浏览器；点击保存只记录本案保存时间。",
            },
            "reviewImport": {
                "statusLabel": "本页导入状态",
                "never": "尚未导入草稿",
                "lastImported": "{imported} 条复核记录已导入，{cleared} 条旧草稿已清除，{unknown} 条未匹配，{duplicate} 条重复，{skipped} 条为空",
                "lastImportedWithSuggestions": "{imported} 条复核记录已导入，{suggestions} 条 AI 参考已载入，{cleared} 条旧草稿已清除，{unknown} 条未匹配，{duplicate} 条重复，{skipped} 条为空",
                "dialogTitle": "导入复核 JSON",
                "success": "导入完成：本次导入已替换旧本地草稿，避免旧草稿混入下一次导出。",
                "successWithSuggestions": "已按 case_id 自动载入；AI 预填只进入参考区，不会自动成为人工结论。",
                "replaceMode": "导入人工复核 JSON 时会先清空旧草稿；AI 参考只载入参考区。",
                "error": "导入失败：{message}",
                "invalidJson": "JSON 格式不正确或不是 filled manual review workbench。",
                "invalidCsv": "CSV 格式不正确或缺少 case_id。",
                "unsupportedFile": "请导入页面导出的 .json 复核文件。CSV 仅用于查看，不再作为正式导入入口。",
                "noRows": "文件中没有可导入的复核记录。",
            },
            "exportPreview": {
                "ready": "本次将导出 {ready} 条复核记录：{cases}",
                "blocked": "{blocked} 条未补齐记录不会导出。",
                "none": "当前没有可导出的复核记录，请先补齐必填项。",
                "confirmJson": "确认导出这些复核记录为 JSON？",
                "confirmCsv": "下载 CSV？CSV 只用于表格查看和人工核对，继续审阅或后续处理请使用 JSON。",
            },
            "overview": {"emptyDiagnostic": "暂无诊断摘要", "rootCauses": "根因"},
            "originalOutput": {
                "title": "原 LLM 输出",
                "subtitle": "用于和证据链、诊断问题进行对照；这是既有评测报告中的原回答，不是本页面重新生成的内容。",
                "confidence": "置信度",
                "source": "来源",
                "missing": "现有离线报告未提供原 LLM 输出。",
            },
            "evidence": {
                "missing_final_expected": "缺少最终预期证据",
                "missing_scenario_core": "缺少场景核心证据",
                "lost_evidence": "流失证据",
                "final_evidence": "最终证据",
                "source": "来源",
                "article": "条款",
                "content": "内容",
                "empty": "暂无证据上下文",
            },
            "questions": {
                "title": "建议复核问题",
                "empty": "暂无问题",
                "original": "原始问题",
            },
            "decision": {
                "readyNotice": "本案复核记录已满足离线导出条件。",
                "statusPrefix": "复核记录状态：",
                "summaryTitle": "复核判断摘要",
                "summarySubtitle": "先看案由、证据和诊断，再决定这条质量诊断是否成立。",
                "authorityNoticeTitle": "听人工填写区",
                "authorityNotice": "正式结论只来自下方人工填写区；参考材料、系统预筛和 AI 参考都不会自动导出为结论。",
                "aiSuggestionTitle": "参考：AI 预填",
                "aiSuggestionSubtitle": "这里是可参考的预填内容，不是人工复核结论；只有引用并人工确认后的草稿才会导出。",
                "aiSuggestionBadge": "AI 参考",
                "aiSuggestionImportedAt": "载入时间",
                "aiSuggestionDecision": "参考结论",
                "aiSuggestionRootCauses": "参考根因",
                "aiSuggestionActions": "参考治理动作",
                "aiSuggestionFixture": "参考回归测试候选",
                "aiSuggestionRationale": "参考理由",
                "aiSuggestionNotes": "参考备注",
                "aiSuggestionNoReviewerCopy": "复制建议不会带入复核人和复核日期，请你亲自填写。",
                "aiSuggestionCopied": "已引用 AI 参考，请人工确认复核人、日期、结论和理由。",
                "aiSuggestionHumanConfirm": "我已人工核对，并将该 AI 参考作为本人复核结论",
                "aiSuggestionHumanConfirmHint": "只有勾选后，引用自 AI 参考的内容才会作为可完成的人工草稿导出。",
                "pilotBatchTitle": "参考：优先复核清单",
                "pilotBatchSubtitle": "这是 v0.4.7.8.15 生成的只读优先级参考，用来提示先看哪些案件；它不是人工结论，也不会自动写入导出草稿。",
                "pilotBatchBadge": "优先复核",
                "pilotBatchRank": "优先顺序",
                "pilotBatchSelectionScore": "筛选分",
                "pilotBatchWhySelected": "为什么优先看",
                "pilotBatchEvidenceIssues": "证据问题摘要",
                "pilotBatchEvidenceToCheck": "需要核对的证据",
                "pilotBatchFinalEvidence": "最终证据链",
                "pilotBatchMissingEvidence": "缺失或曾丢失的证据",
                "pilotBatchPrescreen": "预筛参考",
                "pilotBatchAiSuggestion": "AI 参考",
                "pilotBatchAllowedOptions": "需要你填写的复核结论",
                "pilotBatchInstruction": "人工操作提醒",
                "pilotBatchRequiredFields": "导出前必须填写",
                "pilotBatchOptionalFields": "可以按情况填写",
                "pilotBatchNotDecision": "看过这张清单不等于完成复核；必须在下方表单亲自填写复核人、日期、结论和理由，才可能导出。",
                "pilotBatchReviewed": "标记已读（不写入复核记录）",
                "pilotBatchNoReviewerCopy": "系统预筛和 AI 参考只帮助理解，不会自动复制到 reviewer_input_template。",
                "pilotBatchHumanRequired": "需要人工确认",
                "pilotBatchAdvisoryDecision": "参考结论",
                "pilotBatchAdvisoryRootCauses": "参考根因",
                "pilotBatchAdvisoryActions": "参考治理动作",
                "pilotBatchAdvisoryFixture": "参考回归样本候选",
                "pilotBatchRationale": "参考理由",
                "pilotBatchNotes": "参考备注",
                "pilotReviewAssistTitle": "参考：证据阅读提示",
                "pilotReviewAssistSubtitle": "这是 v0.4.7.8.17 生成的只读阅读参考，用来解释案由、原 LLM 输出和证据支撑缺口；它不是人工复核结论。",
                "pilotReviewAssistBadge": "阅读参考",
                "pilotReviewAssistNotDecision": "此面板只帮助理解案件和证据链，不会写入导出草稿，也不会代替人工判断。",
                "pilotReviewAssistTendency": "参考倾向",
                "pilotReviewAssistSupport": "证据状态",
                "pilotReviewAssistSignals": "参考信号",
                "pilotReviewAssistOriginalClaims": "原 LLM 风险/动作",
                "pilotReviewAssistRisks": "风险类型",
                "pilotReviewAssistActions": "整改动作",
                "pilotReviewAssistFocusQuestions": "建议你重点核对",
                "pilotReviewAssistRationale": "参考理由",
                "pilotReviewAssistMissingEvidence": "缺失、场景核心或流失证据示例",
                "workflowTitle": "推荐复核顺序",
                "workflowEvidence": "1. 先确认案由、待审问题和证据是否说得上同一件事。",
                "workflowDecision": "2. 再选择复核结论，并用法律/证据理由说明为什么。",
                "workflowGovernance": "3. 最后确认根因、治理动作和是否标记为测试样本候选。",
                "caseTopic": "案由线索",
                "mainDiagnostics": "主要诊断",
                "suggestedRootCauses": "建议根因",
                "suggestedActions": "建议治理动作",
                "exportStatus": "本案导出状态",
                "reviewerInfo": "复核信息",
                "conclusionSection": "复核结论与理由",
                "rootCauseSection": "根因判断",
                "actionSection": "治理动作",
                "governanceSection": "治理备注",
                "originalCode": "原始代码",
                "chooseOne": "请选择一个结论",
                "useOriginalCodeHint": "导出仍保留原始代码，便于 importer、diff、validator 继续处理。",
                "requiredBadge": "必填",
                "conditionalBadge": "条件必填",
                "optionalBadge": "可选",
                "requiredHint": "必须填写，缺少会导致草稿不能作为可导出复核结论。",
                "conditionalHint": "只有在选择“确认诊断成立”或“确认需要范围校准”等结论时才需要填写。",
                "optionalHint": "看不准可以先留空；不会阻止导出草稿。",
                "reviewerInfoNote": "记录是谁在什么日期作出本次人工判断。",
                "conclusionSectionNote": "这里回答核心问题：这条系统诊断到底成立、部分成立、驳回，还是信息不足。",
                "rootCauseSectionNote": "如果诊断成立，请勾选造成问题的原因；如果不成立，可在驳回根因中说明。",
                "actionSectionNote": "只选择需要后续治理跟进的动作；这里不会直接修改检索、prompt 或评测样本。",
                "governanceSectionNote": "记录补充说明，并判断是否值得以后做成回归测试样本候选。",
                "reviewer": "复核人",
                "reviewerHelp": "填写你的名字或团队代号。",
                "reviewedAt": "复核日期",
                "reviewedAtPlaceholder": "YYYY-MM-DD",
                "reviewedAtHelp": "建议使用 YYYY-MM-DD，例如 2026-05-11。",
                "decision": "复核结论",
                "selectDecision": "选择复核结论",
                "decisionHelp": "如果无法判断，可以选“信息不足”或“暂缓”。",
                "confirmedRootCauses": "确认的根因",
                "confirmedRootCausesHelp": "当你确认诊断成立或需要范围校准时，至少勾选一个主要原因。",
                "rejectedRootCauses": "驳回的根因",
                "rejectedRootCausesHelp": "如果你认为某个建议根因不成立，可在这里勾选；不确定可以不填。",
                "confirmedFollowUpActions": "确认的治理动作",
                "confirmedFollowUpActionsHelp": "只有你明确希望后续治理跟进时再勾选。",
                "proposedChangeTargets": "建议后续排查目标",
                "proposedChangeTargetsPlaceholder": "例如 metadata_chunking | source_index；多个目标用 | 分隔",
                "proposedChangeTargetsHelp": "不确定工程目标时可以留空，避免误把诊断变成修复指令。",
                "fixtureCandidate": "标记为回归测试样本候选",
                "fixtureCandidateHint": "只表示值得后续整理为测试样本候选，不会直接写入 eval case。",
                "rationale": "理由",
                "rationalePlaceholder": "请说明证据链、案由和诊断之间的关系；如果信息不足，也写明缺什么。",
                "rationaleHelp": "用自然语言写判断理由即可，不要求工程术语。",
                "notes": "备注",
                "notesPlaceholder": "可记录需要后续人工确认的事项。",
                "notesHelp": "记录疑问、待确认事项或给后续 reviewer 的提醒。",
            },
            "draftIssues": {
                "empty_draft": "草稿为空",
                "missing_reviewer": "缺少复核人",
                "missing_reviewed_at": "缺少复核日期",
                "missing_decision": "缺少复核结论",
                "missing_rationale": "缺少理由",
                "missing_confirmed_root_cause": "缺少确认的根因",
                "missing_ai_suggestion_confirmation": "引用的 AI 参考尚未人工确认",
                "prohibited_change_target": "包含禁止变更目标",
            },
            "pipeline": {
                "title": "整份导出处理结果",
                "subtitle": "这是本次导出的整份复核 JSON 的处理结果，不代表当前选中的单个案例。",
                "import": "导入复核记录",
                "diff": "检查变更差异",
                "validation": "检查记录完整性",
                "promotion": "生成待处理动作",
                "closeout": "是否允许进入后续治理",
                "importValue": "{imported} 条记录已导入 / {rejected} 条记录被拒绝",
                "diffValue": "{changed} 个案例有变更 / {blocked} 个案例阻断",
                "diffValueNoBlockers": "{changed} 个案例有变更 / 无阻断",
                "validationValue": "{valid} 条记录有效 / {invalid} 条记录无效 / {pending} 条记录待处理",
                "promotionValue": "{candidates} 个候选 / {ready} 个待处理动作",
                "states": {"ready": "就绪", "blocked": "阻断", "pending": "待处理"},
            },
            "guide": {
                "steps": [
                    "先在左侧选择队列，例如高优先级、待人工复核或本浏览器草稿。",
                    "在案例列表选择一个 case，查看右侧概览、证据、问题和标签说明；整份导出的处理结果看左侧面板。",
                    "进入决策页填写复核人、复核日期、复核结论和理由。",
                    "确认根因、治理动作、后续排查目标，以及是否标记为回归测试样本候选。",
                    "后续处理流程只使用 JSON；CSV 只是给人打开表格查看和核对。",
                    "如需继续上次审阅，请导入之前从本页面导出的 JSON；页面会按 case_id 放回对应案例草稿。",
                ],
            },
            "glossary": {
                "title": "当前案例标签说明",
                "subtitle": "这里解释本案例出现的英文内部标签；导出数据仍保留原始代码。",
                "jumpTo": "查看位置",
                "code": "原始代码",
                "queueTags": "队列标签",
                "issueTypes": "诊断问题",
                "rootCauses": "建议根因",
                "followUpActions": "建议治理动作",
                "diagnostics": "诊断模块",
                "evidenceContext": "证据上下文",
                "gateBlockers": "准入阻断原因",
                "importErrors": "导入错误",
                "guardrails": "安全边界",
                "empty": "当前案例没有可解释标签。",
            },
        },
        "en-US": {
            "documentTitle": "Legal Risk Review Workbench",
            "brand": {
                "kicker": "Harvey-style RAG Governance",
                "title": "Legal Risk Review Workbench",
                "subtitle": "Evidence grounding diagnostics, manual review records, and the global process for the full review export.",
            },
            "sections": {"queues": "Queues", "status": "Batch summary", "globalPipeline": "Full-export result", "guide": "Operation Guide"},
            "topbar": {
                "title": "Manual Evidence Review",
                "subtitle": "Offline workspace generated from saved diagnostics.",
            },
            "language": {"label": "Language", "selectTitle": "Switch interface language"},
            "queues": {
                "all_cases": "All cases",
                "high_priority": "High priority",
                "pilot_batch": "Pilot batch",
                "awaiting_manual_review": "Pending review",
                "blocked_intake_gate": "Blocked gate",
                "with_local_draft": "Local drafts",
                "ready_for_export": "Ready drafts",
            },
            "tabs": {
                "overview": "Overview",
                "evidence": "Evidence",
                "questions": "Questions",
                "decision": "Decision",
                "glossary": "Glossary",
            },
            "sideStatus": {
                "gate": "Gate",
                "imported": "Imported",
                "rejected": "Rejected",
                "readyActions": "Ready actions",
                "localDrafts": "Local drafts",
            },
            "badges": {
                "gate": "Gate",
                "staticData": "Static data",
                "version": "Version",
                "ready": "ready",
                "missing": "missing",
            },
            "statusCodes": {
                "blocked": "blocked",
                "open": "open",
                "pending": "pending",
                "ready": "ready",
                "unknown": "unknown",
                "high": "high",
                "medium": "medium",
                "low": "low",
                "disallowed": "disallowed",
            },
            "kpis": {
                "cases": "Cases",
                "pending": "Pending",
                "highPriority": "High priority",
                "imported": "Imported",
                "validProposed": "Valid proposed",
                "readyActions": "Ready actions",
            },
            "caseQueue": {
                "title": "Case Queue",
                "searchPlaceholder": "Search case, topic, question, issue, queue, domain",
                "count": "{visible} visible / {total} total",
                "empty": "No matching cases",
            },
            "common": {"unknown": "unknown", "rootCauses": "Root causes", "true": "true", "false": "false"},
            "caseContext": {
                "caseTopic": "Case topic",
                "question": "Question under review",
                "scenario": "Risk scenario",
                "domains": "Domains",
                "expectedRiskTypes": "Expected risk types",
                "expectedActions": "Expected remediation actions",
                "source": "Source",
                "notAvailable": "No case topic is available from existing offline reports.",
                "sourceRagEvalReport": "RAG eval report",
                "sourceRagEvalCases": "Eval cases",
                "sourceScenarioRegistry": "Scenario registry",
            },
            "caseBadges": {
                "priority": "priority",
                "draftReady": "draft ready",
                "draftNeedsReview": "draft needs review",
                "exportReady": "export ready",
                "reviewPending": "review pending",
            },
            "exportStatus": {
                "never": "Not exported",
                "clean": "Exported",
                "dirty": "Unexported changes",
                "lastExportedAt": "Last exported",
                "updatedAt": "Last updated",
            },
            "detail": {"noCaseSelected": "No case selected", "noCaseData": "No case data"},
            "actions": {
                "clearDraft": "Clear draft",
                "saveDraft": "Save draft",
                "applyAiSuggestion": "Copy AI suggestion to draft",
                "clearAiSuggestion": "Clear AI suggestion",
                "exportJson": "Export ready drafts JSON",
                "exportCsv": "Download view-only CSV",
                "importReviewFile": "Import review file",
            },
            "draftSave": {
                "never": "Not manually saved yet",
                "saved": "Saved",
                "dirty": "Unmanually saved updates",
                "savedAt": "Last saved {time}",
                "autoSavedHint": "Inputs are auto-stored locally; Save records this draft explicitly.",
            },
            "reviewImport": {
                "statusLabel": "Page import",
                "never": "No draft import yet",
                "lastImported": "{imported} drafts imported, {cleared} old drafts cleared, {unknown} unmatched, {duplicate} duplicate, {skipped} empty",
                "lastImportedWithSuggestions": "{imported} drafts imported, {suggestions} AI suggestions loaded, {cleared} old drafts cleared, {unknown} unmatched, {duplicate} duplicate, {skipped} empty",
                "dialogTitle": "Import review file",
                "success": "Import completed: imported drafts replaced old local drafts so stale drafts cannot mix into the next export.",
                "successWithSuggestions": "Rows were matched by case_id; AI prefills were loaded only as suggestions, not manual decisions.",
                "replaceMode": "Real review-draft imports clear old local drafts first; AI suggestions stay in the suggestion panel.",
                "error": "Import failed: {message}",
                "invalidJson": "The JSON is invalid or is not a filled manual review workbench.",
                "invalidCsv": "The CSV is invalid or missing case_id.",
                "unsupportedFile": "Please import a .json review file exported by this page. CSV is view-only and is not accepted for formal import.",
                "noRows": "The file has no review rows to import.",
            },
            "exportPreview": {
                "ready": "This export will include {ready} ready drafts: {cases}",
                "blocked": "{blocked} incomplete drafts will not be exported.",
                "none": "No drafts are ready to export. Fill required fields first.",
                "confirmJson": "Export these drafts as JSON?",
                "confirmCsv": "Download a view-only CSV? CSV is for spreadsheet review only; use JSON for continued review or downstream processing.",
            },
            "overview": {"emptyDiagnostic": "No diagnostic summary", "rootCauses": "Root causes"},
            "originalOutput": {
                "title": "Original LLM output",
                "subtitle": "Use this to compare the prior answer against evidence and diagnostics; this is read from the saved eval report, not generated by this page.",
                "confidence": "Confidence",
                "source": "Source",
                "missing": "No original LLM output is available in saved offline reports.",
            },
            "evidence": {
                "missing_final_expected": "Missing final expected",
                "missing_scenario_core": "Missing scenario core",
                "lost_evidence": "Lost evidence",
                "final_evidence": "Final evidence",
                "source": "Source",
                "article": "Article",
                "content": "Content",
                "empty": "No evidence context",
            },
            "questions": {
                "title": "Suggested review questions",
                "empty": "No questions",
                "original": "Original question",
            },
            "decision": {
                "readyNotice": "Draft is ready for offline export.",
                "statusPrefix": "Draft status: ",
                "summaryTitle": "Review decision summary",
                "summarySubtitle": "Read the case topic, evidence, and diagnostic before deciding whether the quality signal is valid.",
                "authorityNoticeTitle": "Manual form is authoritative",
                "authorityNotice": "Only the manual form below creates a review decision. Reference materials, prescreen signals, and AI references are never exported as decisions automatically.",
                "aiSuggestionTitle": "AI-assisted suggestion",
                "aiSuggestionSubtitle": "This is a reference prefill, not a manual review decision; only copied and human-confirmed drafts are exported.",
                "aiSuggestionBadge": "AI suggestion",
                "aiSuggestionImportedAt": "Loaded at",
                "aiSuggestionDecision": "Suggested decision",
                "aiSuggestionRootCauses": "Suggested root causes",
                "aiSuggestionActions": "Suggested follow-up actions",
                "aiSuggestionFixture": "Suggested regression-test candidate",
                "aiSuggestionRationale": "Suggested rationale",
                "aiSuggestionNotes": "Suggested notes",
                "aiSuggestionNoReviewerCopy": "Copying the suggestion does not copy reviewer or review date; fill those yourself.",
                "aiSuggestionCopied": "AI suggestion copied. Please manually confirm reviewer, date, decision, and rationale.",
                "aiSuggestionHumanConfirm": "I have manually reviewed and confirmed this AI suggestion",
                "aiSuggestionHumanConfirmHint": "Only after this is checked can copied AI-suggestion conclusions be exported as complete manual drafts.",
                "pilotBatchTitle": "Pilot batch human judgment checklist",
                "pilotBatchSubtitle": "This is a read-only pilot packet from v0.4.7.8.15. It helps decide which cases to review first; it is not a manual conclusion and is never written as an exported draft.",
                "pilotBatchBadge": "Pilot batch",
                "pilotBatchRank": "Pilot rank",
                "pilotBatchSelectionScore": "Selection score",
                "pilotBatchWhySelected": "Why review first",
                "pilotBatchEvidenceIssues": "Evidence issue summary",
                "pilotBatchEvidenceToCheck": "Evidence to check",
                "pilotBatchFinalEvidence": "Final evidence chain",
                "pilotBatchMissingEvidence": "Missing or lost evidence",
                "pilotBatchPrescreen": "Prescreen reference",
                "pilotBatchAiSuggestion": "AI reference suggestion",
                "pilotBatchAllowedOptions": "Human judgment options",
                "pilotBatchInstruction": "Human instruction",
                "pilotBatchRequiredFields": "Minimum fields for later export",
                "pilotBatchOptionalFields": "Optional or conditional fields",
                "pilotBatchNotDecision": "Reading this checklist is not a completed review; you must personally fill reviewer, date, decision, and rationale below before anything can export.",
                "pilotBatchReviewed": "I have read the pilot checklist (page marker only; not exported as a manual decision)",
                "pilotBatchNoReviewerCopy": "Prescreen and AI suggestions help interpretation only; they are not copied into reviewer_input_template automatically.",
                "pilotBatchHumanRequired": "Human confirmation required",
                "pilotBatchAdvisoryDecision": "Advisory decision",
                "pilotBatchAdvisoryRootCauses": "Advisory root causes",
                "pilotBatchAdvisoryActions": "Advisory follow-up actions",
                "pilotBatchAdvisoryFixture": "Advisory regression-test candidate",
                "pilotBatchRationale": "Advisory rationale",
                "pilotBatchNotes": "Advisory notes",
                "pilotReviewAssistTitle": "Pilot review assist",
                "pilotReviewAssistSubtitle": "This is a read-only aid generated by v0.4.7.8.17. It explains case topic, original LLM output, and evidence-support gaps; it is not a manual review decision.",
                "pilotReviewAssistBadge": "Review assist",
                "pilotReviewAssistNotDecision": "This panel only helps interpretation. It is never written into exported drafts and never replaces human judgment.",
                "pilotReviewAssistTendency": "Advisory tendency",
                "pilotReviewAssistSupport": "Evidence support status",
                "pilotReviewAssistSignals": "Assist signals",
                "pilotReviewAssistOriginalClaims": "Original LLM risks/actions",
                "pilotReviewAssistRisks": "Risk types",
                "pilotReviewAssistActions": "Remediation actions",
                "pilotReviewAssistFocusQuestions": "Questions to check",
                "pilotReviewAssistRationale": "Assist rationale",
                "pilotReviewAssistMissingEvidence": "Missing, scenario-core, or lost evidence examples",
                "workflowTitle": "Suggested review order",
                "workflowEvidence": "1. Confirm that the case topic, question, and evidence are about the same issue.",
                "workflowDecision": "2. Choose a decision and explain the legal/evidence reason.",
                "workflowGovernance": "3. Confirm root causes, follow-up actions, and regression-test candidacy.",
                "caseTopic": "Case topic",
                "mainDiagnostics": "Main diagnostics",
                "suggestedRootCauses": "Suggested root causes",
                "suggestedActions": "Suggested follow-up actions",
                "exportStatus": "Export status",
                "reviewerInfo": "Reviewer info",
                "conclusionSection": "Review conclusion and rationale",
                "rootCauseSection": "Root-cause judgment",
                "actionSection": "Follow-up actions",
                "governanceSection": "Governance notes",
                "originalCode": "Code",
                "chooseOne": "Choose one conclusion",
                "useOriginalCodeHint": "Exports still keep original codes for importer, diff, and validator compatibility.",
                "requiredBadge": "Required",
                "conditionalBadge": "Conditional",
                "optionalBadge": "Optional",
                "requiredHint": "Required for a usable review draft; missing values keep the draft from being ready.",
                "conditionalHint": "Required only when the decision confirms the diagnostic or scope adjustment.",
                "optionalHint": "Leave blank if unsure; this does not block draft export.",
                "reviewerInfoNote": "Record who made this manual judgment and when.",
                "conclusionSectionNote": "Answer the core question: valid, partly valid, rejected, insufficient information, or deferred.",
                "rootCauseSectionNote": "If the diagnostic is valid, select the causes; if rejected, record what is rejected.",
                "actionSectionNote": "Select only actions that should enter governance review; this page does not change retrieval, prompts, or eval cases.",
                "governanceSectionNote": "Add notes and mark whether the case is worth preparing as a future regression-test candidate.",
                "reviewer": "Reviewer",
                "reviewerHelp": "Use your name or team code.",
                "reviewedAt": "Reviewed at",
                "reviewedAtPlaceholder": "YYYY-MM-DD",
                "reviewedAtHelp": "Use YYYY-MM-DD, for example 2026-05-11.",
                "decision": "Decision",
                "selectDecision": "Select decision",
                "decisionHelp": "If unsure, choose insufficient information or defer.",
                "confirmedRootCauses": "Confirmed root causes",
                "confirmedRootCausesHelp": "When confirming the issue or scope adjustment, select at least one main cause.",
                "rejectedRootCauses": "Rejected root causes",
                "rejectedRootCausesHelp": "Select causes you believe are invalid; leave blank if unsure.",
                "confirmedFollowUpActions": "Confirmed follow-up actions",
                "confirmedFollowUpActionsHelp": "Select only actions you want the governance chain to consider.",
                "proposedChangeTargets": "Change targets for governance review",
                "proposedChangeTargetsPlaceholder": "Example: metadata_chunking | source_index; use | between targets",
                "proposedChangeTargetsHelp": "Leave blank if the engineering target is unclear.",
                "fixtureCandidate": "Regression-test candidate",
                "fixtureCandidateHint": "This only marks future test-sample candidacy; it does not write to eval cases.",
                "rationale": "Rationale",
                "rationalePlaceholder": "Explain how the evidence, case topic, and diagnostic relate; note missing information if any.",
                "rationaleHelp": "Plain-language reasoning is enough; engineering terminology is not required.",
                "notes": "Notes",
                "notesPlaceholder": "Add follow-up review notes if needed.",
                "notesHelp": "Use this for questions, follow-up reminders, or handoff notes.",
            },
            "draftIssues": {
                "empty_draft": "empty draft",
                "missing_reviewer": "missing reviewer",
                "missing_reviewed_at": "missing reviewed_at",
                "missing_decision": "missing decision",
                "missing_rationale": "missing rationale",
                "missing_confirmed_root_cause": "missing confirmed root cause",
                "missing_ai_suggestion_confirmation": "copied AI suggestion still needs manual confirmation",
                "prohibited_change_target": "prohibited change target",
            },
            "pipeline": {
                "title": "Full-export result",
                "subtitle": "This is the processing result for the full exported review JSON, not the currently selected case.",
                "import": "Imported review records",
                "diff": "Checked changes",
                "validation": "Checked record completeness",
                "promotion": "Generated follow-up actions",
                "closeout": "Allowed for follow-up governance",
                "importValue": "{imported} records imported / {rejected} records rejected",
                "diffValue": "{changed} cases changed / {blocked} cases blocked",
                "diffValueNoBlockers": "{changed} cases changed / no blockers",
                "validationValue": "{valid} records valid / {invalid} records invalid / {pending} records pending",
                "promotionValue": "{candidates} candidates / {ready} follow-up actions",
                "states": {"ready": "ready", "blocked": "blocked", "pending": "pending"},
            },
            "guide": {
                "steps": [
                    "Choose a queue on the left, such as high priority, pending review, or local drafts.",
                    "Select a case in the list and inspect its overview, evidence, questions, and glossary; the full-export process status is in the left global panel.",
                    "Open Decision and fill reviewer, reviewed_at, decision, and rationale.",
                    "Confirm root causes, follow-up actions, proposed change targets, and regression-test candidacy.",
                    "Use JSON for downstream processing. CSV is only for spreadsheet viewing and manual cross-checking.",
                    "To continue prior review work, import a JSON file exported by this page; matching case drafts are restored by case_id.",
                ],
            },
            "glossary": {
                "title": "Current Case Glossary",
                "subtitle": "This explains internal English tags used by the current case; exports still keep the original codes.",
                "jumpTo": "Go to",
                "code": "Code",
                "queueTags": "Queue tags",
                "issueTypes": "Diagnostic issues",
                "rootCauses": "Suggested root causes",
                "followUpActions": "Suggested follow-up actions",
                "diagnostics": "Diagnostics",
                "evidenceContext": "Evidence context",
                "gateBlockers": "Gate blockers",
                "importErrors": "Import errors",
                "guardrails": "Guardrails",
                "empty": "No explainable tags for this case.",
            },
        },
    },
}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def source_meta(path: Path, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": str(path),
        "present": path.exists(),
        "version": data.get("version"),
        "scope": data.get("scope"),
    }


def as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return [item for item in value if item not in (None, "")]
    if value in (None, ""):
        return []
    return [value]


def text_or_empty(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def strip_read_only_report_dangerous_keys(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: strip_read_only_report_dangerous_keys(item)
            for key, item in value.items()
            if key not in READ_ONLY_REPORT_DANGEROUS_KEYS
        }
    if isinstance(value, list):
        return [strip_read_only_report_dangerous_keys(item) for item in value]
    return copy.deepcopy(value)


def extract_rag_eval_reports(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    reports = report.get("reports")
    if not isinstance(reports, list):
        return {}
    return {
        text_or_empty(item.get("id") or item.get("case_id")): item
        for item in reports
        if isinstance(item, dict) and text_or_empty(item.get("id") or item.get("case_id"))
    }


def extract_original_llm_outputs(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    reports = extract_rag_eval_reports(report)
    outputs: dict[str, dict[str, Any]] = {}
    for case_id, item in reports.items():
        answer = text_or_empty(item.get("answer") or item.get("generated_answer") or item.get("response"))
        if not answer:
            continue
        outputs[case_id] = {
            "answer": answer,
            "answer_confidence": item.get("answer_confidence"),
            "source": "rag_eval_report",
        }
    return outputs


def extract_eval_cases(cases_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    cases = cases_data.get("cases")
    if not isinstance(cases, list):
        return {}
    return {
        text_or_empty(item.get("id") or item.get("case_id")): item
        for item in cases
        if isinstance(item, dict) and text_or_empty(item.get("id") or item.get("case_id"))
    }


def extract_scenario_contexts(registry: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    contexts: dict[str, list[dict[str, Any]]] = {}
    scenarios = registry.get("scenarios")
    if not isinstance(scenarios, list):
        return contexts
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            continue
        for case_id in as_list(scenario.get("eval_case_ids")):
            normalized_case_id = text_or_empty(case_id)
            if not normalized_case_id:
                continue
            contexts.setdefault(normalized_case_id, []).append(
                {
                    "scenario_id": text_or_empty(scenario.get("scenario_id")),
                    "domain": text_or_empty(scenario.get("domain")),
                    "description": text_or_empty(scenario.get("description")),
                    "risk_level": text_or_empty(scenario.get("risk_level")),
                    "risk_types": as_list(scenario.get("risk_types")),
                    "required_actions": as_list(scenario.get("required_actions")),
                    "legal_terms": as_list(scenario.get("legal_terms")),
                }
            )
    return contexts


def infer_case_topic(case_id: str, question: str, scenarios: list[dict[str, Any]]) -> str:
    for scenario in scenarios:
        description = text_or_empty(scenario.get("description"))
        if description:
            return description
    if question:
        return question.rstrip("？?。.")
    return case_id


def has_case_context_signal(context: dict[str, Any]) -> bool:
    sources = context.get("sources") if isinstance(context.get("sources"), dict) else {}
    return bool(
        text_or_empty(context.get("question"))
        or as_list(context.get("expected_risk_types"))
        or as_list(context.get("expected_actions"))
        or context.get("scenario_contexts")
        or any(sources.values())
    )


def case_context_for(
    item: dict[str, Any],
    rag_reports: dict[str, dict[str, Any]],
    eval_cases: dict[str, dict[str, Any]],
    scenario_contexts: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    case_id = text_or_empty(item.get("case_id"))
    eval_case = eval_cases.get(case_id, {})
    rag_report = rag_reports.get(case_id, {})
    scenarios = scenario_contexts.get(case_id, [])
    question = text_or_empty(eval_case.get("question") or rag_report.get("question"))
    expected_risk_types = as_list(eval_case.get("expected_risk_types") or rag_report.get("risk_types"))
    expected_actions = as_list(eval_case.get("expected_actions") or rag_report.get("recommended_actions"))
    expected_risk_level = text_or_empty(eval_case.get("expected_risk_level") or rag_report.get("risk_level"))
    return {
        "case_id": case_id,
        "case_topic": infer_case_topic(case_id, question, scenarios),
        "question": question,
        "expected_risk_types": expected_risk_types,
        "expected_actions": expected_actions,
        "expected_risk_level": expected_risk_level,
        "scenario_contexts": scenarios,
        "sources": {
            "rag_eval_report": bool(rag_report),
            "rag_eval_cases": bool(eval_case),
            "scenario_registry": bool(scenarios),
        },
    }


def enrich_workbench_with_case_context(
    workbench: dict[str, Any],
    rag_eval_report: dict[str, Any],
    rag_eval_cases: dict[str, Any],
    scenario_registry: dict[str, Any],
) -> dict[str, Any]:
    enriched = copy.deepcopy(workbench)
    items = enriched.get("workbench_items")
    if not isinstance(items, list):
        return enriched
    rag_reports = extract_rag_eval_reports(rag_eval_report)
    eval_cases = extract_eval_cases(rag_eval_cases)
    scenario_contexts = extract_scenario_contexts(scenario_registry)
    for item in items:
        if not isinstance(item, dict):
            continue
        item["case_context"] = case_context_for(item, rag_reports, eval_cases, scenario_contexts)
    enriched.setdefault("summary", {})["items_with_case_context"] = sum(
        1
        for item in items
        if isinstance(item, dict) and has_case_context_signal(item.get("case_context") or {})
    )
    return enriched


def pilot_batch_cases_by_id(pilot_batch_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if pilot_batch_report.get("schema_kind") != "advisory_pilot_packet":
        return {}
    if pilot_batch_report.get("advisory_packet_only") is not True:
        return {}
    if pilot_batch_report.get("contains_completed_manual_decisions") is True:
        return {}
    summary = pilot_batch_report.get("summary")
    if isinstance(summary, dict) and summary.get("completed_manual_decisions", 0) not in (0, None):
        return {}
    cases = pilot_batch_report.get("pilot_cases")
    if not isinstance(cases, list):
        return {}
    by_case: dict[str, dict[str, Any]] = {}
    for case in cases:
        if not isinstance(case, dict):
            continue
        case_id = text_or_empty(case.get("case_id"))
        if not case_id:
            continue
        advisory_case = strip_read_only_report_dangerous_keys(case)
        by_case[case_id] = advisory_case
    return by_case


def pilot_batch_summary(
    pilot_batch_report: dict[str, Any],
    matched_case_ids: set[str] | None = None,
) -> dict[str, Any]:
    summary = pilot_batch_report.get("summary") if isinstance(pilot_batch_report.get("summary"), dict) else {}
    cases_by_id = pilot_batch_cases_by_id(pilot_batch_report)
    matched_case_ids = matched_case_ids or set()
    unmatched_case_ids = sorted(set(cases_by_id) - matched_case_ids)
    return {
        "schema_kind": pilot_batch_report.get("schema_kind"),
        "advisory_packet_only": pilot_batch_report.get("advisory_packet_only") is True,
        "contains_completed_manual_decisions": pilot_batch_report.get("contains_completed_manual_decisions") is True,
        "pilot_case_count": summary.get("pilot_case_count", len(cases_by_id)),
        "matched_workbench_cases": len(matched_case_ids),
        "unmatched_case_ids": unmatched_case_ids,
        "human_confirmation_required_cases": summary.get("human_confirmation_required_cases", 0),
        "advisory_ai_suggestion_cases": summary.get("advisory_ai_suggestion_cases", 0),
        "completed_manual_decisions": summary.get("completed_manual_decisions", 0),
        "promotion_candidates": summary.get("promotion_candidates", 0),
        "ready_action_candidates": summary.get("ready_action_candidates", 0),
    }


def enrich_workbench_with_pilot_batch(
    workbench: dict[str, Any],
    pilot_batch_report: dict[str, Any],
) -> dict[str, Any]:
    cases_by_id = pilot_batch_cases_by_id(pilot_batch_report)
    if not cases_by_id:
        enriched = copy.deepcopy(workbench)
        enriched.setdefault("summary", {})["pilot_batch_cases"] = 0
        return enriched
    enriched = copy.deepcopy(workbench)
    items = enriched.get("workbench_items")
    if not isinstance(items, list):
        return enriched
    matched_case_ids: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        case_id = text_or_empty(item.get("case_id"))
        pilot_case = cases_by_id.get(case_id)
        if not pilot_case:
            continue
        matched_case_ids.add(case_id)
        item["pilot_batch"] = {
            "in_pilot_batch": True,
            "case_id": case_id,
            "rank": pilot_case.get("rank"),
            "selection_score": pilot_case.get("selection_score"),
            "case_topic": pilot_case.get("case_topic"),
            "question": pilot_case.get("question"),
            "original_llm_output_excerpt": pilot_case.get("original_llm_output_excerpt"),
            "why_selected": as_list(pilot_case.get("why_selected")),
            "evidence_issue_summary": pilot_case.get("evidence_issue_summary") if isinstance(pilot_case.get("evidence_issue_summary"), dict) else {},
            "evidence_to_check": pilot_case.get("evidence_to_check") if isinstance(pilot_case.get("evidence_to_check"), dict) else {},
            "prescreen_advice": pilot_case.get("prescreen_advice") if isinstance(pilot_case.get("prescreen_advice"), dict) else {},
            "ai_suggestion": pilot_case.get("ai_suggestion") if isinstance(pilot_case.get("ai_suggestion"), dict) else {},
            "reviewer_decision_needed": pilot_case.get("reviewer_decision_needed") if isinstance(pilot_case.get("reviewer_decision_needed"), dict) else {},
            "fields_not_written": as_list(pilot_case.get("fields_not_written")),
            "advisory_only": True,
            "not_a_reviewer_decision": True,
        }
        tags = as_list(item.get("queue_tags"))
        if "pilot_batch_review" not in tags:
            item["queue_tags"] = [*tags, "pilot_batch_review"]
    enriched.setdefault("summary", {})["pilot_batch_cases"] = len(matched_case_ids)
    enriched["summary"]["pilot_batch_unmatched_case_ids"] = sorted(set(cases_by_id) - matched_case_ids)
    return enriched


def pilot_review_assist_cases_by_id(pilot_review_assist_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if pilot_review_assist_report.get("schema_kind") != "advisory_pilot_case_review_assist":
        return {}
    if pilot_review_assist_report.get("advisory_packet_only") is not True:
        return {}
    if pilot_review_assist_report.get("contains_completed_manual_decisions") is True:
        return {}
    summary = pilot_review_assist_report.get("summary")
    if isinstance(summary, dict) and summary.get("completed_manual_decisions", 0) not in (0, None):
        return {}
    cases = pilot_review_assist_report.get("assisted_cases")
    if not isinstance(cases, list):
        return {}
    by_case: dict[str, dict[str, Any]] = {}
    for case in cases:
        if not isinstance(case, dict):
            continue
        case_id = text_or_empty(case.get("case_id"))
        if not case_id:
            continue
        advisory_case = strip_read_only_report_dangerous_keys(case)
        by_case[case_id] = advisory_case
    return by_case


def pilot_review_assist_summary(
    pilot_review_assist_report: dict[str, Any],
    matched_case_ids: set[str] | None = None,
) -> dict[str, Any]:
    summary = pilot_review_assist_report.get("summary") if isinstance(pilot_review_assist_report.get("summary"), dict) else {}
    cases_by_id = pilot_review_assist_cases_by_id(pilot_review_assist_report)
    matched_case_ids = matched_case_ids or set()
    return {
        "schema_kind": pilot_review_assist_report.get("schema_kind"),
        "advisory_packet_only": pilot_review_assist_report.get("advisory_packet_only") is True,
        "contains_completed_manual_decisions": pilot_review_assist_report.get("contains_completed_manual_decisions") is True,
        "assisted_cases": summary.get("assisted_cases", len(cases_by_id)),
        "matched_workbench_cases": len(matched_case_ids),
        "unmatched_case_ids": sorted(set(cases_by_id) - matched_case_ids),
        "needs_user_confirmation_cases": summary.get("needs_user_confirmation_cases", 0),
        "high_attention_manual_review_cases": summary.get("high_attention_manual_review_cases", 0),
        "completed_manual_decisions": summary.get("completed_manual_decisions", 0),
        "promotion_candidates": summary.get("promotion_candidates", 0),
        "ready_action_candidates": summary.get("ready_action_candidates", 0),
    }


def enrich_workbench_with_pilot_review_assist(
    workbench: dict[str, Any],
    pilot_review_assist_report: dict[str, Any],
) -> dict[str, Any]:
    cases_by_id = pilot_review_assist_cases_by_id(pilot_review_assist_report)
    if not cases_by_id:
        enriched = copy.deepcopy(workbench)
        enriched.setdefault("summary", {})["pilot_review_assist_cases"] = 0
        return enriched
    enriched = copy.deepcopy(workbench)
    items = enriched.get("workbench_items")
    if not isinstance(items, list):
        return enriched
    matched_case_ids: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        case_id = text_or_empty(item.get("case_id"))
        assist_case = cases_by_id.get(case_id)
        if not assist_case:
            continue
        matched_case_ids.add(case_id)
        assessment = assist_case.get("evidence_support_assessment") if isinstance(assist_case.get("evidence_support_assessment"), dict) else {}
        advisory = assist_case.get("advisory_review_assist") if isinstance(assist_case.get("advisory_review_assist"), dict) else {}
        claims = assist_case.get("original_llm_claims") if isinstance(assist_case.get("original_llm_claims"), dict) else {}
        item["pilot_review_assist"] = {
            "in_pilot_review_assist": True,
            "case_id": case_id,
            "rank": assist_case.get("rank"),
            "plain_case_brief": assist_case.get("plain_case_brief"),
            "advisory_tendency": advisory.get("advisory_tendency"),
            "advisory_tendency_label": advisory.get("advisory_tendency_label"),
            "support_status": assessment.get("support_status"),
            "support_status_label": assessment.get("support_status_label"),
            "plain_assessment": assessment.get("plain_assessment"),
            "detected_assist_signals": as_list(assessment.get("detected_assist_signals")),
            "focus_questions_for_user": as_list(advisory.get("focus_questions_for_user")),
            "advisory_rationale": as_list(advisory.get("advisory_rationale")),
            "risk_types": as_list(claims.get("risk_types")),
            "recommended_actions": as_list(claims.get("recommended_actions")),
            "missing_expected_evidence_examples": as_list(assessment.get("missing_expected_evidence_examples")),
            "missing_scenario_core_evidence_examples": as_list(assessment.get("missing_scenario_core_evidence_examples")),
            "lost_before_final_evidence_examples": as_list(assessment.get("lost_before_final_evidence_examples")),
            "user_confirmation_required": advisory.get("user_confirmation_required") is True,
            "not_a_reviewer_decision": advisory.get("not_a_reviewer_decision") is True,
            "advisory_only": True,
        }
        tags = as_list(item.get("queue_tags"))
        if "pilot_review_assist" not in tags:
            item["queue_tags"] = [*tags, "pilot_review_assist"]
    enriched.setdefault("summary", {})["pilot_review_assist_cases"] = len(matched_case_ids)
    enriched["summary"]["pilot_review_assist_unmatched_case_ids"] = sorted(set(cases_by_id) - matched_case_ids)
    return enriched


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    contract_report = load_json(args.contract_report)
    workbench = load_json(args.workbench)
    intake_contract = load_json(args.intake_contract)
    progress_report = load_json(args.progress_report)
    governance_report = load_json(args.governance_report)
    import_report = load_json(args.import_report)
    diff_report = load_json(args.diff_report)
    validation_report = load_json(args.validation_report)
    promotion_report = load_json(args.promotion_report)
    closeout_report = load_json(args.closeout_report)
    pilot_batch_report = load_json(args.pilot_batch_report)
    pilot_review_assist_report = strip_read_only_report_dangerous_keys(
        load_json(args.pilot_review_assist_report)
    )
    rag_eval_report = load_json(args.rag_eval_report)
    rag_eval_cases = load_json(args.rag_eval_cases)
    scenario_registry = load_json(args.scenario_registry)
    workbench = enrich_workbench_with_case_context(workbench, rag_eval_report, rag_eval_cases, scenario_registry)
    workbench = enrich_workbench_with_pilot_batch(workbench, pilot_batch_report)
    workbench = enrich_workbench_with_pilot_review_assist(workbench, pilot_review_assist_report)
    original_llm_outputs = extract_original_llm_outputs(rag_eval_report)

    workbench_summary = workbench.get("summary") if isinstance(workbench.get("summary"), dict) else {}
    closeout_summary = closeout_report.get("summary") if isinstance(closeout_report.get("summary"), dict) else {}
    progress_summary = progress_report.get("summary") if isinstance(progress_report.get("summary"), dict) else {}

    return {
        "version": VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "guardrails": GUARDRAILS,
        "sources": {
            "contract_report": source_meta(args.contract_report, contract_report),
            "workbench": source_meta(args.workbench, workbench),
            "intake_contract": source_meta(args.intake_contract, intake_contract),
            "progress_report": source_meta(args.progress_report, progress_report),
            "governance_report": source_meta(args.governance_report, governance_report),
            "import_report": source_meta(args.import_report, import_report),
            "diff_report": source_meta(args.diff_report, diff_report),
            "validation_report": source_meta(args.validation_report, validation_report),
            "promotion_report": source_meta(args.promotion_report, promotion_report),
            "closeout_report": source_meta(args.closeout_report, closeout_report),
            "pilot_batch_report": source_meta(args.pilot_batch_report, pilot_batch_report),
            "pilot_review_assist_report": source_meta(args.pilot_review_assist_report, pilot_review_assist_report),
            "rag_eval_report": source_meta(args.rag_eval_report, rag_eval_report),
            "rag_eval_cases": source_meta(args.rag_eval_cases, rag_eval_cases),
            "scenario_registry": source_meta(args.scenario_registry, scenario_registry),
        },
        "ui": UI_CONFIG,
        "summary": {
            "workbench_items": workbench_summary.get("total_workbench_items", 0),
            "pending_items": workbench_summary.get("pending_items", 0),
            "high_priority_items": workbench_summary.get("high_priority_items", 0),
            "gate_status": closeout_summary.get("gate_status", "unknown"),
            "gate_blockers": closeout_summary.get("blockers") or [],
            "completed_cases": progress_summary.get("completed_cases", 0),
            "pending_cases": progress_summary.get("pending_cases", 0),
            "ready_for_static_review": bool(workbench.get("workbench_items")),
            "original_llm_output_cases": len(original_llm_outputs),
            "pilot_batch_cases": workbench_summary.get("pilot_batch_cases", 0),
            "pilot_batch_advisory_only": pilot_batch_report.get("advisory_packet_only") is True,
            "pilot_batch_completed_decisions": (pilot_batch_report.get("summary") or {}).get("completed_manual_decisions", 0),
            "pilot_review_assist_cases": workbench_summary.get("pilot_review_assist_cases", 0),
            "pilot_review_assist_advisory_only": pilot_review_assist_report.get("advisory_packet_only") is True,
            "pilot_review_assist_completed_decisions": (pilot_review_assist_report.get("summary") or {}).get("completed_manual_decisions", 0),
        },
        "contract_report": contract_report,
        "pilot_batch_report": pilot_batch_report,
        "pilot_batch": pilot_batch_summary(
            pilot_batch_report,
            {
                text_or_empty(item.get("case_id"))
                for item in workbench.get("workbench_items", [])
                if isinstance(item, dict) and isinstance(item.get("pilot_batch"), dict)
            },
        ),
        "pilot_review_assist_report": pilot_review_assist_report,
        "pilot_review_assist": pilot_review_assist_summary(
            pilot_review_assist_report,
            {
                text_or_empty(item.get("case_id"))
                for item in workbench.get("workbench_items", [])
                if isinstance(item, dict) and isinstance(item.get("pilot_review_assist"), dict)
            },
        ),
        "original_llm_outputs": original_llm_outputs,
        "workbench": workbench,
        "intake_contract": intake_contract,
        "progress_report": progress_report,
        "governance_report": governance_report,
        "import_report": import_report,
        "diff_report": diff_report,
        "validation_report": validation_report,
        "promotion_report": promotion_report,
        "closeout_report": closeout_report,
    }


def html_document(payload: dict[str, Any]) -> str:
    payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return HTML_TEMPLATE.replace("__WORKBENCH_DATA__", payload_json)


HTML_TEMPLATE = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Legal Risk Manual Review Workbench</title>
  <style>
    :root {
      --page-bg: #f7f8fc;
      --surface: #ffffff;
      --surface-soft: #f8fafc;
      --surface-strong: #edf6f5;
      --text: #1f2937;
      --muted: #556274;
      --faint: #7b8798;
      --primary: #0f766e;
      --primary-ink: #084f49;
      --blue: #2563eb;
      --warning: #d58918;
      --danger: #e14b5a;
      --success: #22a866;
      --border: rgba(129, 140, 160, 0.28);
      --shadow: 0 18px 48px rgba(31, 41, 55, 0.08);
      --radius: 8px;
      --font: Inter, "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
      --mono: "JetBrains Mono", Consolas, monospace;
    }

    * { box-sizing: border-box; }
    html {
      height: 100%;
    }
    body {
      margin: 0;
      min-height: 100vh;
      height: 100vh;
      overflow: hidden;
      background: var(--page-bg);
      color: var(--text);
      font-family: var(--font);
      letter-spacing: 0;
    }

    button, input, select, textarea { font: inherit; }
    button { cursor: pointer; }
    .app-shell {
      display: grid;
      grid-template-columns: minmax(240px, 288px) minmax(0, 1fr);
      grid-template-rows: minmax(0, 1fr);
      min-height: 0;
      height: 100vh;
      overflow: hidden;
    }

    .sidebar {
      min-height: 0;
      height: 100%;
      max-height: 100vh;
      padding: 22px 18px;
      border-right: 1px solid var(--border);
      background: #fbfcff;
      display: flex;
      flex-direction: column;
      gap: 18px;
      overflow: auto;
    }

    .brand {
      display: grid;
      gap: 8px;
      padding: 16px;
      border: 1px solid var(--border);
      border-radius: var(--radius);
      background: var(--surface);
      box-shadow: var(--shadow);
    }
    .brand-kicker {
      color: var(--primary);
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
    }
    .brand h1 {
      margin: 0;
      font-size: 20px;
      line-height: 1.25;
    }
    .brand p {
      margin: 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.55;
    }

    .nav-section, .sidebar-panel {
      display: grid;
      gap: 8px;
    }
    .section-title {
      color: var(--faint);
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
    }
    .nav-button {
      width: 100%;
      border: 1px solid transparent;
      border-radius: var(--radius);
      background: transparent;
      color: var(--text);
      padding: 10px 12px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      text-align: left;
    }
    .nav-button:hover, .nav-button.active {
      border-color: rgba(15, 118, 110, 0.25);
      background: var(--surface-strong);
      color: var(--primary-ink);
    }
    .nav-button span:first-child {
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .count {
      min-width: 28px;
      border-radius: 999px;
      padding: 2px 8px;
      background: rgba(37, 99, 235, 0.1);
      color: var(--blue);
      font-size: 12px;
      font-weight: 700;
      text-align: center;
    }

    .main {
      min-width: 0;
      min-height: 0;
      height: 100%;
      max-height: 100vh;
      padding: 22px;
      display: grid;
      grid-template-rows: auto auto minmax(0, 1fr);
      gap: 16px;
      overflow: hidden;
    }
    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }
    .topbar h2 {
      margin: 0;
      font-size: 24px;
      line-height: 1.2;
    }
    .topbar-subtitle {
      margin: 4px 0 0;
      color: var(--muted);
      font-size: 13px;
    }
    .badges {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      min-height: 28px;
      padding: 5px 10px;
      border: 1px solid var(--border);
      border-radius: 999px;
      background: var(--surface);
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      white-space: nowrap;
    }
    .badge.blocked { color: #9a5b00; background: #fff8e7; border-color: rgba(213, 137, 24, 0.34); }
    .badge.ready { color: #0b7a48; background: #edfff5; border-color: rgba(34, 168, 102, 0.28); }
    .badge.danger { color: #b72d3a; background: #fff1f3; border-color: rgba(225, 75, 90, 0.28); }
    .language-control {
      min-height: 32px;
      border: 1px solid var(--border);
      border-radius: 999px;
      background: var(--surface);
      color: var(--muted);
      padding: 3px 4px 3px 10px;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      font-weight: 800;
      white-space: nowrap;
    }
    .language-select {
      min-height: 24px;
      border: 0;
      border-radius: 999px;
      background: var(--surface-soft);
      color: var(--text);
      padding: 3px 8px;
      font-size: 12px;
      font-weight: 800;
      outline: none;
    }
    .language-select:focus {
      box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.1);
    }

    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(6, minmax(120px, 1fr));
      gap: 10px;
    }
    .kpi {
      min-height: 82px;
      padding: 14px;
      border: 1px solid var(--border);
      border-radius: var(--radius);
      background: var(--surface);
      display: grid;
      align-content: space-between;
    }
    .kpi-value {
      font-size: 26px;
      line-height: 1;
      font-weight: 800;
    }
    .kpi-label {
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
    }

    .workspace {
      min-height: 0;
      height: 100%;
      display: grid;
      grid-template-columns: minmax(330px, 0.42fr) minmax(0, 0.58fr);
      gap: 16px;
      overflow: hidden;
    }
    .panel {
      min-width: 0;
      min-height: 0;
      height: 100%;
      border: 1px solid var(--border);
      border-radius: var(--radius);
      background: var(--surface);
      box-shadow: var(--shadow);
      display: grid;
      overflow: hidden;
    }
    .queue-panel {
      grid-template-rows: auto auto auto minmax(0, 1fr);
    }
    .detail-panel {
      grid-template-rows: auto auto minmax(0, 1fr);
    }
    .panel-header {
      min-height: 62px;
      padding: 14px 16px;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
    }
    .panel-header h3 {
      margin: 0;
      font-size: 15px;
    }
    .panel-header p {
      margin: 3px 0 0;
      color: var(--muted);
      font-size: 12px;
    }
    .search-row {
      padding: 12px 14px;
      border-bottom: 1px solid var(--border);
    }
    .import-row {
      padding: 10px 14px;
      border-bottom: 1px solid var(--border);
      display: grid;
      gap: 8px;
      background: var(--surface-soft);
    }
    .import-row .button {
      width: fit-content;
    }
    .hidden-file-input {
      position: absolute;
      width: 1px;
      height: 1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      white-space: nowrap;
    }
    .import-summary {
      display: none;
      border: 1px solid rgba(15, 118, 110, 0.18);
      border-radius: var(--radius);
      background: #f3fbf9;
      color: var(--primary-ink);
      padding: 8px 10px;
      font-size: 12px;
      line-height: 1.45;
      overflow-wrap: anywhere;
    }
    .import-summary.visible {
      display: block;
    }
    .import-summary.error {
      border-color: rgba(185, 28, 28, 0.28);
      background: #fff3f4;
      color: #9b2530;
    }
    .search-input, .field-input, .field-select, .field-textarea {
      width: 100%;
      border: 1px solid var(--border);
      border-radius: var(--radius);
      background: #ffffff;
      color: var(--text);
      outline: none;
    }
    .search-input, .field-input, .field-select {
      min-height: 38px;
      padding: 8px 10px;
    }
    .field-textarea {
      min-height: 96px;
      resize: vertical;
      padding: 9px 10px;
      line-height: 1.45;
    }
    .search-input:focus, .field-input:focus, .field-select:focus, .field-textarea:focus {
      border-color: rgba(15, 118, 110, 0.62);
      box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.1);
    }

    .case-list {
      min-height: 0;
      max-height: none;
      overflow: auto;
      padding: 10px;
      display: grid;
      gap: 8px;
    }
    .case-row {
      width: 100%;
      border: 1px solid var(--border);
      border-radius: var(--radius);
      background: var(--surface);
      padding: 12px;
      text-align: left;
      display: grid;
      gap: 8px;
    }
    .case-row:hover, .case-row.active {
      border-color: rgba(15, 118, 110, 0.45);
      background: #fbfffe;
    }
    .case-title {
      display: flex;
      gap: 10px;
      align-items: flex-start;
      justify-content: space-between;
      min-width: 0;
    }
    .case-title strong {
      min-width: 0;
      overflow-wrap: anywhere;
      font-family: var(--mono);
      font-size: 12px;
      line-height: 1.4;
    }
    .case-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .case-topic {
      margin: 0;
      color: var(--text);
      font-size: 12px;
      font-weight: 800;
      line-height: 1.45;
      overflow-wrap: anywhere;
    }
    .case-question {
      margin: 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
      overflow-wrap: anywhere;
    }
    .pill {
      max-width: 100%;
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      border-radius: 999px;
      padding: 3px 8px;
      background: var(--surface-soft);
      color: var(--muted);
      border: 1px solid var(--border);
      font-size: 11px;
      font-weight: 700;
      overflow-wrap: anywhere;
    }
    .pill.explained {
      cursor: help;
      text-align: left;
    }
    .pill-code {
      color: var(--faint);
      font-family: var(--mono);
      font-weight: 700;
    }
    .pill.high, .pill.priority { color: #b72d3a; background: #fff1f3; border-color: rgba(225, 75, 90, 0.22); }
    .pill.pending { color: #9a5b00; background: #fff8e7; border-color: rgba(213, 137, 24, 0.26); }
    .pill.ready { color: #0b7a48; background: #edfff5; border-color: rgba(34, 168, 102, 0.26); }

    .detail-body {
      min-height: 0;
      max-height: none;
      overflow: auto;
    }
    .detail-section {
      padding: 16px;
      border-bottom: 1px solid var(--border);
    }
    .detail-title {
      display: grid;
      gap: 8px;
    }
    .detail-title h3 {
      margin: 0;
      font-family: var(--mono);
      font-size: 17px;
      overflow-wrap: anywhere;
    }
    .tab-row {
      display: flex;
      gap: 8px;
      padding: 10px 16px 0;
      flex-wrap: wrap;
    }
    .tab-button {
      border: 1px solid var(--border);
      border-radius: 999px;
      background: #ffffff;
      color: var(--muted);
      padding: 7px 11px;
      font-size: 12px;
      font-weight: 800;
    }
    .tab-button.active {
      background: var(--primary);
      border-color: var(--primary);
      color: #ffffff;
    }
    .empty-state {
      padding: 24px;
      color: var(--muted);
      text-align: center;
    }
    .field-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }
    .field-grid .span-2 { grid-column: span 2; }
    .form-section {
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 12px;
      background: #ffffff;
      display: grid;
      gap: 12px;
    }
    .form-section-title {
      margin: 0;
      font-size: 13px;
      font-weight: 900;
      color: var(--text);
    }
    .form-section-note {
      margin: -4px 0 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
    }
    .field-label {
      display: grid;
      gap: 6px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 800;
    }
    .field-label-head {
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
      color: var(--muted);
      line-height: 1.35;
    }
    .requirement-badge {
      border: 1px solid var(--border);
      border-radius: 999px;
      padding: 2px 7px;
      background: var(--surface-soft);
      color: var(--muted);
      font-size: 10px;
      font-weight: 900;
      line-height: 1.3;
      white-space: nowrap;
    }
    .requirement-badge.required {
      border-color: rgba(185, 28, 28, 0.24);
      background: #fff3f4;
      color: #9b2530;
    }
    .requirement-badge.conditional {
      border-color: rgba(217, 119, 6, 0.26);
      background: #fffaf0;
      color: #9a5b00;
    }
    .requirement-badge.optional {
      border-color: rgba(71, 85, 105, 0.18);
      background: #f8fafc;
      color: var(--faint);
    }
    .field-help {
      margin: 0;
      color: var(--faint);
      font-size: 11px;
      font-weight: 600;
      line-height: 1.45;
      overflow-wrap: anywhere;
    }
    .checkbox-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
    }
    .choice-grid {
      display: grid;
      gap: 8px;
    }
    .check-option {
      min-height: 40px;
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 8px 10px;
      display: flex;
      gap: 8px;
      align-items: flex-start;
      color: var(--text);
      background: var(--surface-soft);
      overflow-wrap: anywhere;
    }
    .check-option strong {
      display: block;
      font-size: 12px;
      line-height: 1.35;
    }
    .check-option small {
      display: block;
      margin-top: 2px;
      color: var(--muted);
      font-size: 11px;
      line-height: 1.4;
    }
    .check-option input:checked + span strong {
      color: var(--primary-ink);
    }
    .check-option input { margin-top: 2px; }
    .decision-code {
      color: var(--faint);
      font-family: var(--mono);
      font-size: 10px;
      overflow-wrap: anywhere;
    }
    .data-block {
      display: grid;
      gap: 10px;
    }
    .summary-list {
      display: grid;
      gap: 10px;
    }
    .summary-item {
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 12px;
      background: var(--surface-soft);
    }
    .summary-item h4 {
      margin: 0 0 8px;
      font-size: 13px;
    }
    .summary-item p, .summary-item li {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.55;
    }
    .summary-item ul {
      margin: 0;
      padding-left: 18px;
    }
    .original-output {
      border: 1px solid rgba(37, 99, 235, 0.16);
      border-radius: var(--radius);
      background: #f6f9ff;
      padding: 12px;
      display: grid;
      gap: 8px;
    }
    .original-output h4 {
      margin: 0;
      font-size: 13px;
    }
    .original-output p {
      margin: 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.55;
      overflow-wrap: anywhere;
    }
    .original-answer {
      max-height: 220px;
      overflow: auto;
      white-space: pre-wrap;
    }
    .question-list {
      display: grid;
      gap: 8px;
    }
    .question-card {
      border: 1px solid var(--border);
      border-radius: var(--radius);
      background: #ffffff;
      padding: 10px;
      display: grid;
      gap: 5px;
    }
    .question-card strong {
      color: var(--text);
      font-size: 13px;
      line-height: 1.45;
      overflow-wrap: anywhere;
    }
    .question-card small {
      color: var(--faint);
      font-size: 11px;
      line-height: 1.4;
      overflow-wrap: anywhere;
    }
    .context-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }
    .context-field {
      border: 1px solid var(--border);
      border-radius: var(--radius);
      background: #ffffff;
      padding: 10px;
      display: grid;
      gap: 6px;
    }
    .context-field.span-2 { grid-column: span 2; }
    .context-label {
      color: var(--faint);
      font-size: 11px;
      font-weight: 900;
    }
    .context-value {
      color: var(--text);
      font-size: 13px;
      line-height: 1.55;
      overflow-wrap: anywhere;
    }
    .decision-summary {
      display: grid;
      gap: 10px;
    }
    .decision-summary-head {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 12px;
      flex-wrap: wrap;
    }
    .decision-workflow {
      border: 1px solid rgba(15, 118, 110, 0.18);
      border-radius: var(--radius);
      background: #f3fbf9;
      padding: 10px 12px;
      display: grid;
      gap: 6px;
      color: var(--primary-ink);
      font-size: 12px;
      line-height: 1.5;
    }
    .decision-workflow strong {
      font-size: 12px;
      font-weight: 900;
    }
    .decision-workflow ol {
      margin: 0;
      padding-left: 18px;
      color: var(--text);
    }
    .decision-workflow li + li {
      margin-top: 3px;
    }
    .ai-suggestion {
      border: 1px solid rgba(217, 119, 6, 0.22);
      border-left: 4px solid var(--warning);
      border-radius: var(--radius);
      background: #fffaf0;
      padding: 12px;
      display: grid;
      gap: 10px;
    }
    .ai-suggestion-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }
    .ai-suggestion h4 {
      margin: 0;
      font-size: 13px;
    }
    .ai-suggestion p {
      margin: 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.55;
      overflow-wrap: anywhere;
    }
    .ai-suggestion-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .glossary-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }
    .glossary-card {
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 12px;
      background: var(--surface-soft);
      display: grid;
      gap: 8px;
    }
    .glossary-card h4 {
      margin: 0;
      font-size: 13px;
    }
    .glossary-card p {
      margin: 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
    }
    .glossary-code {
      color: var(--faint);
      font-family: var(--mono);
      font-size: 11px;
      overflow-wrap: anywhere;
    }
    .jump-link {
      width: fit-content;
      border: 1px solid rgba(15, 118, 110, 0.24);
      border-radius: 999px;
      background: #edf6f5;
      color: var(--primary-ink);
      padding: 4px 8px;
      font-size: 11px;
      font-weight: 800;
    }
    .evidence-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
    }
    .evidence-table th, .evidence-table td {
      padding: 9px 8px;
      border-bottom: 1px solid var(--border);
      text-align: left;
      vertical-align: top;
    }
    .evidence-table th {
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
    }
    .evidence-text {
      max-width: 420px;
      color: var(--muted);
      line-height: 1.45;
      overflow-wrap: anywhere;
    }
    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .button {
      min-height: 38px;
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 8px 12px;
      background: #ffffff;
      color: var(--text);
      font-weight: 800;
      font-size: 12px;
    }
    .button.primary {
      background: var(--primary);
      border-color: var(--primary);
      color: #ffffff;
    }
    .button.blue {
      background: var(--blue);
      border-color: var(--blue);
      color: #ffffff;
    }
    .button:disabled {
      opacity: 0.52;
      cursor: not-allowed;
    }
    .notice {
      border: 1px solid var(--border);
      border-left: 4px solid var(--warning);
      border-radius: var(--radius);
      background: #fffaf0;
      color: #7b4b00;
      padding: 10px 12px;
      font-size: 12px;
      line-height: 1.45;
    }
    .notice.ok {
      border-left-color: var(--success);
      background: #f0fff7;
      color: #0c6c43;
    }
    .notice.danger {
      border-left-color: var(--danger);
      background: #fff3f4;
      color: #9b2530;
    }
    .notice.authority {
      border-left-color: var(--primary);
      background: #f3fbf9;
      color: var(--primary-ink);
      font-weight: 800;
    }
    .notice strong {
      display: block;
      margin-bottom: 3px;
      color: inherit;
    }
    .pipeline {
      display: grid;
      gap: 10px;
      min-width: 0;
    }
    .pipeline-step {
      min-width: 0;
      display: grid;
      grid-template-columns: minmax(96px, 0.28fr) minmax(0, 1fr) minmax(64px, max-content);
      gap: 10px;
      align-items: center;
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 10px 12px;
      background: var(--surface-soft);
    }
    .pipeline-step .pill {
      min-width: 0;
      justify-self: end;
      white-space: normal;
      text-align: center;
    }
    .step-label {
      min-width: 0;
      font-weight: 800;
      font-size: 12px;
      line-height: 1.35;
      overflow-wrap: anywhere;
    }
    .step-value {
      min-width: 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
      overflow-wrap: anywhere;
    }
    .sidebar-panel {
      border: 1px solid var(--border);
      border-radius: var(--radius);
      background: var(--surface);
      padding: 14px;
    }
    .mini-stat {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      color: var(--muted);
      font-size: 12px;
      padding: 6px 0;
      border-bottom: 1px solid rgba(129, 140, 160, 0.18);
    }
    .mini-stat:last-child { border-bottom: 0; }
    .mini-stat strong { color: var(--text); }
    .sidebar-note {
      margin: 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.5;
    }
    .pipeline.compact {
      gap: 8px;
    }
    .pipeline.compact .pipeline-step {
      grid-template-columns: minmax(72px, 0.34fr) minmax(0, 1fr);
      gap: 8px;
      padding: 9px 10px;
    }
    .pipeline.compact .pipeline-step .pill {
      grid-column: 1 / -1;
      justify-self: start;
    }
    .guide-list {
      margin: 0;
      padding-left: 18px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.55;
      display: grid;
      gap: 6px;
    }
    .guide-list strong { color: var(--text); }

    @media (max-width: 1180px) {
      body {
        height: auto;
        min-height: 100vh;
        overflow: auto;
      }
      .app-shell {
        grid-template-columns: 1fr;
        height: auto;
        min-height: 100vh;
        overflow: visible;
      }
      .sidebar {
        position: static;
        border-right: 0;
        border-bottom: 1px solid var(--border);
        height: auto;
        max-height: none;
        overflow: visible;
      }
      .main {
        height: auto;
        max-height: none;
        overflow: visible;
      }
      .kpi-grid { grid-template-columns: repeat(3, minmax(120px, 1fr)); }
      .workspace {
        grid-template-columns: 1fr;
        height: auto;
        overflow: visible;
      }
      .queue-panel, .detail-panel {
        display: block;
        height: auto;
      }
      .case-list, .detail-body {
        max-height: none;
        overflow: visible;
      }
    }
    @media (max-width: 960px) {
      .pipeline-step {
        grid-template-columns: 1fr;
        align-items: start;
      }
      .pipeline-step .pill { justify-self: start; }
    }
    @media (max-width: 720px) {
      .main { padding: 14px; }
      .topbar { align-items: flex-start; flex-direction: column; }
      .badges { justify-content: flex-start; }
      .kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .field-grid, .checkbox-grid { grid-template-columns: 1fr; }
      .glossary-grid { grid-template-columns: 1fr; }
      .field-grid .span-2 { grid-column: auto; }
      .pipeline-step { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <script id="workbench-data" type="application/json">__WORKBENCH_DATA__</script>
  <div id="app" class="app-shell">
    <aside class="sidebar">
      <section class="brand" aria-label="Workbench identity">
        <span id="brand-kicker" class="brand-kicker"></span>
        <h1 id="brand-title"></h1>
        <p id="brand-subtitle"></p>
      </section>
      <section class="nav-section" aria-label="Review queues">
        <div id="queues-section-title" class="section-title"></div>
        <div id="queue-nav"></div>
      </section>
      <section class="sidebar-panel" aria-label="Status summary">
        <div id="status-section-title" class="section-title"></div>
        <div id="side-status"></div>
      </section>
      <section class="sidebar-panel global-pipeline-panel" aria-label="Global process status">
        <div id="global-pipeline-section-title" class="section-title"></div>
        <p id="global-pipeline-subtitle" class="sidebar-note"></p>
        <div id="global-pipeline" class="pipeline compact" data-testid="global-pipeline"></div>
      </section>
      <section class="sidebar-panel" aria-label="Operation guide">
        <div id="guide-section-title" class="section-title"></div>
        <ol id="side-guide" class="guide-list"></ol>
      </section>
    </aside>

    <main class="main">
      <header class="topbar">
        <div>
          <h2 id="topbar-title"></h2>
          <p id="topbar-subtitle" class="topbar-subtitle"></p>
        </div>
        <div class="badges">
          <label class="language-control" for="language-select">
            <span id="language-label"></span>
            <select id="language-select" class="language-select" data-testid="language-select"></select>
          </label>
          <div id="top-badges" class="badges"></div>
        </div>
      </header>

      <section id="kpi-grid" class="kpi-grid" aria-label="Review KPIs"></section>

      <section class="workspace">
        <section class="panel queue-panel" aria-label="Case queue">
          <div class="panel-header">
            <div>
              <h3 id="case-queue-title"></h3>
              <p id="case-count-label"></p>
            </div>
          </div>
          <div class="search-row">
            <input id="search-input" class="search-input" data-testid="search-input" />
          </div>
          <div class="import-row" aria-label="Import review export">
            <button class="button" data-action="import-review-file" data-testid="import-review-file"></button>
            <input
              id="review-import-file"
              class="hidden-file-input"
              type="file"
              accept=".json,application/json"
              data-testid="review-import-input"
            />
            <div id="import-summary" class="import-summary" data-testid="import-summary" aria-live="polite"></div>
          </div>
          <div id="case-list" class="case-list" data-testid="case-list"></div>
        </section>

        <section class="panel detail-panel" aria-label="Case detail">
          <div id="detail-header" class="panel-header"></div>
          <div id="tab-row" class="tab-row"></div>
          <div id="detail-body" class="detail-body" data-testid="case-detail"></div>
        </section>
      </section>
    </main>
  </div>

  <script>
    const payload = JSON.parse(document.getElementById("workbench-data").textContent);
    const workbench = payload.workbench || {};
    const items = Array.isArray(workbench.workbench_items) ? workbench.workbench_items : [];
    const workbenchSummary = workbench.summary || {};
    const contractReport = payload.contract_report || {};
    const intakeContract = (payload.intake_contract || {}).contract || {};
    const fieldContract = contractReport.field_contract || {};
    const allowedValues = fieldContract.allowed_values || intakeContract.allowed_values || {};
    const prohibitedTargets = intakeContract.prohibited_change_targets || (contractReport.contract || {}).prohibited_change_targets || [];
    const progressReport = payload.progress_report || {};
    const originalLlmOutputs = payload.original_llm_outputs || {};
    const pilotBatchReport = payload.pilot_batch_report || {};
    const pilotBatchSummary = payload.pilot_batch || {};
    const closeoutReport = payload.closeout_report || {};
    const importReport = payload.import_report || {};
    const diffReport = payload.diff_report || {};
    const validationReport = payload.validation_report || {};
    const promotionReport = payload.promotion_report || {};
    const guardrails = payload.guardrails || {};
    const uiConfig = payload.ui || {};
    const csvFields = Array.from(new Set([
      "case_id",
      "case_topic",
      "question",
      ...asArray(workbench.csv_fields).filter(field => field !== "case_id"),
    ]));
    const workbenchFingerprint = [
      workbench.version || payload.version || "unknown",
      items.map(item => item.case_id).sort().join("|"),
    ].join("::").split("").reduce((hash, char) => ((hash * 31 + char.charCodeAt(0)) >>> 0), 2166136261).toString(16);
    const stateKey = `legal-risk-manual-review-workbench-v0.4.7.8:${workbenchFingerprint}`;
    const languageKey = "legal-risk-manual-review-workbench-language";
    const exportStateKey = `legal-risk-manual-review-workbench-export-state:${workbenchFingerprint}`;
    const importStateKey = `legal-risk-manual-review-workbench-import-state:${workbenchFingerprint}`;
    const aiSuggestionStateKey = `legal-risk-manual-review-workbench-ai-suggestions-v0.4.7.8:${workbenchFingerprint}`;
    const pilotChecklistStateKey = `legal-risk-manual-review-workbench-pilot-checklist-v0.4.7.8.16:${workbenchFingerprint}`;
    const reviewerDraftFields = [
      "reviewer",
      "reviewed_at",
      "decision",
      "confirmed_root_causes",
      "rejected_root_causes",
      "confirmed_follow_up_actions",
      "proposed_change_targets",
      "fixture_candidate",
      "rationale",
      "notes",
    ];
    const aiSuggestionFields = [
      "decision",
      "confirmed_root_causes",
      "rejected_root_causes",
      "confirmed_follow_up_actions",
      "proposed_change_targets",
      "fixture_candidate",
      "rationale",
      "notes",
    ];

    let currentFilter = "all_cases";
    let activeTab = "overview";
    let selectedCaseId = items[0] ? items[0].case_id : "";
    let query = "";
    let drafts = loadDrafts();
    let aiSuggestions = loadAiSuggestions();
    let pilotChecklistState = loadPilotChecklistState();
    let exportState = loadExportState();
    let importState = loadImportState();
    let currentLanguage = initialLanguage();

    const queueDefs = [
      { key: "all_cases", labelKey: "queues.all_cases", count: () => items.length },
      { key: "high_priority", labelKey: "queues.high_priority", count: () => highPriorityIds().length },
      { key: "pilot_batch", labelKey: "queues.pilot_batch", count: () => pilotBatchCaseIds().length },
      { key: "awaiting_manual_review", labelKey: "queues.awaiting_manual_review", count: () => items.filter(item => item.decision_status === "pending").length },
      { key: "blocked_intake_gate", labelKey: "queues.blocked_intake_gate", count: () => (closeoutReport.summary && closeoutReport.summary.gate_status === "blocked") ? items.length : 0 },
      { key: "with_local_draft", labelKey: "queues.with_local_draft", count: () => draftCaseIdsWithContent().length },
      { key: "ready_for_export", labelKey: "queues.ready_for_export", count: () => readyDraftCaseIds().length },
    ];

    const tabDefs = [
      { key: "overview", labelKey: "tabs.overview" },
      { key: "evidence", labelKey: "tabs.evidence" },
      { key: "questions", labelKey: "tabs.questions" },
      { key: "glossary", labelKey: "tabs.glossary" },
      { key: "decision", labelKey: "tabs.decision" },
    ];

    const labelGlossary = {
      high_risk_grounding_review: {
        zh: ["高风险证据复核", "高风险场景需要人工确认答案是否有足够证据支撑。"],
        en: ["High-risk grounding review", "High-risk cases need human confirmation that the answer is grounded in evidence."],
      },
      scenario_registry_calibration: {
        zh: ["场景登记校准", "检查 scenario registry 中核心条款范围是否过宽、过窄或跨领域。"],
        en: ["Scenario registry calibration", "Checks whether scenario registry core articles are too broad, too narrow, or cross-domain."],
      },
      base_retrieval_quality_review: {
        zh: ["基础召回质量复核", "检查 dense、sparse、union 等基础召回是否已经漏掉关键证据。"],
        en: ["Base retrieval quality review", "Checks whether dense, sparse, or union retrieval missed key evidence."],
      },
      anchor_dependency_review: {
        zh: ["Anchor 依赖复核", "检查是否过度依赖 anchor 补救基础召回缺口。"],
        en: ["Anchor dependency review", "Checks whether anchors are compensating for weak base retrieval."],
      },
      final_evidence_selection_review: {
        zh: ["最终证据选择复核", "检查进入最终答案的证据是否丢失了前面已召回的重要条款。"],
        en: ["Final evidence selection review", "Checks whether final evidence dropped important articles found earlier."],
      },
      primary_evidence_review: {
        zh: ["主要依据复核", "检查主要法律依据是否缺失或未进入最终证据链。"],
        en: ["Primary evidence review", "Checks whether primary legal support is missing from the final chain."],
      },
      final_primary_gap: {
        zh: ["最终证据缺少主要依据", "答案需要的主要法律依据没有进入最终 evidence_chain。"],
        en: ["Final primary gap", "Primary legal support needed by the answer is absent from final evidence."],
      },
      scenario_core_gap: {
        zh: ["场景核心证据缺口", "scenario registry 认为核心的条款没有被最终证据覆盖。"],
        en: ["Scenario core gap", "A core article required by the scenario registry is not covered by final evidence."],
      },
      anchor_dependent_coverage: {
        zh: ["证据覆盖依赖 anchor", "关键证据主要靠 anchor 层补出，基础召回本身偏弱。"],
        en: ["Anchor-dependent coverage", "Key evidence appears mainly after anchors, suggesting weak base retrieval."],
      },
      layer_coverage_regression: {
        zh: ["层间覆盖回退", "证据在召回管线后续阶段变少，说明某一层可能丢证据。"],
        en: ["Layer coverage regression", "Evidence coverage drops later in the retrieval pipeline."],
      },
      low_final_coverage: {
        zh: ["最终覆盖不足", "最终 evidence_chain 覆盖的关键证据比例偏低。"],
        en: ["Low final coverage", "Final evidence covers too little of the expected support."],
      },
      registry_core_review_needed: {
        zh: ["需复核核心条款登记", "需要人工判断 registry 中核心条款是否设置合理。"],
        en: ["Registry core review needed", "A human should check whether registered core articles are appropriate."],
      },
      core_missing_from_final_evidence: {
        zh: ["核心条款未进最终证据", "场景核心条款没有出现在最终证据链中。"],
        en: ["Core missing from final evidence", "Scenario core articles are missing from final evidence."],
      },
      evidence_chain_gap_candidate: {
        zh: ["证据链缺口候选", "可能存在答案与证据链之间的支撑缺口。"],
        en: ["Evidence-chain gap candidate", "The answer may not be fully supported by its evidence chain."],
      },
      final_primary_gap_overlap: {
        zh: ["主要依据缺口重叠", "场景核心缺口与最终主要依据缺口重叠。"],
        en: ["Final primary gap overlap", "Scenario core gap overlaps with missing primary final evidence."],
      },
      cross_domain_core_gap: {
        zh: ["跨领域核心缺口", "缺失的核心条款分布在不同法律领域，需要校准范围。"],
        en: ["Cross-domain core gap", "Missing core articles span domains and need scope calibration."],
      },
      definition_core_candidate: {
        zh: ["定义条款核心候选", "缺失条款可能只是定义条款，需要判断是否应作为核心条款。"],
        en: ["Definition core candidate", "A missing article may be definition-only and should be reviewed before treating it as core."],
      },
      base_retrieval_review_needed: {
        zh: ["需复核基础召回", "基础召回覆盖率低，需要先查 metadata、chunking、query 等输入质量。"],
        en: ["Base retrieval review needed", "Base retrieval coverage is weak; review metadata, chunking, and query coverage."],
      },
      dense_retrieval_gap: {
        zh: ["Dense 召回缺口", "向量召回没有覆盖足够的预期证据。"],
        en: ["Dense retrieval gap", "Dense retrieval missed expected evidence."],
      },
      sparse_retrieval_gap: {
        zh: ["Sparse 召回缺口", "关键词/BM25 召回没有覆盖足够的预期证据。"],
        en: ["Sparse retrieval gap", "Sparse/BM25 retrieval missed expected evidence."],
      },
      union_retrieval_gap: {
        zh: ["合并召回缺口", "dense 与 sparse 合并后仍然漏掉预期证据。"],
        en: ["Union retrieval gap", "The dense/sparse union still missed expected evidence."],
      },
      sparse_only_support: {
        zh: ["仅 Sparse 有支撑", "只有关键词召回命中证据，向量召回贡献不足。"],
        en: ["Sparse-only support", "Only sparse retrieval found support; dense retrieval contributed too little."],
      },
      dense_only_support: {
        zh: ["仅 Dense 有支撑", "只有向量召回命中证据，关键词召回贡献不足。"],
        en: ["Dense-only support", "Only dense retrieval found support; sparse retrieval contributed too little."],
      },
      no_union_gain: {
        zh: ["合并无明显增益", "合并召回没有明显优于单一路径。"],
        en: ["No union gain", "Union retrieval does not materially improve over the best single retriever."],
      },
      anchor_rescue_pattern: {
        zh: ["Anchor 补救模式", "anchor 层补回了基础召回遗漏的证据。"],
        en: ["Anchor rescue pattern", "Anchors recovered evidence that base retrieval missed."],
      },
      metadata_or_chunking_review_candidate: {
        zh: ["Metadata/切块复核候选", "可能需要复核元数据、切块或查询词覆盖。"],
        en: ["Metadata/chunking review candidate", "Metadata, chunking, or query lexical coverage may need review."],
      },
      anchor_dependency_review_needed: {
        zh: ["需复核 Anchor 依赖", "证据覆盖明显依赖 anchor，需要判断是否健康。"],
        en: ["Anchor dependency review needed", "Coverage depends on anchors and needs review."],
      },
      anchor_masking_base_retrieval_gap: {
        zh: ["Anchor 掩盖基础召回缺口", "anchor 补救可能掩盖了基础召回质量问题。"],
        en: ["Anchor masks base retrieval gap", "Anchor support may be hiding a base retrieval quality issue."],
      },
      anchor_rescue_success: {
        zh: ["Anchor 补救成功", "anchor 层把覆盖率提升到了复核阈值以上。"],
        en: ["Anchor rescue success", "Anchors raised coverage above the review threshold."],
      },
      high_anchor_gain: {
        zh: ["Anchor 增益过高", "anchor 相比基础召回带来很大增量，需判断是否过度依赖。"],
        en: ["High anchor gain", "Anchors add a large coverage gain over base retrieval."],
      },
      anchor_supported_but_final_lost: {
        zh: ["Anchor 找到但最终丢失", "anchor 或 rerank_input 中已有证据，但 final evidence 未保留。"],
        en: ["Anchor-supported but final lost", "Evidence found by anchor or rerank_input was not preserved in final evidence."],
      },
      final_selection_review_needed: {
        zh: ["需复核最终证据选择", "最终证据选择阶段可能丢掉了关键条款。"],
        en: ["Final selection review needed", "Final evidence selection may have dropped key articles."],
      },
      rerank_input_to_final_loss: {
        zh: ["Rerank 输入到最终证据流失", "rerank_input 中存在的证据没有进入最终 evidence_chain。"],
        en: ["Rerank input to final loss", "Evidence present in rerank_input did not reach final evidence."],
      },
      primary_evidence_lost: {
        zh: ["主要依据流失", "主要法律依据在最终证据选择中丢失。"],
        en: ["Primary evidence lost", "Primary legal support was dropped before final evidence."],
      },
      scenario_core_lost: {
        zh: ["场景核心证据流失", "场景核心条款在最终证据阶段丢失。"],
        en: ["Scenario core lost", "Scenario core evidence was dropped from final evidence."],
      },
      liability_evidence_lost: {
        zh: ["责任后果证据流失", "责任或后果类条款没有进入最终证据链。"],
        en: ["Liability evidence lost", "Liability or consequence support was dropped."],
      },
      operative_evidence_lost: {
        zh: ["规范性证据流失", "义务、程序、权利或技术要求类证据被丢掉。"],
        en: ["Operative evidence lost", "Operative, procedural, rights, or technical support was dropped."],
      },
      low_final_coverage_after_selection: {
        zh: ["选择后最终覆盖不足", "证据选择后覆盖率低于诊断阈值。"],
        en: ["Low final coverage after selection", "Coverage falls below the threshold after final selection."],
      },
      index_or_source_coverage_review_candidate: {
        zh: ["索引/来源覆盖复核候选", "可能是法规来源或索引覆盖不足导致召回不到。"],
        en: ["Index/source coverage review candidate", "Source or index coverage may be insufficient."],
      },
      registry_core_scope_review_candidate: {
        zh: ["核心范围复核候选", "场景核心条款范围可能需要人工收敛或扩展。"],
        en: ["Registry core scope review candidate", "Scenario core scope may need human calibration."],
      },
      zero_base_recall: {
        zh: ["基础召回为零", "基础召回没有命中预期证据。"],
        en: ["Zero base recall", "Base retrieval found no expected evidence."],
      },
      zero_base_to_anchor_recovery: {
        zh: ["零基础召回后由 Anchor 补回", "基础召回完全没命中，但 anchor 补回了证据。"],
        en: ["Zero base to anchor recovery", "Base retrieval found nothing, but anchors recovered evidence."],
      },
      metadata_chunking_or_query_coverage: {
        zh: ["元数据/切块/查询覆盖问题", "可能是法规元数据、文本切块或查询词覆盖导致召回弱。"],
        en: ["Metadata/chunking/query coverage", "Metadata, chunking, or query lexical coverage may be causing weak retrieval."],
      },
      source_or_index_coverage: {
        zh: ["来源或索引覆盖问题", "可能是法规来源或索引本身没有覆盖到所需条款。"],
        en: ["Source or index coverage", "The source corpus or index may not cover the needed article."],
      },
      anchor_dependency_governance: {
        zh: ["Anchor 依赖治理", "需要治理 anchor 对基础召回缺口的补救方式。"],
        en: ["Anchor dependency governance", "Govern how anchors compensate for base retrieval gaps."],
      },
      scenario_core_scope: {
        zh: ["场景核心范围", "需要人工确认场景核心条款集合是否合理。"],
        en: ["Scenario core scope", "Human review should confirm the scenario core article set."],
      },
      final_evidence_selection_policy: {
        zh: ["最终证据选择策略", "需要设计如何保留主要、责任、程序等关键证据。"],
        en: ["Final evidence selection policy", "A policy is needed to preserve primary, liability, and procedural evidence."],
      },
      primary_evidence_gap: {
        zh: ["主要证据缺口", "答案所需的主要法律依据缺失。"],
        en: ["Primary evidence gap", "Primary legal evidence needed by the answer is missing."],
      },
      high_risk_grounding_gap: {
        zh: ["高风险 grounding 缺口", "高风险结论的证据支撑不足，需要人工确认。"],
        en: ["High-risk grounding gap", "A high-risk conclusion is not sufficiently grounded."],
      },
      functional_typing_metadata: {
        zh: ["法律功能类型元数据问题", "条文的定义、义务、责任、程序等功能类型可能识别不足。"],
        en: ["Functional typing metadata", "Legal functional type metadata may be incomplete or inaccurate."],
      },
      metadata_chunking_or_query_coverage_review: {
        zh: ["复核元数据/切块/查询覆盖", "检查法规元数据、切块粒度和查询词覆盖。"],
        en: ["Review metadata/chunking/query coverage", "Review metadata, chunk size, and query lexical coverage."],
      },
      source_index_coverage_review: {
        zh: ["复核来源/索引覆盖", "确认法规来源和索引是否覆盖所需条款。"],
        en: ["Review source/index coverage", "Confirm that sources and indexes cover needed articles."],
      },
      anchor_dependency_governance_review: {
        zh: ["复核 Anchor 依赖治理", "判断是否需要降低对 anchor 的依赖或治理补救策略。"],
        en: ["Review anchor dependency governance", "Decide whether anchor dependency needs governance."],
      },
      scenario_registry_core_article_review: {
        zh: ["复核场景核心条款", "人工确认 scenario registry 的核心条款设置。"],
        en: ["Review scenario core articles", "Human confirmation of scenario registry core articles."],
      },
      final_evidence_selection_policy_review: {
        zh: ["复核最终证据选择策略", "人工判断哪些证据应从 rerank_input 保留到 final evidence。"],
        en: ["Review final evidence selection policy", "Decide which evidence should be preserved into final evidence."],
      },
      primary_evidence_fixture_candidate_review: {
        zh: ["复核主要证据回归测试样本候选", "确认是否能沉淀为主要证据覆盖测试样本。"],
        en: ["Review primary-evidence test candidate", "Confirm whether this can become a primary-evidence regression test sample."],
      },
      high_risk_manual_grounding_review: {
        zh: ["高风险人工 grounding 复核", "高风险结论必须人工确认 grounding 是否充分。"],
        en: ["High-risk manual grounding review", "A high-risk conclusion needs manual grounding confirmation."],
      },
      functional_typing_fixture_review: {
        zh: ["复核功能类型回归测试样本", "确认是否可作为法律功能类型测试样本。"],
        en: ["Review functional-typing test sample", "Confirm whether this can become a legal functional typing regression test sample."],
      },
      manual_dataset: {
        zh: ["人工复核数据集", "从诊断结果汇总出的人工复核数据包。"],
        en: ["Manual review dataset", "A manual-review package aggregated from diagnostics."],
      },
      scenario_registry_calibration: {
        zh: ["场景登记校准", "复核 scenario registry 的核心条款和领域范围。"],
        en: ["Scenario registry calibration", "Review scenario registry core articles and domain scope."],
      },
      base_retrieval_quality: {
        zh: ["基础召回质量", "评估 dense、sparse、union 在 anchor 前的证据覆盖。"],
        en: ["Base retrieval quality", "Evaluates dense, sparse, and union coverage before anchors."],
      },
      anchor_dependency: {
        zh: ["Anchor 依赖", "评估关键证据是否依赖 anchor 补出。"],
        en: ["Anchor dependency", "Evaluates whether key evidence depends on anchor recovery."],
      },
      final_evidence_selection: {
        zh: ["最终证据选择", "评估从 rerank_input 到 final evidence 是否丢证据。"],
        en: ["Final evidence selection", "Evaluates evidence loss from rerank_input to final evidence."],
      },
      missing_final_expected: {
        zh: ["缺少最终预期证据", "预期应出现的证据没有进入最终 evidence_chain。"],
        en: ["Missing final expected evidence", "Expected evidence is absent from final evidence_chain."],
      },
      missing_scenario_core: {
        zh: ["缺少场景核心证据", "scenario registry 的核心条款没有进入最终证据链。"],
        en: ["Missing scenario core evidence", "Scenario core evidence is absent from final evidence."],
      },
      lost_evidence: {
        zh: ["流失证据", "曾在中间阶段出现但最终被丢掉的证据。"],
        en: ["Lost evidence", "Evidence seen earlier but dropped before final evidence."],
      },
      final_evidence: {
        zh: ["最终证据", "最终交给答案使用的 evidence_chain。"],
        en: ["Final evidence", "Evidence chain used by the final answer."],
      },
      no_imported_review_rows: {
        zh: ["没有导入复核记录", "当前还没有成功导入 reviewer 填写的记录。"],
        en: ["No imported review rows", "No reviewer-filled rows have been imported yet."],
      },
      no_promotion_candidates: {
        zh: ["没有可提升候选", "没有 completed 且 valid 的人工复核结论可进入提升演练。"],
        en: ["No promotion candidates", "No completed and valid manual decisions are ready for promotion dry run."],
      },
      no_ready_action_candidates: {
        zh: ["没有可执行动作", "还没有通过验证、可转为工程动作的候选项。"],
        en: ["No ready action candidates", "No validated candidates are ready to become engineering actions."],
      },
      empty_importable_content: {
        zh: ["可导入内容为空", "导入行没有 reviewer、decision、rationale 等有效填写内容。"],
        en: ["Empty importable content", "The row has no usable reviewer, decision, rationale, or related content."],
      },
      standalone_offline_html: {
        zh: ["独立离线 HTML", "页面是本地静态文件，不需要后端服务。"],
        en: ["Standalone offline HTML", "The page is a local static file with no backend dependency."],
      },
      rag_query_integration: {
        zh: ["禁止接入 RAG 主流程", "本工具只看离线报告，不调用 rag_query。"],
        en: ["RAG main-flow integration disallowed", "This tool only reads offline reports and does not call rag_query."],
      },
      backend_api_write: {
        zh: ["禁止后端写入", "页面不会直接写回后端或 schema。"],
        en: ["Backend API write disallowed", "The page does not write back to backend APIs or schemas."],
      },
      qdrant_access: {
        zh: ["禁止访问 Qdrant", "页面不访问向量数据库。"],
        en: ["Qdrant access disallowed", "The page does not access the vector database."],
      },
      llm_access: {
        zh: ["禁止调用 LLM", "页面不调用大模型。"],
        en: ["LLM access disallowed", "The page does not call an LLM."],
      },
      overwrite_original_decision_schema: {
        zh: ["禁止覆盖原始决策 schema", "导出结果必须走 importer/diff/validator 链路。"],
        en: ["Original decision schema overwrite disallowed", "Exports must go through importer, diff, and validator."],
      },
      hidden_seed_mutation: {
        zh: ["禁止修改 hidden seed", "本工具不修改隐藏评测样本。"],
        en: ["Hidden seed mutation disallowed", "This tool does not change hidden evaluation seeds."],
      },
      anchor_mutation: {
        zh: ["禁止修改 anchor", "本工具不新增或修改 anchor。"],
        en: ["Anchor mutation disallowed", "This tool does not add or modify anchors."],
      },
      rerank_mutation: {
        zh: ["禁止修改 rerank", "本工具不修改重排逻辑。"],
        en: ["Rerank mutation disallowed", "This tool does not modify reranking."],
      },
      prompt_mutation: {
        zh: ["禁止修改 prompt", "本工具不修改生成提示词。"],
        en: ["Prompt mutation disallowed", "This tool does not modify prompts."],
      },
      risk_rule_mutation: {
        zh: ["禁止修改风险规则", "本工具不修改风险补全或术语保留规则。"],
        en: ["Risk rule mutation disallowed", "This tool does not modify risk rules."],
      },
      eval_case_mutation: {
        zh: ["禁止修改 eval case", "本工具不修改评测用例。"],
        en: ["Eval case mutation disallowed", "This tool does not modify evaluation cases."],
      },
    };

    const reviewQuestionGlossary = {
      "Did dense/sparse/union retrieval miss expected evidence before anchor injection?": {
        zh: "在 anchor 介入之前，dense、sparse 或 union 召回是否已经漏掉了预期证据？",
        en: "Did dense/sparse/union retrieval miss expected evidence before anchor injection?",
      },
      "Is anchor dependency acceptable, or does it indicate weak base retrieval metadata?": {
        zh: "当前对 anchor 的依赖是否可以接受，还是说明基础召回的元数据质量偏弱？",
        en: "Is anchor dependency acceptable, or does it indicate weak base retrieval metadata?",
      },
      "Which expected article was present in rerank_input but absent from final evidence?": {
        zh: "哪些预期条款曾出现在 rerank_input 中，但没有进入最终证据链？",
        en: "Which expected article was present in rerank_input but absent from final evidence?",
      },
      "Does the answer rely on a primary statute that is missing from final evidence?": {
        zh: "答案是否依赖某个主要法律依据，但该依据没有出现在最终证据链中？",
        en: "Does the answer rely on a primary statute that is missing from final evidence?",
      },
      "Is the scenario core article truly required, or is the registry core set too broad?": {
        zh: "这个场景核心条款是否确实必要，还是 scenario registry 的核心条款范围设置过宽？",
        en: "Is the scenario core article truly required, or is the registry core set too broad?",
      },
      "Does low final coverage make the answer unsuitable without manual review?": {
        zh: "最终证据覆盖率偏低时，答案是否必须经过人工复核后才适合使用？",
        en: "Does low final coverage make the answer unsuitable without manual review?",
      },
      "Should the missing scenario core article remain a required core article for this scenario?": {
        zh: "缺失的场景核心条款是否仍应作为该场景的必需核心条款保留？",
        en: "Should the missing scenario core article remain a required core article for this scenario?",
      },
      "Does the base retrieval gap point to metadata, chunking, source coverage, or lexical query mismatch?": {
        zh: "基础召回缺口更像是由元数据、文本切块、来源覆盖，还是查询词匹配不足导致？",
        en: "Does the base retrieval gap point to metadata, chunking, source coverage, or lexical query mismatch?",
      },
      "Is anchor support masking weak base retrieval rather than providing healthy supplemental coverage?": {
        zh: "anchor 的补充支撑是否在掩盖基础召回偏弱，而不是提供健康的补充覆盖？",
        en: "Is anchor support masking weak base retrieval rather than providing healthy supplemental coverage?",
      },
      "Which evidence present at rerank_input should be preserved in final evidence?": {
        zh: "哪些已经进入 rerank_input 的证据应该被保留到最终证据链？",
        en: "Which evidence present at rerank_input should be preserved in final evidence?",
      },
      "Does the final answer require the missing primary evidence to be grounded?": {
        zh: "最终答案是否需要缺失的主要证据作为 grounding 支撑？",
        en: "Does the final answer require the missing primary evidence to be grounded?",
      },
      "Does the report conclusion rely on liability or consequence evidence that was dropped?": {
        zh: "报告结论是否依赖已经被丢弃的责任或法律后果类证据？",
        en: "Does the report conclusion rely on liability or consequence evidence that was dropped?",
      },
    };

    const decisionOptionGlossary = {
      confirm_diagnostic_issue: {
        zh: ["确认诊断成立", "证据质量问题成立，后续应进入对应治理动作。"],
        en: ["Confirm diagnostic issue", "The grounding-quality issue is valid and should feed follow-up governance."],
      },
      confirm_scope_adjustment_needed: {
        zh: ["确认需要范围校准", "诊断方向基本成立，但核心条款、场景范围或领域边界需要先校准。"],
        en: ["Confirm scope adjustment needed", "The issue is directionally valid, but scope, core articles, or domain boundaries need calibration."],
      },
      reject_diagnostic_issue: {
        zh: ["驳回诊断", "人工判断该诊断不成立，不应转化为工程动作。"],
        en: ["Reject diagnostic issue", "Human review finds the diagnostic invalid and it should not become an engineering action."],
      },
      insufficient_information: {
        zh: ["信息不足", "现有离线证据不足以判断，需要补充证据或更多上下文。"],
        en: ["Insufficient information", "Saved offline evidence is not enough to decide; more context or evidence is needed."],
      },
      defer: {
        zh: ["暂缓", "暂不形成结论，留待后续批次或更高优先级问题处理后再判断。"],
        en: ["Defer", "Do not decide now; revisit after higher-priority work or more review context."],
      },
    };

    const fieldGlossary = {
      insufficient_saved_evidence: {
        zh: ["现有保存证据不足", "当前离线报告没有足够证据支撑人工结论，需要补充 evidence capture。"],
        en: ["Insufficient saved evidence", "The saved offline reports do not contain enough evidence for a decision."],
      },
      needs_additional_evidence_capture: {
        zh: ["需要补充证据采集", "先补足可复核证据，再决定是否进入工程修复。"],
        en: ["Needs additional evidence capture", "Capture more reviewable evidence before engineering action."],
      },
      no_action: {
        zh: ["无需后续动作", "人工判断不需要形成工程动作或回归测试样本。"],
        en: ["No action", "No engineering action or regression test sample is needed after review."],
      },
    };

    function initialLanguage() {
      const languages = asArray(uiConfig.supported_languages).map(language => language.code);
      const fallback = uiConfig.default_language || "zh-CN";
      try {
        const saved = window.localStorage.getItem(languageKey);
        if (saved && languages.includes(saved)) return saved;
      } catch {}
      return languages.includes(fallback) ? fallback : (languages[0] || "zh-CN");
    }

    function languageMessages(language = currentLanguage) {
      const allMessages = uiConfig.messages || {};
      return allMessages[language] || allMessages[uiConfig.default_language] || allMessages["zh-CN"] || {};
    }

    function valueAtPath(source, path) {
      return path.split(".").reduce((node, key) => (
        node && Object.prototype.hasOwnProperty.call(node, key) ? node[key] : undefined
      ), source);
    }

    function t(path, fallback = "") {
      const value = valueAtPath(languageMessages(), path);
      if (value === undefined || value === null || Array.isArray(value) || typeof value === "object") return fallback;
      return String(value);
    }

    function tArray(path, fallback = []) {
      const value = valueAtPath(languageMessages(), path);
      return asArray(Array.isArray(value) ? value : fallback);
    }

    function formatMessage(template, values) {
      return String(template).replace(/\{([a-zA-Z0-9_]+)\}/g, (_, key) => (
        values[key] === undefined || values[key] === null ? "" : String(values[key])
      ));
    }

    function localizedIssue(issue) {
      const [code, detail] = String(issue).split(":");
      const label = t(`draftIssues.${code}`, code);
      return detail ? `${label}: ${detail}` : label;
    }

    function localizedStatus(value) {
      const text = String(value ?? "");
      return t(`statusCodes.${text}`, text);
    }

    function gateStatus() {
      return (closeoutReport.summary || {}).gate_status || "unknown";
    }

    function isGateOpen() {
      return gateStatus() === "open";
    }

    function visibleQueueDefs() {
      return queueDefs.filter(queue => queue.key !== "blocked_intake_gate" || !isGateOpen());
    }

    function gateBadgeClass() {
      if (gateStatus() === "open") return "ready";
      if (gateStatus() === "blocked") return "blocked";
      return "danger";
    }

    function caseContext(item) {
      return (item && item.case_context) || {};
    }

    function pilotBatchFor(item) {
      return (item && item.pilot_batch && item.pilot_batch.in_pilot_batch) ? item.pilot_batch : null;
    }

    function pilotReviewAssistFor(item) {
      return (item && item.pilot_review_assist && item.pilot_review_assist.in_pilot_review_assist) ? item.pilot_review_assist : null;
    }

    function pilotEvidencePreview(evidence) {
      if (!evidence || typeof evidence !== "object") return "";
      return [evidence.citation, evidence.functional_type, evidence.content_preview]
        .filter(Boolean)
        .join(" - ");
    }

    function caseTopic(item) {
      const context = caseContext(item);
      return context.case_topic || context.question || (item && item.case_id) || t("common.unknown", "unknown");
    }

    function sourceLabel(sourceKey) {
      if (sourceKey === "rag_eval_report") return t("caseContext.sourceRagEvalReport", "RAG eval report");
      if (sourceKey === "rag_eval_cases") return t("caseContext.sourceRagEvalCases", "Eval cases");
      if (sourceKey === "scenario_registry") return t("caseContext.sourceScenarioRegistry", "Scenario registry");
      return sourceKey;
    }

    function caseContextSources(context) {
      return Object.entries((context && context.sources) || {})
        .filter(([, present]) => Boolean(present))
        .map(([key]) => sourceLabel(key));
    }

    function contextField(label, value, extra = "") {
      const values = asArray(value);
      if (!values.length) return "";
      const content = values.length > 1
        ? `<div class="case-meta">${values.map(item => pill(item)).join("")}</div>`
        : `<div class="context-value">${escapeHtml(values[0])}</div>`;
      return `
        <div class="context-field ${extra}">
          <div class="context-label">${escapeHtml(label)}</div>
          ${content}
        </div>
      `;
    }

    function renderCaseContextBlock(item) {
      const context = caseContext(item);
      const scenarios = asArray(context.scenario_contexts);
      const scenarioDescriptions = scenarios.map(scenario => scenario.description).filter(Boolean);
      const scenarioDomains = scenarios.map(scenario => scenario.domain).filter(Boolean);
      const sources = caseContextSources(context);
      const fields = [
        contextField(t("caseContext.caseTopic", "Case topic"), caseTopic(item), "span-2"),
        contextField(t("caseContext.question", "Question under review"), context.question, "span-2"),
        contextField(t("caseContext.scenario", "Risk scenario"), scenarioDescriptions, "span-2"),
        contextField(t("caseContext.domains", "Domains"), scenarioDomains.length ? scenarioDomains : item.expected_domains),
        contextField(t("caseContext.expectedRiskTypes", "Expected risk types"), context.expected_risk_types),
        contextField(t("caseContext.expectedActions", "Expected remediation actions"), context.expected_actions, "span-2"),
        contextField(t("caseContext.source", "Source"), sources),
      ].filter(Boolean).join("");
      return `
        <section class="detail-section">
          <div class="summary-item">
            <h4>${escapeHtml(t("caseContext.caseTopic", "Case topic"))}</h4>
            ${fields ? `<div class="context-grid">${fields}</div>` : `<p>${escapeHtml(t("caseContext.notAvailable", "No case topic is available from existing offline reports."))}</p>`}
          </div>
        </section>
      `;
    }

    function originalOutputFor(item) {
      return originalLlmOutputs[(item && item.case_id) || ""] || {};
    }

    function renderOriginalOutput(item) {
      const output = originalOutputFor(item);
      const answer = output.answer || "";
      const meta = [
        output.source ? `${t("originalOutput.source", "Source")}: ${sourceLabel(output.source)}` : "",
        output.answer_confidence !== undefined && output.answer_confidence !== null
          ? `${t("originalOutput.confidence", "Confidence")}: ${output.answer_confidence}`
          : "",
      ].filter(Boolean).join(" / ");
      return `
        <section class="detail-section">
          <article class="original-output">
            <h4>${escapeHtml(t("originalOutput.title", "Original LLM output"))}</h4>
            <p>${escapeHtml(t("originalOutput.subtitle", ""))}</p>
            ${meta ? `<p>${escapeHtml(meta)}</p>` : ""}
            ${answer ? `<p class="original-answer">${escapeHtml(answer)}</p>` : `<p>${escapeHtml(t("originalOutput.missing", "No original LLM output is available in saved offline reports."))}</p>`}
          </article>
        </section>
      `;
    }

    function glossaryEntry(code) {
      const entry = fieldGlossary[String(code)] || labelGlossary[String(code)] || null;
      if (!entry) return null;
      const pair = currentLanguage === "en-US" ? entry.en : entry.zh;
      return { label: pair[0], description: pair[1], code: String(code) };
    }

    function decisionOptionEntry(code) {
      const entry = decisionOptionGlossary[String(code)] || null;
      if (!entry) return { label: String(code ?? ""), description: "", code: String(code ?? "") };
      const pair = currentLanguage === "en-US" ? entry.en : entry.zh;
      return { label: pair[0], description: pair[1], code: String(code) };
    }

    function reviewQuestionEntry(question) {
      const original = String(question ?? "");
      const entry = reviewQuestionGlossary[original] || null;
      if (!entry) return { label: original, original };
      return {
        label: currentLanguage === "en-US" ? entry.en : entry.zh,
        original,
      };
    }

    function readableLabel(code) {
      const entry = glossaryEntry(code);
      return entry ? entry.label : String(code ?? "");
    }

    function readableTitle(code) {
      const entry = glossaryEntry(code);
      if (!entry) return String(code ?? "");
      return `${entry.label}: ${entry.description}`;
    }

    function explainedPill(code, extra = "") {
      const entry = glossaryEntry(code);
      if (!entry) return pill(code, extra);
      return `<span class="pill explained ${extra}" title="${escapeHtml(entry.description)}">${escapeHtml(entry.label)} <span class="pill-code">/ ${escapeHtml(entry.code)}</span></span>`;
    }

    function requirementBadge(kind) {
      const labels = {
        required: t("decision.requiredBadge", "Required"),
        conditional: t("decision.conditionalBadge", "Conditional"),
        optional: t("decision.optionalBadge", "Optional"),
      };
      const hints = {
        required: t("decision.requiredHint", "Required for a usable review draft."),
        conditional: t("decision.conditionalHint", "Required only for some decisions."),
        optional: t("decision.optionalHint", "Leave blank if unsure."),
      };
      return `<span class="requirement-badge ${escapeHtml(kind)}" title="${escapeHtml(hints[kind] || "")}">${escapeHtml(labels[kind] || kind)}</span>`;
    }

    function fieldLabelText(label, kind, help = "") {
      return `
        <span class="field-label-head">
          <span>${escapeHtml(label)}</span>
          ${requirementBadge(kind)}
        </span>
        ${help ? `<span class="field-help">${escapeHtml(help)}</span>` : ""}
      `;
    }

    function assistSignalPreview(signal) {
      if (!signal || typeof signal !== "object") return String(signal || "");
      return [signal.label, signal.reason].filter(Boolean).join(" - ");
    }

    function renderPilotReviewAssistPanel(item) {
      const assist = pilotReviewAssistFor(item);
      if (!assist) return "";
      const evidenceExamples = [
        ...asArray(assist.missing_expected_evidence_examples),
        ...asArray(assist.missing_scenario_core_evidence_examples),
        ...asArray(assist.lost_before_final_evidence_examples),
      ].map(pilotEvidencePreview).filter(Boolean).slice(0, 8);
      const fields = [
        contextField(t("decision.pilotReviewAssistTendency", "Advisory tendency"), assist.advisory_tendency_label || assist.advisory_tendency),
        contextField(t("decision.pilotReviewAssistSupport", "Evidence support status"), assist.support_status_label || assist.plain_assessment),
        contextField(t("decision.pilotReviewAssistSignals", "Assist signals"), asArray(assist.detected_assist_signals).map(assistSignalPreview), "span-2"),
        contextField(t("decision.pilotReviewAssistRisks", "Risk types"), assist.risk_types, "span-2"),
        contextField(t("decision.pilotReviewAssistActions", "Remediation actions"), assist.recommended_actions, "span-2"),
        contextField(t("decision.pilotReviewAssistFocusQuestions", "Questions to check"), assist.focus_questions_for_user, "span-2"),
        contextField(t("decision.pilotReviewAssistRationale", "Assist rationale"), assist.advisory_rationale, "span-2"),
        contextField(t("decision.pilotReviewAssistMissingEvidence", "Missing, scenario-core, or lost evidence examples"), evidenceExamples, "span-2"),
      ].filter(Boolean).join("");
      return `
        <section class="detail-section">
          <article class="ai-suggestion pilot-review-assist-panel" data-testid="pilot-review-assist-panel">
            <div class="ai-suggestion-head">
              <div>
                <h4>${escapeHtml(t("decision.pilotReviewAssistTitle", "Pilot review assist"))}</h4>
                <p>${escapeHtml(t("decision.pilotReviewAssistSubtitle", ""))}</p>
              </div>
              ${pill(t("decision.pilotReviewAssistBadge", "Review assist"), "pending")}
            </div>
            <div class="notice">${escapeHtml(t("decision.pilotReviewAssistNotDecision", ""))}</div>
            ${assist.plain_case_brief ? `<p>${escapeHtml(assist.plain_case_brief)}</p>` : ""}
            <div class="context-grid">${fields}</div>
          </article>
        </section>
      `;
    }

    function renderAiSuggestion(item) {
      const suggestion = aiSuggestionFor(item.case_id);
      if (!suggestion) return "";
      const decision = suggestion.decision ? decisionOptionEntry(suggestion.decision) : null;
      const fields = [
        contextField(t("decision.aiSuggestionDecision", "Suggested decision"), decision ? `${decision.label} / ${decision.code}` : t("common.unknown", "unknown")),
        contextField(t("decision.aiSuggestionRootCauses", "Suggested root causes"), asArray(suggestion.confirmed_root_causes).map(readableLabel)),
        contextField(t("decision.aiSuggestionActions", "Suggested follow-up actions"), asArray(suggestion.confirmed_follow_up_actions).map(readableLabel)),
        contextField(t("decision.aiSuggestionFixture", "Suggested regression-test candidate"), suggestion.fixture_candidate ? t("common.true", "true") : t("common.false", "false")),
        contextField(t("decision.aiSuggestionRationale", "Suggested rationale"), suggestion.rationale || "", "span-2"),
        suggestion.notes ? contextField(t("decision.aiSuggestionNotes", "Suggested notes"), suggestion.notes, "span-2") : "",
      ].filter(Boolean).join("");
      return `
        <section class="detail-section">
          <article class="ai-suggestion" data-testid="ai-suggestion-panel">
            <div class="ai-suggestion-head">
              <div>
                <h4>${escapeHtml(t("decision.aiSuggestionTitle", "AI-assisted suggestion"))}</h4>
                <p>${escapeHtml(t("decision.aiSuggestionSubtitle", ""))}</p>
              </div>
              ${pill(t("decision.aiSuggestionBadge", "AI suggestion"), "pending")}
            </div>
            <p>${escapeHtml(t("decision.aiSuggestionNoReviewerCopy", ""))}</p>
            ${suggestion.imported_at ? `<p><strong>${escapeHtml(t("decision.aiSuggestionImportedAt", "Loaded at"))}</strong> ${escapeHtml(formatDateTime(suggestion.imported_at))}</p>` : ""}
            <div class="context-grid">${fields}</div>
            <div class="ai-suggestion-actions">
              <button class="button primary" data-action="apply-ai-suggestion">${escapeHtml(t("actions.applyAiSuggestion", "Copy AI suggestion to draft"))}</button>
              <button class="button" data-action="clear-ai-suggestion">${escapeHtml(t("actions.clearAiSuggestion", "Clear AI suggestion"))}</button>
            </div>
          </article>
        </section>
      `;
    }

    function renderPilotBatchPanel(item) {
      const pilot = pilotBatchFor(item);
      if (!pilot) return "";
      const reviewed = Boolean(pilotChecklistState[item.case_id] && pilotChecklistState[item.case_id].reviewed);
      const evidenceIssues = pilot.evidence_issue_summary || {};
      const evidenceToCheck = pilot.evidence_to_check || {};
      const prescreen = pilot.prescreen_advice || {};
      const advisory = pilot.ai_suggestion || {};
      const decisionNeeded = pilot.reviewer_decision_needed || {};
      const missingEvidence = [
        ...asArray(evidenceToCheck.missing_final_expected),
        ...asArray(evidenceToCheck.missing_scenario_core),
        ...asArray(evidenceToCheck.lost_evidence),
      ].map(pilotEvidencePreview).filter(Boolean).slice(0, 8);
      const finalEvidence = asArray(evidenceToCheck.final_evidence).map(pilotEvidencePreview).filter(Boolean).slice(0, 5);
      const optionRows = asArray(decisionNeeded.allowed_options).map(option => `
        <li><strong>${escapeHtml(option.plain_label || option.option_code || "")}</strong>${option.meaning ? ` - ${escapeHtml(option.meaning)}` : ""}</li>
      `).join("");
      const fields = [
        contextField(t("decision.pilotBatchRank", "Pilot rank"), pilot.rank),
        contextField(t("decision.pilotBatchSelectionScore", "Selection score"), pilot.selection_score),
        contextField(t("decision.pilotBatchHumanRequired", "Human confirmation required"), decisionNeeded.human_confirmation_required ? t("common.true", "true") : t("common.false", "false")),
        contextField(t("decision.pilotBatchRequiredFields", "Minimum fields for later export"), decisionNeeded.minimum_fields_for_later_workbench),
        contextField(t("decision.pilotBatchOptionalFields", "Optional or conditional fields"), decisionNeeded.optional_or_conditional_fields, "span-2"),
        contextField(t("decision.pilotBatchWhySelected", "Why review first"), pilot.why_selected, "span-2"),
        contextField(t("decision.pilotBatchEvidenceIssues", "Evidence issue summary"), evidenceIssues.plain_summary, "span-2"),
        contextField(t("decision.pilotBatchFinalEvidence", "Final evidence chain"), finalEvidence, "span-2"),
        contextField(t("decision.pilotBatchMissingEvidence", "Missing or lost evidence"), missingEvidence, "span-2"),
        contextField(t("decision.pilotBatchPrescreen", "Prescreen reference"), [
          prescreen.category_label,
          prescreen.confidence ? `${prescreen.confidence} confidence` : "",
          prescreen.plain_language_guidance,
          prescreen.prescreen_suggested_advisory_decision,
        ].filter(Boolean), "span-2"),
        contextField(t("decision.pilotBatchAdvisoryDecision", "Advisory decision"), advisory.advisory_decision),
        contextField(t("decision.pilotBatchAdvisoryRootCauses", "Advisory root causes"), advisory.advisory_root_causes),
        contextField(t("decision.pilotBatchAdvisoryActions", "Advisory follow-up actions"), advisory.advisory_follow_up_actions, "span-2"),
        contextField(t("decision.pilotBatchAdvisoryFixture", "Advisory regression-test candidate"), advisory.advisory_fixture_candidate === undefined ? "" : (advisory.advisory_fixture_candidate ? t("common.true", "true") : t("common.false", "false"))),
        contextField(t("decision.pilotBatchRationale", "Advisory rationale"), advisory.rationale, "span-2"),
        contextField(t("decision.pilotBatchNotes", "Advisory notes"), advisory.notes, "span-2"),
      ].filter(Boolean).join("");
      return `
        <section class="detail-section">
          <article class="ai-suggestion pilot-batch-panel" data-testid="pilot-batch-panel">
            <div class="ai-suggestion-head">
              <div>
                <h4>${escapeHtml(t("decision.pilotBatchTitle", "Pilot batch human judgment checklist"))}</h4>
                <p>${escapeHtml(t("decision.pilotBatchSubtitle", ""))}</p>
              </div>
              ${pill(t("decision.pilotBatchBadge", "Pilot batch"), "priority")}
            </div>
            <div class="notice">${escapeHtml(t("decision.pilotBatchNotDecision", ""))}</div>
            <p>${escapeHtml(t("decision.pilotBatchNoReviewerCopy", ""))}</p>
            <div class="context-grid">${fields}</div>
            ${optionRows ? `
              <div class="decision-workflow">
                <strong>${escapeHtml(t("decision.pilotBatchAllowedOptions", "Human judgment options"))}</strong>
                <ol>${optionRows}</ol>
              </div>
            ` : ""}
            ${decisionNeeded.plain_instruction ? `
              <div class="decision-workflow">
                <strong>${escapeHtml(t("decision.pilotBatchInstruction", "Human instruction"))}</strong>
                <p>${escapeHtml(decisionNeeded.plain_instruction)}</p>
              </div>
            ` : ""}
            <label class="check-option">
              <input type="checkbox" data-action="toggle-pilot-checklist" ${reviewed ? "checked" : ""} />
              <span><strong>${escapeHtml(t("decision.pilotBatchReviewed", ""))}</strong><small>${escapeHtml(t("decision.pilotBatchNotDecision", ""))}</small></span>
            </label>
          </article>
        </section>
      `;
    }

    function loadDrafts() {
      try {
        const raw = window.localStorage.getItem(stateKey);
        return raw ? JSON.parse(raw) : {};
      } catch {
        return {};
      }
    }

    function loadAiSuggestions() {
      try {
        const raw = window.localStorage.getItem(aiSuggestionStateKey);
        return raw ? JSON.parse(raw) : {};
      } catch {
        return {};
      }
    }

    function loadPilotChecklistState() {
      try {
        const raw = window.localStorage.getItem(pilotChecklistStateKey);
        return raw ? JSON.parse(raw) : {};
      } catch {
        return {};
      }
    }

    function persistPilotChecklistState() {
      window.localStorage.setItem(pilotChecklistStateKey, JSON.stringify(pilotChecklistState));
    }

    function loadExportState() {
      try {
        const raw = window.localStorage.getItem(exportStateKey);
        return raw ? JSON.parse(raw) : {};
      } catch {
        return {};
      }
    }

    function loadImportState() {
      try {
        const raw = window.localStorage.getItem(importStateKey);
        return raw ? JSON.parse(raw) : {};
      } catch {
        return {};
      }
    }

    function persistDrafts() {
      window.localStorage.setItem(stateKey, JSON.stringify(drafts));
      render();
    }

    function persistAiSuggestions() {
      window.localStorage.setItem(aiSuggestionStateKey, JSON.stringify(aiSuggestions));
    }

    function persistExportState() {
      window.localStorage.setItem(exportStateKey, JSON.stringify(exportState));
    }

    function persistImportState() {
      window.localStorage.setItem(importStateKey, JSON.stringify(importState));
    }

    function touchDraft(caseId) {
      const draft = caseDraft(caseId);
      draft.updated_at = new Date().toISOString();
      drafts[caseId] = draft;
    }

    function latestDraftUpdatedAt() {
      return Object.values(drafts)
        .map(draft => draft && draft.updated_at)
        .filter(Boolean)
        .sort()
        .pop() || "";
    }

    function formatDateTime(value) {
      if (!value) return "";
      try {
        return new Date(value).toLocaleString(currentLanguage === "en-US" ? "en-US" : "zh-CN");
      } catch {
        return value;
      }
    }

    function exportStatusSummary() {
      const lastExportedAt = exportState.last_exported_at || "";
      const latestUpdatedAt = latestDraftUpdatedAt();
      if (!lastExportedAt) return { state: "never", label: t("exportStatus.never", "Not exported") };
      if (latestUpdatedAt && latestUpdatedAt > lastExportedAt) {
        return { state: "dirty", label: t("exportStatus.dirty", "Unexported changes") };
      }
      return { state: "clean", label: `${t("exportStatus.clean", "Exported")} ${formatDateTime(lastExportedAt)}` };
    }

    function draftSaveSummary(draft) {
      const lastSavedAt = draft && draft.saved_at ? draft.saved_at : "";
      const updatedAt = draft && draft.updated_at ? draft.updated_at : "";
      if (!lastSavedAt) {
        return { state: "never", label: t("draftSave.never", "Not manually saved yet") };
      }
      if (updatedAt && updatedAt > lastSavedAt) {
        return { state: "dirty", label: t("draftSave.dirty", "Unmanually saved updates") };
      }
      return {
        state: "saved",
        label: formatMessage(t("draftSave.savedAt", "Last saved {time}"), { time: formatDateTime(lastSavedAt) }),
      };
    }

    function importStatusSummary() {
      if (!importState.last_imported_at) {
        return { state: "never", label: t("reviewImport.never", "No draft import yet") };
      }
      if (importState.suggestion_rows) {
        return {
          state: importState.error ? "error" : "ready",
          label: formatMessage(t("reviewImport.lastImportedWithSuggestions", "{imported} drafts filled, {suggestions} AI suggestions loaded, {unknown} unmatched, {skipped} empty"), {
            imported: importState.imported_rows || 0,
            suggestions: importState.suggestion_rows || 0,
            cleared: importState.cleared_draft_rows || 0,
            unknown: importState.unknown_rows || 0,
            duplicate: importState.duplicate_rows || 0,
            skipped: importState.skipped_rows || 0,
          }),
        };
      }
      return {
        state: importState.error ? "error" : "ready",
        label: formatMessage(t("reviewImport.lastImported", "{imported} filled, {unknown} unmatched, {skipped} empty"), {
          imported: importState.imported_rows || 0,
          cleared: importState.cleared_draft_rows || 0,
          unknown: importState.unknown_rows || 0,
          duplicate: importState.duplicate_rows || 0,
          skipped: importState.skipped_rows || 0,
        }),
      };
    }

    function renderImportSummary() {
      const target = document.getElementById("import-summary");
      if (!target) return;
      const summary = importStatusSummary();
      target.className = `import-summary ${importState.last_imported_at ? "visible" : ""} ${summary.state === "error" ? "error" : ""}`;
      if (!importState.last_imported_at) {
        target.textContent = "";
        return;
      }
      const prefix = importState.error
        ? formatMessage(t("reviewImport.error", "Import failed: {message}"), { message: importState.error })
        : (importState.suggestion_rows
          ? t("reviewImport.successWithSuggestions", "Rows were matched by case_id; AI prefills were loaded only as suggestions, not manual decisions.")
          : t("reviewImport.success", "Import completed: imported drafts replaced old local drafts so stale drafts cannot mix into the next export."));
      target.textContent = `${prefix} ${summary.label}`;
    }

    function escapeHtml(value) {
      return String(value ?? "").replace(/[&<>"']/g, char => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
      }[char]));
    }

    function asArray(value) {
      if (Array.isArray(value)) return value.filter(item => item !== null && item !== undefined && String(item).trim() !== "");
      if (value === null || value === undefined || value === "") return [];
      return [value];
    }

    function highPriorityIds() {
      return asArray(workbenchSummary.high_priority_case_ids);
    }

    function pilotBatchCaseIds() {
      return items
        .filter(item => pilotBatchFor(item))
        .sort((left, right) => Number(pilotBatchFor(left).rank || 9999) - Number(pilotBatchFor(right).rank || 9999))
        .map(item => item.case_id);
    }

    function itemByCaseId(caseId) {
      return items.find(item => item.case_id === caseId) || items[0] || null;
    }

    function currentItem() {
      return itemByCaseId(selectedCaseId);
    }

    function caseDraft(caseId) {
      if (!drafts[caseId]) {
        const item = itemByCaseId(caseId);
        const template = item && item.reviewer_input_template ? item.reviewer_input_template : {};
        drafts[caseId] = looksLikeAiAssistedSource(template, payload) ? {} : draftTemplateFromImportRow(template);
      }
      return drafts[caseId];
    }

    function aiSuggestionFor(caseId) {
      return aiSuggestions[caseId] || null;
    }

    function humanDraftForExport(caseId) {
      const draft = drafts[caseId] || {};
      const status = draftStatus(draft);
      if (!status.ready) return {};
      const sanitized = {};
      reviewerDraftFields.forEach(field => {
        if (Object.prototype.hasOwnProperty.call(draft, field)) {
          sanitized[field] = draft[field];
        }
      });
      return sanitized;
    }

    function currentCaseIds() {
      return new Set(items.map(item => item.case_id));
    }

    function draftCaseIdsWithContent() {
      const knownCases = currentCaseIds();
      return Object.keys(drafts).filter(caseId => knownCases.has(caseId) && hasDraftContent(drafts[caseId]));
    }

    function readyDraftCaseIds() {
      return draftCaseIdsWithContent().filter(caseId => draftStatus(drafts[caseId]).ready);
    }

    function blockedDraftCaseIds() {
      return draftCaseIdsWithContent().filter(caseId => !draftStatus(drafts[caseId]).ready);
    }

    function hasDraftContent(draft) {
      if (!draft) return false;
      return Boolean(
        draft.reviewer || draft.reviewed_at || draft.decision ||
        asArray(draft.confirmed_root_causes).length ||
        asArray(draft.rejected_root_causes).length ||
        asArray(draft.confirmed_follow_up_actions).length ||
        asArray(draft.proposed_change_targets).length ||
        draft.fixture_candidate || draft.rationale || draft.notes
      );
    }

    function decisionIsTerminal(decision) {
      return ["confirm_diagnostic_issue", "confirm_scope_adjustment_needed", "reject_diagnostic_issue"].includes(decision);
    }

    function hasOnlyAllowedValues(values, allowed) {
      const allowedSet = new Set(asArray(allowed));
      return asArray(values).every(value => allowedSet.has(value));
    }

    function draftStatus(draft) {
      const issues = [];
      const decision = draft && draft.decision ? draft.decision : "";
      if (!hasDraftContent(draft)) {
        return { ready: false, issues: ["empty_draft"], severity: "pending" };
      }
      if (!draft.reviewer) issues.push("missing_reviewer");
      if (!draft.reviewed_at) issues.push("missing_reviewed_at");
      if (!decision) issues.push("missing_decision");
      if (!draft.rationale) issues.push("missing_rationale");
      if (decision && !asArray(allowedValues.decision).includes(decision)) issues.push("invalid_decision");
      if (!hasOnlyAllowedValues(draft.confirmed_root_causes, allowedValues.confirmed_root_causes)) issues.push("invalid_confirmed_root_cause");
      if (!hasOnlyAllowedValues(draft.rejected_root_causes, allowedValues.rejected_root_causes)) issues.push("invalid_rejected_root_cause");
      if (!hasOnlyAllowedValues(draft.confirmed_follow_up_actions, allowedValues.confirmed_follow_up_actions)) issues.push("invalid_follow_up_action");
      if (decisionIsTerminal(decision) && asArray(draft.confirmed_root_causes).length === 0 && decision !== "reject_diagnostic_issue") {
        issues.push("missing_confirmed_root_cause");
      }
      if (draft.ai_suggestion_applied_at && !draft.human_confirmed_ai_suggestion) {
        issues.push("missing_ai_suggestion_confirmation");
      }
      const targets = asArray(draft.proposed_change_targets).map(value => String(value).trim()).filter(Boolean);
      const blocked = targets.filter(target => prohibitedTargets.includes(target));
      if (blocked.length) issues.push("prohibited_change_target:" + blocked.join("|"));
      return { ready: issues.length === 0, issues, severity: issues.length ? "warning" : "ready" };
    }

    function matchesFilter(item) {
      if (!item) return false;
      const draft = drafts[item.case_id] || {};
      if (currentFilter === "high_priority" && !highPriorityIds().includes(item.case_id)) return false;
      if (currentFilter === "pilot_batch" && !pilotBatchCaseIds().includes(item.case_id)) return false;
      if (currentFilter === "awaiting_manual_review" && item.decision_status !== "pending") return false;
      if (currentFilter === "blocked_intake_gate" && ((closeoutReport.summary || {}).gate_status !== "blocked")) return false;
      if (currentFilter === "with_local_draft" && !hasDraftContent(draft)) return false;
      if (currentFilter === "ready_for_export" && !draftStatus(draft).ready) return false;
      if (!query) return true;
      const haystack = [
        item.case_id,
        caseTopic(item),
        caseContext(item).question,
        asArray(caseContext(item).expected_risk_types).join(" "),
        asArray(caseContext(item).expected_actions).join(" "),
        asArray(caseContext(item).scenario_contexts).map(scenario => [scenario.scenario_id, scenario.description, scenario.domain].join(" ")).join(" "),
        item.risk_level,
        asArray(item.expected_domains).join(" "),
        asArray(item.queue_tags).join(" "),
        asArray(item.issue_types).join(" "),
        asArray(item.suggested_root_causes).join(" "),
        asArray(item.suggested_follow_up_actions).join(" "),
        pilotBatchFor(item) ? asArray(pilotBatchFor(item).why_selected).join(" ") : "",
        pilotBatchFor(item) ? asArray((pilotBatchFor(item).evidence_issue_summary || {}).plain_summary).join(" ") : "",
        pilotBatchFor(item) ? ((pilotBatchFor(item).prescreen_advice || {}).plain_language_guidance || "") : "",
        pilotBatchFor(item) ? ((pilotBatchFor(item).ai_suggestion || {}).advisory_decision || "") : "",
        pilotReviewAssistFor(item) ? (pilotReviewAssistFor(item).advisory_tendency_label || "") : "",
        pilotReviewAssistFor(item) ? (pilotReviewAssistFor(item).support_status_label || "") : "",
        pilotReviewAssistFor(item) ? asArray(pilotReviewAssistFor(item).focus_questions_for_user).join(" ") : "",
      ].join(" ").toLowerCase();
      return haystack.includes(query.toLowerCase());
    }

    function filteredItems() {
      const visible = items.filter(matchesFilter);
      if (currentFilter !== "pilot_batch") return visible;
      const rankByCaseId = new Map(pilotBatchCaseIds().map((caseId, index) => [caseId, index]));
      return visible.sort((left, right) => (
        (rankByCaseId.get(left.case_id) ?? 9999) - (rankByCaseId.get(right.case_id) ?? 9999)
      ));
    }

    function pill(value, extra = "") {
      return `<span class="pill ${extra}">${escapeHtml(value)}</span>`;
    }

    function render() {
      renderStaticText();
      renderQueues();
      renderSideStatus();
      renderGlobalPipeline();
      renderGuide();
      renderLanguageSelect();
      renderBadges();
      renderKpis();
      renderCaseList();
      renderDetail();
    }

    function renderStaticText() {
      document.documentElement.lang = currentLanguage;
      document.title = t("documentTitle", "Legal Risk Review Workbench");
      document.getElementById("brand-kicker").textContent = t("brand.kicker", "");
      document.getElementById("brand-title").textContent = t("brand.title", "");
      document.getElementById("brand-subtitle").textContent = t("brand.subtitle", "");
      document.getElementById("queues-section-title").textContent = t("sections.queues", "Queues");
      document.getElementById("status-section-title").textContent = t("sections.status", "Status");
      document.getElementById("global-pipeline-section-title").textContent = t("sections.globalPipeline", "Global process");
      document.getElementById("global-pipeline-subtitle").textContent = t("pipeline.subtitle", "");
      document.getElementById("guide-section-title").textContent = t("sections.guide", "Operation Guide");
      document.getElementById("topbar-title").textContent = t("topbar.title", "Manual Evidence Review");
      document.getElementById("topbar-subtitle").textContent = t("topbar.subtitle", "");
      document.getElementById("language-label").textContent = t("language.label", "Language");
      document.getElementById("case-queue-title").textContent = t("caseQueue.title", "Case Queue");
      document.getElementById("search-input").placeholder = t("caseQueue.searchPlaceholder", "");
      const importButton = document.querySelector('[data-action="import-review-file"]');
      if (importButton) {
        importButton.textContent = t("actions.importReviewFile", "Import review file");
        importButton.title = t("reviewImport.dialogTitle", "Import an exported review file");
      }
      renderImportSummary();
    }

    function renderQueues() {
      document.getElementById("queue-nav").innerHTML = visibleQueueDefs().map(queue => `
        <button class="nav-button ${currentFilter === queue.key ? "active" : ""}" data-filter="${escapeHtml(queue.key)}">
          <span>${escapeHtml(t(queue.labelKey, queue.key))}</span>
          <span class="count">${escapeHtml(queue.count())}</span>
        </button>
      `).join("");
    }

    function renderSideStatus() {
      const summary = closeoutReport.summary || {};
      const exportSummary = exportStatusSummary();
      const importSummary = importStatusSummary();
      const blockers = asArray(summary.blockers || summary.gate_blockers);
      document.getElementById("side-status").innerHTML = [
        [t("sideStatus.gate", "Gate"), localizedStatus(summary.gate_status || "unknown")],
        [t("sideStatus.gateBlockers", "Gate blockers"), blockers.length ? blockers.map(readableLabel).join(" | ") : t("sideStatus.noGateBlockers", "No blockers")],
        [t("sideStatus.imported", "Imported"), summary.imported_rows ?? 0],
        [t("sideStatus.rejected", "Rejected"), summary.rejected_rows ?? 0],
        [t("sideStatus.readyActions", "Ready actions"), summary.ready_action_candidates ?? 0],
        [t("sideStatus.localDrafts", "Local drafts"), draftCaseIdsWithContent().length],
        [t("exportStatus.lastExportedAt", "Last exported"), exportSummary.label],
        [t("reviewImport.statusLabel", "Page import"), importSummary.label],
      ].map(([label, value]) => `<div class="mini-stat"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("");
    }

    function pipelineSteps() {
      const closeout = closeoutReport.summary || {};
      const importSummary = importReport.summary || {};
      const diffSummary = diffReport.summary || {};
      const validationSummary = validationReport.summary || {};
      const promotionSummary = promotionReport.summary || {};
      const diffBlocked = diffSummary.blocked_cases ?? diffSummary.blocked_diff_cases ?? 0;
      const diffState = diffBlocked ? "blocked" : "ready";
      return [
        [
          t("pipeline.import", "Import"),
          formatMessage(t("pipeline.importValue", "{imported} imported / {rejected} rejected"), {
            imported: importSummary.imported_rows ?? 0,
            rejected: importSummary.rejected_rows ?? 0,
          }),
          importSummary.imported_rows ? "ready" : "blocked",
        ],
        [
          t("pipeline.diff", "Diff"),
          formatMessage(t(diffBlocked ? "pipeline.diffValue" : "pipeline.diffValueNoBlockers", "{changed} changed / {blocked} blocked"), {
            changed: diffSummary.changed_cases ?? 0,
            blocked: diffBlocked,
          }),
          diffState,
        ],
        [
          t("pipeline.validation", "Validation"),
          formatMessage(t("pipeline.validationValue", "{valid} valid / {invalid} invalid / {pending} pending"), {
            valid: validationSummary.valid_records ?? 0,
            invalid: validationSummary.invalid_records ?? 0,
            pending: validationSummary.pending_records ?? 0,
          }),
          validationSummary.valid_records ? "ready" : "pending",
        ],
        [
          t("pipeline.promotion", "Promotion"),
          formatMessage(t("pipeline.promotionValue", "{candidates} candidates / {ready} ready actions"), {
            candidates: promotionSummary.promotion_candidates ?? 0,
            ready: promotionSummary.ready_action_candidates ?? 0,
          }),
          promotionSummary.ready_action_candidates ? "ready" : "blocked",
        ],
        [t("pipeline.closeout", "Closeout"), localizedStatus(closeout.gate_status || "unknown"), closeout.gate_status === "open" ? "ready" : "blocked"],
      ];
    }

    function renderPipelineSteps() {
      return pipelineSteps().map(([label, value, state]) => `
        <div class="pipeline-step">
          <div class="step-label">${escapeHtml(label)}</div>
          <div class="step-value">${escapeHtml(value)}</div>
          ${pill(t(`pipeline.states.${state}`, state), state === "ready" ? "ready" : "pending")}
        </div>
      `).join("");
    }

    function renderGlobalPipeline() {
      document.getElementById("global-pipeline").innerHTML = renderPipelineSteps();
    }

    function renderGuide() {
      const steps = tArray("guide.steps", uiConfig.guide_steps || []);
      document.getElementById("side-guide").innerHTML = steps.map(step => `<li>${escapeHtml(step)}</li>`).join("");
    }

    function renderLanguageSelect() {
      const select = document.getElementById("language-select");
      const languages = asArray(uiConfig.supported_languages);
      select.innerHTML = languages.map(language => `
        <option value="${escapeHtml(language.code)}" ${language.code === currentLanguage ? "selected" : ""}>${escapeHtml(language.label)}</option>
      `).join("");
      select.disabled = languages.length <= 1;
      select.title = t("language.selectTitle", "Switch interface language");
    }

    function renderBadges() {
      const gate = gateStatus();
      const ready = payload.summary && payload.summary.ready_for_static_review;
      const exportSummary = exportStatusSummary();
      document.getElementById("top-badges").innerHTML = `
        <span class="badge ${gateBadgeClass()}">${escapeHtml(t("badges.gate", "Gate"))} ${escapeHtml(localizedStatus(gate))}</span>
        <span class="badge ${ready ? "ready" : "danger"}">${escapeHtml(t("badges.staticData", "Static data"))} ${escapeHtml(ready ? t("badges.ready", "ready") : t("badges.missing", "missing"))}</span>
        <span class="badge ${exportSummary.state === "dirty" ? "blocked" : (exportSummary.state === "clean" ? "ready" : "")}">${escapeHtml(exportSummary.label)}</span>
        <span class="badge">${escapeHtml(t("badges.version", "Version"))} ${escapeHtml(payload.version)}</span>
      `;
    }

    function renderKpis() {
      const closeout = closeoutReport.summary || {};
      const validation = validationReport.summary || {};
      const promotion = promotionReport.summary || {};
      const kpis = [
        [t("kpis.cases", "Cases"), workbenchSummary.total_workbench_items ?? items.length],
        [t("kpis.pending", "Pending"), workbenchSummary.pending_items ?? 0],
        [t("kpis.highPriority", "High priority"), workbenchSummary.high_priority_items ?? 0],
        [t("kpis.imported", "Imported"), closeout.imported_rows ?? 0],
        [t("kpis.validProposed", "Valid proposed"), validation.valid_records ?? 0],
        [t("kpis.readyActions", "Ready actions"), promotion.ready_action_candidates ?? 0],
      ];
      document.getElementById("kpi-grid").innerHTML = kpis.map(([label, value]) => `
        <article class="kpi">
          <div class="kpi-value">${escapeHtml(value)}</div>
          <div class="kpi-label">${escapeHtml(label)}</div>
        </article>
      `).join("");
    }

    function renderCaseList() {
      const visible = filteredItems();
      document.getElementById("case-count-label").textContent = formatMessage(
        t("caseQueue.count", "{visible} visible / {total} total"),
        { visible: visible.length, total: items.length }
      );
      if (!visible.length) {
        document.getElementById("case-list").innerHTML = `<div class="empty-state">${escapeHtml(t("caseQueue.empty", "No matching cases"))}</div>`;
        return;
      }
      if (!visible.some(item => item.case_id === selectedCaseId)) {
        selectedCaseId = visible[0].case_id;
      }
      document.getElementById("case-list").innerHTML = visible.map(item => {
        const draft = drafts[item.case_id] || {};
        const status = draftStatus(draft);
        const pilot = pilotBatchFor(item);
        const domains = asArray(item.expected_domains).slice(0, 3).map(value => explainedPill(value)).join("");
        const tags = asArray(item.queue_tags).slice(0, 3).map(value => explainedPill(value)).join("");
        const context = caseContext(item);
        return `
          <button class="case-row ${item.case_id === selectedCaseId ? "active" : ""}" data-case-id="${escapeHtml(item.case_id)}">
            <span class="case-title">
              <strong>${escapeHtml(item.case_id)}</strong>
              ${pill("P" + (item.priority_score ?? 0), Number(item.priority_score || 0) >= 10 ? "priority" : "")}
            </span>
            <p class="case-topic">${escapeHtml(caseTopic(item))}</p>
            ${context.question ? `<p class="case-question">${escapeHtml(context.question)}</p>` : ""}
            <span class="case-meta">
              ${pill(localizedStatus(item.risk_level || "unknown"), item.risk_level === "high" ? "high" : "")}
              ${pill(localizedStatus(item.decision_status || "pending"), item.decision_status || "pending")}
              ${pilot ? pill(t("decision.pilotBatchBadge", "Pilot batch") + " #" + (pilot.rank || ""), "priority") : ""}
              ${hasDraftContent(draft) ? pill(status.ready ? t("caseBadges.draftReady", "draft ready") : t("caseBadges.draftNeedsReview", "draft needs review"), status.ready ? "ready" : "pending") : ""}
            </span>
            <span class="case-meta">${domains}${tags}</span>
          </button>
        `;
      }).join("");
    }

    function renderDetail() {
      const item = currentItem();
      if (!item) {
        document.getElementById("detail-header").innerHTML = `<div><h3>${escapeHtml(t("detail.noCaseSelected", "No case selected"))}</h3></div>`;
        document.getElementById("tab-row").innerHTML = "";
        document.getElementById("detail-body").innerHTML = `<div class="empty-state">${escapeHtml(t("detail.noCaseData", "No case data"))}</div>`;
        return;
      }
      const draft = caseDraft(item.case_id);
      const status = draftStatus(draft);
      renderDetailHeader(item, draft, status);
      document.getElementById("tab-row").innerHTML = tabDefs.map(tab => `
        <button class="tab-button ${activeTab === tab.key ? "active" : ""}" data-tab="${escapeHtml(tab.key)}">${escapeHtml(t(tab.labelKey, tab.key))}</button>
      `).join("");
      const renderers = {
        overview: () => renderOverview(item),
        evidence: () => renderEvidence(item),
        questions: () => renderQuestions(item),
        glossary: () => renderGlossary(item),
        decision: () => renderDecision(item, draft, status),
      };
      if (!renderers[activeTab]) {
        activeTab = "overview";
      }
      document.getElementById("detail-body").innerHTML = renderers[activeTab]();
      bindDecisionInputs(item, draft);
    }

    function renderDetailHeader(item, draft, status) {
      const exportSummary = exportStatusSummary();
      const saveSummary = draftSaveSummary(draft);
      const suggestion = aiSuggestionFor(item.case_id);
      const pilot = pilotBatchFor(item);
      document.getElementById("detail-header").innerHTML = `
        <div class="detail-title">
          <h3>${escapeHtml(item.case_id)}</h3>
          <p class="case-topic">${escapeHtml(caseTopic(item))}</p>
          <div class="case-meta">
            ${pill(localizedStatus(item.risk_level || "unknown"), item.risk_level === "high" ? "high" : "")}
            ${pill(t("caseBadges.priority", "priority") + " " + (item.priority_score ?? 0), Number(item.priority_score || 0) >= 10 ? "priority" : "")}
            ${pill(status.ready ? t("caseBadges.exportReady", "export ready") : t("caseBadges.reviewPending", "review pending"), status.ready ? "ready" : "pending")}
            ${suggestion ? pill(t("decision.aiSuggestionBadge", "AI suggestion"), "pending") : ""}
            ${pilot ? pill(t("decision.pilotBatchBadge", "Pilot batch") + " #" + (pilot.rank || ""), "priority") : ""}
            ${pill(exportSummary.label, exportSummary.state === "dirty" ? "pending" : (exportSummary.state === "clean" ? "ready" : ""))}
            ${hasDraftContent(draft) ? pill(saveSummary.label, saveSummary.state === "saved" ? "ready" : "pending") : ""}
            ${draft.updated_at ? pill(`${t("exportStatus.updatedAt", "Last updated")} ${formatDateTime(draft.updated_at)}`) : ""}
          </div>
        </div>
        <div class="actions">
          <button class="button primary" data-action="save-case-draft">${escapeHtml(t("actions.saveDraft", "Save draft"))}</button>
          ${suggestion ? `<button class="button" data-action="apply-ai-suggestion">${escapeHtml(t("actions.applyAiSuggestion", "Copy AI suggestion to draft"))}</button>` : ""}
          <button class="button" data-action="clear-case-draft">${escapeHtml(t("actions.clearDraft", "Clear draft"))}</button>
          <button class="button primary" data-action="export-json">${escapeHtml(t("actions.exportJson", "Export ready drafts JSON"))}</button>
          <button class="button blue" data-action="export-csv">${escapeHtml(t("actions.exportCsv", "Download view-only CSV"))}</button>
        </div>
      `;
    }

    function renderOverview(item) {
      const diagnostic = item.diagnostic_summary || {};
      const sections = Object.entries(diagnostic).map(([name, value]) => {
        const issues = asArray(value.detected_issues);
        const reasons = asArray(value.review_reasons);
        const roots = asArray(value.root_causes);
        return `
          <article class="summary-item">
            <h4>${escapeHtml(name)}</h4>
            <div class="case-meta">${issues.slice(0, 8).map(issue => explainedPill(issue, "pending")).join("")}</div>
            ${reasons.length ? `<ul>${reasons.slice(0, 5).map(reason => `<li>${escapeHtml(reason)}</li>`).join("")}</ul>` : ""}
            ${roots.length ? `<p>${escapeHtml(t("overview.rootCauses", "Root causes"))}: ${roots.map(root => explainedPill(root)).join(" ")}</p>` : ""}
          </article>
        `;
      }).join("");
      return `
        ${renderCaseContextBlock(item)}
        ${renderOriginalOutput(item)}
        <section class="detail-section">
          <div class="case-meta">
            ${asArray(item.expected_domains).map(value => explainedPill(value)).join("")}
            ${asArray(item.issue_types).slice(0, 8).map(value => explainedPill(value, "pending")).join("")}
            ${asArray(item.suggested_root_causes).slice(0, 6).map(value => explainedPill(value)).join("")}
          </div>
        </section>
        <section class="detail-section data-block">
          <div class="summary-list">${sections || `<div class="empty-state">${escapeHtml(t("overview.emptyDiagnostic", "No diagnostic summary"))}</div>`}</div>
        </section>
      `;
    }

    function evidenceLabel(key) {
      return t(`evidence.${key}`, key);
    }

    function renderEvidence(item) {
      const context = item.evidence_context || {};
      const blocks = Object.entries(context).map(([key, rows]) => {
        const list = asArray(rows);
        if (!list.length) return "";
        return `
          <article class="summary-item">
            <h4>${escapeHtml(evidenceLabel(key))} (${list.length})</h4>
            <table class="evidence-table">
              <thead><tr><th>${escapeHtml(t("evidence.source", "Source"))}</th><th>${escapeHtml(t("evidence.article", "Article"))}</th><th>${escapeHtml(t("evidence.content", "Content"))}</th></tr></thead>
              <tbody>
                ${list.map(row => `
                  <tr>
                    <td>${escapeHtml(row.source || row.law_name || row.citation || "")}</td>
                    <td>${escapeHtml(row.article_no || row.article || row.section_no || "")}</td>
                    <td class="evidence-text">${escapeHtml(row.content || row.matched_content || row.text || JSON.stringify(row))}</td>
                  </tr>
                `).join("")}
              </tbody>
            </table>
          </article>
        `;
      }).join("");
      return `
        ${renderOriginalOutput(item)}
        <section class="detail-section"><div class="summary-list">${blocks || `<div class="empty-state">${escapeHtml(t("evidence.empty", "No evidence context"))}</div>`}</div></section>
      `;
    }

    function renderQuestions(item) {
      const questions = asArray(item.suggested_review_questions);
      const rows = questions.map(question => {
        const entry = reviewQuestionEntry(question);
        const showOriginal = currentLanguage !== "en-US" && entry.original && entry.original !== entry.label;
        return `
          <div class="question-card">
            <strong>${escapeHtml(entry.label)}</strong>
            ${showOriginal ? `<small>${escapeHtml(t("questions.original", "Original question"))}: ${escapeHtml(entry.original)}</small>` : ""}
          </div>
        `;
      }).join("");
      return `
        <section class="detail-section">
          <div class="summary-item">
            <h4>${escapeHtml(t("questions.title", "Suggested review questions"))}</h4>
            ${questions.length ? `<div class="question-list">${rows}</div>` : `<p>${escapeHtml(t("questions.empty", "No questions"))}</p>`}
          </div>
        </section>
      `;
    }

    function glossaryRows(title, codes, targetTab) {
      const uniqueCodes = Array.from(new Set(asArray(codes).map(value => String(value)).filter(Boolean)));
      if (!uniqueCodes.length) return "";
      return `
        <article class="summary-item">
          <h4>${escapeHtml(title)}</h4>
          <div class="glossary-grid">
            ${uniqueCodes.map(code => {
              const entry = glossaryEntry(code) || { label: code, description: "", code };
              return `
                <div class="glossary-card" id="glossary-${escapeHtml(code)}">
                  <h4>${escapeHtml(entry.label)}</h4>
                  <div class="glossary-code">${escapeHtml(t("glossary.code", "Code"))}: ${escapeHtml(entry.code)}</div>
                  ${entry.description ? `<p>${escapeHtml(entry.description)}</p>` : ""}
                  ${targetTab ? `<button class="jump-link" data-jump-tab="${escapeHtml(targetTab)}">${escapeHtml(t("glossary.jumpTo", "Go to"))}</button>` : ""}
                </div>
              `;
            }).join("")}
          </div>
        </article>
      `;
    }

    function renderGlossary(item) {
      const diagnostic = item.diagnostic_summary || {};
      const closeout = closeoutReport.summary || {};
      const importErrors = asArray((importReport.import_results || [])
        .filter(row => row.case_id === item.case_id)
        .flatMap(row => asArray(row.errors)));
      const sections = [
        glossaryRows(t("glossary.queueTags", "Queue tags"), item.queue_tags, "overview"),
        glossaryRows(t("glossary.issueTypes", "Diagnostic issues"), item.issue_types, "overview"),
        glossaryRows(t("glossary.rootCauses", "Suggested root causes"), item.suggested_root_causes, "decision"),
        glossaryRows(t("glossary.followUpActions", "Suggested follow-up actions"), item.suggested_follow_up_actions, "decision"),
        glossaryRows(t("glossary.diagnostics", "Diagnostics"), Object.keys(diagnostic), "overview"),
        glossaryRows(t("glossary.evidenceContext", "Evidence context"), Object.keys(item.evidence_context || {}), "evidence"),
        glossaryRows(t("glossary.gateBlockers", "Gate blockers"), closeout.blockers || [], ""),
        glossaryRows(t("glossary.importErrors", "Import errors"), importErrors, ""),
        glossaryRows(t("glossary.guardrails", "Guardrails"), Object.keys(guardrails), ""),
      ].filter(Boolean).join("");
      return `
        <section class="detail-section">
          <div class="summary-item">
            <h4>${escapeHtml(t("glossary.title", "Current Case Glossary"))}</h4>
            <p>${escapeHtml(t("glossary.subtitle", ""))}</p>
          </div>
        </section>
        <section class="detail-section data-block">
          <div class="summary-list">${sections || `<div class="empty-state">${escapeHtml(t("glossary.empty", "No explainable tags for this case."))}</div>`}</div>
        </section>
      `;
    }

    function renderDecision(item, draft, status) {
      const decisions = asArray(allowedValues.decision);
      const roots = asArray(allowedValues.confirmed_root_causes);
      const actions = asArray(allowedValues.confirmed_follow_up_actions);
      const noticeClass = status.ready ? "ok" : (status.issues.some(issue => issue.startsWith("prohibited")) ? "danger" : "");
      return `
        ${renderDecisionSummary(item, draft, status)}
        ${renderPilotReviewAssistPanel(item)}
        ${renderPilotBatchPanel(item)}
        ${renderAiSuggestion(item)}
        <section class="detail-section">
          <div class="notice authority">
            <strong>${escapeHtml(t("decision.authorityNoticeTitle", "Manual form is authoritative"))}</strong>
            ${escapeHtml(t("decision.authorityNotice", ""))}
          </div>
        </section>
        <section class="detail-section">
          <div class="notice ${noticeClass}">
            ${status.ready ? escapeHtml(t("decision.readyNotice", "Draft is ready for offline export.")) : escapeHtml(t("decision.statusPrefix", "Draft status: ")) + escapeHtml(status.issues.map(localizedIssue).join(" | "))}
          </div>
          <p class="form-section-note">${escapeHtml(t("draftSave.autoSavedHint", ""))}</p>
        </section>
        <section class="detail-section">
          <form id="decision-form" class="field-grid" data-testid="decision-form">
            <section class="form-section span-2">
              <h4 class="form-section-title">${escapeHtml(t("decision.reviewerInfo", "Reviewer info"))}</h4>
              <p class="form-section-note">${escapeHtml(t("decision.reviewerInfoNote", ""))}</p>
              <label class="field-label">${fieldLabelText(t("decision.reviewer", "Reviewer"), "required", t("decision.reviewerHelp", ""))}
                <input class="field-input" data-field="reviewer" value="${escapeHtml(draft.reviewer || "")}" />
              </label>
              <label class="field-label">${fieldLabelText(t("decision.reviewedAt", "Reviewed at"), "required", t("decision.reviewedAtHelp", ""))}
                <input class="field-input" data-field="reviewed_at" value="${escapeHtml(draft.reviewed_at || "")}" placeholder="${escapeHtml(t("decision.reviewedAtPlaceholder", "YYYY-MM-DD"))}" />
              </label>
            </section>
            <section class="form-section span-2">
              <h4 class="form-section-title">${escapeHtml(t("decision.conclusionSection", "Review conclusion and rationale"))}</h4>
              <p class="form-section-note">${escapeHtml(t("decision.conclusionSectionNote", ""))}</p>
              <p class="form-section-note">${escapeHtml(t("decision.useOriginalCodeHint", ""))}</p>
              <label class="field-label span-2">${fieldLabelText(t("decision.decision", "Decision"), "required", t("decision.decisionHelp", ""))}
                <div class="choice-grid">${decisionChoices(decisions, draft.decision)}</div>
              </label>
              <label class="field-label span-2">${fieldLabelText(t("decision.rationale", "Rationale"), "required", t("decision.rationaleHelp", ""))}
                <textarea class="field-textarea" data-field="rationale" placeholder="${escapeHtml(t("decision.rationalePlaceholder", ""))}">${escapeHtml(draft.rationale || "")}</textarea>
              </label>
            </section>
            <section class="form-section span-2">
              <h4 class="form-section-title">${escapeHtml(t("decision.rootCauseSection", "Root-cause judgment"))}</h4>
              <p class="form-section-note">${escapeHtml(t("decision.rootCauseSectionNote", ""))}</p>
              <label class="field-label span-2">${fieldLabelText(t("decision.confirmedRootCauses", "Confirmed root causes"), "conditional", t("decision.confirmedRootCausesHelp", ""))}
                <div class="checkbox-grid">${checkboxes("confirmed_root_causes", roots, draft.confirmed_root_causes)}</div>
              </label>
              <label class="field-label span-2">${fieldLabelText(t("decision.rejectedRootCauses", "Rejected root causes"), "optional", t("decision.rejectedRootCausesHelp", ""))}
                <div class="checkbox-grid">${checkboxes("rejected_root_causes", roots, draft.rejected_root_causes)}</div>
              </label>
            </section>
            <section class="form-section span-2">
              <h4 class="form-section-title">${escapeHtml(t("decision.actionSection", "Follow-up actions"))}</h4>
              <p class="form-section-note">${escapeHtml(t("decision.actionSectionNote", ""))}</p>
              <label class="field-label span-2">${fieldLabelText(t("decision.confirmedFollowUpActions", "Confirmed follow-up actions"), "optional", t("decision.confirmedFollowUpActionsHelp", ""))}
                <div class="checkbox-grid">${checkboxes("confirmed_follow_up_actions", actions, draft.confirmed_follow_up_actions)}</div>
              </label>
              <label class="field-label span-2">${fieldLabelText(t("decision.proposedChangeTargets", "Proposed change targets"), "optional", t("decision.proposedChangeTargetsHelp", ""))}
                <input class="field-input" data-field="proposed_change_targets" value="${escapeHtml(asArray(draft.proposed_change_targets).join(" | "))}" placeholder="${escapeHtml(t("decision.proposedChangeTargetsPlaceholder", "Use | between targets"))}" />
              </label>
            </section>
            <section class="form-section span-2">
              <h4 class="form-section-title">${escapeHtml(t("decision.governanceSection", "Governance notes"))}</h4>
              <p class="form-section-note">${escapeHtml(t("decision.governanceSectionNote", ""))}</p>
              <label class="check-option">
                <input type="checkbox" data-field="fixture_candidate" ${draft.fixture_candidate ? "checked" : ""} />
                <span><strong>${escapeHtml(t("decision.fixtureCandidate", "Regression-test candidate"))}</strong><small>${escapeHtml(t("decision.fixtureCandidateHint", ""))}</small></span>
              </label>
              ${draft.ai_suggestion_applied_at ? `
                <label class="check-option">
                  <input type="checkbox" data-field="human_confirmed_ai_suggestion" ${draft.human_confirmed_ai_suggestion ? "checked" : ""} />
                  <span><strong>${escapeHtml(t("decision.aiSuggestionHumanConfirm", "I have manually reviewed and confirmed this AI suggestion"))}</strong><small>${escapeHtml(t("decision.aiSuggestionHumanConfirmHint", ""))}</small></span>
                </label>
              ` : ""}
              <label class="field-label span-2">${fieldLabelText(t("decision.notes", "Notes"), "optional", t("decision.notesHelp", ""))}
                <textarea class="field-textarea" data-field="notes" placeholder="${escapeHtml(t("decision.notesPlaceholder", ""))}">${escapeHtml(draft.notes || "")}</textarea>
              </label>
            </section>
          </form>
        </section>
      `;
    }

    function renderDecisionSummary(item, draft, status) {
      const diagnosticNames = Object.keys(item.diagnostic_summary || {});
      const exportSummary = exportStatusSummary();
      const selectedDecision = draft.decision ? decisionOptionEntry(draft.decision) : null;
      return `
        <section class="detail-section">
          <div class="summary-item decision-summary">
            <div class="decision-summary-head">
              <div>
                <h4>${escapeHtml(t("decision.summaryTitle", "Review decision summary"))}</h4>
                <p>${escapeHtml(t("decision.summarySubtitle", ""))}</p>
              </div>
              ${pill(status.ready ? t("caseBadges.exportReady", "export ready") : t("caseBadges.reviewPending", "review pending"), status.ready ? "ready" : "pending")}
            </div>
            <div class="decision-workflow">
              <strong>${escapeHtml(t("decision.workflowTitle", "Suggested review order"))}</strong>
              <ol>
                <li>${escapeHtml(t("decision.workflowEvidence", ""))}</li>
                <li>${escapeHtml(t("decision.workflowDecision", ""))}</li>
                <li>${escapeHtml(t("decision.workflowGovernance", ""))}</li>
              </ol>
            </div>
            <div class="context-grid">
              ${contextField(t("decision.caseTopic", "Case topic"), caseTopic(item), "span-2")}
              ${contextField(t("decision.mainDiagnostics", "Main diagnostics"), diagnosticNames.length ? diagnosticNames.map(readableLabel) : item.issue_types, "span-2")}
              ${contextField(t("decision.suggestedRootCauses", "Suggested root causes"), asArray(item.suggested_root_causes).map(readableLabel))}
              ${contextField(t("decision.suggestedActions", "Suggested follow-up actions"), asArray(item.suggested_follow_up_actions).map(readableLabel))}
              ${contextField(t("decision.decision", "Decision"), selectedDecision ? `${selectedDecision.label} / ${selectedDecision.code}` : t("decision.chooseOne", "Choose one conclusion"))}
              ${contextField(t("decision.exportStatus", "Export status"), exportSummary.label)}
            </div>
          </div>
        </section>
      `;
    }

    function decisionChoices(options, selected) {
      return options.map(value => {
        const entry = decisionOptionEntry(value);
        return `
          <label class="check-option">
            <input type="radio" name="review-decision" data-field="decision" value="${escapeHtml(value)}" ${selected === value ? "checked" : ""} />
            <span>
              <strong>${escapeHtml(entry.label)}</strong>
              <small>${escapeHtml(entry.description)}</small>
              <span class="decision-code">${escapeHtml(t("decision.originalCode", "Code"))}: ${escapeHtml(entry.code)}</span>
            </span>
          </label>
        `;
      }).join("");
    }

    function checkboxes(field, options, selected) {
      const chosen = new Set(asArray(selected));
      return options.map(value => {
        const entry = glossaryEntry(value) || { label: value, description: "", code: value };
        return `
        <label class="check-option">
          <input type="checkbox" data-field="${escapeHtml(field)}" value="${escapeHtml(value)}" ${chosen.has(value) ? "checked" : ""} />
          <span>
            <strong>${escapeHtml(entry.label)}</strong>
            ${entry.description ? `<small>${escapeHtml(entry.description)}</small>` : ""}
            <span class="decision-code">${escapeHtml(t("decision.originalCode", "Code"))}: ${escapeHtml(entry.code)}</span>
          </span>
        </label>
      `;
      }).join("");
    }

    function renderGuideDetail(item) {
      const steps = tArray("guide.steps", uiConfig.guide_steps || []);
      return `
        <section class="detail-section">
          <div class="summary-list">
            <article class="summary-item">
              <h4>${escapeHtml(t("guide.detailTitle", "Operation Guide"))}</h4>
              <ol class="guide-list">
                ${steps.map(step => `<li>${escapeHtml(step)}</li>`).join("")}
              </ol>
            </article>
            <article class="summary-item">
              <h4>${escapeHtml(t("guide.currentCaseTitle", "Current case"))}</h4>
              <p>${escapeHtml(t("guide.currentCasePrefix", "Reviewing: "))}${escapeHtml(item.case_id)}</p>
              <p>${escapeHtml(t("guide.exportReminder", ""))}</p>
            </article>
          </div>
        </section>
      `;
    }

    function bindDecisionInputs(item, draft) {
      const form = document.getElementById("decision-form");
      if (!form) return;
      form.addEventListener("input", event => updateDraftFromInput(item.case_id, event.target));
      form.addEventListener("change", event => updateDraftFromInput(item.case_id, event.target));
    }

    function updateDraftFromInput(caseId, target) {
      const field = target.getAttribute("data-field");
      if (!field) return;
      const draft = caseDraft(caseId);
      if (["confirmed_root_causes", "rejected_root_causes", "confirmed_follow_up_actions"].includes(field)) {
        const checked = Array.from(document.querySelectorAll(`[data-field="${field}"]:checked`)).map(input => input.value);
        draft[field] = checked;
      } else if (field === "fixture_candidate" || field === "human_confirmed_ai_suggestion") {
        draft[field] = target.checked;
      } else if (field === "proposed_change_targets") {
        draft[field] = target.value.split("|").map(value => value.trim()).filter(Boolean);
      } else {
        draft[field] = target.value;
      }
      touchDraft(caseId);
      window.localStorage.setItem(stateKey, JSON.stringify(drafts));
      renderQueues();
      renderSideStatus();
      renderBadges();
      const item = itemByCaseId(caseId);
      if (item && item.case_id === selectedCaseId) {
        renderDetailHeader(item, draft, draftStatus(draft));
      }
    }

    function buildFilledWorkbench() {
      const readyIds = new Set(readyDraftCaseIds());
      const clonedItems = items.filter(item => readyIds.has(item.case_id)).map(item => ({
        ...item,
        pilot_batch: undefined,
        pilot_review_assist: undefined,
        reviewer_input_template: humanDraftForExport(item.case_id),
      }));
      const exportedCaseIds = clonedItems.map(item => item.case_id);
      return {
        version: payload.version,
        scope: "filled visual manual review workbench export",
        exported_at: new Date().toISOString(),
        source_workbench_version: workbench.version,
        workbench_fingerprint: workbenchFingerprint,
        source_imported_case_ids: asArray(importState.imported_case_ids),
        advisory_packet_only: false,
        contains_completed_manual_decisions: clonedItems.length > 0,
        csv_fields: csvFields,
        guardrails,
        summary: {
          total_source_workbench_items: items.length,
          total_workbench_items: clonedItems.length,
          exported_draft_items: clonedItems.length,
          exported_case_ids: exportedCaseIds,
          local_draft_items: draftCaseIdsWithContent().length,
          ready_draft_items: readyIds.size,
          blocked_draft_items: blockedDraftCaseIds().length,
          pilot_checklist_marked_cases: Object.values(pilotChecklistState).filter(value => value && value.reviewed).length,
          export_policy: "ready_human_drafts_only",
        },
        workbench_items: clonedItems,
      };
    }

    function csvEscape(value) {
      const raw = Array.isArray(value) ? value.join(" | ") : String(value ?? "");
      const text = /^[=+\-@]/.test(raw.trim()) ? "'" + raw : raw;
      return /[",\n\r]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
    }

    function csvForWorkbench(data) {
      const rows = [csvFields.join(",")];
      data.workbench_items.forEach(item => {
        const template = item.reviewer_input_template || {};
        const counts = item.evidence_context_counts || {};
        const row = {
          case_id: item.case_id,
          case_topic: (item.case_context && item.case_context.case_topic) || "",
          question: (item.case_context && item.case_context.question) || "",
          priority_score: item.priority_score,
          risk_level: item.risk_level,
          expected_domains: asArray(item.expected_domains),
          queue_tags: asArray(item.queue_tags),
          issue_types: asArray(item.issue_types),
          suggested_root_causes: asArray(item.suggested_root_causes),
          suggested_follow_up_actions: asArray(item.suggested_follow_up_actions),
          review_question_count: asArray(item.suggested_review_questions).length,
          missing_final_expected_count: counts.missing_final_expected || 0,
          missing_scenario_core_count: counts.missing_scenario_core || 0,
          lost_evidence_count: counts.lost_evidence || 0,
          reviewer: template.reviewer || "",
          reviewed_at: template.reviewed_at || "",
          decision: template.decision || "",
          confirmed_root_causes: asArray(template.confirmed_root_causes),
          rejected_root_causes: asArray(template.rejected_root_causes),
          confirmed_follow_up_actions: asArray(template.confirmed_follow_up_actions),
          proposed_change_targets: asArray(template.proposed_change_targets),
          fixture_candidate: template.fixture_candidate ? "true" : "false",
          rationale: template.rationale || "",
          notes: template.notes || "",
        };
        rows.push(csvFields.map(field => csvEscape(row[field])).join(","));
      });
      return rows.join("\n");
    }

    function download(filename, mime, text) {
      const blob = new Blob([text], { type: mime });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    }

    function confirmExport(kind, data) {
      const readyIds = data.summary.exported_case_ids || [];
      if (!readyIds.length) {
        window.alert(t("exportPreview.none", "No drafts are ready to export. Fill required fields first."));
        return false;
      }
      const blocked = data.summary.blocked_draft_items || 0;
      const previewLines = [
        formatMessage(t("exportPreview.ready", "This export will include {ready} ready drafts: {cases}"), {
          ready: readyIds.length,
          cases: readyIds.join(", "),
        }),
      ];
      if (blocked) {
        previewLines.push(formatMessage(t("exportPreview.blocked", "{blocked} incomplete drafts will not be exported."), { blocked }));
      }
      previewLines.push(t(kind === "csv" ? "exportPreview.confirmCsv" : "exportPreview.confirmJson", "Export these drafts?"));
      return window.confirm(previewLines.join("\n"));
    }

    function exportJson() {
      const data = buildFilledWorkbench();
      if (!confirmExport("json", data)) return;
      download("filled_manual_review_workbench.json", "application/json;charset=utf-8", JSON.stringify(data, null, 2));
      markExported();
    }

    function exportCsv() {
      const data = buildFilledWorkbench();
      if (!confirmExport("csv", data)) return;
      download("filled_manual_review_workbench.csv", "text/csv;charset=utf-8", "\ufeff" + csvForWorkbench(data));
      markExported();
    }

    function markExported() {
      const readyIds = readyDraftCaseIds();
      exportState = {
        last_exported_at: new Date().toISOString(),
        local_draft_items: draftCaseIdsWithContent().length,
        ready_draft_items: readyIds.length,
        blocked_draft_items: blockedDraftCaseIds().length,
        exported_draft_items: readyIds.length,
        exported_case_ids: readyIds,
      };
      persistExportState();
      renderSideStatus();
      renderBadges();
      renderDetail();
    }

    function saveCaseDraft(caseId) {
      const draft = caseDraft(caseId);
      const now = new Date().toISOString();
      if (!draft.updated_at) draft.updated_at = now;
      draft.saved_at = now;
      drafts[caseId] = draft;
      window.localStorage.setItem(stateKey, JSON.stringify(drafts));
      renderQueues();
      renderSideStatus();
      renderBadges();
      const item = itemByCaseId(caseId);
      if (item && item.case_id === selectedCaseId) {
        renderDetailHeader(item, draft, draftStatus(draft));
      }
    }

    function applyAiSuggestion(caseId) {
      const suggestion = aiSuggestionFor(caseId);
      if (!suggestion) return;
      const draft = caseDraft(caseId);
      aiSuggestionFields.forEach(field => {
        if (Object.prototype.hasOwnProperty.call(suggestion, field)) {
          draft[field] = Array.isArray(suggestion[field]) ? [...suggestion[field]] : suggestion[field];
        }
      });
      draft.notes = [draft.notes, t("decision.aiSuggestionCopied", "AI suggestion copied. Please manually confirm reviewer, date, decision, and rationale.")]
        .filter(Boolean)
        .join("\n");
      draft.ai_suggestion_applied_at = new Date().toISOString();
      draft.human_confirmed_ai_suggestion = false;
      touchDraft(caseId);
      window.localStorage.setItem(stateKey, JSON.stringify(drafts));
      render();
    }

    function clearAiSuggestion(caseId) {
      delete aiSuggestions[caseId];
      persistAiSuggestions();
      render();
    }

    function draftTemplateFromImportRow(row) {
      const source = row && row.reviewer_input_template && typeof row.reviewer_input_template === "object"
        ? row.reviewer_input_template
        : row || {};
      const draft = {};
      reviewerDraftFields.forEach(field => {
        if (!Object.prototype.hasOwnProperty.call(source, field)) return;
        if (["confirmed_root_causes", "rejected_root_causes", "confirmed_follow_up_actions", "proposed_change_targets"].includes(field)) {
          draft[field] = asArray(source[field]).flatMap(value => String(value).split("|")).map(value => value.trim()).filter(Boolean);
        } else if (field === "fixture_candidate") {
          draft[field] = source[field] === true || String(source[field]).toLowerCase() === "true" || String(source[field]) === "1";
        } else {
          draft[field] = source[field] ?? "";
        }
      });
      if (row && row.updated_at && !draft.updated_at) draft.updated_at = row.updated_at;
      return draft;
    }

    function suggestionSourceFromImportRow(row) {
      if (row && row.ai_review_suggestion && typeof row.ai_review_suggestion === "object") {
        return row.ai_review_suggestion;
      }
      if (row && row.reviewer_input_template && typeof row.reviewer_input_template === "object") {
        return row.reviewer_input_template;
      }
      return row || {};
    }

    function looksLikeAiAssistedSource(source, container = {}) {
      const markerText = [
        container.scope,
        container.version,
        source.prefill_scope,
        source.reviewer,
        source.notes,
        source.rationale,
      ].map(value => String(value || "")).join(" ").toLowerCase();
      return Boolean(
        Boolean(source && source.human_confirmation_required === true) ||
        Boolean(source && source.ai_suggestion === true) ||
        Boolean(source && source.suggestion_type === "ai_assisted_manual_review_prefill") ||
        container.human_confirmation_required === true ||
        (container.guardrails && container.guardrails.human_confirmation_required === true) ||
        (container.guardrails && container.guardrails.advisory_draft_only === true) ||
        markerText.includes("codex") ||
        markerText.includes("ai-assisted") ||
        markerText.includes("ai assisted") ||
        markerText.includes("ai辅助") ||
        markerText.includes("辅助预填") ||
        markerText.includes("待人工确认")
      );
    }

    function aiSuggestionFromImportRow(row, container = {}) {
      const source = suggestionSourceFromImportRow(row);
      const suggestion = {};
      aiSuggestionFields.forEach(field => {
        if (!Object.prototype.hasOwnProperty.call(source, field)) return;
        if (["confirmed_root_causes", "rejected_root_causes", "confirmed_follow_up_actions", "proposed_change_targets"].includes(field)) {
          suggestion[field] = asArray(source[field]).flatMap(value => String(value).split("|")).map(value => value.trim()).filter(Boolean);
        } else if (field === "fixture_candidate") {
          suggestion[field] = source[field] === true || String(source[field]).toLowerCase() === "true" || String(source[field]) === "1";
        } else {
          suggestion[field] = source[field] ?? "";
        }
      });
      suggestion.source = "ai_prefill_import";
      suggestion.human_confirmation_required = true;
      suggestion.imported_at = new Date().toISOString();
      if (container.version) suggestion.source_version = container.version;
      return suggestion;
    }

    function isFilledWorkbenchExport(container) {
      const summary = container && typeof container.summary === "object" ? container.summary : {};
      return Boolean(
        container && typeof container === "object" &&
        container.scope === "filled visual manual review workbench export" &&
        summary.export_policy === "ready_human_drafts_only" &&
        container.workbench_fingerprint === workbenchFingerprint &&
        Array.isArray(container.workbench_items) &&
        Array.isArray(summary.exported_case_ids) &&
        summary.exported_case_ids.length === container.workbench_items.length &&
        summary.exported_case_ids.every(caseId => container.workbench_items.some(item => item && item.case_id === caseId)) &&
        container.advisory_packet_only !== true &&
        container.contains_completed_manual_decisions !== false
      );
    }

    function isSafeAiSuggestionImport(container) {
      const guardrails = container && typeof container.guardrails === "object" ? container.guardrails : {};
      return Boolean(
        container && typeof container === "object" &&
        container.scope === "safe visual workbench AI suggestion import" &&
        container.human_confirmation_required === true &&
        container.reviewer_input_template_written === false &&
        (guardrails.advisory_draft_only === true || guardrails.reviewer_decision_import === "disallowed_without_human_copy") &&
        Array.isArray(container.workbench_items)
      );
    }

    function assertNoDraftRowsInSuggestionImport(rows) {
      if (rows.some(row => row && row.reviewer_input_template && typeof row.reviewer_input_template === "object")) {
        throw new Error(t("reviewImport.invalidJson", "The JSON is invalid or is not a filled manual review workbench."));
      }
    }

    function parseReviewJson(text) {
      let parsed;
      try {
        parsed = JSON.parse(text);
      } catch {
        throw new Error(t("reviewImport.invalidJson", "The JSON is invalid or is not a filled manual review workbench."));
      }
      if (!isFilledWorkbenchExport(parsed) && !isSafeAiSuggestionImport(parsed)) {
        throw new Error(t("reviewImport.invalidJson", "The JSON is invalid or is not a filled manual review workbench."));
      }
      const rows = Array.isArray(parsed.workbench_items) ? parsed.workbench_items : [];
      if (!rows.length) {
        throw new Error(t("reviewImport.noRows", "The file has no review rows to import."));
      }
      if (isSafeAiSuggestionImport(parsed)) {
        assertNoDraftRowsInSuggestionImport(rows);
      }
      return rows.map(row => {
        const isAiSuggestion = isSafeAiSuggestionImport(parsed) || looksLikeAiAssistedSource(suggestionSourceFromImportRow(row), parsed || {});
        return {
          case_id: row && row.case_id,
          draft: isAiSuggestion ? {} : draftTemplateFromImportRow(row),
          ai_suggestion: isAiSuggestion ? aiSuggestionFromImportRow(row, parsed || {}) : null,
          import_kind: isAiSuggestion ? "ai_suggestion" : "filled_workbench_export",
        };
      });
    }

    function parseCsvRows(text) {
      const input = String(text || "").replace(/^\ufeff/, "");
      const rows = [];
      let row = [];
      let cell = "";
      let inQuotes = false;
      for (let index = 0; index < input.length; index += 1) {
        const char = input[index];
        const next = input[index + 1];
        if (char === '"' && inQuotes && next === '"') {
          cell += '"';
          index += 1;
        } else if (char === '"') {
          inQuotes = !inQuotes;
        } else if (char === "," && !inQuotes) {
          row.push(cell);
          cell = "";
        } else if ((char === "\n" || char === "\r") && !inQuotes) {
          if (char === "\r" && next === "\n") index += 1;
          row.push(cell);
          if (row.some(value => value !== "")) rows.push(row);
          row = [];
          cell = "";
        } else {
          cell += char;
        }
      }
      row.push(cell);
      if (row.some(value => value !== "")) rows.push(row);
      return rows;
    }

    function parseReviewCsv(text) {
      const rows = parseCsvRows(text);
      if (rows.length < 2) {
        throw new Error(t("reviewImport.noRows", "The file has no review rows to import."));
      }
      const headers = rows[0].map(header => String(header || "").trim());
      const caseIndex = headers.indexOf("case_id");
      if (caseIndex < 0) {
        throw new Error(t("reviewImport.invalidCsv", "The CSV is invalid or missing case_id."));
      }
      return rows.slice(1).map(values => {
        const record = {};
        headers.forEach((header, index) => {
          record[header] = values[index] ?? "";
        });
        return {
          case_id: record.case_id,
          draft: draftTemplateFromImportRow(record),
          ai_suggestion: looksLikeAiAssistedSource(record, {}) ? aiSuggestionFromImportRow(record, {}) : null,
        };
      });
    }

    function parseReviewImport(text, fileName = "") {
      const lowerName = String(fileName || "").toLowerCase();
      if (lowerName.endsWith(".json") || text.trim().startsWith("{") || text.trim().startsWith("[")) return parseReviewJson(text);
      throw new Error(t("reviewImport.unsupportedFile", "Please import a .json file."));
    }

    // CSV import is intentionally unsupported. CSV remains a view-only export for spreadsheet review.

    function applyReviewImport(records) {
      const knownCases = new Set(items.map(item => item.case_id));
      const duplicateSeen = new Set();
      const draftRecords = records.filter(record => {
        const caseId = record && record.case_id ? String(record.case_id).trim() : "";
        if (!caseId || !knownCases.has(caseId) || (record && record.ai_suggestion)) return false;
        return hasDraftContent(draftTemplateFromImportRow(record && record.draft ? record.draft : {}));
      });
      const summary = {
        total_rows: records.length,
        imported_rows: 0,
        suggestion_rows: 0,
        unknown_rows: 0,
        skipped_rows: 0,
        duplicate_rows: 0,
        cleared_draft_rows: draftRecords.length ? draftCaseIdsWithContent().length : 0,
        imported_case_ids: [],
        suggestion_case_ids: [],
        unknown_case_ids: [],
        duplicate_case_ids: [],
      };
      if (draftRecords.length) {
        drafts = {};
      }
      records.forEach(record => {
        const caseId = record && record.case_id ? String(record.case_id).trim() : "";
        const draft = draftTemplateFromImportRow(record && record.draft ? record.draft : {});
        const suggestion = record && record.ai_suggestion ? record.ai_suggestion : null;
        if (!caseId) {
          summary.skipped_rows += 1;
          return;
        }
        if (!knownCases.has(caseId)) {
          summary.unknown_rows += 1;
          summary.unknown_case_ids.push(caseId);
          return;
        }
        if (duplicateSeen.has(caseId)) {
          summary.duplicate_rows += 1;
          summary.duplicate_case_ids.push(caseId);
          return;
        }
        duplicateSeen.add(caseId);
        if (suggestion) {
          aiSuggestions[caseId] = suggestion;
          summary.suggestion_rows += 1;
          summary.suggestion_case_ids.push(caseId);
          return;
        }
        if (!hasDraftContent(draft)) {
          summary.skipped_rows += 1;
          return;
        }
        drafts[caseId] = {
          ...draft,
          imported_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
        summary.imported_rows += 1;
        summary.imported_case_ids.push(caseId);
      });
      return summary;
    }

    function updateImportState(summary, error = "") {
      importState = {
        last_imported_at: new Date().toISOString(),
        total_rows: summary.total_rows || 0,
        imported_rows: summary.imported_rows || 0,
        suggestion_rows: summary.suggestion_rows || 0,
        unknown_rows: summary.unknown_rows || 0,
        skipped_rows: summary.skipped_rows || 0,
        duplicate_rows: summary.duplicate_rows || 0,
        cleared_draft_rows: summary.cleared_draft_rows || 0,
        imported_case_ids: asArray(summary.imported_case_ids),
        suggestion_case_ids: asArray(summary.suggestion_case_ids),
        unknown_case_ids: asArray(summary.unknown_case_ids),
        duplicate_case_ids: asArray(summary.duplicate_case_ids),
        error,
      };
      persistImportState();
    }

    function importReviewFile(file) {
      if (!file) return;
      if (!/\.json$/i.test(file.name || "")) {
        updateImportState({ total_rows: 0 }, t("reviewImport.unsupportedFile", "Please import a .json file."));
        renderImportSummary();
        renderSideStatus();
        return;
      }
      const reader = new FileReader();
      reader.onload = () => {
        try {
          const records = parseReviewImport(String(reader.result || ""), file.name || "");
          const summary = applyReviewImport(records);
          updateImportState(summary);
          window.localStorage.setItem(stateKey, JSON.stringify(drafts));
          persistAiSuggestions();
          render();
        } catch (error) {
          updateImportState({ total_rows: 0 }, error && error.message ? error.message : String(error));
          renderImportSummary();
          renderSideStatus();
        }
      };
      reader.onerror = () => {
        updateImportState({ total_rows: 0 }, reader.error && reader.error.message ? reader.error.message : t("reviewImport.unsupportedFile", "Please import a .json file."));
        renderImportSummary();
        renderSideStatus();
      };
      reader.readAsText(file, "utf-8");
    }

    document.addEventListener("click", event => {
      const filterButton = event.target.closest("[data-filter]");
      if (filterButton) {
        currentFilter = filterButton.getAttribute("data-filter");
        render();
        return;
      }
      const caseButton = event.target.closest("[data-case-id]");
      if (caseButton) {
        selectedCaseId = caseButton.getAttribute("data-case-id");
        activeTab = "overview";
        render();
        return;
      }
      const tabButton = event.target.closest("[data-tab]");
      if (tabButton) {
        activeTab = tabButton.getAttribute("data-tab");
        renderDetail();
        return;
      }
      const actionButton = event.target.closest("[data-action]");
      if (actionButton) {
        const action = actionButton.getAttribute("data-action");
        if (action === "export-json") exportJson();
        if (action === "export-csv") exportCsv();
        if (action === "save-case-draft") saveCaseDraft(selectedCaseId);
        if (action === "apply-ai-suggestion") applyAiSuggestion(selectedCaseId);
        if (action === "clear-ai-suggestion") clearAiSuggestion(selectedCaseId);
        if (action === "toggle-pilot-checklist") {
          pilotChecklistState[selectedCaseId] = {
            reviewed: Boolean(actionButton.checked),
            reviewed_at: new Date().toISOString(),
          };
          persistPilotChecklistState();
          renderDetail();
        }
        if (action === "import-review-file") {
          const input = document.getElementById("review-import-file");
          if (input) input.click();
        }
        if (action === "clear-case-draft") {
          delete drafts[selectedCaseId];
          persistDrafts();
        }
      }
      const jumpButton = event.target.closest("[data-jump-tab]");
      if (jumpButton) {
        activeTab = jumpButton.getAttribute("data-jump-tab");
        renderDetail();
      }
    });

    document.getElementById("search-input").addEventListener("input", event => {
      query = event.target.value || "";
      renderCaseList();
      renderDetail();
    });

    document.getElementById("language-select").addEventListener("change", event => {
      currentLanguage = event.target.value || (uiConfig.default_language || "zh-CN");
      try {
        window.localStorage.setItem(languageKey, currentLanguage);
      } catch {}
      render();
    });

    document.getElementById("review-import-file").addEventListener("change", event => {
      const file = event.target.files && event.target.files[0];
      importReviewFile(file);
      event.target.value = "";
    });

    render();
  </script>
</body>
</html>
"""


def build_report(payload: dict[str, Any], output_path: Path) -> dict[str, Any]:
    summary = payload.get("summary") or {}
    embedded_payload_text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return {
        "version": VERSION,
        "scope": "manual review visual workbench static build",
        "outputs": {
            "html": str(output_path),
        },
        "summary": {
            "html_generated": output_path.exists(),
            "workbench_items": summary.get("workbench_items", 0),
            "pending_items": summary.get("pending_items", 0),
            "high_priority_items": summary.get("high_priority_items", 0),
            "gate_status": summary.get("gate_status", "unknown"),
            "ready_for_static_review": summary.get("ready_for_static_review", False),
            "original_llm_output_cases": summary.get(
                "original_llm_output_cases",
                len(payload.get("original_llm_outputs") or {}),
            ),
            "supports_case_list": True,
            "supports_case_detail": True,
            "supports_reviewer_form": True,
            "supports_json_export": True,
            "supports_csv_export": True,
            "supports_pipeline_status": True,
            "supports_independent_panel_scrolling": True,
            "keeps_detail_panel_synced_with_app_shell": True,
            "uses_fixed_height_app_shell": True,
            "keeps_sidebar_scroll_independent": True,
            "restores_natural_mobile_flow": True,
            "supports_operation_guide": True,
            "supports_language_switch": True,
            "supports_case_label_glossary": True,
            "supports_case_context": True,
            "supports_decision_tab_readability": True,
            "supports_question_i18n": True,
            "supports_original_llm_output_panel": True,
            "supports_compact_language_control": True,
            "supports_export_state_tracking": True,
            "supports_review_export_import": True,
            "supports_field_requirement_labels": True,
            "supports_manual_draft_save": True,
            "supports_ai_suggestion_isolation": True,
            "supports_pilot_batch_queue": True,
            "supports_per_case_human_judgment_checklist": True,
            "supports_pilot_batch_advisory_panel": True,
            "supports_pilot_review_assist_panel": True,
            "supports_manual_authority_notice": True,
            "uses_concise_export_button_labels": True,
            "shows_open_gate_as_no_blockers": True,
            "hides_blocked_gate_queue_when_open": True,
            "moves_pipeline_status_to_global_sidebar": True,
            "removes_pipeline_from_case_tabs": True,
            "embedded_payload_question_pollution_free": "???" not in embedded_payload_text,
            "supports_scoped_local_drafts": True,
            "imports_replace_stale_local_drafts": True,
            "supports_json_import_contract": True,
            "supports_export_case_preview": True,
            "exports_exported_case_ids": True,
            "validates_frontend_allowed_values": True,
            "escapes_csv_formula_cells": True,
            "requires_human_confirmation_for_copied_ai_suggestion": True,
            "exports_ready_human_drafts_only": True,
            "pilot_batch_cases": summary.get("pilot_batch_cases", 0),
            "pilot_batch_advisory_only": summary.get("pilot_batch_advisory_only", False),
            "pilot_batch_completed_decisions": summary.get("pilot_batch_completed_decisions", 0),
            "pilot_review_assist_cases": summary.get("pilot_review_assist_cases", 0),
            "pilot_review_assist_advisory_only": summary.get("pilot_review_assist_advisory_only", False),
            "pilot_review_assist_completed_decisions": summary.get("pilot_review_assist_completed_decisions", 0),
            "items_with_case_context": (payload.get("workbench", {}).get("summary") or {}).get("items_with_case_context", 0),
            "default_language": UI_CONFIG["default_language"],
            "supported_languages": [language["code"] for language in UI_CONFIG["supported_languages"]],
        },
        "guardrails": GUARDRAILS,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build standalone visual manual-review workbench HTML.")
    parser.add_argument("--contract-report", type=Path, default=DEFAULT_CONTRACT_REPORT_PATH)
    parser.add_argument("--workbench", type=Path, default=DEFAULT_WORKBENCH_PATH)
    parser.add_argument("--intake-contract", type=Path, default=DEFAULT_INTAKE_CONTRACT_PATH)
    parser.add_argument("--progress-report", type=Path, default=DEFAULT_PROGRESS_REPORT_PATH)
    parser.add_argument("--governance-report", type=Path, default=DEFAULT_GOVERNANCE_REPORT_PATH)
    parser.add_argument("--import-report", type=Path, default=DEFAULT_IMPORT_REPORT_PATH)
    parser.add_argument("--diff-report", type=Path, default=DEFAULT_DIFF_REPORT_PATH)
    parser.add_argument("--validation-report", type=Path, default=DEFAULT_VALIDATION_REPORT_PATH)
    parser.add_argument("--promotion-report", type=Path, default=DEFAULT_PROMOTION_REPORT_PATH)
    parser.add_argument("--closeout-report", type=Path, default=DEFAULT_CLOSEOUT_REPORT_PATH)
    parser.add_argument("--pilot-batch-report", type=Path, default=DEFAULT_PILOT_BATCH_REPORT_PATH)
    parser.add_argument("--pilot-review-assist-report", type=Path, default=DEFAULT_PILOT_REVIEW_ASSIST_REPORT_PATH)
    parser.add_argument("--rag-eval-report", type=Path, default=DEFAULT_RAG_EVAL_REPORT_PATH)
    parser.add_argument("--rag-eval-cases", type=Path, default=DEFAULT_RAG_EVAL_CASES_PATH)
    parser.add_argument("--scenario-registry", type=Path, default=DEFAULT_SCENARIO_REGISTRY_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_payload(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html_document(payload), encoding="utf-8")
    report = build_report(payload, args.output)
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = report["summary"]
    print(
        "Manual review visual workbench built: "
        f"{summary['workbench_items']} cases, "
        f"gate={summary['gate_status']}, "
        f"html={args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
