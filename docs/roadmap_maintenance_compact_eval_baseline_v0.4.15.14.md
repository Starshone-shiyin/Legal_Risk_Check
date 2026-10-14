# v0.4.15.14 Roadmap Maintenance & Compact Eval Baseline

## Scope

This version converts `docs/project_review_and_roadmap.md` from a long
per-version ledger into a current-state roadmap. The previous long version is
preserved as `docs/archive/project_review_and_roadmap_v0.4.15.13_snapshot.md`.

It also runs a compact full RAG eval baseline using the opt-in
`--compact-report` profile introduced in v0.4.15.13.

## Result

- Roadmap now keeps project positioning, current capabilities, phase summary,
  current governance baseline, current risks, recommended next work, validation
  strategy, and "not recommended now" boundaries.
- Detailed per-version history remains in `changelog.md`.
- Final report wording remains in `docs/final_report_version_guide.md`.
- Historical roadmap detail is retained in the archive snapshot.
- Compact full RAG eval baseline:
  - report: `tests/post_roadmap_maintenance_compact_full_rag_eval_v0.4.15.14_report.json`
  - result: 60/60 passed
  - retrieval stages: `{"PASS": 60}`

## Boundary

- No hidden seed, anchor, prompt, rerank, risk supplement, term preservation,
  scenario registry, fixture, eval case, Qdrant, or retriever change.
- No new gate chain.
- This version is roadmap maintenance plus a lightweight eval baseline, not a
  runtime behavior change.

## Verification

- `.\venv\Scripts\python.exe tools\run_rag_eval.py --cases tests\rag_eval_cases.json --output tests\post_roadmap_maintenance_compact_full_rag_eval_v0.4.15.14_report.json --check-risk --compact-report`
