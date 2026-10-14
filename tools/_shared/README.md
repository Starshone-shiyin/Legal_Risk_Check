# Shared Tooling Scaffold

This package is reserved for small shared helpers used by offline project tools.

Current status: `layout.py` provides path-compatibility helpers for future
directory cleanup. Existing root-level tools remain the public entrypoints, and
existing `tests/*.json` reports remain authoritative.

Available helper:

- `layout.py`: resolves the project root without assuming the caller depth,
  maps legacy `tests/<report>.json` files to future `reports/<group>/` mirror
  paths, and exposes a non-migrating compatibility contract.

Candidate helpers for a later phase:

- JSON read/write helpers with `utf-8-sig` input compatibility.
- Text normalization and compact display helpers.
- Source/evidence metadata extraction helpers.
- Recursive forbidden-key scans for advisory/manual-review boundary checks.
- Shared guardrail constants for offline diagnostics.

Compatibility rule: future shared helpers should be introduced behind existing
tool entrypoints first. Do not move tool modules, change default output paths,
or switch report readers until tests, docs, and health checks cover the new
paths.
