"""Build a safe AI-suggestion import file for the visual workbench.

The output keeps AI-assisted prefill content under ai_review_suggestion instead
of reviewer_input_template, so the visual workbench can show it as reference
material without turning it into a completed manual decision. It does not
modify decision schemas, retrieval, rerank, prompts, anchors, risk rules, eval
cases, hidden seeds, or the RAG main flow.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


VERSION = "0.4.7.8.13"

DEFAULT_INPUT_PATH = Path("tests/manual_review_prefill_high_confidence_12_v2.json")
DEFAULT_OUTPUT_PATH = Path("tests/manual_review_ai_suggestion_prefill_high_confidence_12_v2.json")

SUGGESTION_FIELDS = [
    "decision",
    "confirmed_root_causes",
    "rejected_root_causes",
    "confirmed_follow_up_actions",
    "proposed_change_targets",
    "fixture_candidate",
    "rationale",
    "notes",
]


def load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def build_safe_suggestion(input_data: dict[str, Any]) -> dict[str, Any]:
    items = []
    for item in input_data.get("workbench_items") or []:
        if not isinstance(item, dict):
            continue
        template = item.get("reviewer_input_template")
        if not isinstance(template, dict):
            continue
        suggestion = {
            field: template.get(field)
            for field in SUGGESTION_FIELDS
            if field in template
        }
        suggestion.update(
            {
                "ai_suggestion": True,
                "suggestion_type": "ai_assisted_manual_review_prefill",
                "human_confirmation_required": True,
                "source_reviewer_label": template.get("reviewer", ""),
                "source_reviewed_at": template.get("reviewed_at", ""),
            }
        )
        items.append(
            {
                "case_id": item.get("case_id"),
                "prefill_scope": item.get("prefill_scope"),
                "prescreen_confidence": item.get("prescreen_confidence"),
                "prescreen_score": item.get("prescreen_score"),
                "risk_level": item.get("risk_level"),
                "question": item.get("question"),
                "ai_review_suggestion": suggestion,
            }
        )

    return {
        "version": VERSION,
        "scope": "safe visual workbench AI suggestion import",
        "source_prefill_version": input_data.get("version"),
        "human_confirmation_required": True,
        "reviewer_input_template_written": False,
        "summary": {
            "suggestion_items": len(items),
        },
        "guardrails": {
            **(input_data.get("guardrails") if isinstance(input_data.get("guardrails"), dict) else {}),
            "advisory_draft_only": True,
            "human_confirmation_required": True,
            "reviewer_decision_import": "disallowed_without_human_copy",
        },
        "workbench_items": items,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build safe AI suggestions for the manual review visual workbench.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data = load_json(args.input)
    output = build_safe_suggestion(data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"AI suggestion prefill built: {output['summary']['suggestion_items']} suggestions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
