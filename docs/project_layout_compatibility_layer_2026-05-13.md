# Project Layout Compatibility Layer - 2026-05-13

## Purpose

This maintenance pass adds a small compatibility layer for future directory
cleanup. It does not move files and does not change default tool behavior.

Current authoritative paths remain:

- generated reports: `tests/*.json`, `tests/*.csv`, and related existing
  artifacts;
- tool entrypoints: root-level `tools/*.py`;
- visual workbench HTML: `tools/manual_review_visual_workbench/index.html`.

## Added Module

`tools/_shared/layout.py` provides:

- `project_root()`: finds the repository root without assuming a fixed tool
  depth;
- `legacy_report_path(name)`: returns the current authoritative
  `tests/<name>` path;
- `report_scaffold_path(group, name)`: returns a future
  `reports/<group>/<name>` mirror path;
- `resolve_report_pair(path, group)`: reports both legacy and future locations
  while selecting the legacy path;
- `resolve_existing_report(..., allow_future_fallback=True)`: supports explicit
  future fallback only when requested and only if the legacy file is absent;
- `compatibility_contract()`: serializes the current non-migrating contract.

## Health Check Coverage

`tools/run_project_health_check.py` now reports `layout_compatibility`:

- legacy `tests/*.json` paths remain authoritative;
- future `reports/<group>/` paths are mirrors/fallback targets only;
- automatic migration is disabled;
- tool entrypoint migration is disabled.

It also reports `layout_helper_pilot_defaults` for low-risk pilot tools:

- `tools/check_evidence_alignment.py`;
- `tools/check_evidence_coverage.py`;
- `tools/check_legal_functional_type_config.py`;
- `tools/build_evidence_manual_review_dataset.py`;
- `tools/build_evidence_root_cause_action_plan.py`;
- `tools/build_evidence_action_series_baseline.py`;
- `tools/draft_evidence_coverage_gates.py`.
- `tools/build_manual_review_visual_workbench.py`;
- `tools/import_manual_review_workbench.py`;
- `tools/build_manual_review_export_pipeline_dry_run.py`;
- `tools/build_pilot_manual_review_round1_support.py`;
- `tools/build_mobile_pilot_review_decision_aid.py`.

These tools now express generated-report defaults through `legacy_report_path()`
where applicable. Their defaults still resolve to `tests/*.json`.

## Third-Batch Manual Review Pilot

The third batch covers manual review and workbench tooling. It only changes how
direct `tests/<report>.json` report defaults are expressed in code.

Deliberately unchanged defaults include:

- visual workbench HTML output: `tools/manual_review_visual_workbench/index.html`;
- Markdown documentation outputs under `docs/`;
- CSV workbench input paths;
- decision schema and proposed schema JSON paths;
- `tests/rag_eval_cases.json` and other eval-case data;
- `config/scenario_registry.json`;
- nested dry-run artifact directory:
  `tests/manual_review_export_pipeline_dry_run_artifacts`.

`tools/run_project_health_check.py` now also checks that the nested dry-run
artifact directory remains an isolated `tests/` artifact directory and is not
treated as a `reports/` migration target.

## Boundaries

This layer must not be used to silently change where tools read or write.

Any future migration must first add:

- explicit CLI flags or dual-output behavior;
- compatibility readers for both legacy and future paths;
- unit tests for every migrated consumer;
- updated docs and health-check expectations.

No hidden seed, anchor, rerank, prompt, risk supplement, term preservation,
scenario registry, eval case, `rag_query`, backend, Qdrant, or LLM behavior is
changed by this maintenance pass.

## Validation

```powershell
.\venv\Scripts\python.exe -m py_compile tools\_shared\layout.py tools\run_project_health_check.py tests\test_layout_compatibility.py tests\test_project_health_check.py
.\venv\Scripts\python.exe -m py_compile tools\check_evidence_alignment.py tools\check_evidence_coverage.py tools\check_legal_functional_type_config.py
.\venv\Scripts\python.exe -m unittest tests.test_layout_compatibility tests.test_project_health_check tests.test_evidence_alignment tests.test_evidence_coverage tests.test_legal_functional_type_config
.\venv\Scripts\python.exe -m unittest tests.test_manual_review_visual_workbench tests.test_manual_review_workbench_import tests.test_manual_review_export_pipeline_dry_run tests.test_pilot_manual_review_round1_support tests.test_mobile_pilot_review_decision_aid tests.test_project_health_check
.\venv\Scripts\python.exe tools\run_project_health_check.py --output tests\project_health_check_report.json --fail-on-error
```
