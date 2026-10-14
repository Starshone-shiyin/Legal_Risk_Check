# Skill Module Offline Acceptance

## Scope

This document defines an offline acceptance boundary for the proposed Skill
module. It deliberately validates saved JSON contracts only; it does not claim
that a real HTTP API, model provider, Qdrant collection, or execution service is
already available.

The judge command is:

```text
venv\Scripts\python.exe tools\judge_skill_module.py --skill-api <skill-api.json> --runtime <runtime-validation.json> --output <judge-report.json>
```

It returns exit code `0` for `accepted` and `1` for `needs_revision`.

## Fixed-Node Workflow

The current version permits only the following node types:

| Node type | Role |
|---|---|
| `document_extract` | Normalize an already-authorized material extraction result. |
| `retrieve` | Retrieve legal evidence through the service boundary. |
| `evidence_gate` | Route on evidence sufficiency. |
| `web_supplement` | Request controlled online supplementation through the existing service boundary. |
| `risk_analysis` | Select the bounded legal, compliance, or market analysis focus. |
| `human_review` | Record a review handoff rather than making an autonomous approval. |
| `report_output` | Return Markdown or JSON through the public result contract. |

The graph must have unique non-empty node IDs, references only declared nodes,
and be acyclic. Node configuration is an object. Common `enabled` and
`timeout_ms` fields are type-checked; retrieval `top_k`, ESG `threshold`, and
output format have bounded validation.

## API and Runtime Evidence

The `skill-api-v1` JSON must declare all CRUD operations as endpoint contracts:
`GET list`, `POST create`, `GET get`, `PATCH update`, and `DELETE delete`.
It also declares protected built-in examples and a frontend boundary.

The `skill-runtime-validation-v1` JSON is evidence from the implementation
line. It must show passed configuration rejection tests, every CRUD operation,
built-in example protection, frontend-boundary validation, and a run plan. The
run plan must name every declared node exactly once and expose the same ordered
execution list. The judge then verifies its graph is acyclic.

Built-in examples are immutable templates: each sets `is_builtin: true`, and
the runtime report must list it in
`protected_example_ids`.

## Frontend Boundary

The frontend may call only public list/create/get/update/delete/run/read-run
operations. It must explicitly forbid direct node execution, direct model calls,
direct vector-store access, and writes to built-in examples. A passed runtime
validation must also state `no_direct_provider_access: true`.

This prevents the visual editor from becoming a hidden execution or data-access
channel. Provider credentials, retrieval internals, and persistence remain on
the service side.

## Third-Layer Reservation

This release fixes the node vocabulary and requires a directed acyclic plan. It
does **not** yet accept arbitrary third-layer composition, custom code nodes,
loops, side effects, provider selection, or direct tool invocation.

The future third layer may introduce guarded composition only after it has a
versioned node registry, permission model, typed input/output contracts,
resource limits, audit trail, deterministic replay semantics, and its own
security review. Until then, any node outside the whitelist is correctly judged
as `needs_revision`.

## Minimal Fixture Shape

```json
{
  "schema_version": "skill-api-v1",
  "nodes": [{"node_id": "retrieve", "node_type": "retrieve", "parameters": {}}],
  "edges": [],
  "crud": {"list": {"method": "GET", "path": "/skills"}},
  "builtin_examples": [{"skill_id": "builtin-legal-baseline", "is_builtin": true}],
  "frontend_boundary": {
    "allowed_operations": ["list"],
    "forbidden_operations": ["execute_node", "direct_model_call", "direct_vectorstore_access", "write_builtin_example"],
    "no_direct_provider_access": true
  }
}
```

The fixture is illustrative only. For acceptance, all five CRUD entries and all
runtime-validation fields described above are required.
