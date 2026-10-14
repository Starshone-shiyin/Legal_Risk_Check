import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tools.build_manual_review_visual_workbench import (
    DEFAULT_CLOSEOUT_REPORT_PATH,
    DEFAULT_CONTRACT_REPORT_PATH,
    DEFAULT_DIFF_REPORT_PATH,
    DEFAULT_GOVERNANCE_REPORT_PATH,
    DEFAULT_IMPORT_REPORT_PATH,
    DEFAULT_INTAKE_CONTRACT_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_PILOT_BATCH_REPORT_PATH,
    DEFAULT_PILOT_REVIEW_ASSIST_REPORT_PATH,
    DEFAULT_PROGRESS_REPORT_PATH,
    DEFAULT_PROMOTION_REPORT_PATH,
    DEFAULT_RAG_EVAL_CASES_PATH,
    DEFAULT_RAG_EVAL_REPORT_PATH,
    DEFAULT_REPORT_OUTPUT_PATH,
    DEFAULT_SCENARIO_REGISTRY_PATH,
    DEFAULT_VALIDATION_REPORT_PATH,
    DEFAULT_WORKBENCH_PATH,
    GUARDRAILS,
    build_payload,
    build_report,
    enrich_workbench_with_case_context,
    extract_original_llm_outputs,
    has_case_context_signal,
    html_document,
)
from tools._shared.layout import legacy_report_path


def write_json(path: Path, data: dict):
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def contains_key(value, target: str) -> bool:
    if isinstance(value, dict):
        return target in value or any(contains_key(item, target) for item in value.values())
    if isinstance(value, list):
        return any(contains_key(item, target) for item in value)
    return False


def args_for(tmp: Path):
    return SimpleNamespace(
        contract_report=tmp / "contract_report.json",
        workbench=tmp / "workbench.json",
        intake_contract=tmp / "intake_contract.json",
        progress_report=tmp / "progress.json",
        governance_report=tmp / "governance.json",
        import_report=tmp / "import.json",
        diff_report=tmp / "diff.json",
        validation_report=tmp / "validation.json",
        promotion_report=tmp / "promotion.json",
        closeout_report=tmp / "closeout.json",
        pilot_batch_report=tmp / "pilot_batch.json",
        pilot_review_assist_report=tmp / "pilot_review_assist.json",
        rag_eval_report=tmp / "rag_eval_report.json",
        rag_eval_cases=tmp / "rag_eval_cases.json",
        scenario_registry=tmp / "scenario_registry.json",
    )


class ManualReviewVisualWorkbenchTest(unittest.TestCase):
    def test_default_paths_keep_legacy_reports_without_migrating_other_inputs(self):
        self.assertEqual(
            DEFAULT_CONTRACT_REPORT_PATH,
            legacy_report_path("manual_review_visual_workbench_contract_report.json"),
        )
        self.assertEqual(DEFAULT_INTAKE_CONTRACT_PATH, legacy_report_path("manual_review_intake_contract_report.json"))
        self.assertEqual(DEFAULT_PROGRESS_REPORT_PATH, legacy_report_path("evidence_manual_review_progress_report.json"))
        self.assertEqual(DEFAULT_GOVERNANCE_REPORT_PATH, legacy_report_path("evidence_manual_review_governance_report.json"))
        self.assertEqual(DEFAULT_IMPORT_REPORT_PATH, legacy_report_path("manual_review_workbench_import_report.json"))
        self.assertEqual(DEFAULT_DIFF_REPORT_PATH, legacy_report_path("manual_review_decision_diff_report.json"))
        self.assertEqual(
            DEFAULT_VALIDATION_REPORT_PATH,
            legacy_report_path("proposed_manual_review_decision_validation_report.json"),
        )
        self.assertEqual(
            DEFAULT_PROMOTION_REPORT_PATH,
            legacy_report_path("validated_decision_promotion_dry_run_report.json"),
        )
        self.assertEqual(DEFAULT_CLOSEOUT_REPORT_PATH, legacy_report_path("manual_review_intake_gate_closeout_report.json"))
        self.assertEqual(DEFAULT_PILOT_BATCH_REPORT_PATH, legacy_report_path("manual_review_pilot_batch_report.json"))
        self.assertEqual(
            DEFAULT_PILOT_REVIEW_ASSIST_REPORT_PATH,
            legacy_report_path("manual_review_pilot_case_review_assist_report.json"),
        )
        self.assertEqual(DEFAULT_REPORT_OUTPUT_PATH, legacy_report_path("manual_review_visual_workbench_build_report.json"))
        self.assertEqual(DEFAULT_WORKBENCH_PATH, Path("tests/evidence_manual_review_workbench.json"))
        self.assertEqual(DEFAULT_RAG_EVAL_REPORT_PATH, Path("tests/rag_eval_report.json"))
        self.assertEqual(DEFAULT_RAG_EVAL_CASES_PATH, Path("tests/rag_eval_cases.json"))
        self.assertEqual(DEFAULT_SCENARIO_REGISTRY_PATH, Path("config/scenario_registry.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, Path("tools/manual_review_visual_workbench/index.html"))

    def test_payload_embeds_saved_reports_and_guardrails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            args = args_for(tmp)
            write_json(args.contract_report, {"version": "0.4.7.8.0", "field_contract": {}})
            write_json(
                args.workbench,
                {
                    "version": "0.4.7.6.0",
                    "summary": {"total_workbench_items": 1, "pending_items": 1, "high_priority_items": 1},
                    "workbench_items": [{"case_id": "case_a", "decision_status": "pending"}],
                    "csv_fields": ["case_id", "reviewer"],
                },
            )
            write_json(args.intake_contract, {"version": "0.4.7.7.0", "contract": {}})
            write_json(args.progress_report, {"summary": {"completed_cases": 0, "pending_cases": 1}})
            write_json(args.governance_report, {"summary": {"blocked_action_candidates": 1}})
            write_json(args.import_report, {"summary": {"imported_rows": 0, "rejected_rows": 1}})
            write_json(args.diff_report, {"summary": {"changed_cases": 0}})
            write_json(args.validation_report, {"summary": {"valid_records": 0, "pending_records": 1}})
            write_json(args.promotion_report, {"summary": {"promotion_candidates": 0, "ready_action_candidates": 0}})
            write_json(args.closeout_report, {"summary": {"gate_status": "blocked", "blockers": ["no_imported_review_rows"]}})
            write_json(
                args.pilot_batch_report,
                {
                    "version": "0.4.7.8.15",
                    "schema_kind": "advisory_pilot_packet",
                    "contains_completed_manual_decisions": False,
                    "advisory_packet_only": True,
                    "summary": {
                        "pilot_case_count": 1,
                        "human_confirmation_required_cases": 1,
                        "advisory_ai_suggestion_cases": 1,
                        "completed_manual_decisions": 0,
                        "promotion_candidates": 0,
                        "ready_action_candidates": 0,
                    },
                    "pilot_cases": [
                        {
                            "case_id": "case_a",
                            "rank": 1,
                            "selection_score": 99,
                            "why_selected": ["high-risk grounding issue"],
                            "evidence_issue_summary": {"plain_summary": ["final evidence may miss primary support"]},
                            "evidence_to_check": {
                                "final_evidence": [{"citation": "Article 1", "functional_type": "operative_rule"}],
                                "missing_final_expected": [{"citation": "Article 2", "functional_type": "liability_rule"}],
                            },
                            "prescreen_advice": {
                                "prescreen_suggested_advisory_decision": "confirm_diagnostic_issue",
                                "plain_language_guidance": "Check the final evidence chain first.",
                                "not_a_reviewer_decision": True,
                            },
                            "ai_suggestion": {
                                "advisory_only": True,
                                "human_confirmation_required": True,
                                "advisory_decision": "confirm_diagnostic_issue",
                                "advisory_root_causes": ["primary_evidence_gap"],
                                "advisory_follow_up_actions": ["needs_additional_evidence_capture"],
                                "not_a_reviewer_decision": True,
                            },
                            "reviewer_decision_needed": {
                                "human_confirmation_required": True,
                                "allowed_options": [
                                    {
                                        "option_code": "agree_confirm_diagnostic_issue",
                                        "plain_label": "同意诊断成立",
                                        "meaning": "The reviewer still decides manually.",
                                    }
                                ],
                                "minimum_fields_for_later_workbench": ["reviewer", "reviewed_at", "decision", "rationale"],
                                "optional_or_conditional_fields": ["confirmed_root_causes"],
                                "plain_instruction": "Read the case, then decide manually.",
                            },
                            "reviewer_input_template": {"decision": "must_not_copy"},
                        }
                    ],
                },
            )
            write_json(
                args.pilot_review_assist_report,
                {
                    "version": "0.4.7.8.17",
                    "schema_kind": "advisory_pilot_case_review_assist",
                    "contains_completed_manual_decisions": False,
                    "advisory_packet_only": True,
                    "summary": {
                        "assisted_cases": 1,
                        "needs_user_confirmation_cases": 1,
                        "high_attention_manual_review_cases": 1,
                        "completed_manual_decisions": 0,
                        "promotion_candidates": 0,
                        "ready_action_candidates": 0,
                    },
                    "assisted_cases": [
                        {
                            "case_id": "case_a",
                            "rank": 1,
                            "plain_case_brief": "Customer data leak review.",
                            "evidence_support_assessment": {
                                "support_status": "likely_evidence_support_gap_needs_user_confirmation",
                                "support_status_label": "Likely evidence support gap; user confirmation required",
                                "plain_assessment": "Final evidence may not support the main issue.",
                                "detected_assist_signals": [
                                    {
                                        "code": "primary_issue_missing_evidence",
                                        "label": "Main issue lacks evidence",
                                        "reason": "Expected liability evidence is missing.",
                                    }
                                ],
                                "missing_expected_evidence_examples": [{"citation": "Article 2"}],
                            },
                            "advisory_review_assist": {
                                "advisory_tendency": "likely_review_issue_confirmable_but_user_must_decide",
                                "advisory_tendency_label": "Likely confirmable, but the user must decide",
                                "focus_questions_for_user": ["Does Article 2 support notification duties?"],
                                "advisory_rationale": ["This is only a reading aid."],
                                "user_confirmation_required": True,
                                "not_a_reviewer_decision": True,
                            },
                            "original_llm_claims": {
                                "risk_types": ["data leak"],
                                "recommended_actions": ["notify regulator"],
                            },
                            "reviewer_input_template": {"decision": "must_not_copy"},
                            "reviewer_decision": {"decision": "must_not_copy"},
                            "workbench_items": [{"case_id": "must_not_copy"}],
                            "decision_status": "must_not_copy",
                        }
                    ],
                },
            )
            write_json(
                args.rag_eval_report,
                {
                    "reports": [
                        {
                            "id": "case_a",
                            "question": "公司应如何处理客户数据泄露？",
                            "answer": "公司应立即采取补救措施并通知监管部门和个人。",
                            "answer_confidence": 0.91,
                        }
                    ]
                },
            )
            write_json(
                args.rag_eval_cases,
                {
                    "cases": [
                        {
                            "id": "case_a",
                            "question": "公司应如何处理客户数据泄露？",
                            "expected_risk_types": ["数据泄露"],
                            "expected_actions": ["通知监管部门"],
                        }
                    ]
                },
            )
            write_json(
                args.scenario_registry,
                {
                    "scenarios": [
                        {
                            "scenario_id": "customer_data_leak",
                            "domain": "数据合规",
                            "description": "客户数据泄露后，需要判断企业通知、补救和赔偿责任。",
                            "eval_case_ids": ["case_a"],
                        }
                    ]
                },
            )

            payload = build_payload(args)

        self.assertEqual(payload["version"], "0.4.7.8.23")
        self.assertEqual(payload["summary"]["workbench_items"], 1)
        self.assertEqual(payload["summary"]["pilot_batch_cases"], 1)
        self.assertTrue(payload["summary"]["pilot_batch_advisory_only"])
        self.assertEqual(payload["summary"]["pilot_batch_completed_decisions"], 0)
        self.assertEqual(payload["summary"]["pilot_review_assist_cases"], 1)
        self.assertTrue(payload["summary"]["pilot_review_assist_advisory_only"])
        self.assertEqual(payload["summary"]["pilot_review_assist_completed_decisions"], 0)
        self.assertTrue(payload["summary"]["ready_for_static_review"])
        self.assertEqual(payload["guardrails"]["rag_query_integration"], "disallowed")
        self.assertEqual(payload["workbench"]["workbench_items"][0]["case_id"], "case_a")
        self.assertEqual(payload["pilot_batch_report"]["schema_kind"], "advisory_pilot_packet")
        self.assertTrue(payload["pilot_batch_report"]["advisory_packet_only"])
        self.assertFalse(payload["pilot_batch_report"]["contains_completed_manual_decisions"])
        self.assertEqual(payload["pilot_batch"]["matched_workbench_cases"], 1)
        pilot = payload["workbench"]["workbench_items"][0]["pilot_batch"]
        self.assertTrue(pilot["advisory_only"])
        self.assertTrue(pilot["not_a_reviewer_decision"])
        self.assertNotIn("reviewer_input_template", pilot)
        self.assertEqual(pilot["ai_suggestion"]["advisory_decision"], "confirm_diagnostic_issue")
        assist = payload["workbench"]["workbench_items"][0]["pilot_review_assist"]
        self.assertTrue(assist["advisory_only"])
        self.assertTrue(assist["not_a_reviewer_decision"])
        self.assertTrue(assist["user_confirmation_required"])
        self.assertEqual(assist["advisory_tendency_label"], "Likely confirmable, but the user must decide")
        self.assertEqual(assist["support_status_label"], "Likely evidence support gap; user confirmation required")
        self.assertEqual(assist["risk_types"], ["data leak"])
        self.assertEqual(assist["recommended_actions"], ["notify regulator"])
        self.assertNotIn("reviewer_input_template", assist)
        self.assertNotIn("reviewer_decision", assist)
        self.assertNotIn("workbench_items", assist)
        self.assertNotIn("decision_status", assist)
        self.assertEqual(payload["pilot_review_assist_report"]["schema_kind"], "advisory_pilot_case_review_assist")
        self.assertTrue(payload["pilot_review_assist_report"]["advisory_packet_only"])
        self.assertFalse(payload["pilot_review_assist_report"]["contains_completed_manual_decisions"])
        self.assertFalse(contains_key(payload["pilot_review_assist_report"], "reviewer_input_template"))
        self.assertFalse(contains_key(payload["pilot_review_assist_report"], "reviewer_decision"))
        self.assertFalse(contains_key(payload["pilot_review_assist_report"], "workbench_items"))
        self.assertFalse(contains_key(payload["pilot_review_assist_report"], "decision_status"))
        self.assertEqual(payload["pilot_review_assist"]["matched_workbench_cases"], 1)
        self.assertEqual(
            payload["workbench"]["workbench_items"][0]["case_context"]["case_topic"],
            "客户数据泄露后，需要判断企业通知、补救和赔偿责任。",
        )
        self.assertEqual(payload["workbench"]["summary"]["items_with_case_context"], 1)
        self.assertEqual(
            payload["original_llm_outputs"]["case_a"]["answer"],
            "公司应立即采取补救措施并通知监管部门和个人。",
        )
        self.assertEqual(payload["original_llm_outputs"]["case_a"]["answer_confidence"], 0.91)
        self.assertEqual(payload["ui"]["default_language"], "zh-CN")
        self.assertEqual(
            [language["code"] for language in payload["ui"]["supported_languages"]],
            ["zh-CN", "en-US"],
        )
        self.assertEqual(payload["ui"]["supported_languages"][0]["label"], "简体中文")
        self.assertEqual(payload["ui"]["supported_languages"][1]["label"], "English")
        self.assertIn("messages", payload["ui"])
        self.assertIn("法律风控人工复核台", payload["ui"]["messages"]["zh-CN"]["brand"]["title"])
        self.assertEqual(payload["ui"]["messages"]["zh-CN"]["sections"]["globalPipeline"], "整份导出处理结果")
        self.assertEqual(
            payload["ui"]["messages"]["zh-CN"]["pipeline"]["subtitle"],
            "这是本次导出的整份复核 JSON 的处理结果，不代表当前选中的单个案例。",
        )
        self.assertEqual(payload["ui"]["messages"]["en-US"]["sections"]["globalPipeline"], "Full-export result")
        self.assertIn("Operation Guide", payload["ui"]["messages"]["en-US"]["sections"]["guide"])

    def test_html_is_self_contained_and_contains_export_controls(self):
        payload = {
            "version": "0.4.7.8.13",
            "summary": {"ready_for_static_review": True},
            "guardrails": GUARDRAILS,
            "ui": {
                "default_language": "zh-CN",
                "supported_languages": [
                    {"code": "zh-CN", "label": "简体中文"},
                    {"code": "en-US", "label": "English"},
                ],
                "guide_steps": ["先选择队列。", "再填写复核。"],
                "messages": {
                    "zh-CN": {
                        "brand": {"title": "法律风控人工复核台"},
                        "sections": {"guide": "操作指南"},
                        "queues": {"all_cases": "全部案例"},
                        "actions": {
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
                            "autoSavedHint": "输入会自动暂存在本浏览器。",
                        },
                        "reviewImport": {
                            "statusLabel": "本页导入状态",
                            "never": "尚未导入草稿",
                            "lastImported": "{imported} 条复核记录已导入，{cleared} 条旧草稿已清除，{unknown} 条未匹配，{duplicate} 条重复，{skipped} 条为空",
                            "lastImportedWithSuggestions": "{imported} 条复核记录已导入，{suggestions} 条 AI 参考已载入，{cleared} 条旧草稿已清除，{unknown} 条未匹配，{duplicate} 条重复，{skipped} 条为空",
                            "dialogTitle": "导入复核 JSON",
                            "success": "导入完成：本次导入已替换旧本地草稿，避免旧草稿混入下一次导出。",
                            "successWithSuggestions": "已按 case_id 自动载入；AI 预填只进入参考区，不会自动成为人工结论。",
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
                        "caseBadges": {"exportReady": "可导出", "reviewPending": "待复核"},
                        "originalOutput": {
                            "title": "原 LLM 输出",
                            "subtitle": "用于和证据链、诊断问题进行对照。",
                            "confidence": "置信度",
                            "source": "来源",
                            "missing": "现有离线报告未提供原 LLM 输出。",
                        },
                        "questions": {"title": "建议复核问题", "empty": "暂无问题", "original": "原始问题"},
                        "caseContext": {
                            "caseTopic": "案由线索",
                            "question": "待审问题",
                            "scenario": "风险场景",
                            "domains": "涉及领域",
                            "expectedRiskTypes": "预期风险类型",
                            "expectedActions": "预期整改动作",
                            "source": "来源",
                            "sourceRagEvalCases": "评测用例",
                            "sourceScenarioRegistry": "场景登记",
                        },
                        "decision": {
                            "summaryTitle": "复核判断摘要",
                            "summarySubtitle": "先确认诊断是否成立。",
                            "authorityNoticeTitle": "听人工填写区",
                            "authorityNotice": "正式结论只来自下方人工填写区；参考材料、系统预筛和 AI 参考都不会自动导出为结论。",
                            "aiSuggestionTitle": "参考：AI 预填",
                            "aiSuggestionSubtitle": "这里是可参考的预填内容，不是人工复核结论。",
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
                            "useOriginalCodeHint": "导出仍保留原始代码。",
                            "requiredBadge": "必填",
                            "conditionalBadge": "条件必填",
                            "optionalBadge": "可选",
                            "requiredHint": "必须填写。",
                            "conditionalHint": "部分结论需要填写。",
                            "optionalHint": "不确定可以留空。",
                            "reviewer": "复核人",
                            "reviewerHelp": "填写你的名字或团队代号。",
                            "reviewedAt": "复核日期",
                            "reviewedAtPlaceholder": "YYYY-MM-DD",
                            "reviewedAtHelp": "建议使用 YYYY-MM-DD。",
                            "decision": "复核结论",
                            "decisionHelp": "如果无法判断，可以选信息不足或暂缓。",
                            "confirmedRootCauses": "确认的根因",
                            "confirmedRootCausesHelp": "确认诊断成立时至少选择一个。",
                            "rejectedRootCauses": "驳回的根因",
                            "rejectedRootCausesHelp": "不确定可以不填。",
                            "confirmedFollowUpActions": "确认的治理动作",
                            "confirmedFollowUpActionsHelp": "明确需要后续跟进时再选。",
                            "proposedChangeTargets": "拟变更目标",
                            "proposedChangeTargetsHelp": "不确定工程目标时可以留空。",
                            "fixtureCandidate": "标记为回归测试样本候选",
                            "fixtureCandidateHint": "只表示值得后续整理为测试样本候选，不会直接写入 eval case。",
                            "rationale": "理由",
                            "rationaleHelp": "用自然语言写判断理由即可。",
                            "notes": "备注",
                            "notesHelp": "记录疑问或待确认事项。",
                        },
                    },
                    "en-US": {
                        "brand": {"title": "Legal Risk Review Workbench"},
                        "sections": {"guide": "Operation Guide"},
                        "queues": {"all_cases": "All cases"},
                        "actions": {
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
                            "autoSavedHint": "Inputs are auto-stored locally.",
                        },
                        "reviewImport": {
                            "statusLabel": "Page import",
                            "never": "No draft import yet",
                            "lastImported": "{imported} drafts imported, {cleared} old drafts cleared, {unknown} unmatched, {duplicate} duplicate, {skipped} empty",
                            "lastImportedWithSuggestions": "{imported} drafts imported, {suggestions} AI suggestions loaded, {cleared} old drafts cleared, {unknown} unmatched, {duplicate} duplicate, {skipped} empty",
                            "dialogTitle": "Import review file",
                            "success": "Import completed: imported drafts replaced old local drafts so stale drafts cannot mix into the next export.",
                            "successWithSuggestions": "Rows were matched by case_id; AI prefills were loaded only as suggestions, not manual decisions.",
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
                        "caseBadges": {"exportReady": "export ready", "reviewPending": "review pending"},
                        "originalOutput": {
                            "title": "Original LLM output",
                            "subtitle": "Use this to compare the prior answer against evidence and diagnostics.",
                            "confidence": "Confidence",
                            "source": "Source",
                            "missing": "No original LLM output is available in saved offline reports.",
                        },
                        "questions": {"title": "Suggested review questions", "empty": "No questions", "original": "Original question"},
                        "caseContext": {
                            "caseTopic": "Case topic",
                            "question": "Question under review",
                            "scenario": "Risk scenario",
                            "domains": "Domains",
                            "expectedRiskTypes": "Expected risk types",
                            "expectedActions": "Expected remediation actions",
                            "source": "Source",
                            "sourceRagEvalCases": "Eval cases",
                            "sourceScenarioRegistry": "Scenario registry",
                        },
                        "decision": {
                            "summaryTitle": "Review decision summary",
                            "summarySubtitle": "Confirm whether the diagnostic is valid.",
                            "aiSuggestionTitle": "AI-assisted suggestion",
                            "aiSuggestionSubtitle": "This is a reference prefill, not a manual review decision.",
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
                            "useOriginalCodeHint": "Exports still keep original codes.",
                            "requiredBadge": "Required",
                            "conditionalBadge": "Conditional",
                            "optionalBadge": "Optional",
                            "requiredHint": "Required.",
                            "conditionalHint": "Required for some decisions.",
                            "optionalHint": "Leave blank if unsure.",
                            "reviewer": "Reviewer",
                            "reviewerHelp": "Use your name or team code.",
                            "reviewedAt": "Reviewed at",
                            "reviewedAtPlaceholder": "YYYY-MM-DD",
                            "reviewedAtHelp": "Use YYYY-MM-DD.",
                            "decision": "Decision",
                            "decisionHelp": "If unsure, choose insufficient information or defer.",
                            "confirmedRootCauses": "Confirmed root causes",
                            "confirmedRootCausesHelp": "Select at least one when confirming the issue.",
                            "rejectedRootCauses": "Rejected root causes",
                            "rejectedRootCausesHelp": "Leave blank if unsure.",
                            "confirmedFollowUpActions": "Confirmed follow-up actions",
                            "confirmedFollowUpActionsHelp": "Select only actions to consider.",
                            "proposedChangeTargets": "Proposed change targets",
                            "proposedChangeTargetsHelp": "Leave blank if unclear.",
                            "fixtureCandidate": "Regression-test candidate",
                            "fixtureCandidateHint": "This only marks future test-sample candidacy; it does not write to eval cases.",
                            "rationale": "Rationale",
                            "rationaleHelp": "Plain-language reasoning is enough.",
                            "notes": "Notes",
                            "notesHelp": "Use this for follow-up notes.",
                        },
                    },
                },
            },
            "original_llm_outputs": {
                "case_a": {
                    "answer": "公司应立即采取补救措施并通知监管部门和个人。",
                    "answer_confidence": 0.91,
                    "source": "rag_eval_report",
                }
            },
            "workbench": {
                "summary": {"total_workbench_items": 1, "pending_items": 1, "high_priority_items": 0},
                "csv_fields": ["case_id"],
                "workbench_items": [
                    {
                        "case_id": "case_a",
                        "decision_status": "pending",
                        "case_context": {
                            "case_topic": "客户数据泄露后的企业通知和补救责任",
                            "question": "公司应如何处理客户数据泄露？",
                            "expected_risk_types": ["数据泄露"],
                            "expected_actions": ["通知监管部门"],
                            "scenario_contexts": [
                                {"description": "客户数据泄露场景", "domain": "数据合规"}
                            ],
                            "sources": {"rag_eval_cases": True, "scenario_registry": True},
                        },
                        "diagnostic_summary": {
                            "anchor_dependency": {
                                "detected_issues": ["anchor_dependency_review_needed"],
                                "review_reasons": ["Needs review."],
                                "root_causes": ["anchor_dependency_governance"],
                            }
                        },
                        "issue_types": ["anchor_dependency_review_needed"],
                        "suggested_root_causes": ["anchor_dependency_governance", "insufficient_saved_evidence"],
                        "suggested_follow_up_actions": ["anchor_dependency_governance_review", "needs_additional_evidence_capture"],
                        "suggested_review_questions": [
                            "Did dense/sparse/union retrieval miss expected evidence before anchor injection?"
                        ],
                    }
                ],
            },
            "contract_report": {
                "field_contract": {
                    "allowed_values": {
                        "decision": [
                            "confirm_diagnostic_issue",
                            "confirm_scope_adjustment_needed",
                            "reject_diagnostic_issue",
                            "insufficient_information",
                            "defer",
                        ],
                        "confirmed_root_causes": [
                            "anchor_dependency_governance",
                            "insufficient_saved_evidence",
                        ],
                        "rejected_root_causes": [
                            "anchor_dependency_governance",
                            "insufficient_saved_evidence",
                        ],
                        "confirmed_follow_up_actions": [
                            "anchor_dependency_governance_review",
                            "needs_additional_evidence_capture",
                            "no_action",
                        ],
                    }
                }
            },
        }

        html = html_document(payload)

        self.assertIn("Legal Risk Manual Review Workbench", html)
        self.assertIn("case_a", html)
        self.assertIn("Export ready drafts JSON", html)
        self.assertIn("Download view-only CSV", html)
        self.assertIn("Import review file", html)
        self.assertIn("Save draft", html)
        self.assertIn("操作指南", html)
        self.assertIn("法律风控人工复核台", html)
        self.assertIn("保存本案草稿", html)
        self.assertIn("导出复核记录 JSON", html)
        self.assertIn("下载 CSV", html)
        self.assertIn("导入复核 JSON", html)
        self.assertIn("Operation Guide", html)
        self.assertIn("All cases", html)
        self.assertIn("language-select", html)
        self.assertIn("简体中文", html)
        self.assertIn("English", html)
        self.assertIn("案由线索", html)
        self.assertIn("客户数据泄露后的企业通知和补救责任", html)
        self.assertIn("公司应如何处理客户数据泄露？", html)
        self.assertIn('"case_topic"', html)
        self.assertIn('"question"', html)
        self.assertIn("version: payload.version", html)
        self.assertNotIn('version: "0.4.7.8.2"', html)
        self.assertIn("decisionOptionGlossary", html)
        self.assertIn("fieldGlossary", html)
        self.assertIn("decision-workflow", html)
        self.assertIn("workflowEvidence", html)
        self.assertIn("fixtureCandidateHint", html)
        self.assertIn("rationalePlaceholder", html)
        self.assertIn("复核判断摘要", html)
        self.assertIn("确认诊断成立", html)
        self.assertIn("确认需要范围校准", html)
        self.assertIn("驳回诊断", html)
        self.assertIn("信息不足", html)
        self.assertIn("暂缓", html)
        self.assertIn("原始代码", html)
        self.assertIn("现有保存证据不足", html)
        self.assertIn("需要补充证据采集", html)
        self.assertIn("reviewQuestionGlossary", html)
        self.assertIn("question-card", html)
        self.assertIn("在 anchor 介入之前，dense、sparse 或 union 召回是否已经漏掉了预期证据？", html)
        self.assertIn("原始问题", html)
        self.assertIn("originalLlmOutputs", html)
        self.assertIn("original-output", html)
        self.assertIn("原 LLM 输出", html)
        self.assertIn("公司应立即采取补救措施并通知监管部门和个人。", html)
        self.assertIn('"answer_confidence":0.91', html)
        self.assertIn("language-control", html)
        self.assertIn('name="review-decision"', html)
        self.assertIn("languageKey", html)
        self.assertIn("labelGlossary", html)
        self.assertIn("data-jump-tab", html)
        self.assertIn("exportStateKey", html)
        self.assertIn("markExported", html)
        self.assertIn("readyDraftCaseIds", html)
        self.assertIn("blockedDraftCaseIds", html)
        self.assertIn("ready_human_drafts_only", html)
        self.assertIn("exported_draft_items", html)
        self.assertIn("blocked_draft_items", html)
        self.assertIn("draft.human_confirmed_ai_suggestion = false", html)
        self.assertIn("items.filter(item => readyIds.has(item.case_id))", html)
        self.assertIn("saveCaseDraft", html)
        self.assertIn('data-action="save-case-draft"', html)
        self.assertIn("saved_at", html)
        self.assertIn("draftSave", html)
        self.assertIn("尚未点击保存", html)
        self.assertIn("上次保存", html)
        self.assertIn("Unmanually saved updates", html)
        self.assertIn("requirement-badge", html)
        self.assertIn("fieldLabelText", html)
        self.assertIn("必填", html)
        self.assertIn("条件必填", html)
        self.assertIn("可选", html)
        self.assertIn("Required", html)
        self.assertIn("Conditional", html)
        self.assertIn("Optional", html)
        self.assertIn("用自然语言写判断理由即可", html)
        self.assertIn("Leave blank if unsure", html)
        self.assertIn("review-import-file", html)
        self.assertIn("review-import-input", html)
        self.assertIn("import-summary", html)
        self.assertIn("importReviewFile", html)
        self.assertIn("parseReviewJson", html)
        self.assertIn("CSV import is intentionally unsupported", html)
        self.assertIn("FileReader", html)
        self.assertIn("reviewerDraftFields", html)
        self.assertIn("importStateKey", html)
        self.assertIn("导入完成：本次导入已替换旧本地草稿", html)
        self.assertIn("Import completed: imported drafts replaced old local drafts", html)
        self.assertIn("workbenchFingerprint", html)
        self.assertIn("cleared_draft_rows", html)
        self.assertIn("exported_case_ids", html)
        self.assertIn("window.confirm", html)
        self.assertIn("window.alert", html)
        self.assertIn("isFilledWorkbenchExport", html)
        self.assertIn("isSafeAiSuggestionImport", html)
        self.assertIn("invalid_decision", html)
        self.assertIn("invalid_follow_up_action", html)
        self.assertNotIn('key: "guide"', html)
        self.assertIn("localStorage", html)
        self.assertNotIn("fetch(", html)
        self.assertNotIn("rag_query(", html)
        self.assertNotIn("/ask", html)

    def test_build_report_declares_static_tool_capabilities(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "index.html"
            output.write_text("<html></html>", encoding="utf-8")
            report = build_report(
                {
                    "summary": {
                        "workbench_items": 3,
                        "pending_items": 2,
                        "high_priority_items": 1,
                        "gate_status": "blocked",
                        "ready_for_static_review": True,
                        "original_llm_output_cases": 2,
                    }
                },
                output,
            )

        self.assertTrue(report["summary"]["html_generated"])
        self.assertTrue(report["summary"]["supports_case_list"])
        self.assertTrue(report["summary"]["supports_reviewer_form"])
        self.assertTrue(report["summary"]["supports_csv_export"])
        self.assertTrue(report["summary"]["supports_operation_guide"])
        self.assertTrue(report["summary"]["supports_language_switch"])
        self.assertTrue(report["summary"]["supports_case_label_glossary"])
        self.assertTrue(report["summary"]["supports_case_context"])
        self.assertTrue(report["summary"]["supports_decision_tab_readability"])
        self.assertTrue(report["summary"]["supports_question_i18n"])
        self.assertTrue(report["summary"]["supports_original_llm_output_panel"])
        self.assertTrue(report["summary"]["supports_compact_language_control"])
        self.assertTrue(report["summary"]["supports_export_state_tracking"])
        self.assertTrue(report["summary"]["supports_review_export_import"])
        self.assertTrue(report["summary"]["supports_field_requirement_labels"])
        self.assertTrue(report["summary"]["supports_manual_draft_save"])
        self.assertTrue(report["summary"]["supports_ai_suggestion_isolation"])
        self.assertTrue(report["summary"]["supports_pilot_batch_queue"])
        self.assertTrue(report["summary"]["supports_per_case_human_judgment_checklist"])
        self.assertTrue(report["summary"]["supports_pilot_batch_advisory_panel"])
        self.assertTrue(report["summary"]["supports_pilot_review_assist_panel"])
        self.assertTrue(report["summary"]["supports_scoped_local_drafts"])
        self.assertTrue(report["summary"]["imports_replace_stale_local_drafts"])
        self.assertTrue(report["summary"]["supports_json_import_contract"])
        self.assertTrue(report["summary"]["supports_export_case_preview"])
        self.assertTrue(report["summary"]["exports_exported_case_ids"])
        self.assertTrue(report["summary"]["validates_frontend_allowed_values"])
        self.assertTrue(report["summary"]["escapes_csv_formula_cells"])
        self.assertTrue(report["summary"]["requires_human_confirmation_for_copied_ai_suggestion"])
        self.assertTrue(report["summary"]["exports_ready_human_drafts_only"])
        self.assertEqual(report["summary"]["pilot_batch_cases"], 0)
        self.assertFalse(report["summary"]["pilot_batch_advisory_only"])
        self.assertEqual(report["summary"]["pilot_batch_completed_decisions"], 0)
        self.assertEqual(report["summary"]["pilot_review_assist_cases"], 0)
        self.assertFalse(report["summary"]["pilot_review_assist_advisory_only"])
        self.assertEqual(report["summary"]["pilot_review_assist_completed_decisions"], 0)
        self.assertEqual(report["summary"]["original_llm_output_cases"], 2)
        self.assertEqual(report["summary"]["default_language"], "zh-CN")
        self.assertEqual(report["summary"]["supported_languages"], ["zh-CN", "en-US"])
        self.assertEqual(report["guardrails"]["backend_api_write"], "disallowed")

    def test_pilot_review_assist_rejects_completed_manual_decision_reports(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            args = args_for(tmp)
            for path in [
                args.contract_report,
                args.intake_contract,
                args.progress_report,
                args.governance_report,
                args.import_report,
                args.diff_report,
                args.validation_report,
                args.promotion_report,
                args.closeout_report,
                args.rag_eval_report,
                args.rag_eval_cases,
                args.scenario_registry,
            ]:
                write_json(path, {})
            write_json(
                args.workbench,
                {
                    "summary": {"total_workbench_items": 1},
                    "workbench_items": [{"case_id": "case_a"}],
                },
            )
            write_json(
                args.pilot_batch_report,
                {
                    "schema_kind": "advisory_pilot_packet",
                    "advisory_packet_only": True,
                    "contains_completed_manual_decisions": False,
                    "summary": {"completed_manual_decisions": 0},
                    "pilot_cases": [],
                },
            )
            write_json(
                args.pilot_review_assist_report,
                {
                    "schema_kind": "advisory_pilot_case_review_assist",
                    "advisory_packet_only": True,
                    "contains_completed_manual_decisions": True,
                    "summary": {"assisted_cases": 1, "completed_manual_decisions": 1},
                    "assisted_cases": [{"case_id": "case_a", "plain_case_brief": "Must not attach."}],
                },
            )

            payload = build_payload(args)

        item = payload["workbench"]["workbench_items"][0]
        self.assertNotIn("pilot_review_assist", item)
        self.assertEqual(payload["summary"]["pilot_review_assist_cases"], 0)
        self.assertTrue(payload["summary"]["pilot_review_assist_completed_decisions"], 1)

    def test_pilot_batch_rejects_completed_or_non_advisory_reports(self):
        for invalid_patch in [
            {"contains_completed_manual_decisions": True, "summary": {"completed_manual_decisions": 1}},
            {"advisory_packet_only": False, "summary": {"completed_manual_decisions": 0}},
            {"schema_kind": "filled_manual_review_export", "summary": {"completed_manual_decisions": 0}},
        ]:
            with self.subTest(invalid_patch=invalid_patch):
                with tempfile.TemporaryDirectory() as tmpdir:
                    tmp = Path(tmpdir)
                    args = args_for(tmp)
                    for path in [
                        args.contract_report,
                        args.intake_contract,
                        args.progress_report,
                        args.governance_report,
                        args.import_report,
                        args.diff_report,
                        args.validation_report,
                        args.promotion_report,
                        args.closeout_report,
                        args.rag_eval_report,
                        args.rag_eval_cases,
                        args.scenario_registry,
                    ]:
                        write_json(path, {})
                    write_json(
                        args.workbench,
                        {
                            "summary": {"total_workbench_items": 1},
                            "workbench_items": [{"case_id": "case_a"}],
                        },
                    )
                    pilot_batch = {
                        "schema_kind": "advisory_pilot_packet",
                        "advisory_packet_only": True,
                        "contains_completed_manual_decisions": False,
                        "summary": {
                            "pilot_case_count": 1,
                            "completed_manual_decisions": 0,
                            "promotion_candidates": 0,
                            "ready_action_candidates": 0,
                        },
                        "pilot_cases": [
                            {
                                "case_id": "case_a",
                                "rank": 1,
                                "reviewer_input_template": {"decision": "must_not_attach"},
                            }
                        ],
                    }
                    pilot_batch.update(invalid_patch)
                    write_json(args.pilot_batch_report, pilot_batch)
                    write_json(
                        args.pilot_review_assist_report,
                        {
                            "schema_kind": "advisory_pilot_case_review_assist",
                            "advisory_packet_only": True,
                            "contains_completed_manual_decisions": False,
                            "summary": {"completed_manual_decisions": 0},
                            "assisted_cases": [],
                        },
                    )

                    payload = build_payload(args)

                item = payload["workbench"]["workbench_items"][0]
                self.assertNotIn("pilot_batch", item)
                self.assertEqual(payload["summary"]["pilot_batch_cases"], 0)

    def test_case_context_is_derived_from_existing_offline_reports(self):
        workbench = {
            "summary": {},
            "workbench_items": [{"case_id": "case_a", "expected_domains": ["数据合规"]}],
        }
        rag_eval_report = {"reports": [{"id": "case_a", "question": "企业发生数据泄露后应承担什么责任？"}]}
        rag_eval_cases = {
            "cases": [
                {
                    "id": "case_a",
                    "question": "企业发生数据泄露后应承担什么责任？",
                    "expected_risk_types": ["行政处罚", "民事赔偿"],
                    "expected_actions": ["立即补救", "通知个人和监管部门"],
                }
            ]
        }
        scenario_registry = {
            "scenarios": [
                {
                    "scenario_id": "data_breach",
                    "domain": "数据合规",
                    "description": "个人信息泄露后，审查企业安全保护、通知和补救义务。",
                    "eval_case_ids": ["case_a"],
                }
            ]
        }

        enriched = enrich_workbench_with_case_context(
            workbench,
            rag_eval_report,
            rag_eval_cases,
            scenario_registry,
        )

        context = enriched["workbench_items"][0]["case_context"]
        self.assertEqual(context["case_topic"], "个人信息泄露后，审查企业安全保护、通知和补救义务。")
        self.assertEqual(context["question"], "企业发生数据泄露后应承担什么责任？")
        self.assertEqual(context["expected_risk_types"], ["行政处罚", "民事赔偿"])
        self.assertEqual(context["expected_actions"], ["立即补救", "通知个人和监管部门"])
        self.assertTrue(context["sources"]["rag_eval_report"])
        self.assertTrue(context["sources"]["rag_eval_cases"])
        self.assertTrue(context["sources"]["scenario_registry"])

    def test_case_context_count_requires_existing_report_signal(self):
        self.assertFalse(has_case_context_signal({"case_topic": "case_a", "sources": {}}))
        self.assertTrue(has_case_context_signal({"question": "企业是否需要通知监管部门？", "sources": {}}))
        self.assertTrue(has_case_context_signal({"case_topic": "case_a", "sources": {"rag_eval_cases": True}}))

    def test_original_llm_outputs_are_extracted_from_saved_report_only(self):
        outputs = extract_original_llm_outputs(
            {
                "reports": [
                    {
                        "id": "case_a",
                        "answer": "原回答内容",
                        "answer_confidence": 0.88,
                    },
                    {"id": "case_b", "answer": ""},
                ]
            }
        )

        self.assertEqual(outputs["case_a"]["answer"], "原回答内容")
        self.assertEqual(outputs["case_a"]["answer_confidence"], 0.88)
        self.assertEqual(outputs["case_a"]["source"], "rag_eval_report")
        self.assertNotIn("case_b", outputs)


if __name__ == "__main__":
    unittest.main()
