# Controlled Online Search

The project now has a guarded online-search foundation for facts that may change
after the local legal corpus was built. Local RAG remains the default source for
statutes and stable legal concepts.

## Runtime Modes

`AskRequest.online_search_mode` accepts:

- `off`: no web request is made.
- `auto`: search only when the question contains a current-fact signal such as
  latest, current, effective, announcement, regulatory action, or market event.
- `force`: execute the search plan even without a current-fact signal.

`/ask` defaults to `auto`; ordinary legal-concept questions therefore remain
local-only because they do not satisfy the current-fact trigger.

The environment switch is also required:

```text
EXTERNAL_RISK_WEB_SEARCH_ENABLED=true
EXTERNAL_RISK_WEB_SEARCH_PROVIDER=tavily
EXTERNAL_RISK_WEB_SEARCH_TIMEOUT_SECONDS=8
EXTERNAL_RISK_WEB_SEARCH_MAX_RESULTS=5
```

The default is disabled. For a stable production-like demonstration, configure
Tavily:

```text
EXTERNAL_RISK_WEB_SEARCH_ENABLED=true
EXTERNAL_RISK_WEB_SEARCH_PROVIDER=tavily
EXTERNAL_RISK_WEB_SEARCH_API_KEY=your_tavily_key
```

The startup script supports `-EnableWebSearch` and `-DisableWebSearch`. A failed
or disabled provider returns an empty result set and the normal local RAG answer
path continues.

`bing_html` and `duckduckgo_html` remain available only as explicit experimental
fallbacks. They should not be the primary provider because public result pages
can be affected by bot challenges, locale drift, or unrelated trending results.

## HTTP API

`POST /external-risk/web-search`

```json
{
  "question": "latest data export regulatory policy",
  "mode": "auto",
  "domain": "legal",
  "max_results": 5
}
```

The response includes the search plan, trigger, query, allowed domains, source
tier, trust score, URL, snippet, and fetch timestamp. Legal and regulatory
intent is restricted to configured official government domains. Market and
company intent prefers exchanges, disclosure platforms, and configured trusted
media domains.

`GET /external-risk/web-search/status` reports whether the provider is enabled
and whether a live request has actually been made.

## Evidence Boundary

Search results are tagged as `web_result` and `external_web_evidence`. They are
not treated as statutory text. The URL is reclassified at the evidence boundary
so a provider cannot raise its own trust score. Current legal conclusions still
require an official source or a matching local statute, and online evidence
always keeps `requires_human_review` enabled.

The search provider currently retrieves result pages only. It does not execute
arbitrary page scripts, follow untrusted instructions, or automatically persist
web pages into the legal Qdrant collection.
