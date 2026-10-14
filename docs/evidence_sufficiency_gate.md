# Evidence Sufficiency Gate

## Purpose

The Evidence Sufficiency Gate (ESG) is a deterministic post-retrieval controller.
It is not an answer-accuracy score. It measures whether selected evidence is fit
to support a legal answer and determines the next route: answer with evidence,
controlled web supplementation, or human review.

## Feature Vector

For selected evidence set `E`, with target evidence count `K' = min(max(K,1),3)`:

```text
C = min(1, |E| / K')                         # coverage
Q = cited_items / |E|                         # citation ratio
A = authoritative_items / |E|                 # authority ratio
D = min(1, unique_sources / min(K', 2))        # source diversity
L = 1 if legal query has local primary law else 0
```

```text
ESG = 0.25*C + 0.25*Q + 0.20*A + 0.10*D + 0.20*L
```

For a non-legal external-fact query, `L=1`: a trusted official web source can
support the fact. For a legal query, web sources remain supplementary and cannot
replace a local primary law source.

## Routing Policy

| Condition | Route |
|---|---|
| `ESG >= 0.78` and no evidence gaps | `answer_with_evidence` |
| Legal query lacks local primary-law evidence | `web_supplement` |
| Other incomplete or weak evidence | `human_review` |

## Integration

1. Dense, sparse, anchor, and rerank stages select legal evidence.
2. ESG creates a structured `evidence_sufficiency` report.
3. In `auto` mode, a legal retrieval gap can trigger controlled official-domain
   web search. If web evidence is added, RAG regenerates the answer once.
4. The API returns ESG fields so the UI, evaluator, and report can distinguish
   retrieval confidence from evidence sufficiency.

## Evaluation Claims

Report ESG as a routing and governance mechanism, not as legal correctness.
Use the unit cases in `tests/test_evidence_sufficiency.py` and retrieval cases to
report: gate pass rate, web-supplement rate, human-review rate, and the share of
legal answers with at least one local primary-law source.
