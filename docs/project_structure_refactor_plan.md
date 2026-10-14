# Project Structure Refactor Plan

## Purpose

This maintenance pass prepares a safer project structure without changing
runtime behavior. It adds directory scaffolds and documentation so later cleanup
can happen gradually instead of moving many files at once.

Follow-up maintenance added `tools/_shared/layout.py`, a compatibility layer
that can calculate future `reports/<group>/` mirror paths while still selecting
legacy `tests/*.json` paths as authoritative.

The project is not off direction: the core `src/` code remains comparatively
small. The visible bloat mainly comes from generated reports and many offline
governance tools living flat under `tests/` and `tools/`.

## Current Findings

- `tests/` contains both real unit tests and generated JSON/CSV/Markdown
  artifacts. Several reports are multi-megabyte eval or audit outputs.
- `tools/` contains many offline scripts in one flat directory. Some scripts are
  entrypoints; some are diagnostics; some build manual-review workbench assets.
- Many tools and docs still hard-code paths such as `tests/*.json` and
  `tools/manual_review_visual_workbench/index.html`.
- Some tools compute repository root with `Path(__file__).resolve().parents[1]`,
  which assumes root-level `tools/*.py` entrypoints.
- `reports/` previously existed for exported risk reports. The new subfolders
  are only a future grouping scaffold and do not replace that convention yet.
- Moving files immediately would risk breaking existing reports, tests, and
  documentation references.

## Scaffold Added

Future report groups:

```text
reports/
  eval/
  audits/
  manual_review/
  dry_run/
```

Future tool groups:

```text
tools/
  _shared/
  eval/
  evidence_diagnostics/
  manual_review/
    workbench/
    pilot/
  ops/
  ingestion/
```

Documentation support:

```text
docs/
  indexes/
  archive/
```

## Non-Goals

This pass does not:

- move or delete existing files;
- change default output paths;
- change imports or public tool entrypoints;
- change RAG retrieval, rerank, prompt, anchor, risk supplement, term
  preservation, scenario registry, eval cases, or hidden seeds;
- connect any diagnostic tool to `rag_query`;
- mark the new layout as canonical.

## Migration Phases

1. Scaffold and document the target shape. Existing paths stay authoritative.
2. Extract small shared helpers into `tools/_shared/` while keeping old
   entrypoints. Current status: `layout.py` exists for path compatibility only.
3. Add optional dual-output support for high-volume generated reports.
4. Move generated artifacts from `tests/` to `reports/` only after readers,
   tests, docs, and health checks support both old and new locations.
5. Archive old version-specific docs only after the roadmap and final-report
   guide preserve their useful summary.

## Guardrails

- Prefer compatibility wrappers over path-breaking moves.
- Keep unit tests under `tests/test_*.py`.
- Treat existing `tests/*.json` reports as canonical until a later migration
  explicitly changes that contract.
- Any future cleanup must pass `tools/run_project_health_check.py`.
- Large cleanup should be split by domain: reports first, tools second, docs
  last.
