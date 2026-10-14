import unittest
from pathlib import Path

from tools.check_rule_convergence_plan import scenario_blocks, validate_plan_text


VALID_PLAN = """
## Scenario ID 命名规范
## 职责边界
## 候选场景

### `pipl_children_consent`

现状信号：
当前涉及规则：
收敛设计：
验证命令：
```bash
python tools/run_rag_eval.py --check-risk --output tests/targeted_eval_report.json --case-id risk_children_data_001
python tools/check_rag_stability_report.py --report tests/rag_stability_report.json
python tools/audit_rule_debt.py --anchor-rules config/rag_anchor_rules.json --risk-rules config/risk_payload_supplement_rules.json --stability-report tests/rag_stability_report.json --json-output tests/rule_debt_report.json --md-output docs/rule_debt_report_v0.4.5.16.md
```

### `vat_false_invoice_deduction`

现状信号：
当前涉及规则：
收敛设计：
验证命令：
```bash
python tools/run_rag_eval.py --check-risk --output tests/targeted_eval_report.json --case-id risk_vat_false_invoice_001
python tools/check_rag_stability_report.py --report tests/rag_stability_report.json
python tools/audit_rule_debt.py --anchor-rules config/rag_anchor_rules.json --risk-rules config/risk_payload_supplement_rules.json --stability-report tests/rag_stability_report.json --json-output tests/rule_debt_report.json --md-output docs/rule_debt_report_v0.4.5.16.md
```

### `trade_secret_customer_list_leak`

现状信号：
当前涉及规则：
收敛设计：
验证命令：
```bash
python tools/run_rag_eval.py --check-risk --output tests/targeted_eval_report.json --case-id risk_employee_data_export_001
python tools/check_rag_stability_report.py --report tests/rag_stability_report.json
python tools/audit_rule_debt.py --anchor-rules config/rag_anchor_rules.json --risk-rules config/risk_payload_supplement_rules.json --stability-report tests/rag_stability_report.json --json-output tests/rule_debt_report.json --md-output docs/rule_debt_report_v0.4.5.16.md
```

## 迁移顺序
## 不做事项
不修改 `src/rag/retriever.py`
## 发布门禁
"""


class RuleConvergencePlanTest(unittest.TestCase):
    def test_validate_plan_text_accepts_valid_plan(self):
        self.assertEqual(validate_plan_text(VALID_PLAN), [])

    def test_validate_plan_text_rejects_missing_sections(self):
        errors = validate_plan_text("### `pipl_children_consent`\n")

        self.assertTrue(any("missing section" in error for error in errors))

    def test_validate_plan_text_rejects_too_few_scenarios(self):
        plan = VALID_PLAN.replace("### `vat_false_invoice_deduction`", "#### `vat_false_invoice_deduction`")
        plan = plan.replace("### `trade_secret_customer_list_leak`", "#### `trade_secret_customer_list_leak`")

        errors = validate_plan_text(plan)

        self.assertTrue(any("scenario count" in error for error in errors))

    def test_scenario_blocks_extracts_scenario_ids(self):
        blocks = scenario_blocks(VALID_PLAN)

        self.assertIn("pipl_children_consent", blocks)
        self.assertIn("vat_false_invoice_deduction", blocks)

    def test_repository_plan_passes(self):
        plan_text = Path("docs/rule_convergence_plan_v0.4.5.17.md").read_text(encoding="utf-8")

        self.assertEqual(validate_plan_text(plan_text), [])


if __name__ == "__main__":
    unittest.main()
