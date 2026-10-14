import argparse
import re
from pathlib import Path


DEFAULT_PLAN = Path("docs/rule_convergence_plan_v0.4.5.17.md")
SCENARIO_HEADING_RE = re.compile(r"^### `([a-z][a-z0-9_]*)`$", re.MULTILINE)
SCENARIO_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")


REQUIRED_SECTIONS = [
    "## Scenario ID 命名规范",
    "## 职责边界",
    "## 候选场景",
    "## 迁移顺序",
    "## 不做事项",
    "## 发布门禁",
]

REQUIRED_SCENARIO_FIELDS = [
    "现状信号：",
    "当前涉及规则：",
    "收敛设计：",
    "验证命令：",
]


def scenario_blocks(plan_text: str) -> dict[str, str]:
    matches = list(SCENARIO_HEADING_RE.finditer(plan_text))
    blocks: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(plan_text)
        blocks[match.group(1)] = plan_text[start:end]
    return blocks


def validate_plan_text(plan_text: str) -> list[str]:
    errors: list[str] = []
    for section in REQUIRED_SECTIONS:
        if section not in plan_text:
            errors.append(f"missing section: {section}")

    scenarios = scenario_blocks(plan_text)
    if not 3 <= len(scenarios) <= 5:
        errors.append(f"scenario count must be between 3 and 5, got {len(scenarios)}")

    for scenario_id, block in scenarios.items():
        if not SCENARIO_ID_RE.match(scenario_id):
            errors.append(f"invalid scenario_id: {scenario_id}")
        for field in REQUIRED_SCENARIO_FIELDS:
            if field not in block:
                errors.append(f"{scenario_id} missing field: {field}")
        if "python tools/run_rag_eval.py --check-risk" not in block:
            errors.append(f"{scenario_id} missing targeted eval command")
        if "python tools/check_rag_stability_report.py" not in block:
            errors.append(f"{scenario_id} missing stability gate command")
        if "python tools/audit_rule_debt.py" not in block:
            errors.append(f"{scenario_id} missing rule debt audit command")

    if "不修改 `src/rag/retriever.py`" not in plan_text:
        errors.append("plan must explicitly state no retriever.py changes")

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the v0.4.5.17 rule convergence plan structure.")
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors = validate_plan_text(args.plan.read_text(encoding="utf-8"))
    if errors:
        print("Rule convergence plan check failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Rule convergence plan check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
