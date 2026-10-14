import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


HTML_PATH = Path("tools/manual_review_visual_workbench/index.html")
BUILD_REPORT_PATH = Path("tests/manual_review_visual_workbench_build_report.json")


def read_html() -> str:
    return HTML_PATH.read_text(encoding="utf-8")


def embedded_payload(html: str) -> dict:
    match = re.search(
        r'<script id="workbench-data" type="application/json">([\s\S]*?)</script>',
        html,
    )
    if not match:
        raise AssertionError("workbench-data JSON script is missing")
    return json.loads(match.group(1))


def css_block(html: str, selector: str) -> str:
    match = re.search(rf"{re.escape(selector)}\s*\{{([\s\S]*?)\n    \}}", html)
    if not match:
        raise AssertionError(f"CSS block is missing: {selector}")
    return match.group(1)


def css_media_block(html: str, media: str) -> str:
    match = re.search(rf"{re.escape(media)}\s*\{{([\s\S]*?)\n    \}}\n    @media", html)
    if match:
        return match.group(1)
    match = re.search(rf"{re.escape(media)}\s*\{{([\s\S]*?)\n    \}}\n  </style>", html)
    if not match:
        raise AssertionError(f"CSS media block is missing: {media}")
    return match.group(1)


class ManualReviewVisualWorkbenchBuildArtifactTest(unittest.TestCase):
    def test_generated_html_embeds_current_workbench_payload(self):
        html = read_html()
        payload = embedded_payload(html)

        self.assertEqual(payload["version"], "0.4.7.8.23")
        self.assertEqual(len(payload["workbench"]["workbench_items"]), 36)
        self.assertEqual(payload["summary"]["pilot_batch_cases"], 5)
        self.assertTrue(payload["summary"]["pilot_batch_advisory_only"])
        self.assertEqual(payload["summary"]["pilot_batch_completed_decisions"], 0)
        self.assertEqual(payload["summary"]["pilot_review_assist_cases"], 5)
        self.assertTrue(payload["summary"]["pilot_review_assist_advisory_only"])
        self.assertEqual(payload["summary"]["pilot_review_assist_completed_decisions"], 0)
        self.assertEqual(payload["pilot_batch_report"]["schema_kind"], "advisory_pilot_packet")
        self.assertTrue(payload["pilot_batch_report"]["advisory_packet_only"])
        self.assertFalse(payload["pilot_batch_report"]["contains_completed_manual_decisions"])
        self.assertEqual(payload["pilot_batch"]["matched_workbench_cases"], 5)
        self.assertEqual(payload["pilot_review_assist_report"]["schema_kind"], "advisory_pilot_case_review_assist")
        self.assertTrue(payload["pilot_review_assist_report"]["advisory_packet_only"])
        self.assertFalse(payload["pilot_review_assist_report"]["contains_completed_manual_decisions"])
        self.assertEqual(payload["pilot_review_assist"]["matched_workbench_cases"], 5)
        self.assertEqual(payload["summary"]["gate_status"], "open")
        self.assertTrue(payload["summary"]["ready_for_static_review"])
        self.assertGreater(payload["workbench"]["summary"]["items_with_case_context"], 0)
        first_context = payload["workbench"]["workbench_items"][0]["case_context"]
        self.assertIn("case_topic", first_context)
        self.assertIn("question", first_context)
        self.assertIn("risk_employee_data_export_001", payload["original_llm_outputs"])
        self.assertIn("answer", payload["original_llm_outputs"]["risk_employee_data_export_001"])
        self.assertEqual(payload["ui"]["default_language"], "zh-CN")
        self.assertEqual(payload["ui"]["supported_languages"][0]["label"], "简体中文")
        self.assertEqual(payload["ui"]["supported_languages"][1]["label"], "English")
        self.assertEqual(
            [language["code"] for language in payload["ui"]["supported_languages"]],
            ["zh-CN", "en-US"],
        )
        self.assertIn("法律风控人工复核台", payload["ui"]["messages"]["zh-CN"]["brand"]["title"])
        self.assertIn("Operation Guide", payload["ui"]["messages"]["en-US"]["sections"]["guide"])
        pilot_items = [item for item in payload["workbench"]["workbench_items"] if item.get("pilot_batch")]
        self.assertEqual(len(pilot_items), 5)
        self.assertTrue(all(item["pilot_batch"]["advisory_only"] for item in pilot_items))
        self.assertTrue(all(item["pilot_batch"]["not_a_reviewer_decision"] for item in pilot_items))
        self.assertTrue(all("reviewer_input_template" not in item["pilot_batch"] for item in pilot_items))
        assist_items = [item for item in payload["workbench"]["workbench_items"] if item.get("pilot_review_assist")]
        self.assertEqual(len(assist_items), 5)
        self.assertTrue(all(item["pilot_review_assist"]["advisory_only"] for item in assist_items))
        self.assertTrue(all(item["pilot_review_assist"]["not_a_reviewer_decision"] for item in assist_items))
        for item in assist_items:
            self.assertNotIn("reviewer_input_template", item["pilot_review_assist"])
            self.assertNotIn("reviewer_decision", item["pilot_review_assist"])
            self.assertNotIn("workbench_items", item["pilot_review_assist"])
            self.assertNotIn("decision_status", item["pilot_review_assist"])

    def test_generated_html_contains_required_workbench_controls(self):
        html = read_html()

        required = [
            'data-testid="search-input"',
            'data-testid="case-list"',
            'data-testid="case-detail"',
            'data-testid="decision-form"',
            'data-action="save-case-draft"',
            'data-action="export-json"',
            'data-action="export-csv"',
            'data-action="import-review-file"',
            'data-action="apply-ai-suggestion"',
            'data-testid="language-select"',
            'data-testid="review-import-input"',
            'data-testid="import-summary"',
            'id="side-guide"',
            'id="global-pipeline"',
            'data-testid="global-pipeline"',
            "操作指南",
            "整批概况",
            "整份导出处理结果",
            "这是本次导出的整份复核 JSON 的处理结果，不代表当前选中的单个案例。",
            "用于查看证据支撑诊断、填写人工复核记录，并查看整份复核导出的处理结果。",
            "简体中文",
            "English",
            "法律风控人工复核台",
            "全部案例",
            "导出复核记录 JSON",
            "下载 CSV",
            "导入复核 JSON",
            "导入复核记录",
            "检查变更差异",
            "检查记录完整性",
            "生成待处理动作",
            "是否允许进入后续治理",
            "Legal Risk Review Workbench",
            "Operation Guide",
            "Batch summary",
            "Full-export result",
            "This is the processing result for the full exported review JSON, not the currently selected case.",
            "Evidence grounding diagnostics, manual review records, and the global process for the full review export.",
            "All cases",
            "Export ready drafts JSON",
            "Download view-only CSV",
            "Import review file",
            "Save draft",
            "保存本案草稿",
            "languageKey",
            "labelGlossary",
            "data-jump-tab",
            "exportStateKey",
            "importStateKey",
            "markExported",
            "saveCaseDraft",
            "saved_at",
            "draftSave",
            "aiSuggestionStateKey",
            "aiSuggestionFields",
            "ai-suggestion",
            "ai_review_suggestion",
            "human_confirmed_ai_suggestion",
            "missing_ai_suggestion_confirmation",
            "humanDraftForExport",
            "readyDraftCaseIds",
            "blockedDraftCaseIds",
            "ready_human_drafts_only",
            "exported_draft_items",
            "blocked_draft_items",
            "pilot_batch",
            "pilotBatchCaseIds",
            "rankByCaseId",
            "pilot-batch-panel",
            "pilotReviewAssistFor",
            "pilot-review-assist-panel",
            "参考：证据阅读提示",
            "阅读参考",
            "此面板只帮助理解案件和证据链，不会写入导出草稿，也不会代替人工判断。",
            "pilot_review_assist: undefined",
            "参考：优先复核清单",
            "看过这张清单不等于完成复核",
            "I have read the pilot checklist",
            "advisory_decision",
            "advisory_root_causes",
            "advisory_follow_up_actions",
            "pilotChecklistStateKey",
            "toggle-pilot-checklist",
            "draft.human_confirmed_ai_suggestion = false",
            "looksLikeAiAssistedSource",
            "applyAiSuggestion",
            "参考：AI 预填",
            "我已人工核对，并将该 AI 参考作为本人复核结论",
            "引用 AI 参考到草稿",
            "AI suggestion",
            "I have manually reviewed and confirmed this AI suggestion",
            "Copy AI suggestion to draft",
            "上次保存",
            "有未手动保存的更新",
            "requirement-badge",
            "fieldLabelText",
            "field-label-head",
            "必填",
            "条件必填",
            "可选",
            "Required",
            "Conditional",
            "Optional",
            "importReviewFile",
            "parseReviewJson",
            "FileReader",
            "reviewerDraftFields",
            "本页导入状态",
            "导入完成：本次导入已替换旧本地草稿",
            "workbenchFingerprint",
            "cleared_draft_rows",
            "duplicate_rows",
            "exported_case_ids",
            "window.confirm",
            "window.alert",
            "isFilledWorkbenchExport",
            "isSafeAiSuggestionImport",
            "invalid_decision",
            "invalid_follow_up_action",
            "CSV import is intentionally unsupported",
            "caseContext",
            "案由线索",
            "待审问题",
            "风险场景",
            "预期整改动作",
            "标签说明",
            "当前案例标签说明",
            "最终证据选择策略",
            "高风险证据复核",
            "未导出的更新",
            'risk_employee_data_export_001',
        ]
        for marker in required:
            self.assertIn(marker, html)
        decision_markers = [
            "decisionOptionGlossary",
            "fieldGlossary",
            "reviewQuestionGlossary",
            "question-card",
            "原始问题",
            "在 anchor 介入之前，dense、sparse 或 union 召回是否已经漏掉了预期证据？",
            "originalLlmOutputs",
            "original-output",
            "原 LLM 输出",
            "language-control",
            "decision-workflow",
            'name="review-decision"',
            "confirm_scope_adjustment_needed",
            "insufficient_information",
            "fixtureCandidateHint",
        ]
        for marker in decision_markers:
            self.assertIn(marker, html)
        self.assertNotIn('key: "guide"', html)
        self.assertNotIn('key: "pipeline", labelKey: "tabs.pipeline"', html)
        self.assertNotIn("后续状态", html)
        self.assertNotIn("后续准入检查状态", html)
        self.assertNotIn("function renderPipeline()", html)
        self.assertNotIn('data-tab="pipeline"', html)
        self.assertNotIn('data-jump-tab="pipeline"', html)

    def test_build_report_declares_decision_tab_readability(self):
        report = json.loads(BUILD_REPORT_PATH.read_text(encoding="utf-8"))

        self.assertEqual(report["version"], "0.4.7.8.23")
        self.assertTrue(report["summary"]["supports_decision_tab_readability"])
        self.assertTrue(report["summary"]["supports_question_i18n"])
        self.assertTrue(report["summary"]["supports_original_llm_output_panel"])
        self.assertTrue(report["summary"]["supports_compact_language_control"])
        self.assertTrue(report["summary"]["supports_review_export_import"])
        self.assertTrue(report["summary"]["supports_field_requirement_labels"])
        self.assertTrue(report["summary"]["supports_manual_draft_save"])
        self.assertTrue(report["summary"]["supports_ai_suggestion_isolation"])
        self.assertTrue(report["summary"]["supports_pilot_batch_queue"])
        self.assertTrue(report["summary"]["supports_per_case_human_judgment_checklist"])
        self.assertTrue(report["summary"]["supports_pilot_batch_advisory_panel"])
        self.assertTrue(report["summary"]["supports_pilot_review_assist_panel"])
        self.assertTrue(report["summary"]["supports_manual_authority_notice"])
        self.assertTrue(report["summary"]["uses_concise_export_button_labels"])
        self.assertTrue(report["summary"]["shows_open_gate_as_no_blockers"])
        self.assertTrue(report["summary"]["hides_blocked_gate_queue_when_open"])
        self.assertTrue(report["summary"]["moves_pipeline_status_to_global_sidebar"])
        self.assertTrue(report["summary"]["removes_pipeline_from_case_tabs"])
        self.assertTrue(report["summary"]["supports_independent_panel_scrolling"])
        self.assertTrue(report["summary"]["keeps_detail_panel_synced_with_app_shell"])
        self.assertTrue(report["summary"]["uses_fixed_height_app_shell"])
        self.assertTrue(report["summary"]["keeps_sidebar_scroll_independent"])
        self.assertTrue(report["summary"]["restores_natural_mobile_flow"])
        self.assertTrue(report["summary"]["embedded_payload_question_pollution_free"])
        self.assertTrue(report["summary"]["supports_scoped_local_drafts"])
        self.assertTrue(report["summary"]["imports_replace_stale_local_drafts"])
        self.assertTrue(report["summary"]["supports_json_import_contract"])
        self.assertTrue(report["summary"]["supports_export_case_preview"])
        self.assertTrue(report["summary"]["exports_exported_case_ids"])
        self.assertTrue(report["summary"]["validates_frontend_allowed_values"])
        self.assertTrue(report["summary"]["escapes_csv_formula_cells"])
        self.assertTrue(report["summary"]["requires_human_confirmation_for_copied_ai_suggestion"])
        self.assertTrue(report["summary"]["exports_ready_human_drafts_only"])
        self.assertEqual(report["summary"]["pilot_batch_cases"], 5)
        self.assertTrue(report["summary"]["pilot_batch_advisory_only"])
        self.assertEqual(report["summary"]["pilot_batch_completed_decisions"], 0)
        self.assertEqual(report["summary"]["pilot_review_assist_cases"], 5)
        self.assertTrue(report["summary"]["pilot_review_assist_advisory_only"])
        self.assertEqual(report["summary"]["pilot_review_assist_completed_decisions"], 0)
        self.assertEqual(report["summary"]["workbench_items"], 36)
        self.assertEqual(report["summary"]["gate_status"], "open")

    def test_generated_html_does_not_call_rag_or_backend_entrypoints(self):
        html = read_html()

        prohibited = [
            "fetch(",
            "XMLHttpRequest",
            "/ask",
            "rag_query(",
            "ChatOpenAI",
        ]
        for marker in prohibited:
            self.assertNotIn(marker, html)

    def test_generated_html_does_not_embed_question_mark_pollution(self):
        html = read_html()

        self.assertNotIn("???", html)

    def test_open_gate_is_shown_as_no_blockers_not_zero_blocker_queue(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is required for the executable gate display check")

        html = read_html()
        payload_match = re.search(
            r'<script id="workbench-data" type="application/json">([\s\S]*?)</script>',
            html,
        )
        script_match = re.search(
            r"<script>\s*(const payload = JSON\.parse[\s\S]*?)\s*document\.addEventListener\(\"click\"",
            html,
        )
        if not payload_match or not script_match:
            raise AssertionError("workbench payload or executable script is missing")

        test_script = f"""
const vm = require("node:vm");
const store = new Map();
const payloadText = {json.dumps(payload_match.group(1))};
const elements = new Map();
const elementFor = id => {{
  if (!elements.has(id)) {{
    elements.set(id, {{
      id,
      textContent: "",
      innerHTML: "",
      className: "",
      value: "",
      checked: false,
      disabled: false,
      title: "",
      placeholder: "",
      appendChild() {{}},
      remove() {{}},
      addEventListener() {{}},
      setAttribute() {{}},
      querySelectorAll() {{ return []; }},
    }});
  }}
  return elements.get(id);
}};
const script = {json.dumps(script_match.group(1))} + `
render();
if (gateStatus() !== "open" || !isGateOpen()) {{
  throw new Error("expected current generated workbench gate to be open");
}}
if (visibleQueueDefs().some(queue => queue.key === "blocked_intake_gate")) {{
  throw new Error("open gate should not render a blocked-gate queue with count 0");
}}
const statusText = document.getElementById("side-status").innerHTML;
if (!statusText.includes("无阻断")) {{
  throw new Error("open gate side status should show no blockers");
}}
const globalPipelineText = document.getElementById("global-pipeline").innerHTML;
if (!globalPipelineText.includes("无阻断")) {{
  throw new Error("open gate global pipeline should show no blockers");
}}
currentFilter = "blocked_intake_gate";
if (filteredItems().length !== 0) {{
  throw new Error("blocked gate filter should be empty when gate is open");
}}
`;

const context = {{
  console,
  window: {{
    localStorage: {{
      getItem(key) {{ return store.has(key) ? store.get(key) : null; }},
      setItem(key, value) {{ store.set(key, String(value)); }},
    }},
  }},
  document: {{
    documentElement: {{}},
    title: "",
    getElementById(id) {{
      if (id === "workbench-data") return {{ textContent: payloadText }};
      return elementFor(id);
    }},
    querySelector() {{ return elementFor("query-selector"); }},
    querySelectorAll() {{ return []; }},
    createElement() {{ return elementFor("created-element-" + elements.size); }},
    body: elementFor("body"),
  }},
  URL: {{
    createObjectURL() {{ return "blob:test"; }},
    revokeObjectURL() {{}},
  }},
  Blob: function Blob() {{}},
  FileReader: function FileReader() {{}},
}};

vm.runInNewContext(script, context, {{ timeout: 5000 }});
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = Path(tmpdir) / "open_gate_display_check.js"
            script_path.write_text(test_script, encoding="utf-8")
            result = subprocess.run(
                [node, str(script_path)],
                cwd=Path.cwd(),
                text=True,
                capture_output=True,
                timeout=10,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_ai_suggestion_copy_requires_human_confirmation_before_export(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is required for the executable workbench export check")

        html = read_html()
        payload_match = re.search(
            r'<script id="workbench-data" type="application/json">([\s\S]*?)</script>',
            html,
        )
        script_match = re.search(
            r"<script>\s*(const payload = JSON\.parse[\s\S]*?)\s*document\.addEventListener\(\"click\"",
            html,
        )
        if not payload_match or not script_match:
            raise AssertionError("workbench payload or executable script is missing")

        test_script = f"""
const vm = require("node:vm");
const store = new Map();
const payloadText = {json.dumps(payload_match.group(1))};
const script = {json.dumps(script_match.group(1))} + `
render = function() {{}};
const cid = items[0].case_id;
aiSuggestions[cid] = {{
  ai_suggestion: true,
  human_confirmation_required: true,
  decision: "confirm_diagnostic_issue",
  confirmed_root_causes: ["primary_evidence_gap"],
  rejected_root_causes: [],
  confirmed_follow_up_actions: ["needs_additional_evidence_capture"],
  proposed_change_targets: [],
  fixture_candidate: true,
  rationale: "AI suggestion for executable export isolation test.",
  notes: "advisory only"
}};

applyAiSuggestion(cid);
drafts[cid].reviewer = "Human Reviewer";
drafts[cid].reviewed_at = "2026-05-12";

if (drafts[cid].human_confirmed_ai_suggestion !== false) {{
  throw new Error("copying an AI suggestion must reset human confirmation");
}}

const blocked = buildFilledWorkbench();
if (blocked.workbench_items.length !== 0) {{
  throw new Error("unconfirmed AI copied draft was exported");
}}
if (blocked.summary.export_policy !== "ready_human_drafts_only") {{
  throw new Error("export policy is not ready_human_drafts_only");
}}
if (blocked.summary.blocked_draft_items !== 1) {{
  throw new Error("blocked AI copied draft was not counted");
}}

drafts[cid].human_confirmed_ai_suggestion = true;
const ready = buildFilledWorkbench();
if (ready.workbench_items.length !== 1) {{
  throw new Error("confirmed ready human draft was not exported");
}}
const exportedTemplate = ready.workbench_items[0].reviewer_input_template;
if (exportedTemplate.human_confirmed_ai_suggestion !== undefined) {{
  throw new Error("human confirmation marker leaked into reviewer_input_template");
}}
if (exportedTemplate.ai_suggestion_applied_at !== undefined) {{
  throw new Error("AI provenance marker leaked into reviewer_input_template");
}}

applyAiSuggestion(cid);
if (drafts[cid].human_confirmed_ai_suggestion !== false) {{
  throw new Error("recopying an AI suggestion did not reset human confirmation");
}}
const reset = buildFilledWorkbench();
if (reset.workbench_items.length !== 0) {{
  throw new Error("recopied AI suggestion stayed exportable without reconfirmation");
}}
`;

const inertElement = () => ({{
  textContent: "",
  innerHTML: "",
  className: "",
  value: "",
  checked: false,
  appendChild() {{}},
  remove() {{}},
  addEventListener() {{}},
  setAttribute() {{}},
  querySelectorAll() {{ return []; }},
}});

const context = {{
  console,
  window: {{
    localStorage: {{
      getItem(key) {{ return store.has(key) ? store.get(key) : null; }},
      setItem(key, value) {{ store.set(key, String(value)); }},
    }},
  }},
  document: {{
    documentElement: {{}},
    getElementById(id) {{
      if (id === "workbench-data") return {{ textContent: payloadText }};
      return inertElement();
    }},
    querySelectorAll() {{ return []; }},
    createElement() {{ return inertElement(); }},
    body: inertElement(),
  }},
  URL: {{
    createObjectURL() {{ return "blob:test"; }},
    revokeObjectURL() {{}},
  }},
  Blob: function Blob() {{}},
  FileReader: function FileReader() {{}},
}};

vm.runInNewContext(script, context, {{ timeout: 5000 }});
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = Path(tmpdir) / "ai_suggestion_export_check.js"
            script_path.write_text(test_script, encoding="utf-8")
            result = subprocess.run(
                [node, str(script_path)],
                cwd=Path.cwd(),
                text=True,
                capture_output=True,
                timeout=10,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_pilot_checklist_marker_does_not_export_manual_decision(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is required for the executable pilot checklist export check")

        html = read_html()
        payload_match = re.search(
            r'<script id="workbench-data" type="application/json">([\s\S]*?)</script>',
            html,
        )
        script_match = re.search(
            r"<script>\s*(const payload = JSON\.parse[\s\S]*?)\s*document\.addEventListener\(\"click\"",
            html,
        )
        if not payload_match or not script_match:
            raise AssertionError("workbench payload or executable script is missing")

        test_script = f"""
const vm = require("node:vm");
const store = new Map();
const payloadText = {json.dumps(payload_match.group(1))};
const script = {json.dumps(script_match.group(1))} + `
render = function() {{}};
const cid = pilotBatchCaseIds()[0];
if (!cid) {{
  throw new Error("pilot batch queue is empty");
}}
currentFilter = "pilot_batch";
if (!filteredItems().some(item => item.case_id === cid)) {{
  throw new Error("pilot batch filter did not include the pilot case");
}}
const visible = filteredItems();
if (visible[0].case_id !== cid) {{
  throw new Error("pilot batch queue did not preserve pilot rank order");
}}
if (visible.some(item => !item.pilot_batch)) {{
  throw new Error("pilot batch queue included a non-pilot case");
}}
pilotChecklistState[cid] = {{ reviewed: true, reviewed_at: "2026-05-12T00:00:00Z" }};
persistPilotChecklistState();
const checklistOnly = buildFilledWorkbench();
if (checklistOnly.workbench_items.length !== 0) {{
  throw new Error("checklist-only pilot marker exported as a manual decision");
}}
if (checklistOnly.summary.pilot_checklist_marked_cases !== 1) {{
  throw new Error("pilot checklist marker was not counted separately");
}}
drafts[cid] = {{
  reviewer: "Human Reviewer",
  reviewed_at: "2026-05-12",
  decision: "confirm_diagnostic_issue",
  confirmed_root_causes: ["primary_evidence_gap"],
  rationale: "Human reviewer wrote this, not the pilot packet."
}};
const ready = buildFilledWorkbench();
if (ready.workbench_items.length !== 1) {{
  throw new Error("real human draft did not export");
}}
const exported = ready.workbench_items[0];
if (exported.pilot_batch !== undefined) {{
  throw new Error("pilot advisory metadata leaked into exported item");
}}
if (exported.pilot_review_assist !== undefined) {{
  throw new Error("pilot review assist metadata leaked into exported item");
}}
if (exported.reviewer_input_template.decision !== "confirm_diagnostic_issue") {{
  throw new Error("manual decision did not come from reviewer_input_template");
}}
`;

const inertElement = () => ({{
  textContent: "",
  innerHTML: "",
  className: "",
  value: "",
  checked: false,
  appendChild() {{}},
  remove() {{}},
  addEventListener() {{}},
  setAttribute() {{}},
  querySelectorAll() {{ return []; }},
}});

const context = {{
  console,
  window: {{
    localStorage: {{
      getItem(key) {{ return store.has(key) ? store.get(key) : null; }},
      setItem(key, value) {{ store.set(key, String(value)); }},
    }},
  }},
  document: {{
    documentElement: {{}},
    getElementById(id) {{
      if (id === "workbench-data") return {{ textContent: payloadText }};
      return inertElement();
    }},
    querySelectorAll() {{ return []; }},
    createElement() {{ return inertElement(); }},
    body: inertElement(),
  }},
  URL: {{
    createObjectURL() {{ return "blob:test"; }},
    revokeObjectURL() {{}},
  }},
  Blob: function Blob() {{}},
  FileReader: function FileReader() {{}},
}};

vm.runInNewContext(script, context, {{ timeout: 5000 }});
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = Path(tmpdir) / "pilot_checklist_export_check.js"
            script_path.write_text(test_script, encoding="utf-8")
            result = subprocess.run(
                [node, str(script_path)],
                cwd=Path.cwd(),
                text=True,
                capture_output=True,
                timeout=10,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_import_replaces_stale_drafts_and_csv_cells_are_escaped(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is required for the executable import governance check")

        html = read_html()
        payload_match = re.search(
            r'<script id="workbench-data" type="application/json">([\s\S]*?)</script>',
            html,
        )
        script_match = re.search(
            r"<script>\s*(const payload = JSON\.parse[\s\S]*?)\s*document\.addEventListener\(\"click\"",
            html,
        )
        if not payload_match or not script_match:
            raise AssertionError("workbench payload or executable script is missing")

        test_script = f"""
const vm = require("node:vm");
const store = new Map();
const payloadText = {json.dumps(payload_match.group(1))};
const script = {json.dumps(script_match.group(1))} + `
render = function() {{}};
const first = items[0].case_id;
const second = items[1].case_id;
drafts[first] = {{
  reviewer: "Old Reviewer",
  reviewed_at: "2026-05-10",
  decision: "confirm_diagnostic_issue",
  confirmed_root_causes: ["primary_evidence_gap"],
  confirmed_follow_up_actions: ["needs_additional_evidence_capture"],
  rationale: "old ready draft"
}};
drafts[second] = {{
  reviewer: "Stale Reviewer",
  reviewed_at: "2026-05-10",
  decision: "confirm_diagnostic_issue",
  confirmed_root_causes: ["primary_evidence_gap"],
  confirmed_follow_up_actions: ["needs_additional_evidence_capture"],
  rationale: "stale ready draft"
}};
const importFile = JSON.stringify({{
  scope: "filled visual manual review workbench export",
  advisory_packet_only: false,
  contains_completed_manual_decisions: true,
  summary: {{ export_policy: "ready_human_drafts_only" }},
  workbench_items: [
    {{
      case_id: first,
      reviewer_input_template: {{
        reviewer: "Human Reviewer",
        reviewed_at: "2026-05-13",
        decision: "confirm_diagnostic_issue",
        confirmed_root_causes: ["primary_evidence_gap"],
        confirmed_follow_up_actions: ["needs_additional_evidence_capture"],
        rationale: "=SUM(1,1)"
      }}
    }}
  ]
}});
const importObject = JSON.parse(importFile);
importObject.workbench_fingerprint = workbenchFingerprint;
importObject.summary.exported_case_ids = [first];
let wrongFingerprintRejected = false;
try {{
  const wrong = {{ ...importObject, workbench_fingerprint: "wrong-fingerprint" }};
  parseReviewImport(JSON.stringify(wrong), "filled_manual_review_workbench.json");
}} catch (error) {{
  wrongFingerprintRejected = true;
}}
if (!wrongFingerprintRejected) {{
  throw new Error("filled JSON with a wrong workbench fingerprint was accepted");
}}
const records = parseReviewImport(JSON.stringify(importObject), "filled_manual_review_workbench.json");
const summary = applyReviewImport(records);
if (summary.imported_rows !== 1 || summary.cleared_draft_rows !== 2) {{
  throw new Error("import did not replace stale drafts");
}}
if (drafts[second]) {{
  throw new Error("stale draft survived replacement import");
}}
const exported = buildFilledWorkbench();
if (exported.workbench_items.length !== 1 || exported.summary.exported_case_ids[0] !== first) {{
  throw new Error("exported case ids did not reflect replaced import");
}}
const directCells = ["=SUM(1,1)", "+SUM(1,1)", "-SUM(1,1)", "@HYPERLINK(x)"].map(csvEscape);
if (!directCells.every(cell => cell.includes("'"))) {{
  throw new Error("CSV formula-like cell was not escaped");
}}
const csv = csvForWorkbench(exported);
if (!csv.includes("'=SUM(1,1)")) {{
  throw new Error("exported CSV did not contain escaped rationale");
}}
let csvRejected = false;
try {{
  parseReviewImport("case_id,reviewer\\\\n" + first + ",Reviewer", "manual.csv");
}} catch (error) {{
  csvRejected = true;
}}
if (!csvRejected) {{
  throw new Error("CSV import was not rejected");
}}
const advisory = JSON.stringify({{
  scope: "safe visual workbench AI suggestion import",
  human_confirmation_required: true,
  reviewer_input_template_written: false,
  guardrails: {{ advisory_draft_only: true }},
  workbench_items: [{{
    case_id: second,
    ai_review_suggestion: {{
      ai_suggestion: true,
      human_confirmation_required: true,
      decision: "confirm_diagnostic_issue",
      rationale: "advisory only"
    }}
  }}]
}});
const suggestionSummary = applyReviewImport(parseReviewImport(advisory, "suggestions.json"));
if (suggestionSummary.suggestion_rows !== 1 || suggestionSummary.cleared_draft_rows !== 0) {{
  throw new Error("AI suggestion import should not clear or create manual drafts");
}}
`;

const inertElement = () => ({{
  textContent: "",
  innerHTML: "",
  className: "",
  value: "",
  checked: false,
  appendChild() {{}},
  remove() {{}},
  addEventListener() {{}},
  setAttribute() {{}},
  querySelectorAll() {{ return []; }},
}});

const context = {{
  console,
  window: {{
    localStorage: {{
      getItem(key) {{ return store.has(key) ? store.get(key) : null; }},
      setItem(key, value) {{ store.set(key, String(value)); }},
    }},
    alert() {{}},
    confirm() {{ return true; }},
  }},
  document: {{
    documentElement: {{}},
    getElementById(id) {{
      if (id === "workbench-data") return {{ textContent: payloadText }};
      return inertElement();
    }},
    querySelectorAll() {{ return []; }},
    createElement() {{ return inertElement(); }},
    body: inertElement(),
  }},
  URL: {{
    createObjectURL() {{ return "blob:test"; }},
    revokeObjectURL() {{}},
  }},
  Blob: function Blob() {{}},
  FileReader: function FileReader() {{}},
}};

vm.runInNewContext(script, context, {{ timeout: 5000 }});
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = Path(tmpdir) / "workbench_import_governance_check.js"
            script_path.write_text(test_script, encoding="utf-8")
            result = subprocess.run(
                [node, str(script_path)],
                cwd=Path.cwd(),
                text=True,
                capture_output=True,
                timeout=10,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_generated_html_has_responsive_layout_guards(self):
        html = read_html()
        app_shell = css_block(html, ".app-shell")
        sidebar = css_block(html, ".sidebar")
        main = css_block(html, ".main")
        workspace = css_block(html, ".workspace")
        panel = css_block(html, ".panel")
        case_list = css_block(html, ".case-list")
        detail_body = css_block(html, ".detail-body")
        narrow_layout = css_media_block(html, "@media (max-width: 1180px)")

        self.assertIn("@media (max-width: 720px)", html)
        self.assertIn("html {\n      height: 100%;", html)
        self.assertIn("body {\n      margin: 0;\n      min-height: 100vh;\n      height: 100vh;", html)
        self.assertIn("display: grid;", app_shell)
        self.assertIn("grid-template-rows: minmax(0, 1fr);", app_shell)
        self.assertIn("height: 100vh;", app_shell)
        self.assertIn("overflow: hidden;", app_shell)
        self.assertIn("height: 100%;", sidebar)
        self.assertIn("max-height: 100vh;", sidebar)
        self.assertIn("overflow: auto;", sidebar)
        self.assertIn("height: 100%;", main)
        self.assertIn("max-height: 100vh;", main)
        self.assertIn("overflow: hidden;", main)
        self.assertIn("height: 100%;", workspace)
        self.assertIn("overflow: hidden;", workspace)
        self.assertIn("height: 100%;", panel)
        self.assertIn("overflow: hidden;", panel)
        self.assertIn(".queue-panel", html)
        self.assertIn(".detail-panel", html)
        self.assertIn('class="panel queue-panel"', html)
        self.assertIn('class="panel detail-panel"', html)
        self.assertIn("grid-template-rows: auto auto auto minmax(0, 1fr)", html)
        self.assertIn("grid-template-rows: auto auto minmax(0, 1fr)", html)
        self.assertIn("min-height: 0;", case_list)
        self.assertIn("max-height: none;", case_list)
        self.assertIn("overflow: auto;", case_list)
        self.assertIn("min-height: 0;", detail_body)
        self.assertIn("max-height: none;", detail_body)
        self.assertIn("overflow: auto;", detail_body)
        self.assertNotIn("calc(100vh", case_list)
        self.assertNotIn("calc(100vh", detail_body)
        self.assertIn("body {\n        height: auto;", html)
        self.assertIn("height: auto;", narrow_layout)
        self.assertIn("max-height: none;", narrow_layout)
        self.assertIn("overflow: visible;", narrow_layout)
        self.assertIn(".queue-panel, .detail-panel", narrow_layout)
        self.assertIn(".case-list, .detail-body", narrow_layout)
        self.assertIn("overflow-wrap: anywhere", html)
        self.assertIn("letter-spacing: 0", html)
        self.assertIn("border-radius: var(--radius)", html)
        self.assertIn(".language-select", html)
        self.assertIn(".language-control", html)
        self.assertIn(".decision-workflow", html)
        self.assertIn("@media (max-width: 960px)", html)
        self.assertIn("grid-template-columns: minmax(96px, 0.28fr) minmax(0, 1fr) minmax(64px, max-content)", html)
        self.assertIn(".pipeline-step .pill", html)
        self.assertIn("justify-self: start", html)


if __name__ == "__main__":
    unittest.main()
