const tabNames = {
    dashboard: "首页驾驶舱",
    lifecycle: "生命周期风控",
    internal: "内部风控",
    market: "市场行情",
    supply: "供应链地图",
    legal: "法律风控",
    skills: "我的技能",
    settings: "系统配置",
};

const riskLabels = {
    low: "低",
    med: "中",
    high: "高",
    crit: "严重",
    pending: "待评估",
};

const navItems = document.querySelectorAll(".nav-item[data-tab]");
const breadcrumb = document.getElementById("breadcrumb-current");
const DEFAULT_BACKEND_BASE_URL = "http://127.0.0.1:8000";
const FALLBACK_BACKEND_BASE_URL = "http://127.0.0.1:8003";
const LEGACY_BACKEND_BASE_URL = "http://127.0.0.1:8002";
const LOCAL_BACKEND_BASE_URLS = [DEFAULT_BACKEND_BASE_URL, FALLBACK_BACKEND_BASE_URL, LEGACY_BACKEND_BASE_URL];
const LOCAL_BACKEND_FAILOVER_TIMEOUT_MS = 5000;
const LEGAL_COLLECTION_NAME = "legal_knowledge_staging_20260811";
const BACKEND_BASE_URL_KEY = "riskflow.backendBaseUrl";
const DISMISSED_NAV_BADGES_KEY = "riskflow.dismissedNavBadges";
const SIDEBAR_COLLAPSED_KEY = "riskflow.sidebarCollapsed";
const LEGAL_THREADS_KEY = "riskflow.legalThreads";
const LEGAL_DOCUMENT_SELECTION_KEY = "riskflow.legalDocumentSelection";
const NEW_LEGAL_THREAD_TITLE = "新对话";
const backendState = {
    baseUrl: getBackendBaseUrl(),
    connected: false,
    product: {},
    externalRisk: null,
    internalRisk: null,
    riskIntake: null,
};
const runtimeSettingsState = {
    loaded: false,
    feeds: [],
};
const LLM_CHANNEL_PRESETS = {
    openai: { provider: "openai_compatible", baseUrl: "https://api.openai.com/v1", model: "gpt-5.6-luna" },
    deepseek: { provider: "openai_compatible", baseUrl: "https://api.deepseek.com/v1", model: "deepseek-v4-flash" },
    qwen: { provider: "openai_compatible", baseUrl: "https://dashscope.aliyuncs.com/compatible-mode/v1", model: "qwen3.8-max" },
    zhipu: { provider: "openai_compatible", baseUrl: "https://open.bigmodel.cn/api/paas/v4", model: "glm-5.2" },
    kimi: { provider: "openai_compatible", baseUrl: "https://api.moonshot.cn/v1", model: "kimi-k3" },
    siliconflow: { provider: "openai_compatible", baseUrl: "https://api.siliconflow.cn/v1", model: "deepseek-ai/DeepSeek-V4-Flash" },
    openrouter: { provider: "openai_compatible", baseUrl: "https://openrouter.ai/api/v1", model: "openai/gpt-5.6-luna" },
    ollama: { provider: "openai_compatible", baseUrl: "http://127.0.0.1:11434/v1", model: "qwen3.5:9b" },
    anthropic: { provider: "anthropic_messages", baseUrl: "https://api.anthropic.com", model: "claude-sonnet-5" },
    gemini: { provider: "gemini_generate_content", baseUrl: "https://generativelanguage.googleapis.com", model: "gemini-3.7-flash" },
};
const skillState = {
    loaded: false,
    loading: false,
    serviceAvailable: false,
    nodeTypesAvailable: false,
    skills: [],
    nodeTypes: [],
    selectedId: null,
    editingId: null,
    draftNodes: [],
};
const MAX_SKILL_NODES = 6;
const quoteState = {
    symbol: "sh000001",
    interval: "intraday",
    refreshTimer: null,
    refreshMs: 15000,
    requestId: 0,
    manualUntil: 0,
    points: [],
    windowSize: 80,
    windowEnd: null,
    dragStartX: null,
    dragStartWindowEnd: null,
};
let legalThreads = loadLegalThreads();
let currentLegalThreadId = legalThreads[0]?.id || createLegalThreadId();
let selectedLegalDocumentIds = loadSelectedLegalDocumentIds();
let pendingLegalEvidenceContext = null;
let documentRefreshTimer = null;
let renderedLegalDocumentTaskSignature = "";
let chatAttachmentTaskStates = new Map();
let chatAttachmentErrors = [];

navItems.forEach((item) => {
    item.addEventListener("click", () => switchTab(item.dataset.tab, item));
});

document.getElementById("sidebar-toggle")?.addEventListener("click", () => {
    const collapsed = document.body.classList.toggle("sidebar-collapsed");
    try {
        window.localStorage.setItem(SIDEBAR_COLLAPSED_KEY, collapsed ? "1" : "0");
    } catch {
        // Visual state still updates if storage is unavailable.
    }
});

function switchTab(tabId, navElement) {
    navItems.forEach((item) => item.classList.remove("active"));
    navElement.classList.add("active");
    document.querySelectorAll(".view").forEach((view) => view.classList.remove("active"));
    document.getElementById(`view-${tabId}`).classList.add("active");
    breadcrumb.textContent = tabNames[tabId];
    clearNavBadge(tabId);
    if (tabId === "legal") void refreshDocumentWorkspace();
    if (tabId === "settings") void loadRuntimeSettings();
    if (tabId === "skills") void loadSkills();
}

function activateInitialTabFromUrl() {
    try {
        const tabId = new URLSearchParams(window.location.search).get("tab");
        if (!tabId || !tabNames[tabId]) return;
        const navElement = document.querySelector(`.nav-item[data-tab="${tabId}"]`);
        if (navElement) switchTab(tabId, navElement);
    } catch {
        // Keep the default dashboard tab if URL parsing fails.
    }
}

function getDismissedNavBadges() {
    try {
        return JSON.parse(window.localStorage.getItem(DISMISSED_NAV_BADGES_KEY) || "[]");
    } catch {
        return [];
    }
}

function setDismissedNavBadges(values) {
    try {
        window.localStorage.setItem(DISMISSED_NAV_BADGES_KEY, JSON.stringify([...new Set(values)]));
    } catch {
        // Ignore storage failures; the visual state still updates for this session.
    }
}

function clearNavBadge(tabId) {
    const badge = document.querySelector(`.nav-item[data-tab="${tabId}"] .nav-badge`);
    if (!badge) return;
    badge.classList.add("dismissed");
    setDismissedNavBadges([...getDismissedNavBadges(), tabId]);
}

function restoreDismissedNavBadges() {
    getDismissedNavBadges().forEach((tabId) => {
        document.querySelector(`.nav-item[data-tab="${tabId}"] .nav-badge`)?.classList.add("dismissed");
    });
}

function restoreSidebarState() {
    try {
        if (window.localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === "1") {
            document.body.classList.add("sidebar-collapsed");
        }
    } catch {
        // Ignore storage failures.
    }
}

function getBackendBaseUrl() {
    try {
        const params = new URLSearchParams(window.location.search);
        const queryUrl = params.get("api");
        if (queryUrl) {
            window.localStorage.setItem(BACKEND_BASE_URL_KEY, queryUrl);
            return normalizeBaseUrl(queryUrl);
        }
        const storedUrl = normalizeBaseUrl(window.localStorage.getItem(BACKEND_BASE_URL_KEY) || "");
        if (storedUrl && !LOCAL_BACKEND_BASE_URLS.includes(storedUrl)) return storedUrl;
        return DEFAULT_BACKEND_BASE_URL;
    } catch {
        return DEFAULT_BACKEND_BASE_URL;
    }
}

function normalizeBaseUrl(url) {
    return String(url || DEFAULT_BACKEND_BASE_URL).trim().replace(/\/+$/, "");
}

function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        "\"": "&quot;",
        "'": "&#39;",
    })[char]);
}

const RICH_ANSWER_ALLOWED_TAGS = new Set([
    "A", "BLOCKQUOTE", "BR", "CODE", "EM", "H2", "H3", "H4", "HR", "LI", "OL", "P",
    "PRE", "STRONG", "TABLE", "TBODY", "TD", "TH", "THEAD", "TR", "UL",
]);
const RICH_ANSWER_DROP_TAGS = new Set(["SCRIPT", "STYLE", "IFRAME", "OBJECT", "EMBED", "FORM", "INPUT", "BUTTON"]);

function isSafeAnswerUrl(value = "") {
    const source = String(value || "").trim();
    if (!source || source.startsWith("#")) return true;
    try {
        const url = new URL(source, window.location.origin);
        return ["http:", "https:", "mailto:"].includes(url.protocol);
    } catch {
        return false;
    }
}

function sanitizeAnswerHtml(value = "") {
    const documentFragment = new DOMParser().parseFromString(String(value || ""), "text/html");
    const nodes = [...documentFragment.body.querySelectorAll("*")];

    nodes.forEach((node) => {
        const tagName = node.tagName;
        if (RICH_ANSWER_DROP_TAGS.has(tagName)) {
            node.remove();
            return;
        }
        if (!RICH_ANSWER_ALLOWED_TAGS.has(tagName)) {
            node.replaceWith(...node.childNodes);
            return;
        }

        [...node.attributes].forEach((attribute) => {
            const name = attribute.name.toLowerCase();
            const isAllowedLinkAttribute = tagName === "A" && ["href", "title", "target"].includes(name);
            const isAllowedTableAttribute = ["TD", "TH"].includes(tagName) && ["colspan", "rowspan"].includes(name);
            if (!isAllowedLinkAttribute && !isAllowedTableAttribute) node.removeAttribute(attribute.name);
        });

        if (tagName === "A") {
            if (!isSafeAnswerUrl(node.getAttribute("href"))) {
                node.removeAttribute("href");
            }
            if (node.getAttribute("target") === "_blank") {
                node.setAttribute("rel", "noopener noreferrer");
            } else {
                node.removeAttribute("target");
            }
        }
    });
    return documentFragment.body.innerHTML;
}

function renderInlineMarkdown(value = "") {
    const htmlTokens = [];
    const tokenized = String(value || "").replace(/<\/?[a-zA-Z][^>]*>/g, (tag) => {
        const index = htmlTokens.push(tag) - 1;
        return `@@ANSWER_HTML_${index}@@`;
    });
    let rendered = escapeHtml(tokenized);
    rendered = rendered.replace(/`([^`]+)`/g, "<code>$1</code>");
    rendered = rendered.replace(/\[([^\]]+)\]\(([^\s)]+)(?:\s+&quot;[^&]*&quot;)?\)/g, '<a href="$2" target="_blank">$1</a>');
    rendered = rendered.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    rendered = rendered.replace(/__([^_]+)__/g, "<strong>$1</strong>");
    rendered = rendered.replace(/(?<!\*)\*([^*\n]+)\*(?!\*)/g, "<em>$1</em>");
    rendered = rendered.replace(/(?<!_)_([^_\n]+)_(?!_)/g, "<em>$1</em>");
    return rendered.replace(/@@ANSWER_HTML_(\d+)@@/g, (_match, index) => htmlTokens[Number(index)] || "");
}

function splitMarkdownTableRow(line = "") {
    return String(line || "").trim().replace(/^\||\|$/g, "").split("|").map((cell) => cell.trim());
}

function isMarkdownTableSeparator(line = "") {
    return /^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(String(line || ""));
}

function renderMarkdownAnswer(text = "") {
    const lines = String(text || "").replace(/\r\n/g, "\n").replace(/\r/g, "\n").split("\n");
    const blocks = [];
    let paragraph = [];
    let list = null;
    let quote = [];
    let code = null;

    const flushParagraph = () => {
        if (!paragraph.length) return;
        blocks.push(`<p>${renderInlineMarkdown(paragraph.join("<br>"))}</p>`);
        paragraph = [];
    };
    const flushList = () => {
        if (!list?.items.length) {
            list = null;
            return;
        }
        blocks.push(`<${list.type}>${list.items.map((item) => `<li>${renderInlineMarkdown(item)}</li>`).join("")}</${list.type}>`);
        list = null;
    };
    const flushQuote = () => {
        if (!quote.length) return;
        blocks.push(`<blockquote>${renderInlineMarkdown(quote.join("<br>"))}</blockquote>`);
        quote = [];
    };
    const flushAll = () => {
        flushParagraph();
        flushList();
        flushQuote();
    };

    for (let index = 0; index < lines.length; index += 1) {
        const line = lines[index];
        const trimmed = line.trim();

        if (trimmed.startsWith("```")) {
            if (code === null) {
                flushAll();
                code = [];
            } else {
                blocks.push(`<pre><code>${escapeHtml(code.join("\n"))}</code></pre>`);
                code = null;
            }
            continue;
        }
        if (code !== null) {
            code.push(line);
            continue;
        }
        if (!trimmed) {
            flushAll();
            continue;
        }

        const heading = trimmed.match(/^(#{1,3})\s+(.+)$/);
        if (heading) {
            flushAll();
            const level = Math.min(4, heading[1].length + 1);
            blocks.push(`<h${level}>${renderInlineMarkdown(heading[2])}</h${level}>`);
            continue;
        }
        if (/^(?:---|\*\*\*|___)$/.test(trimmed)) {
            flushAll();
            blocks.push("<hr>");
            continue;
        }
        if (index + 1 < lines.length && trimmed.includes("|") && isMarkdownTableSeparator(lines[index + 1])) {
            flushAll();
            const headers = splitMarkdownTableRow(trimmed);
            const rows = [];
            index += 2;
            while (index < lines.length && lines[index].trim().includes("|")) {
                rows.push(splitMarkdownTableRow(lines[index]));
                index += 1;
            }
            index -= 1;
            blocks.push(`<table><thead><tr>${headers.map((cell) => `<th>${renderInlineMarkdown(cell)}</th>`).join("")}</tr></thead><tbody>${rows.map((row) => `<tr>${headers.map((_cell, column) => `<td>${renderInlineMarkdown(row[column] || "")}</td>`).join("")}</tr>`).join("")}</tbody></table>`);
            continue;
        }
        const quoteMatch = trimmed.match(/^>\s?(.*)$/);
        if (quoteMatch) {
            flushParagraph();
            flushList();
            quote.push(quoteMatch[1]);
            continue;
        }
        const unordered = trimmed.match(/^[-+*]\s+(.+)$/);
        const ordered = trimmed.match(/^\d+[.)]\s+(.+)$/);
        if (unordered || ordered) {
            flushParagraph();
            flushQuote();
            const type = unordered ? "ul" : "ol";
            if (!list || list.type !== type) {
                flushList();
                list = { type, items: [] };
            }
            list.items.push((unordered || ordered)[1]);
            continue;
        }

        flushList();
        flushQuote();
        paragraph.push(line);
    }

    if (code !== null) blocks.push(`<pre><code>${escapeHtml(code.join("\n"))}</code></pre>`);
    flushAll();
    return sanitizeAnswerHtml(blocks.join(""));
}

function usesRichAnswerMarkup(text = "") {
    const value = String(text || "");
    return /(?:^|\n)\s*(?:#{1,6}\s+|[-+]\s+|>\s+|```)|(?:\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^\)]+\)|<\/?[a-zA-Z][^>]*>)/.test(value);
}

function normalizeRiskLevel(level) {
    const value = String(level || "low").toLowerCase();
    if (value === "critical" || value === "crit") return "crit";
    if (value === "high") return "high";
    if (value === "medium" || value === "med") return "med";
    return "low";
}

function riskScoreFor(level) {
    if (level === "crit") return 95;
    if (level === "high") return 82;
    if (level === "med") return 58;
    return 28;
}

function riskColorFor(level) {
    if (level === "crit") return "var(--red)";
    if (level === "high") return "var(--orange)";
    if (level === "med") return "var(--yellow)";
    return "var(--green)";
}

function trendClassForValue(value) {
    const number = Number(value);
    if (!Number.isFinite(number) || number === 0) return "flat";
    return number > 0 ? "up" : "down";
}

function marketTrendClassForValue(value) {
    const trend = trendClassForValue(value);
    if (trend === "up") return "market-up";
    if (trend === "down") return "market-down";
    return "market-flat";
}

function trendColorForValue(value) {
    const trend = trendClassForValue(value);
    if (trend === "up") return "var(--red)";
    if (trend === "down") return "var(--green)";
    return "var(--muted)";
}

function formatPercentSigned(value, digits = 1) {
    const number = Number(value);
    if (!Number.isFinite(number)) return "";
    // All return and move values in the application use decimal ratios. Do not
    // infer an alternate unit from magnitude: IPO gains can legitimately exceed 100%.
    const pct = number * 100;
    const sign = pct > 0 ? "+" : "";
    return `${sign}${pct.toFixed(digits)}%`;
}

function renderBackendStatus(status, label) {
    const actions = document.querySelector(".topbar-actions");
    if (!actions) return;
    let badge = document.getElementById("backend-status");
    if (!badge) {
        badge = document.createElement("button");
        badge.id = "backend-status";
        badge.className = "backend-status";
        badge.type = "button";
        badge.title = "点击后在控制台查看后端地址";
        badge.addEventListener("click", () => console.info(`Backend API: ${backendState.baseUrl}`));
        actions.prepend(badge);
    }
    badge.className = `backend-status ${status}`;
    badge.innerHTML = `<span></span>${escapeHtml(label)}`;
}

function createLegalThreadId() {
    if (window.crypto?.randomUUID) return window.crypto.randomUUID();
    return `thread-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

const lifecycleStageCatalog = [
    {
        id: "formation",
        label: "设立与治理",
        scope: "主体、章程、出资和核心资产安排",
        projectStages: ["establishment"],
        businessStages: ["formation"],
        productStages: ["stage-incorporation"],
    },
    {
        id: "research",
        label: "研发与验证",
        scope: "研发资料、数据来源、技术验证和成果归属",
        projectStages: ["research_and_development"],
        businessStages: ["research"],
        productStages: ["stage-data-compliance"],
    },
    {
        id: "market-access",
        label: "市场准入与客户导入",
        scope: "材料合规声明、客户准入、产品安全和交付边界",
        projectStages: ["market_access"],
        businessStages: ["market_access"],
        productStages: [],
    },
    {
        id: "commercialization",
        label: "商业化与质量交付",
        scope: "质量协议、验收追溯、供货合同和产品责任",
        projectStages: ["commercialization"],
        businessStages: ["commercialization", "product"],
        productStages: [],
    },
    {
        id: "financing",
        label: "融资与税务治理",
        scope: "融资文件、研发费用、税务口径和关联交易安排",
        projectStages: ["financing"],
        businessStages: ["financing"],
        productStages: [],
    },
    {
        id: "scaling",
        label: "规模扩张与市场竞争",
        scope: "扩产投资、竞争合规、经销体系和重大客户集中度",
        projectStages: ["scale_expansion", "market_expansion"],
        businessStages: ["scaling", "growth"],
        productStages: [],
    },
    {
        id: "transition",
        label: "退出/战略调整与供应链韧性",
        scope: "双源供应、跨境采购、出口管制、重组或退出安排",
        projectStages: ["strategic_adjustment", "exit"],
        businessStages: ["transition", "exit", "operation"],
        productStages: [],
    },
];

function getLifecycleStageCatalog() {
    const productData = backendState.product?.lifecycleRisk?.data;
    // Product view models are fixture-backed display fallbacks.  Once the
    // tenant has an actual lifecycle scope, its internal-risk and intake
    // workflow is the source of truth; otherwise a stale fixture can hide
    // most of the registered lifecycle stages.
    if (backendState.riskIntake?.scope?.lifecycle_states?.length) {
        return lifecycleStageCatalog;
    }
    if (!productData?.scenario_driven || !Array.isArray(productData.stages) || !productData.stages.length) {
        return lifecycleStageCatalog;
    }
    return productData.stages
        .map((stage, index) => ({
            ...stage,
            id: stage.stage_id || stage.id || `scenario-stage-${index + 1}`,
            label: stage.label || stage.stage_id || `场景阶段 ${index + 1}`,
            scope: stage.scope || "由当前产业链场景生成的生命周期控制范围。",
            projectStages: [...new Set([...(stage.project_stages || []), stage.control_stage].filter(Boolean))],
            productStages: [...new Set([...(stage.product_stages || []), stage.stage_id].filter(Boolean))],
            businessStages: [...new Set([...(stage.business_stages || []), stage.business_stage].filter(Boolean))],
            controlStage: stage.control_stage || stage.controlStage || null,
            projectIds: stage.project_ids || [],
            stateIds: stage.state_ids || [],
            nodeIds: stage.node_ids || [],
            supplierIds: stage.supplier_ids || [],
            externalDomains: stage.external_domains || stage.externalDomains || [],
        }))
        .sort((left, right) => (Number(left.phase_order) || 0) - (Number(right.phase_order) || 0));
}

function lifecycleStageForState(state, scope) {
    const catalog = getLifecycleStageCatalog();
    const object = (scope?.objects || []).find((item) => item.object_id === state?.scope_id);
    return catalog.find((stage) => (
        stage.projectIds?.includes(state?.scope_id)
        || stage.stateIds?.includes(state?.state_id)
        || stage.projectIds?.includes(object?.project_id)
        || (stage.businessStages?.includes(state?.business_stage) && (!stage.controlStage || stage.controlStage === state?.control_stage))
        || stage.id === state?.scenario_stage_id
        || stage.id === state?.business_stage
        || stage.projectStages?.includes(state?.control_stage)
    )) || null;
}

const lifecycleRiskTitleOverrides = {
    "Training data and overseas cloud arrangement require verification": "训练数据与云服务安排待核验",
    "Open-source components and model assets lack release review": "开源组件与技术资产待核验",
    "Third-party model contract does not define customer data responsibilities": "第三方服务合同的数据责任待明确",
};

const lifecycleCheckTitleOverrides = {
    "Data source and authorization": "数据来源与授权依据",
    "Cross-border architecture review": "跨境数据处理架构核验",
    "Open-source component list": "开源组件清单",
    "Release and technical-secret review": "发布与技术秘密核验",
    "Customer and provider data boundary": "客户与服务商数据边界",
    "Complete the training data authorization inventory": "完成训练数据授权清单",
    "Assess the overseas cloud and data export arrangement": "核验境外云服务与数据出境安排",
    "Produce an SBOM and complete open-source license review": "生成软件物料清单并完成开源许可核验",
};

const lifecycleExternalStageMap = {
    data_model_governance: ["research"],
    technology_ip: ["research"],
    product_commercialization: ["market-access", "commercialization", "scaling"],
    cross_border_supply_chain: ["transition"],
    corporate_finance_governance: ["formation", "financing", "scaling"],
    supply_chain: ["transition"],
    export_control: ["transition"],
    ip: ["research"],
    disclosure: ["market-access", "commercialization"],
};

let selectedLifecycleStageId = "research";

function lifecycleRiskLabel(level) {
    return { critical: "严重", high: "高", medium: "中", low: "低" }[normalizeRiskLevel(level)] || "待评估";
}

function lifecycleStageForProjectStage(stageId) {
    return getLifecycleStageCatalog().find((stage) => stage.projectStages.includes(stageId))?.id || null;
}

function lifecycleStageForProductStage(stageId) {
    return getLifecycleStageCatalog().find((stage) => stage.productStages.includes(stageId))?.id || null;
}

function lifecycleBusinessStageLabel(stageId) {
    const catalog = getLifecycleStageCatalog();
    return catalog.find((stage) => stage.id === stageId || stage.businessStages?.includes(stageId))?.label || stageId || "待配置";
}

function lifecycleStageForRisk(risk, scope) {
    const catalog = getLifecycleStageCatalog();
    const matchedIds = new Set(risk?.matched_object_ids || []);
    const matchedObject = (scope?.objects || []).find((object) => matchedIds.has(object.object_id));
    const projectMatch = catalog.find((stage) => stage.projectIds?.includes(risk?.project_id) || stage.projectIds?.includes(matchedObject?.project_id));
    if (projectMatch) return projectMatch.id;
    const matchedStates = (scope?.objects || [])
        .filter((object) => matchedIds.has(object.object_id))
        .flatMap((object) => object.lifecycle_state_ids || []);
    const activeState = (scope?.lifecycle_states || []).find((state) => matchedStates.includes(state.state_id) && state.status === "active");
    return lifecycleStageForState(activeState, scope)?.id || activeState?.business_stage || lifecycleStageForProjectStage(risk?.lifecycle_stage);
}

function displayLifecycleRiskTitle(risk) {
    const title = risk?.title || "待补充风险事项";
    return lifecycleRiskTitleOverrides[title] || title;
}

function displayLifecycleCheckTitle(check) {
    const title = typeof check === "string" ? check : check?.title;
    return lifecycleCheckTitleOverrides[title] || title || "待补充核验材料";
}

function lifecycleStagesForExternalSignal(signal) {
    const catalog = getLifecycleStageCatalog();
    const explicitStageIds = Array.isArray(signal?.lifecycle_stage_ids)
        ? signal.lifecycle_stage_ids
        : signal?.metadata?.lifecycle_stage_id
            ? [signal.metadata.lifecycle_stage_id]
            : [];
    if (explicitStageIds.length) return [...new Set(explicitStageIds)];
    const domains = [
        ...(Array.isArray(signal?.affected_domains) ? signal.affected_domains : []),
        signal?.risk_domain,
        signal?.metadata?.risk_domain,
    ].filter(Boolean).map((domain) => String(domain).trim().toLowerCase());
    const dynamicMatches = catalog
        .filter((stage) => (stage.externalDomains || []).some((domain) => domains.includes(String(domain).trim().toLowerCase())))
        .map((stage) => stage.id);
    return dynamicMatches.length
        ? [...new Set(dynamicMatches)]
        : [...new Set(domains.flatMap((domain) => lifecycleExternalStageMap[domain] || []))];
}

const EXTERNAL_SIGNAL_TYPE_LABELS = {
    market: "证券/指数行情",
    commodity_futures: "商品期货行情",
    policy: "政策消息",
    news: "财经消息",
    disclosure: "监管披露",
    news_policy: "消息与政策",
    supply_chain: "供应链数据",
    company_profile: "企业画像",
};

const EXTERNAL_SIGNAL_DOMAIN_LABELS = {
    market: "市场",
    disclosure: "信息披露",
    supply_chain: "供应链",
    contract: "合同履约",
    logistics: "物流运输",
    energy: "能源成本",
    trade: "贸易政策",
    policy: "政策环境",
    financing: "融资环境",
    legal: "法律合规",
    agriculture: "农业",
    agriculture_food: "农产品与食品",
    food: "食品",
    maritime_logistics: "海运物流",
    oil_transport: "油运",
    data_center: "数据中心",
    cross_border: "跨境贸易",
    chemical: "化工",
    metal: "金属",
    metals: "金属材料",
    telecom: "通信",
    consumer_electronics: "消费电子",
    display_panel: "显示面板",
    semiconductor: "半导体",
    semiconductor_materials: "半导体材料",
    electronic_chemical: "电子化学品",
    electronics: "电子",
    solvent: "溶剂",
    material: "材料",
    path: "产业路径",
    risk_domain: "风险领域",
};

function externalSignalTypeLabel(value) {
    const key = String(value || "").trim();
    return EXTERNAL_SIGNAL_TYPE_LABELS[key] || key || "外部信号";
}

function externalSignalDomainLabel(value) {
    const key = String(value || "").trim();
    return EXTERNAL_SIGNAL_DOMAIN_LABELS[key] || key;
}

function externalSignalMetricLabel(signal) {
    const metric = String(signal?.metric || "").trim();
    if (metric === "intraday_return") return "日内涨跌";
    const dayMatch = metric.match(/^(\d+)d_return$/i);
    if (dayMatch) return `${dayMatch[1]}日涨跌`;
    if (metric === "price") return "最新价";
    if (metric === "volume") return "成交量";
    if (metric === "news_rule_match") return "消息规则匹配";
    if (metric === "policy_rule_match") return "政策规则匹配";
    if (metric === "supply_chain_market_observation") return "供应链市场观察";
    return metric || "市场变化";
}

function externalSignalDisplayTitle(signal) {
    const metadata = signal?.metadata || {};
    if (metadata.instrument_label) {
        return `${metadata.instrument_label} · ${externalSignalMetricLabel(signal)}`;
    }
    return signal?.title || signal?.entity || "外部风险信号";
}

function externalInstrumentDisplayLabel(value) {
    const raw = String(value || "").trim();
    if (!raw) return "";
    const symbol = resolveMarketSymbol(raw);
    if (!symbol || symbol === raw && !/^(?:sh|sz|bj|hk_|kr_|us_|hf_|if_|bk_|bond_)/i.test(raw)) return raw;
    const name = quoteDisplayName("", symbol);
    return name && name !== symbol ? standardInstrumentLabel(name, symbol) : standardInstrumentCode(symbol);
}

function localizeExternalInstrumentText(value) {
    return String(value || "").replace(/\b(?:sh|sz|bj)\d{6}\b|\b(?:hk_|kr_|us_|hf_|if_|bk_|bond_)[A-Za-z0-9]+\b/gi, (symbol) => externalInstrumentDisplayLabel(symbol));
}

function lifecycleExternalSignalTitle(signal) {
    return externalSignalDisplayTitle(signal);
}

function buildLifecycleStages() {
    const productData = backendState.product?.lifecycleRisk?.data;
    const productRisks = backendState.product?.risks?.items || [];
    const workflow = backendState.internalRisk?.data;
    const enterpriseScope = backendState.riskIntake?.scope;
    const productRiskById = new Map(productRisks.map((risk) => [risk.risk_id, risk]));
    const catalog = getLifecycleStageCatalog();
    const stages = catalog.map((stage) => ({
        ...stage,
        risks: [],
        gates: [],
        tasks: [],
        externalSignals: [],
        evidenceRefs: [],
        recommendedActions: [],
        sourceKinds: new Set([productData?.scenario_driven ? "scenario" : "template"]),
    }));
    const byId = new Map(stages.map((stage) => [stage.id, stage]));

    (workflow?.risk_items || []).forEach((risk) => {
        const stage = byId.get(lifecycleStageForRisk(risk, enterpriseScope));
        if (!stage) return;
        stage.risks.push({
            id: risk.risk_id,
            title: displayLifecycleRiskTitle(risk),
            level: normalizeRiskLevel(risk.risk_level),
            status: risk.status,
            facts: risk.trigger_facts || [],
            missingMaterials: risk.missing_materials || [],
            owner: null,
            source: "内部风控",
        });
        stage.evidenceRefs.push(...(risk.evidence_refs || []));
        stage.sourceKinds.add("workflow");
    });

    (workflow?.gates || []).forEach((gate) => {
        const stage = byId.get(
            stages.find((item) => item.projectIds?.includes(gate.project_id))?.id
                || lifecycleStageForProjectStage(gate.lifecycle_stage),
        );
        if (!stage) return;
        stage.gates.push({
            title: gate.title,
            decision: gate.decision,
            owner: gate.owner,
            missing: (gate.checks || []).filter((check) => check.status === "missing"),
        });
        stage.sourceKinds.add("workflow");
    });

    (workflow?.remediation_tasks || []).forEach((task) => {
        const risk = (workflow.risk_items || []).find((item) => item.risk_id === task.risk_id);
        const stage = byId.get(
            stages.find((item) => item.projectIds?.includes(task.project_id) || item.projectIds?.includes(risk?.project_id))?.id
                || lifecycleStageForProjectStage(risk?.lifecycle_stage),
        );
        if (!stage) return;
        stage.tasks.push({ title: task.title, owner: task.owner, dueDate: task.due_date, status: task.status });
        stage.evidenceRefs.push(...(task.evidence_refs || []));
        stage.sourceKinds.add("workflow");
    });

    (productData?.stages || []).forEach((productStage) => {
        const stage = byId.get(productStage.stage_id) || byId.get(lifecycleStageForProductStage(productStage.stage_id));
        if (!stage) return;
        (productStage.risk_ids || []).forEach((riskId) => {
            const risk = productRiskById.get(riskId);
            if (!risk || stage.risks.some((item) => item.id === riskId)) return;
            stage.risks.push({
                id: riskId,
                title: risk.title,
                level: normalizeRiskLevel(risk.risk_level || productStage.risk_level),
                status: "open",
                facts: [risk.summary].filter(Boolean),
                missingMaterials: [],
                owner: null,
                source: "生命周期视图",
            });
        });
        stage.evidenceRefs.push(...(productStage.evidence_refs || []));
        stage.recommendedActions.push(...(productStage.recommended_actions || []));
        if ((productStage.risk_ids || []).length || (productStage.evidence_refs || []).length) stage.sourceKinds.add("product");
    });

    const externalSignals = supplyState.externalSignals || backendState.externalRisk?.data?.signals || [];
    externalSignals.forEach((signal) => {
        lifecycleStagesForExternalSignal(signal).forEach((stageId) => {
            const stage = byId.get(stageId);
            if (!stage) return;
            stage.externalSignals.push({
                title: lifecycleExternalSignalTitle(signal),
                level: normalizeRiskLevel(signal.severity),
                source: signal.source || "外部风险",
            });
            stage.sourceKinds.add("external");
        });
    });

    return stages.map((stage) => {
        const highCount = stage.risks.filter((risk) => ["high", "critical"].includes(risk.level)).length;
        const missingCount = stage.risks.reduce((sum, risk) => sum + risk.missingMaterials.length, 0)
            + stage.gates.reduce((sum, gate) => sum + gate.missing.length, 0);
        const primaryGate = stage.gates.find((gate) => gate.decision === "suspended")
            || stage.gates.find((gate) => gate.decision === "rectification_required")
            || stage.gates[0];
        const hasConnectedRecord = stage.nodeIds?.length || stage.risks.length || stage.gates.length || stage.tasks.length;
        return {
            ...stage,
            highCount,
            missingCount,
            primaryGate,
            hasConnectedRecord,
            evidenceRefs: [...new Set(stage.evidenceRefs)],
            recommendedActions: [...new Set(stage.recommendedActions)],
        };
    });
}

function lifecycleStageState(stage) {
    if (!stage.hasConnectedRecord) return "baseline";
    if (stage.highCount || ["suspended", "rectification_required"].includes(stage.primaryGate?.decision)) return "attention";
    return "tracked";
}

function renderLifecycleOverview(stages) {
    const container = document.getElementById("lifecycle-overview");
    if (!container) return;
    const productData = backendState.product?.lifecycleRisk?.data;
    const scenarioDriven = productData?.scenario_driven === true;
    const connected = stages.filter((stage) => stage.hasConnectedRecord).length;
    const openRisks = stages.reduce((sum, stage) => sum + stage.risks.filter((risk) => risk.status !== "closed").length, 0);
    const pendingItems = stages.reduce((sum, stage) => sum + stage.missingCount, 0);
    const title = scenarioDriven
        ? productData.title || productData.company_name || "场景全生命周期"
        : "通用企业生命周期模板";
    const description = scenarioDriven
        ? productData.description || "阶段、风险和控制项由当前调试场景生成。"
        : "已接入事项会显示在对应阶段；未接入阶段不作风险判断。";
    const sourceLabel = scenarioDriven
        ? `场景数据 · ${productData.stage_count || stages.length} 个产业链阶段`
        : "模板与演示数据";
    container.innerHTML = `
        <div class="lifecycle-overview-main">
            <span class="metric-label">生命周期总览</span>
            <h2>${escapeHtml(title)}</h2>
            <p>${escapeHtml(description)}</p>
        </div>
        <dl class="lifecycle-overview-metrics">
            <div><dt>已接入阶段</dt><dd>${connected}<small>/${stages.length}</small></dd></div>
            <div><dt>待处理事项</dt><dd>${openRisks}</dd></div>
            <div><dt>材料缺口</dt><dd>${pendingItems}</dd></div>
        </dl>
        <div class="lifecycle-overview-note"><span class="lifecycle-source-mark"></span>${escapeHtml(sourceLabel)}</div>
    `;
}

const lifecycleTopicCatalog = [
    { id: "data", label: "数据与安全", domains: ["data_model_governance"] },
    { id: "ip", label: "研发与知识资产", domains: ["technology_ip"] },
    { id: "people", label: "人员与关键岗位", domains: [] },
    { id: "supply", label: "供应链与第三方", domains: ["cross_border_supply_chain"] },
    { id: "finance", label: "融资与治理", domains: ["corporate_finance_governance"] },
    { id: "product", label: "产品与市场", domains: ["product_commercialization"] },
    { id: "crossborder", label: "跨境合规", domains: ["cross_border_supply_chain", "data_model_governance"] },
];

function renderLifecycleContext() {
    const container = document.getElementById("lifecycle-context");
    if (!container) return;
    const productData = backendState.product?.lifecycleRisk?.data;
    const scenarioDriven = productData?.scenario_driven === true;
    const scope = backendState.riskIntake?.scope;
    const workflow = backendState.internalRisk?.data;
    const activeStates = (scope?.lifecycle_states || []).filter((state) => state.status === "active");
    const topics = lifecycleTopicCatalog.map((topic) => {
        const risks = (workflow?.risk_items || []).filter((risk) => topic.domains.includes(risk.risk_domain) && risk.status !== "closed");
        const label = risks.length ? `${risks.length} 项待跟进` : topic.domains.length ? "已接入，暂无事项" : "尚未建立清单";
        return `<li class="${risks.some((risk) => ["high", "critical"].includes(risk.risk_level)) ? "is-attention" : ""}"><span>${escapeHtml(topic.label)}</span><strong>${escapeHtml(label)}</strong></li>`;
    }).join("");
    if (!scope || !activeStates.length) {
        container.innerHTML = `<div class="lifecycle-context-empty"><strong>当前经营情况待补充</strong><span>先登记企业、项目和当前经营事项，系统才能提示需要关注的管理动作。</span></div>`;
        return;
    }
    const contexts = activeStates.map((state) => {
        const object = (scope.objects || []).find((item) => item.object_id === state.scope_id || item.project_id === state.scope_id);
        const stage = lifecycleStageForState(state, scope);
        const gate = (workflow?.gates || []).find((item) => item.project_id === state.scope_id || item.lifecycle_stage === state.control_stage);
        const decision = gate ? (internalGateDecisionLabels[gate.decision] || gate.decision) : "尚未设置";
        return `
            <article class="lifecycle-context-item">
                <div><span class="metric-label">当前经营事项</span><h2>${escapeHtml(object?.name || state.scope_id)}</h2><p>${escapeHtml(stage?.label || state.business_stage)} · ${escapeHtml(internalRiskStageLabels[state.control_stage] || "管理环节待补充")}</p></div>
                <dl><div><dt>关键决策点</dt><dd>${escapeHtml(decision)}</dd></div><div><dt>负责人</dt><dd>${escapeHtml(state.owner || "待分配")}</dd></div><div><dt>阶段依据</dt><dd>${escapeHtml(state.basis || "待补充")}</dd></div></dl>
            </article>`;
    }).join("");
    const contextNote = scenarioDriven ? "场景全生命周期" : "演示数据";
    container.innerHTML = `<div class="lifecycle-context-head"><div><span class="metric-label">企业当前情况</span><h2>${escapeHtml(scope.name)}</h2><p>每个产业链节点按自身进度关联风险、证据和控制动作；阶段由当前场景动态生成。</p></div><span class="lifecycle-context-note">${escapeHtml(contextNote)}</span></div>${contexts}<section class="lifecycle-topic-panel"><div><span class="metric-label">持续关注领域</span><p>数据、人员、供应链等领域贯穿经营全过程，不是独立的经营阶段。</p></div><ul>${topics}</ul></section>`;
    const latestTransitions = (scope.lifecycle_state_history || []).slice(-3).reverse();
    if (latestTransitions.length) {
        container.insertAdjacentHTML("beforeend", `<section class="lifecycle-history-panel"><div><span class="metric-label">经营阶段变更记录</span><p>每次调整都保留负责人、依据、生效时间和关键决策结果。</p></div><ul>${latestTransitions.map((item) => `<li><strong>${escapeHtml(lifecycleBusinessStageLabel(item.previous_business_stage))} -> ${escapeHtml(lifecycleBusinessStageLabel(item.business_stage))}</strong><span>${escapeHtml(formatInternalDate(item.effective_from))} · ${escapeHtml(item.changed_by)}${item.gate_decision ? ` · 决策结果：${escapeHtml(internalGateDecisionLabels[item.gate_decision] || item.gate_decision)}` : ""}</span><small>${escapeHtml(item.basis)}</small></li>`).join("")}</ul></section>`);
    }
}

function renderLifecycle() {
    const container = document.getElementById("flowchart");
    if (!container) return;
    const stages = buildLifecycleStages();
    renderLifecycleOverview(stages);
    renderLifecycleContext();
    if (!stages.some((stage) => stage.id === selectedLifecycleStageId)) selectedLifecycleStageId = stages[0]?.id;
    if (!stages.find((stage) => stage.id === selectedLifecycleStageId)?.hasConnectedRecord) {
        selectedLifecycleStageId = stages.find((stage) => stage.hasConnectedRecord)?.id || stages[0]?.id;
    }
    container.innerHTML = stages.map((stage, index) => {
        const state = lifecycleStageState(stage);
        const stateLabel = state === "attention" ? "需要处理" : state === "tracked" ? "已有事项" : "尚未建立清单";
        const context = stage.hasConnectedRecord ? `${stage.risks.length} 项事项` : "尚无企业事项";
        return `
            <button class="flow-node ${state === "attention" ? "is-attention" : ""} ${selectedLifecycleStageId === stage.id ? "active" : ""}" type="button" data-lifecycle="${stage.id}" aria-pressed="${selectedLifecycleStageId === stage.id}">
                <span class="flow-index">${String(index + 1).padStart(2, "0")}</span>
                <span class="flow-label">${escapeHtml(stage.label)}</span>
                <small>${escapeHtml(context)}</small>
                <em class="flow-state ${state}">${stateLabel}</em>
            </button>
            ${index < stages.length - 1 ? '<span class="flow-line" aria-hidden="true"></span>' : ""}
        `;
    }).join("");
    container.querySelectorAll(".flow-node").forEach((node) => {
        node.addEventListener("click", () => selectLifecycle(node.dataset.lifecycle));
    });
    selectLifecycle(selectedLifecycleStageId, true);
}

function selectLifecycle(id, preserveTrack = false) {
    const stages = buildLifecycleStages();
    const stage = stages.find((item) => item.id === id) || stages[0];
    if (!stage) return;
    selectedLifecycleStageId = stage.id;
    if (!preserveTrack) renderLifecycle();
    document.querySelectorAll(".flow-node").forEach((node) => {
        const selected = node.dataset.lifecycle === stage.id;
        node.classList.toggle("active", selected);
        node.setAttribute("aria-pressed", String(selected));
    });

    const state = lifecycleStageState(stage);
    const stateLabel = state === "attention" ? "需要优先处理" : state === "tracked" ? "已有事项" : "尚未建立清单";
    const gateLabel = stage.primaryGate
        ? (internalGateDecisionLabels[stage.primaryGate.decision] || "待确认")
        : "尚未设置";
    const riskRows = stage.risks.length
        ? stage.risks.map((risk) => `<li><span class="risk-dot ${risk.level === "critical" ? "crit" : risk.level === "high" ? "high" : risk.level === "medium" ? "med" : "low"}"></span><div><strong>${escapeHtml(risk.title)}</strong><small>${escapeHtml(risk.source)} · ${lifecycleRiskLabel(risk.level)}风险</small></div></li>`).join("")
        : '<li class="lifecycle-empty">尚未接入企业事项，不默认标记为低风险。</li>';
    const controlRows = stage.hasConnectedRecord
        ? [
            `<li><span>关联证据</span><strong>${stage.evidenceRefs.length} 项</strong></li>`,
            `<li><span>材料缺口</span><strong class="${stage.missingCount ? "has-gap" : ""}">${stage.missingCount} 项</strong></li>`,
            `<li><span>关键决策点</span><strong>${escapeHtml(gateLabel)}</strong></li>`,
        ].join("")
        : '<li class="lifecycle-empty">完成企业信息和基础材料登记后，可在此建立控制项。</li>';
    const actions = [
        ...stage.gates.flatMap((gate) => gate.missing.slice(0, 2).map((item) => `补充${displayLifecycleCheckTitle(item)}`)),
        ...stage.recommendedActions.map(displayLifecycleCheckTitle),
        ...stage.tasks.filter((task) => task.status !== "verified").slice(0, 2).map((task) => displayLifecycleCheckTitle(task.title)),
    ];
    const actionRows = actions.length
        ? [...new Set(actions)].slice(0, 4).map((item) => `<li>${escapeHtml(item)}</li>`).join("")
        : '<li class="lifecycle-empty">当前没有待分派动作。</li>';
    const scope = backendState.riskIntake?.scope;
    const stageStateIds = new Set([
        ...(stage.stateIds || []),
        ...(scope?.lifecycle_states || []).filter((item) => lifecycleStageForState(item, scope)?.id === stage.id).map((item) => item.state_id),
    ]);
    const intakeCases = (backendState.riskIntake?.cases || []).filter((item) => (
        stage.projectStages.includes(item.target_lifecycle_stage)
        || (item.lifecycle_state_ids || []).some((stateId) => stageStateIds.has(stateId))
    ));
    const externalSignals = stage.externalSignals.slice(0, 2);
    const externalRows = intakeCases.length
        ? intakeCases.slice(0, 2).map((item) => `<li><span class="risk-dot ${item.signal.severity === "critical" ? "crit" : item.signal.severity === "high" ? "high" : item.signal.severity === "medium" ? "med" : "low"}"></span><div><strong>${escapeHtml(item.signal.title)}</strong><small>${item.status === "pending_triage" ? "待核实" : item.status === "promoted" ? "已登记为风险线索" : "已完成核实"} · ${escapeHtml(item.signal.as_of)}</small></div>${item.status === "pending_triage" ? `<button class="link-button" type="button" data-lifecycle-intake="${escapeHtml(item.intake_id)}">核实</button>` : ""}</li>`).join("")
        : externalSignals.length
            ? externalSignals.map((signal) => `<li><span class="risk-dot ${signal.level === "critical" ? "crit" : signal.level === "high" ? "high" : signal.level === "medium" ? "med" : "low"}"></span><div><strong>${escapeHtml(signal.title)}</strong><small>${escapeHtml(signal.source)} · 尚未命中企业对象</small></div></li>`).join("")
            : '<li class="lifecycle-external-empty">暂无与本阶段有关的外部风险线索。只有命中已登记企业对象的信息才进入待核实清单。</li>';
    const detail = document.getElementById("lc-detail");
    if (!detail) return;
    detail.innerHTML = `
        <section class="lifecycle-detail-panel">
            <header class="lc-detail-head">
                <div><span class="metric-label">${stateLabel}</span><h2>${escapeHtml(stage.label)}</h2><p>${escapeHtml(stage.scope)}</p></div>
                <div class="lifecycle-detail-actions">
                    <button class="btn" type="button" data-lifecycle-action="evidence" ${stage.evidenceRefs.length ? "" : "disabled"}>查看证据</button>
                    <button class="btn" type="button" data-lifecycle-action="external">外部风险</button>
                    <button class="btn btn-primary" type="button" data-lifecycle-action="internal">进入处置</button>
                </div>
            </header>
            <div class="lifecycle-summary-row">
                <div><span>风险事项</span><strong>${stage.risks.length}</strong></div>
                <div><span>高风险</span><strong class="${stage.highCount ? "high" : ""}">${stage.highCount}</strong></div>
                <div><span>整改任务</span><strong>${stage.tasks.length}</strong></div>
                <div><span>数据来源</span><strong>${stage.sourceKinds.has("scenario") ? "当前调试场景" : stage.sourceKinds.has("workflow") ? "内部风控" : "通用模板"}</strong></div>
            </div>
            <div class="lifecycle-detail-grid">
                <section><h3>风险事项</h3><ul class="lifecycle-risk-list">${riskRows}</ul></section>
                <section><h3>控制与证据</h3><ul class="lifecycle-control-list">${controlRows}</ul></section>
                <section><h3>建议处理顺序</h3><ol class="lifecycle-action-list">${actionRows}</ol></section>
            </div>
            <section class="lifecycle-external-strip">
                <div><span class="metric-label">外部风险线索</span><h3>${intakeCases.length ? `${intakeCases.filter((item) => item.status === "pending_triage").length} 条待核实` : externalSignals.length ? "已发现外部信息，尚未关联企业" : "等待外部信息"}</h3><button class="link-button" type="button" data-lifecycle-action="sync-external">更新外部信息</button></div>
                <ul class="lifecycle-external-list">${externalRows}</ul>
            </section>
        </section>
    `;
    detail.querySelector('[data-lifecycle-action="internal"]')?.addEventListener("click", () => {
        document.querySelector('.nav-item[data-tab="internal"]')?.click();
    });
    detail.querySelector('[data-lifecycle-action="external"]')?.addEventListener("click", () => {
        document.querySelector('.nav-item[data-tab="market"]')?.click();
    });
    detail.querySelector('[data-lifecycle-action="sync-external"]')?.addEventListener("click", async (event) => {
        const button = event.currentTarget;
        const originalLabel = button.textContent;
        button.disabled = true;
        button.textContent = "同步中";
        try {
            await syncRiskIntakeCases();
        } catch (error) {
            console.info(error);
            button.textContent = "同步失败";
            window.setTimeout(() => { button.textContent = originalLabel; button.disabled = false; }, 1400);
        }
    });
    detail.querySelectorAll('[data-lifecycle-intake]').forEach((button) => {
        button.addEventListener("click", () => showExternalIntakeDrawer(button.dataset.lifecycleIntake));
    });
    detail.querySelector('[data-lifecycle-action="evidence"]')?.addEventListener("click", () => {
        openLifecycleEvidenceContext(stage);
    });
}

async function openLifecycleEvidenceContext(stage) {
    const evidenceRefs = [...new Set(stage?.evidenceRefs || [])];
    pendingLegalEvidenceContext = { stageLabel: stage?.label || "生命周期事项", evidenceRefs };
    document.querySelector('.nav-item[data-tab="legal"]')?.click();
    window.setTimeout(() => document.getElementById("legal-document-list")?.scrollIntoView({ behavior: "smooth", block: "start" }), 180);
}

const mapRegionGroups = {
    china: ["北京", "天津", "河北", "山西", "内蒙古", "辽宁", "吉林", "黑龙江", "上海", "江苏", "浙江", "安徽", "福建", "江西", "山东", "河南", "湖北", "湖南", "广东", "广西", "海南", "重庆", "四川", "贵州", "云南", "西藏", "陕西", "甘肃", "青海", "宁夏", "新疆", "台湾", "香港", "澳门"],
    northeast: ["辽宁", "吉林", "黑龙江"],
    north: ["北京", "天津", "河北", "山西", "内蒙古", "山东"],
    northwest: ["陕西", "甘肃", "青海", "宁夏", "新疆"],
    east: ["上海", "江苏", "浙江", "安徽", "福建", "江西"],
    central: ["河南", "湖北", "湖南"],
    southwest: ["重庆", "四川", "贵州", "云南", "西藏"],
    south: ["广东", "广西", "海南", "香港", "澳门", "台湾"],
};

const provinceRisk = {
    广东: "high",
    广西: "med",
    河北: "med",
    新疆: "med",
    北京: "low",
    上海: "low",
    江苏: "low",
    浙江: "low",
};

const regionsData = {
    global: { name: "全球网络", nameEn: "Worldwide Network", totalSuppliers: 158, overallRisk: "med", keyFactors: ["地缘政治波动", "汇率波动", "跨境合规"], suppliers: [{ name: "深圳电子组件", province: "中国", risk: "high" }, { name: "Munich Auto Parts", province: "德国", risk: "low" }] },
    china: { name: "中国大陆", nameEn: "Mainland China", totalSuppliers: 142, overallRisk: "med", keyFactors: ["区域集中度", "出口管制", "环保合规"], suppliers: [{ name: "上海精密制造", province: "上海", risk: "low" }] },
    northeast: { name: "东北", nameEn: "Northeast China", provinces: [{ name: "辽宁", count: 5, risk: "low" }, { name: "吉林", count: 3, risk: "low" }, { name: "黑龙江", count: 4, risk: "low" }], totalSuppliers: 12, overallRisk: "low", keyFactors: ["重工业配套"], suppliers: [{ name: "沈阳钢构", province: "辽宁", risk: "low" }] },
    north: { name: "华北", nameEn: "North China", provinces: [{ name: "北京", count: 8, risk: "low" }, { name: "河北", count: 6, risk: "med" }, { name: "山东", count: 5, risk: "low" }], totalSuppliers: 25, overallRisk: "med", keyFactors: ["政策敏感", "能源价格"], suppliers: [{ name: "河北金属", province: "河北", risk: "med" }] },
    northwest: { name: "西北", nameEn: "Northwest China", provinces: [{ name: "陕西", count: 4, risk: "low" }, { name: "新疆", count: 3, risk: "med" }], totalSuppliers: 11, overallRisk: "low", keyFactors: ["能源资源", "运输距离"], suppliers: [{ name: "西安航材", province: "陕西", risk: "low" }] },
    east: { name: "华东", nameEn: "East China", provinces: [{ name: "上海", count: 12, risk: "low" }, { name: "江苏", count: 15, risk: "low" }, { name: "浙江", count: 14, risk: "low" }], totalSuppliers: 69, overallRisk: "low", keyFactors: ["产业集群", "港口便利", "数据合规"], suppliers: [{ name: "上海精密制造", province: "上海", risk: "low" }, { name: "苏州传感科技", province: "江苏", risk: "low" }] },
    central: { name: "华中", nameEn: "Central China", provinces: [{ name: "湖北", count: 9, risk: "low" }, { name: "河南", count: 8, risk: "low" }], totalSuppliers: 23, overallRisk: "low", keyFactors: ["交通枢纽"], suppliers: [{ name: "武汉汽车电子", province: "湖北", risk: "low" }] },
    southwest: { name: "西南", nameEn: "Southwest China", provinces: [{ name: "四川", count: 9, risk: "low" }, { name: "重庆", count: 7, risk: "low" }], totalSuppliers: 23, overallRisk: "low", keyFactors: ["水电资源", "交付周期"], suppliers: [{ name: "成都云控", province: "四川", risk: "low" }] },
    south: { name: "华南", nameEn: "South China", provinces: [{ name: "广东", count: 18, risk: "high" }, { name: "广西", count: 5, risk: "med" }, { name: "海南", count: 2, risk: "low" }], totalSuppliers: 25, overallRisk: "high", keyFactors: ["出口依赖", "供应商集中", "物流波动"], suppliers: [{ name: "深圳电子组件", province: "广东", risk: "high" }, { name: "东莞模具", province: "广东", risk: "med" }] },
    overseas: { name: "海外", nameEn: "International", totalSuppliers: 16, overallRisk: "med", keyFactors: ["跨境合规", "汇率波动"], suppliers: [{ name: "Texas Materials", province: "美国", risk: "high" }] },
    sea: { name: "东南亚", nameEn: "ASEAN", provinces: [{ name: "越南", count: 4, risk: "med" }], totalSuppliers: 8, overallRisk: "med", keyFactors: ["关税转移", "本地用工"], suppliers: [{ name: "HCMC Textiles", province: "越南", risk: "med" }] },
    eu: { name: "欧洲", nameEn: "Europe", provinces: [{ name: "德国", count: 3, risk: "low" }], totalSuppliers: 5, overallRisk: "low", keyFactors: ["GDPR", "ESG"], suppliers: [{ name: "Munich Auto", province: "德国", risk: "low" }] },
    na: { name: "北美", nameEn: "North America", provinces: [{ name: "美国", count: 3, risk: "high" }], totalSuppliers: 3, overallRisk: "high", keyFactors: ["出口管制", "长臂管辖"], suppliers: [{ name: "Texas Materials", province: "美国", risk: "high" }] },
};

const provinceSupplierCounts = {
    上海: 12,
    江苏: 15,
    浙江: 14,
    广东: 18,
    广西: 5,
    河北: 6,
    北京: 8,
    辽宁: 5,
    吉林: 3,
    黑龙江: 4,
    湖北: 9,
    河南: 8,
    四川: 9,
    重庆: 7,
    陕西: 4,
    新疆: 3,
    海南: 2,
};

const tooltip = document.getElementById("map-tooltip");
const contextMenu = document.getElementById("supplier-context-menu");
const regionButtons = document.querySelectorAll(".region-item[data-region]");
const svg = document.getElementById("china-map");
const provinceMeta = new Map();
let mapViewportGroup = null;
const defaultMapZoom = 1.06;
let mapZoom = defaultMapZoom;
let activeRegionKey = "china";
let selectedProvinceName = null;

function collectCoords(geometry, callback) {
    const visitRing = (ring) => ring.forEach(([lon, lat]) => callback(lon, lat));
    if (geometry.type === "Polygon") geometry.coordinates.forEach(visitRing);
    if (geometry.type === "MultiPolygon") geometry.coordinates.forEach((polygon) => polygon.forEach(visitRing));
}

function getGeoBounds(features) {
    const bounds = { minLon: Infinity, minLat: Infinity, maxLon: -Infinity, maxLat: -Infinity };
    features.forEach((feature) => {
        collectCoords(feature.geometry, (lon, lat) => {
            bounds.minLon = Math.min(bounds.minLon, lon);
            bounds.maxLon = Math.max(bounds.maxLon, lon);
            bounds.minLat = Math.min(bounds.minLat, lat);
            bounds.maxLat = Math.max(bounds.maxLat, lat);
        });
    });
    return bounds;
}

function createProjection(features) {
    const bounds = getGeoBounds(features);
    const width = 1000;
    const height = 780;
    const padding = -24;
    const geoWidth = bounds.maxLon - bounds.minLon;
    const geoHeight = bounds.maxLat - bounds.minLat;
    const scale = Math.min((width - padding * 2) / geoWidth, (height - padding * 2) / geoHeight);
    const mapWidth = geoWidth * scale;
    const mapHeight = geoHeight * scale;
    const offsetX = (width - mapWidth) / 2;
    const offsetY = (height - mapHeight) / 2;

    return ([lon, lat]) => [
        offsetX + (lon - bounds.minLon) * scale,
        offsetY + (bounds.maxLat - lat) * scale,
    ];
}

function pathFromGeometry(geometry, project) {
    const ringToPath = (ring) => ring.map((point, index) => {
        const [x, y] = project(point);
        return `${index === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(" ") + " Z";

    if (geometry.type === "Polygon") return geometry.coordinates.map(ringToPath).join(" ");
    if (geometry.type === "MultiPolygon") return geometry.coordinates.flatMap((polygon) => polygon.map(ringToPath)).join(" ");
    return "";
}

function projectedBounds(feature, project) {
    const bounds = { minX: Infinity, minY: Infinity, maxX: -Infinity, maxY: -Infinity };
    collectCoords(feature.geometry, (lon, lat) => {
        const [x, y] = project([lon, lat]);
        bounds.minX = Math.min(bounds.minX, x);
        bounds.maxX = Math.max(bounds.maxX, x);
        bounds.minY = Math.min(bounds.minY, y);
        bounds.maxY = Math.max(bounds.maxY, y);
    });
    return bounds;
}

function mergeBounds(boundsList) {
    return boundsList.reduce((merged, bounds) => ({
        minX: Math.min(merged.minX, bounds.minX),
        minY: Math.min(merged.minY, bounds.minY),
        maxX: Math.max(merged.maxX, bounds.maxX),
        maxY: Math.max(merged.maxY, bounds.maxY),
    }), { minX: Infinity, minY: Infinity, maxX: -Infinity, maxY: -Infinity });
}

function renderChinaMap() {
    if (!window.CHINA_PROVINCES) return;

    const project = createProjection(window.CHINA_PROVINCES.features);
    mapViewportGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
    const provinceLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
    const frameLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
    const labelLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");

    mapViewportGroup.append(frameLayer, provinceLayer, labelLayer);
    svg.replaceChildren(mapViewportGroup);

    window.CHINA_PROVINCES.features.forEach((feature) => {
        const name = feature.properties.name;
        const bounds = projectedBounds(feature, project);
        provinceMeta.set(name, { feature, bounds, risk: provinceRisk[name] || "low" });

        const d = pathFromGeometry(feature.geometry, project);
        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("class", "province-path");
        path.setAttribute("data-province", name);
        path.setAttribute("d", d);
        path.addEventListener("mouseenter", (event) => showProvinceTooltip(event, name));
        path.addEventListener("mousemove", positionTooltip);
        path.addEventListener("mouseleave", () => tooltip.classList.remove("visible"));
        path.addEventListener("click", () => selectProvince(name));
        path.addEventListener("contextmenu", (event) => openSupplierMenu(event, { province: name }));
        provinceLayer.appendChild(path);

        const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
        label.setAttribute("class", "province-label");
        label.setAttribute("data-province-label", name);
        label.setAttribute("x", ((bounds.minX + bounds.maxX) / 2).toFixed(1));
        label.setAttribute("y", ((bounds.minY + bounds.maxY) / 2).toFixed(1));
        label.textContent = name.length > 3 ? name.slice(0, 2) : name;
        labelLayer.appendChild(label);
    });

    Object.entries(mapRegionGroups).forEach(([key, names]) => {
        if (key === "china") return;
        const bounds = mergeBounds(names.map((name) => provinceMeta.get(name)?.bounds).filter(Boolean));
        if (!Number.isFinite(bounds.minX)) return;

        names.forEach((name) => {
            const meta = provinceMeta.get(name);
            if (!meta) return;
            const frame = document.createElementNS("http://www.w3.org/2000/svg", "path");
            frame.setAttribute("class", "region-frame");
            frame.setAttribute("data-region-frame", key);
            frame.setAttribute("d", pathFromGeometry(meta.feature.geometry, project));
            frameLayer.appendChild(frame);
        });
    });
    applyMapZoom();
}

function applyMapZoom() {
    if (!mapViewportGroup) return;
    const cx = 500;
    const cy = 390;
    mapViewportGroup.setAttribute("transform", `translate(${cx} ${cy}) scale(${mapZoom}) translate(${-cx} ${-cy})`);
}

function setupMapZoomControls() {
    const zoomIn = document.getElementById("map-zoom-in");
    const zoomOut = document.getElementById("map-zoom-out");
    const zoomReset = document.getElementById("map-zoom-reset");
    if (!zoomIn || !zoomOut || !zoomReset) return;
    zoomIn.addEventListener("click", () => {
        mapZoom = Math.min(1.8, Number((mapZoom + 0.12).toFixed(2)));
        applyMapZoom();
    });
    zoomOut.addEventListener("click", () => {
        mapZoom = Math.max(0.9, Number((mapZoom - 0.12).toFixed(2)));
        applyMapZoom();
    });
    zoomReset.addEventListener("click", () => {
        mapZoom = defaultMapZoom;
        applyMapZoom();
    });
}

regionButtons.forEach((button) => {
    button.addEventListener("click", () => {
        const toggleId = button.dataset.toggle;
        if (toggleId) {
            button.classList.toggle("expanded");
            const children = document.getElementById(toggleId);
            if (children) children.classList.toggle("expanded");
            const symbol = button.querySelector(".region-symbol");
            if (symbol) symbol.textContent = children?.classList.contains("expanded") ? "⌄" : "›";
        }
        selectRegion(button.dataset.region);
    });
});

function showProvinceTooltip(event, name) {
    const risk = provinceRisk[name] || "low";
    tooltip.innerHTML = `
        <div class="tooltip-title">${name}<span class="risk-dot ${risk}"></span></div>
        <div class="tooltip-sub">省级供应链视图</div>
        <div class="tooltip-row"><span>供应商</span><strong>${provinceSupplierCounts[name] || 0}</strong></div>
        <div class="tooltip-row"><span>风险等级</span><strong>${riskLabels[risk]}</strong></div>
    `;
    tooltip.classList.add("visible");
    positionTooltip(event);
}

function showRegionTooltip(event, data) {
    tooltip.innerHTML = `
        <div class="tooltip-title">${data.name}<span class="risk-dot ${data.overallRisk}"></span></div>
        <div class="tooltip-sub">${data.nameEn}</div>
        <div class="tooltip-row"><span>供应商</span><strong>${data.totalSuppliers}</strong></div>
        <div class="tooltip-row"><span>风险等级</span><strong>${riskLabels[data.overallRisk]}</strong></div>
    `;
    tooltip.classList.add("visible");
    positionTooltip(event);
}

function positionTooltip(event) {
    const rect = document.querySelector(".map-center").getBoundingClientRect();
    let x = event.clientX - rect.left + 16;
    let y = event.clientY - rect.top + 16;
    if (x + tooltip.offsetWidth > rect.width - 18) x -= tooltip.offsetWidth + 32;
    if (y + tooltip.offsetHeight > rect.height - 18) y -= tooltip.offsetHeight + 32;
    tooltip.style.left = `${x}px`;
    tooltip.style.top = `${y}px`;
}

function selectRegion(key) {
    activeRegionKey = key;
    selectedProvinceName = null;
    regionButtons.forEach((button) => button.classList.remove("active"));
    document.querySelectorAll(`.region-item[data-region="${key}"]`).forEach((item) => item.classList.add("active"));

    const provinceNames = mapRegionGroups[key] || [];
    const shouldDim = provinceNames.length > 0 && key !== "china";

    document.querySelectorAll(".province-path").forEach((path) => {
        const selected = provinceNames.includes(path.dataset.province);
        path.classList.toggle("highlighted", selected && key !== "china");
        path.classList.toggle("selected", selected && key !== "china");
        path.classList.toggle("dimmed", shouldDim && !selected);
    });
    document.querySelectorAll(".province-label").forEach((label) => {
        const selected = provinceNames.includes(label.dataset.provinceLabel);
        label.classList.toggle("highlighted", selected && key !== "china");
        label.classList.toggle("dimmed", shouldDim && !selected);
    });
    document.querySelectorAll(".region-frame").forEach((frame) => {
        frame.classList.toggle("active", frame.dataset.regionFrame === key);
    });

    renderDetailPanel(key);
}

function selectProvince(name) {
    const groupKey = Object.entries(mapRegionGroups).find(([key, names]) => key !== "china" && names.includes(name))?.[0] || "china";
    if (selectedProvinceName === name) {
        selectRegion("china");
        return;
    }
    activeRegionKey = groupKey;
    selectedProvinceName = name;
    const risk = provinceRisk[name] || "low";
    const supplierCount = provinceSupplierCounts[name] || 0;

    regionButtons.forEach((button) => button.classList.remove("active"));
    document.querySelectorAll(`.region-item[data-region="${groupKey}"]`).forEach((item) => item.classList.add("active"));
    document.querySelectorAll(".province-path").forEach((path) => {
        const isSelected = path.dataset.province === name;
        path.classList.toggle("selected", isSelected);
        path.classList.toggle("highlighted", isSelected);
        path.classList.toggle("dimmed", !isSelected);
    });
    document.querySelectorAll(".province-label").forEach((label) => {
        const isSelected = label.dataset.provinceLabel === name;
        label.classList.toggle("highlighted", isSelected);
        label.classList.toggle("dimmed", !isSelected);
    });
    document.querySelectorAll(".region-frame").forEach((frame) => {
        frame.classList.toggle("active", frame.dataset.regionFrame === groupKey);
    });

    renderProvinceDetailPanel(name, groupKey, risk, supplierCount);
}

function renderDetailPanel(key) {
    const data = regionsData[key];
    if (!data) return;

    const pct = data.overallRisk === "low" ? 28 : data.overallRisk === "med" ? 58 : data.overallRisk === "high" ? 82 : 95;
    const color = data.overallRisk === "low" ? "var(--green)" : data.overallRisk === "med" ? "var(--yellow)" : data.overallRisk === "high" ? "var(--orange)" : "var(--red)";
    const provinceCount = (mapRegionGroups[key] || data.provinces || []).length;

    document.getElementById("detail-panel").innerHTML = `
        <div class="detail-header">
            <div class="detail-title">${data.name} <span class="risk-text ${data.overallRisk}">${riskLabels[data.overallRisk]}</span></div>
            <div class="detail-subtitle">${data.nameEn}</div>
        </div>
        <div class="detail-section">
            <h2>概览</h2>
            <div class="detail-metric"><span>供应商</span><strong>${data.totalSuppliers}</strong></div>
            ${provinceCount ? `<div class="detail-metric"><span>省级单元</span><strong>${provinceCount}</strong></div>` : ""}
            <div class="detail-metric"><span>风险分</span><strong style="color:${color}">${pct}/100</strong></div>
            <div class="risk-bar"><div style="width:${pct}%; background:${color}"></div></div>
        </div>
        <div class="detail-section">
            <h2>关键因素</h2>
            <div class="pill-list">${data.keyFactors.map((factor) => `<span class="pill">${factor}</span>`).join("")}</div>
        </div>
        <div class="detail-section">
            <h2>重点供应商</h2>
            <div class="supplier-list">
                ${data.suppliers.map((supplier) => `
                    <div class="supplier-item" data-supplier="${supplier.name}" data-province="${supplier.province}">
                        <span class="risk-dot ${supplier.risk}"></span>
                        <div><div class="supplier-name">${supplier.name}</div><div class="supplier-province">${supplier.province}</div></div>
                        <div class="supplier-risk"><span class="risk-text ${supplier.risk}">${riskLabels[supplier.risk]}</span></div>
                    </div>
                `).join("")}
            </div>
        </div>
        <div class="header-actions">
            <button class="btn" type="button">查看全部</button>
            <button class="btn btn-primary" type="button">运行分析</button>
        </div>
    `;
}

function renderProvinceDetailPanel(name, groupKey, risk, supplierCount) {
    const group = regionsData[groupKey];
    const pct = risk === "low" ? 26 : risk === "med" ? 56 : risk === "high" ? 82 : 95;
    const color = risk === "low" ? "var(--green)" : risk === "med" ? "var(--yellow)" : risk === "high" ? "var(--orange)" : "var(--red)";
    document.getElementById("detail-panel").innerHTML = `
        <div class="detail-header">
            <div class="detail-title">${name} <span class="risk-text ${risk}">${riskLabels[risk]}</span></div>
            <div class="detail-subtitle">${group?.name || "省级视图"} / Province View</div>
        </div>
        <div class="detail-section">
            <h2>省份概览</h2>
            <div class="detail-metric"><span>供应商</span><strong>${supplierCount}</strong></div>
            <div class="detail-metric"><span>所属大区</span><strong>${group?.name || "-"}</strong></div>
            <div class="detail-metric"><span>风险分</span><strong style="color:${color}">${pct}/100</strong></div>
            <div class="risk-bar"><div style="width:${pct}%; background:${color}"></div></div>
        </div>
        <div class="detail-section">
            <h2>建议动作</h2>
            <div class="pill-list"><span class="pill">复核关键供应商</span><span class="pill">检查替代来源</span><span class="pill">更新合同条款</span></div>
        </div>
    `;
}

function openSupplierMenu(event, context = {}) {
    event.preventDefault();
    event.stopPropagation();
    if (!contextMenu) return;
    const menuWidth = 148;
    const menuHeight = 102;
    let x = event.clientX;
    let y = event.clientY;
    if (x + menuWidth > window.innerWidth - 8) x = window.innerWidth - menuWidth - 8;
    if (y + menuHeight > window.innerHeight - 8) y = window.innerHeight - menuHeight - 8;
    contextMenu.style.left = `${Math.max(8, x)}px`;
    contextMenu.style.top = `${Math.max(8, y)}px`;
    contextMenu.dataset.province = context.province || "";
    contextMenu.dataset.supplier = context.supplier || "";
    contextMenu.classList.add("open");
    contextMenu.setAttribute("aria-hidden", "false");
}

function closeSupplierMenu() {
    if (!contextMenu) return;
    contextMenu.classList.remove("open");
    contextMenu.setAttribute("aria-hidden", "true");
}

function setupSupplierContextMenu() {
    if (!contextMenu) return;
    contextMenu.addEventListener("click", (event) => {
        const button = event.target.closest("button[data-action]");
        if (!button) return;
        const action = button.dataset.action;
        const province = contextMenu.dataset.province;
        const supplier = contextMenu.dataset.supplier;
        const labels = { add: "添加供应商", edit: "编辑供应商", delete: "删除供应商" };
        console.info(`${labels[action]}: ${supplier || province || "供应链"}`);
        closeSupplierMenu();
    });
    document.addEventListener("click", closeSupplierMenu);
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") closeSupplierMenu();
    });
    document.getElementById("detail-panel").addEventListener("contextmenu", (event) => {
        const item = event.target.closest(".supplier-item");
        if (!item) return;
        openSupplierMenu(event, { supplier: item.dataset.supplier, province: item.dataset.province });
    });
}

async function fetchBackendJsonFrom(baseUrl, path, options = {}) {
    const timeoutMs = Number(options.timeoutMs || 0);
    const controller = timeoutMs ? new AbortController() : null;
    const timeoutId = controller ? window.setTimeout(() => controller.abort(), timeoutMs) : null;
    const { timeoutMs: _timeoutMs, ...fetchOptions } = options;
    const response = await fetch(`${baseUrl}${path}`, {
        ...fetchOptions,
        signal: controller?.signal || options.signal,
        headers: {
            Accept: "application/json",
            ...(fetchOptions.body ? { "Content-Type": "application/json" } : {}),
            ...(fetchOptions.headers || {}),
        },
    }).finally(() => {
        if (timeoutId) window.clearTimeout(timeoutId);
    });
    if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        const error = new Error(payload?.detail || payload?.error?.message || `${path} returned ${response.status}`);
        error.status = response.status;
        error.code = payload?.error?.code || null;
        error.payload = payload;
        throw error;
    }
    return response.json();
}

async function fetchBackendJson(path, options = {}) {
    const method = String(options.method || "GET").toUpperCase();
    if (supplyState?.source === "developer_debug" && method !== "GET" && !path.startsWith("/developer-debug/")) {
        throw new Error("workspace writes are locked while a developer debug scenario is active");
    }
    const fallbackBaseUrl = alternateLocalBackendBaseUrl(backendState.baseUrl);
    const primaryOptions = fallbackBaseUrl && Number(options.timeoutMs) > LOCAL_BACKEND_FAILOVER_TIMEOUT_MS
        ? { ...options, timeoutMs: LOCAL_BACKEND_FAILOVER_TIMEOUT_MS }
        : options;
    try {
        return await fetchBackendJsonFrom(backendState.baseUrl, path, primaryOptions);
    } catch (error) {
        if (!fallbackBaseUrl) throw error;
        const payload = await fetchBackendJsonFrom(fallbackBaseUrl, path, options);
        setWorkingBackendBaseUrl(fallbackBaseUrl);
        return payload;
    }
}

function alternateLocalBackendBaseUrl(baseUrl) {
    const normalized = normalizeBaseUrl(baseUrl);
    if (!LOCAL_BACKEND_BASE_URLS.includes(normalized)) return "";
    return LOCAL_BACKEND_BASE_URLS.find((candidate) => candidate !== normalized) || "";
}

function setWorkingBackendBaseUrl(baseUrl) {
    backendState.baseUrl = baseUrl;
    try {
        window.localStorage.setItem(BACKEND_BASE_URL_KEY, baseUrl);
    } catch {
        // Keep the working in-memory connection when local storage is unavailable.
    }
    try {
        const url = new URL(window.location.href);
        const requestedBaseUrl = normalizeBaseUrl(url.searchParams.get("api") || "");
        if (LOCAL_BACKEND_BASE_URLS.includes(requestedBaseUrl) && requestedBaseUrl !== baseUrl) {
            url.searchParams.set("api", baseUrl);
            window.history.replaceState({}, "", url);
        }
    } catch {
        // The active in-memory backend remains available when URL replacement fails.
    }
}

function settingElement(id) {
    return document.getElementById(id);
}

function setSettingsStatus(message, tone = "") {
    const status = settingElement("settings-form-status");
    if (!status) return;
    status.textContent = message;
    status.dataset.tone = tone;
}

function setSettingsSourceStatus(message, tone = "") {
    const status = settingElement("settings-source-status");
    if (!status) return;
    status.textContent = message;
    status.dataset.tone = tone;
}

function setSettingValue(id, value) {
    const input = settingElement(id);
    if (input) input.value = value ?? "";
}

function setSettingChecked(id, value) {
    const input = settingElement(id);
    if (input) input.checked = Boolean(value);
}

function runtimeFeedRow(feed, index) {
    const safe = (value) => escapeHtml(value ?? "");
    return `
        <div class="settings-feed-row" data-feed-index="${index}">
            <label><span>名称</span><input data-feed-field="name" maxlength="120" value="${safe(feed.name)}"></label>
            <label><span>类型</span><select data-feed-field="signal_type"><option value="news" ${feed.signal_type === "news" ? "selected" : ""}>新闻</option><option value="policy" ${feed.signal_type === "policy" ? "selected" : ""}>政策</option></select></label>
            <label><span>适配器</span><select data-feed-field="adapter"><option value="rss_atom" ${feed.adapter === "rss_atom" ? "selected" : ""}>RSS / Atom</option><option value="official_policy_html" ${feed.adapter === "official_policy_html" ? "selected" : ""}>政策网页</option><option value="cailianshe_telegraph" ${feed.adapter === "cailianshe_telegraph" ? "selected" : ""}>财联社电报</option><option value="yicai_homepage" ${feed.adapter === "yicai_homepage" ? "selected" : ""}>第一财经首页</option><option value="sina_futures_html" ${feed.adapter === "sina_futures_html" ? "selected" : ""}>新浪期货</option><option value="eastmoney_futures_html" ${feed.adapter === "eastmoney_futures_html" ? "selected" : ""}>东方财富期货</option><option value="futures_exchange_notice_html" ${feed.adapter === "futures_exchange_notice_html" ? "selected" : ""}>期货交易所公告</option></select></label>
            <label class="settings-feed-url"><span>HTTPS 地址</span><input data-feed-field="url" type="url" maxlength="1000" value="${safe(feed.url)}"></label>
            <label><span>关联度</span><input data-feed-field="risk_relevance" type="number" min="0.1" max="1" step="0.05" value="${safe(feed.risk_relevance)}"></label>
            <button class="settings-feed-remove" type="button" data-feed-remove="${index}" title="删除来源" aria-label="删除 ${safe(feed.name || "来源")}">
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 7l1-3h4l1 3"/><path d="M6 7l1 13h10l1-13"/></svg>
            </button>
            <input data-feed-field="feed_id" type="hidden" value="${safe(feed.feed_id)}">
        </div>`;
}

function renderRuntimeFeeds() {
    const list = settingElement("settings-feed-list");
    if (!list) return;
    list.innerHTML = runtimeSettingsState.feeds.length
        ? runtimeSettingsState.feeds.map(runtimeFeedRow).join("")
        : `<div class="empty-state settings-feed-empty">暂无 RSS 来源。添加来源后需选择与地址类型对应的适配器。</div>`;
}

function readRuntimeFeeds() {
    return Array.from(document.querySelectorAll(".settings-feed-row")).map((row) => {
        const value = (field) => row.querySelector(`[data-feed-field="${field}"]`)?.value?.trim() || "";
        return {
            feed_id: value("feed_id"),
            name: value("name"),
            signal_type: value("signal_type"),
            adapter: value("adapter"),
            url: value("url"),
            risk_relevance: Number(value("risk_relevance")),
        };
    });
}

function populateRuntimeSettings(data) {
    runtimeSettingsState.loaded = true;
    runtimeSettingsState.feeds = Array.isArray(data?.intelligence_feeds) ? data.intelligence_feeds : [];
    setSettingValue("settings-backend-url", backendState.baseUrl);
    setSettingValue("settings-llm-provider", data?.llm_provider || "openai_compatible");
    setSettingValue("settings-llm-preset", findLlmChannelPreset(data));
    setSettingValue("settings-llm-base-url", data?.llm_base_url);
    setSettingValue("settings-llm-model", data?.llm_model);
    setSettingChecked("settings-vision-llm-enabled", data?.vision_llm_enabled);
    setSettingValue("settings-vision-llm-base-url", data?.vision_llm_base_url);
    setSettingValue("settings-vision-llm-model", data?.vision_llm_model || "deepseek-v4-flash-vision-exp");
    syncLlmChannelControls();
    setSettingValue("settings-siliconflow-base-url", data?.siliconflow_base_url);
    setSettingValue("settings-embedding-model", data?.embedding_model);
    setSettingValue("settings-qdrant-host", data?.qdrant_host);
    setSettingValue("settings-qdrant-port", data?.qdrant_port);
    setSettingValue("settings-http-timeout", data?.external_risk_http_timeout_seconds);
    setSettingValue("settings-intelligence-poll-seconds", data?.external_risk_intelligence_poll_seconds);
    setSettingValue("settings-web-search-provider", data?.external_risk_web_search_provider);
    setSettingValue("settings-web-search-timeout", data?.external_risk_web_search_timeout_seconds);
    setSettingValue("settings-web-search-max-results", data?.external_risk_web_search_max_results);
    setSettingChecked("settings-live-enabled", data?.external_risk_live_enabled);
    setSettingChecked("settings-http-enabled", data?.external_risk_http_enabled);
    setSettingChecked("settings-akshare-enabled", data?.external_risk_akshare_enabled);
    setSettingChecked("settings-intelligence-enabled", data?.external_risk_intelligence_enabled);
    setSettingChecked("settings-intelligence-scheduler-enabled", data?.external_risk_intelligence_scheduler_enabled);
    setSettingChecked("settings-web-search-enabled", data?.external_risk_web_search_enabled);
    const llmKeyStatus = settingElement("settings-llm-key-status");
    const embeddingKeyStatus = settingElement("settings-siliconflow-key-status");
    const webSearchKeyStatus = settingElement("settings-web-search-key-status");
    const visionKeyStatus = settingElement("settings-vision-llm-key-status");
    if (llmKeyStatus) llmKeyStatus.textContent = data?.llm_api_key_configured ? "已配置" : "未配置";
    if (embeddingKeyStatus) embeddingKeyStatus.textContent = data?.siliconflow_api_key_configured ? "已配置" : "未配置";
    if (webSearchKeyStatus) webSearchKeyStatus.textContent = data?.external_risk_web_search_api_key_configured ? "已配置" : "未配置";
    if (visionKeyStatus) visionKeyStatus.textContent = data?.vision_llm_api_key_configured ? "已配置" : "未配置";
    const llmKey = settingElement("settings-llm-api-key");
    const embeddingKey = settingElement("settings-siliconflow-api-key");
    const webSearchKey = settingElement("settings-web-search-api-key");
    const visionKey = settingElement("settings-vision-llm-api-key");
    if (llmKey) llmKey.value = "";
    if (embeddingKey) embeddingKey.value = "";
    if (webSearchKey) webSearchKey.value = "";
    if (visionKey) visionKey.value = "";
    renderRuntimeFeeds();
}

async function loadRuntimeSettings() {
    if (!settingElement("runtime-settings-form")) return;
    setSettingsSourceStatus("正在读取后端配置");
    try {
        const payload = await fetchBackendJson("/settings/runtime", { timeoutMs: 10000 });
        populateRuntimeSettings(payload.data || {});
        setSettingsSourceStatus(`已连接 ${backendState.baseUrl}`, "success");
        if (!runtimeSettingsState.loaded) setSettingsStatus("");
    } catch (error) {
        runtimeSettingsState.loaded = false;
        setSettingsSourceStatus("未能读取后端配置", "error");
        setSettingsStatus(error.message || "读取配置失败", "error");
    }
}

function runtimeSettingsPayload() {
    const inputValue = (id) => String(settingElement(id)?.value || "").trim();
    const checked = (id) => Boolean(settingElement(id)?.checked);
    const payload = {
        llm_provider: inputValue("settings-llm-provider"),
        llm_base_url: inputValue("settings-llm-base-url"),
        llm_model: inputValue("settings-llm-model"),
        vision_llm_enabled: checked("settings-vision-llm-enabled"),
        vision_llm_base_url: inputValue("settings-vision-llm-base-url"),
        vision_llm_model: inputValue("settings-vision-llm-model"),
        siliconflow_base_url: inputValue("settings-siliconflow-base-url"),
        embedding_model: inputValue("settings-embedding-model"),
        qdrant_host: inputValue("settings-qdrant-host"),
        qdrant_port: Number(inputValue("settings-qdrant-port")),
        external_risk_live_enabled: checked("settings-live-enabled"),
        external_risk_http_enabled: checked("settings-http-enabled"),
        external_risk_akshare_enabled: checked("settings-akshare-enabled"),
        external_risk_http_timeout_seconds: Number(inputValue("settings-http-timeout")),
        external_risk_intelligence_enabled: checked("settings-intelligence-enabled"),
        external_risk_intelligence_poll_seconds: Number(inputValue("settings-intelligence-poll-seconds")),
        external_risk_intelligence_scheduler_enabled: checked("settings-intelligence-scheduler-enabled"),
        external_risk_web_search_enabled: checked("settings-web-search-enabled"),
        external_risk_web_search_provider: inputValue("settings-web-search-provider"),
        external_risk_web_search_timeout_seconds: Number(inputValue("settings-web-search-timeout")),
        external_risk_web_search_max_results: Number(inputValue("settings-web-search-max-results")),
        intelligence_feeds: readRuntimeFeeds(),
    };
    const llmApiKey = inputValue("settings-llm-api-key");
    const visionApiKey = inputValue("settings-vision-llm-api-key");
    const siliconflowApiKey = inputValue("settings-siliconflow-api-key");
    const webSearchApiKey = inputValue("settings-web-search-api-key");
    if (llmApiKey) payload.llm_api_key = llmApiKey;
    if (visionApiKey) payload.vision_llm_api_key = visionApiKey;
    if (siliconflowApiKey) payload.siliconflow_api_key = siliconflowApiKey;
    if (webSearchApiKey) payload.external_risk_web_search_api_key = webSearchApiKey;
    return payload;
}

function applyLlmChannelPreset(presetId) {
    const preset = LLM_CHANNEL_PRESETS[presetId];
    if (preset) {
        setSettingValue("settings-llm-provider", preset.provider);
        setSettingValue("settings-llm-base-url", preset.baseUrl);
        setSettingValue("settings-llm-model", preset.model);
    }
    syncLlmChannelControls();
    if (preset) setSettingsStatus("已填入当前渠道的推荐模型，可按账户权限自行覆盖。", "");
}

function findLlmChannelPreset(data) {
    const provider = String(data?.llm_provider || "openai_compatible").trim();
    const baseUrl = String(data?.llm_base_url || "").replace(/\/$/, "");
    return Object.entries(LLM_CHANNEL_PRESETS).find(([, preset]) => (
        preset.provider === provider && preset.baseUrl.replace(/\/$/, "") === baseUrl
    ))?.[0] || "custom";
}

function syncLlmChannelControls() {
    const presetId = settingElement("settings-llm-preset")?.value || "custom";
    const isCustom = presetId === "custom";
    const protocolControl = settingElement("settings-llm-protocol-control");
    const provider = settingElement("settings-llm-provider");
    if (protocolControl) protocolControl.hidden = !isCustom;
    if (provider) provider.disabled = !isCustom;
}

async function testConfiguredBackend() {
    const field = settingElement("settings-backend-url");
    const candidate = normalizeBaseUrl(field?.value || "");
    if (!/^https?:\/\//i.test(candidate)) {
        setSettingsStatus("请输入有效的后端地址", "error");
        return;
    }
    setSettingsStatus("正在测试连接");
    try {
        const health = await fetchBackendJsonFrom(candidate, "/health", { timeoutMs: 7000 });
        if (health?.status !== "ok") throw new Error("后端健康检查未通过");
        setWorkingBackendBaseUrl(candidate);
        setSettingValue("settings-backend-url", candidate);
        setSettingsSourceStatus(`已连接 ${candidate}`, "success");
        setSettingsStatus("连接成功，已切换到该后端", "success");
        await loadRuntimeSettings();
    } catch (error) {
        setSettingsStatus(error.message || "连接失败", "error");
    }
}

async function saveRuntimeSettings(event) {
    event?.preventDefault();
    const backendUrl = normalizeBaseUrl(settingElement("settings-backend-url")?.value || "");
    if (!/^https?:\/\//i.test(backendUrl)) {
        setSettingsStatus("请输入有效的后端地址", "error");
        return;
    }
    if (backendUrl !== backendState.baseUrl) {
        setSettingsStatus("请先测试新的后端地址，再保存服务端配置", "error");
        return;
    }
    const saveButton = settingElement("settings-save");
    if (saveButton) saveButton.disabled = true;
    setSettingsStatus("正在保存配置");
    try {
        const payload = await fetchBackendJson("/settings/runtime", {
            method: "PUT",
            body: JSON.stringify(runtimeSettingsPayload()),
            timeoutMs: 15000,
        });
        populateRuntimeSettings(payload.data || {});
        const restartNote = payload.restart_required ? " 后台定时同步开关将在重启后端后生效。" : "";
        setSettingsStatus(`配置已保存。${restartNote}`, "success");
        setSettingsSourceStatus(`已连接 ${backendState.baseUrl}`, "success");
    } catch (error) {
        setSettingsStatus(error.message || "保存失败", "error");
    } finally {
        if (saveButton) saveButton.disabled = false;
    }
}

async function refreshConfiguredRss() {
    const button = settingElement("settings-refresh-rss");
    if (button) button.disabled = true;
    setSettingsStatus("正在刷新 RSS 与政策来源");
    try {
        const payload = await fetchBackendJson("/external-risk/intelligence/refresh", { method: "POST", timeoutMs: 20000 });
        setSettingsStatus(`已刷新 ${Array.isArray(payload.items) ? payload.items.length : 0} 条可复核信号`, "success");
        void refreshExternalRiskDashboard();
    } catch (error) {
        setSettingsStatus(error.message || "RSS 刷新失败", "error");
    } finally {
        if (button) button.disabled = false;
    }
}

async function testConfiguredWebSearch() {
    const button = settingElement("settings-test-web-search");
    if (button) button.disabled = true;
    setSettingsStatus("正在测试联网检索");
    try {
        const payload = await fetchBackendJson("/external-risk/web-search", {
            method: "POST",
            body: JSON.stringify({
                question: "最新的数据出境监管政策",
                mode: "auto",
                domain: "legal",
                max_results: 3,
            }),
            timeoutMs: 20000,
        });
        const count = Array.isArray(payload.items) ? payload.items.length : 0;
        if (count) {
            setSettingsStatus(`联网检索可用，已获得 ${count} 条可复核来源`, "success");
        } else {
            setSettingsStatus(payload.error || "未获得可用来源", "error");
        }
    } catch (error) {
        setSettingsStatus(error.message || "联网检索测试失败", "error");
    } finally {
        if (button) button.disabled = false;
    }
}

function setupRuntimeSettings() {
    const form = settingElement("runtime-settings-form");
    if (!form) return;
    form.addEventListener("submit", saveRuntimeSettings);
    settingElement("settings-test-connection")?.addEventListener("click", testConfiguredBackend);
    settingElement("settings-llm-preset")?.addEventListener("change", (event) => {
        applyLlmChannelPreset(event.target.value);
    });
    settingElement("settings-llm-provider")?.addEventListener("change", () => syncLlmChannelControls());
    settingElement("settings-llm-base-url")?.addEventListener("change", () => {
        const presetId = settingElement("settings-llm-preset")?.value;
        const preset = LLM_CHANNEL_PRESETS[presetId];
        const baseUrl = String(settingElement("settings-llm-base-url")?.value || "").trim().replace(/\/$/, "");
        if (preset && preset.baseUrl.replace(/\/$/, "") !== baseUrl) {
            setSettingValue("settings-llm-preset", "custom");
            syncLlmChannelControls();
        }
    });
    settingElement("settings-refresh-rss")?.addEventListener("click", refreshConfiguredRss);
    settingElement("settings-test-web-search")?.addEventListener("click", testConfiguredWebSearch);
    settingElement("settings-add-feed")?.addEventListener("click", () => {
        runtimeSettingsState.feeds.push({
            feed_id: `intelligence-feed-${Date.now()}`,
            name: "新 RSS 来源",
            url: "https://",
            signal_type: "news",
            adapter: "rss_atom",
            risk_relevance: 1,
        });
        renderRuntimeFeeds();
    });
    settingElement("settings-feed-list")?.addEventListener("click", (event) => {
        const button = event.target.closest("[data-feed-remove]");
        if (!button) return;
        const index = Number(button.dataset.feedRemove);
        if (!Number.isInteger(index)) return;
        runtimeSettingsState.feeds.splice(index, 1);
        renderRuntimeFeeds();
    });
}

function skillItemsFromPayload(payload) {
    if (Array.isArray(payload)) return payload;
    const data = payload?.data || payload || {};
    return Array.isArray(data.items) ? data.items : Array.isArray(data.skills) ? data.skills : [];
}

function skillNodeTypesFromPayload(payload) {
    if (Array.isArray(payload)) return payload;
    const data = payload?.data || payload || {};
    if (Array.isArray(data.items)) return data.items;
    if (Array.isArray(data.node_types)) return data.node_types;
    const registry = data.node_types && typeof data.node_types === "object" ? data.node_types : data;
    return Object.entries(registry)
        .filter(([, definition]) => definition && typeof definition === "object" && !Array.isArray(definition))
        .map(([node_type, definition]) => ({ node_type, ...definition }));
}

function normalizeSkillNode(node, index = 0) {
    return {
        node_id: String(node?.node_id || `node-${index + 1}`),
        node_type: String(node?.node_type || ""),
        parameters: node?.parameters && typeof node.parameters === "object" ? node.parameters : {},
    };
}

function normalizeSkill(raw, index = 0) {
    const nodes = Array.isArray(raw?.nodes) ? raw.nodes : Array.isArray(raw?.workflow_nodes) ? raw.workflow_nodes : [];
    const protectedSkill = Boolean(raw?.protected || raw?.is_builtin || raw?.builtin || raw?.mutable === false);
    return {
        id: String(raw?.skill_id || raw?.id || raw?.key || `skill-${index + 1}`),
        name: String(raw?.name || raw?.title || `未命名技能 ${index + 1}`),
        description: String(raw?.description || raw?.summary || "暂无用途说明"),
        builtin: protectedSkill,
        nodes: nodes.map(normalizeSkillNode).filter((node) => node.node_type),
        raw,
    };
}

function normalizeSkillNodeType(raw, index = 0) {
    return {
        node_type: String(raw?.node_type || `node-type-${index + 1}`),
        name: String(raw?.name || raw?.label || raw?.title || raw?.node_type || `节点 ${index + 1}`),
        description: String(raw?.description || raw?.summary || "固定流程节点"),
        parameters: raw?.parameters && typeof raw.parameters === "object" ? raw.parameters : {},
    };
}

function skillNodeTypeMeta(nodeType) {
    return skillState.nodeTypes.find((item) => item.node_type === nodeType)
        || { node_type: nodeType, name: nodeType || "未知节点", description: "服务端返回的固定节点", parameters: {} };
}

function selectedSkill() {
    return skillState.skills.find((skill) => skill.id === skillState.selectedId) || null;
}

function setSkillsServiceStatus(message, tone = "") {
    const status = document.getElementById("skills-service-status");
    if (!status) return;
    status.textContent = message;
    status.className = `data-mode-badge${tone === "disabled" ? " disabled" : ""}`;
    if (tone && tone !== "disabled") status.dataset.tone = tone;
    else delete status.dataset.tone;
}

function setSkillEditorStatus(message, tone = "") {
    const status = document.getElementById("skill-editor-status");
    if (!status) return;
    status.textContent = message;
    status.dataset.tone = tone;
}

function renderSkills() {
    const list = document.getElementById("skills-list");
    const count = document.getElementById("skills-count");
    const empty = document.getElementById("skills-empty-state");
    const detail = document.getElementById("skills-detail");
    if (!list || !count || !empty || !detail) return;

    const createButton = document.getElementById("skills-create-button");
    if (createButton) {
        createButton.disabled = !skillState.serviceAvailable || !skillState.nodeTypesAvailable;
        createButton.title = createButton.disabled ? "连接技能服务并读取节点类型后可新建技能" : "新建技能";
    }

    count.textContent = String(skillState.skills.length);
    if (!skillState.serviceAvailable) {
        list.innerHTML = `<div class="skills-service-empty"><strong>技能服务暂不可用</strong><p>请确认后端已启动且提供 <code>/skills</code> 接口。此页面不会将技能写入浏览器本地缓存。</p></div>`;
        empty.hidden = false;
        empty.innerHTML = `<strong>等待技能服务</strong><p>连接恢复后可读取、编排、运行和保存技能。</p>`;
        detail.hidden = true;
        return;
    }

    if (!skillState.skills.length) {
        list.innerHTML = `<div class="skills-service-empty"><strong>暂无已保存技能</strong><p>可从右上角创建一个固定节点流程。</p></div>`;
        empty.hidden = false;
        empty.innerHTML = `<strong>新建第一个技能</strong><p>选择固定节点并排序，保存后即可在此输入问题运行。</p>`;
        detail.hidden = true;
        return;
    }

    if (!selectedSkill()) skillState.selectedId = skillState.skills[0].id;
    const active = selectedSkill();
    list.innerHTML = skillState.skills.map((skill) => `
        <button class="skill-list-item ${skill.id === active?.id ? "active" : ""}" type="button" data-skill-select="${escapeHtml(skill.id)}" aria-pressed="${skill.id === active?.id}">
            <span class="skill-list-item-main"><strong>${escapeHtml(skill.name)}</strong><small>${escapeHtml(skill.description)}</small></span>
            <span class="skill-kind-badge ${skill.builtin ? "builtin" : "custom"}">${skill.builtin ? "内置" : "自建"}</span>
        </button>`).join("");
    empty.hidden = true;
    detail.hidden = false;
    renderSkillDetail(active);
}

function renderSkillDetail(skill) {
    const detail = document.getElementById("skills-detail");
    if (!detail || !skill) return;
    const canEdit = !skill.builtin;
    const nodes = skill.nodes.length
        ? skill.nodes.map((node, index) => {
            const meta = skillNodeTypeMeta(node.node_type);
            return `<li><span class="skill-node-order">${index + 1}</span><div><strong>${escapeHtml(meta.name)}</strong><small>${escapeHtml(meta.description)}</small></div></li>`;
        }).join("")
        : `<li class="skill-node-empty">该技能尚未返回节点定义。</li>`;
    detail.innerHTML = `
        <div class="skills-detail-head">
            <div>
                <div class="skills-title-row"><h2>${escapeHtml(skill.name)}</h2><span class="skill-kind-badge ${skill.builtin ? "builtin" : "custom"}">${skill.builtin ? "内置技能" : "自建技能"}</span></div>
                <p>${escapeHtml(skill.description)}</p>
            </div>
            <div class="skills-detail-actions">
                <button class="btn" type="button" data-skill-edit ${canEdit ? "" : "disabled title=\"内置技能不可编辑\""}>编辑</button>
                <button class="icon-button skills-delete-button" type="button" data-skill-delete aria-label="删除技能" title="删除技能" ${canEdit ? "" : "disabled"}>
                    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 7l1-3h4l1 3"/><path d="M6 7l1 13h10l1-13"/></svg>
                </button>
            </div>
        </div>
        <section class="skills-detail-section">
            <div class="skills-section-label"><span class="metric-label">固定流程</span><span>${skill.nodes.length} 个节点</span></div>
            <ol class="skills-node-flow">${nodes}</ol>
        </section>
        <section class="skills-run-section">
            <div class="skills-section-label"><span class="metric-label">运行技能</span><span>仅通过服务端公开运行接口执行</span></div>
            <form id="skill-run-form" class="skill-run-form">
                <label><span>输入问题</span><textarea id="skill-run-question" rows="4" required placeholder="输入需要分析的问题或待审查事项"></textarea></label>
                <div class="skills-run-actions"><span id="skill-run-status" class="skill-run-status"></span><button class="btn btn-primary" type="submit">运行</button></div>
            </form>
            <div id="skill-run-result" class="skill-run-result" hidden></div>
        </section>`;
}

function renderSkillEditorNodeTypes() {
    const types = document.getElementById("skill-node-types");
    const selected = document.getElementById("skill-selected-nodes");
    const status = document.getElementById("skill-node-picker-status");
    if (!types || !selected || !status) return;
    const available = skillState.nodeTypes;
    const atLimit = skillState.draftNodes.length >= MAX_SKILL_NODES;
    status.textContent = skillState.nodeTypesAvailable
        ? `${available.length} 个可用固定节点 · 已选 ${skillState.draftNodes.length}/${MAX_SKILL_NODES}`
        : "节点类型服务不可用";
    types.innerHTML = available.length ? available.map((nodeType) => {
        const checked = skillState.draftNodes.some((node) => node.node_type === nodeType.node_type);
        const disabled = !checked && atLimit;
        return `<label class="skill-node-type ${checked ? "selected" : ""} ${disabled ? "disabled" : ""}"><input type="checkbox" data-skill-node-toggle="${escapeHtml(nodeType.node_type)}" ${checked ? "checked" : ""} ${disabled ? "disabled" : ""}><span><strong>${escapeHtml(nodeType.name)}</strong><small>${escapeHtml(nodeType.description)}</small></span></label>`;
    }).join("") : `<div class="skills-service-empty">暂未获得可编排的固定节点。</div>`;
    selected.innerHTML = skillState.draftNodes.length ? skillState.draftNodes.map((node, index) => {
        const meta = skillNodeTypeMeta(node.node_type);
        return `<li data-skill-draft-index="${index}"><span class="skill-node-order">${index + 1}</span><div><strong>${escapeHtml(meta.name)}</strong><small>${escapeHtml(meta.description)}</small></div><div class="skill-node-sort-actions"><button type="button" data-skill-node-move="up" data-skill-draft-index="${index}" aria-label="上移 ${escapeHtml(meta.name)}" title="上移" ${index === 0 ? "disabled" : ""}>↑</button><button type="button" data-skill-node-move="down" data-skill-draft-index="${index}" aria-label="下移 ${escapeHtml(meta.name)}" title="下移" ${index === skillState.draftNodes.length - 1 ? "disabled" : ""}>↓</button></div></li>`;
    }).join("") : `<li class="skill-node-empty">尚未选择节点。</li>`;
}

function defaultSkillDraftNodes() {
    const recommended = ["retrieve", "evidence_gate", "risk_analysis", "human_review", "report_output"];
    const selected = recommended.filter((nodeType) => skillState.nodeTypes.some((item) => item.node_type === nodeType));
    return selected.map((node_type, index) => ({ node_id: `${node_type}-${index + 1}`, node_type, parameters: {} }));
}

function openSkillEditor(skill = null) {
    const dialog = document.getElementById("skill-editor-dialog");
    if (!dialog) return;
    if (!skillState.serviceAvailable) {
        setSkillsServiceStatus("技能服务暂不可用", "disabled");
        return;
    }
    if (!skillState.nodeTypesAvailable) {
        setSkillsServiceStatus("节点类型不可用，暂不能编排", "disabled");
        return;
    }
    if (skill?.builtin) return;
    skillState.editingId = skill?.id || null;
    skillState.draftNodes = skill ? skill.nodes.map((node, index) => ({ ...node, node_id: node.node_id || `node-${index + 1}` })) : defaultSkillDraftNodes();
    document.getElementById("skill-editor-title").textContent = skill ? "编辑技能" : "新建技能";
    document.getElementById("skill-editor-name").value = skill?.name || "";
    document.getElementById("skill-editor-description").value = skill?.description || "";
    setSkillEditorStatus("");
    renderSkillEditorNodeTypes();
    if (typeof dialog.showModal === "function") dialog.showModal();
}

function closeSkillEditor() {
    const dialog = document.getElementById("skill-editor-dialog");
    if (dialog?.open) dialog.close();
    skillState.editingId = null;
    skillState.draftNodes = [];
}

function buildSkillPayload() {
    const name = String(document.getElementById("skill-editor-name")?.value || "").trim();
    const description = String(document.getElementById("skill-editor-description")?.value || "").trim();
    const nodes = skillState.draftNodes.map((node, index) => ({
        node_id: node.node_id || `${node.node_type}-${index + 1}`,
        node_type: node.node_type,
        parameters: node.parameters || {},
    }));
    return {
        name,
        description,
        nodes,
        edges: nodes.slice(1).map((node, index) => ({ source: nodes[index].node_id, target: node.node_id })),
    };
}

function skillValidationMessage(payload) {
    const result = payload?.data || payload || {};
    const errors = Array.isArray(result.errors) ? result.errors : Array.isArray(result.issues) ? result.issues : [];
    if (result.valid === false || errors.length) return errors.length ? errors.map((error) => typeof error === "string" ? error : error.message || JSON.stringify(error)).join("；") : "流程校验未通过";
    return result.message || "流程校验通过";
}

async function validateSkillDraft() {
    const button = document.getElementById("skill-editor-validate");
    const payload = buildSkillPayload();
    if (!payload.name) {
        setSkillEditorStatus("请填写技能名称", "error");
        return false;
    }
    if (!payload.nodes.length) {
        setSkillEditorStatus("请至少选择一个固定节点", "error");
        return false;
    }
    if (payload.nodes.length > MAX_SKILL_NODES) {
        setSkillEditorStatus(`每个技能最多选择 ${MAX_SKILL_NODES} 个节点`, "error");
        return false;
    }
    if (button) button.disabled = true;
    setSkillEditorStatus("正在校验流程");
    try {
        const response = await fetchBackendJson("/skills/validate", { method: "POST", body: JSON.stringify(payload), timeoutMs: 10000 });
        const message = skillValidationMessage(response);
        const validation = response?.data || response || {};
        const errors = Array.isArray(validation.errors) ? validation.errors : Array.isArray(validation.issues) ? validation.issues : [];
        const valid = validation.valid !== false && errors.length === 0;
        setSkillEditorStatus(message, valid ? "success" : "error");
        return valid;
    } catch (error) {
        setSkillEditorStatus(error.message || "流程校验服务暂不可用", "error");
        return false;
    } finally {
        if (button) button.disabled = false;
    }
}

async function saveSkillDraft(event) {
    event.preventDefault();
    const saveButton = document.getElementById("skill-editor-save");
    const payload = buildSkillPayload();
    if (!payload.name || !payload.nodes.length) {
        setSkillEditorStatus(!payload.name ? "请填写技能名称" : "请至少选择一个固定节点", "error");
        return;
    }
    if (payload.nodes.length > MAX_SKILL_NODES) {
        setSkillEditorStatus(`每个技能最多选择 ${MAX_SKILL_NODES} 个节点`, "error");
        return;
    }
    if (saveButton) saveButton.disabled = true;
    setSkillEditorStatus("正在保存技能");
    try {
        const path = skillState.editingId ? `/skills/${encodeURIComponent(skillState.editingId)}` : "/skills";
        const response = await fetchBackendJson(path, { method: skillState.editingId ? "PATCH" : "POST", body: JSON.stringify(payload), timeoutMs: 12000 });
        const saved = response?.data || response?.item || response?.skill || response;
        const savedId = saved?.skill_id || saved?.id || skillState.editingId;
        closeSkillEditor();
        await loadSkills({ force: true, selectedId: savedId });
        setSkillsServiceStatus("技能已保存", "success");
    } catch (error) {
        setSkillEditorStatus(error.message || "保存失败，技能未写入", "error");
    } finally {
        if (saveButton) saveButton.disabled = false;
    }
}

async function deleteSelectedSkill() {
    const skill = selectedSkill();
    if (!skill || skill.builtin) return;
    if (!window.confirm(`删除“${skill.name}”后无法恢复，是否继续？`)) return;
    const deleteButton = document.querySelector("[data-skill-delete]");
    if (deleteButton) deleteButton.disabled = true;
    try {
        await fetchBackendJson(`/skills/${encodeURIComponent(skill.id)}`, { method: "DELETE", timeoutMs: 10000 });
        skillState.selectedId = null;
        await loadSkills({ force: true });
        setSkillsServiceStatus("技能已删除", "success");
    } catch (error) {
        if (deleteButton) deleteButton.disabled = false;
        setSkillsServiceStatus(error.message || "删除失败", "error");
    }
}

function presentSkillRunResult(payload) {
    const result = document.getElementById("skill-run-result");
    if (!result) return;
    const data = payload?.data || payload || {};
    const output = data.result ?? data.output ?? data.answer ?? data.markdown ?? payload;
    const plan = Array.isArray(data.execution_plan) ? data.execution_plan : [];
    result.hidden = false;
    const outputText = typeof output === "string" ? output : JSON.stringify(output, null, 2);
    result.textContent = plan.length ? `${outputText}\n\n执行计划\n${plan.map((node, index) => `${index + 1}. ${node?.node_type || String(node)}`).join("\n")}` : outputText;
}

async function runSelectedSkill(event) {
    event.preventDefault();
    const skill = selectedSkill();
    const question = String(document.getElementById("skill-run-question")?.value || "").trim();
    const status = document.getElementById("skill-run-status");
    const button = document.querySelector("#skill-run-form button[type=submit]");
    if (!skill || !question || !status) return;
    if (button) button.disabled = true;
    status.textContent = "运行中";
    status.dataset.tone = "";
    try {
        const payload = await fetchBackendJson(`/skills/${encodeURIComponent(skill.id)}/run`, { method: "POST", body: JSON.stringify({ question }), timeoutMs: 60000 });
        presentSkillRunResult(payload);
        status.textContent = "运行完成";
        status.dataset.tone = "success";
    } catch (error) {
        status.textContent = error.message || "运行失败，技能服务暂不可用";
        status.dataset.tone = "error";
    } finally {
        if (button) button.disabled = false;
    }
}

async function loadSkills({ force = false, selectedId = null } = {}) {
    if (skillState.loading || (skillState.loaded && !force)) return;
    skillState.loading = true;
    setSkillsServiceStatus("正在读取技能服务");
    try {
        const [skillResponse, nodeTypeResponse] = await Promise.allSettled([
            fetchBackendJson("/skills", { timeoutMs: 10000 }),
            fetchBackendJson("/skills/node-types", { timeoutMs: 10000 }),
        ]);
        if (skillResponse.status !== "fulfilled") throw skillResponse.reason;
        skillState.skills = skillItemsFromPayload(skillResponse.value).map(normalizeSkill);
        skillState.serviceAvailable = true;
        skillState.nodeTypesAvailable = nodeTypeResponse.status === "fulfilled";
        skillState.nodeTypes = skillState.nodeTypesAvailable ? skillNodeTypesFromPayload(nodeTypeResponse.value).map(normalizeSkillNodeType).filter((nodeType) => nodeType.node_type) : [];
        skillState.loaded = true;
        skillState.selectedId = selectedId && skillState.skills.some((skill) => skill.id === String(selectedId)) ? String(selectedId) : skillState.selectedId;
        setSkillsServiceStatus(skillState.nodeTypesAvailable ? `已连接 · ${skillState.skills.length} 个技能` : "技能已读取，节点类型暂不可用", skillState.nodeTypesAvailable ? "success" : "disabled");
    } catch (error) {
        skillState.loaded = false;
        skillState.serviceAvailable = false;
        skillState.nodeTypesAvailable = false;
        skillState.skills = [];
        skillState.nodeTypes = [];
        skillState.selectedId = null;
        setSkillsServiceStatus("技能服务暂不可用", "disabled");
        console.info(error);
    } finally {
        skillState.loading = false;
        renderSkills();
    }
}

function setupSkillsWorkspace() {
    document.getElementById("skills-refresh-button")?.addEventListener("click", () => void loadSkills({ force: true }));
    document.getElementById("skills-create-button")?.addEventListener("click", () => openSkillEditor());
    document.getElementById("skills-list")?.addEventListener("click", (event) => {
        const item = event.target.closest("[data-skill-select]");
        if (!item) return;
        skillState.selectedId = item.dataset.skillSelect;
        renderSkills();
    });
    document.getElementById("skills-detail")?.addEventListener("click", (event) => {
        if (event.target.closest("[data-skill-edit]")) openSkillEditor(selectedSkill());
        if (event.target.closest("[data-skill-delete]")) void deleteSelectedSkill();
    });
    document.getElementById("skills-detail")?.addEventListener("submit", (event) => {
        if (event.target.matches("#skill-run-form")) void runSelectedSkill(event);
    });
    document.getElementById("skill-editor-close")?.addEventListener("click", closeSkillEditor);
    document.getElementById("skill-editor-cancel")?.addEventListener("click", closeSkillEditor);
    document.getElementById("skill-editor-form")?.addEventListener("submit", (event) => void saveSkillDraft(event));
    document.getElementById("skill-editor-validate")?.addEventListener("click", () => void validateSkillDraft());
    document.getElementById("skill-node-types")?.addEventListener("change", (event) => {
        const input = event.target.closest("[data-skill-node-toggle]");
        if (!input) return;
        const type = input.dataset.skillNodeToggle;
        if (input.checked) {
            if (skillState.draftNodes.length >= MAX_SKILL_NODES) {
                input.checked = false;
                setSkillEditorStatus(`每个技能最多选择 ${MAX_SKILL_NODES} 个节点；请先取消一个已选节点。`, "error");
                renderSkillEditorNodeTypes();
                return;
            }
            skillState.draftNodes.push({ node_id: `${type}-${skillState.draftNodes.length + 1}`, node_type: type, parameters: {} });
        } else {
            skillState.draftNodes = skillState.draftNodes.filter((node) => node.node_type !== type);
        }
        renderSkillEditorNodeTypes();
    });
    document.getElementById("skill-selected-nodes")?.addEventListener("click", (event) => {
        const button = event.target.closest("[data-skill-node-move]");
        if (!button) return;
        const index = Number(button.dataset.skillDraftIndex);
        const direction = button.dataset.skillNodeMove === "up" ? -1 : 1;
        const target = index + direction;
        if (!Number.isInteger(index) || target < 0 || target >= skillState.draftNodes.length) return;
        [skillState.draftNodes[index], skillState.draftNodes[target]] = [skillState.draftNodes[target], skillState.draftNodes[index]];
        renderSkillEditorNodeTypes();
    });
}

async function fetchBackendStream(path, options = {}, handlers = {}) {
    const candidates = [backendState.baseUrl, ...LOCAL_BACKEND_BASE_URLS]
        .map(normalizeBaseUrl)
        .filter((baseUrl, index, values) => baseUrl && values.indexOf(baseUrl) === index);
    let lastError = null;
    for (const baseUrl of candidates) {
        try {
            await fetchBackendStreamFrom(baseUrl, path, options, handlers);
            if (baseUrl !== backendState.baseUrl) setWorkingBackendBaseUrl(baseUrl);
            return baseUrl;
        } catch (error) {
            lastError = error;
        }
    }
    throw lastError || new Error(`${path} unavailable`);
}

async function fetchBackendStreamFrom(baseUrl, path, options = {}, handlers = {}) {
    const response = await fetch(`${baseUrl}${path}`, {
        ...options,
        headers: {
            Accept: "text/event-stream",
            ...(options.body ? { "Content-Type": "application/json" } : {}),
            ...(options.headers || {}),
        },
    });
    if (!response.ok || !response.body) throw new Error(`${path} returned ${response.status}`);

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    const dispatchBlock = (block) => {
        const lines = block.split(/\r?\n/);
        let eventName = "message";
        const dataLines = [];
        lines.forEach((line) => {
            if (line.startsWith("event:")) eventName = line.slice(6).trim();
            else if (line.startsWith("data:")) dataLines.push(line.slice(5).trimStart());
        });
        if (!dataLines.length) return;
        const payload = JSON.parse(dataLines.join("\n"));
        handlers[eventName]?.(payload);
    };

    while (true) {
        const { value, done } = await reader.read();
        buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
        const blocks = buffer.split(/\r?\n\r?\n/);
        buffer = blocks.pop() || "";
        blocks.forEach(dispatchBlock);
        if (done) break;
    }
    if (buffer.trim()) dispatchBlock(buffer);
}

async function loadBackendProductData() {
    renderBackendStatus("loading", "连接后端中");
    const endpoints = {
        dashboard: "/product/dashboard/summary",
        legalWorkspace: "/product/legal/workspace",
        lifecycleRisk: "/product/lifecycle/risk",
        risks: "/product/risks",
        externalRiskDashboard: "/external-risk/market-dashboard",
    };
    const fastResults = await Promise.allSettled(
        Object.entries(endpoints)
            .filter(([key]) => key !== "externalRiskDashboard")
            .map(async ([key, path]) => [key, await fetchBackendJson(path, { timeoutMs: 8000 })])
    );
    const externalRiskResult = fetchBackendJson(endpoints.externalRiskDashboard, { timeoutMs: 12000 })
        .then((payload) => {
            if (supplyState.source === "developer_debug") return;
            backendState.product.externalRiskDashboard = payload;
            applyExternalRiskDashboardData(payload.data, payload.meta);
            renderBackendStatus("online", `后端已连接 · ${externalDataSourceLabel(payload.meta?.data_source || "external-risk")}`);
        })
        .catch((error) => {
            console.info(error);
            const mode = document.getElementById("external-risk-mode");
            if (mode) {
                mode.textContent = "实时行情暂不可用";
                mode.className = "data-mode-badge disabled";
            }
        });

    const product = {};
    fastResults.forEach((result) => {
        if (result.status === "fulfilled") {
            const [key, payload] = result.value;
            product[key] = payload;
        }
    });

    if (!Object.keys(product).length) {
        backendState.connected = false;
        renderBackendStatus("offline", "静态数据");
        console.info(`Product backend unavailable: ${backendState.baseUrl}`);
        return;
    }

    if (supplyState.source === "developer_debug") return;
    backendState.connected = true;
    backendState.product = product;
    applyBackendProductData(product);
    const source = getProductMeta(product)?.data_source || "backend";
    renderBackendStatus("online", `后端已连接 · ${externalDataSourceLabel(source)}`);
    window.setTimeout(() => refreshWorkflowQuotes(), 1200);
    // Do not leave the initial market panel on its fixture fallback while the
    // real dashboard request is still resolving.  Awaiting keeps the first
    // rendered data-boundary labels consistent with the visible signals.
    await externalRiskResult;
}

const internalRiskDomainLabels = {
    data_model_governance: "数据与模型治理",
    technology_ip: "技术与知识资产",
    product_commercialization: "产品商业化",
    cross_border_supply_chain: "跨境与供应链",
    corporate_finance_governance: "公司治理与科技金融",
};

const internalRiskStageLabels = {
    establishment: "设立与治理",
    research_and_development: "研发与验证",
    market_access: "市场准入与客户导入",
    market_expansion: "规模扩张与客户导入",
    commercialization: "商业化与质量交付",
    financing: "融资与税务治理",
    scale_expansion: "规模扩张与市场竞争",
    strategic_adjustment: "退出/战略调整与供应链韧性",
    exit: "退出安排",
    project_initiation: "项目立项",
    data_access: "数据接入",
    model_training: "模型训练",
    product_launch: "产品上线",
    commercialization: "商业化",
    cross_border: "跨境协作",
};

const internalGateDecisionLabels = {
    approved: "可以进入下一阶段",
    conditional_approval: "补齐材料后，可提交下一阶段决策",
    rectification_required: "需补齐材料并完成整改",
    suspended: "暂缓推进",
};

const internalTaskStatusLabels = {
    not_started: "待开始",
    in_progress: "整改中",
    blocked: "受阻",
    pending_review: "待复核",
    verified: "已验证",
};

const internalReviewStatusLabels = {
    pending: "待复核",
    approved: "已确认",
    changes_requested: "退回整改",
    rejected: "未通过",
};

const internalRiskFilters = {
    level: "all",
    stage: "all",
};

const internalInboxState = {
    stage: "intake",
    selectedType: null,
    selectedId: null,
    initialized: false,
};

const internalEvidenceDocuments = {
    items: [],
    loaded: false,
    loading: null,
    available: true,
};

function internalRiskLevelClass(level) {
    if (!String(level || "").trim()) return "pending";
    return normalizeRiskLevel(level);
}

function internalRiskSummary(workflow) {
    const risks = workflow?.risk_items || [];
    const gates = workflow?.gates || [];
    const tasks = workflow?.remediation_tasks || [];
    const reviews = workflow?.manual_reviews || [];
    return {
        highRisks: risks.filter((risk) => ["high", "critical"].includes(risk.risk_level) && risk.status !== "closed").length,
        gated: gates.filter((gate) => ["rectification_required", "suspended"].includes(gate.decision)).length,
        pendingTasks: tasks.filter((task) => task.status !== "verified").length,
        pendingReviews: reviews.filter((review) => review.status === "pending").length,
    };
}

function renderRiskGovernanceDashboard(workflow) {
    if (!workflow) return;
    const summary = internalRiskSummary(workflow);
    const intakeCases = backendState.riskIntake?.cases || [];
    const pendingIntake = intakeCases.filter((item) => item.status === "pending_triage");
    const managementAssistance = workflow.management_assistance || { suggestions: [], reminders: [] };
    const pendingSuggestions = managementAssistance.suggestions.filter((item) => item.status === "pending");
    const activeReminders = managementAssistance.reminders.filter((item) => item.status === "active");
    const highRisk = summary.highRisks > 0 || summary.gated > 0;
    const label = document.querySelector(".score-main .metric-label");
    const value = document.querySelector(".score-value");
    const trend = document.querySelector(".score-trend");
    if (label) label.textContent = "综合风险状态";
    if (value) value.innerHTML = `<span class="score-status ${highRisk ? "high" : "low"}">${highRisk ? "需要优先处理" : "持续关注"}</span>`;
    if (trend) trend.innerHTML = `<span class="risk-dot ${highRisk ? "high" : "low"}"></span>根据风险清单、关键决策点和待核实外部信息汇总；资料不足时不显示风险分数。`;

    const dimensions = document.querySelector(".score-dimensions");
    if (dimensions) {
        dimensions.innerHTML = [
            ["高风险事项", summary.highRisks, "需要优先处理"],
            ["待处理决策点", summary.gated, "需要负责人决定后再推进"],
            ["待办整改", summary.pendingTasks, "责任与期限已绑定"],
            ["外部待核实", pendingIntake.length, "尚未计入企业风险"],
            ["处理建议", pendingSuggestions.length, "采纳后才会创建整改任务"],
            ["时限提醒", activeReminders.length, "仅提示，不自动变更状态"],
        ].map(([metric, count, note]) => `<div class="dimension-card"><span>${metric}</span><strong>${count}</strong><div class="metric-unit">${note}</div></div>`).join("");
    }

    const activeRisks = (workflow.risk_items || []).filter((risk) => risk.status !== "closed");
    const alertList = document.querySelector(".alert-list");
    const alertCount = document.querySelector(".dashboard-left .section-heading span");
    if (alertList) {
        const alertItems = [
            ...activeRisks.map((risk) => ({
                title: displayLifecycleRiskTitle(risk),
                message: (risk.trigger_facts || ["等待补充触发事实"])[0],
                level: normalizeRiskLevel(risk.risk_level),
            })),
            ...pendingIntake.map((item) => ({
                title: `待核实：${item.signal.title}`,
                message: `已关联 ${item.matched_objects.length} 个企业对象，等待人工确认后决定是否登记为风险线索。`,
                level: normalizeRiskLevel(item.signal.severity),
            })),
            ...activeReminders.map((item) => ({
                title: item.title,
                message: item.detail,
                level: item.reminder_type === "overdue" ? "high" : "med",
            })),
        ].slice(0, 5);
        alertList.innerHTML = alertItems.length
            ? alertItems.map((item) => `<article class="alert-row"><span class="risk-dot ${item.level}"></span><div><strong>${escapeHtml(item.title)}</strong><p>${escapeHtml(item.message)}</p></div><span class="risk-text ${item.level}">${riskLabels[item.level]}</span></article>`).join("")
            : '<div class="empty-state">当前没有已确认的风险事项；外部信息必须关联企业对象并经人工核实后，才进入后续处理。</div>';
        if (alertCount) alertCount.textContent = `${alertItems.length} 项`;
    }

    const taskList = document.querySelector(".task-list");
    const taskCount = document.querySelector(".dashboard-right .section-heading span");
    const openTasks = (workflow.remediation_tasks || []).filter((task) => task.status !== "verified").slice(0, 5);
    if (taskList) taskList.innerHTML = openTasks.length
        ? openTasks.map((task) => `<div class="task-item"><span>${escapeHtml(displayLifecycleCheckTitle(task.title))}</span><strong>${escapeHtml(formatInternalDate(task.due_date))}</strong></div>`).join("")
        : '<div class="empty-state">当前没有待办整改任务。</div>';
    if (taskCount) taskCount.textContent = `${openTasks.length} 项`;

    const sourceSummary = document.getElementById("dashboard-source-summary");
    const sourceList = document.getElementById("dashboard-source-list");
    const scope = backendState.riskIntake?.scope;
    const latestSync = backendState.riskIntake?.syncBatches?.[0];
    const internalSource = backendState.internalRisk?.meta?.data_source;
    const externalSourceStatus = !backendState.riskIntake
        ? "未接入"
        : !latestSync
            ? `${pendingIntake.length} 条待核实；尚无同步记录`
            : latestSync.source_health?.status === "healthy"
                ? `最近同步 ${formatInternalDate(latestSync.completed_at)}；${latestSync.new_case_count} 条新增待核实`
                : latestSync.source_health?.status === "stale"
                    ? `最近信息已过期；本次未新增线索`
                    : `来源更新失败；保留历史信息，不新增线索`;
    const sourceRows = [
        ["企业风险清单", internalSource === "fixture_sample" ? "演示数据，非实时连接" : "来源状态未声明"],
        ["企业范围与生命周期", scope ? `演示范围已加载 · ${formatInternalDate(scope.updated_at)}` : "未接入"],
        ["外部风险线索", externalSourceStatus],
    ];
    if (sourceSummary) sourceSummary.textContent = "按已加载资料展示";
    if (sourceList) sourceList.innerHTML = sourceRows.map(([name, status]) =>
        `<div class="status-row"><span>${escapeHtml(name)}</span><strong>${escapeHtml(status)}</strong></div>`
    ).join("");
}

function filteredInternalRiskWorkflow(workflow) {
    const allRisks = workflow?.risk_items || [];
    const allGates = workflow?.gates || [];
    const allTasks = workflow?.remediation_tasks || [];
    const allReviews = workflow?.manual_reviews || [];
    const risks = allRisks.filter((risk) => {
        const stageMatches = internalRiskFilters.stage === "all" || risk.lifecycle_stage === internalRiskFilters.stage;
        const levelMatches = internalRiskFilters.level === "all"
            || (internalRiskFilters.level === "high" && ["high", "critical"].includes(risk.risk_level))
            || (internalRiskFilters.level === "open" && risk.status !== "closed");
        return stageMatches && levelMatches;
    });
    const riskIds = new Set(risks.map((risk) => risk.risk_id));
    const gates = allGates.filter((gate) => gate.risk_item_ids.some((riskId) => riskIds.has(riskId)));
    const tasks = allTasks.filter((task) => riskIds.has(task.risk_id));
    const reviewTargetIds = new Set([
        ...risks.map((risk) => risk.risk_id),
        ...gates.map((gate) => gate.gate_id),
        ...tasks.map((task) => task.task_id),
    ]);
    const reviews = allReviews.filter((review) => reviewTargetIds.has(review.target_id));
    return { risks, gates, tasks, reviews };
}

function updateInternalWorkbenchTitle({ risks, tasks }) {
    const title = document.getElementById("internal-workbench-title");
    if (!title) return;
    const labels = [];
    if (internalRiskFilters.level === "high") labels.push("高风险及以上");
    if (internalRiskFilters.level === "open") labels.push("待处置事项");
    if (internalRiskFilters.stage !== "all") labels.push(internalRiskStageLabels[internalRiskFilters.stage] || internalRiskFilters.stage);
    title.textContent = labels.length ? labels.join(" · ") : "全部风险事项";
    title.title = `当前显示 ${risks.length} 项风险、${tasks.length} 项整改任务`;
}

function internalReviewTargetTitle(review, risks, gates, tasks) {
    if (review.target_type === "risk_gate") {
        return gates.find((gate) => gate.gate_id === review.target_id)?.title || review.target_id;
    }
    if (review.target_type === "remediation_task") {
        return tasks.find((task) => task.task_id === review.target_id)?.title || review.target_id;
    }
    return risks.find((risk) => risk.risk_id === review.target_id)?.title || review.target_id;
}

function classifyInternalReviews(reviews, tasks) {
    const tasksById = new Map(tasks.map((task) => [task.task_id, task]));
    const pending = reviews.filter((review) => review.status === "pending");
    return {
        queue: pending.filter((review) => review.target_type !== "remediation_task" || tasksById.get(review.target_id)?.status === "pending_review"),
        waiting: pending.filter((review) => review.target_type === "remediation_task" && tasksById.get(review.target_id)?.status !== "pending_review"),
        history: reviews.filter((review) => review.status !== "pending"),
        tasksById,
    };
}

function formatInternalDate(value) {
    if (!value) return "未设置期限";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return escapeHtml(value);
    return `${date.getMonth() + 1}月${date.getDate()}日`;
}

function formatExternalTimestamp(value) {
    if (!value) return "未记录";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    return new Intl.DateTimeFormat("zh-CN", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false,
    }).format(date).replace(/\//g, "-");
}

function renderInternalRiskDashboard(workflow) {
    const strip = document.getElementById("internal-dashboard-strip");
    const metrics = document.getElementById("internal-dashboard-metrics");
    const badge = document.getElementById("internal-risk-nav-badge");
    if (!strip || !metrics || !workflow) return;
    const summary = internalRiskSummary(workflow);
    metrics.innerHTML = [
        ["高风险事项", summary.highRisks, "需要优先核验"],
        ["暂不满足准入条件", summary.gated, "完成整改后再决定"],
        ["待办整改", summary.pendingTasks, "责任人与期限已绑定"],
        ["待人工复核", summary.pendingReviews, "系统不会自动确认"],
    ].map(([label, value, note]) => `
        <div class="internal-strip-metric"><span>${label}</span><strong>${value}</strong><small>${note}</small></div>
    `).join("");
    if (badge) {
        badge.textContent = String(summary.highRisks + summary.pendingReviews);
        badge.classList.toggle("dismissed", summary.highRisks + summary.pendingReviews === 0);
    }
    strip.classList.remove("is-unavailable");
}

function internalRiskClosureBlockers(risk, workflow) {
    const relatedTasks = (workflow.remediation_tasks || []).filter((task) => task.risk_id === risk.risk_id);
    const relatedGates = (workflow.gates || []).filter((gate) => (gate.risk_item_ids || []).includes(risk.risk_id));
    const reviewsById = new Map((workflow.manual_reviews || []).map((review) => [review.review_id, review]));
    return [
        ...relatedTasks.filter((task) => task.status !== "verified").map((task) => `整改未完成：${task.title}`),
        ...relatedTasks.filter((task) => task.requires_manual_review && reviewsById.get(task.review_id)?.status !== "approved").map((task) => `整改复核未确认：${task.title}`),
        ...relatedGates.filter((gate) => gate.decision !== "approved").map((gate) => `尚未确认是否可进入下一阶段：${gate.title}`),
    ];
}

function buildInternalInbox(workflow, filtered) {
    const { risks, gates, tasks, reviews } = filtered;
    const riskById = new Map(risks.map((risk) => [risk.risk_id, risk]));
    const reviewGroups = classifyInternalReviews(reviews, tasks);
    const events = (workflow.risk_events || []).filter((event) => {
        const stageMatches = internalRiskFilters.stage === "all" || event.lifecycle_stage === internalRiskFilters.stage;
        const suggestedLevel = event.assessment_snapshot?.report?.risk_level;
        const levelMatches = internalRiskFilters.level === "all"
            || (internalRiskFilters.level === "open" && !["confirmed", "rejected"].includes(event.status))
            || (internalRiskFilters.level === "high" && ["high", "critical"].includes(suggestedLevel));
        return stageMatches && levelMatches;
    });
    const materials = [
        ...gates.filter((gate) => (gate.checks || []).some((check) => check.status === "missing")).map((gate) => ({
            kind: "gate", id: gate.gate_id, title: gate.title,
            status: `${(gate.checks || []).filter((check) => check.status === "missing").length} 项待补`,
            context: `${internalRiskStageLabels[gate.lifecycle_stage] || gate.lifecycle_stage} · ${gate.owner}`,
            action: "查看要求", priority: "high", updatedAt: "先补材料",
        })),
        ...tasks.filter((task) => task.status === "blocked" || (task.status === "in_progress" && !(task.evidence_refs || []).length)).map((task) => ({
            kind: "task", id: task.task_id, title: task.title,
            status: task.status === "blocked" ? "处理受阻" : "材料未关联",
            context: riskById.get(task.risk_id)?.title || task.risk_id,
            action: "补充材料", priority: task.status === "blocked" ? "high" : "med", updatedAt: formatInternalDate(task.due_date),
        })),
    ];
    const materialTaskIds = new Set(materials.filter((item) => item.kind === "task").map((item) => item.id));
    return {
        intake: events.filter((event) => event.status === "draft").map((event) => ({
            kind: "event", id: event.event_id, title: event.title, status: "待分析",
            context: event.description, action: "开始分析", priority: "med", updatedAt: formatInternalDate(event.updated_at),
        })),
        materials,
        remediate: tasks.filter((task) => ["not_started", "in_progress", "blocked"].includes(task.status) && !materialTaskIds.has(task.task_id)).map((task) => ({
            kind: "task", id: task.task_id, title: task.title, status: internalTaskStatusLabels[task.status] || task.status,
            context: riskById.get(task.risk_id)?.title || task.risk_id, action: "处理任务",
            priority: task.status === "blocked" ? "high" : "med", updatedAt: formatInternalDate(task.due_date),
        })),
        review: [
            ...events.filter((event) => event.status === "assessed").map((event) => ({
                kind: "event", id: event.event_id, title: event.title, status: "等待确认",
                context: "分析已完成，需要人工确认是否加入风险清单", action: "人工确认",
                priority: internalRiskLevelClass(event.assessment_snapshot?.report?.risk_level), updatedAt: formatInternalDate(event.updated_at),
            })),
            ...reviewGroups.queue.map((review) => ({
                kind: review.target_type === "risk_gate" ? "gate" : "review", id: review.target_type === "risk_gate" ? review.target_id : review.review_id,
                title: internalReviewTargetTitle(review, risks, gates, tasks),
                status: review.target_type === "risk_gate" ? "下一阶段条件检查" : "待人工复核",
                context: review.target_type === "risk_gate" ? "先核对尚未满足的条件，再决定是否进入下一阶段" : "材料已提交，等待复核结论",
                action: review.target_type === "risk_gate" ? "查看条件" : "记录结论", priority: "med", updatedAt: "等待人工处理",
            })),
        ],
        close: risks.filter((risk) => risk.status !== "closed").map((risk) => {
            const blockers = internalRiskClosureBlockers(risk, workflow);
            return {
                kind: "risk", id: risk.risk_id, title: risk.title,
                status: blockers.length ? `尚有 ${blockers.length} 项前置条件` : "可结束事项",
                context: blockers[0] || "整改、复核和下一阶段条件检查均已完成",
                action: "结束检查", priority: blockers.length ? internalRiskLevelClass(risk.risk_level) : "low",
                updatedAt: blockers.length ? "继续处理前置事项" : "可提交确认", blockers,
            };
        }).sort((a, b) => a.blockers.length - b.blockers.length),
    };
}

function renderInternalInbox(workflow, filtered) {
    const rail = document.getElementById("internal-process-rail");
    const stageNav = document.getElementById("internal-stage-nav");
    const list = document.getElementById("internal-work-list");
    const title = document.getElementById("internal-list-title");
    const kicker = document.getElementById("internal-list-kicker");
    const count = document.getElementById("internal-list-count");
    if (!rail || !stageNav || !list || !title || !kicker || !count) return;
    const inbox = buildInternalInbox(workflow, filtered);
    const stages = [
        ["intake", "添加记录", "登记后先完成分析"],
        ["materials", "补充材料", "材料齐备后，可提交进入下一阶段的决定"],
        ["remediate", "整改办理", "处理责任人事项"],
        ["review", "人工确认", "人工记录正式结论"],
        ["close", "结束事项", "完成全部前置检查"],
    ];
    if (!stages.some(([key]) => key === internalInboxState.stage)) internalInboxState.stage = "intake";
    if (!internalInboxState.initialized && !inbox[internalInboxState.stage].length) {
        internalInboxState.stage = stages.find(([key]) => inbox[key].length)?.[0] || "intake";
    }
    internalInboxState.initialized = true;
    rail.innerHTML = stages.map(([key, label], index) => `
        <button type="button" class="internal-process-step ${key === internalInboxState.stage ? "is-active" : ""}" data-internal-stage="${key}">
            <span>${index + 1}</span><strong>${label}</strong><em>${inbox[key].length} 项</em>
        </button>${index < stages.length - 1 ? '<i aria-hidden="true"></i>' : ""}
    `).join("");
    stageNav.innerHTML = stages.map(([key, label, hint], index) => `
        <button type="button" class="internal-stage-item ${key === internalInboxState.stage ? "is-active" : ""}" data-internal-stage="${key}">
            <span>${index + 1}</span><div><strong>${label}</strong><small>${hint}</small></div><em>${inbox[key].length} 项</em>
        </button>
    `).join("");
    const current = inbox[internalInboxState.stage];
    const currentStage = stages.find(([key]) => key === internalInboxState.stage);
    kicker.textContent = `第 ${stages.findIndex(([key]) => key === internalInboxState.stage) + 1} 步`;
    title.textContent = currentStage[1];
    count.textContent = `${current.length} 项`;
    list.innerHTML = current.map((item) => `
        <article class="internal-inbox-row ${item.id === internalInboxState.selectedId && item.kind === internalInboxState.selectedType ? "is-selected" : ""}" data-internal-item-type="${item.kind}" data-internal-item-id="${escapeHtml(item.id)}" tabindex="0">
            <span class="internal-inbox-priority ${item.priority}"></span>
            <div class="internal-inbox-main"><div><span class="risk-text ${item.priority}">${escapeHtml(item.status)}</span><strong>${escapeHtml(item.title)}</strong></div><p>${escapeHtml(item.context)}</p></div>
            <div class="internal-inbox-meta"><span>${escapeHtml(item.updatedAt)}</span><button type="button" class="open-detail">${escapeHtml(item.action)}</button></div>
        </article>
    `).join("") || '<div class="internal-inbox-empty"><strong>当前没有待办</strong><p>可以继续查看下一阶段，或添加一条记录。</p></div>';
}

function renderInternalRiskWorkspace(workflow, meta = {}) {
    if (!workflow) return;
    const { risks, gates, tasks, reviews } = filteredInternalRiskWorkflow(workflow);
    const summary = internalRiskSummary(workflow);
    const sourceStatus = document.getElementById("internal-risk-source-status");
    const summaryElement = document.getElementById("internal-control-summary");
    if (!summaryElement) return;
    updateInternalWorkbenchTitle({ risks, tasks });
    if (sourceStatus) {
        sourceStatus.textContent = meta.data_source === "fixture_sample" ? "演示数据" : "工作流已连接";
        sourceStatus.className = "data-mode-badge";
    }
    summaryElement.innerHTML = [
        ["高风险事项", summary.highRisks, "high"],
        ["暂不满足准入条件", summary.gated, "crit"],
        ["待办整改", summary.pendingTasks, "med"],
        ["待人工复核", summary.pendingReviews, "med"],
    ].map(([label, value, level]) => `
        <div class="internal-summary-metric"><span>${label}</span><strong class="${level}">${value}</strong></div>
    `).join("");
    renderInternalInbox(workflow, { risks, gates, tasks, reviews });
    return;

    const eventQueue = document.getElementById("internal-event-queue");
    const eventList = document.getElementById("internal-event-list");
    const eventCount = document.getElementById("internal-event-count");
    const gateList = document.getElementById("internal-gate-list");
    const ledger = document.getElementById("internal-risk-ledger");
    const taskList = document.getElementById("internal-task-list");
    const reviewList = document.getElementById("internal-review-list");
    const reviewWaiting = document.getElementById("internal-review-waiting");
    const reviewHistoryList = document.getElementById("internal-review-history-list");
    const reviewHistoryCount = document.getElementById("internal-review-history-count");
    if (!summaryElement || !gateList || !ledger || !taskList || !reviewList || !reviewHistoryList) return;

    updateInternalWorkbenchTitle({ risks, tasks });

    document.getElementById("internal-gate-count").textContent = `${gates.length} 个节点`;
    document.getElementById("internal-risk-count").textContent = `${risks.length} 项`;
    document.getElementById("internal-task-count").textContent = `${tasks.length} 项`;
    const reviewGroups = classifyInternalReviews(reviews, tasks);
    document.getElementById("internal-review-count").textContent = `${reviewGroups.queue.length} 项待处理`;
    if (reviewWaiting) {
        reviewWaiting.textContent = reviewGroups.waiting.length
            ? `另有 ${reviewGroups.waiting.length} 项整改任务尚未满足复核条件`
            : "仅展示已提交材料或需节点决定的事项";
    }
    if (reviewHistoryCount) reviewHistoryCount.textContent = `${reviewGroups.history.length} 项`;
    if (sourceStatus) {
        sourceStatus.textContent = meta.data_source === "fixture_sample" ? "演示数据" : "工作流已连接";
        sourceStatus.className = "data-mode-badge";
    }

    const events = workflow.risk_events || [];
    if (eventQueue && eventList && eventCount) {
        eventQueue.hidden = !events.length;
        eventCount.textContent = `${events.length} 项`;
        eventList.innerHTML = events.map((event) => {
            const assessmentJob = (workflow.assessment_jobs || []).find((job) => job.event_id === event.event_id && ["queued", "running"].includes(job.status));
            const labels = { draft: assessmentJob ? `评估中 · ${assessmentJob.stage}` : "待分析", assessed: "等人确认", confirmed: "已加入风险清单", rejected: "未加入风险清单" };
            const reportLevel = internalRiskLevelClass(event.assessment_snapshot?.report?.risk_level);
            return `<article class="internal-event-row"><div><span class="risk-text ${event.status === "confirmed" ? "low" : event.status === "rejected" ? "crit" : reportLevel}">${escapeHtml(labels[event.status] || event.status)}</span><strong>${escapeHtml(event.title)}</strong><p>${escapeHtml(event.description)}</p></div><div class="internal-event-row-meta"><span>${escapeHtml(internalRiskStageLabels[event.lifecycle_stage] || event.lifecycle_stage)}</span><span>${formatInternalDate(event.updated_at)}</span><button class="btn" type="button" data-internal-event-open="${escapeHtml(event.event_id)}">${event.status === "assessed" ? "人工确认" : "查看记录"}</button></div></article>`;
        }).join("");
    }

    summaryElement.innerHTML = [
        ["高风险事项", summary.highRisks, "high"],
        ["暂不满足准入条件", summary.gated, "crit"],
        ["待办整改", summary.pendingTasks, "med"],
        ["待人工复核", summary.pendingReviews, "med"],
    ].map(([label, value, level]) => `
        <div class="internal-summary-metric"><span>${label}</span><strong class="${level}">${value}</strong></div>
    `).join("");

    gateList.innerHTML = gates.map((gate) => {
        const missing = (gate.checks || []).filter((check) => check.status === "missing").length;
        const linkedRisks = (gate.risk_item_ids || []).map((riskId) => risks.find((risk) => risk.risk_id === riskId)?.title).filter(Boolean);
        const riskLevel = linkedRisks.length
            ? internalRiskLevelClass(risks.find((risk) => gate.risk_item_ids.includes(risk.risk_id))?.risk_level)
            : "med";
        return `
            <article class="internal-gate-card">
                <div class="internal-card-meta"><span>${escapeHtml(internalRiskStageLabels[gate.lifecycle_stage] || gate.lifecycle_stage)}</span><span class="risk-text ${riskLevel}">${internalGateDecisionLabels[gate.decision] || gate.decision}</span></div>
                <h3>${escapeHtml(gate.title)}</h3>
                <p>${escapeHtml(linkedRisks[0] || "等待关联风险事项")}</p>
                <div class="internal-gate-footer"><span>${missing ? `${missing} 项材料待补` : "材料已齐备"}</span><button class="open-detail" type="button" data-internal-gate-id="${escapeHtml(gate.gate_id)}">查看核验项</button></div>
            </article>
        `;
    }).join("") || '<div class="empty-state">当前没有需要确认的阶段条件。</div>';

    ledger.innerHTML = risks.map((risk) => `
        <article class="internal-ledger-row">
            <div><div class="internal-ledger-title">${escapeHtml(risk.title)}</div><p>${escapeHtml((risk.trigger_facts || ["等待补充触发事实"])[0])}</p></div>
            <div class="internal-ledger-meta"><strong>${escapeHtml(internalRiskDomainLabels[risk.risk_domain] || risk.risk_domain)}</strong><span>${escapeHtml(internalRiskStageLabels[risk.lifecycle_stage] || risk.lifecycle_stage)}</span></div>
            <div><span class="risk-text ${internalRiskLevelClass(risk.risk_level)}">${riskLabels[internalRiskLevelClass(risk.risk_level)]}</span><span class="internal-status-text">${risk.status === "mitigating" ? "整改中" : risk.status === "closed" ? "已关闭" : "待处置"}</span></div>
            <div class="internal-ledger-meta"><strong>${(risk.missing_materials || []).length} 项材料缺口</strong><span>${(risk.task_ids || []).length} 项整改任务</span>${risk.status !== "closed" ? `<button class="open-detail" type="button" data-internal-risk-close="${escapeHtml(risk.risk_id)}">结束事项</button>` : ""}</div>
        </article>
    `).join("") || '<div class="empty-state">当前没有风险事项。</div>';

    taskList.innerHTML = tasks.map((task) => {
        const action = nextInternalTaskAction(task.status);
        return `
            <article class="internal-task-card">
                <div class="internal-card-meta"><span>${escapeHtml(task.owner)}</span><span class="risk-text ${task.status === "blocked" ? "crit" : task.status === "pending_review" ? "med" : "low"}">${internalTaskStatusLabels[task.status] || task.status}</span></div>
                <h3>${escapeHtml(task.title)}</h3>
                <p>关联事项：${escapeHtml(risks.find((risk) => risk.risk_id === task.risk_id)?.title || task.risk_id)}</p>
                <div class="internal-task-footer"><span>${formatInternalDate(task.due_date)}</span><button class="btn ${action ? "btn-primary" : ""}" type="button" data-internal-task-open="${escapeHtml(task.task_id)}">${action ? "处理任务" : task.status === "pending_review" ? "查看复核" : "查看记录"}</button></div>
            </article>
        `;
    }).join("") || '<div class="empty-state">当前没有整改任务。</div>';

    reviewList.innerHTML = reviewGroups.queue.map((review) => {
        const targetTitle = internalReviewTargetTitle(review, risks, gates, tasks);
        const task = reviewGroups.tasksById.get(review.target_id);
        const canDecide = review.target_type === "risk_gate" || (review.target_type === "remediation_task" && task?.status === "pending_review");
        return `
        <article class="internal-review-card">
            <div class="internal-card-meta"><span>${escapeHtml(review.target_type === "risk_gate" ? "业务准入节点" : review.target_type === "remediation_task" ? "整改任务" : "风险事项")}</span><span class="risk-text med">待人工结论</span></div>
            <h3>${escapeHtml(targetTitle)}</h3>
            <p>${review.target_type === "risk_gate" ? "节点决定必须由人工登记，系统会逐项核验是否满足进入下一阶段的条件。" : canDecide ? "材料已提交，等待具有权限的复核人确认结论。" : "关联整改尚未完成，当前不开放通过或退回决定。"}</p>
            <div class="internal-review-footer">${canDecide ? `<button class="btn btn-primary" type="button" data-internal-review-open="${escapeHtml(review.review_id)}">${review.target_type === "risk_gate" ? "登记阶段决定" : "记录复核决定"}</button>` : '<span>等待整改完成并通过复核</span>'}</div>
        </article>
        `;
    }).join("") || '<div class="empty-state">当前没有已触发的复核事项。</div>';

    reviewHistoryList.innerHTML = reviewGroups.history.map((review) => `
        <article class="internal-review-history-row"><span class="risk-text ${review.status === "approved" ? "low" : "crit"}">${internalReviewStatusLabels[review.status] || review.status}</span><div><strong>${escapeHtml(internalReviewTargetTitle(review, risks, gates, tasks))}</strong><p>${escapeHtml(review.conclusion || "未填写结论")}</p></div><span>${escapeHtml(review.reviewer || "未指定复核人")}</span></article>
    `).join("") || '<div class="empty-state">尚无已完成的复核记录。</div>';
}

function nextInternalTaskAction(status) {
    return {
        not_started: { status: "in_progress", label: "开始整改" },
        in_progress: { status: "pending_review", label: "提交材料并提请复核" },
        blocked: { status: "in_progress", label: "恢复处理" },
    }[status] || null;
}

function hideInternalDetailPanels() {
    ["internal-event-drawer", "internal-task-drawer", "internal-gate-detail", "internal-review-drawer"].forEach((id) => {
        const panel = document.getElementById(id);
        if (panel) panel.hidden = true;
    });
    document.getElementById("internal-detail-empty")?.setAttribute("hidden", "");
}

function clearInternalDetailSelection() {
    internalInboxState.selectedType = null;
    internalInboxState.selectedId = null;
    hideInternalDetailPanels();
    document.getElementById("internal-detail-empty")?.removeAttribute("hidden");
    renderInternalInbox(backendState.internalRisk?.data, filteredInternalRiskWorkflow(backendState.internalRisk?.data || {}));
}

function focusInternalDetail(drawer) {
    document.getElementById("internal-detail-empty")?.setAttribute("hidden", "");
    drawer?.closest(".internal-work-detail")?.scrollTo({ top: 0, behavior: "smooth" });
}

function openInternalInboxItem(type, id = null) {
    internalInboxState.selectedType = type;
    internalInboxState.selectedId = id;
    hideInternalDetailPanels();
    if (type === "event") showInternalEventDrawer(id);
    if (type === "task") openInternalTaskDrawer(id);
    if (type === "review") showInternalReviewDrawer(id);
    if (type === "gate") showInternalGateDecisionDrawer(id);
    if (type === "risk") showInternalRiskClosureDrawer(id);
    renderInternalInbox(backendState.internalRisk?.data, filteredInternalRiskWorkflow(backendState.internalRisk?.data || {}));
}

async function loadInternalEvidenceDocuments() {
    if (internalEvidenceDocuments.loaded) return internalEvidenceDocuments.items;
    if (internalEvidenceDocuments.loading) return internalEvidenceDocuments.loading;
    internalEvidenceDocuments.loading = fetchBackendJson("/documents", { timeoutMs: 6000 })
        .then((payload) => {
            internalEvidenceDocuments.items = payload.items || [];
            internalEvidenceDocuments.loaded = true;
            return internalEvidenceDocuments.items;
        })
        .catch(() => {
            internalEvidenceDocuments.available = false;
            internalEvidenceDocuments.loaded = true;
            return [];
        })
        .finally(() => { internalEvidenceDocuments.loading = null; });
    return internalEvidenceDocuments.loading;
}

function internalEvidenceDocumentOptions(task) {
    if (!internalEvidenceDocuments.available) {
        return '<p class="internal-document-hint">材料服务暂不可用，可继续填写材料编号。</p>';
    }
    const completedDocuments = internalEvidenceDocuments.items.filter(
        (item) => item.status === "completed" && item.markdown_available,
    );
    if (!completedDocuments.length) {
        return '<p class="internal-document-hint">暂无已解析材料，可在法律风控中上传并解析 PDF 后回到此处关联。</p>';
    }
    const selected = new Set(task.evidence_refs || []);
    const orderedDocuments = [...completedDocuments].sort((left, right) => Number(selected.has(right.task_id)) - Number(selected.has(left.task_id)));
    return `
        <div class="internal-document-picker">
            <label>已有解析材料<select id="internal-task-documents" multiple size="3" aria-label="关联已解析材料">${orderedDocuments.map((document) => `<option value="${escapeHtml(document.task_id)}" ${selected.has(document.task_id) ? "selected" : ""}>${selected.has(document.task_id) ? "已关联 · " : "可关联 · "}${escapeHtml(document.original_filename)} · ${escapeHtml(document.task_id)}</option>`).join("")}</select></label>
            <span>已关联材料置顶；勾选后以文档任务编号留痕。可预览解析稿、打开原件或下载。</span>
            <div class="internal-parsed-material-list">${orderedDocuments.map((document) => `
                <div class="internal-parsed-material-card ${selected.has(document.task_id) ? "selected" : ""}">
                    <div><strong>${escapeHtml(document.original_filename)}</strong><span>${selected.has(document.task_id) ? "当前任务已关联" : "可关联"} · 已解析 · ${escapeHtml(document.task_id)}</span></div>
                    <div class="internal-evidence-actions"><button type="button" data-internal-evidence-preview="${escapeHtml(document.task_id)}">预览解析稿</button><button type="button" data-internal-evidence-open="${escapeHtml(document.task_id)}">打开原件</button><button type="button" data-internal-evidence-download="${escapeHtml(document.task_id)}">下载解析稿</button></div>
                </div>
            `).join("")}</div>
        </div>
    `;
}

function resolveInternalProjectSource(ref) {
    const sourceRef = String(ref || "").trim();
    const workflow = backendState.internalRisk?.data || {};
    if (!sourceRef) return null;
    const event = (workflow.risk_events || []).find((item) => (item.source_refs || []).includes(sourceRef));
    if (event) return { type: "event", id: event.event_id, title: event.title, label: "风险事件" };
    const task = (workflow.remediation_tasks || []).find((item) => (item.evidence_refs || []).includes(sourceRef));
    if (task) return { type: "task", id: task.task_id, title: task.title, label: "整改任务" };
    const risk = (workflow.risk_items || []).find((item) => (item.evidence_refs || []).includes(sourceRef));
    if (risk) return { type: "risk", id: risk.risk_id, title: risk.title, label: "风险事项" };
    const gate = (workflow.gates || []).find((item) => (item.checks || []).some((check) => (check.evidence_refs || []).includes(sourceRef)));
    if (gate) return { type: "gate", id: gate.gate_id, title: gate.title, label: "准入节点" };
    return null;
}

function renderInternalProjectSourceList(refs = []) {
    const values = [...new Set((refs || []).map((ref) => String(ref || "").trim()).filter(Boolean))];
    if (!values.length) return "";
    return `<div class="internal-project-source-list">${values.map((ref) => {
        const target = resolveInternalProjectSource(ref);
        return `<div class="internal-project-source" data-internal-project-ref="${escapeHtml(ref)}"><div><strong>${escapeHtml(ref)}</strong><span>${target ? `项目内${escapeHtml(target.label)}：${escapeHtml(target.title)}` : "未映射到项目内记录的来源编号"}</span></div>${target ? `<button type="button" data-internal-project-source-open="${escapeHtml(ref)}">跳转高亮</button>` : ""}</div>`;
    }).join("")}</div>`;
}

function highlightInternalProjectSource(ref) {
    const selector = `[data-internal-project-ref="${CSS.escape(String(ref || ""))}"]`;
    const element = document.querySelector(selector);
    if (!element) return;
    element.scrollIntoView({ behavior: "smooth", block: "center" });
    element.classList.add("internal-source-highlight");
    window.setTimeout(() => element.classList.remove("internal-source-highlight"), 2200);
}

async function openInternalProjectSource(ref) {
    const target = resolveInternalProjectSource(ref);
    if (!target) return;
    if (target.type === "event") showInternalEventDrawer(target.id);
    if (target.type === "task") await openInternalTaskDrawer(target.id);
    if (target.type === "risk") showInternalRiskClosureDrawer(target.id);
    if (target.type === "gate") showInternalGateDetail(target.id);
    window.setTimeout(() => highlightInternalProjectSource(ref), 40);
}

function internalEvidenceStatusLabel(document) {
    return {
        uploaded: "已上传，等待解析",
        processing: "解析中",
        completed: "解析完成",
        failed: "解析失败",
    }[document?.status] || "外部材料编号";
}

function internalEventReportView(event) {
    const report = event.assessment_snapshot?.report || {};
    const result = {
        answer: report.executive_summary || "未生成可展示的法律分析结论。",
        recommended_actions: (report.action_plan || []).map((item) => item.action).filter(Boolean),
        missing_evidence: report.review_reasons || [],
        evidence_chain: report.evidence_chain || [],
    };
    const level = internalRiskLevelClass(report.risk_level);
    const confidence = report.confidence?.overall ?? report.confidence?.answer;
    const reviewRequired = "等人确认";
    return `
        <section class="internal-event-assessment">
            <div class="internal-event-assessment-meta"><span class="risk-text ${level}">${riskLabels[level] || "待评估"}${level === "pending" ? "" : "风险建议"}</span><span>${reviewRequired}</span>${Number.isFinite(confidence) ? `<span>分析置信度 ${Math.round(confidence * 100)}%</span>` : ""}</div>
            <div class="internal-event-answer">${renderAnswerContent(result)}</div>
            <details class="internal-event-evidence"><summary>查看分析详情</summary><p>生成时间：${formatInternalDate(event.assessment_snapshot?.generated_at)}</p><p>记录编号：${escapeHtml(event.assessment_snapshot?.snapshot_id || "-")}</p><p>系统只保存本次情况和分析结果；不会自动加入清单、让项目继续或结束风险。</p></details>
        </section>
    `;
}

function showInternalEventDrawer(eventId = null) {
    const drawer = document.getElementById("internal-event-drawer");
    const workflow = backendState.internalRisk?.data;
    if (!drawer || !workflow) return;
    const event = eventId ? (workflow.risk_events || []).find((item) => item.event_id === eventId) : null;
    drawer.hidden = false;
    if (!event) {
        drawer.innerHTML = `
            <div class="internal-drawer-head"><div><span class="metric-label">记录新情况</span><h2>先写清楚发生了什么</h2><p>系统会提供风险分析，但不能替你作出管理决策。</p></div><button class="icon-button" type="button" aria-label="关闭新情况登记" data-internal-event-close>&times;</button></div>
            <div class="internal-event-form">
                <label class="internal-form-wide">事件名称<input id="internal-event-title" type="text" maxlength="160" placeholder="例如：新增境外模型服务用于客户数据处理"></label>
                <label>项目阶段<select id="internal-event-stage"><option value="establishment">设立与治理</option><option value="research_and_development">研发与验证</option><option value="market_access">市场准入与客户导入</option><option value="commercialization">商业化与质量交付</option><option value="financing">融资与税务治理</option><option value="scale_expansion">规模扩张与市场竞争</option><option value="strategic_adjustment">退出/战略调整与供应链韧性</option></select></label>
                <label>风险领域<select id="internal-event-domain"><option value="data_model_governance">数据与模型治理</option><option value="technology_ip">技术与知识资产</option><option value="product_commercialization">产品商业化</option><option value="cross_border_supply_chain">跨境与供应链</option><option value="corporate_finance_governance">公司治理与科技金融</option></select></label>
                <label class="internal-form-wide">触发事实<textarea id="internal-event-description" rows="4" placeholder="记录实际发生的业务变化、数据范围、合作方、计划时间与已知缺口。"></textarea></label>
                <label>登记人<input id="internal-event-reporter" type="text" value="风险治理专员" maxlength="80"></label>
                <label>关联材料编号<input id="internal-event-sources" type="text" placeholder="例如：supplier-alert-01, architecture-v3"></label>
                <div class="internal-drawer-actions"><span>提交后会生成分析结果，供人工确认使用。</span><button class="btn btn-primary" type="button" data-internal-event-assess>开始分析</button></div>
            </div>
        `;
    } else {
        const decision = event.confirmation;
        const decisionLabel = event.status === "confirmed" ? "已加入风险清单" : event.status === "rejected" ? "未加入风险清单" : "等人确认";
        drawer.innerHTML = `
            <div class="internal-drawer-head"><div><span class="metric-label">风险事件 · ${escapeHtml(decisionLabel)}</span><h2>${escapeHtml(event.title)}</h2><p>${escapeHtml(event.description)}</p></div><button class="icon-button" type="button" aria-label="关闭风险事件" data-internal-event-close>&times;</button></div>
            <div class="internal-drawer-meta"><span>登记人 <strong>${escapeHtml(event.reported_by)}</strong></span><span>发生时间 <strong>${formatInternalDate(event.occurred_at)}</strong></span><span>关联材料 <strong>${(event.source_refs || []).length + (event.document_task_ids || []).length} 项</strong></span></div>
            ${renderInternalProjectSourceList(event.source_refs || [])}
            ${event.assessment_snapshot ? internalEventReportView(event) : '<div class="internal-drawer-notice">还没有分析结果。</div>'}
            ${event.status === "assessed" ? `
                <div class="internal-event-confirmation"><label>确认人<input id="internal-event-reviewer" type="text" maxlength="80" placeholder="填写复核人姓名或角色"></label><label class="internal-form-wide">确认说明<textarea id="internal-event-conclusion" rows="3" placeholder="说明要不要加入风险清单，以及接下来怎么做"></textarea></label><div class="internal-drawer-actions"><span>只有人工确认后才会加入风险清单。</span><div class="internal-event-actions"><button class="btn" type="button" data-internal-event-confirm="rejected" data-internal-event-id="${escapeHtml(event.event_id)}">不加入清单</button><button class="btn btn-primary" type="button" data-internal-event-confirm="confirmed" data-internal-event-id="${escapeHtml(event.event_id)}">加入风险清单</button></div></div></div>
            ` : decision ? `<div class="internal-drawer-notice">${escapeHtml(decision.reviewer)}：${escapeHtml(decision.conclusion)}${event.confirmed_risk_id ? `（已登记到风险清单：${escapeHtml(event.confirmed_risk_id)}）` : ""}</div>` : ""}
        `;
    }
    focusInternalDetail(drawer);
}

async function createAndAssessInternalEvent(button) {
    const title = document.getElementById("internal-event-title")?.value.trim();
    const description = document.getElementById("internal-event-description")?.value.trim();
    const reporter = document.getElementById("internal-event-reporter")?.value.trim();
    if (!title || !description || !reporter) {
        button.textContent = "请填写事件名称、事实与登记人";
        return;
    }
    const originalLabel = button.textContent;
    button.disabled = true;
    button.textContent = "分析中";
    try {
        const sourceRefs = (document.getElementById("internal-event-sources")?.value || "").split(",").map((item) => item.trim()).filter(Boolean);
        const created = await fetchBackendJson("/internal-risk/events", {
            method: "POST",
            body: JSON.stringify({
                title,
                description,
                lifecycle_stage: document.getElementById("internal-event-stage")?.value,
                risk_domain: document.getElementById("internal-event-domain")?.value,
                occurred_at: new Date().toISOString(),
                reported_by: reporter,
                source_refs: sourceRefs,
            }),
            timeoutMs: 8000,
        });
        const queued = await fetchBackendJson(`/internal-risk/events/${encodeURIComponent(created.data.event_id)}/assessment-jobs`, {
            method: "POST",
            body: JSON.stringify({ input_filters: {} }),
            timeoutMs: 8000,
        });
        const assessed = await waitForInternalAssessmentJob(queued.data, button);
        await loadInternalRiskWorkflow();
        showInternalEventDrawer(assessed.event_id);
    } catch (error) {
        console.info(error);
        button.textContent = "生成失败";
        window.setTimeout(() => { button.textContent = originalLabel; button.disabled = false; }, 1800);
    }
}

async function waitForInternalAssessmentJob(job, button) {
    const stageLabels = {
        accepted: "已提交评估",
        material_loading: "正在读取材料",
        rag_assessment: "正在核验证据",
        snapshot_persisted: "评估已完成",
        failed: "评估未完成",
    };
    const deadline = Date.now() + 70000;
    let current = job;
    while (Date.now() < deadline) {
        button.textContent = stageLabels[current.stage] || "正在评估";
        if (current.status === "completed") {
            const workflow = backendState.internalRisk?.data;
            const event = (workflow?.risk_events || []).find((item) => item.event_id === current.event_id);
            return event || { event_id: current.event_id };
        }
        if (current.status === "failed") {
            throw new Error(current.failure_message || "材料/RAG 评估未完成");
        }
        await new Promise((resolve) => window.setTimeout(resolve, 800));
        const response = await fetchBackendJson(`/internal-risk/assessment-jobs/${encodeURIComponent(current.assessment_job_id)}`, { timeoutMs: 8000 });
        current = response.data;
    }
    throw new Error("材料/RAG 评估超时，可稍后刷新查看任务状态");
}

async function confirmInternalEvent(eventId, decision, button) {
    const reviewer = document.getElementById("internal-event-reviewer")?.value.trim();
    const conclusion = document.getElementById("internal-event-conclusion")?.value.trim();
    if (!reviewer || !conclusion) {
        button.textContent = "请填写确认人与说明";
        return;
    }
    const originalLabel = button.textContent;
    button.disabled = true;
    button.textContent = "记录中";
    try {
        await fetchBackendJson(`/internal-risk/events/${encodeURIComponent(eventId)}/confirmation`, {
            method: "PATCH",
            body: JSON.stringify({ decision, reviewer, conclusion }),
            timeoutMs: 8000,
        });
        await loadInternalRiskWorkflow();
        showInternalEventDrawer(eventId);
    } catch (error) {
        console.info(error);
        button.textContent = "记录失败";
        window.setTimeout(() => { button.textContent = originalLabel; button.disabled = false; }, 1600);
    }
}

function renderInternalTaskEvidence(task) {
    const documentsById = new Map(internalEvidenceDocuments.items.map((item) => [item.task_id, item]));
    const refs = task.evidence_refs || [];
    const fileRefs = refs.map((ref) => documentsById.get(ref)).filter(Boolean);
    const textRefs = refs.filter((ref) => !documentsById.has(ref));
    return `
        <section class="internal-evidence-panel">
            <div class="internal-evidence-head"><div><span class="metric-label">整改证据包</span><strong>${refs.length} 项关联材料</strong></div><button class="btn" type="button" data-internal-evidence-upload="${escapeHtml(task.task_id)}">上传 PDF</button></div>
            <input id="internal-task-evidence-upload" type="file" accept="application/pdf,.pdf" hidden data-task-id="${escapeHtml(task.task_id)}">
            <div class="internal-evidence-list">
                ${fileRefs.map((document) => `<div class="internal-evidence-row"><div><strong>${escapeHtml(document.original_filename)}</strong><span>${escapeHtml(internalEvidenceStatusLabel(document))} · 文件材料</span></div><div class="internal-evidence-actions">${document.markdown_available ? `<button type="button" data-internal-evidence-preview="${escapeHtml(document.task_id)}">预览解析稿</button><button type="button" data-internal-evidence-download="${escapeHtml(document.task_id)}">下载解析稿</button>` : ""}<button type="button" data-internal-evidence-open="${escapeHtml(document.task_id)}">打开原件</button><button type="button" data-internal-evidence-source="${escapeHtml(document.task_id)}">下载原件</button></div></div>`).join("")}
                ${textRefs.map((ref) => `<div class="internal-evidence-row" data-internal-project-ref="${escapeHtml(ref)}"><div><strong>${escapeHtml(ref)}</strong><span>项目内或外部来源编号</span></div><div class="internal-evidence-actions">${resolveInternalProjectSource(ref) ? `<button type="button" data-internal-project-source-open="${escapeHtml(ref)}">跳转高亮</button>` : ""}</div></div>`).join("")}
                ${refs.length ? "" : '<p class="internal-evidence-empty">尚未关联材料。可上传 PDF 或填写外部系统的材料编号。</p>'}
            </div>
        </section>
    `;
}

async function openInternalTaskDrawer(taskId) {
    await loadInternalEvidenceDocuments();
    showInternalTaskDrawer(taskId);
}

async function uploadInternalTaskEvidence(input) {
    const taskId = input?.dataset.taskId;
    const file = input?.files?.[0];
    if (!taskId || !file) return;
    const trigger = document.querySelector(`[data-internal-evidence-upload="${CSS.escape(taskId)}"]`);
    const originalLabel = trigger?.textContent;
    if (trigger) {
        trigger.disabled = true;
        trigger.textContent = "上传中";
    }
    try {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("purpose", "remediation_evidence");
        const upload = await fetchBackendForm("/documents/upload", formData);
        const documentTaskId = upload?.data?.task_id;
        if (!documentTaskId) throw new Error("材料服务未返回文件编号");
        await fetchBackendJson(`/internal-risk/tasks/${encodeURIComponent(taskId)}/evidence`, {
            method: "POST",
            body: JSON.stringify({
                evidence_refs: [documentTaskId],
                changed_by: "internal-risk-workbench",
                note: "Uploaded remediation evidence; parsing is pending.",
            }),
            timeoutMs: 8000,
        });
        internalEvidenceDocuments.loaded = false;
        internalEvidenceDocuments.available = true;
        await loadInternalRiskWorkflow();
        await openInternalTaskDrawer(taskId);
    } catch (error) {
        console.info(error);
        if (trigger) {
            trigger.textContent = "上传失败";
            window.setTimeout(() => {
                trigger.textContent = originalLabel;
                trigger.disabled = false;
            }, 1600);
        }
    } finally {
        input.value = "";
    }
}

async function previewInternalTaskEvidence(documentTaskId) {
    try {
        const result = await fetchBackendJson(`/documents/${encodeURIComponent(documentTaskId)}/result`, { timeoutMs: 10000 });
        document.getElementById("document-preview-content").textContent = result.markdown || "";
        document.getElementById("document-preview-dialog")?.showModal();
    } catch (error) {
        console.info(error);
    }
}

function downloadInternalTaskEvidence(documentTaskId, kind) {
    const path = kind === "source" ? "source" : "content";
    window.open(`${backendState.baseUrl}/documents/${encodeURIComponent(documentTaskId)}/${path}`, "_blank", "noopener");
}

async function openInternalTaskEvidence(documentTaskId, button) {
    if (!documentTaskId) return;
    const originalLabel = button?.textContent;
    if (button) {
        button.disabled = true;
        button.textContent = "正在打开";
    }
    try {
        await fetchBackendJson(`/documents/${encodeURIComponent(documentTaskId)}/open`, { method: "POST", timeoutMs: 8000 });
        if (button) button.textContent = "已交给默认程序";
    } catch (error) {
        console.info(error);
        if (button) button.textContent = "打开失败";
    } finally {
        if (button) window.setTimeout(() => {
            button.textContent = originalLabel;
            button.disabled = false;
        }, 1800);
    }
}

function showInternalTaskDrawer(taskId) {
    const workflow = backendState.internalRisk?.data;
    const drawer = document.getElementById("internal-task-drawer");
    const task = workflow?.remediation_tasks?.find((item) => item.task_id === taskId);
    if (!drawer || !task) return;
    const risk = workflow.risk_items?.find((item) => item.risk_id === task.risk_id);
    const action = nextInternalTaskAction(task.status);
    const statusDetail = task.status === "pending_review"
        ? "已提交人工复核，系统不会自动确认完成或允许进入下一阶段。"
        : task.status === "verified"
            ? "该任务已完成验证，仍可在人工复核记录中查看关联结论。"
            : "请补充处理说明和材料编号，再更新任务进度。";
    drawer.hidden = false;
    drawer.innerHTML = `
        <div class="internal-drawer-head">
            <div><span class="metric-label">整改任务 · ${escapeHtml(internalTaskStatusLabels[task.status] || task.status)}</span><h2>${escapeHtml(task.title)}</h2><p>${escapeHtml(risk?.title || task.risk_id)}</p></div>
            <button class="icon-button" type="button" aria-label="关闭任务处理面板" data-internal-task-close>&times;</button>
        </div>
        <div class="internal-drawer-meta"><span>责任人 <strong>${escapeHtml(task.owner)}</strong></span><span>计划完成 <strong>${formatInternalDate(task.due_date)}</strong></span><span>已有材料 <strong>${task.evidence_refs?.length || 0} 项</strong></span></div>
        ${renderInternalTaskEvidence(task)}
        ${action ? `
            <div class="internal-drawer-form">
                <label>处理说明<textarea id="internal-task-note" rows="3" placeholder="记录本次处理范围、阻塞原因或提交说明"></textarea></label>
                <label>材料编号<input id="internal-task-evidence" type="text" value="${escapeHtml((task.evidence_refs || []).join(", "))}" placeholder="例如：data-inventory-v1, contract-redline-v2"></label>
                ${internalEvidenceDocumentOptions(task)}
                <div class="internal-drawer-actions"><span>${escapeHtml(statusDetail)}</span><button class="btn btn-primary" type="button" data-internal-task-save="${escapeHtml(task.task_id)}" data-next-status="${action.status}">${action.label}</button></div>
            </div>
        ` : `<div class="internal-drawer-notice">${escapeHtml(statusDetail)}</div>`}
    `;
    focusInternalDetail(drawer);
}

function showInternalReviewDrawer(reviewId) {
    const workflow = backendState.internalRisk?.data;
    const drawer = document.getElementById("internal-review-drawer");
    const review = workflow?.manual_reviews?.find((item) => item.review_id === reviewId);
    const task = workflow?.remediation_tasks?.find((item) => item.task_id === review?.target_id);
    const risk = workflow?.risk_items?.find((item) => item.risk_id === task?.risk_id);
    if (!drawer || !review || !task || task.status !== "pending_review" || review.status !== "pending") return;
    drawer.hidden = false;
    drawer.innerHTML = `
        <div class="internal-drawer-head">
            <div><span class="metric-label">人工复核 · 仅授权人员可提交决定</span><h2>${escapeHtml(task.title)}</h2><p>${escapeHtml(risk?.title || task.risk_id)}</p></div>
            <button class="icon-button" type="button" aria-label="关闭人工复核面板" data-internal-review-close>&times;</button>
        </div>
        <div class="internal-drawer-meta"><span>整改材料 <strong>${task.evidence_refs?.length || 0} 项</strong></span><span>整改责任人 <strong>${escapeHtml(task.owner)}</strong></span><span>当前状态 <strong>待人工复核</strong></span></div>
        <div class="internal-review-form">
            <label>复核人<input id="internal-reviewer" type="text" placeholder="填写复核人姓名或角色" required></label>
            <label>复核结论<select id="internal-review-decision" aria-label="选择复核结论"><option value="approved">确认整改完成</option><option value="changes_requested">退回继续整改</option><option value="rejected">拒绝本次整改材料</option></select></label>
            <label class="internal-form-wide">结论说明<textarea id="internal-review-conclusion" rows="3" placeholder="说明核验范围、材料充分性和后续要求" required></textarea></label>
            <div class="internal-drawer-actions"><span>人工决定会同时更新整改任务状态并写入审计历史。</span><button class="btn btn-primary" type="button" data-internal-review-save="${escapeHtml(review.review_id)}">记录复核决定</button></div>
        </div>
    `;
    focusInternalDetail(drawer);
}

function showInternalGateDetail(gateId) {
    const workflow = backendState.internalRisk?.data;
    const drawer = document.getElementById("internal-gate-detail");
    const gate = workflow?.gates?.find((item) => item.gate_id === gateId);
    if (!drawer || !gate) return;
    const linkedReviews = (workflow.manual_reviews || []).filter((review) => review.review_id === gate.review_id);
    drawer.hidden = false;
    drawer.innerHTML = `
        <div class="internal-detail-head"><div><span class="metric-label">${escapeHtml(internalRiskStageLabels[gate.lifecycle_stage] || gate.lifecycle_stage)}</span><h3>${escapeHtml(gate.title)}</h3></div><span class="risk-text ${gate.decision === "suspended" ? "crit" : gate.decision === "approved" ? "low" : "med"}">${internalGateDecisionLabels[gate.decision]}</span></div>
        <div class="internal-detail-grid">
            <div><h3>核验项</h3><ul>${(gate.checks || []).map((check) => `<li><span class="risk-dot ${check.status === "passed" ? "low" : check.status === "missing" ? "high" : "med"}"></span>${escapeHtml(check.title)}：${check.status === "passed" ? "已核验" : check.status === "missing" ? "待补充" : "不适用"}${renderInternalProjectSourceList(check.evidence_refs || [])}</li>`).join("")}</ul></div>
            <div><h3>责任人</h3><p>${escapeHtml(gate.owner)}</p><h3>人工复核</h3><p>${escapeHtml(linkedReviews[0]?.conclusion || "尚未形成复核结论")}</p></div>
        </div>
        <div class="internal-detail-actions"><button class="btn" type="button" data-internal-gate-decision-open="${escapeHtml(gate.gate_id)}">登记节点决定</button></div>
    `;
    focusInternalDetail(drawer);
}

function internalGateBlockers(gate) {
    const workflow = backendState.internalRisk?.data || {};
    const linkedRiskIds = new Set(gate.risk_item_ids || []);
    const tasks = (workflow.remediation_tasks || []).filter((task) => linkedRiskIds.has(task.risk_id));
    const reviews = new Map((workflow.manual_reviews || []).map((review) => [review.review_id, review]));
    return [
        ...(gate.checks || []).filter((check) => check.status === "missing").map((check) => `核验项未完成：${check.title}`),
        ...tasks.filter((task) => task.status !== "verified").map((task) => `整改任务未验证：${task.title}`),
        ...tasks.filter((task) => task.requires_manual_review && reviews.get(task.review_id)?.status !== "approved").map((task) => `整改复核未批准：${task.title}`),
    ];
}

function renderInternalBlockerList(blockers, emptyText) {
    if (!blockers.length) return `<div class="internal-drawer-notice">${escapeHtml(emptyText)}</div>`;
    return `<div class="internal-drawer-notice internal-blocker-notice"><strong>当前不能继续的原因</strong><ul class="internal-blocker-list">${blockers.map((blocker) => `<li>${escapeHtml(blocker)}</li>`).join("")}</ul></div>`;
}

function internalWorkflowBlockerSummary(error, fallback) {
    const blockers = error?.payload?.error?.blockers;
    if (!Array.isArray(blockers) || !blockers.length) return fallback;
    const messages = blockers.map((blocker) => blocker?.message).filter(Boolean);
    return messages.length ? `需先处理：${messages[0]}` : fallback;
}

function showInternalGateDecisionDrawer(gateId) {
    const workflow = backendState.internalRisk?.data;
    const drawer = document.getElementById("internal-review-drawer");
    const gate = workflow?.gates?.find((item) => item.gate_id === gateId);
    if (!drawer || !gate) return;
    const blockers = internalGateBlockers(gate);
    const canProceed = blockers.length === 0;
    drawer.hidden = false;
    drawer.innerHTML = `
        <div class="internal-drawer-head"><div><span class="metric-label">阶段决策</span><h2>${escapeHtml(gate.title)}</h2><p>系统只提示条件；是否进入下一阶段，由授权负责人决定。</p></div><button class="icon-button" type="button" aria-label="关闭阶段决策" data-internal-review-close>&times;</button></div>
        <div class="internal-drawer-meta"><span>当前结论 <strong>${escapeHtml(internalGateDecisionLabels[gate.decision] || gate.decision)}</strong></span><span>责任人 <strong>${escapeHtml(gate.owner)}</strong></span></div>
        ${renderInternalBlockerList(blockers, "材料已齐备、整改已完成、复核已通过，可以提交进入下一阶段的决定。")}
        <div class="internal-review-form"><label>复核人<input id="internal-gate-reviewer" type="text" placeholder="填写授权复核人"></label><label class="internal-form-wide">决定说明<textarea id="internal-gate-conclusion" rows="3" placeholder="填写本次决定的依据和后续要求"></textarea></label><div class="internal-drawer-actions"><span>${canProceed ? "确认后，项目可进入下一阶段。" : "请先补齐材料或完成整改。"}</span><div class="internal-event-actions"><button class="btn btn-primary" type="button" data-internal-gate-decision-save="${escapeHtml(gate.gate_id)}" data-internal-gate-decision="approved" ${canProceed ? "" : "disabled"}>进入下一阶段</button><button class="btn" type="button" data-internal-gate-decision-save="${escapeHtml(gate.gate_id)}" data-internal-gate-decision="rectification_required">补齐材料并整改</button><button class="btn" type="button" data-internal-gate-decision-save="${escapeHtml(gate.gate_id)}" data-internal-gate-decision="suspended">暂缓推进</button></div></div></div>
    `;
    focusInternalDetail(drawer);
}

function showInternalRiskClosureDrawer(riskId) {
    const workflow = backendState.internalRisk?.data;
    const drawer = document.getElementById("internal-review-drawer");
    const risk = workflow?.risk_items?.find((item) => item.risk_id === riskId);
    if (!drawer || !risk) return;
    const relatedTasks = (workflow.remediation_tasks || []).filter((task) => task.risk_id === riskId);
    const relatedGates = (workflow.gates || []).filter((gate) => (gate.risk_item_ids || []).includes(riskId));
    const blockers = [
        ...relatedTasks.filter((task) => task.status !== "verified").map((task) => `整改任务未验证：${task.title}`),
        ...relatedGates.filter((gate) => gate.decision !== "approved").map((gate) => `关联业务准入节点未通过：${gate.title}`),
    ];
    drawer.hidden = false;
    drawer.innerHTML = `
        <div class="internal-drawer-head"><div><span class="metric-label">结束事项前检查</span><h2>${escapeHtml(risk.title)}</h2><p>结束前需全部整改任务、任务复核和关联业务准入节点均完成正式核验。</p></div><button class="icon-button" type="button" aria-label="关闭事项结束检查" data-internal-review-close>&times;</button></div>
        ${renderInternalProjectSourceList(risk.evidence_refs || [])}
        ${renderInternalBlockerList(blockers, "前端未发现阻塞项，提交时仍将由服务端再次验证。")}
        <div class="internal-review-form"><label>确认人<input id="internal-risk-closer" type="text" placeholder="填写授权复核人"></label><label class="internal-form-wide">结束说明<textarea id="internal-risk-close-conclusion" rows="3" placeholder="说明结束依据和后续监控要求"></textarea></label><div class="internal-drawer-actions"><span>结束事项不会改变历史事件、材料或审计记录。</span><button class="btn btn-primary" type="button" data-internal-risk-close-save="${escapeHtml(risk.risk_id)}">确认结束事项</button></div></div>
    `;
    focusInternalDetail(drawer);
}

async function recordInternalGateDecision(gateId, decision, button) {
    const reviewer = document.getElementById("internal-gate-reviewer")?.value.trim();
    const conclusion = document.getElementById("internal-gate-conclusion")?.value.trim();
    if (!reviewer || !conclusion || !decision) { button.textContent = "请填写复核人与说明"; return; }
    const originalLabel = button.textContent; button.disabled = true; button.textContent = "记录中";
    try { await fetchBackendJson(`/internal-risk/gates/${encodeURIComponent(gateId)}/decision`, { method: "PATCH", body: JSON.stringify({ decision, reviewer, conclusion }), timeoutMs: 8000 }); document.getElementById("internal-review-drawer").hidden = true; await loadInternalRiskWorkflow(); } catch (error) { console.info(error); button.textContent = internalWorkflowBlockerSummary(error, "记录失败"); window.setTimeout(() => { button.textContent = originalLabel; button.disabled = false; }, 2800); }
}

async function closeInternalRisk(riskId, button) {
    const reviewer = document.getElementById("internal-risk-closer")?.value.trim();
    const conclusion = document.getElementById("internal-risk-close-conclusion")?.value.trim();
    if (!reviewer || !conclusion) { button.textContent = "请填写确认人与说明"; return; }
    const originalLabel = button.textContent; button.disabled = true; button.textContent = "核验中";
    try { await fetchBackendJson(`/internal-risk/risks/${encodeURIComponent(riskId)}/closure`, { method: "PATCH", body: JSON.stringify({ reviewer, conclusion }), timeoutMs: 8000 }); document.getElementById("internal-review-drawer").hidden = true; await loadInternalRiskWorkflow(); } catch (error) { console.info(error); button.textContent = internalWorkflowBlockerSummary(error, "关闭失败"); window.setTimeout(() => { button.textContent = originalLabel; button.disabled = false; }, 2800); }
}

async function loadInternalRiskWorkflow() {
    const sourceStatus = document.getElementById("internal-risk-source-status");
    try {
        const [payload, assistancePayload] = await Promise.all([
            fetchBackendJson("/internal-risk/workflow", { timeoutMs: 8000 }),
            fetchBackendJson(`/internal-risk/management-assistance?company_id=${encodeURIComponent(activeRiskIntakeCompanyId)}`, { timeoutMs: 8000 }),
        ]);
        if (supplyState.source === "developer_debug") return;
        payload.data.management_assistance = {
            suggestions: assistancePayload.suggestions || [],
            reminders: assistancePayload.reminders || [],
        };
        backendState.internalRisk = payload;
        renderInternalRiskDashboard(payload.data);
        renderRiskGovernanceDashboard(payload.data);
        renderInternalRiskWorkspace(payload.data, payload.meta || {});
        renderLifecycle();
        void loadRiskIntake();
    } catch (error) {
        console.info(error);
        if (sourceStatus) {
            sourceStatus.textContent = "内部风控服务暂不可用";
            sourceStatus.className = "data-mode-badge disabled";
        }
        document.getElementById("internal-dashboard-strip")?.classList.add("is-unavailable");
    }
}

let activeRiskIntakeCompanyId = "demo-ai-enterprise";

async function loadRiskIntake() {
    try {
        const [scopePayload, casesPayload] = await Promise.all([
            fetchBackendJson(`/risk-intake/scopes/${encodeURIComponent(activeRiskIntakeCompanyId)}`, { timeoutMs: 8000 }),
            fetchBackendJson(`/risk-intake/external-cases?company_id=${encodeURIComponent(activeRiskIntakeCompanyId)}`, { timeoutMs: 8000 }),
        ]);
        if (supplyState.source === "developer_debug") return;
        let syncBatches = [];
        try {
            const syncPayload = await fetchBackendJson(`/risk-intake/external-cases/sync-summary?company_id=${encodeURIComponent(activeRiskIntakeCompanyId)}&limit=1`, { timeoutMs: 8000 });
            syncBatches = syncPayload.items || [];
        } catch (error) {
            console.info(error);
        }
        backendState.riskIntake = { scope: scopePayload.data, cases: casesPayload.items || [], syncBatches };
        renderRiskGovernanceDashboard(backendState.internalRisk?.data);
        renderLifecycle();
    } catch (error) {
        console.info(error);
        backendState.riskIntake = null;
        renderLifecycle();
    }
}

async function syncRiskIntakeCases() {
    await fetchBackendJson(`/risk-intake/external-cases/sync?company_id=${encodeURIComponent(activeRiskIntakeCompanyId)}`, {
        method: "POST",
        timeoutMs: 12000,
    });
    await loadRiskIntake();
}

function showExternalIntakeDrawer(intakeId) {
    const item = (backendState.riskIntake?.cases || []).find((caseItem) => caseItem.intake_id === intakeId);
    const drawer = document.getElementById("internal-review-drawer");
    if (!item || !drawer) return;
    const scope = backendState.riskIntake?.scope;
    const objects = item.matched_objects.map((match) => {
        const object = (scope?.objects || []).find((candidate) => candidate.object_id === match.object_id);
        return `${object?.name || match.object_id}（${match.match_type}）`;
    }).join("、");
    const projectCandidates = [...new Map(
        item.matched_objects.map((match) => (scope?.objects || []).find((candidate) => candidate.object_id === match.object_id))
            .filter((object) => object?.project_id)
            .map((object) => [object.project_id, object])
    ).entries()].map(([projectId, object]) => ({
        projectId,
        name: (scope?.objects || []).find((candidate) => candidate.object_id === projectId)?.name || object.name || projectId,
    }));
    const projectSelection = projectCandidates.length > 1
        ? `<label>受影响项目<select id="external-intake-project" required><option value="">请选择受影响项目</option>${projectCandidates.map((project) => `<option value="${escapeHtml(project.projectId)}">${escapeHtml(project.name)}</option>`).join("")}</select></label>`
        : projectCandidates.length === 1
            ? `<input id="external-intake-project" type="hidden" value="${escapeHtml(projectCandidates[0].projectId)}">`
            : `<div class="internal-drawer-notice"><strong>未识别受影响项目</strong><p>请先在企业范围中登记该对象归属的项目，再登记为风险线索。</p></div>`;
    drawer.hidden = false;
    drawer.innerHTML = `
        <div class="internal-drawer-head"><div><span class="metric-label">待核实外部信息</span><h2>${escapeHtml(item.signal.title)}</h2><p>外部信息不会自动成为企业风险；请确认关联对象、信息来源和实际影响。</p></div><button class="icon-button" type="button" aria-label="关闭核实窗口" data-internal-review-close>&times;</button></div>
        <div class="internal-drawer-meta"><span>关联对象 <strong>${escapeHtml(objects || "未关联")}</strong></span><span>信息时间 <strong>${escapeHtml(item.signal.as_of)}</strong></span><span>可靠程度 <strong>${Math.round(Number(item.signal.confidence || 0) * 100)}%</strong></span></div>
        <div class="internal-drawer-notice"><strong>关联依据</strong><p>${escapeHtml(item.matched_objects.map((match) => `${match.rule_id}：${match.matched_values.join("、")}`).join("；"))}</p><strong>原始信息</strong><p>${escapeHtml(item.signal.evidence || "未提供摘要")}</p></div>
        <div class="internal-review-form"><label>核实人<input id="external-intake-reviewer" type="text" placeholder="填写姓名或岗位"></label>${projectSelection}<label class="internal-form-wide">核实说明<textarea id="external-intake-conclusion" rows="3" placeholder="说明关联对象、影响范围和建议采取的处理措施"></textarea></label><div class="internal-drawer-actions"><span>登记后只形成一条待核实风险线索；仍需系统辅助分析和人工确认，才会进入风险清单。</span><div class="internal-event-actions"><button class="btn btn-primary" type="button" data-external-intake-triage="promote" data-intake-id="${escapeHtml(item.intake_id)}">登记为风险线索</button><button class="btn" type="button" data-external-intake-triage="reject" data-intake-id="${escapeHtml(item.intake_id)}">不作为风险线索</button></div></div></div>
    `;
    drawer.querySelectorAll("[data-external-intake-triage]").forEach((button) => {
        button.addEventListener("click", () => recordExternalIntakeTriage(button.dataset.intakeId, button.dataset.externalIntakeTriage, button));
    });
    focusInternalDetail(drawer);
}

async function recordExternalIntakeTriage(intakeId, decision, button) {
    const reviewer = document.getElementById("external-intake-reviewer")?.value.trim();
    const conclusion = document.getElementById("external-intake-conclusion")?.value.trim();
    const projectId = document.getElementById("external-intake-project")?.value.trim();
    if (!reviewer || !conclusion) {
        button.textContent = "请填写核实人和说明";
        return;
    }
    if (decision === "promote" && !projectId) {
        button.textContent = "请选择受影响项目";
        return;
    }
    const originalLabel = button.textContent;
    button.disabled = true;
    button.textContent = "记录中";
    try {
        await fetchBackendJson(`/risk-intake/external-cases/${encodeURIComponent(intakeId)}/triage`, {
            method: "PATCH",
            body: JSON.stringify({ decision, reviewer, conclusion, project_id: projectId || undefined }),
            timeoutMs: 10000,
        });
        document.getElementById("internal-review-drawer").hidden = true;
        await Promise.all([loadRiskIntake(), loadInternalRiskWorkflow()]);
    } catch (error) {
        console.info(error);
        button.textContent = "记录失败";
        window.setTimeout(() => { button.textContent = originalLabel; button.disabled = false; }, 1400);
    }
}

async function advanceInternalTask(taskId, status, button, update = {}) {
    if (!taskId || !status) return;
    const originalLabel = button?.textContent;
    if (button) {
        button.disabled = true;
        button.textContent = "更新中";
    }
    try {
        await fetchBackendJson(`/internal-risk/tasks/${encodeURIComponent(taskId)}`, {
            method: "PATCH",
            body: JSON.stringify({
                status,
                changed_by: "internal-risk-workbench",
                note: update.note || `工作台更新为${internalTaskStatusLabels[status] || status}`,
                evidence_refs: update.evidenceRefs,
            }),
            timeoutMs: 8000,
        });
        await loadInternalRiskWorkflow();
        if (update.reopenTaskId) showInternalTaskDrawer(update.reopenTaskId);
    } catch (error) {
        console.info(error);
        if (button) {
            button.textContent = "更新失败";
            window.setTimeout(() => { button.textContent = originalLabel; button.disabled = false; }, 1400);
        }
    }
}

async function recordInternalReviewDecision(reviewId, button) {
    const reviewer = document.getElementById("internal-reviewer")?.value.trim();
    const conclusion = document.getElementById("internal-review-conclusion")?.value.trim();
    const status = document.getElementById("internal-review-decision")?.value;
    if (!reviewer || !conclusion || !status) {
        if (button) button.textContent = "请填写复核人与结论";
        return;
    }
    const originalLabel = button?.textContent;
    if (button) {
        button.disabled = true;
        button.textContent = "记录中";
    }
    try {
        await fetchBackendJson(`/internal-risk/reviews/${encodeURIComponent(reviewId)}`, {
            method: "PATCH",
            body: JSON.stringify({ status, reviewer, conclusion }),
            timeoutMs: 8000,
        });
        document.getElementById("internal-review-drawer").hidden = true;
        await loadInternalRiskWorkflow();
    } catch (error) {
        console.info(error);
        if (button) {
            button.textContent = "记录失败";
            window.setTimeout(() => { button.textContent = originalLabel; button.disabled = false; }, 1400);
        }
    }
}

function setupInternalRiskControls() {
    document.getElementById("internal-risk-refresh")?.addEventListener("click", loadInternalRiskWorkflow);
    document.getElementById("management-assistance-refresh")?.addEventListener("click", async (event) => {
        const button = event.currentTarget;
        const label = button.textContent;
        button.disabled = true;
        button.textContent = "生成中";
        try {
            await fetchBackendJson(`/internal-risk/management-assistance/refresh?company_id=${encodeURIComponent(activeRiskIntakeCompanyId)}`, {
                method: "POST", timeoutMs: 8000,
            });
            await loadInternalRiskWorkflow();
        } catch (error) {
            console.info(error);
            button.textContent = "生成失败";
            window.setTimeout(() => { button.textContent = label; button.disabled = false; }, 1500);
            return;
        }
        button.textContent = label;
        button.disabled = false;
    });
    document.getElementById("internal-risk-event-create")?.addEventListener("click", () => openInternalInboxItem("event"));
    document.getElementById("internal-risk-level-filter")?.addEventListener("change", (event) => {
        internalRiskFilters.level = event.target.value;
        renderInternalRiskWorkspace(backendState.internalRisk?.data, backendState.internalRisk?.meta || {});
    });
    document.getElementById("internal-stage-filter")?.addEventListener("change", (event) => {
        internalRiskFilters.stage = event.target.value;
        renderInternalRiskWorkspace(backendState.internalRisk?.data, backendState.internalRisk?.meta || {});
    });
    document.getElementById("dashboard-internal-open")?.addEventListener("click", () => {
        document.querySelector('.nav-item[data-tab="internal"]')?.click();
    });
    document.getElementById("internal-process-rail")?.addEventListener("click", (event) => {
        const button = event.target.closest("[data-internal-stage]");
        if (!button) return;
        internalInboxState.stage = button.dataset.internalStage;
        internalInboxState.initialized = true;
        clearInternalDetailSelection();
    });
    document.getElementById("internal-stage-nav")?.addEventListener("click", (event) => {
        const button = event.target.closest("[data-internal-stage]");
        if (!button) return;
        internalInboxState.stage = button.dataset.internalStage;
        internalInboxState.initialized = true;
        clearInternalDetailSelection();
    });
    document.getElementById("internal-work-list")?.addEventListener("click", (event) => {
        const row = event.target.closest("[data-internal-item-type]");
        if (!row) return;
        openInternalInboxItem(row.dataset.internalItemType, row.dataset.internalItemId);
    });
    document.getElementById("internal-gate-list")?.addEventListener("click", (event) => {
        const button = event.target.closest("[data-internal-gate-id]");
        if (button) showInternalGateDetail(button.dataset.internalGateId);
    });
    document.getElementById("internal-gate-detail")?.addEventListener("click", (event) => {
        const button = event.target.closest("[data-internal-gate-decision-open]");
        if (button) showInternalGateDecisionDrawer(button.dataset.internalGateDecisionOpen);
    });
    document.getElementById("internal-risk-ledger")?.addEventListener("click", (event) => {
        const button = event.target.closest("[data-internal-risk-close]");
        if (button) showInternalRiskClosureDrawer(button.dataset.internalRiskClose);
    });
    document.getElementById("internal-task-list")?.addEventListener("click", (event) => {
        const button = event.target.closest("[data-internal-task-open]");
        if (button) openInternalTaskDrawer(button.dataset.internalTaskOpen);
    });
    document.getElementById("internal-event-list")?.addEventListener("click", (event) => {
        const button = event.target.closest("[data-internal-event-open]");
        if (button) showInternalEventDrawer(button.dataset.internalEventOpen);
    });
    document.getElementById("internal-event-drawer")?.addEventListener("click", (event) => {
        if (event.target.closest("[data-internal-event-close]")) {
            clearInternalDetailSelection();
            return;
        }
        const assessButton = event.target.closest("[data-internal-event-assess]");
        if (assessButton) {
            createAndAssessInternalEvent(assessButton);
            return;
        }
        const projectSourceButton = event.target.closest("[data-internal-project-source-open]");
        if (projectSourceButton) {
            openInternalProjectSource(projectSourceButton.dataset.internalProjectSourceOpen);
            return;
        }
        const confirmButton = event.target.closest("[data-internal-event-confirm]");
        const eventId = confirmButton?.dataset.internalEventId;
        if (confirmButton && eventId) confirmInternalEvent(eventId, confirmButton.dataset.internalEventConfirm, confirmButton);
    });
    document.getElementById("internal-task-drawer")?.addEventListener("click", (event) => {
        const closeButton = event.target.closest("[data-internal-task-close]");
        if (closeButton) {
            clearInternalDetailSelection();
            return;
        }
        const uploadButton = event.target.closest("[data-internal-evidence-upload]");
        if (uploadButton) {
            document.getElementById("internal-task-evidence-upload")?.click();
            return;
        }
        const previewButton = event.target.closest("[data-internal-evidence-preview]");
        if (previewButton) {
            previewInternalTaskEvidence(previewButton.dataset.internalEvidencePreview);
            return;
        }
        const downloadButton = event.target.closest("[data-internal-evidence-download]");
        if (downloadButton) {
            downloadInternalTaskEvidence(downloadButton.dataset.internalEvidenceDownload, "content");
            return;
        }
        const sourceButton = event.target.closest("[data-internal-evidence-source]");
        if (sourceButton) {
            downloadInternalTaskEvidence(sourceButton.dataset.internalEvidenceSource, "source");
            return;
        }
        const openButton = event.target.closest("[data-internal-evidence-open]");
        if (openButton) {
            openInternalTaskEvidence(openButton.dataset.internalEvidenceOpen, openButton);
            return;
        }
        const projectSourceButton = event.target.closest("[data-internal-project-source-open]");
        if (projectSourceButton) {
            openInternalProjectSource(projectSourceButton.dataset.internalProjectSourceOpen);
            return;
        }
        const saveButton = event.target.closest("[data-internal-task-save]");
        if (!saveButton) return;
        const note = document.getElementById("internal-task-note")?.value.trim();
        const evidenceRefs = (document.getElementById("internal-task-evidence")?.value || "")
            .split(",")
            .map((value) => value.trim())
            .filter(Boolean);
        const documentRefs = [...document.querySelectorAll("#internal-task-documents option:checked")]
            .map((option) => option.value)
            .filter(Boolean);
        advanceInternalTask(saveButton.dataset.internalTaskSave, saveButton.dataset.nextStatus, saveButton, {
            note,
            evidenceRefs: [...new Set([...evidenceRefs, ...documentRefs])],
            reopenTaskId: saveButton.dataset.internalTaskSave,
        });
    });
    document.getElementById("internal-task-drawer")?.addEventListener("change", (event) => {
        const input = event.target.closest("#internal-task-evidence-upload");
        if (input?.files?.length) uploadInternalTaskEvidence(input);
    });
    document.getElementById("internal-review-list")?.addEventListener("click", (event) => {
        const button = event.target.closest("[data-internal-review-open]");
        if (!button) return;
        const review = backendState.internalRisk?.data?.manual_reviews?.find((item) => item.review_id === button.dataset.internalReviewOpen);
        if (review?.target_type === "risk_gate") showInternalGateDecisionDrawer(review.target_id);
        else showInternalReviewDrawer(button.dataset.internalReviewOpen);
    });
    document.getElementById("internal-review-drawer")?.addEventListener("click", (event) => {
        if (event.target.closest("[data-internal-review-close]")) {
            clearInternalDetailSelection();
            return;
        }
        const projectSourceButton = event.target.closest("[data-internal-project-source-open]");
        if (projectSourceButton) {
            openInternalProjectSource(projectSourceButton.dataset.internalProjectSourceOpen);
            return;
        }
        const gateButton = event.target.closest("[data-internal-gate-decision-save]");
        if (gateButton) {
            recordInternalGateDecision(gateButton.dataset.internalGateDecisionSave, gateButton.dataset.internalGateDecision, gateButton);
            return;
        }
        const riskCloseButton = event.target.closest("[data-internal-risk-close-save]");
        if (riskCloseButton) {
            closeInternalRisk(riskCloseButton.dataset.internalRiskCloseSave, riskCloseButton);
            return;
        }
        const button = event.target.closest("[data-internal-review-save]");
        if (button) recordInternalReviewDecision(button.dataset.internalReviewSave, button);
    });
}

function getProductMeta(product) {
    if (product.externalRiskDashboard?.meta) return product.externalRiskDashboard.meta;
    return Object.values(product).find((payload) => payload?.meta)?.meta || null;
}

function applyBackendProductData(product) {
    // The dashboard is driven by the internal risk workflow, not product fixtures.
    // This avoids showing an unsupported score or English units as live risk data.
    applyExternalRiskDashboardData(product.externalRiskDashboard?.data, product.externalRiskDashboard?.meta);
    applyLifecycleData(product.lifecycleRisk?.data);
    applyLegalWorkspaceData(product.legalWorkspace?.data);
}

async function refreshExternalRiskDashboard() {
    if (supplyState.source === "developer_debug") return;
    const panel = document.getElementById("external-risk-panel");
    const mode = document.getElementById("external-risk-mode");
    if (panel) panel.classList.add("loading");
    if (mode) mode.textContent = "refreshing";
    try {
        const payload = await fetchBackendJson("/external-risk/market-dashboard", { timeoutMs: 10000 });
        applyExternalRiskDashboardData(payload.data, payload.meta);
        renderBackendStatus("online", `后端已连接 · ${externalDataSourceLabel(payload.meta?.data_source || "external-risk")}`);
    } catch (error) {
        if (panel) panel.classList.add("error");
        if (mode) {
            mode.textContent = "unavailable";
            mode.className = "data-mode-badge disabled";
        }
        console.info(error);
    } finally {
        if (panel) panel.classList.remove("loading");
    }
}

function setupExternalRiskControls() {
    document.getElementById("external-risk-refresh")?.addEventListener("click", refreshExternalRiskDashboard);
}

function setupQuoteControls() {
    normalizeQuoteSelectLabels();
    document.getElementById("quote-interval-tabs")?.addEventListener("click", (event) => {
        const button = event.target.closest("button[data-interval]");
        if (!button) return;
        quoteState.interval = button.dataset.interval || "intraday";
        resetQuoteWindow();
        document.querySelectorAll("#quote-interval-tabs button").forEach((item) => {
            item.classList.toggle("active", item === button);
        });
        refreshQuoteSeries();
    });

    document.getElementById("quote-symbol-select")?.addEventListener("change", (event) => {
        quoteState.symbol = event.target.value || "sh000001";
        resetQuoteWindow();
        refreshQuoteSeries();
    });

    const quoteSearch = document.getElementById("quote-symbol-search");
    const quoteSearchButton = document.getElementById("quote-symbol-search-button");
    const runQuoteSearch = () => {
        const symbol = resolveMarketSymbol(quoteSearch?.value);
        if (!symbol) return;
        quoteState.symbol = symbol;
        quoteState.manualUntil = Date.now() + 8000;
        resetQuoteWindow();
        syncQuoteSymbolSelect(symbol);
        refreshQuoteSeries();
    };
    quoteSearchButton?.addEventListener("click", runQuoteSearch);
    quoteSearch?.addEventListener("keydown", (event) => {
        if (event.key !== "Enter") return;
        event.preventDefault();
        runQuoteSearch();
    });

    setupQuoteChartDrag();
}

function setupGlobalSearch() {
    const input = document.getElementById("global-search-input");
    if (!input) return;
    input.addEventListener("keydown", (event) => {
        if (event.key !== "Enter") return;
        event.preventDefault();
        const symbol = resolveMarketSymbol(input.value);
        if (!symbol) return;
        quoteState.symbol = symbol;
        quoteState.manualUntil = Date.now() + 8000;
        resetQuoteWindow();
        syncQuoteSymbolSelect(symbol);
        document.querySelector(`.nav-item[data-tab="market"]`)?.click();
        const quoteSearch = document.getElementById("quote-symbol-search");
        if (quoteSearch) quoteSearch.value = input.value;
        refreshQuoteSeries();
    });
}

function startQuoteAutoRefresh() {
    if (quoteState.refreshTimer) window.clearInterval(quoteState.refreshTimer);
    quoteState.refreshTimer = window.setInterval(() => {
        if (document.hidden) return;
        if (Date.now() < quoteState.manualUntil) return;
        refreshQuoteSeries();
    }, quoteState.refreshMs);
}

function resetQuoteWindow() {
    quoteState.windowEnd = null;
    quoteState.dragStartX = null;
    quoteState.dragStartWindowEnd = null;
}

function setupQuoteChartDrag() {
    const chart = document.getElementById("quote-chart");
    if (!chart) return;
    chart.addEventListener("pointerdown", (event) => {
        if (quoteState.interval === "intraday" || quoteState.points.length <= quoteState.windowSize) return;
        quoteState.dragStartX = event.clientX;
        quoteState.dragStartWindowEnd = getQuoteWindowEnd();
        chart.setPointerCapture?.(event.pointerId);
        chart.classList.add("dragging");
    });
    chart.addEventListener("pointermove", (event) => {
        if (quoteState.dragStartX == null || quoteState.dragStartWindowEnd == null) return;
        const deltaX = event.clientX - quoteState.dragStartX;
        const pointsPerPixel = quoteState.windowSize / Math.max(chart.clientWidth || 1, 1);
        const deltaPoints = Math.round(-deltaX * pointsPerPixel);
        const maxEnd = quoteState.points.length;
        const minEnd = Math.min(quoteState.windowSize, maxEnd);
        quoteState.windowEnd = clamp(quoteState.dragStartWindowEnd + deltaPoints, minEnd, maxEnd);
        renderKlineQuoteChart(quoteState.points);
    });
    const stopDrag = (event) => {
        if (quoteState.dragStartX == null) return;
        quoteState.dragStartX = null;
        quoteState.dragStartWindowEnd = null;
        chart.releasePointerCapture?.(event.pointerId);
        chart.classList.remove("dragging");
    };
    chart.addEventListener("pointerup", stopDrag);
    chart.addEventListener("pointercancel", stopDrag);
    chart.addEventListener("pointerleave", stopDrag);
}

const QUOTE_INTERVAL_LABELS = {
    intraday: "分时",
    daily: "日K",
    weekly: "周K",
    monthly: "月K",
};

const A_SHARE_AFTER_HOURS_EFFECTIVE = new Date("2026-07-06T00:00:00+08:00").getTime();

const WORKFLOW_CATEGORIES = {
    resource: "资源与大宗",
    chemical: "化学品期货",
    substrate: "玻璃基板与面板",
    specialty_gas: "电子特气",
    semiconductor_material: "半导体材料",
    equipment: "半导体设备",
    memory: "存储链",
    optical: "光模块与通信",
    terminal: "终端与品牌",
    logistics: "物流与能源",
    macro: "指数利率",
};

const WORKFLOW_FUTURES_VENUES = {
    hf_CAD: "LME", hf_AHD: "LME", hf_SND: "LME", hf_NID: "LME", hf_ZSD: "LME", hf_PBD: "LME",
    hf_SI: "COMEX", hf_GC: "COMEX", hf_XPD: "NYMEX", hf_XPT: "NYMEX", hf_NG: "NYMEX", hf_CL: "NYMEX",
    hf_C: "CBOT", hf_S: "CBOT", hf_W: "CBOT",
    if_EC0: "上期能源", if_SC0: "上期能源", if_LU0: "上期能源",
    if_SI0: "广期所",
    if_AU0: "上期所", if_AG0: "上期所", if_CU0: "上期所", if_AL0: "上期所", if_ZN0: "上期所",
    if_NI0: "上期所", if_SN0: "上期所", if_RB0: "上期所", if_HC0: "上期所", if_BU0: "上期所",
    if_FU0: "上期所", if_RU0: "上期所", if_SP0: "上期所", if_SH0: "上期所",
    if_I0: "大商所", if_J0: "大商所", if_JM0: "大商所", if_EG0: "大商所", if_PP0: "大商所",
    if_L0: "大商所", if_V0: "大商所", if_EB0: "大商所", if_PG0: "大商所", if_P0: "大商所",
    if_Y0: "大商所", if_M0: "大商所", if_A0: "大商所", if_LH0: "大商所", if_JD0: "大商所",
    if_SA0: "郑商所", if_MA0: "郑商所", if_TA0: "郑商所", if_FG0: "郑商所", if_UR0: "郑商所",
    if_PX0: "郑商所", if_PF0: "郑商所", if_RM0: "郑商所", if_OI0: "郑商所", if_SR0: "郑商所",
    if_CF0: "郑商所",
    if_IF0: "中金所", if_IH0: "中金所", if_IC0: "中金所", if_IM0: "中金所",
    if_T0: "中金所", if_TF0: "中金所", if_TS0: "中金所",
};

const WORKFLOW_FUTURES_EXCHANGE_CODES = {
    LME: "LME", COMEX: "COMEX", NYMEX: "NYMEX", CBOT: "CBOT",
    "上期能源": "INE", "广期所": "GFEX", "上期所": "SHFE", "大商所": "DCE",
    "郑商所": "CZCE", "中金所": "CFFEX",
};

function workflowFuturesDisplayName(symbol, name) {
    const displayName = String(name || "").trim();
    const venue = WORKFLOW_FUTURES_VENUES[String(symbol || "").trim()];
    if (!displayName || !venue || displayName.includes("（")) return displayName;
    return `${displayName}（${venue}）`;
}

const WORKFLOW_NODE_LIBRARY = [
    { symbol: "hf_CAD", name: "伦铜", category: "resource", group: "基础金属", lane: "上游资源", note: "电力、PCB、连接器和设备成本敏感项", recommendations: ["hf_AHD", "hf_SND"] },
    { symbol: "hf_XPT", name: "铂金", category: "resource", group: "贵金属/催化", lane: "上游资源", note: "电子化学品、催化和贵金属成本压力参考", recommendations: ["hf_XPD", "hf_GC"] },
    { symbol: "hf_XPD", name: "钯金", category: "resource", group: "贵金属/催化", lane: "上游资源", note: "电子与汽车供应链贵金属价格参考", recommendations: ["hf_XPT", "hf_GC"] },
    { symbol: "hf_NID", name: "伦镍", category: "resource", group: "基础金属", lane: "上游资源", note: "合金、电池和精密部件成本参考", recommendations: ["hf_CAD", "hf_AHD"] },
    { symbol: "hf_SND", name: "伦锡", category: "resource", group: "焊料/封装", lane: "上游资源", note: "焊料、电子组装和封装链条参考", recommendations: ["hf_CAD", "hf_PBD"] },
    { symbol: "hf_AHD", name: "伦铝", category: "resource", group: "结构/散热金属", lane: "上游资源", note: "结构件、散热件和电网材料参考", recommendations: ["hf_CAD", "hf_ZSD"] },
    { symbol: "hf_ZSD", name: "伦锌", category: "resource", group: "镀层/结构金属", lane: "上游资源", note: "镀层、结构件和耐腐蚀材料参考", recommendations: ["hf_AHD", "hf_PBD"] },
    { symbol: "hf_PBD", name: "伦铅", category: "resource", group: "工业金属", lane: "上游资源", note: "电池和部分工业材料价格参考", recommendations: ["hf_ZSD", "hf_SND"] },
    { symbol: "if_CU0", name: "沪铜主连", category: "resource", group: "基础金属", lane: "上游资源", note: "国内电网、PCB 与连接器成本锚", recommendations: ["hf_CAD", "if_AL0"] },
    { symbol: "if_AL0", name: "沪铝主连", category: "resource", group: "结构/散热金属", lane: "上游资源", note: "国内结构件、散热件与电网材料成本锚", recommendations: ["hf_AHD", "if_CU0"] },
    { symbol: "if_SN0", name: "沪锡主连", category: "resource", group: "焊料/封装", lane: "上游资源", note: "电子焊料、封装与组装成本锚", recommendations: ["hf_SND", "if_CU0"] },
    { symbol: "if_NI0", name: "沪镍主连", category: "resource", group: "合金/电池", lane: "上游资源", note: "合金、电池与精密部件成本锚", recommendations: ["hf_NID", "if_SN0"] },
    { symbol: "if_SI0", name: "工业硅主连", category: "resource", group: "硅系原料", lane: "上游资源", note: "硅材料、半导体和光伏产业链成本参考", recommendations: ["if_CU0", "if_SA0"] },
    { symbol: "if_SA0", name: "纯碱主连", category: "substrate", group: "玻璃基板原料", lane: "上游材料", note: "玻璃、光伏和部分化工材料成本参考", recommendations: ["us_GLW", "sh600552"] },
    { symbol: "if_EG0", name: "乙二醇主连", category: "chemical", group: "电子化学品", lane: "半导体材料", note: "电子化学品与溶剂成本代理，需结合场景节点确认", recommendations: ["if_MA0", "sh688146"] },
    { symbol: "if_PP0", name: "聚丙烯主连", category: "chemical", group: "封装聚合物", lane: "封装测试", note: "塑封与包装材料成本代理，需结合场景节点确认", recommendations: ["if_TA0", "sh600584"] },
    { symbol: "if_L0", name: "聚乙烯主连", category: "chemical", group: "封装聚合物", lane: "封装测试", note: "聚合物包装材料成本代理，需结合场景节点确认", recommendations: ["if_PP0", "sh600584"] },
    { symbol: "if_V0", name: "PVC主连", category: "chemical", group: "工业聚合物", lane: "外部成本", note: "工业聚合物与线缆材料成本代理，需结合场景节点确认", recommendations: ["if_PP0", "if_SH0"] },
    { symbol: "if_MA0", name: "甲醇主连", category: "chemical", group: "电子化学品", lane: "半导体材料", note: "溶剂与化工原料成本代理，需结合场景节点确认", recommendations: ["if_EG0", "if_SH0"] },
    { symbol: "if_TA0", name: "PTA主连", category: "chemical", group: "化工与薄膜", lane: "封装测试", note: "聚酯薄膜及包装材料成本代理，需结合场景节点确认", recommendations: ["if_PP0", "if_FG0"] },
    { symbol: "if_SH0", name: "烧碱主连", category: "chemical", group: "湿电子化学品", lane: "半导体材料", note: "清洗、湿法工艺化学品成本代理，需结合场景节点确认", recommendations: ["if_EG0", "sh688146"] },
    { symbol: "if_FG0", name: "玻璃主连", category: "chemical", group: "基板玻璃", lane: "玻璃基板与面板", note: "基板玻璃与封装材料成本代理，需结合场景节点确认", recommendations: ["if_SA0", "sh600552"] },
    { symbol: "if_UR0", name: "尿素主连", category: "chemical", group: "工业化学品", lane: "外部成本", note: "工业化学品成本代理，需结合场景节点确认", recommendations: ["if_MA0", "if_EG0"] },
    { symbol: "if_EB0", name: "苯乙烯主连", category: "chemical", group: "聚合物原料", lane: "封装测试", note: "聚合物与包装材料成本代理，需结合场景节点确认", recommendations: ["if_PP0", "if_L0"] },
    { symbol: "if_PX0", name: "对二甲苯主连", category: "chemical", group: "聚酯原料", lane: "封装测试", note: "聚酯薄膜原料成本代理，需结合场景节点确认", recommendations: ["if_TA0", "if_PF0"] },
    { symbol: "if_PF0", name: "短纤主连", category: "chemical", group: "聚酯材料", lane: "封装测试", note: "聚酯材料成本代理，需结合场景节点确认", recommendations: ["if_PX0", "if_TA0"] },
    { symbol: "if_PG0", name: "液化石油气主连", category: "chemical", group: "能源化工", lane: "外部成本", note: "能源化工与物流成本代理，需结合场景节点确认", recommendations: ["hf_CL", "if_SC0"] },
    { symbol: "us_GLW", name: "康宁", category: "substrate", group: "玻璃基板", lane: "玻璃基板", note: "显示玻璃、光纤和特种玻璃材料需求锚", recommendations: ["sh600552", "sz000725", "sz000100"] },
    { symbol: "sh600552", name: "凯盛科技", category: "substrate", group: "玻璃基板", lane: "玻璃基板", note: "显示材料、超薄玻璃和电子玻璃链条参考", recommendations: ["us_GLW", "sh600707"] },
    { symbol: "sh600707", name: "彩虹股份", category: "substrate", group: "面板/显示玻璃", lane: "面板制造", note: "显示面板和基板玻璃相关产能与价格参考", recommendations: ["sz000725", "sz000100"] },
    { symbol: "sz000725", name: "京东方A", category: "substrate", group: "显示面板", lane: "面板制造", note: "显示面板、消费电子终端和订单周期参考", recommendations: ["sz000100", "sh600707"] },
    { symbol: "sz000100", name: "TCL科技", category: "substrate", group: "显示面板", lane: "面板制造", note: "大尺寸面板、半导体显示和周期价格参考", recommendations: ["sz000725", "sh600707"] },
    { symbol: "sh688146", name: "中船特气", category: "specialty_gas", group: "电子特气", lane: "半导体材料", note: "电子特气、刻蚀/清洗气体国产化供应参考", recommendations: ["sh688106", "sh688268"] },
    { symbol: "sh688106", name: "金宏气体", category: "specialty_gas", group: "电子特气", lane: "半导体材料", note: "大宗气体、电子特气和晶圆厂认证进度参考", recommendations: ["sh688146", "sh688268"] },
    { symbol: "sh688268", name: "华特气体", category: "specialty_gas", group: "电子特气", lane: "半导体材料", note: "特种气体、光刻/刻蚀工艺材料供应参考", recommendations: ["sh688146", "sh688106"] },
    { symbol: "bk_BK0877", name: "PCB", category: "semiconductor_material", group: "PCB/载板", lane: "电子制造材料", note: "电子材料与制造中游", recommendations: ["hf_CAD", "hf_SND"] },
    { symbol: "sh688981", name: "中芯国际", category: "semiconductor_material", group: "晶圆制造", lane: "晶圆制造", note: "晶圆制造、国产替代和产能利用率参考", recommendations: ["sh688008", "sh688012"] },
    { symbol: "sh688012", name: "中微公司", category: "equipment", group: "刻蚀设备", lane: "半导体设备", note: "刻蚀设备与先进制程资本开支参考", recommendations: ["sh688072", "bk_BK1326"] },
    { symbol: "sh688072", name: "拓荆科技", category: "equipment", group: "薄膜沉积设备", lane: "半导体设备", note: "薄膜沉积设备、先进制程扩产与国产替代参考", recommendations: ["sh688012", "bk_BK1326"] },
    { symbol: "bk_BK1326", name: "半导体设备", category: "equipment", group: "设备板块", lane: "半导体设备", note: "晶圆厂资本开支与设备国产化链条", recommendations: ["sh688012", "sh688072"] },
    { symbol: "sh688008", name: "澜起科技", category: "memory", group: "内存接口芯片", lane: "存储/服务器", note: "服务器内存接口芯片和AI服务器需求参考", recommendations: ["us_MU", "kr_000660"] },
    { symbol: "kr_005930", name: "三星电子", category: "memory", group: "存储/晶圆", lane: "存储/服务器", note: "DRAM、NAND、代工和全球电子供应链景气参考", recommendations: ["kr_000660", "us_WDC", "us_SNDK"] },
    { symbol: "kr_000660", name: "SK海力士", category: "memory", group: "HBM/DRAM", lane: "存储/服务器", note: "HBM、DRAM 和 AI 服务器存储需求锚", recommendations: ["kr_005930", "us_MU"] },
    { symbol: "us_MU", name: "美光科技", category: "memory", group: "DRAM/NAND", lane: "存储/服务器", note: "DRAM、NAND 周期和服务器需求参考", recommendations: ["kr_000660", "us_WDC"] },
    { symbol: "us_WDC", name: "西部数据", category: "memory", group: "NAND/HDD", lane: "存储/服务器", note: "NAND、HDD 和数据中心存储需求参考", recommendations: ["us_SNDK", "us_MU"] },
    { symbol: "us_SNDK", name: "闪迪", category: "memory", group: "NAND/消费存储", lane: "存储/服务器", note: "NAND、消费存储和西部数据分拆后存储资产参考", recommendations: ["us_WDC", "us_MU"] },
    { symbol: "sz300308", name: "中际旭创", category: "optical", group: "光模块", lane: "算力互联", note: "高速光模块、CPO和海外云厂商资本开支参考", recommendations: ["bk_BK1128", "bk_BK1590"] },
    { symbol: "bk_BK1128", name: "CPO概念", category: "optical", group: "CPO/光互联", lane: "算力互联", note: "AI算力网络、光模块和高速互联", recommendations: ["sz300308", "bk_BK1590"] },
    { symbol: "bk_BK1590", name: "通信设备", category: "optical", group: "通信设备", lane: "算力互联", note: "网络设备、运营商投资和算力基础设施", recommendations: ["bk_BK1128", "sz300308"] },
    { symbol: "bk_BK1037", name: "消费电子", category: "terminal", group: "终端需求", lane: "终端应用", note: "终端需求、库存周期和订单履约", recommendations: ["us_AAPL", "bk_BK1162"] },
    { symbol: "bk_BK1164", name: "AIPC", category: "terminal", group: "AI终端", lane: "终端应用", note: "AI终端换机与上游零部件拉动", recommendations: ["bk_BK1162", "us_AAPL"] },
    { symbol: "bk_BK1162", name: "AI手机", category: "terminal", group: "AI终端", lane: "终端应用", note: "手机端AI应用和消费电子需求", recommendations: ["bk_BK1164", "bk_BK1037"] },
    { symbol: "bk_BK1178", name: "AI眼镜", category: "terminal", group: "AI终端", lane: "终端应用", note: "新型终端和小批量供应链波动", recommendations: ["bk_BK1162", "bk_BK1037"] },
    { symbol: "us_AAPL", name: "苹果", category: "terminal", group: "消费电子品牌", lane: "终端应用", note: "消费电子终端需求、供应商订单和美元收入参考", recommendations: ["bk_BK1037", "sz000725"] },
    { symbol: "us_NVDA", name: "英伟达", category: "terminal", group: "AI算力需求", lane: "终端应用", note: "AI算力景气度和产业链需求锚", recommendations: ["us_MSFT", "bk_BK1128"] },
    { symbol: "us_MSFT", name: "微软", category: "terminal", group: "云资本开支", lane: "终端应用", note: "云计算资本开支和AI应用需求参考", recommendations: ["us_NVDA", "us_NDX"] },
    { symbol: "if_EC0", name: "欧线集运主连", category: "logistics", group: "海运物流", lane: "外部成本", note: "出口交付、海运成本和履约周期", recommendations: ["if_SC0", "hf_CL"] },
    { symbol: "if_SC0", name: "原油主连", category: "logistics", group: "能源成本", lane: "外部成本", note: "国内能源、化工和运输成本参考", recommendations: ["hf_CL", "if_EC0"] },
    { symbol: "if_FU0", name: "燃料油主连", category: "logistics", group: "航运燃料", lane: "外部成本", note: "船燃、航运与炼化成本锚", recommendations: ["if_EC0", "hf_CL"] },
    { symbol: "if_BU0", name: "沥青主连", category: "logistics", group: "基建与物流", lane: "外部成本", note: "道路运输、基建与石化成本锚", recommendations: ["if_FU0", "if_SC0"] },
    { symbol: "hf_CL", name: "原油", category: "logistics", group: "能源成本", lane: "外部成本", note: "能源、化工和物流成本参考", recommendations: ["if_SC0", "if_EC0"] },
    { symbol: "sh601857", name: "中国石油", category: "logistics", group: "石油开采/油运", lane: "能源供应", note: "原油供给、油运和地缘政治冲击参考", recommendations: ["sh600028", "sh600938", "if_SC0"] },
    { symbol: "sh600028", name: "中国石化", category: "logistics", group: "炼化/油运", lane: "能源供应", note: "炼化、成品油和原油运输成本参考", recommendations: ["sh601857", "sh600938", "if_SC0"] },
    { symbol: "sh600938", name: "中国海油", category: "logistics", group: "海上油气", lane: "能源供应", note: "海上油气供给和油价风险参考", recommendations: ["sh601857", "sh600028", "hf_CL"] },
    { symbol: "sh601919", name: "中远海控", category: "logistics", group: "集装箱航运", lane: "海运物流", note: "集运运价、航线扰动和港口拥堵参考", recommendations: ["if_EC0", "sh600026", "sh601872"] },
    { symbol: "sh600026", name: "中远海能", category: "logistics", group: "油运", lane: "海运物流", note: "油轮运输、航道安全和运力周转参考", recommendations: ["sh601872", "sh601919", "hf_CL"] },
    { symbol: "sh601872", name: "招商轮船", category: "logistics", group: "油运/干散货", lane: "海运物流", note: "油运和国际航线风险参考", recommendations: ["sh600026", "sh601919", "if_EC0"] },
    { symbol: "hf_GC", name: "纽约黄金", category: "macro", group: "避险资产", lane: "宏观金融", note: "避险情绪和实际利率压力参考", recommendations: ["bond_000012", "us_SPX"] },
    { symbol: "if_T0", name: "十年期国债主连", category: "macro", group: "利率/久期", lane: "宏观金融", note: "国内无风险利率、融资成本与估值折现率锚", recommendations: ["bond_000012", "if_IF0"] },
    { symbol: "if_IF0", name: "沪深300主连", category: "macro", group: "风险偏好", lane: "宏观金融", note: "A股大盘风险偏好与融资环境锚", recommendations: ["if_T0", "bk_BK1203"] },
    { symbol: "bond_000012", name: "国债指数", category: "macro", group: "利率/久期", lane: "宏观金融", note: "无风险利率、融资成本和估值折现率参考", recommendations: ["hf_GC", "us_SPX"] },
    { symbol: "us_NDX", name: "纳斯达克100", category: "macro", group: "科技指数", lane: "宏观金融", note: "全球科技风险偏好和美元流动性", recommendations: ["us_SPX", "us_NVDA"] },
    { symbol: "us_SPX", name: "标普500", category: "macro", group: "权益指数", lane: "宏观金融", note: "美股整体风险偏好和海外需求参考", recommendations: ["us_NDX", "bond_000012"] },
    { symbol: "bk_BK1203", name: "非银金融", category: "macro", group: "融资环境", lane: "宏观金融", note: "风险偏好、融资环境和上市公司估值压力参考", recommendations: ["bond_000012", "us_SPX"] },
    { symbol: "bk_BK0457", name: "电网设备", category: "terminal", group: "电力终端需求", lane: "终端应用", note: "电力基础设施、储能接入和制造端需求", recommendations: ["hf_CAD", "hf_AHD"] },
];

const DEFAULT_WORKFLOW_NODES = [
    { id: "node-soda", symbol: "if_SA0", x: 36, y: 34, group: "玻璃基板原料" },
    { id: "node-corning", symbol: "us_GLW", x: 356, y: 34, group: "玻璃基板" },
    { id: "node-boe", symbol: "sz000725", x: 676, y: 34, group: "显示面板" },
    { id: "node-consumer", symbol: "bk_BK1037", x: 996, y: 34, group: "终端需求" },
    { id: "node-aapl", symbol: "us_AAPL", x: 1316, y: 34, group: "消费电子品牌" },
    { id: "node-kaisheng", symbol: "sh600552", x: 356, y: 202, group: "玻璃基板" },
    { id: "node-irico", symbol: "sh600707", x: 676, y: 202, group: "显示面板" },
    { id: "node-tcl", symbol: "sz000100", x: 676, y: 370, group: "显示面板" },
    { id: "node-gas-cssc", symbol: "sh688146", x: 36, y: 570, group: "电子特气" },
    { id: "node-smic", symbol: "sh688981", x: 356, y: 570, group: "晶圆制造" },
    { id: "node-semi-equipment", symbol: "bk_BK1326", x: 676, y: 570, group: "设备板块" },
    { id: "node-cpo", symbol: "bk_BK1128", x: 996, y: 570, group: "CPO/光互联" },
    { id: "node-nvda", symbol: "us_NVDA", x: 1316, y: 570, group: "AI算力需求" },
    { id: "node-gas-jinhong", symbol: "sh688106", x: 36, y: 738, group: "电子特气" },
    { id: "node-naura-peer", symbol: "sh688012", x: 676, y: 738, group: "刻蚀设备" },
    { id: "node-memory-samsung", symbol: "kr_005930", x: 356, y: 938, group: "存储/晶圆" },
    { id: "node-memory-hynix", symbol: "kr_000660", x: 676, y: 938, group: "HBM/DRAM" },
    { id: "node-memory-wdc", symbol: "us_WDC", x: 996, y: 938, group: "NAND/HDD" },
    { id: "node-logistics", symbol: "if_EC0", x: 36, y: 1138, group: "海运物流" },
    { id: "node-rates", symbol: "bond_000012", x: 36, y: 1306, group: "利率/久期" },
];

const DEFAULT_WORKFLOW_LINKS = [
    { source: "node-soda", target: "node-corning", relation: "原料->玻璃基板" },
    { source: "node-soda", target: "node-kaisheng", relation: "原料->玻璃基板" },
    { source: "node-corning", target: "node-boe", relation: "玻璃基板->显示面板" },
    { source: "node-kaisheng", target: "node-irico", relation: "玻璃基板->显示面板" },
    { source: "node-boe", target: "node-consumer", relation: "面板->消费电子" },
    { source: "node-tcl", target: "node-consumer", relation: "面板->消费电子" },
    { source: "node-consumer", target: "node-aapl", relation: "终端需求锚" },
    { source: "node-gas-cssc", target: "node-smic", relation: "电子特气->晶圆制造" },
    { source: "node-gas-jinhong", target: "node-smic", relation: "电子特气->晶圆制造" },
    { source: "node-smic", target: "node-semi-equipment", relation: "晶圆厂资本开支->设备" },
    { source: "node-naura-peer", target: "node-cpo", relation: "设备景气->光互联" },
    { source: "node-semi-equipment", target: "node-cpo", relation: "设备/制程->光互联" },
    { source: "node-cpo", target: "node-nvda", relation: "光互联->AI算力" },
    { source: "node-memory-samsung", target: "node-memory-hynix", relation: "存储同业景气" },
    { source: "node-memory-hynix", target: "node-memory-wdc", relation: "存储周期传导" },
    { source: "node-memory-hynix", target: "node-nvda", relation: "HBM/存储->AI算力" },
    { source: "node-memory-wdc", target: "node-nvda", relation: "存储->数据中心" },
    { source: "node-logistics", target: "node-consumer", relation: "海运成本->交付" },
    { source: "node-rates", target: "node-nvda", relation: "利率/估值->科技需求" },
];

const workflowState = {
    nodes: [],
    links: [],
    quotes: new Map(),
    selectedNodeId: null,
    selectedLinkId: null,
    connectMode: false,
    connectSourceId: null,
    connectSourcePort: "right",
    drag: null,
    pan: null,
    panSuppressClick: false,
    dragSuppressClick: false,
    refreshTimer: null,
    quoteRefreshPromise: null,
    saveTimer: null,
    saveStatus: "idle",
    storagePath: "",
    revision: 0,
    conflict: null,
    supplierBindingsPending: false,
    supplyChainSync: null,
    loaded: false,
    readOnly: false,
    debugRunId: null,
    viewport: { zoom: 1, panX: 0, panY: 0, initialized: false, userAdjusted: false },
    canvasObserver: null,
};

async function refreshQuoteSeries() {
    const requestId = ++quoteState.requestId;
    const chart = document.getElementById("quote-chart");
    const meta = document.getElementById("quote-chart-meta");
    if (chart) chart.classList.add("loading");
    if (meta && !quoteState.points.length) meta.textContent = "加载中";
    try {
        const params = new URLSearchParams({
            symbol: quoteState.symbol,
            interval: quoteState.interval,
            _: String(Date.now()),
        });
        const payload = await fetchBackendJson(`/external-risk/quote-series?${params.toString()}`, { timeoutMs: 20000 });
        if (requestId !== quoteState.requestId) return;
        renderQuoteSeries(payload.data);
    } catch (error) {
        if (requestId !== quoteState.requestId) return;
        if (meta) meta.textContent = "暂不可用";
        renderEmptyQuoteChart("行情序列暂不可用");
        console.info(error);
    } finally {
        if (requestId === quoteState.requestId && chart) chart.classList.remove("loading");
    }
}

function quoteSourceLabel(source) {
    if (source === "provider_unavailable") return "真实历史暂不可用";
    if (source === "eastmoney_provider") return "东方财富";
    if (source === "yahoo_chart") return "Yahoo Finance";
    if (source === "live_provider") return "实时";
    if (source === "sina_global_futures") return "新浪全球期货";
    if (source === "sina_cn_futures") return "新浪期货";
    return source || "-";
}

function quoteReferenceLabel(data) {
    const basisLabels = {
        previous_close: "昨收基准",
        listing_reference: "上市首日 · 发行价/上市参考价",
        period_open: "区间开盘基准",
        first_available: "首个可用价基准",
    };
    const limitLabels = {
        new_listing_initial_period: "上市初期 · 不适用常规涨跌幅限制",
        main_normal_10pct: "主板 · 涨跌幅限制 ±10%",
        main_st_10pct: "主板 ST · 涨跌幅限制 ±10%",
        star_normal_20pct: "科创板 · 涨跌幅限制 ±20%",
        star_st_20pct: "科创板 ST · 涨跌幅限制 ±20%",
        chinext_normal_20pct: "创业板 · 涨跌幅限制 ±20%",
        chinext_st_20pct: "创业板 ST · 涨跌幅限制 ±20%",
        bse_normal_30pct: "北交所 · 涨跌幅限制 ±30%",
        bse_st_30pct: "北交所 ST · 涨跌幅限制 ±30%",
    };
    return [basisLabels[data?.change_basis], limitLabels[data?.price_limit_label]]
        .filter(Boolean)
        .join(" · ");
}

function renderQuoteSeries(data) {
    const title = document.getElementById("quote-chart-title");
    const meta = document.getElementById("quote-chart-meta");
    const rawPoints = Array.isArray(data?.points) ? data.points.filter((point) => Number.isFinite(Number(point.close))) : [];
    const points = data?.interval === "intraday" ? quoteIntradayDisplayPoints(rawPoints, data.symbol || quoteState.symbol) : rawPoints;
    if (title) title.textContent = standardInstrumentLabel(data?.name || data?.symbol || quoteState.symbol, data?.symbol || quoteState.symbol);
    if (!points.length) {
        if (meta) meta.textContent = `${QUOTE_INTERVAL_LABELS[data?.interval] || data?.interval || ""} · 暂无数据`;
        renderEmptyQuoteChart("暂无行情数据");
        return;
    }
    quoteState.points = points;
    if (quoteState.windowEnd == null || quoteState.windowEnd > points.length) {
        quoteState.windowEnd = points.length;
    }

    const displayPoints = data.interval === "intraday" ? points : quoteVisiblePoints(points);
    const serviceReference = Number(data?.reference_price);
    const baseline = Number.isFinite(serviceReference) && serviceReference > 0
        ? serviceReference
        : quoteZeroBaseline(displayPoints);
    const serviceMove = Number(data?.change_rate);
    const latestMove = Number.isFinite(serviceMove)
        ? serviceMove
        : quoteStats(displayPoints, baseline).move;
    const trend = trendClassForValue(latestMove);
    const marketTrend = marketTrendClassForValue(latestMove);
    if (meta) {
        const timestamp = data.source === "live_provider" && data.as_of ? ` · ${escapeHtml(data.as_of)}` : "";
        const reference = quoteReferenceLabel(data);
        const referenceHtml = reference ? ` · <span class="quote-reference">${escapeHtml(reference)}</span>` : "";
        meta.innerHTML = `${escapeHtml(QUOTE_INTERVAL_LABELS[data.interval] || data.interval)} · ${escapeHtml(quoteSourceLabel(data.source))}${timestamp}${referenceHtml} · <span class="quote-meta-move ${trend} ${marketTrend}">${formatPercentSigned(latestMove, 2)}</span>`;
    }

    if (data.interval === "intraday") {
        renderIntradayQuoteChart(points, trend, data.symbol || quoteState.symbol);
    } else {
        renderKlineQuoteChart(points);
    }
}

function standardInstrumentCode(rawSymbol) {
    const symbol = String(rawSymbol || "").trim();
    const mainland = symbol.match(/^(sh|sz|bj)(\d{6})$/i);
    if (mainland) return `${mainland[1].toUpperCase()}.${mainland[2]}`;
    const hongKong = symbol.match(/^hk_(\d{1,5})$/i);
    if (hongKong) return `HKEX.${hongKong[1].padStart(5, "0")}`;
    const korean = symbol.match(/^kr_(\d{6})$/i);
    if (korean) return `KRX.${korean[1]}`;
    if (/^us_/i.test(symbol)) return `US.${symbol.replace(/^us_/i, "").toUpperCase()}`;
    if (/^bk_/i.test(symbol)) return `EM.${symbol.replace(/^bk_/i, "").toUpperCase()}`;
    if (/^bond_/i.test(symbol)) return `CNI.${symbol.replace(/^bond_/i, "")}`;
    if (/^hf_/i.test(symbol)) return `HF.${symbol.replace(/^hf_/i, "").toUpperCase()}`;
    if (/^if_/i.test(symbol)) {
        const venue = WORKFLOW_FUTURES_VENUES[symbol];
        const exchange = WORKFLOW_FUTURES_EXCHANGE_CODES[venue] || "CNF";
        return `${exchange}.${symbol.replace(/^if_/i, "").toUpperCase()}`;
    }
    return symbol.toUpperCase();
}

function quoteDisplayName(name, symbol) {
    const displayName = String(name || "").trim();
    if (displayName && !/^[+-]?\d+(?:\.\d+)?%?$/.test(displayName)) return workflowFuturesDisplayName(symbol, displayName);
    const option = document.querySelector(`#quote-symbol-select option[value="${cssEscape(symbol)}"]`);
    return workflowFuturesDisplayName(symbol, option?.dataset.displayName?.trim() || option?.textContent?.trim() || workflowLibraryBySymbol(symbol).name || symbol);
}

function standardInstrumentLabel(name, symbol) {
    const displayName = quoteDisplayName(name, symbol);
    const code = standardInstrumentCode(symbol);
    return displayName && code ? `${displayName}（${code}）` : displayName || code;
}

function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
}

function formatPrice(value) {
    const number = Number(value);
    if (!Number.isFinite(number)) return "-";
    if (Math.abs(number) >= 1000) return number.toFixed(2);
    if (Math.abs(number) >= 100) return number.toFixed(2);
    if (Math.abs(number) >= 10) return number.toFixed(3);
    return number.toFixed(4);
}

function quoteZeroBaseline(points) {
    const firstWithBaseline = points.find((point) => Number.isFinite(Number(point.baseline_price)));
    if (firstWithBaseline) return Number(firstWithBaseline.baseline_price);
    const first = points.find((point) => Number.isFinite(Number(point.open)) || Number.isFinite(Number(point.close)));
    return Number(first?.open ?? first?.close ?? 0);
}

function quoteStats(points, baseline) {
    const closes = points.map((point) => Number(point.close)).filter(Number.isFinite);
    const highs = points.map((point) => Number(point.high ?? point.close)).filter(Number.isFinite);
    const lows = points.map((point) => Number(point.low ?? point.close)).filter(Number.isFinite);
    const last = points[points.length - 1] || {};
    const latest = Number(last.close);
    // Intraday pct_change from some providers is minute-over-minute. The pre-close baseline
    // is the only consistent source for the displayed daily change and zero line.
    const move = baseline ? (latest - baseline) / baseline : latestPointMove(points);
    return {
        latest,
        move,
        high: Math.max(...highs, ...closes),
        low: Math.min(...lows, ...closes),
    };
}

function quoteIntradayDisplayPoints(points, symbol = quoteState.symbol) {
    const valid = Array.isArray(points) ? points.filter((point) => Number.isFinite(Number(point?.close))) : [];
    if (valid.length < 2) return valid;
    if (/^(kr_|hk_)/i.test(symbol)) return valid;
    const domain = quoteIntradayDomain(valid, symbol);
    if (!Array.isArray(domain.segments) || !domain.segments.length) return valid;
    const latest = valid[valid.length - 1];
    const latestValue = quotePointDomainValue(latest, symbol, domain, valid.length - 1);
    if (!Number.isFinite(latestValue)) return valid;
    const closeValue = domain.segments[domain.segments.length - 1].max;
    const gapToClose = closeValue - latestValue;
    if (gapToClose <= 0 || gapToClose > 45) return valid;
    const nowValue = quoteCurrentDomainMinuteForSymbol(symbol, closeValue);
    if (nowValue < closeValue) return valid;
    return [
        ...valid,
        {
            ...latest,
            time: domain.labelEnd || latest.time,
            timestamp: Number.isFinite(Number(latest.timestamp)) ? Math.round(closeValue * 60) : latest.timestamp,
            synthetic_close_endpoint: true,
        },
    ];
}

function quoteCurrentDomainMinuteForSymbol(symbol, closeValue) {
    if (/^kr_/i.test(symbol)) return Date.now() / 60000;
    if (/^hk_/i.test(symbol)) return Date.now() / 60000;
    if (/^us_/i.test(symbol)) return Date.now() / 60000;
    if (closeValue > 24 * 60 * 1000) return Date.now() / 60000;
    const now = new Date();
    return now.getHours() * 60 + now.getMinutes();
}

function latestPointMove(points) {
    const latestPoint = points[points.length - 1] || {};
    const latest = Number(latestPoint.close);
    const explicit = Number(latestPoint.change_percent);
    if (Number.isFinite(explicit)) {
        return Math.abs(explicit) > 1 ? explicit / 100 : explicit;
    }
    const previous = [...points].slice(0, -1).reverse().find((point) => Number.isFinite(Number(point.close)));
    const previousClose = Number(previous?.close);
    if (Number.isFinite(latest) && Number.isFinite(previousClose) && previousClose !== 0) {
        return (latest - previousClose) / previousClose;
    }
    const baseline = Number(latestPoint.baseline_price);
    if (Number.isFinite(latest) && Number.isFinite(baseline) && baseline !== 0) {
        return (latest - baseline) / baseline;
    }
    return 0;
}

function quoteValueRange(values, paddingRatio = 0.08) {
    const finite = values.map(Number).filter(Number.isFinite);
    if (!finite.length) return { min: 0, max: 1, range: 1 };
    const min = Math.min(...finite);
    const max = Math.max(...finite);
    const rawRange = max === min ? Math.max(Math.abs(max) * 0.01, 1) : max - min;
    const pad = rawRange * paddingRatio;
    const paddedMin = min - pad;
    const paddedMax = max + pad;
    return {
        min: paddedMin,
        max: paddedMax,
        range: Math.max(paddedMax - paddedMin, 1e-9),
    };
}

function quotePointOverlay({ width, pad, baseline, stats, latestX, latestY, highY, lowY, zeroY, trend, rangeLabel = "" }) {
    const right = width - pad.right;
    const marketTrend = marketTrendClassForValue(stats.move);
    const highMove = baseline ? (stats.high - baseline) / baseline : 0;
    const lowMove = baseline ? (stats.low - baseline) / baseline : 0;
    return `
        <line class="quote-zero" x1="${pad.left}" x2="${right}" y1="${zeroY.toFixed(1)}" y2="${zeroY.toFixed(1)}"></line>
        <circle class="quote-last-dot ${trend} ${marketTrend}" cx="${latestX.toFixed(1)}" cy="${latestY.toFixed(1)}" r="3.4"></circle>
        <line class="quote-last-guide" x1="${pad.left}" x2="${right}" y1="${latestY.toFixed(1)}" y2="${latestY.toFixed(1)}"></line>
        <text class="quote-price-label ${trend} ${marketTrend}" x="${right}" y="${Math.max(13, latestY - 5).toFixed(1)}" text-anchor="end">${formatPrice(stats.latest)}</text>
        <text class="quote-extreme-label quote-high-label" x="${right}" y="${Math.max(28, Number(highY) + 11).toFixed(1)}" text-anchor="end">高 ${formatPercentSigned(highMove, 2)}</text>
        <text class="quote-extreme-label quote-low-label" x="${right}" y="${Math.min(202, Number(lowY) - 5).toFixed(1)}" text-anchor="end">低 ${formatPercentSigned(lowMove, 2)}</text>
        <text class="quote-zero-label" x="${right}" y="${Math.max(13, zeroY - 5).toFixed(1)}" text-anchor="end">0%</text>
        <text class="quote-stats" x="${pad.left}" y="13">最新 ${formatPrice(stats.latest)}  高 ${formatPrice(stats.high)}  低 ${formatPrice(stats.low)}  ${formatPercentSigned(stats.move)}</text>
        ${rangeLabel ? `<text class="quote-range-label" x="${right}" y="13" text-anchor="end">${escapeHtml(rangeLabel)}</text>` : ""}
        <text class="quote-baseline" x="${pad.left}" y="${Math.min(212, zeroY + 13).toFixed(1)}">基准 ${formatPrice(baseline)}</text>
    `;
}

function quoteIntradayDomain(points, symbol = quoteState.symbol) {
    const timestamped = points.map((point) => Number(point?.timestamp)).filter((value) => Number.isFinite(value) && value > 0);
    if (timestamped.length >= 2) {
        const session = timestampIntradaySession(symbol, timestamped);
        if (session) return session;
        const values = timestamped.map((value) => value / 60);
        return { min: Math.min(...values), max: Math.max(...values) };
    }
    const session = minuteIntradaySession(symbol, points);
    if (session) return session;
    const timed = points.map((point) => quoteTimeLabelMinutes(point?.time)).filter(Number.isFinite);
    if (timed.length >= 2) return { min: Math.min(...timed), max: Math.max(...timed) };
    return { min: 0, max: Math.max(points.length - 1, 1), useIndex: true };
}

function quotePointTimeValue(point) {
    const timestamp = Number(point?.timestamp);
    if (Number.isFinite(timestamp) && timestamp > 0) return timestamp / 60;
    return quoteTimeLabelMinutes(point?.time);
}

function quotePointDomainValue(point, symbol, domain, index = -1) {
    if (Array.isArray(domain?.values) && index >= 0 && Number.isFinite(domain.values[index])) {
        return domain.values[index];
    }
    const value = quotePointTimeValue(point);
    if (!Number.isFinite(value)) return value;
    if (/^(if_|hf_|us_)/i.test(symbol || "") && domain?.max > 24 * 60 && value < 6 * 60) {
        return value + 24 * 60;
    }
    return value;
}

function quoteTimeLabelMinutes(label) {
    const match = String(label || "").match(/(\d{1,2}):(\d{2})(?::\d{2})?$/);
    if (!match) return NaN;
    return Number(match[1]) * 60 + Number(match[2]);
}

function minuteIntradaySession(symbol, points = []) {
    const session = intradayTradingSession(symbol, points);
    if (!session) return null;
    return decorateIntradayDomain(
        session.segments.map(([start, end]) => ({ min: start, max: end })),
        session,
    );
}

function timestampIntradaySession(symbol, timestamps) {
    const latest = Math.max(...timestamps);
    const latestDate = new Date(latest * 1000);
    const session = intradayTradingSession(symbol);
    if (session && /^kr_/i.test(symbol)) return exchangeDateSessionDomain(latest, session, 9 * 60, timestamps);
    if (session && /^hk_/i.test(symbol)) return exchangeDateSessionDomain(latest, session, 8 * 60, timestamps);
    if (session && !/^us_/i.test(symbol)) return localDateSessionDomain(latestDate, session);
    if (/^us_/i.test(symbol)) return usLocalSessionDomain(latestDate);
    return null;
}

function intradayTradingSession(symbol, points = []) {
    const value = String(symbol || "");
    if (/^hk_/i.test(value)) {
        return {
            segments: [
                [9 * 60 + 30, 12 * 60],
                [13 * 60, 16 * 60],
            ],
            labelStart: "09:30",
            labelEnd: "16:00",
        };
    }
    if (/^kr_/i.test(value)) {
        return {
            segments: [[9 * 60, 15 * 60 + 30]],
            labelStart: "09:00",
            labelEnd: "15:30",
        };
    }
    if (/^us_/i.test(value)) {
        return {
            segments: [[21 * 60 + 30, 28 * 60]],
            labelStart: "21:30",
            labelEnd: "04:00",
        };
    }
    if (/^if_/i.test(value)) {
        return futuresTradingSession(points);
    }
    if (/^hf_/i.test(value)) {
        return globalCommodityTradingSession(points);
    }
    if (/^(sh688|sz300|bj)/i.test(value) || isPostCloseFixedPriceEnabled(value)) {
        return {
            segments: [
                [9 * 60 + 30, 11 * 60 + 30],
                [13 * 60, 15 * 60],
                [15 * 60 + 5, 15 * 60 + 30],
            ],
            labelStart: "09:30",
            labelEnd: "15:30",
        };
    }
    if (/^(sh|sz|bk_|bond_)/i.test(value)) {
        return {
            segments: [
                [9 * 60 + 30, 11 * 60 + 30],
                [13 * 60, 15 * 60],
            ],
            labelStart: "09:30",
            labelEnd: "15:00",
        };
    }
    return null;
}

function isPostCloseFixedPriceEnabled(symbol) {
    if (!/^(sh|sz|bj)/i.test(symbol)) return false;
    if (/^(sh688|sz300|bj)/i.test(symbol)) return true;
    return Date.now() >= A_SHARE_AFTER_HOURS_EFFECTIVE;
}

function futuresTradingSession(points = []) {
    const minutes = quoteOrderedMinuteValues(points, "if_").filter(Number.isFinite);
    const hasNight = minutes.some((minute) => minute >= 21 * 60 || minute < 3 * 60);
    if (hasNight) {
        const dayOffset = 24 * 60;
        const nightValues = minutes.filter((minute) => minute < dayOffset + 9 * 60);
        const latestMinute = Math.max(...minutes);
        const segments = [];
        if (nightValues.length >= 2) {
            segments.push([Math.min(...nightValues), Math.max(...nightValues)]);
        }
        [[9 * 60, 10 * 60 + 15], [10 * 60 + 30, 11 * 60 + 30], [13 * 60 + 30, 15 * 60]].forEach(([start, end]) => {
            const shiftedStart = dayOffset + start;
            if (latestMinute < shiftedStart) return;
            const shiftedEnd = Math.min(dayOffset + end, latestMinute);
            if (shiftedEnd > shiftedStart) segments.push([shiftedStart, shiftedEnd]);
        });
        return {
            segments,
            labelStart: "21:00",
            labelEnd: minutesToClockOfDay(latestMinute),
            values: minutes,
        };
    }
    return {
        segments: [
            [9 * 60, 10 * 60 + 15],
            [10 * 60 + 30, 11 * 60 + 30],
            [13 * 60 + 30, 15 * 60],
        ],
        labelStart: "09:00",
        labelEnd: "15:00",
        values: minutes,
    };
}

function globalCommodityTradingSession(points = []) {
    const values = quoteOrderedMinuteValues(points, "hf_").filter(Number.isFinite);
    if (values.length >= 2) {
        const start = Math.min(...values);
        const end = Math.max(...values);
        return {
            segments: [[start, end]],
            labelStart: minutesToClockOfDay(start),
            labelEnd: minutesToClockOfDay(end),
            values,
        };
    }
    return null;
}

function quoteOrderedMinuteValues(points, symbol = "") {
    const raw = points.map((point) => quoteTimeLabelMinutes(point?.time));
    let offset = 0;
    let previous = null;
    return raw.map((minute) => {
        if (!Number.isFinite(minute)) return NaN;
        let value = minute + offset;
        if (/^(if_|hf_)/i.test(symbol) && previous != null && value < previous - 60) {
            offset += 24 * 60;
            value = minute + offset;
        }
        previous = value;
        return value;
    });
}

function minutesToClockOfDay(value) {
    const minute = ((Math.round(value) % (24 * 60)) + 24 * 60) % (24 * 60);
    return `${String(Math.floor(minute / 60)).padStart(2, "0")}:${String(minute % 60).padStart(2, "0")}`;
}

function localDateSessionDomain(date, session) {
    return decorateIntradayDomain(
        session.segments.map(([start, end]) => ({
            min: localEpochMinute(date, start),
            max: localEpochMinute(date, end),
        })),
        session,
    );
}

function exchangeDateSessionDomain(timestampSeconds, session, exchangeUtcOffsetMinutes, timestamps = []) {
    const exchangeDate = exchangeDateParts(timestampSeconds, exchangeUtcOffsetMinutes);
    const domain = decorateIntradayDomain(
        session.segments.map(([start, end]) => ({
            min: exchangeEpochMinute(exchangeDate, start, exchangeUtcOffsetMinutes),
            max: exchangeEpochMinute(exchangeDate, end, exchangeUtcOffsetMinutes),
        })),
        session,
    );
    return trimClosedTimestampDomain(domain, timestamps);
}

function trimClosedTimestampDomain(domain, timestamps) {
    if (!domain || !Array.isArray(timestamps) || !timestamps.length) return domain;
    const latestMinute = Math.max(...timestamps) / 60;
    const lastSegment = domain.segments[domain.segments.length - 1];
    const gapToClose = lastSegment.max - latestMinute;
    if (gapToClose <= 0 || gapToClose > 45 || Date.now() / 60000 < lastSegment.max) return domain;
    const segments = domain.segments.map((segment, index) => (
        index === domain.segments.length - 1 ? { ...segment, max: latestMinute } : segment
    ));
    return decorateIntradayDomain(segments, {
        labelStart: domain.labelStart,
        labelEnd: minutesToClockLabel(latestMinute),
    });
}

function minutesToClockLabel(value) {
    const date = new Date(value * 60000);
    return `${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}

function exchangeDateParts(timestampSeconds, exchangeUtcOffsetMinutes) {
    const shifted = new Date((timestampSeconds + exchangeUtcOffsetMinutes * 60) * 1000);
    return {
        year: shifted.getUTCFullYear(),
        month: shifted.getUTCMonth(),
        day: shifted.getUTCDate(),
    };
}

function exchangeEpochMinute(dateParts, minuteOfDay, exchangeUtcOffsetMinutes) {
    const dayOffset = Math.floor(minuteOfDay / (24 * 60));
    const minuteInDay = minuteOfDay - dayOffset * 24 * 60;
    const utcMilliseconds = Date.UTC(
        dateParts.year,
        dateParts.month,
        dateParts.day + dayOffset,
        Math.floor(minuteInDay / 60),
        minuteInDay % 60,
        0,
        0,
    ) - exchangeUtcOffsetMinutes * 60000;
    return utcMilliseconds / 60000;
}

function usLocalSessionDomain(date) {
    const minute = date.getHours() * 60 + date.getMinutes();
    const sessionDate = new Date(date);
    if (minute < 12 * 60) {
        sessionDate.setDate(sessionDate.getDate() - 1);
    }
    return localDateSessionDomain(sessionDate, intradayTradingSession("us_"));
}

function decorateIntradayDomain(segments, session) {
    const validSegments = segments.filter((segment) => Number.isFinite(segment.min) && Number.isFinite(segment.max) && segment.max > segment.min);
    if (!validSegments.length) return null;
    const total = validSegments.reduce((sum, segment) => sum + (segment.max - segment.min), 0);
    return {
        min: validSegments[0].min,
        max: validSegments[validSegments.length - 1].max,
        segments: validSegments,
        total: Math.max(total, 1),
        labelStart: session?.labelStart,
        labelEnd: session?.labelEnd,
        values: session?.values,
    };
}

function localEpochMinute(date, minuteOfDay) {
    const local = new Date(date);
    local.setHours(Math.floor(minuteOfDay / 60), minuteOfDay % 60, 0, 0);
    return local.getTime() / 60000;
}

function quoteIntradayXFor(points, width, pad, symbol = quoteState.symbol) {
    const domain = quoteIntradayDomain(points, symbol);
    const span = Math.max(domain.max - domain.min, 1);
    return (point, index) => {
        if (domain.useIndex) {
            return pad.left + (index / Math.max(points.length - 1, 1)) * (width - pad.left - pad.right);
        }
        const value = quotePointDomainValue(point, symbol, domain, index);
        const normalized = Number.isFinite(value)
            ? quoteIntradayNormalizedPosition(domain, value, span)
            : index / Math.max(points.length - 1, 1);
        return pad.left + clamp(normalized, 0, 1) * (width - pad.left - pad.right);
    };
}

function quoteIntradayNormalizedPosition(domain, value, span) {
    if (!Array.isArray(domain.segments) || !domain.segments.length) {
        return (value - domain.min) / span;
    }
    let offset = 0;
    for (const segment of domain.segments) {
        const segmentSpan = segment.max - segment.min;
        if (value <= segment.min) return offset / domain.total;
        if (value <= segment.max) return (offset + value - segment.min) / domain.total;
        offset += segmentSpan;
    }
    return 1;
}

function quoteIntradayAxisLabels(points, symbol = quoteState.symbol) {
    const domain = quoteIntradayDomain(points, symbol);
    return {
        start: domain.labelStart || points[0]?.time || "",
        end: domain.labelEnd || points[points.length - 1]?.time || "",
    };
}

function renderEmptyQuoteChart(label) {
    const svg = document.querySelector("#quote-chart svg");
    if (!svg) return;
    svg.innerHTML = `
        <text class="quote-empty" x="380" y="112" text-anchor="middle">${escapeHtml(label)}</text>
    `;
}

function renderIntradayQuoteChart(points, trend, symbol = quoteState.symbol) {
    const svg = document.querySelector("#quote-chart svg");
    if (!svg) return;
    const width = 760;
    const height = 220;
    const pad = { left: 36, right: 18, top: 18, bottom: 28 };
    const baseline = quoteZeroBaseline(points);
    const stats = quoteStats(points, baseline);
    const closes = points.map((point) => Number(point.close));
    const { min, max, range } = quoteValueRange([...closes, baseline], 0.08);
    const xForPoint = quoteIntradayXFor(points, width, pad, symbol);
    const yFor = (value) => pad.top + ((max - value) / range) * (height - pad.top - pad.bottom);
    const line = points.map((point, index) => `${index === 0 || quoteSessionBreak(points, index, symbol) ? "M" : "L"}${xForPoint(point, index).toFixed(1)} ${yFor(Number(point.close)).toFixed(1)}`).join(" ");
    const firstX = xForPoint(points[0], 0).toFixed(1);
    const lastX = xForPoint(points[points.length - 1], points.length - 1).toFixed(1);
    const baseY = (height - pad.bottom).toFixed(1);
    const area = /^if_/i.test(symbol || "") ? "" : `${line} L${lastX} ${baseY} L${firstX} ${baseY} Z`;
    const latestX = xForPoint(points[points.length - 1], points.length - 1);
    const latestY = yFor(Number(points[points.length - 1].close));
    const zeroY = yFor(baseline);
    const axisLabels = quoteIntradayAxisLabels(points, symbol);
    svg.innerHTML = `
        <path class="quote-grid" d="M${pad.left} ${pad.top}H${width - pad.right}M${pad.left} ${height / 2}H${width - pad.right}M${pad.left} ${height - pad.bottom}H${width - pad.right}"></path>
        ${area ? `<path class="quote-area ${trend} ${marketTrendClassForValue(stats.move)}" d="${area}"></path>` : ""}
        <path class="quote-line ${trend} ${marketTrendClassForValue(stats.move)}" d="${line}"></path>
        ${quotePointOverlay({ width, pad, baseline, stats, latestX, latestY, highY: yFor(stats.high), lowY: yFor(stats.low), zeroY, trend })}
        <text class="quote-axis" x="${pad.left}" y="${height - 8}">${escapeHtml(axisLabels.start)}</text>
        <text class="quote-axis" x="${width - pad.right}" y="${height - 8}" text-anchor="end">${escapeHtml(axisLabels.end)}</text>
    `;
}

function quoteSessionBreak(points, index, symbol = quoteState.symbol) {
    if (index <= 0 || !/^if_/i.test(symbol || "")) return false;
    const previous = quoteTimeLabelMinutes(points[index - 1]?.time);
    const current = quoteTimeLabelMinutes(points[index]?.time);
    return Number.isFinite(previous) && Number.isFinite(current) && current < previous - 60 && current >= 8 * 60;
}

function renderKlineQuoteChart(points) {
    const svg = document.querySelector("#quote-chart svg");
    if (!svg) return;
    const width = 760;
    const height = 220;
    const pad = { left: 36, right: 18, top: 18, bottom: 28 };
    const end = getQuoteWindowEnd();
    const start = Math.max(0, end - quoteState.windowSize);
    const visible = quoteVisiblePoints(points);
    const baseline = quoteZeroBaseline(visible);
    const stats = quoteStats(visible, baseline);
    const values = visible.flatMap((point) => [
        Number(point.high ?? point.close),
        Number(point.low ?? point.close),
        Number(point.open ?? point.close),
        Number(point.close),
    ]).filter(Number.isFinite);
    const { min, max, range } = quoteValueRange(values, 0.1);
    const slot = (width - pad.left - pad.right) / Math.max(visible.length, 1);
    const candleWidth = Math.max(3, Math.min(10, slot * 0.58));
    const yFor = (value) => pad.top + ((max - value) / range) * (height - pad.top - pad.bottom);
    const boundedYFor = (value) => clamp(yFor(value), pad.top, height - pad.bottom);
    const candles = visible.map((point, index) => {
        const open = Number(point.open ?? point.close);
        const close = Number(point.close);
        const high = Number(point.high ?? Math.max(open, close));
        const low = Number(point.low ?? Math.min(open, close));
        const x = pad.left + slot * index + slot / 2;
        const yOpen = yFor(open);
        const yClose = yFor(close);
        const bodyY = Math.min(yOpen, yClose);
        const bodyHeight = Math.max(Math.abs(yClose - yOpen), 2);
        const trend = close >= open ? "up" : "down";
        const marketTrend = close >= open ? "market-up" : "market-down";
        return `
            <line class="quote-wick ${trend} ${marketTrend}" x1="${x.toFixed(1)}" x2="${x.toFixed(1)}" y1="${yFor(high).toFixed(1)}" y2="${yFor(low).toFixed(1)}"></line>
            <rect class="quote-candle ${trend} ${marketTrend}" x="${(x - candleWidth / 2).toFixed(1)}" y="${bodyY.toFixed(1)}" width="${candleWidth.toFixed(1)}" height="${bodyHeight.toFixed(1)}"></rect>
        `;
    }).join("");
    const lastIndex = Math.max(visible.length - 1, 0);
    const latestX = pad.left + slot * lastIndex + slot / 2;
    const latestY = yFor(Number(visible[lastIndex]?.close ?? stats.latest));
    const zeroY = boundedYFor(baseline);
    const trend = trendClassForValue(stats.move);
    const rangeLabel = `${start + 1}-${end} / ${points.length}`;
    svg.innerHTML = `
        <path class="quote-grid" d="M${pad.left} ${pad.top}H${width - pad.right}M${pad.left} ${height / 2}H${width - pad.right}M${pad.left} ${height - pad.bottom}H${width - pad.right}"></path>
        ${candles}
        ${quotePointOverlay({ width, pad, baseline, stats, latestX, latestY, highY: yFor(stats.high), lowY: yFor(stats.low), zeroY, trend, rangeLabel })}
        <text class="quote-axis" x="${pad.left}" y="${height - 8}">${escapeHtml(visible[0]?.time || "")}</text>
        <text class="quote-axis" x="${width - pad.right}" y="${height - 8}" text-anchor="end">${escapeHtml(visible[visible.length - 1]?.time || "")}</text>
    `;
}

function getQuoteWindowEnd() {
    const maxEnd = quoteState.points.length;
    const minEnd = Math.min(quoteState.windowSize, maxEnd);
    return clamp(quoteState.windowEnd ?? maxEnd, minEnd, maxEnd);
}

function quoteVisiblePoints(points) {
    const end = getQuoteWindowEnd();
    const start = Math.max(0, end - quoteState.windowSize);
    return points.slice(start, end);
}

function workflowLibraryBySymbol(symbol) {
    const known = WORKFLOW_NODE_LIBRARY.find((item) => item.symbol === symbol);
    if (known) return known;
    if (/^(sh|sz|bj)\d{6}$/i.test(symbol)) {
        return { symbol, name: `A股 ${symbol.toUpperCase()}`, category: "terminal", note: "通过输入代码导入的 A 股行情卡片" };
    }
    if (/^hk_\d{1,5}$/i.test(symbol)) {
        return { symbol, name: `港股 ${symbol.replace(/^hk_/i, "").padStart(4, "0")}`, category: "macro", note: "通过输入代码导入的港股行情卡片" };
    }
    if (/^us_/i.test(symbol)) {
        return { symbol, name: `美股 ${symbol.replace(/^us_/i, "").toUpperCase()}`, category: "macro", note: "通过输入代码导入的美股行情卡片" };
    }
    return { symbol, name: symbol, category: "macro", note: "自定义行情节点" };
}

function workflowNodeMeta(node) {
    const fallback = workflowLibraryBySymbol(node?.symbol || "");
    return {
        ...fallback,
        name: workflowFuturesDisplayName(node?.symbol, node?.name || fallback.name),
        lane: node?.lane || fallback.lane,
        group: node?.group || fallback.group,
        recommendations: node?.recommendations || fallback.recommendations || [],
    };
}

function setupWorkflowControls() {
    resetWorkflowGraph();
    workflowState.selectedNodeId = workflowState.nodes[0]?.id || null;

    const categorySelect = document.getElementById("workflow-category-select");
    const nodeSelect = document.getElementById("workflow-node-select");
    const addButton = document.getElementById("workflow-add-node");
    const importInput = document.getElementById("workflow-symbol-input");
    const importButton = document.getElementById("workflow-import-symbol");
    const connectButton = document.getElementById("workflow-connect-mode");
    const saveButton = document.getElementById("workflow-save");
    const resetButton = document.getElementById("workflow-reset");
    const canvas = document.getElementById("workflow-canvas");
    const fitViewButton = document.getElementById("workflow-fit-view");
    const resetViewButton = document.getElementById("workflow-reset-view");

    if (!categorySelect || !nodeSelect || !canvas) return;

    categorySelect.innerHTML = Object.entries(WORKFLOW_CATEGORIES)
        .map(([key, label]) => `<option value="${escapeHtml(key)}">${escapeHtml(label)}</option>`)
        .join("");
    categorySelect.addEventListener("change", () => populateWorkflowNodeSelect());
    populateWorkflowNodeSelect();

    addButton?.addEventListener("click", () => addWorkflowNode(nodeSelect.value));
    importButton?.addEventListener("click", () => importWorkflowSymbol(importInput?.value));
    importInput?.addEventListener("keydown", (event) => {
        if (event.key !== "Enter") return;
        event.preventDefault();
        importWorkflowSymbol(importInput.value);
    });
    connectButton?.addEventListener("click", () => {
        workflowState.connectMode = !workflowState.connectMode;
        workflowState.connectSourceId = null;
        workflowState.connectSourcePort = "right";
        connectButton.classList.toggle("active", workflowState.connectMode);
        connectButton.textContent = workflowState.connectMode ? "退出连线" : "连线";
        renderWorkflowCanvas();
    });
    saveButton?.addEventListener("click", () => saveWorkflowGraph({ immediate: true }));
    document.getElementById("workflow-open-supply-map")?.addEventListener("click", () => {
        document.querySelector('.nav-item[data-tab="supply"]')?.click();
        renderSupplyWorkspace();
    });
    document.getElementById("workflow-reload-current")?.addEventListener("click", () => reloadWorkflowAfterConflict());
    document.getElementById("workflow-merge-draft")?.addEventListener("click", () => mergeWorkflowDraftAfterConflict());
    resetButton?.addEventListener("click", () => {
        resetWorkflowGraph();
        workflowState.selectedNodeId = workflowState.nodes[0]?.id || null;
        workflowState.selectedLinkId = null;
        workflowState.connectSourceId = null;
        workflowState.connectSourcePort = "right";
        renderWorkflowPalette();
        renderWorkflowCanvas({ fit: true });
        refreshWorkflowQuotes();
        scheduleWorkflowSave();
    });

    canvas.addEventListener("click", (event) => {
        if (event.target !== canvas && event.target.id !== "workflow-stage" && event.target.id !== "workflow-nodes" && event.target.id !== "workflow-links") return;
        if (workflowState.panSuppressClick) {
            workflowState.panSuppressClick = false;
            return;
        }
        workflowState.selectedNodeId = null;
        workflowState.selectedLinkId = null;
        workflowState.connectSourceId = null;
        workflowState.connectSourcePort = "right";
        renderWorkflowCanvas();
    });
    canvas.addEventListener("pointerdown", startWorkflowPan);
    canvas.addEventListener("pointermove", handleWorkflowPointerMove);
    canvas.addEventListener("pointermove", handleWorkflowPanMove);
    canvas.addEventListener("pointerup", stopWorkflowDrag);
    canvas.addEventListener("pointerup", stopWorkflowPan);
    canvas.addEventListener("pointercancel", stopWorkflowDrag);
    canvas.addEventListener("pointercancel", stopWorkflowPan);
    canvas.addEventListener("wheel", handleWorkflowWheel, { passive: false });
    fitViewButton?.addEventListener("click", () => fitWorkflowView({ userAdjusted: true }));
    resetViewButton?.addEventListener("click", resetWorkflowView);
    setupWorkflowCanvasResizeObserver(canvas);

    renderWorkflowPalette();
    renderWorkflowCanvas({ fit: true });
    loadWorkflowGraph();
    startWorkflowAutoRefresh();
}

function resetWorkflowGraph() {
    workflowState.nodes = layoutWorkflowNodes(DEFAULT_WORKFLOW_NODES, DEFAULT_WORKFLOW_LINKS);
    workflowState.links = normalizeWorkflowLinks(DEFAULT_WORKFLOW_LINKS, workflowState.nodes);
}

async function loadWorkflowGraph() {
    setWorkflowSaveStatus("loading", "读取项目文件");
    try {
        const payload = await fetchBackendJson("/external-risk/workflow");
        if (workflowState.readOnly) return;
        const graph = payload.data || {};
        workflowState.storagePath = graph.storage_path || "";
        workflowState.revision = Number.isInteger(graph.revision) ? graph.revision : 0;
        workflowState.conflict = null;
        setWorkflowConflictActions(false);
        const hasPersistedNodes = Array.isArray(graph.nodes) && graph.nodes.length;
        if (hasPersistedNodes) {
            applyWorkflowGraph(graph);
            workflowState.selectedNodeId = workflowState.nodes[0]?.id || null;
            workflowState.selectedLinkId = null;
            renderWorkflowPalette();
            renderWorkflowCanvas({ fit: true });
            window.setTimeout(() => refreshWorkflowQuotes(), 1000);
        } else {
            // An empty response must never cause the local default canvas to
            // overwrite a map saved by another browser while this page loads.
            setWorkflowSaveStatus("idle", "未保存关系图；请确认后手动保存");
        }
        workflowState.loaded = true;
        syncSupplierWorkflowNodes();
        const suffix = workflowState.storagePath ? ` · ${workflowState.storagePath}` : "";
        if (workflowState.supplierBindingsPending) {
            setWorkflowSaveStatus("dirty", "供应商卡片待确认；保存后才写入关系图");
        } else if (hasPersistedNodes) {
            const sync = workflowState.supplyChainSync;
            setWorkflowSaveStatus(
                sync?.status === "action_required" ? "dirty" : "saved",
                sync?.message || `已连接项目文件${suffix}`,
            );
        }
    } catch (error) {
        if (workflowState.readOnly) return;
        console.info(error);
        setWorkflowSaveStatus("error", "未连接保存接口");
    }
}

function applyWorkflowGraph(graph) {
    const nodes = Array.isArray(graph.nodes) ? graph.nodes : [];
    const links = Array.isArray(graph.links) ? graph.links : [];
    workflowState.nodes = nodes
        .filter((node) => node?.id && node?.symbol)
        .map((node) => ({
            id: String(node.id),
            symbol: String(node.symbol),
            name: node.name || null,
            nodeKind: node.node_kind || "market",
            supplierId: node.supplier_id || null,
            x: Number.isFinite(Number(node.x)) ? Number(node.x) : 0,
            y: Number.isFinite(Number(node.y)) ? Number(node.y) : 0,
            lane: node.lane || workflowLibraryBySymbol(String(node.symbol)).lane || null,
            group: node.group || workflowLibraryBySymbol(String(node.symbol)).group || null,
            recommendations: Array.isArray(node.recommendations) ? node.recommendations : workflowLibraryBySymbol(String(node.symbol)).recommendations || [],
        }));
    workflowState.links = normalizeWorkflowLinks(links, workflowState.nodes);
    setWorkflowSupplyChainSync(graph.supply_chain_sync || null);
}

function setWorkflowSupplyChainSync(sync) {
    workflowState.supplyChainSync = sync && typeof sync === "object" ? sync : null;
    const actionButton = document.getElementById("workflow-open-supply-map");
    if (!actionButton) return;
    const unbound = Array.isArray(sync?.unbound_supplier_nodes) ? sync.unbound_supplier_nodes.length : 0;
    const missing = Array.isArray(sync?.missing_supplier_ids) ? sync.missing_supplier_ids.length : 0;
    const actionRequired = sync?.status === "action_required" && (unbound || missing);
    actionButton.hidden = !actionRequired;
    if (!actionRequired) return;
    actionButton.textContent = `维护供应链节点${unbound + missing ? `（${unbound + missing}）` : ""}`;
    actionButton.title = sync?.message || "画布中存在未绑定的供应商节点，请在供应链地图维护后重新保存。";
}

function setWorkflowDebugReadOnly(enabled) {
    workflowState.readOnly = Boolean(enabled);
    if (workflowState.readOnly && workflowState.saveTimer) {
        window.clearTimeout(workflowState.saveTimer);
        workflowState.saveTimer = null;
    }
    const controlIds = [
        "workflow-category-select", "workflow-node-select", "workflow-add-node",
        "workflow-symbol-input", "workflow-import-symbol", "workflow-connect-mode",
        "workflow-save", "workflow-reset",
    ];
    controlIds.forEach((id) => {
        const control = document.getElementById(id);
        if (control) control.disabled = workflowState.readOnly;
    });
}

function applyDebugWorkflowGraph(snapshot) {
    const graph = snapshot?.market_canvas || {};
    applyWorkflowGraph(graph);
    workflowState.nodes = layoutWorkflowNodes(workflowState.nodes, workflowState.links);
    workflowState.selectedNodeId = snapshot?.selection?.node_id || workflowState.nodes[0]?.id || null;
    workflowState.selectedLinkId = null;
    workflowState.connectMode = false;
    workflowState.connectSourceId = null;
    workflowState.debugRunId = snapshot?.run_id || null;
    setWorkflowDebugReadOnly(true);
    renderWorkflowPalette();
    renderWorkflowCanvas({ fit: true });
    setWorkflowSaveStatus("saved", "调试场景关系只读");
}

function workflowGraphSnapshot() {
    return {
        version: "0.1.0",
        revision: workflowState.revision,
        nodes: workflowState.nodes.map((node) => ({
            id: node.id,
            symbol: node.symbol,
            name: node.name || null,
            node_kind: node.nodeKind || "market",
            supplier_id: node.supplierId || null,
            x: Math.round(Number(node.x) || 0),
            y: Math.round(Number(node.y) || 0),
            lane: node.lane || workflowLibraryBySymbol(node.symbol).lane || null,
            group: node.group || workflowLibraryBySymbol(node.symbol).group || null,
            recommendations: workflowLibraryBySymbol(node.symbol).recommendations || [],
        })),
        links: workflowState.links.map((link) => ({
            source: link.source,
            target: link.target,
            sourcePort: link.sourcePort || "right",
            targetPort: link.targetPort || "left",
            relation: link.relation || null,
            relation_id: link.relationId || null,
            source_kind: link.sourceKind || "manual_canvas",
            correlation_layers: Array.isArray(link.correlationLayers) ? link.correlationLayers : [],
            evidence_grade: link.evidenceGrade || "unverified",
            relationship_scope: link.relationshipScope || "industry_proxy",
            evidence_refs: Array.isArray(link.evidenceRefs) ? link.evidenceRefs : [],
            boundary_note: link.boundaryNote || "",
            confirmed_by: link.confirmedBy || null,
            confirmed_at: link.confirmedAt || null,
            updated_at: link.updatedAt || null,
        })),
        bound_supplier_ids: workflowState.nodes
            .filter((node) => node.nodeKind === "supplier" && node.supplierId)
            .map((node) => node.supplierId),
    };
}

function workflowLinkParts(link) {
    if (Array.isArray(link)) {
        return { source: link[0], target: link[1], relation: null, sourcePort: null, targetPort: null, relationId: null, sourceKind: "legacy", correlationLayers: [], evidenceGrade: "unverified", relationshipScope: "industry_proxy", evidenceRefs: [], boundaryNote: "", confirmedBy: null, confirmedAt: null, updatedAt: null };
    }
    return {
        source: link?.source,
        target: link?.target,
        relation: link?.relation || null,
        sourcePort: link?.sourcePort || null,
        targetPort: link?.targetPort || null,
        relationId: link?.relationId || link?.relation_id || null,
        sourceKind: link?.sourceKind || link?.source_kind || "legacy",
        correlationLayers: link?.correlationLayers || link?.correlation_layers || [],
        evidenceGrade: link?.evidenceGrade || link?.evidence_grade || "unverified",
        relationshipScope: link?.relationshipScope || link?.relationship_scope || "industry_proxy",
        evidenceRefs: link?.evidenceRefs || link?.evidence_refs || [],
        boundaryNote: link?.boundaryNote || link?.boundary_note || "",
        confirmedBy: link?.confirmedBy || link?.confirmed_by || null,
        confirmedAt: link?.confirmedAt || link?.confirmed_at || null,
        updatedAt: link?.updatedAt || link?.updated_at || null,
    };
}

function normalizeWorkflowLinks(links, nodes) {
    const byId = new Map(nodes.map((node) => [node.id, node]));
    return (links || []).map(workflowLinkParts)
        .filter((link) => byId.has(link.source) && byId.has(link.target))
        .map((link) => {
            const ports = workflowAutoPorts(byId.get(link.source), byId.get(link.target));
            return {
                source: String(link.source),
                target: String(link.target),
                sourcePort: link.sourcePort || ports.sourcePort,
                targetPort: link.targetPort || ports.targetPort,
                relation: link.relation || null,
                relationId: link.relationId || null,
                sourceKind: link.sourceKind || "legacy",
                correlationLayers: Array.isArray(link.correlationLayers) ? link.correlationLayers : [],
                evidenceGrade: link.evidenceGrade || "unverified",
                relationshipScope: link.relationshipScope || "industry_proxy",
                evidenceRefs: Array.isArray(link.evidenceRefs) ? link.evidenceRefs : [],
                boundaryNote: link.boundaryNote || "",
                confirmedBy: link.confirmedBy || null,
                confirmedAt: link.confirmedAt || null,
                updatedAt: link.updatedAt || null,
            };
        });
}

function workflowAutoPorts(sourceNode, targetNode) {
    if (!sourceNode || !targetNode) return { sourcePort: "right", targetPort: "left" };
    if (Number(sourceNode.x) <= Number(targetNode.x)) {
        return { sourcePort: "right", targetPort: "left" };
    }
    return { sourcePort: "left", targetPort: "right" };
}

function workflowDirectionalLink(sourceId, targetId, relation = null) {
    const sourceNode = workflowState.nodes.find((node) => node.id === sourceId);
    const targetNode = workflowState.nodes.find((node) => node.id === targetId);
    const ports = workflowAutoPorts(sourceNode, targetNode);
    return {
        source: sourceId, target: targetId, ...ports, relation,
        relationId: newWorkflowRelationId(sourceId, targetId), sourceKind: "manual_canvas",
        correlationLayers: defaultWorkflowCorrelationLayers(sourceNode, targetNode),
        evidenceGrade: "unverified", relationshipScope: "industry_proxy", evidenceRefs: [], boundaryNote: "",
        confirmedBy: null, confirmedAt: null, updatedAt: null,
    };
}

function newWorkflowRelationId(source, target) {
    return `rel-local-${String(source).replace(/[^a-zA-Z0-9_-]/g, "_")}-${String(target).replace(/[^a-zA-Z0-9_-]/g, "_")}-${Date.now().toString(36)}`;
}

function defaultWorkflowCorrelationLayers(sourceNode, targetNode) {
    const layers = ["path"];
    if (sourceNode?.nodeKind === "market" || targetNode?.nodeKind === "market") layers.unshift("material");
    if (sourceNode?.nodeKind === "supplier" && targetNode?.nodeKind === "supplier") layers.unshift("counterparty");
    return layers;
}

function scheduleWorkflowSave(delay = 700) {
    if (workflowState.readOnly) return;
    if (workflowState.saveTimer) window.clearTimeout(workflowState.saveTimer);
    setWorkflowSaveStatus("dirty", "待保存");
    workflowState.saveTimer = window.setTimeout(() => saveWorkflowGraph(), delay);
}

async function saveWorkflowGraph({ immediate = false } = {}) {
    if (workflowState.readOnly) return;
    if (workflowState.saveTimer) {
        window.clearTimeout(workflowState.saveTimer);
        workflowState.saveTimer = null;
    }
    setWorkflowSaveStatus("saving", immediate ? "正在保存" : "自动保存中");
    const draft = workflowGraphSnapshot();
    try {
        const payload = await fetchBackendJson("/external-risk/workflow", {
            method: "PUT",
            body: JSON.stringify(draft),
        });
        if (workflowState.readOnly) return;
        workflowState.storagePath = payload.data?.storage_path || workflowState.storagePath;
        workflowState.revision = Number.isInteger(payload.data?.revision) ? payload.data.revision : workflowState.revision;
        setWorkflowSupplyChainSync(payload.data?.supply_chain_sync || null);
        workflowState.conflict = null;
        clearRetainedWorkflowDraft();
        setWorkflowConflictActions(false);
        workflowState.supplierBindingsPending = false;
        renderSupplyWorkspace();
        const sync = workflowState.supplyChainSync;
        const suffix = workflowState.storagePath ? ` · ${workflowState.storagePath}` : "";
        setWorkflowSaveStatus(
            sync?.status === "action_required" ? "dirty" : "saved",
            sync?.message || `已保存到项目文件${suffix}`,
        );
    } catch (error) {
        if (workflowState.readOnly) return;
        console.info(error);
        if (error?.status === 409 || error?.code === "EXTERNAL_RISK_WORKFLOW_CONFLICT") {
            workflowState.conflict = {
                draft,
                currentGraph: error?.payload?.current_graph || null,
                diff: error?.payload?.diff || null,
            };
            retainWorkflowDraft(draft);
            setWorkflowConflictActions(true);
            const changed = Number(workflowState.conflict.diff?.relations?.changed?.length || 0)
                + Number(workflowState.conflict.diff?.nodes?.changed?.length || 0);
            setWorkflowSaveStatus("conflict", `发现新版本；已保留本地草稿${changed ? `（${changed} 项差异）` : ""}`);
            return;
        }
        setWorkflowSaveStatus("error", "保存失败，检查后端");
    }
}

function retainWorkflowDraft(draft) {
    try { window.sessionStorage.setItem("external-risk-workflow-draft", JSON.stringify(draft)); } catch (_error) { /* optional browser recovery */ }
}

function clearRetainedWorkflowDraft() {
    try { window.sessionStorage.removeItem("external-risk-workflow-draft"); } catch (_error) { /* optional browser recovery */ }
}

function setWorkflowConflictActions(visible) {
    ["workflow-reload-current", "workflow-merge-draft"].forEach((id) => {
        const button = document.getElementById(id);
        if (button) button.hidden = !visible;
    });
}

function reloadWorkflowAfterConflict() {
    const current = workflowState.conflict?.currentGraph;
    if (!current) return loadWorkflowGraph();
    applyWorkflowGraph(current);
    workflowState.revision = Number.isInteger(current.revision) ? current.revision : workflowState.revision;
    workflowState.storagePath = current.storage_path || workflowState.storagePath;
    workflowState.conflict = null;
    clearRetainedWorkflowDraft();
    setWorkflowConflictActions(false);
    renderWorkflowPalette();
    renderWorkflowCanvas();
    renderSupplyWorkspace();
    setWorkflowSaveStatus("saved", "已载入最新版本；本地草稿未合并");
}

async function mergeWorkflowDraftAfterConflict() {
    const conflict = workflowState.conflict;
    if (!conflict?.draft) return;
    const confirmedBy = window.prompt("受控合并：请输入确认人姓名或工号");
    if (!confirmedBy?.trim()) return;
    const confirmationNote = window.prompt("请说明合并理由（将写入审计记录）");
    if (!confirmationNote?.trim()) return;
    setWorkflowSaveStatus("saving", "正在执行受控合并");
    try {
        const payload = await fetchBackendJson("/external-risk/workflow/merge", {
            method: "POST",
            body: JSON.stringify({
                base_revision: Number(conflict.draft.revision || 0),
                draft: conflict.draft,
                confirmed_by: confirmedBy.trim(),
                confirmation_note: confirmationNote.trim(),
            }),
        });
        applyWorkflowGraph(payload.data || {});
        workflowState.revision = Number.isInteger(payload.data?.revision) ? payload.data.revision : workflowState.revision;
        workflowState.storagePath = payload.data?.storage_path || workflowState.storagePath;
        workflowState.conflict = null;
        clearRetainedWorkflowDraft();
        setWorkflowConflictActions(false);
        renderWorkflowPalette();
        renderWorkflowCanvas();
        renderSupplyWorkspace();
        setWorkflowSaveStatus("saved", "已受控合并并保留服务端新增关系");
    } catch (error) {
        console.info(error);
        setWorkflowSaveStatus("error", "受控合并失败；请重新读取最新版本");
    }
}

function setWorkflowSaveStatus(status, label) {
    workflowState.saveStatus = status;
    const element = document.getElementById("workflow-save-status");
    if (!element) return;
    element.textContent = label;
    element.dataset.status = status;
    element.title = workflowState.storagePath || label;
}

function layoutWorkflowNodes(nodes, links) {
    const byId = new Map(nodes.map((node) => [node.id, { ...node }]));
    const incoming = new Map(nodes.map((node) => [node.id, 0]));
    const outgoing = new Map(nodes.map((node) => [node.id, []]));
    links.forEach((link) => {
        const { source, target } = workflowLinkParts(link);
        if (!byId.has(source) || !byId.has(target)) return;
        incoming.set(target, (incoming.get(target) || 0) + 1);
        outgoing.get(source)?.push(target);
    });
    const queue = nodes.filter((node) => !incoming.get(node.id)).map((node) => node.id);
    const depth = new Map(queue.map((id) => [id, 0]));
    while (queue.length) {
        const id = queue.shift();
        const nextDepth = (depth.get(id) || 0) + 1;
        (outgoing.get(id) || []).forEach((target) => {
            if ((depth.get(target) ?? -1) < nextDepth) depth.set(target, nextDepth);
            incoming.set(target, Math.max(0, (incoming.get(target) || 0) - 1));
            if (incoming.get(target) === 0) queue.push(target);
        });
    }
    nodes.forEach((node) => {
        if (!depth.has(node.id)) depth.set(node.id, 0);
    });
    const columns = new Map();
    nodes.forEach((node) => {
        const column = depth.get(node.id) || 0;
        if (!columns.has(column)) columns.set(column, []);
        columns.get(column).push(node.id);
    });
    const xStep = 320;
    const yStep = 158;
    const startX = 36;
    const startY = 34;
    [...columns.entries()].forEach(([column, ids]) => {
        ids.forEach((id, index) => {
            const node = byId.get(id);
            node.x = startX + column * xStep;
            node.y = startY + index * yStep;
        });
    });
    return nodes.map((node) => byId.get(node.id));
}

function populateWorkflowNodeSelect() {
    const categorySelect = document.getElementById("workflow-category-select");
    const nodeSelect = document.getElementById("workflow-node-select");
    if (!categorySelect || !nodeSelect) return;
    const category = categorySelect.value || Object.keys(WORKFLOW_CATEGORIES)[0];
    const nodes = WORKFLOW_NODE_LIBRARY.filter((node) => node.category === category);
    nodeSelect.innerHTML = nodes.map((node) => {
        const name = workflowFuturesDisplayName(node.symbol, node.name);
        const code = standardInstrumentCode(node.symbol);
        return `<option value="${escapeHtml(node.symbol)}">${escapeHtml(code ? `${name}（${code}）` : name)}</option>`;
    }).join("");
}

function renderWorkflowPalette() {
    const palette = document.getElementById("workflow-palette");
    if (!palette) return;
    palette.innerHTML = Object.entries(WORKFLOW_CATEGORIES).map(([category, label]) => {
        const nodes = WORKFLOW_NODE_LIBRARY.filter((node) => node.category === category);
        return `
            <div class="workflow-palette-group">
                <h3>${escapeHtml(label)}</h3>
                ${nodes.map((node) => {
                    const used = workflowState.nodes.some((item) => item.symbol === node.symbol);
                    return `
                        <button class="workflow-palette-item ${used ? "used" : ""}" type="button" data-workflow-add="${escapeHtml(node.symbol)}" ${workflowState.readOnly ? "disabled" : ""}>
                            <span>${escapeHtml(workflowFuturesDisplayName(node.symbol, node.name))}</span>
                            <small>${escapeHtml(standardInstrumentCode(node.symbol))}</small>
                        </button>
                    `;
                }).join("")}
            </div>
        `;
    }).join("");
    palette.querySelectorAll("[data-workflow-add]").forEach((button) => {
        button.addEventListener("click", () => addWorkflowNode(button.dataset.workflowAdd));
    });
}

function addWorkflowNode(symbol) {
    if (workflowState.readOnly) return;
    if (!symbol) return;
    const existing = workflowState.nodes.find((node) => node.symbol === symbol);
    if (existing) {
        workflowState.selectedNodeId = existing.id;
        renderWorkflowCanvas();
        return;
    }
    const maxX = workflowState.nodes.reduce((value, item) => Math.max(value, item.x || 0), 0);
    const sameColumnCount = workflowState.nodes.filter((item) => item.x >= maxX - 20).length;
    const node = {
        id: `node-${symbol.replace(/[^a-zA-Z0-9]+/g, "-")}-${Date.now().toString(36)}`,
        symbol,
        x: maxX + 260,
        y: 34 + sameColumnCount * 158,
    };
    workflowState.nodes.push(node);
    workflowState.selectedNodeId = node.id;
    workflowState.selectedLinkId = null;
    renderWorkflowPalette();
    renderWorkflowCanvas();
    refreshWorkflowNodeQuote(node);
    scheduleWorkflowSave();
}

function importWorkflowSymbol(rawSymbol) {
    const symbol = normalizeWorkflowImportSymbol(rawSymbol);
    if (!symbol) return;
    addWorkflowNode(symbol);
    const input = document.getElementById("workflow-symbol-input");
    if (input) input.value = "";
}

function normalizeWorkflowImportSymbol(rawSymbol) {
    return resolveMarketSymbol(rawSymbol);
}

function resolveMarketSymbol(rawSymbol) {
    const value = String(rawSymbol || "").trim();
    if (!value) return "";
    const lower = value.toLowerCase();
    const compact = lower.replace(/\s+/g, "");
    const known = [...WORKFLOW_NODE_LIBRARY, ...quoteSelectSymbols()]
        .find((item) => [item.symbol, item.name, item.group, item.lane].some((field) => String(field || "").toLowerCase() === lower));
    if (known?.symbol) return known.symbol;
    const fuzzy = [...WORKFLOW_NODE_LIBRARY, ...quoteSelectSymbols()]
        .find((item) => [item.symbol, item.name, item.group, item.lane].some((field) => String(field || "").toLowerCase().includes(compact)));
    if (fuzzy?.symbol) return fuzzy.symbol;
    if (/^(sh|sz|bj)\d{6}$/i.test(value)) return value.toLowerCase();
    if (/^\d{6}$/.test(value)) {
        if (/^(5|6|9)/.test(value)) return `sh${value}`;
        if (/^(8|4)/.test(value)) return `bj${value}`;
        return `sz${value}`;
    }
    if (/^hk_\d{1,5}$/i.test(value)) return value.toLowerCase();
    if (/^hk\d{1,5}$/i.test(value)) return `hk_${value.replace(/^hk/i, "").padStart(4, "0")}`;
    if (/^us_[a-z.]+$/i.test(value)) return value.toUpperCase().replace(/^US_/, "us_");
    if (/^[a-z.]{1,8}$/i.test(value)) return `us_${value.toUpperCase()}`;
    return value;
}

function quoteSelectSymbols() {
    const select = document.getElementById("quote-symbol-select");
    if (!select) return [];
    return [...select.options].map((option) => ({
        symbol: option.value,
        name: option.dataset.displayName || option.textContent || option.value,
    }));
}

function normalizeQuoteSelectLabels() {
    const select = document.getElementById("quote-symbol-select");
    if (!select) return;
    [...select.options].forEach((option) => {
        if (!option.value || option.dataset.displayName) return;
        const displayName = String(option.textContent || option.value).trim();
        option.dataset.displayName = displayName;
        const code = standardInstrumentCode(option.value);
        option.textContent = code ? `${displayName}（${code}）` : displayName;
    });
}

function syncQuoteSymbolSelect(symbol) {
    const select = document.getElementById("quote-symbol-select");
    if (!select) return;
    const option = [...select.options].find((item) => item.value === symbol);
    if (option) select.value = symbol;
}

const WORKFLOW_NODE_WIDTH = 232;
const WORKFLOW_NODE_HEIGHT = 172;
const WORKFLOW_WORLD_PADDING = 44;
const WORKFLOW_MIN_ZOOM = 0.35;
const WORKFLOW_MAX_ZOOM = 2.4;

function workflowCanvasBounds() {
    const positions = workflowState.nodes.map((node) => ({
        x: Number(node.x) || 0,
        y: Number(node.y) || 0,
    }));
    const minX = Math.min(0, ...positions.map((node) => node.x - WORKFLOW_WORLD_PADDING));
    const minY = Math.min(0, ...positions.map((node) => node.y - WORKFLOW_WORLD_PADDING));
    const maxX = Math.max(640, ...positions.map((node) => node.x + WORKFLOW_NODE_WIDTH + WORKFLOW_WORLD_PADDING));
    const maxY = Math.max(420, ...positions.map((node) => node.y + WORKFLOW_NODE_HEIGHT + WORKFLOW_WORLD_PADDING));
    return { minX, minY, maxX, maxY, width: maxX - minX, height: maxY - minY };
}

function applyWorkflowViewportTransform() {
    const stage = document.getElementById("workflow-stage");
    if (!stage) return;
    const viewport = workflowState.viewport;
    stage.style.transform = `translate(${viewport.panX}px, ${viewport.panY}px) scale(${viewport.zoom})`;
}

function prepareWorkflowCanvasStage() {
    const stage = document.getElementById("workflow-stage");
    if (!stage) return;
    const bounds = workflowCanvasBounds();
    stage.style.width = `${bounds.maxX}px`;
    stage.style.height = `${bounds.maxY}px`;
    applyWorkflowViewportTransform();
}

function fitWorkflowView({ userAdjusted = false } = {}) {
    const canvas = document.getElementById("workflow-canvas");
    if (!canvas || !canvas.clientWidth || !canvas.clientHeight) return;
    const bounds = workflowCanvasBounds();
    const insetX = 36;
    const insetTop = 36;
    const insetBottom = 78;
    const availableWidth = Math.max(1, canvas.clientWidth - insetX * 2);
    const availableHeight = Math.max(1, canvas.clientHeight - insetTop - insetBottom);
    const zoom = clamp(Math.min(availableWidth / bounds.width, availableHeight / bounds.height), WORKFLOW_MIN_ZOOM, 1.15);
    workflowState.viewport.zoom = zoom;
    workflowState.viewport.panX = insetX + (availableWidth - bounds.width * zoom) / 2 - bounds.minX * zoom;
    workflowState.viewport.panY = insetTop + (availableHeight - bounds.height * zoom) / 2 - bounds.minY * zoom;
    workflowState.viewport.initialized = true;
    workflowState.viewport.userAdjusted = userAdjusted;
    prepareWorkflowCanvasStage();
}

function resetWorkflowView() {
    workflowState.viewport.zoom = 1;
    workflowState.viewport.panX = 24;
    workflowState.viewport.panY = 24;
    workflowState.viewport.initialized = true;
    workflowState.viewport.userAdjusted = true;
    prepareWorkflowCanvasStage();
}

function handleWorkflowWheel(event) {
    event.preventDefault();
    const canvas = event.currentTarget;
    const rect = canvas.getBoundingClientRect();
    const viewport = workflowState.viewport;
    const priorZoom = viewport.zoom;
    const nextZoom = clamp(priorZoom * Math.exp(-event.deltaY * 0.0015), WORKFLOW_MIN_ZOOM, WORKFLOW_MAX_ZOOM);
    if (nextZoom === priorZoom) return;
    const cursorX = event.clientX - rect.left;
    const cursorY = event.clientY - rect.top;
    const worldX = (cursorX - viewport.panX) / priorZoom;
    const worldY = (cursorY - viewport.panY) / priorZoom;
    viewport.zoom = nextZoom;
    viewport.panX = cursorX - worldX * nextZoom;
    viewport.panY = cursorY - worldY * nextZoom;
    viewport.initialized = true;
    viewport.userAdjusted = true;
    applyWorkflowViewportTransform();
}

function setupWorkflowCanvasResizeObserver(canvas) {
    if (workflowState.canvasObserver || !window.ResizeObserver) return;
    workflowState.canvasObserver = new ResizeObserver(() => {
        if (workflowState.viewport.userAdjusted) {
            renderWorkflowLinks();
        } else {
            fitWorkflowView();
        }
    });
    workflowState.canvasObserver.observe(canvas);
}

function renderWorkflowCanvas({ fit = false } = {}) {
    const container = document.getElementById("workflow-nodes");
    if (!container) return;
    prepareWorkflowCanvasStage();
    container.innerHTML = workflowState.nodes.map((node) => renderWorkflowNode(node)).join("");
    container.querySelectorAll(".workflow-node").forEach((element) => {
        element.addEventListener("pointerdown", startWorkflowDrag);
        element.addEventListener("click", handleWorkflowNodeClick);
        element.addEventListener("contextmenu", (event) => {
            event.preventDefault();
            if (workflowState.readOnly) return;
            removeWorkflowNode(element.dataset.nodeId);
        });
        element.querySelectorAll("[data-workflow-port]").forEach((port) => {
            port.addEventListener("pointerdown", (event) => event.stopPropagation());
            port.addEventListener("click", (event) => handleWorkflowPortClick(event, element.dataset.nodeId, port.dataset.workflowPort));
        });
        element.querySelector("[data-workflow-remove]")?.addEventListener("click", (event) => {
            event.stopPropagation();
            removeWorkflowNode(element.dataset.nodeId);
        });
    });
    renderWorkflowLinks();
    renderWorkflowInspector();
    if (fit || !workflowState.viewport.initialized) fitWorkflowView();
}

function renderWorkflowNode(node) {
    const meta = workflowNodeMeta(node);
    const quote = workflowState.quotes.get(node.symbol);
    const chainAlert = workflowChainAlertForNode(node.id);
    const move = quote?.move;
    const trend = trendClassForValue(move);
    const marketTrend = marketTrendClassForValue(move);
    const selected = workflowState.selectedNodeId === node.id ? "selected" : "";
    const source = workflowState.connectSourceId === node.id ? `connect-source connect-source-${workflowState.connectSourcePort}` : "";
    const status = quote?.error ? "error" : quote ? "" : "loading";
    const displayName = node.nodeKind === "supplier" ? meta.name : quoteDisplayName(quote?.name, node.symbol);
    const groupAndCode = [meta.group || WORKFLOW_CATEGORIES[meta.category] || meta.category, standardInstrumentCode(node.symbol)].filter(Boolean).join(" · ");
    const controls = workflowState.readOnly ? "" : `
        <button class="workflow-port workflow-port-left" type="button" data-workflow-port="left" aria-label="连接到 ${escapeHtml(meta.name)}"></button>
        <button class="workflow-port workflow-port-right" type="button" data-workflow-port="right" aria-label="从 ${escapeHtml(meta.name)} 连接"></button>`;
    return `
        <article class="workflow-node ${node.nodeKind === "supplier" ? "supplier-workflow-node" : ""} ${selected} ${source} ${status} ${chainAlert ? `chain-${normalizeRiskLevel(chainAlert.severity)}` : ""}" data-node-id="${escapeHtml(node.id)}" data-symbol="${escapeHtml(node.symbol)}" style="transform: translate(${node.x}px, ${node.y}px);">
            ${controls}
            <div class="workflow-node-top">
                <div>
                    <h3>${escapeHtml(displayName)}</h3>
                    <span>${escapeHtml(groupAndCode)}</span>
                </div>
                ${workflowState.readOnly ? "" : '<button type="button" aria-label="移除节点" data-workflow-remove>×</button>'}
            </div>
            <div class="workflow-node-quote">
                <strong>${workflowQuotePrice(quote)}</strong>
                <span class="market-change ${trend} ${marketTrend}">${workflowQuoteMove(quote, move)}</span>
            </div>
            ${node.nodeKind === "supplier" ? `<div class="workflow-supplier-hint">${workflowState.readOnly ? "比赛演练映射：非真实供货关系" : "请手工连线并标注证据口径"}</div>` : ""}
            ${chainAlert ? `<div class="workflow-chain-alert">链条传导 ${Math.round((Number(chainAlert.transmission_score) || 0) * 100)}%</div>` : ""}
            <svg class="workflow-spark" viewBox="0 0 160 42" preserveAspectRatio="none">${renderWorkflowSparkPath(quote?.points || [], move, node.symbol)}</svg>
            <div class="workflow-node-meta">${quote ? `${escapeHtml(meta.lane || quoteSourceLabel(quote.source))} · ${escapeHtml(quote.asOf || node.symbol)}` : "正在接收行情"}</div>
        </article>
    `;
}

function workflowChainAlertForNode(nodeId) {
    const alerts = backendState.externalRisk?.chain_alerts || [];
    return alerts
        .filter((alert) => Array.isArray(alert.affected_node_ids) && alert.affected_node_ids.includes(nodeId))
        .sort((left, right) => Number(right.transmission_score || 0) - Number(left.transmission_score || 0))[0] || null;
}

function workflowChainAlertForLink(link) {
    const alerts = backendState.externalRisk?.chain_alerts || [];
    return alerts
        .filter((alert) => Array.isArray(alert.path_node_ids)
            && alert.path_node_ids.some((nodeId, index) => nodeId === link.source && alert.path_node_ids[index + 1] === link.target))
        .sort((left, right) => Number(right.transmission_score || 0) - Number(left.transmission_score || 0))[0] || null;
}

function handleWorkflowPortClick(event, nodeId, port = "right") {
    event.preventDefault();
    event.stopPropagation();
    if (workflowState.readOnly) return;
    if (!workflowState.connectSourceId) {
        workflowState.connectSourceId = nodeId;
        workflowState.connectSourcePort = port;
        workflowState.selectedNodeId = nodeId;
        workflowState.selectedLinkId = null;
        renderWorkflowCanvas();
        return;
    }
    if (workflowState.connectSourceId === nodeId && workflowState.connectSourcePort === port) {
        workflowState.connectSourceId = null;
        workflowState.connectSourcePort = "right";
        renderWorkflowCanvas();
        return;
    }
    addWorkflowLink(workflowState.connectSourceId, nodeId, workflowState.connectSourcePort, port);
    workflowState.connectSourceId = null;
    workflowState.connectSourcePort = "right";
    workflowState.selectedNodeId = null;
    renderWorkflowCanvas();
}

function handleWorkflowNodeClick(event) {
    if (workflowState.dragSuppressClick) {
        workflowState.dragSuppressClick = false;
        return;
    }
    const element = event.currentTarget;
    const nodeId = element.dataset.nodeId;
    const node = workflowState.nodes.find((item) => item.id === nodeId);
    if (!node) return;
    if (!workflowState.readOnly && workflowState.connectMode) {
        if (!workflowState.connectSourceId) {
            workflowState.connectSourceId = nodeId;
            workflowState.connectSourcePort = "right";
        } else if (workflowState.connectSourceId !== nodeId) {
            const link = workflowDirectionalLink(workflowState.connectSourceId, nodeId);
            addWorkflowLink(link.source, link.target, link.sourcePort, link.targetPort, link.relation, link);
            workflowState.connectSourceId = null;
            workflowState.connectSourcePort = "right";
        }
    }
    workflowState.selectedNodeId = nodeId;
    workflowState.selectedLinkId = null;
    selectWorkflowQuote(node.symbol);
    renderWorkflowCanvas();
}

function addWorkflowLink(source, target, sourcePort = "right", targetPort = "left", relation = null, metadata = {}) {
    if (workflowState.readOnly) return;
    if (workflowState.links.some((link) => link.source === source && link.target === target)) return;
    const sourceNode = workflowState.nodes.find((node) => node.id === source);
    const targetNode = workflowState.nodes.find((node) => node.id === target);
    workflowState.links.push({
        source, target, sourcePort, targetPort, relation,
        relationId: metadata.relationId || newWorkflowRelationId(source, target),
        sourceKind: metadata.sourceKind || "manual_canvas",
        correlationLayers: metadata.correlationLayers || defaultWorkflowCorrelationLayers(sourceNode, targetNode),
        evidenceGrade: metadata.evidenceGrade || "unverified",
        relationshipScope: metadata.relationshipScope || "industry_proxy",
        evidenceRefs: metadata.evidenceRefs || [],
        boundaryNote: metadata.boundaryNote || "",
        confirmedBy: metadata.confirmedBy || null,
        confirmedAt: metadata.confirmedAt || null,
        updatedAt: metadata.updatedAt || null,
    });
    workflowState.selectedLinkId = workflowLinkId(source, target);
    renderSupplyWorkspace();
    scheduleWorkflowSave();
}

function removeWorkflowNode(nodeId) {
    if (workflowState.readOnly) return;
    workflowState.nodes = workflowState.nodes.filter((node) => node.id !== nodeId);
    workflowState.links = workflowState.links.filter((link) => link.source !== nodeId && link.target !== nodeId);
    if (workflowState.selectedNodeId === nodeId) workflowState.selectedNodeId = workflowState.nodes[0]?.id || null;
    if (workflowState.connectSourceId === nodeId) workflowState.connectSourceId = null;
    if (workflowState.selectedLinkId && !workflowState.links.some((link) => workflowLinkId(link.source, link.target) === workflowState.selectedLinkId)) {
        workflowState.selectedLinkId = null;
    }
    renderWorkflowPalette();
    renderWorkflowCanvas();
    renderSupplyWorkspace();
    scheduleWorkflowSave();
}

function removeWorkflowLink(linkId) {
    if (workflowState.readOnly) return;
    workflowState.links = workflowState.links.filter((link) => workflowLinkId(link.source, link.target) !== linkId);
    if (workflowState.selectedLinkId === linkId) workflowState.selectedLinkId = null;
    renderWorkflowCanvas();
    renderSupplyWorkspace();
    scheduleWorkflowSave();
}

function startWorkflowDrag(event) {
    if (event.button !== 0 || event.target.closest("button")) return;
    const element = event.currentTarget;
    const node = workflowState.nodes.find((item) => item.id === element.dataset.nodeId);
    const canvas = document.getElementById("workflow-canvas");
    if (!node || !canvas) return;
    workflowState.drag = {
        nodeId: node.id,
        startX: event.clientX,
        startY: event.clientY,
        originX: node.x,
        originY: node.y,
        moved: false,
    };
    element.setPointerCapture?.(event.pointerId);
    element.classList.add("dragging");
}

function handleWorkflowPointerMove(event) {
    if (!workflowState.drag) return;
    const node = workflowState.nodes.find((item) => item.id === workflowState.drag.nodeId);
    if (!node) return;
    const zoom = workflowState.viewport.zoom || 1;
    node.x = clamp(workflowState.drag.originX + (event.clientX - workflowState.drag.startX) / zoom, 16, 16000);
    node.y = clamp(workflowState.drag.originY + (event.clientY - workflowState.drag.startY) / zoom, 16, 16000);
    if (Math.abs(event.clientX - workflowState.drag.startX) > 3 || Math.abs(event.clientY - workflowState.drag.startY) > 3) {
        workflowState.drag.moved = true;
    }
    const element = document.querySelector(`[data-node-id="${cssEscape(node.id)}"]`);
    if (element) element.style.transform = `translate(${node.x}px, ${node.y}px)`;
    prepareWorkflowCanvasStage();
    renderWorkflowLinks();
}

function stopWorkflowDrag() {
    if (!workflowState.drag) return;
    document.querySelectorAll(".workflow-node.dragging").forEach((node) => node.classList.remove("dragging"));
    const moved = workflowState.drag.moved;
    workflowState.drag = null;
    if (moved) {
        window.setTimeout(() => {
            workflowState.dragSuppressClick = false;
        }, 0);
        workflowState.dragSuppressClick = true;
        scheduleWorkflowSave();
    }
}

function startWorkflowPan(event) {
    if (event.button !== 0) return;
    const canvas = event.currentTarget;
    if (event.target !== canvas && event.target.id !== "workflow-stage" && event.target.id !== "workflow-nodes" && event.target.id !== "workflow-links") return;
    workflowState.pan = {
        pointerId: event.pointerId,
        startX: event.clientX,
        startY: event.clientY,
        panX: workflowState.viewport.panX,
        panY: workflowState.viewport.panY,
        moved: false,
    };
    canvas.setPointerCapture?.(event.pointerId);
    canvas.classList.add("panning");
}

function handleWorkflowPanMove(event) {
    if (!workflowState.pan) return;
    const canvas = document.getElementById("workflow-canvas");
    if (!canvas) return;
    const dx = event.clientX - workflowState.pan.startX;
    const dy = event.clientY - workflowState.pan.startY;
    workflowState.viewport.panX = workflowState.pan.panX + dx;
    workflowState.viewport.panY = workflowState.pan.panY + dy;
    workflowState.viewport.initialized = true;
    workflowState.viewport.userAdjusted = true;
    applyWorkflowViewportTransform();
    if (Math.abs(dx) > 3 || Math.abs(dy) > 3) {
        workflowState.pan.moved = true;
    }
}

function stopWorkflowPan(event) {
    if (!workflowState.pan) return;
    const canvas = document.getElementById("workflow-canvas");
    const moved = workflowState.pan.moved;
    canvas?.releasePointerCapture?.(workflowState.pan.pointerId ?? event?.pointerId);
    canvas?.classList.remove("panning");
    workflowState.pan = null;
    if (moved) {
        workflowState.panSuppressClick = true;
        window.setTimeout(() => {
            workflowState.panSuppressClick = false;
        }, 0);
    }
}

function renderWorkflowLinks() {
    const svg = document.getElementById("workflow-links");
    if (!svg) return;
    const bounds = workflowCanvasBounds();
    const width = bounds.maxX;
    const height = bounds.maxY;
    svg.style.width = `${width}px`;
    svg.style.height = `${height}px`;
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.innerHTML = workflowState.links.map((link) => {
        const source = workflowState.nodes.find((node) => node.id === link.source);
        const target = workflowState.nodes.find((node) => node.id === link.target);
        if (!source || !target) return "";
        const linkId = workflowLinkId(link.source, link.target);
        const selected = workflowState.selectedLinkId === linkId ? "selected" : "";
        const chainAlert = workflowChainAlertForLink(link);
        const sourcePort = link.sourcePort || "right";
        const targetPort = link.targetPort || "left";
        const start = workflowPortPoint(source, sourcePort);
        const end = workflowPortPoint(target, targetPort);
        const x1 = start.x;
        const y1 = start.y;
        const x2 = end.x;
        const y2 = end.y;
        const direction = sourcePort === "left" ? -1 : 1;
        const targetDirection = targetPort === "right" ? 1 : -1;
        const mid = Math.max(56, Math.abs(x2 - x1) * 0.42);
        const d = `M${x1} ${y1} C${x1 + direction * mid} ${y1}, ${x2 + targetDirection * mid} ${y2}, ${x2} ${y2}`;
        return `
            <path class="workflow-link-hit" data-link-id="${escapeHtml(linkId)}" d="${d}"></path>
            <path class="workflow-link ${selected} ${chainAlert ? `chain-${normalizeRiskLevel(chainAlert.severity)}` : ""}" data-link-id="${escapeHtml(linkId)}" d="${d}"></path>
        `;
    }).join("");
    svg.querySelectorAll(".workflow-link-hit").forEach((path) => {
        path.addEventListener("click", (event) => {
            event.stopPropagation();
            workflowState.selectedLinkId = path.dataset.linkId;
            workflowState.selectedNodeId = null;
            renderWorkflowCanvas();
        });
        path.addEventListener("contextmenu", (event) => {
            event.preventDefault();
            event.stopPropagation();
            if (workflowState.readOnly) return;
            removeWorkflowLink(path.dataset.linkId);
        });
    });
}

function workflowPortPoint(node, port) {
    const size = workflowNodeSize(node);
    return {
        x: Number(node.x || 0) + (port === "left" ? -8 : size.width + 8),
        y: Number(node.y || 0) + size.height / 2,
    };
}

function workflowNodeSize(node) {
    const element = document.querySelector(`[data-node-id="${cssEscape(node.id)}"]`);
    if (element) {
        return {
            width: element.offsetWidth || 232,
            height: element.offsetHeight || 132,
        };
    }
    return { width: 232, height: 132 };
}

function workflowLinkId(source, target) {
    return `${source}--${target}`;
}

function workflowRelationLabel(relation) {
    const labels = {
        industry_material_position: "材料位置关系",
        industry_equipment_position: "设备位置关系",
        industry_design_to_foundry_position: "设计至代工位置关系",
        industry_manufacturing_position: "制造位置关系",
        industry_packaging_to_system_position: "封装至系统位置关系",
    };
    return labels[relation] || relation || "上游至下游关系";
}

function workflowEvidenceGradeLabel(grade) {
    return {
        unverified: "待核验",
        scenario_proxy: "演练代理",
        document_referenced: "文档佐证",
        contract_verified: "合同核验",
    }[grade] || "待核验";
}

function workflowScopeLabel(scope) {
    return {
        industry_proxy: "行业位置代理",
        cost_proxy: "成本传导代理",
        commercial_relationship: "商业关系",
        peer_reference: "同业参考",
    }[scope] || "行业位置代理";
}

function workflowRelationSourceLabel(source) {
    return {
        commodity_catalog: "商品目录",
        supplier_master: "供应商主数据",
        imported: "公开材料导入",
        scenario: "演练场景",
        legacy: "历史关系",
    }[source] || source || "未标注";
}

function renderWorkflowInspector() {
    const inspector = document.getElementById("workflow-inspector");
    if (!inspector) return;
    if (workflowState.selectedLinkId) {
        renderWorkflowLinkInspector(inspector, workflowState.selectedLinkId);
        return;
    }
    const node = workflowState.nodes.find((item) => item.id === workflowState.selectedNodeId);
    if (!node) {
        inspector.innerHTML = `<div class="empty-state">选择一个卡片查看行情与风险含义。</div>`;
        return;
    }
    const meta = workflowNodeMeta(node);
    const quote = workflowState.quotes.get(node.symbol);
    const move = quote?.move;
    const trend = trendClassForValue(move);
    const marketTrend = marketTrendClassForValue(move);
    const upstream = workflowState.links.filter((link) => link.target === node.id).length;
    const downstream = workflowState.links.filter((link) => link.source === node.id).length;
    const recommendations = (workflowState.readOnly ? [] : meta.recommendations || [])
        .map((symbol) => workflowLibraryBySymbol(symbol))
        .filter((item) => item?.symbol && item.symbol !== node.symbol);
    inspector.innerHTML = `
        <div class="workflow-inspector-head">
            <span>${escapeHtml(meta.lane || WORKFLOW_CATEGORIES[meta.category] || meta.category)}</span>
            <h3>${escapeHtml(meta.name)}</h3>
            <p>${escapeHtml(meta.note)}</p>
        </div>
        <div class="workflow-inspector-price">
            <strong>${quote ? formatPrice(quote.latest) : "--"}</strong>
            <span class="market-change ${trend} ${marketTrend}">${quote ? workflowQuoteMove(quote, move) : "--"}</span>
        </div>
        <div class="workflow-inspector-grid">
            <div><span>上游</span><strong>${upstream}</strong></div>
            <div><span>下游</span><strong>${downstream}</strong></div>
            <div><span>证券/合约</span><strong>${escapeHtml(standardInstrumentCode(node.symbol))}</strong></div>
            <div><span>来源</span><strong>${quote ? escapeHtml(quoteSourceLabel(quote.source)) : "--"}</strong></div>
            <div><span>细分领域</span><strong>${escapeHtml(meta.group || "-")}</strong></div>
            <div><span>节点层级</span><strong>${escapeHtml(meta.lane || "-")}</strong></div>
        </div>
        ${recommendations.length ? `
            <div class="workflow-recommendations">
                <span>同类推荐</span>
                ${recommendations.map((item) => `
                    <button type="button" data-workflow-recommend="${escapeHtml(item.symbol)}">
                        ${escapeHtml(workflowFuturesDisplayName(item.symbol, item.name))}<small>${escapeHtml(standardInstrumentCode(item.symbol))}</small>
                    </button>
                `).join("")}
            </div>
        ` : ""}
        <button class="btn btn-primary workflow-inspector-open" type="button" data-open-symbol="${escapeHtml(node.symbol)}">查看主图</button>
    `;
    inspector.querySelector("[data-open-symbol]")?.addEventListener("click", () => selectWorkflowQuote(node.symbol));
    inspector.querySelectorAll("[data-workflow-recommend]").forEach((button) => {
        button.addEventListener("click", () => addWorkflowNode(button.dataset.workflowRecommend));
    });
}

function renderWorkflowLinkInspector(inspector, linkId) {
    const link = workflowState.links.find((item) => workflowLinkId(item.source, item.target) === linkId);
    if (!link) {
        inspector.innerHTML = `<div class="empty-state">选择一个卡片查看行情与风险含义。</div>`;
        return;
    }
    const sourceNode = workflowState.nodes.find((node) => node.id === link.source);
    const targetNode = workflowState.nodes.find((node) => node.id === link.target);
    const sourceMeta = workflowNodeMeta(sourceNode);
    const targetMeta = workflowNodeMeta(targetNode);
    inspector.innerHTML = `
        <div class="workflow-inspector-head">
            <span>${workflowState.readOnly ? "场景关系" : "连线"}</span>
            <h3>${escapeHtml(sourceMeta.name)} → ${escapeHtml(targetMeta.name)}</h3>
            <p>${escapeHtml(workflowRelationLabel(link.relation))}${workflowState.readOnly ? "。此调试场景只读。" : "。左键选中后高亮，右键可直接删除。"}</p>
        </div>
        <div class="workflow-inspector-grid">
            <div><span>上游证券/合约</span><strong>${escapeHtml(sourceNode ? standardInstrumentCode(sourceNode.symbol) : "-")}</strong></div>
            <div><span>下游证券/合约</span><strong>${escapeHtml(targetNode ? standardInstrumentCode(targetNode.symbol) : "-")}</strong></div>
            <div><span>起点圆心</span><strong>${link.sourcePort === "left" ? "左侧" : "右侧"}</strong></div>
            <div><span>终点圆心</span><strong>${link.targetPort === "left" ? "左侧" : "右侧"}</strong></div>
            <div><span>关系来源</span><strong>${escapeHtml(workflowRelationSourceLabel(link.sourceKind || "legacy"))}</strong></div>
            <div><span>证据等级</span><strong>${escapeHtml(workflowEvidenceGradeLabel(link.evidenceGrade))}</strong></div>
            <div><span>关系口径</span><strong>${escapeHtml(workflowScopeLabel(link.relationshipScope))}</strong></div>
            <div><span>风险计分</span><strong>${link.confirmedBy && link.confirmedAt ? `已确认 · ${escapeHtml(link.confirmedBy)}` : "未确认，不计入正式系数"}</strong></div>
            <div><span>相关性分层</span><strong>${escapeHtml((link.correlationLayers || []).join(" / ") || "未分类")}</strong></div>
            <div><span>关系编号</span><strong>${escapeHtml(link.relationId || "保存后生成")}</strong></div>
        </div>
        ${link.boundaryNote ? `<div class="workflow-boundary-note">${escapeHtml(link.boundaryNote)}</div>` : ""}
        ${link.evidenceRefs?.length ? `<div class="workflow-boundary-note">证据引用：${escapeHtml(link.evidenceRefs.join("、"))}</div>` : ""}
        ${workflowState.readOnly ? "" : `
            ${link.confirmedBy && link.confirmedAt ? "" : `<button class="btn btn-primary workflow-inspector-confirm" type="button" data-confirm-link="${escapeHtml(linkId)}">确认关系并纳入正式系数</button>`}
            <button class="btn workflow-inspector-delete" type="button" data-delete-link="${escapeHtml(linkId)}">删除连线</button>
        `}
    `;
    inspector.querySelector("[data-confirm-link]")?.addEventListener("click", () => confirmWorkflowLink(linkId));
    inspector.querySelector("[data-delete-link]")?.addEventListener("click", () => removeWorkflowLink(linkId));
}

function confirmWorkflowLink(linkId) {
    const link = workflowState.links.find((item) => workflowLinkId(item.source, item.target) === linkId);
    if (!link || workflowState.readOnly) return;
    const confirmedBy = window.prompt("请输入关系确认人姓名或工号；确认后才纳入正式风险系数");
    if (!confirmedBy?.trim()) return;
    link.confirmedBy = confirmedBy.trim();
    link.confirmedAt = new Date().toISOString();
    link.updatedAt = link.confirmedAt;
    renderWorkflowCanvas();
    scheduleWorkflowSave(0);
}

function selectWorkflowQuote(symbol) {
    quoteState.symbol = symbol;
    quoteState.manualUntil = Date.now() + 8000;
    resetQuoteWindow();
    syncQuoteSymbolSelect(symbol);
    const quoteSearch = document.getElementById("quote-symbol-search");
    if (quoteSearch) quoteSearch.value = symbol;
    refreshQuoteSeries();
}

function startWorkflowAutoRefresh() {
    if (workflowState.refreshTimer) window.clearInterval(workflowState.refreshTimer);
    workflowState.refreshTimer = window.setInterval(() => {
        if (document.hidden) return;
        refreshWorkflowQuotes();
    }, 30000);
}

async function refreshWorkflowQuotes() {
    if (workflowState.quoteRefreshPromise) return workflowState.quoteRefreshPromise;
    const nodes = [...workflowState.nodes];
    const concurrency = 3;
    let nextIndex = 0;
    const worker = async () => {
        while (nextIndex < nodes.length) {
            const node = nodes[nextIndex++];
            await refreshWorkflowNodeQuote(node);
        }
    };
    workflowState.quoteRefreshPromise = Promise.all(
        Array.from({ length: Math.min(concurrency, nodes.length) }, worker),
    ).finally(() => {
        workflowState.quoteRefreshPromise = null;
    });
    return workflowState.quoteRefreshPromise;
}

async function refreshWorkflowNodeQuote(node) {
    try {
        const params = new URLSearchParams({ symbol: node.symbol, interval: "intraday", _: String(Date.now()) });
        const payload = await fetchBackendJson(`/external-risk/quote-series?${params.toString()}`, { timeoutMs: 20000 });
        const data = payload.data || {};
        const rawPoints = Array.isArray(data.points) ? data.points.filter((point) => Number.isFinite(Number(point.close))) : [];
        const points = quoteIntradayDisplayPoints(rawPoints, node.symbol);
        if (!points.length) throw new Error("empty workflow quote");
        const visible = points.slice(-360);
        const serviceReference = Number(data.reference_price);
        const baseline = Number.isFinite(serviceReference) && serviceReference > 0
            ? serviceReference
            : quoteZeroBaseline(visible);
        const stats = quoteStats(visible, baseline);
        const serviceMove = Number(data.change_rate);
        workflowState.quotes.set(node.symbol, {
            latest: stats.latest,
            move: Number.isFinite(serviceMove) ? serviceMove : stats.move,
            points: visible,
            name: quoteDisplayName(data.name, node.symbol),
            source: data.source,
            asOf: data.as_of || visible[visible.length - 1]?.time || node.symbol,
            referencePrice: Number.isFinite(serviceReference) ? serviceReference : baseline,
            changeBasis: data.change_basis || "unavailable",
            instrumentStatus: data.instrument_status || "unknown",
            priceLimitLabel: data.price_limit_label || "",
        });
    } catch (error) {
        workflowState.quotes.set(node.symbol, { error: true, points: [], latest: null, move: 0, source: "provider_unavailable", asOf: node.symbol });
        console.info(error);
    }
    renderWorkflowCanvas();
}

function renderWorkflowSparkPath(points, move, symbol = quoteState.symbol) {
    const valid = points.filter((point) => Number.isFinite(Number(point.close)));
    if (valid.length < 2) return "";
    const width = 160;
    const height = 42;
    const pad = 4;
    const baseline = workflowSparkBaseline(valid);
    const moves = valid.map((point) => {
        const close = Number(point.close);
        return baseline ? (close - baseline) / baseline : 0;
    });
    const rangeAbs = Math.max(0.001, ...moves.map((value) => Math.abs(value))) * 1.12;
    const min = -rangeAbs;
    const max = rangeAbs;
    const range = max - min;
    const timeXForPoint = quoteIntradayXFor(valid, width, { left: pad, right: pad }, symbol);
    const timePositions = valid.map((point, index) => timeXForPoint(point, index));
    const plottedWidth = Math.max(...timePositions) - Math.min(...timePositions);
    const usableWidth = width - pad * 2;
    // Sector detail endpoints can return only the final few trading minutes. Spread that slice across
    // the card instead of rendering an unreadable fragment at the end of the all-day session axis.
    const xForPoint = plottedWidth < usableWidth * 0.32
        ? (_point, index) => pad + (valid.length <= 1 ? 0 : index / (valid.length - 1)) * usableWidth
        : timeXForPoint;
    const yFor = (value) => pad + ((max - value) / range) * (height - pad * 2);
    const d = moves.map((value, index) => `${index === 0 || quoteSessionBreak(valid, index, symbol) ? "M" : "L"}${xForPoint(valid[index], index).toFixed(1)} ${yFor(value).toFixed(1)}`).join(" ");
    const latestMove = Number.isFinite(Number(move)) ? Number(move) : moves[moves.length - 1] || 0;
    const trend = trendClassForValue(latestMove);
    const marketTrend = marketTrendClassForValue(latestMove);
    const zeroY = yFor(0);
    return `
        <line class="workflow-spark-zero" x1="${pad}" x2="${width - pad}" y1="${zeroY.toFixed(1)}" y2="${zeroY.toFixed(1)}"></line>
        <path class="${trend} ${marketTrend}" d="${d}"></path>
    `;
}

function workflowQuotePrice(quote) {
    if (!quote || quote.error || !Number.isFinite(Number(quote.latest))) return "--";
    return formatPrice(quote.latest);
}

function workflowQuoteMove(quote, move) {
    if (!quote || quote.error || !Number.isFinite(Number(move))) return "--";
    return formatPercentSigned(move, quote.instrumentStatus === "new_listing" ? 2 : 1);
}

function workflowSparkBaseline(points) {
    const explicitPoint = points.find((point) => Number.isFinite(Number(point.baseline_price)) && Number(point.baseline_price) !== 0);
    if (explicitPoint) return Number(explicitPoint.baseline_price);
    const first = points.find((point) => Number.isFinite(Number(point.open)) || Number.isFinite(Number(point.close)));
    if (first) return Number(first.open ?? first.close);
    return quoteZeroBaseline(points);
}

function cssEscape(value) {
    return window.CSS?.escape ? CSS.escape(value) : String(value).replace(/[^a-zA-Z0-9_-]/g, "\\$&");
}

function applyDashboardData(data, risks) {
    if (!data) return;
    const overall = data.overall_risk || {};
    const level = normalizeRiskLevel(overall.level);
    const scoreValue = document.querySelector(".score-value");
    if (scoreValue && typeof overall.score === "number") {
        scoreValue.innerHTML = `${overall.score}<span>/100</span>`;
        scoreValue.style.color = riskColorFor(level);
    }
    const trend = document.querySelector(".score-trend");
    if (trend && overall.summary) {
        trend.innerHTML = `<span class="risk-dot ${level}"></span>${escapeHtml(overall.summary)}`;
    }

    const dimensions = document.querySelector(".score-dimensions");
    if (dimensions && Array.isArray(data.key_metrics)) {
        dimensions.innerHTML = data.key_metrics.map((metric) => `
            <div class="dimension-card">
                <span>${escapeHtml(metric.label)}</span>
                <strong>${escapeHtml(metric.value)}</strong>
                <div class="metric-unit">${escapeHtml(metric.unit || "")}</div>
            </div>
        `).join("");
    }

    const riskById = new Map((risks || []).map((risk) => [risk.risk_id, risk]));
    const alertList = document.querySelector(".alert-list");
    if (alertList && Array.isArray(data.alerts) && data.alerts.length) {
        alertList.innerHTML = data.alerts.map((alert) => {
            const risk = normalizeRiskLevel(alert.severity || riskById.get(alert.risk_id)?.risk_level);
            return `
                <article class="alert-row">
                    <span class="risk-dot ${risk}"></span>
                    <div><strong>${escapeHtml(alert.title)}</strong><p>${escapeHtml(alert.message)}</p></div>
                    <span class="risk-text ${risk}">${riskLabels[risk]}</span>
                </article>
            `;
        }).join("");
    }

    const taskList = document.querySelector(".task-list");
    if (taskList && Array.isArray(data.tasks) && data.tasks.length) {
        taskList.innerHTML = data.tasks.map((task) => `
            <div class="task-item"><span>${escapeHtml(task.title)}</span><strong>${escapeHtml(task.due_date || task.status || "-")}</strong></div>
        `).join("");
    }

    const statusList = document.querySelector(".status-list");
    if (statusList && Array.isArray(data.data_sources) && data.data_sources.length) {
        statusList.innerHTML = data.data_sources.map((source) => {
            const risk = source.status === "ready" ? "low" : source.status === "mock" ? "med" : "high";
            return `
                <div class="status-row">
                    <span>${escapeHtml(source.label)}</span>
                    <strong><span class="risk-dot ${risk}"></span>${escapeHtml(source.status)}</strong>
                </div>
            `;
        }).join("");
    }
}

function applyMarketData(data) {
    if (!data || !Array.isArray(data.signals)) return;
    const cards = document.querySelectorAll(".market-card:not(.wide)");
    data.signals.slice(0, cards.length).forEach((signal, index) => {
        const card = cards[index];
        const risk = normalizeRiskLevel(signal.severity);
        const hasValue = typeof signal.value === "number";
        const trend = hasValue ? trendClassForValue(signal.value) : risk === "low" ? "flat" : "down";
        const marketTrend = hasValue ? marketTrendClassForValue(signal.value) : "market-flat";
        card.innerHTML = `
            <h3>${escapeHtml(externalSignalDisplayTitle(signal))}</h3>
            <div class="market-number ${trend} ${marketTrend}">${hasValue ? formatSignalValue(signal.value) : riskLabels[risk]}</div>
            <p>${escapeHtml(signal.summary)}</p>
        `;
    });

    const tbody = document.querySelector(".data-table tbody");
    if (tbody) {
        tbody.innerHTML = data.signals.map((signal) => {
            const risk = normalizeRiskLevel(signal.severity);
            const hasValue = typeof signal.value === "number";
            const trend = hasValue ? trendClassForValue(signal.value) : "flat";
            const marketTrend = hasValue ? marketTrendClassForValue(signal.value) : "market-flat";
            return `
                <tr>
                    <td>${escapeHtml(externalSignalDisplayTitle(signal))}</td>
                    <td>${hasValue ? `<span class="market-change ${trend} ${marketTrend}">${formatSignalValue(signal.value)}</span>` : escapeHtml(signal.direction || "-")}</td>
                    <td>${escapeHtml((signal.affected_domains || []).map(externalSignalDomainLabel).join(" / "))}</td>
                    <td><span class="risk-text ${risk}">${riskLabels[risk]}</span></td>
                    <td>${escapeHtml(signal.summary)}</td>
                </tr>
            `;
        }).join("");
    }
}

function normalizeProvinceName(location = {}) {
    const aliases = {
        Beijing: "北京",
        Shanghai: "上海",
        Jiangsu: "江苏",
        Zhejiang: "浙江",
        Guangdong: "广东",
        Sichuan: "四川",
        Shandong: "山东",
        Hebei: "河北",
    };
    return aliases[location.province] || location.province || location.region || location.country || "-";
}

function applySupplyChainData(data) {
    if (!data || !Array.isArray(data.nodes)) return;
    const suppliers = data.nodes.map((node) => ({
        name: node.label || node.node_id,
        province: normalizeProvinceName(node.location),
        country: node.location?.country || "",
        risk: normalizeRiskLevel(node.risk_level),
    }));
    const chinaSuppliers = suppliers.filter((supplier) => supplier.country === "China");
    const overseasSuppliers = suppliers.filter((supplier) => supplier.country !== "China");

    if (chinaSuppliers.length) {
        regionsData.china.suppliers = chinaSuppliers;
        regionsData.china.totalSuppliers = chinaSuppliers.length;
        regionsData.china.overallRisk = chinaSuppliers.some((item) => item.risk === "high" || item.risk === "crit") ? "high" : "med";
        chinaSuppliers.forEach((supplier) => {
            if (supplier.province && supplier.province !== "-") {
                provinceSupplierCounts[supplier.province] = Math.max(provinceSupplierCounts[supplier.province] || 0, 1);
                provinceRisk[supplier.province] = supplier.risk;
            }
        });
    }
    if (overseasSuppliers.length) {
        regionsData.overseas.suppliers = overseasSuppliers;
        regionsData.overseas.totalSuppliers = overseasSuppliers.length;
    }

    const summary = document.querySelector(".supply-summary");
    if (summary) {
        const highCount = suppliers.filter((supplier) => supplier.risk === "high" || supplier.risk === "crit").length;
        summary.innerHTML = `
            <span><strong>${suppliers.length}</strong> 后端节点</span>
            <span><strong>${data.edges?.length || 0}</strong> 关系</span>
            <span><strong class="orange">${highCount}</strong> 高风险</span>
        `;
    }
    renderDetailPanel(activeRegionKey || "china");
}

function applyLifecycleData(data) {
    if (!data) return;
    renderLifecycle();
}

function applyLegalWorkspaceData(data) {
    if (!data) return;
    const filePanel = document.querySelector(".file-panel");
    if (filePanel && Array.isArray(data.supported_upload_types)) {
        filePanel.dataset.supportedUploadTypes = data.supported_upload_types.join(",");
    }
}

function loadSelectedLegalDocumentIds() {
    try {
        const ids = JSON.parse(window.localStorage.getItem(LEGAL_DOCUMENT_SELECTION_KEY) || "[]");
        return new Set(Array.isArray(ids) ? ids.filter((value) => typeof value === "string") : []);
    } catch {
        return new Set();
    }
}

function saveSelectedLegalDocumentIds() {
    try {
        window.localStorage.setItem(LEGAL_DOCUMENT_SELECTION_KEY, JSON.stringify([...selectedLegalDocumentIds]));
    } catch {
        // The current selection remains usable for this page session.
    }
}

function loadLegalThreads() {
    try {
        const threads = JSON.parse(window.localStorage.getItem(LEGAL_THREADS_KEY) || "[]");
        return Array.isArray(threads) ? threads : [];
    } catch {
        return [];
    }
}

function saveLegalThreads() {
    try {
        window.localStorage.setItem(LEGAL_THREADS_KEY, JSON.stringify(legalThreads));
    } catch {
        // Keep the in-memory conversation even if storage is unavailable.
    }
}

function getCurrentThread() {
    let thread = legalThreads.find((item) => item.id === currentLegalThreadId);
    if (!thread) {
        thread = createLegalThread();
        legalThreads.unshift(thread);
        currentLegalThreadId = thread.id;
        saveLegalThreads();
    }
    return thread;
}

function createLegalThread() {
    return {
        id: createLegalThreadId(),
        title: NEW_LEGAL_THREAD_TITLE,
        messages: [],
        evidenceState: null,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
    };
}

function renderThreadList() {
    const list = document.getElementById("legal-thread-list");
    if (!list) return;
    if (!legalThreads.length) legalThreads.push(createLegalThread());
    list.innerHTML = legalThreads.map((thread) => `
        <div class="chat-thread ${thread.id === currentLegalThreadId ? "active" : ""}" role="button" tabindex="0" data-thread-id="${escapeHtml(thread.id)}" title="${escapeHtml(normalizeThreadTitle(thread.title))}">
            <span class="chat-thread-title">${escapeHtml(normalizeThreadTitle(thread.title))}</span>
            <button class="chat-delete-button" type="button" aria-label="删除对话" data-delete-thread="${escapeHtml(thread.id)}">
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M6 6l1 14h10l1-14"/></svg>
            </button>
        </div>
    `).join("");
}

function renderCurrentThread() {
    const messages = document.getElementById("legal-messages");
    if (!messages) return;
    const thread = getCurrentThread();
    messages.innerHTML = thread.messages.map((message) => renderMessage(message)).join("");
    messages.scrollTop = messages.scrollHeight;
    renderThreadList();
    renderEvidenceState(thread.evidenceState);
}

function renderMessage(message) {
    if (message.role === "user") return `<div class="msg-user">${escapeHtml(message.content)}</div>`;
    if (message.status === "thinking") return `<div class="msg-ai">${renderThinking()}</div>`;
    if (message.status === "streaming") return `<div class="msg-ai">${renderStreamingContent(message)}</div>`;
    if (message.status === "error") {
        return `<div class="msg-ai"><div class="ai-section"><div class="ai-section-title gray">分析服务暂不可用</div><p>${escapeHtml(message.content)}</p></div></div>`;
    }
    return `<div class="msg-ai">${renderAnswerContent(message.result)}</div>`;
}

function renderThinkingLegacy() {
    return `<div class="thinking-row"><span class="thinking-pulse" aria-hidden="true"></span><span>分析中</span></div>`;
}

function renderThinking(label = "\u5206\u6790\u4e2d") {
    return `<div class="thinking-row"><span class="thinking-pulse" aria-hidden="true"></span><span>${escapeHtml(label)}</span></div>`;
}

function classifyAnswerLine(line = "") {
    const text = String(line || "").trim();
    if (!text) return "break";
    if (/^(?:[（(]\d+[）)]|[①②③④⑤⑥⑦⑧⑨⑩])\s*/.test(text)) return "sub_list_item";
    if (/^(?:\d+[.、)]|[一二三四五六七八九十]+[、.)]|[-*•])\s*/.test(text)) return "list_item";
    if (text.length <= 28 && /(结论|依据|证据|建议|动作|风险|优先级|问题|补救|维权|制度)[:：]?$/.test(text)) return "heading";
    return "paragraph";
}

function normalizeListText(line = "") {
    return String(line || "").trim().replace(/^(?:\d+[.、)]|[一二三四五六七八九十]+[、.)]|[-*•])\s*/, "");
}

function normalizeSubListText(line = "") {
    return String(line || "").trim().replace(/^(?:[（(]\d+[）)]|[①②③④⑤⑥⑦⑧⑨⑩])\s*/, "");
}

function renderInlineAnswerText(value = "") {
    return escapeHtml(value)
        .replace(/^\*([^*]{1,32}?[：:])\*\*\s*/, "<strong>$1</strong> ")
        .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
        .replace(/\*(.+?)\*/g, "<strong>$1</strong>");
}

const ANSWER_SECTION_LABELS = new Set(["共同点", "相同点", "不同点", "差异点", "区别", "注意", "提示", "结论", "依据", "建议", "风险提示", "证据不足"]);
const ANSWER_NESTABLE_SECTION_LABELS = new Set(["共同点", "相同点", "不同点", "差异点", "区别", "依据", "建议", "证据不足"]);
const ANSWER_DIFFERENCE_LABELS = new Set(["不同点", "差异点", "区别"]);
const ANSWER_LIST_CLOSING_PATTERN = /^(综上|因此|总之|整体来看|总体而言|需要注意|由于检索|由于依据|由于材料)/;

function parseAnswerLabel(text = "") {
    const value = String(text || "").trim();
    const plainLabel = value.replace(/^\*+|\*+$/g, "").trim();
    if (ANSWER_SECTION_LABELS.has(plainLabel)) return { label: plainLabel, content: "" };

    const patterns = [
        /^\*([^*：:]{1,28})[：:]\*\*\s*(.*)$/,
        /^\*\*([^*：:]{1,28})\*\*[：:]\s*(.*)$/,
        /^\*\*([^*：:]{1,28}[：:])\*\*\s*(.*)$/,
        /^([^：:]{1,28})[：:]\s*(.*)$/,
    ];
    for (const pattern of patterns) {
        const match = value.match(pattern);
        if (!match) continue;
        const label = match[1].replace(/[：:]$/, "").trim();
        const content = (match[2] || "").trim();
        if (label) return { label, content };
    }
    return null;
}

function formatAnswerLabel(label, content = "") {
    const suffix = content ? ` ${content}` : "";
    return `**${label}：**${suffix}`.trim();
}

function normalizeAnswerListItems(items = []) {
    const normalized = [];
    for (let index = 0; index < items.length; index += 1) {
        const item = items[index];
        if (typeof item === "object") {
            normalized.push(item);
            continue;
        }
        const label = parseAnswerLabel(item);
        if (!label || !ANSWER_SECTION_LABELS.has(label.label)) {
            normalized.push(item);
            continue;
        }

        if (label.content) {
            normalized.push(formatAnswerLabel(label.label, label.content));
            continue;
        }

        const next = items[index + 1];
        const nextLabel = parseAnswerLabel(next || "");
        const shouldMergeNext = next && !(ANSWER_DIFFERENCE_LABELS.has(label.label) && nextLabel && !ANSWER_SECTION_LABELS.has(nextLabel.label));
        if (shouldMergeNext) {
            normalized.push(formatAnswerLabel(label.label, next));
            index += 1;
        } else {
            normalized.push(formatAnswerLabel(label.label));
        }
    }
    return normalized;
}

function shouldNestUnderDifference(item = "") {
    const label = parseAnswerLabel(item);
    return Boolean(label && !ANSWER_SECTION_LABELS.has(label.label));
}

function buildAnswerListTree(items = []) {
    const normalizedItems = normalizeAnswerListItems(items);
    const tree = [];
    let activeSection = null;

    normalizedItems.forEach((item) => {
        if (typeof item === "object" && item.kind === "sub_list_item") {
            const parent = activeSection || tree[tree.length - 1];
            if (parent) {
                parent.children.push(item.text);
                return;
            }
            tree.push({ text: item.text, children: [] });
            return;
        }
        const text = typeof item === "object" ? item.text : item;
        const label = parseAnswerLabel(text);
        if (label && ANSWER_NESTABLE_SECTION_LABELS.has(label.label)) {
            const node = { text, children: [] };
            tree.push(node);
            activeSection = node;
            return;
        }
        if (activeSection && (!label || !ANSWER_SECTION_LABELS.has(label.label))) {
            activeSection.children.push(text);
            return;
        }
        tree.push({ text, children: [] });
        if (label && ANSWER_SECTION_LABELS.has(label.label)) activeSection = null;
    });

    return tree;
}

function renderAnswerList(items = []) {
    const tree = buildAnswerListTree(items);
    return `<ol class="stream-list">${tree.map((item) => `
        <li>
            <span>${renderInlineAnswerText(item.text)}</span>
            ${item.children.length ? `<ol class="stream-sublist">${item.children.map((child) => `<li>${renderInlineAnswerText(child)}</li>`).join("")}</ol>` : ""}
        </li>
    `).join("")}</ol>`;
}

function parseComplexReviewAnswer(text = "") {
    const normalized = String(text || "").replace(/\r\n/g, "\n").replace(/\r/g, "\n");
    if (!/(初步判断|依据|补救\/应对动作|补救|应对动作)/.test(normalized)) return null;

    const lines = normalized.split("\n");
    const intro = [];
    const blocks = [];
    let current = null;
    let activeField = null;

    const issuePattern = /^(\d+)[.、]\s*(.+)$/;
    const fieldPattern = /^(初步判断|依据|补救\/应对动作|补救|应对动作|建议动作)[:：]\s*(.*)$/;
    const flushCurrent = () => {
        if (!current) return;
        const hasStructuredField = Object.values(current.fields).some((value) => value.trim());
        if (hasStructuredField) blocks.push(current);
        current = null;
        activeField = null;
    };

    lines.forEach((line) => {
        const trimmed = line.trim();
        if (!trimmed) return;

        const issueMatch = trimmed.match(issuePattern);
        if (issueMatch) {
            flushCurrent();
            current = {
                number: issueMatch[1],
                title: issueMatch[2],
                fields: {},
            };
            return;
        }

        if (!current) {
            intro.push(trimmed);
            return;
        }

        const fieldMatch = trimmed.match(fieldPattern);
        if (fieldMatch) {
            activeField = fieldMatch[1];
            current.fields[activeField] = fieldMatch[2] || "";
            return;
        }

        if (activeField) {
            current.fields[activeField] = `${current.fields[activeField] || ""} ${trimmed}`.trim();
        } else {
            current.title = `${current.title} ${trimmed}`.trim();
        }
    });
    flushCurrent();

    return blocks.length >= 2 ? { intro, blocks } : null;
}

function renderComplexReviewAnswer(text = "") {
    const parsed = parseComplexReviewAnswer(text);
    if (!parsed) return "";

    const fieldOrder = ["初步判断", "依据", "补救/应对动作", "补救", "应对动作", "建议动作"];
    const introHtml = parsed.intro.length
        ? `<div class="review-case-intro">${parsed.intro.map((item) => `<p>${escapeHtml(item)}</p>`).join("")}</div>`
        : "";
    const blocksHtml = parsed.blocks.map((block) => {
        const fields = fieldOrder
            .filter((label) => block.fields[label])
            .map((label) => `
                <div class="review-field">
                    <div class="review-field-label">${escapeHtml(label)}</div>
                    <div class="review-field-content">${escapeHtml(block.fields[label])}</div>
                </div>
            `).join("");
        return `
            <article class="review-issue-card">
                <div class="review-issue-heading">
                    <span class="review-issue-number">${escapeHtml(block.number)}</span>
                    <h3>${escapeHtml(block.title)}</h3>
                </div>
                <div class="review-field-grid">${fields}</div>
            </article>
        `;
    }).join("");

    return `${introHtml}<div class="review-issue-list">${blocksHtml}</div>`;
}

function renderFormattedAnswerText(text = "") {
    if (usesRichAnswerMarkup(text)) {
        return `<div class="answer-rich">${renderMarkdownAnswer(text)}</div>`;
    }

    const complexReview = renderComplexReviewAnswer(text);
    if (complexReview) return complexReview;

    const lines = String(text || "").replace(/\r\n/g, "\n").replace(/\r/g, "\n").split("\n");
    const blocks = [];
    let listItems = [];

    const flushList = () => {
        if (!listItems.length) return;
        blocks.push(renderAnswerList(listItems));
        listItems = [];
    };

    lines.forEach((line) => {
        const trimmed = line.trim();
        const kind = classifyAnswerLine(trimmed);
        if (kind === "break") return;
        if (kind === "list_item") {
            listItems.push(normalizeListText(trimmed));
            return;
        }
        if (kind === "sub_list_item") {
            listItems.push({ kind, text: normalizeSubListText(trimmed) });
            return;
        }
        if (kind === "heading") {
            flushList();
            blocks.push(`<div class="answer-subtitle">${renderInlineAnswerText(trimmed.replace(/[:：]$/, ""))}</div>`);
        } else if (listItems.length && !ANSWER_LIST_CLOSING_PATTERN.test(trimmed)) {
            listItems.push(trimmed);
        } else {
            flushList();
            blocks.push(`<p class="answer-paragraph">${renderInlineAnswerText(trimmed)}</p>`);
        }
    });
    flushList();

    return blocks.length ? blocks.join("") : "";
}

function renderStreamingContent(message = {}) {
    const content = message.content || "";
    const stage = message.stage || "\u5206\u6790\u4e2d";
    return `
        <div class="ai-section">
            <div class="ai-section-title">\u98ce\u9669\u7ed3\u8bba</div>
            ${content ? `<div class="streaming-answer">${renderFormattedAnswerText(content)}</div>` : renderThinking(stage)}
            <div class="streaming-status">${escapeHtml(stage)}</div>
        </div>
    `;
}

function renderAnswerContent(result = {}) {
    const actions = result.recommended_actions || [];
    const evidence = result.evidence_chain || [];
    const missing = result.missing_evidence || [];
    const materials = result.material_sources || [];
    return `
        <div class="ai-section">
            <div class="ai-section-title">风险结论</div>
            <div class="answer-body">${renderFormattedAnswerText(result.answer || "")}</div>
        </div>
        ${missing.length ? `<div class="ai-section"><div class="ai-section-title gray">缺少依据</div><ul class="ai-list">${missing.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul></div>` : ""}
        ${evidence.length ? `<div class="ai-section"><div class="ai-section-title gray">证据链</div><ol class="ai-list numbered">${evidence.map((item) => `<li>${escapeHtml(item.law_name || item.source || item.evidence_id || "")} ${escapeHtml(item.article || "")}</li>`).join("")}</ol></div>` : ""}
        ${materials.length ? `<div class="ai-section"><div class="ai-section-title gray">已审查合同材料</div><ul class="ai-list">${materials.map((item) => `<li>${escapeHtml(item.filename || "未命名合同")}${item.truncated ? "（已截断）" : ""}</li>`).join("")}</ul></div>` : ""}
        ${actions.length ? `<div class="ai-section"><div class="ai-section-title">建议动作</div><ul class="ai-list">${actions.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul></div>` : ""}
    `;
}

function normalizeThreadTitle(title) {
    return !title || /^\?+$/.test(title) ? NEW_LEGAL_THREAD_TITLE : title;
}

function persistAndRenderThread(threadId = currentLegalThreadId) {
    const thread = legalThreads.find((item) => item.id === threadId) || getCurrentThread();
    thread.updatedAt = new Date().toISOString();
    legalThreads = [thread, ...legalThreads.filter((item) => item.id !== thread.id)];
    saveLegalThreads();
    if (thread.id === currentLegalThreadId) renderCurrentThread();
    else renderThreadList();
}

function appendChatMessage(message) {
    const thread = getCurrentThread();
    thread.messages.push(message);
    if (message.role === "user" && normalizeThreadTitle(thread.title) === NEW_LEGAL_THREAD_TITLE) {
        thread.title = message.content.length > 18 ? `${message.content.slice(0, 18)}...` : message.content;
    }
    persistAndRenderThread();
    return message.id;
}

function replaceThreadMessage(threadId, messageId, nextMessage) {
    const thread = legalThreads.find((item) => item.id === threadId);
    if (!thread) return;
    const index = thread.messages.findIndex((message) => message.id === messageId);
    if (index >= 0) thread.messages[index] = nextMessage;
    persistAndRenderThread(thread.id);
}

function resetEvidencePanel() {
    renderEvidenceState(null);
}

function renderEvidenceState(state) {
    const empty = document.getElementById("evidence-empty");
    const confidence = document.getElementById("evidence-confidence");
    const quote = document.getElementById("evidence-quote");
    const tags = document.getElementById("risk-tags");
    const provenance = document.getElementById("evidence-provenance");
    if (!state) {
        if (empty) {
            empty.hidden = false;
            empty.textContent = "等待分析";
        }
        if (confidence) {
            confidence.hidden = true;
            confidence.innerHTML = "";
        }
        if (quote) {
            quote.hidden = true;
            quote.innerHTML = "";
        }
        if (provenance) {
            provenance.hidden = true;
            provenance.innerHTML = "";
            provenance.removeAttribute("data-mode");
        }
        if (tags) tags.innerHTML = "";
        return;
    }
    if (empty) {
        empty.hidden = Boolean(state.firstEvidence);
        empty.textContent = state.missing?.length ? `缺少依据：${state.missing[0]}` : "暂无可引用依据";
    }
    if (confidence && !state.firstEvidence) {
        confidence.hidden = true;
        confidence.innerHTML = "";
    } else if (confidence && state.confidenceScore != null) {
        const pct = Math.round(state.confidenceScore * 100);
        confidence.hidden = false;
        confidence.innerHTML = `<span>置信度</span><strong>${pct}%</strong><div class="risk-bar"><div style="width:${pct}%; background:#212529;"></div></div>`;
    }
    if (quote && state.firstEvidence) {
        quote.hidden = false;
        quote.innerHTML = `${escapeHtml(state.firstEvidence.excerpt || state.firstEvidence.text || "")}<span>${escapeHtml(state.firstEvidence.law_name || state.firstEvidence.source || state.firstEvidence.evidence_id || "")}</span>`;
    }
    if (provenance && state.retrievalStatus) {
        const status = state.retrievalStatus;
        const confidence = Number(status.retrieval_confidence);
        const facts = [];
        if (Number.isFinite(confidence)) facts.push(`检索置信度 ${Math.round(confidence * 100)}%`);
        facts.push(`可引用证据 ${Number(status.evidence_count) || 0} 条`);
        if (Number(status.material_count) > 0) facts.push(`已用材料 ${Number(status.material_count)} 份`);
        if (status.backend_url) facts.push(`服务 ${String(status.backend_url).replace(/^https?:\/\//, "")}`);
        if (status.collection_name) facts.push(`法库 ${status.collection_name}`);
        provenance.hidden = false;
        provenance.dataset.mode = status.mode || "";
        provenance.innerHTML = `<strong>${escapeHtml(status.label || "证据状态")}</strong><span>${escapeHtml(status.reason || "")}</span><span>${escapeHtml(facts.join(" · "))}</span>`;
    } else if (provenance) {
        provenance.hidden = true;
        provenance.innerHTML = "";
        provenance.removeAttribute("data-mode");
    }
    if (tags) tags.innerHTML = (state.riskTypes || []).map((item) => `<span>${escapeHtml(item)}</span>`).join("");
}

function updateEvidencePanel(result, threadId = currentLegalThreadId) {
    const thread = legalThreads.find((item) => item.id === threadId);
    if (!thread) return;
    thread.evidenceState = {
        missing: result.missing_evidence || [],
        firstEvidence: result.evidence_chain?.[0] || null,
        confidenceScore: result.confidence_score,
        riskTypes: result.risk_types || [],
        retrievalStatus: resolveRetrievalStatus(result),
    };
    saveLegalThreads();
    if (thread.id === currentLegalThreadId) renderEvidenceState(thread.evidenceState);
}

function resolveRetrievalStatus(result = {}) {
    const diagnostics = result.client_diagnostics || {};
    if (result.retrieval_status?.mode) {
        return {
            ...result.retrieval_status,
            backend_url: diagnostics.backend_url || result.retrieval_status.backend_url,
            collection_name: diagnostics.collection_name || result.retrieval_status.collection_name,
        };
    }
    const filters = result.filters || {};
    const evidenceCount = Array.isArray(result.evidence_chain) ? result.evidence_chain.length : 0;
    const fallback = String(filters.fallback || "");
    const base = {
        evidence_count: evidenceCount,
        material_count: Array.isArray(result.material_sources) ? result.material_sources.length : 0,
        retrieval_confidence: result.retrieval_confidence,
        backend_url: diagnostics.backend_url,
        collection_name: diagnostics.collection_name,
    };
    if (filters.answer_status === "general_chat") {
        return { ...base, mode: "general_chat", label: "通用对话（未执行 RAG 检索）", reason: "本次回答没有使用系统证据；风险决策请补充事实、材料或明确风险问题。" };
    }
    if (fallback) {
        return { ...base, mode: "local_fallback", label: "本地法规兜底（RAG 服务异常）", reason: "本次回答来自受控本地法规文本，需人工复核。" };
    }
    if (evidenceCount) {
        return { ...base, mode: "rag", label: "RAG 检索与证据校验已完成", reason: "该服务尚未返回完整检索诊断；已按实际返回证据展示。" };
    }
    if (filters.answer_status === "insufficient_direct_evidence") {
        return { ...base, mode: "rag_no_usable_evidence", label: "RAG 已检索，但没有可用于决策的直接证据", reason: "系统未将不足或无关材料伪装成结论。" };
    }
    return null;
}

function attachAskClientDiagnostics(result, backendUrl = backendState.baseUrl) {
    if (!result || typeof result !== "object") return result;
    return {
        ...result,
        client_diagnostics: {
            ...(result.client_diagnostics || {}),
            backend_url: normalizeBaseUrl(backendUrl),
            collection_name: LEGAL_COLLECTION_NAME,
        },
    };
}

function startNewChat() {
    const thread = createLegalThread();
    legalThreads.unshift(thread);
    currentLegalThreadId = thread.id;
    saveLegalThreads();
    renderCurrentThread();
    getChatInput()?.focus();
}

function selectLegalThread(threadId) {
    currentLegalThreadId = threadId;
    renderCurrentThread();
    getChatInput()?.focus();
}

function deleteLegalThread(threadId) {
    legalThreads = legalThreads.filter((thread) => thread.id !== threadId);
    if (!legalThreads.length) legalThreads.push(createLegalThread());
    if (currentLegalThreadId === threadId) currentLegalThreadId = legalThreads[0].id;
    saveLegalThreads();
    renderCurrentThread();
}

async function streamLegalQuestion(question, requestThreadId, pendingId) {
    let streamedAnswer = "";
    let finalResult = null;
    const backendUrl = await fetchBackendStream("/ask/stream", {
        method: "POST",
        body: JSON.stringify({ question, k: 5, collection_name: LEGAL_COLLECTION_NAME, thread_id: requestThreadId, document_task_ids: readyChatAttachmentIds() }),
    }, {
        status: (payload) => {
            replaceThreadMessage(requestThreadId, pendingId, {
                id: pendingId,
                role: "assistant",
                status: "streaming",
                content: streamedAnswer,
                stage: payload.label || payload.stage || "\u5206\u6790\u4e2d",
                createdAt: new Date().toISOString(),
            });
        },
        answer_delta: (payload) => {
            streamedAnswer += payload.text || "";
            replaceThreadMessage(requestThreadId, pendingId, {
                id: pendingId,
                role: "assistant",
                status: "streaming",
                content: streamedAnswer,
                stage: "\u8f93\u51fa\u5206\u6790\u7ed3\u679c",
                createdAt: new Date().toISOString(),
            });
        },
        final: (payload) => {
            finalResult = payload.result;
        },
        error: (payload) => {
            throw new Error(payload.message || payload.code || "stream error");
        },
    });
    if (!finalResult) throw new Error("stream ended without final result");
    finalResult = attachAskClientDiagnostics(finalResult, backendUrl);
    replaceThreadMessage(requestThreadId, pendingId, {
        id: pendingId,
        role: "assistant",
        status: "done",
        result: finalResult,
        createdAt: new Date().toISOString(),
    });
    updateEvidencePanel(finalResult, requestThreadId);
    return finalResult;
}

async function sendLegalQuestionLegacy() {
    const input = getChatInput();
    if (!input) return;
    const question = input.value.trim();
    if (!question) return;
    input.value = "";
    resizeChatInput(input);
    const requestThreadId = currentLegalThreadId;
    appendChatMessage({ id: createLegalThreadId(), role: "user", content: question, createdAt: new Date().toISOString() });
    const pendingId = createLegalThreadId();
    appendChatMessage({ id: pendingId, role: "assistant", status: "thinking", createdAt: new Date().toISOString() });
    try {
        const result = attachAskClientDiagnostics(await fetchBackendJson("/ask", {
            method: "POST",
            body: JSON.stringify({ question, k: 5, collection_name: LEGAL_COLLECTION_NAME, thread_id: requestThreadId, document_task_ids: readyChatAttachmentIds() }),
        }));
        replaceThreadMessage(requestThreadId, pendingId, { id: pendingId, role: "assistant", status: "done", result, createdAt: new Date().toISOString() });
        updateEvidencePanel(result, requestThreadId);
    } catch (error) {
        replaceThreadMessage(requestThreadId, pendingId, {
            id: pendingId,
            role: "assistant",
            status: "error",
            content: "请稍后重试，或检查后端分析服务是否已启动。",
            createdAt: new Date().toISOString(),
        });
        console.info(error);
    }
}

async function sendLegalQuestion() {
    const input = getChatInput();
    if (!input) return;
    const question = input.value.trim();
    if (!question) return;
    input.value = "";
    resizeChatInput(input);
    const requestThreadId = currentLegalThreadId;
    appendChatMessage({ id: createLegalThreadId(), role: "user", content: question, createdAt: new Date().toISOString() });
    const pendingId = createLegalThreadId();
    appendChatMessage({ id: pendingId, role: "assistant", status: "thinking", createdAt: new Date().toISOString() });
    try {
        await streamLegalQuestion(question, requestThreadId, pendingId);
    } catch (error) {
        try {
            const result = attachAskClientDiagnostics(await fetchBackendJson("/ask", {
                method: "POST",
                body: JSON.stringify({ question, k: 5, collection_name: LEGAL_COLLECTION_NAME, thread_id: requestThreadId, document_task_ids: readyChatAttachmentIds() }),
            }));
            replaceThreadMessage(requestThreadId, pendingId, {
                id: pendingId,
                role: "assistant",
                status: "done",
                result,
                createdAt: new Date().toISOString(),
            });
            updateEvidencePanel(result, requestThreadId);
        } catch (fallbackError) {
            replaceThreadMessage(requestThreadId, pendingId, {
                id: pendingId,
                role: "assistant",
                status: "error",
                content: "\u8bf7\u7a0d\u540e\u91cd\u8bd5\uff0c\u6216\u68c0\u67e5\u540e\u7aef\u5206\u6790\u670d\u52a1\u662f\u5426\u5df2\u542f\u52a8\u3002",
                createdAt: new Date().toISOString(),
            });
            console.info(error, fallbackError);
        }
    }
}

function applyExternalRiskDashboardData(data, meta = {}) {
    const panel = document.getElementById("external-risk-panel");
    if (!panel || !data) return;
    backendState.externalRisk = data;
    panel.classList.remove("loading", "error");
    panel.dataset.dataMode = data.summary?.data_mode || meta.data_source || "unavailable_live_provider";

    const headline = document.getElementById("external-risk-headline");
    if (headline) headline.textContent = data.summary?.headline || "外部市场与供应链风险监控";

    const mode = document.getElementById("external-risk-mode");
    if (mode) {
        const label = data.debug_scenario ? "调试场景" : externalRiskModeLabel(data.summary?.provider_mode, data.summary?.data_mode);
        mode.textContent = label;
        mode.className = `data-mode-badge ${data.debug_scenario ? "fixture" : normalizeDataModeClass(data.summary?.provider_mode, data.summary?.data_mode)}`;
        mode.title = `数据源：${externalDataSourceLabel(meta.data_source || data.summary?.data_mode || "unavailable_live_provider")}`;
    }

    renderExternalRiskSummary(data.summary || {});
    renderExternalRiskSignals(data.signals || []);
    renderExternalRiskObservations(data.market_observations || []);
    renderExternalRiskChainAlerts(data.chain_alerts || []);
    renderExternalRiskTasks(data.legal_query_tasks || []);
    renderExternalRiskProviders(data.provider_statuses || [], data.intelligence_status || null);
    applyExternalRiskToMarketCards(data.signals || []);
    setSupplyExternalSignals(data.signals || []);
    renderLifecycle();
}

function externalRiskModeLabel(providerMode, dataMode) {
    if (providerMode === "hybrid" || dataMode === "hybrid_provider") return "混合实时";
    if (providerMode === "live" || dataMode === "live_provider") return "实时";
    if (dataMode === "unavailable_live_provider") return "实时行情暂不可用";
    if (providerMode === "disabled") return "实时行情已关闭";
    return "实时行情暂不可用";
}

function externalDataSourceLabel(value) {
    return {
        live_provider: "实时行情",
        unavailable_live_provider: "实时行情暂不可用",
        fixture_sample: "场景数据",
        developer_debug: "开发调试",
        external_risk: "外部风险服务",
        backend: "后端服务",
    }[String(value || "")] || String(value || "外部风险服务");
}

function externalDataAccessLabel(value) {
    return {
        live_called: "已请求实时数据",
        cache_read: "已读取缓存",
        fixture_only: "场景数据",
        scenario_record: "比赛演练记录",
        not_called: "未请求",
        unavailable: "暂不可用",
    }[String(value || "")] || String(value || "未标注");
}

function normalizeDataModeClass(providerMode, dataMode) {
    if (dataMode === "unavailable_live_provider") return "disabled";
    if (providerMode === "hybrid" || providerMode === "live") return "live";
    if (providerMode === "disabled") return "disabled";
    return "fixture";
}

const RISK_COEFFICIENT_COMPONENT_LABELS = {
    severity: "\u4fe1\u53f7\u4e25\u91cd\u5ea6",
    materiality: "\u5f02\u5e38\u5e45\u5ea6",
    threshold_pressure: "\u9608\u503c\u538b\u529b",
    chain_transmission: "\u94fe\u6761\u4f20\u5bfc",
    legal_exposure: "\u6cd5\u5f8b\u66dd\u9732",
    persistence: "\u6301\u7eed\u6027",
};

function riskCoefficientFormulaTooltip(formula) {
    return `
        <button class="risk-formula-info" type="button" aria-label="\u67e5\u770b\u98ce\u9669\u7cfb\u6570\u8ba1\u7b97\u516c\u5f0f">
            <span aria-hidden="true">i</span>
            <span class="risk-formula-tooltip" role="tooltip">
                <span class="risk-formula-title">\u98ce\u9669\u7cfb\u6570\u516c\u5f0f</span>
                <math class="risk-math" display="block" aria-label="R equals 100 times the weighted risk factors" data-latex="${escapeHtml(formula)}">
                    <mrow>
                        <mi>R</mi><mo>=</mo><mn>100</mn><mo>(</mo>
                        <mn>0.22</mn><mi>S</mi><mo>+</mo><mn>0.20</mn><mi>M</mi><mo>+</mo>
                        <mn>0.16</mn><mi>T</mi><mo>+</mo><mn>0.16</mn><mi>C</mi><mo>+</mo>
                        <mn>0.14</mn><mi>L</mi><mo>+</mo><mn>0.12</mn><mi>P</mi><mo>)</mo>
                    </mrow>
                </math>
                <math class="risk-math risk-math-secondary" display="block" aria-label="C is the combined chain transmission exposure">
                    <mrow>
                        <mi>C</mi><mo>=</mo><mn>1</mn><mo>-</mo><munderover><mo>&prod;</mo><mi>j</mi><mo></mo></munderover>
                        <mo>(</mo><mn>1</mn><mo>-</mo><msub><mi>a</mi><mi>j</mi></msub><mo>)</mo>
                    </mrow>
                </math>
                <math class="risk-math risk-math-secondary" display="block" aria-label="S is the combined adverse signal exposure">
                    <mrow>
                        <mi>S</mi><mo>=</mo><mn>1</mn><mo>-</mo><munderover><mo>&prod;</mo><mi>i</mi><mo></mo></munderover>
                        <mo>(</mo><mn>1</mn><mo>-</mo><msub><mi>c</mi><mi>i</mi></msub><msub><mi>r</mi><mi>i</mi></msub><msub><mi>s</mi><mi>i</mi></msub><mo>)</mo>
                    </mrow>
                </math>
                <span class="risk-formula-note">S \u4e3a\u7f6e\u4fe1\u5ea6\u3001\u76f8\u5173\u5ea6\u52a0\u6743\u540e\u7684\u8d1f\u9762\u4fe1\u53f7\u66dd\u9732\uff1bM \u4e3a\u5df2\u89c2\u6d4b\u7684\u5f02\u5e38\u5e45\u5ea6\uff0cT \u4e3a\u8d85\u9608\u503c\u538b\u529b\uff0cC \u4e3a\u5f53\u524d\u753b\u5e03\u4e2d\u5df2\u786e\u8ba4\u7684\u94fe\u6761\u4f20\u5bfc\uff08\u5176\u8bc1\u636e\u7b49\u7ea7\u4e0e\u5173\u7cfb\u8fb9\u754c\u4ee5\u753b\u5e03\u6807\u6ce8\u4e3a\u51c6\uff09\uff0cL \u4e3a\u76f4\u63a5\u6cd5\u5f8b\u66dd\u9732\uff0cP \u4e3a\u6301\u7eed\u6027\u3002\u6cd5\u5f8b\u68c0\u7d22\u4efb\u52a1\u6570\u4e0d\u53c2\u4e0e\u98ce\u9669\u52a0\u5206\u3002</span>
            </span>
        </button>
    `;
}

function renderExternalRiskSummary(summary) {
    const container = document.getElementById("external-risk-summary");
    if (!container) return;
    const riskCoefficient = Number(summary.risk_coefficient ?? 0);
    const components = summary.risk_coefficient_components || {};
    const formula = summary.risk_coefficient_formula || "R=100(0.22S+0.20M+0.16T+0.16C+0.14L+0.12P)";
    const quality = Math.round(Math.max(0, Math.min(Number(summary.risk_coefficient_quality ?? 0), 1)) * 100);
    const items = [
        ["\u4fe1\u53f7", summary.signal_count ?? 0],
        ["\u9ad8\u98ce\u9669", summary.high_or_above_count ?? 0],
        ["\u5b9e\u65f6", summary.live_signal_count ?? 0],
        ["\u6cd5\u5f8b\u4efb\u52a1", summary.legal_task_count ?? 0],
    ];
    const dataQuality = backendState.externalRisk?.data_quality || {};
    const relationshipCounts = dataQuality.relationship_evidence_counts || {};
    const relationshipSummary = Object.entries(relationshipCounts)
        .filter(([, count]) => Number(count) > 0)
        .map(([grade, count]) => `${workflowEvidenceGradeLabel(grade)} ${count}`)
        .join(" · ") || "无已保存关系";
    const componentRows = Object.entries(components).map(([key, value]) => `
        <div class="risk-component-row">
            <span>${escapeHtml(RISK_COEFFICIENT_COMPONENT_LABELS[key] || key)}</span>
            <div><i style="width:${Math.max(3, Math.min(Number(value) || 0, 24) / 24 * 100).toFixed(1)}%"></i></div>
            <strong>${Number(value).toFixed(1)}</strong>
        </div>
    `).join("");
    const lowScoreExplanation = Number(summary.high_or_above_count || 0) > 0 && summary.risk_coefficient_level === "low"
        ? '<p class="external-risk-score-explanation">高等级信号尚未形成已确认的企业传导关系，因此综合风险仍为低；请先核验关联范围。</p>'
        : "";
    container.innerHTML = `${items.map(([label, value]) => `
        <div class="external-risk-stat">
            <span>${escapeHtml(label)}</span>
            <strong>${escapeHtml(value)}</strong>
        </div>
    `).join("")}
        <div class="external-risk-stat risk-coefficient-stat">
            <span>\u98ce\u9669\u7cfb\u6570 ${riskCoefficientFormulaTooltip(formula)}</span>
            <strong>${riskCoefficient.toFixed(1)} \u00b7 ${riskLevelLabel(summary.risk_coefficient_level)}</strong>
        </div>
        <section class="risk-coefficient-detail" aria-label="\u98ce\u9669\u8be6\u60c5">
            <div class="risk-coefficient-detail-head">
                <span>\u98ce\u9669\u8be6\u60c5</span>
                <strong>\u8bc1\u636e\u8d28\u91cf ${quality}%</strong>
            </div>
            <div class="risk-component-list">${componentRows || `<span class="empty-state">\u6682\u65e0\u53ef\u89e3\u91ca\u7684\u98ce\u9669\u56e0\u5b50\u3002</span>`}</div>
            ${lowScoreExplanation}
        </section>
        <section class="risk-coefficient-detail external-data-boundary" aria-label="\u6570\u636e\u8fb9\u754c">
            <div class="risk-coefficient-detail-head"><span>\u6570\u636e\u4e0e\u5173\u7cfb\u8fb9\u754c</span><strong>\u4f9b\u5e94\u94fe\uff1a${escapeHtml(dataQuality.supply_chain_data_access === "scenario_record" ? "\u6bd4\u8d5b\u6f14\u7ec3\u8bb0\u5f55" : dataQuality.supply_chain_data_access || "\u672a\u6807\u6ce8")}</strong></div>
            <div class="external-data-boundary-grid"><span>\u5e02\u573a\u8bf7\u6c42\uff1a${escapeHtml(externalDataAccessLabel(dataQuality.market_data_access))}</span><span>\u5546\u54c1\u8bf7\u6c42\uff1a${escapeHtml(externalDataAccessLabel(dataQuality.commodity_data_access))}</span><span>RSS/\u653f\u7b56\uff1a${escapeHtml(externalDataAccessLabel(dataQuality.news_policy_data_access))}</span><span>\u753b\u5e03\u8bc1\u636e\uff1a${escapeHtml(relationshipSummary)}</span></div>
            <p>${escapeHtml(dataQuality.relationship_boundary || "\u5e02\u573a\u4e0eRSS\u53ef\u4e3a\u4e8b\u5b9e\u7ebf\u7d22\uff1b\u4f9b\u5e94\u5546\u4e0e\u753b\u5e03\u5173\u7cfb\u987b\u53e6\u884c\u6838\u9a8c\u3002")}</p>
        </section>`;
}

function riskLevelLabel(level) {
    if (level === "critical") return "极高";
    if (level === "high") return "高";
    if (level === "medium") return "中";
    return "低";
}

function renderExternalRiskSignals(signals) {
    const container = document.getElementById("external-risk-signals");
    const count = document.getElementById("external-risk-signal-count");
    if (count) count.textContent = `${signals.length}`;
    if (!container) return;
    if (!signals.length) {
        container.innerHTML = `<div class="empty-state">暂未收到外部风险信号。</div>`;
        return;
    }
    container.innerHTML = signals.slice(0, 8).map((signal) => {
        const risk = normalizeRiskLevel(signal.severity);
        const value = formatSignalValue(signal.value);
        const domains = (signal.affected_domains || []).slice(0, 3);
        const metadata = signal.metadata || {};
        const displayTitle = externalSignalDisplayTitle(signal);
        const signalTypeLabel = externalSignalTypeLabel(signal.signal_type);
        const metricLabel = externalSignalMetricLabel(signal);
        const csrcInstruments = Array.isArray(metadata.csrc_instruments) ? metadata.csrc_instruments : [];
        const csrcContext = metadata.csrc_instrument_status === "not_disclosed"
            ? "监管环境提示 · 涉及证券：官方公告未披露"
            : csrcInstruments.length ? `涉及证券：${csrcInstruments.join("、")}` : "";
        const sourceName = metadata.feed_name || "外部来源";
        const relevance = Number(metadata.risk_relevance);
        const relevanceText = Number.isFinite(relevance) && relevance < 0.999
            ? `风险相关度 ${(relevance * 100).toFixed(0)}%`
            : "风险相关度 100%";
        const sourceUrl = /^https?:\/\//i.test(String(signal.source || "")) ? String(signal.source) : "";
        const sourceLink = sourceUrl
            ? `<a class="external-signal-source" href="${escapeHtml(sourceUrl)}" target="_blank" rel="noopener noreferrer">原文</a>`
            : "";
        const staleNotice = metadata.source_stale
            ? `<span class="external-signal-stale">来源暂不可达，使用最近成功快照</span>`
            : "";
        const relationStatus = metadata.entity_match_status
            || (signal.signal_type === "commodity_futures" ? "产业链关联待人工核验" : "企业关联待人工核验");
        const commodityDetails = signal.signal_type === "commodity_futures"
            ? renderCommoditySignalDetails(signal, metadata)
            : "";
        return `
            <article class="external-signal-card">
                <div class="external-signal-top">
                    <span class="risk-dot ${risk}"></span>
                    <div>
                        <h3>${escapeHtml(displayTitle)}</h3>
                        <div class="external-signal-meta">${escapeHtml(sourceName)} / ${escapeHtml(signalTypeLabel)} / ${escapeHtml(metricLabel)} ${sourceLink}</div>
                    </div>
                    <span class="risk-text ${risk}">${riskLabels[risk]}</span>
                </div>
                ${renderExternalSignalEvidence(signal.evidence)}
                ${csrcContext ? `<div class="external-signal-identifier">${escapeHtml(csrcContext)}</div>` : ""}
                ${commodityDetails}
                <div class="external-signal-foot">
                    <span>${escapeHtml(value)}</span>
                    <span>${escapeHtml(signal.as_of || "-")}</span>
                    <span>${escapeHtml(relevanceText)}</span>
                </div>
                <div class="external-signal-relation">${escapeHtml(relationStatus)} · 风险相关度仅表示规则匹配，不等同于已确认业务影响。</div>
                ${staleNotice}
                ${domains.length ? `<div class="pill-list compact">${domains.map((item) => `<span class="pill">${escapeHtml(externalSignalDomainLabel(item))}</span>`).join("")}</div>` : ""}
            </article>
        `;
    }).join("");
}

function renderExternalRiskObservations(observations) {
    const container = document.getElementById("external-risk-observations");
    const count = document.getElementById("external-risk-observation-count");
    if (count) count.textContent = `${observations.length}`;
    if (!container) return;
    if (!observations.length) {
        container.innerHTML = `<div class="empty-state">暂无跨行业产业链观察。</div>`;
        return;
    }
    container.innerHTML = observations.slice(0, 8).map((signal) => {
        const risk = normalizeRiskLevel(signal.severity);
        const metadata = signal.metadata || {};
        const sourceName = metadata.feed_name || signal.source || "外部来源";
        const sourceUrl = /^https?:\/\//i.test(String(signal.source || "")) ? String(signal.source) : "";
        const sourceLink = sourceUrl
            ? `<a class="external-signal-source" href="${escapeHtml(sourceUrl)}" target="_blank" rel="noopener noreferrer">原文</a>`
            : "";
        const tags = Array.isArray(metadata.industry_tags)
            ? metadata.industry_tags.filter((tag) => tag && tag !== "supply_chain_market_observation").slice(0, 4).map(externalSignalDomainLabel)
            : [];
        return `
            <article class="external-observation-card">
                <div class="external-signal-top">
                    <span class="risk-dot ${risk}"></span>
                    <div>
                        <h3>${escapeHtml(externalSignalDisplayTitle(signal))}</h3>
                        <div class="external-signal-meta">${escapeHtml(sourceName)} · ${escapeHtml(signal.as_of || "-")} ${sourceLink}</div>
                    </div>
                    <span class="observation-context-label">市场观察</span>
                </div>
                ${renderExternalSignalEvidence(signal.evidence)}
                <div class="external-observation-foot">
                    <span>${escapeHtml(signal.direction === "negative" ? "偏不利" : signal.direction === "positive" ? "偏有利" : "中性")}</span>
                    <span>不计入企业风险系数</span>
                </div>
                ${tags.length ? `<div class="pill-list compact">${tags.map((tag) => `<span class="pill">${escapeHtml(tag)}</span>`).join("")}</div>` : ""}
            </article>`;
    }).join("");
}

function renderExternalSignalEvidence(evidence) {
    const text = String(evidence || "").trim();
    if (!text) return "";
    const previewLimit = 440;
    if (text.length <= previewLimit) {
        return `<p class="external-signal-evidence">${escapeHtml(text)}</p>`;
    }
    return `
        <p class="external-signal-evidence">${escapeHtml(text.slice(0, previewLimit))}...</p>
        <details class="external-signal-evidence-more">
            <summary>展开全文</summary>
            <div>${escapeHtml(text)}</div>
        </details>`;
}

function renderCommoditySignalDetails(signal, metadata) {
    const contractValues = [
        ...(Array.isArray(metadata.contracts) ? metadata.contracts : []),
        metadata.contract,
        metadata.instrument_code,
    ].filter((value, index, values) => value != null && String(value).trim() && values.indexOf(value) === index);
    const latest = Number(metadata.latest_price ?? metadata.current ?? metadata.quote);
    const previous = Number(metadata.previous_close ?? metadata.previous);
    const observedPeriods = Number(metadata.observation_periods);
    const metricMatch = String(signal.metric || "").match(/(\d+)d(?:_|$)/i);
    const periods = Number.isFinite(observedPeriods) && observedPeriods > 0
        ? observedPeriods
        : metricMatch ? Number(metricMatch[1]) : 1;
    const quoteText = Number.isFinite(latest)
        ? `报价 ${formatPrice(latest)}${Number.isFinite(previous) ? ` / 昨结 ${formatPrice(previous)}` : ""}`
        : "报价未随该信号提供";
    const contractText = contractValues.length ? `合约 ${contractValues.join(" / ")}` : "合约未标注";
    const linkedNodes = Array.isArray(metadata.linked_node_ids) ? metadata.linked_node_ids.filter(Boolean) : [];
    const relation = String(metadata.chain_link_relation || "").trim();
    const linkageText = metadata.chain_linked
        ? `产业链关联 ${linkedNodes.length ? linkedNodes.join(" / ") : "场景配置"}${relation ? ` · ${relation}` : ""}`
        : "产业链关联待核验";
    const asOf = String(signal.as_of || "-").replace("T", " ").replace(/\+\d{2}:\d{2}$/, "");
    return `
        <div class="external-signal-commodity">
            <span>${escapeHtml(contractText)}</span>
            <span>${escapeHtml(linkageText)}</span>
            <span>${escapeHtml(quoteText)}</span>
            <span>${escapeHtml(`观察期 ${periods} 个交易日`)}</span>
            <span>${escapeHtml(`截止 ${asOf}`)}</span>
        </div>`;
}

function renderExternalRiskChainAlerts(alerts) {
    const container = document.getElementById("external-risk-chain-alerts");
    const count = document.getElementById("external-risk-chain-count");
    if (count) count.textContent = `${alerts.length}`;
    if (!container) return;
    if (!alerts.length) {
        container.innerHTML = `<div class="empty-state">暂无可验证的产业链传导提示。</div>`;
        return;
    }
    container.innerHTML = alerts.slice(0, 4).map((alert) => {
        const risk = normalizeRiskLevel(alert.severity);
        const symbols = (alert.affected_symbols || []).slice(0, 4).map(externalInstrumentDisplayLabel);
        const score = Math.round(Math.max(0, Math.min(Number(alert.transmission_score) || 0, 1)) * 100);
        const association = alert.association_type === "industry" ? "产业关联"
            : alert.association_type === "mixed" ? "链路 + 产业关联"
                : "画布链路";
        const evidenceGrade = workflowEvidenceGradeLabel(alert.relationship_evidence_grade || "unverified");
        const boundary = String(alert.relationship_boundary || "").trim();
        const tags = Array.isArray(alert.association_tags) ? alert.association_tags.slice(0, 3).map(externalSignalDomainLabel) : [];
        const external = Array.isArray(alert.external_instruments) ? alert.external_instruments.slice(0, 4).map(externalInstrumentDisplayLabel) : [];
        return `
            <article class="external-chain-alert">
                <span class="risk-dot ${risk}"></span>
                <div>
                    <strong>${escapeHtml(localizeExternalInstrumentText(alert.summary || "产业链传导提示"))}</strong>
                    <div class="external-chain-alert-meta">
                        <span>传导强度 ${score}%</span>
                        <span>${escapeHtml(association)}</span>
                        <span>${escapeHtml(evidenceGrade)}</span>
                        ${symbols.length ? `<span>${escapeHtml(symbols.join(" · "))}</span>` : ""}
                        ${tags.length ? `<span>${escapeHtml(tags.join(" / "))}</span>` : ""}
                        ${external.length ? `<span>画布外：${escapeHtml(external.join("、"))}</span>` : ""}
                    </div>
                    ${boundary ? `<p class="external-chain-boundary">${escapeHtml(boundary)}</p>` : ""}
                </div>
            </article>
        `;
    }).join("");
}

function renderExternalRiskTasks(tasks) {
    const container = document.getElementById("external-risk-tasks");
    const count = document.getElementById("external-risk-task-count");
    if (count) count.textContent = `${tasks.length}`;
    if (!container) return;
    if (!tasks.length) {
        container.innerHTML = `<div class="empty-state">暂未生成法律检索任务。</div>`;
        return;
    }
    container.innerHTML = tasks.slice(0, 5).map((task) => {
        const risk = normalizeRiskLevel(task.severity);
        const metadata = task.metadata || {};
        const isLiveSignal = metadata.origin === "live_external_signal";
        const feedName = metadata.feed_name || metadata.signal_source || "";
        const relevance = Number(metadata.risk_relevance);
        const relevanceLabel = Number.isFinite(relevance) ? `相关度 ${Math.round(relevance * 100)}%` : "";
        const staleLabel = metadata.source_stale ? "使用最近成功快照" : "";
        const taskMeta = [
            isLiveSignal ? "实时信号" : "预设任务",
            feedName,
            relevanceLabel,
            staleLabel,
        ].filter(Boolean);
        return `
            <div class="external-task-item">
                <span class="risk-dot ${risk}"></span>
                <div>
                    <strong>${escapeHtml(task.query || task.task_id)}</strong>
                    ${taskMeta.length ? `<div class="external-task-meta${isLiveSignal ? " live" : ""}">${taskMeta.map((item) => `<span>${escapeHtml(item)}</span>`).join("")}</div>` : ""}
                    <p>${escapeHtml(task.fact_background || "")}</p>
                </div>
            </div>
        `;
    }).join("");
}

function renderExternalRiskProviders(providers, intelligenceStatus = null) {
    const container = document.getElementById("external-risk-providers");
    const count = document.getElementById("external-risk-provider-count");
    const feeds = Array.isArray(intelligenceStatus?.feeds) ? intelligenceStatus.feeds : [];
    if (count) count.textContent = feeds.length ? `${providers.length} 组 · ${feeds.length} 源` : `${providers.length}`;
    if (!container) return;
    const successfulFeeds = feeds.filter((feed) => feed.status === "success").length;
    const latestCheckedAt = feeds
        .map((feed) => feed.last_checked_at)
        .filter(Boolean)
        .sort()
        .slice(-1)[0] || intelligenceStatus?.cache_updated_at || "";
    const cacheFresh = intelligenceStatus?.cache_fresh === true;
    const feedStatusLabel = feeds.length
        ? `${successfulFeeds}/${feeds.length} 源成功 · 全源匹配 ${Number(intelligenceStatus?.cached_signal_count || 0)} 条`
        : "尚未读取消息源";
    const freshnessLabel = cacheFresh ? "数据有效" : latestCheckedAt ? "等待下一次刷新" : "未抓取";
    const summary = `
        <div class="external-provider-summary">
            <div>
                <strong>RSS / 政策消息</strong>
                <span>${escapeHtml(feedStatusLabel)}</span>
            </div>
            <div>
                <span>最近抓取</span>
                <strong>${escapeHtml(formatExternalTimestamp(latestCheckedAt))}</strong>
            </div>
            <div>
                <span>更新状态</span>
                <strong class="external-provider-freshness ${cacheFresh ? "fresh" : "stale"}">${escapeHtml(freshnessLabel)}</strong>
            </div>
            <div>
                <span>轮询周期</span>
                <strong>${escapeHtml(`${Number(intelligenceStatus?.poll_seconds || 0)} 秒`)}</strong>
            </div>
        </div>`;
    const feedItems = feeds.length ? `
        <div class="external-feed-health-list" aria-label="消息源逐源状态">
            ${feeds.map((feed) => {
                const status = feed.status || "not_called";
                const statusClass = status === "success" ? "low" : status === "empty" || status === "not_called" ? "med" : "high";
                const statusText = status === "success" ? "成功" : status === "empty" ? "空结果" : status === "failed" ? "失败" : "未调用";
                const detail = [
                    `${Number(feed.signal_count || 0)} 条匹配`,
                    feed.last_checked_at ? `检查 ${formatExternalTimestamp(feed.last_checked_at)}` : "未检查",
                ].join(" · ");
                return `
                    <div class="external-feed-health-item">
                        <span class="risk-dot ${statusClass}"></span>
                        <div>
                            <strong>${escapeHtml(feed.source_name || feed.feed_id)}</strong>
                            <span>${escapeHtml(statusText)} · ${escapeHtml(detail)}</span>
                            ${feed.error ? `<p>${escapeHtml(feed.error)}</p>` : ""}
                        </div>
                    </div>`;
            }).join("")}
        </div>` : "";
    container.innerHTML = summary + feedItems + providers.map((provider) => {
        const risk = provider.status === "available" || provider.status === "fixture_only" ? "low"
            : provider.status === "not_configured" ? "med"
            : "high";
        const providerLabel = {
            tencent_http_provider: "腾讯行情",
            akshare_market_provider: "AkShare 行情",
            akshare_commodity_futures_provider: "AkShare 商品期货",
            news_policy_rss_provider: "RSS / 政策消息",
            fixture_supply_chain_provider: "供应链场景",
            fixture_company_profile_provider: "企业画像场景",
        }[provider.provider_id] || provider.provider_id;
        const modeLabel = provider.mode === "live" ? "实时" : provider.mode === "fixture" ? "场景" : "关闭";
        const accessLabel = {
            live_called: "已请求",
            cache_read: "读缓存",
            fixture_only: "场景数据",
            not_called: "未请求",
        }[provider.runtime_access] || provider.runtime_access;
        return `
            <div class="external-provider-item">
                <span class="risk-dot ${risk}"></span>
                <div>
                    <strong>${escapeHtml(providerLabel)}</strong>
                    <span>${escapeHtml(externalSignalTypeLabel(provider.provider_type))} · ${escapeHtml(modeLabel)} · ${escapeHtml(accessLabel)}</span>
                    ${provider.message ? `<p class="external-provider-message">${escapeHtml(provider.message)}</p>` : ""}
                </div>
            </div>
        `;
    }).join("");
}

function applyExternalRiskToMarketCards(signals) {
    const cards = document.querySelectorAll(".market-card:not(.wide)");
    if (!signals.length) {
        cards.forEach((card) => {
            card.innerHTML = `
                <h3>\u5b9e\u65f6\u4fe1\u53f7</h3>
                <div class="market-number flat market-flat">--</div>
                <p>\u6b63\u5728\u7b49\u5f85\u53ef\u590d\u6838\u7684\u5b9e\u65f6\u5e02\u573a\u6570\u636e</p>
            `;
        });
        const tbody = document.querySelector(".data-table tbody");
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="5" class="market-empty-row">\u6682\u65e0\u53ef\u590d\u6838\u7684\u5b9e\u65f6\u5e02\u573a\u4e0e\u4ea7\u4e1a\u94fe\u4fe1\u53f7</td></tr>`;
        }
        return;
    }
    signals.slice(0, cards.length).forEach((signal, index) => {
        const card = cards[index];
        const risk = normalizeRiskLevel(signal.severity);
        const hasValue = typeof signal.value === "number";
        const trend = hasValue ? trendClassForValue(signal.value) : "flat";
        const marketTrend = hasValue ? marketTrendClassForValue(signal.value) : "market-flat";
        const summary = marketCardSignalSummary(signal);
        card.innerHTML = `
            <h3>${escapeHtml(externalSignalDisplayTitle(signal))}</h3>
            <div class="market-number ${hasValue ? trend : "flat"} ${marketTrend}">${formatSignalValue(signal.value) || riskLabels[risk]}</div>
            <p>${escapeHtml(summary)}</p>
        `;
    });

    const tbody = document.querySelector(".data-table tbody");
    if (!tbody) return;
    tbody.innerHTML = signals.map((signal) => {
        const risk = normalizeRiskLevel(signal.severity);
        const hasValue = typeof signal.value === "number";
        const trend = hasValue ? trendClassForValue(signal.value) : "flat";
        const marketTrend = hasValue ? marketTrendClassForValue(signal.value) : "market-flat";
        return `
            <tr>
                <td>${escapeHtml(externalSignalDisplayTitle(signal))}</td>
                <td>${hasValue ? `<span class="market-change ${trend} ${marketTrend}">${formatSignalValue(signal.value)}</span>` : escapeHtml(signal.direction || "-")}</td>
                <td>${escapeHtml((signal.affected_domains || []).map(externalSignalDomainLabel).join(" / "))}</td>
                <td><span class="risk-text ${risk}">${riskLabels[risk]}</span></td>
                <td>${escapeHtml(signal.evidence || "")}</td>
            </tr>
        `;
    }).join("");
}

function marketCardSignalSummary(signal) {
    const metadata = signal.metadata || {};
    const fixtureLabel = /^fixture\./i.test(String(signal.source || "")) ? " · 样例数据，非实时" : "";
    if (signal.signal_type !== "commodity_futures") {
        return `${String(signal.evidence || signal.source || "").trim()}${fixtureLabel}`;
    }
    const contracts = [
        ...(Array.isArray(metadata.contracts) ? metadata.contracts : []),
        metadata.contract,
        metadata.instrument_code,
    ].filter((value, index, values) => value != null && String(value).trim() && values.indexOf(value) === index);
    const latest = Number(metadata.latest_price ?? metadata.current ?? metadata.quote);
    const period = Number(metadata.observation_periods) || Number(String(signal.metric || "").match(/(\d+)d(?:_|$)/i)?.[1]) || 1;
    const quote = Number.isFinite(latest) ? `报价 ${formatPrice(latest)}` : "报价未随信号提供";
    const asOf = String(signal.as_of || "-").replace("T", " ").replace(/\+\d{2}:\d{2}$/, "");
    return `${contracts.length ? `合约 ${contracts.join("/")}` : "合约未标注"} · ${quote} · ${period} 个交易日 · 截止 ${asOf}${fixtureLabel}`;
}

function formatSignalValue(value) {
    if (value == null || value === "") return "";
    if (typeof value === "number") {
        if (Math.abs(value) < 1) return formatPercentSigned(value);
        return Number.isInteger(value) ? String(value) : value.toFixed(2);
    }
    return String(value);
}

function setupLegalChat() {
    const input = getChatInput();
    const button = document.querySelector(".chat-input .send-button");
    const newChatButton = document.getElementById("new-chat-button");
    const threadList = document.getElementById("legal-thread-list");
    if (!input || !button) return;
    button.addEventListener("click", sendLegalQuestion);
    newChatButton?.addEventListener("click", startNewChat);
    threadList?.addEventListener("click", (event) => {
        const deleteButton = event.target.closest("[data-delete-thread]");
        if (deleteButton) {
            event.stopPropagation();
            deleteLegalThread(deleteButton.dataset.deleteThread);
            return;
        }
        const threadButton = event.target.closest(".chat-thread[data-thread-id]");
        if (threadButton) selectLegalThread(threadButton.dataset.threadId);
    });
    threadList?.addEventListener("keydown", (event) => {
        if (event.key !== "Enter" && event.key !== " ") return;
        const deleteButton = event.target.closest("[data-delete-thread]");
        if (deleteButton) {
            event.preventDefault();
            deleteLegalThread(deleteButton.dataset.deleteThread);
        }
    });
    input.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            sendLegalQuestion();
        }
    });
    input.addEventListener("input", () => resizeChatInput(input));
    input.addEventListener("paste", handleChatImagePaste);
    renderCurrentThread();
}

function setupDocumentUpload() {
    const input = document.getElementById("chat-attachment-input");
    const dropTarget = document.querySelector("#view-legal .chat-panel");
    document.getElementById("chat-attachment-button")?.addEventListener("click", () => input?.click());
    input?.addEventListener("change", uploadChatAttachment);
    document.getElementById("chat-attachment-tray")?.addEventListener("click", handleChatAttachmentAction);
    // The list is rendered asynchronously, so delegate from its stable outer
    // container.  Without this listener its checkboxes visually toggled but
    // the selected material IDs were never passed to the RAG request.
    document.getElementById("legal-document-list")?.addEventListener("click", handleDocumentListAction);
    setupChatFileDropzone(dropTarget);
    refreshChatAttachments();
}

function setupChatFileDropzone(dropTarget) {
    if (!dropTarget) return;
    let dragDepth = 0;
    const hasFiles = (event) => Array.from(event.dataTransfer?.types || []).includes("Files");
    const clearDropState = () => {
        dragDepth = 0;
        dropTarget.classList.remove("dragging-files");
    };
    dropTarget.addEventListener("dragenter", (event) => {
        if (!hasFiles(event)) return;
        event.preventDefault();
        dragDepth += 1;
        dropTarget.classList.add("dragging-files");
    });
    dropTarget.addEventListener("dragover", (event) => {
        if (!hasFiles(event)) return;
        event.preventDefault();
        event.dataTransfer.dropEffect = "copy";
    });
    dropTarget.addEventListener("dragleave", (event) => {
        if (!hasFiles(event)) return;
        dragDepth -= 1;
        if (dragDepth <= 0) clearDropState();
    });
    dropTarget.addEventListener("drop", async (event) => {
        if (!hasFiles(event)) return;
        event.preventDefault();
        clearDropState();
        await uploadChatFiles(Array.from(event.dataTransfer.files || []));
    });
}

function renderSelectedUploadFile() {
    const input = document.getElementById("document-upload-input");
    const filename = document.getElementById("document-upload-filename");
    const submit = document.getElementById("document-upload-submit");
    const status = document.getElementById("document-upload-status");
    const file = input?.files?.[0];
    if (filename) filename.textContent = file ? `${file.name} · ${formatDocumentSize(file.size)}` : "尚未选择文件";
    if (status) status.textContent = "";
    if (submit) submit.disabled = !file;
}

async function fetchBackendForm(path, formData) {
    const request = async (baseUrl) => {
        const response = await fetch(`${baseUrl}${path}`, { method: "POST", body: formData, headers: { Accept: "application/json" } });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(payload?.error?.message || `${path} returned ${response.status}`);
        return payload;
    };
    return request(backendState.baseUrl);
}

async function submitContractUpload(event) {
    event.preventDefault();
    const input = document.getElementById("document-upload-input");
    const submit = document.getElementById("document-upload-submit");
    const status = document.getElementById("document-upload-status");
    const file = input?.files?.[0];
    if (!file) return;
    if (submit) submit.disabled = true;
    if (status) status.textContent = "正在上传材料";
    try {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("purpose", "contract_review");
        await fetchBackendForm("/documents/upload", formData);
        if (status) status.textContent = "已上传，MineU 正在解析";
        input.value = "";
        renderSelectedUploadFile();
        document.getElementById("document-upload-dialog")?.close();
        refreshDocumentWorkspace();
    } catch (error) {
        if (status) status.textContent = error.message || "上传失败";
    } finally {
        if (submit) submit.disabled = !(input?.files?.[0]);
    }
}

async function refreshDocumentWorkspace() {
    const parserStatus = document.getElementById("document-parser-status");
    try {
        const [capabilities, taskPayload] = await Promise.all([
            fetchBackendJson("/documents/capabilities", { timeoutMs: 5000 }),
            fetchBackendJson("/documents", { timeoutMs: 5000 }),
        ]);
        if (parserStatus) {
            parserStatus.textContent = capabilities.available
                ? "MineU 云端已就绪 · 勾选已解析材料后可用于本次分析"
                : "MineU 轻量云端暂不可用 · 请稍后重试";
            parserStatus.classList.toggle("warning", !capabilities.available);
        }
        const tasks = taskPayload.items || [];
        const signature = legalDocumentTaskSignature(tasks);
        const list = document.getElementById("legal-document-list");
        if (signature !== renderedLegalDocumentTaskSignature || pendingLegalEvidenceContext || !list?.children.length) {
            renderLegalDocuments(tasks);
            renderedLegalDocumentTaskSignature = signature;
        }
        scheduleDocumentRefresh(tasks);
    } catch (error) {
        if (parserStatus) {
            parserStatus.textContent = "材料解析服务暂不可用";
            parserStatus.classList.add("warning");
        }
        renderLegalDocuments([]);
    }
}

function legalDocumentTaskSignature(tasks = []) {
    return tasks.map((task) => [
        task.task_id,
        task.status,
        task.parser_message || "",
        task.error_code || "",
        task.error_message || "",
        task.size_bytes || 0,
    ].join(":" )).join("|");
}

function renderLegalSelectionStatus() {
    const selectionStatus = document.getElementById("legal-selection-status");
    if (!selectionStatus) return;
    const count = selectedLegalDocumentIds.size;
    selectionStatus.textContent = count
        ? `已选择 ${count} 份已解析材料；本次 RAG 将只使用这些材料（最多 3 份）。`
        : "尚未选择材料；可选择最多 3 份已解析材料用于本次 RAG 分析。";
    selectionStatus.classList.toggle("ready", count > 0);
    document.querySelectorAll('[data-document-select][data-document-ready="true"]').forEach((input) => {
        input.disabled = !input.checked && count >= 3;
    });
}

function scheduleDocumentRefresh(tasks) {
    if (documentRefreshTimer) window.clearTimeout(documentRefreshTimer);
    if (tasks.some((task) => task.status === "uploaded" || task.status === "processing")) {
        documentRefreshTimer = window.setTimeout(refreshDocumentWorkspace, 1500);
    }
}

function renderLegalDocuments(tasks) {
    const container = document.getElementById("legal-document-list");
    if (!container) return;
    tasks.forEach((task) => chatAttachmentTaskStates.set(task.task_id, task.status));
    const availableIds = new Set(tasks.filter((task) => task.status === "completed").map((task) => task.task_id));
    const context = pendingLegalEvidenceContext;
    const contextualDocumentIds = new Set((context?.evidenceRefs || []).filter((ref) => availableIds.has(ref)));
    if (contextualDocumentIds.size) {
        selectedLegalDocumentIds = new Set(contextualDocumentIds);
        saveSelectedLegalDocumentIds();
    }
    selectedLegalDocumentIds = new Set([...selectedLegalDocumentIds].filter((id) => availableIds.has(id)));
    saveSelectedLegalDocumentIds();
    renderLegalSelectionStatus();
    if (!tasks.length) {
        container.innerHTML = '<div class="empty-state">尚未上传材料</div>';
        return;
    }
    const contextNotice = context ? `<div class="legal-evidence-context"><strong>来自生命周期：${escapeHtml(context.stageLabel)}</strong><span>${contextualDocumentIds.size ? `已自动选中 ${contextualDocumentIds.size} 份关联解析材料。` : `关联编号 ${context.evidenceRefs.length} 项；其中暂无可直接用于法律工作台的解析材料。`}</span></div>` : "";
    pendingLegalEvidenceContext = null;
    container.innerHTML = contextNotice + tasks.map((task) => {
        const completed = task.status === "completed";
        const selected = selectedLegalDocumentIds.has(task.task_id);
        const selectionAtCapacity = !selected && selectedLegalDocumentIds.size >= 3;
        const status = documentStatusLabel(task);
        return `
            <article class="legal-document-item ${selected ? "selected" : ""}">
                <label class="legal-document-select" title="用于本次分析">
                    <input type="checkbox" data-document-select="${escapeHtml(task.task_id)}" data-document-ready="${completed ? "true" : "false"}" ${completed && selected ? "checked" : ""} ${completed && !selectionAtCapacity ? "" : "disabled"}>
                    <span></span>
                </label>
                <div class="legal-document-main">
                    <strong title="${escapeHtml(task.original_filename)}">${escapeHtml(task.original_filename)}</strong>
                    <span>${escapeHtml(status)} · ${formatDocumentSize(task.size_bytes)}</span>
                    ${task.error_message ? `<p>${escapeHtml(task.error_message)}</p>` : ""}
                </div>
                <div class="legal-document-actions">
                    ${completed ? '<button type="button" data-document-action="preview" title="查看解析文本" aria-label="查看解析文本">预览</button>' : ""}
                    ${completed ? '<button type="button" data-document-action="download" title="下载 Markdown" aria-label="下载 Markdown">下载</button>' : ""}
                    ${task.status === "failed" ? '<button type="button" data-document-action="retry" title="重新解析" aria-label="重新解析">重新解析</button>' : ""}
                    <button type="button" data-document-action="delete" title="删除材料" aria-label="删除材料">删除</button>
                </div>
            </article>
        `;
    }).join("");
}

function documentStatusLabel(task) {
    if (task.status === "completed") return "已解析，可用于审查";
    if (task.status === "processing" || task.status === "uploaded") return task.parser_message || "解析中";
    return task.error_code === "MINEU_UNAVAILABLE" ? "等待 MineU 配置" : "解析失败";
}

function formatDocumentSize(value) {
    const bytes = Number(value) || 0;
    if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

async function uploadChatAttachment() {
    const input = document.getElementById("chat-attachment-input");
    const files = Array.from(input?.files || []);
    if (!files.length) return;
    input.value = "";
    await uploadChatFiles(files);
}

async function handleChatImagePaste(event) {
    const imageItem = Array.from(event.clipboardData?.items || []).find((item) => item.type.startsWith("image/"));
    if (!imageItem) return;
    event.preventDefault();
    const image = imageItem.getAsFile();
    if (!image) return;
    const mimeType = String(image.type || "").toLowerCase();
    const extensions = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/gif": "gif",
        "image/webp": "webp",
        "image/bmp": "bmp",
        "image/jp2": "jp2",
    };
    const extension = extensions[mimeType];
    if (!extension) {
        chatAttachmentErrors = [{
            client_id: `paste-${Date.now()}`,
            original_filename: "粘贴图片",
            size_bytes: image.size,
            status: "failed",
            error_message: "暂不支持该图片格式，请使用 PNG、JPG、GIF、WebP、BMP 或 JP2。",
        }];
        renderChatAttachments([]);
        return;
    }
    const filename = `粘贴图片_${new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14)}.${extension}`;
    await uploadChatFiles([new File([image], filename, { type: mimeType })]);
}

async function uploadChatFiles(files) {
    const remaining = Math.max(0, 3 - selectedLegalDocumentIds.size);
    if (!remaining) {
        chatAttachmentErrors = [{
            client_id: `limit-${Date.now()}`,
            original_filename: "附件数量已达上限",
            size_bytes: 0,
            status: "failed",
            error_message: "单次分析最多选择 3 份材料，请先移除已有附件。",
        }];
        renderChatAttachments([]);
        return;
    }
    const accepted = files.slice(0, remaining);
    chatAttachmentErrors = files.length > accepted.length ? [{
        client_id: `limit-${Date.now()}`,
        original_filename: "部分材料未上传",
        size_bytes: 0,
        status: "failed",
        error_message: "单次分析最多选择 3 份材料。",
    }] : [];
    for (const file of accepted) {
        await uploadChatFile(file, { clearErrors: false });
    }
}

async function uploadChatFile(file, { clearErrors = true } = {}) {
    const button = document.getElementById("chat-attachment-button");
    if (button) button.disabled = true;
    if (clearErrors) chatAttachmentErrors = [];
    try {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("purpose", "contract_review");
        const payload = await fetchBackendForm("/documents/upload", formData);
        const taskId = payload?.data?.task_id;
        if (taskId) {
            selectedLegalDocumentIds.add(taskId);
            saveSelectedLegalDocumentIds();
        }
        await refreshChatAttachments();
    } catch (error) {
        chatAttachmentErrors.push({
            client_id: `${Date.now()}`,
            original_filename: file.name,
            size_bytes: file.size,
            status: "failed",
            error_message: error.message || "上传失败",
        });
        renderChatAttachments([]);
    } finally {
        if (button) button.disabled = false;
    }
}

async function refreshChatAttachments() {
    try {
        const payload = await fetchBackendJson("/documents", { timeoutMs: 5000 });
        const tasks = payload.items || [];
        const knownIds = new Set(tasks.map((task) => task.task_id));
        selectedLegalDocumentIds = new Set([...selectedLegalDocumentIds].filter((id) => knownIds.has(id)));
        tasks.forEach((task) => chatAttachmentTaskStates.set(task.task_id, task.status));
        saveSelectedLegalDocumentIds();
        renderChatAttachments(tasks);
        scheduleChatAttachmentRefresh(tasks);
    } catch (error) {
        console.info(error);
        renderChatAttachments([]);
    }
}

function scheduleChatAttachmentRefresh(tasks) {
    if (documentRefreshTimer) window.clearTimeout(documentRefreshTimer);
    if (tasks.some((task) => selectedLegalDocumentIds.has(task.task_id) && ["uploaded", "processing"].includes(task.status))) {
        documentRefreshTimer = window.setTimeout(refreshChatAttachments, 1500);
    }
}

function renderChatAttachments(tasks) {
    const container = document.getElementById("chat-attachment-tray");
    if (!container) return;
    const selected = tasks.filter((task) => selectedLegalDocumentIds.has(task.task_id));
    const visibleTasks = [...selected, ...chatAttachmentErrors];
    container.innerHTML = visibleTasks.map((task) => {
        const type = chatAttachmentType(task.original_filename);
        const id = task.task_id || task.client_id;
        return `
            <article class="chat-attachment-card" data-attachment-id="${escapeHtml(id)}">
                <span class="attachment-file-icon type-${type}" aria-hidden="true">${chatAttachmentTypeLabel(type, task.original_filename)}</span>
                <div class="attachment-file-info">
                    <strong title="${escapeHtml(task.original_filename)}">${escapeHtml(task.original_filename)}</strong>
                    <span>${escapeHtml(chatAttachmentStatus(task))} · ${formatDocumentSize(task.size_bytes)}</span>
                </div>
                <button class="attachment-remove-button" type="button" data-document-remove="${escapeHtml(id)}" title="移除附件" aria-label="移除附件">×</button>
            </article>
        `;
    }).join("");
}

function chatAttachmentStatus(task) {
    if (task.status === "completed") return "已就绪";
    if (task.status === "uploaded") return "正在上传";
    if (task.status === "processing") return "正在解析";
    return task.error_message || "解析失败";
}

function chatAttachmentType(filename) {
    const extension = String(filename || "").split(".").pop().toLowerCase();
    if (["doc", "docx"].includes(extension)) return "word";
    if (["xls", "xlsx", "csv"].includes(extension)) return "sheet";
    if (["ppt", "pptx"].includes(extension)) return "slides";
    if (["jpg", "jpeg", "png", "jp2", "webp", "gif", "bmp"].includes(extension)) return "image";
    if (["txt", "md"].includes(extension)) return "text";
    return extension === "pdf" ? "pdf" : "file";
}

function chatAttachmentTypeLabel(type, filename) {
    const extension = String(filename || "").split(".").pop().toLowerCase();
    if (type === "word") return extension === "docx" ? "DOCX" : "DOC";
    if (type === "sheet") return extension.toUpperCase();
    if (type === "slides") return extension.toUpperCase();
    if (type === "image") return extension === "jpeg" ? "JPG" : extension.toUpperCase();
    if (type === "text") return extension.toUpperCase();
    return { pdf: "PDF", file: "FILE" }[type] || "FILE";
}

function readyChatAttachmentIds() {
    return [...selectedLegalDocumentIds].filter((taskId) => chatAttachmentTaskStates.get(taskId) === "completed");
}

async function handleChatAttachmentAction(event) {
    const removeButton = event.target.closest("[data-document-remove]");
    if (!removeButton) return;
    const attachmentId = removeButton.dataset.documentRemove;
    if (!selectedLegalDocumentIds.has(attachmentId)) {
        chatAttachmentErrors = chatAttachmentErrors.filter((item) => item.client_id !== attachmentId);
        renderChatAttachments([]);
        return;
    }
    removeButton.disabled = true;
    try {
        await fetchBackendJson(`/documents/${encodeURIComponent(attachmentId)}`, { method: "DELETE", timeoutMs: 10000 });
    } catch (error) {
        console.info(error);
    } finally {
        selectedLegalDocumentIds.delete(attachmentId);
        chatAttachmentTaskStates.delete(attachmentId);
        saveSelectedLegalDocumentIds();
        refreshChatAttachments();
    }
}

async function handleDocumentListAction(event) {
    const selection = event.target.closest("[data-document-select]");
    if (selection) {
        const taskId = selection.dataset.documentSelect;
        if (selection.checked && !selectedLegalDocumentIds.has(taskId) && selectedLegalDocumentIds.size >= 3) {
            selection.checked = false;
            refreshDocumentWorkspace();
            return;
        }
        if (selection.checked) selectedLegalDocumentIds.add(taskId);
        else selectedLegalDocumentIds.delete(taskId);
        saveSelectedLegalDocumentIds();
        selection.closest(".legal-document-item")?.classList.toggle("selected", selection.checked);
        renderLegalSelectionStatus();
        return;
    }
    const button = event.target.closest("[data-document-action]");
    if (!button) return;
    const taskId = button.closest(".legal-document-item")?.querySelector("[data-document-select]")?.dataset.documentSelect;
    if (!taskId) return;
    const action = button.dataset.documentAction;
    if (action === "preview") {
        try {
            const result = await fetchBackendJson(`/documents/${encodeURIComponent(taskId)}/result`, { timeoutMs: 10000 });
            document.getElementById("document-preview-content").textContent = result.markdown || "";
            document.getElementById("document-preview-dialog")?.showModal();
        } catch (error) {
            console.info(error);
        }
        return;
    }
    if (action === "download") {
        window.open(`${backendState.baseUrl}/documents/${encodeURIComponent(taskId)}/content`, "_blank", "noopener");
        return;
    }
    if (action === "retry") {
        try {
            await fetchBackendJson(`/documents/${encodeURIComponent(taskId)}/retry`, { method: "POST", timeoutMs: 10000 });
            refreshDocumentWorkspace();
        } catch (error) {
            console.info(error);
        }
        return;
    }
    if (action === "delete") {
        if (!window.confirm("删除该合同及其解析结果？")) return;
        try {
            await fetchBackendJson(`/documents/${encodeURIComponent(taskId)}`, { method: "DELETE", timeoutMs: 10000 });
            selectedLegalDocumentIds.delete(taskId);
            saveSelectedLegalDocumentIds();
            refreshDocumentWorkspace();
        } catch (error) {
            console.info(error);
        }
    }
}

function startSelectedContractReview() {
    if (!selectedLegalDocumentIds.size) {
        document.getElementById("legal-upload-button")?.click();
        return;
    }
    const input = getChatInput();
    if (!input) return;
    input.value = "请审查所选合同，识别重大风险、缺失或不利条款，并给出条款级修改建议。请区分合同文本事实、法律依据与待补充信息。";
    sendLegalQuestion();
}

function getChatInput() {
    return document.querySelector(".chat-input textarea") || document.querySelector(".chat-input input");
}

function resizeChatInput(input) {
    if (!input || input.tagName !== "TEXTAREA") return;
    input.style.height = "auto";
    input.style.height = `${Math.min(input.scrollHeight, 136)}px`;
}

// Supply-chain records are persisted by the backend. Map risk is computed from
// those records plus only the external signals that can be matched to a record.
const SUPPLY_RISK_FORMULA = String.raw`R_{sc}=100(0.28C+0.24K+0.20A+0.18E+0.10L),\quad E=0.45B+0.55S`;
const SUPPLY_COMPONENT_LABELS = {
    concentration: "区域集中度",
    criticality: "业务关键性",
    alternatives: "可替代性不足",
    external: "外部市场暴露",
    compliance: "合规暴露",
};
const SUPPLY_CONTROL_STATUS_LABELS = {
    not_started: "未启动",
    monitoring: "持续监控",
    mitigating: "整改中",
    closed: "已关闭",
};
const SUPPLY_COUNTRY_ALIASES = {
    "中国": "China", "中国大陆": "China", China: "China",
    "美国": "United States of America", USA: "United States of America", "United States": "United States of America", "United States of America": "United States of America",
    "德国": "Germany", Germany: "Germany", "日本": "Japan", Japan: "Japan",
    "韩国": "South Korea", "South Korea": "South Korea", "新加坡": "Singapore", Singapore: "Singapore",
    "越南": "Vietnam", Vietnam: "Vietnam", "印度": "India", India: "India",
    "法国": "France", France: "France", "英国": "United Kingdom", "United Kingdom": "United Kingdom",
    "墨西哥": "Mexico", Mexico: "Mexico", "巴西": "Brazil", Brazil: "Brazil",
    "澳大利亚": "Australia", Australia: "Australia", "加拿大": "Canada", Canada: "Canada",
};
const SUPPLY_COUNTRY_LABELS = {
    China: "中国", "United States of America": "美国", Germany: "德国", Japan: "日本", "South Korea": "韩国",
    Singapore: "新加坡", Vietnam: "越南", India: "印度", France: "法国", "United Kingdom": "英国",
    Mexico: "墨西哥", Brazil: "巴西", Australia: "澳大利亚", Canada: "加拿大",
};
const supplyState = {
    suppliers: [],
    externalSignals: [],
    source: "workspace",
    debugRunId: null,
    mapMode: "china",
    selectedLocation: null,
    selectedSupplierId: null,
    mapPan: { x: 0, y: 0 },
    drag: null,
    suppressClickUntil: 0,
    locations: new Map(),
    featureLocations: new Map(),
};
const developerDebugState = { context: null };

function canonicalSupplyCountry(value = "") {
    const country = String(value || "").trim();
    return SUPPLY_COUNTRY_ALIASES[country] || country;
}

function supplyCountryLabel(country = "") {
    const canonical = canonicalSupplyCountry(country);
    return SUPPLY_COUNTRY_LABELS[canonical] || canonical || "未指定国家";
}

function isChinaSupplier(supplier) {
    return canonicalSupplyCountry(supplier.country) === "China";
}

function supplyLocationKey(supplier, mode = supplyState.mapMode) {
    if (mode === "china") return isChinaSupplier(supplier) ? String(supplier.province || "").trim() : "";
    return canonicalSupplyCountry(supplier.country);
}

function clampUnit(value) {
    return Math.max(0, Math.min(1, Number(value || 0)));
}

function riskLevelFromScore(score) {
    if (score >= 80) return "crit";
    if (score >= 60) return "high";
    if (score >= 35) return "med";
    return "low";
}

function externalSignalWeight(signal) {
    const severity = { low: 0.25, medium: 0.5, med: 0.5, high: 0.75, critical: 1, crit: 1 }[String(signal.severity || "").toLowerCase()] || 0;
    return clampUnit(severity * clampUnit(signal.confidence ?? 0.7));
}

function normalizedValues(values = []) {
    return new Set(values
        .flatMap((value) => String(value || "").split(/[，,;/|]/))
        .map((value) => value.trim().toLowerCase())
        .filter(Boolean));
}

function signalMetadataValues(signal, keys) {
    const metadata = signal.metadata || {};
    return keys.flatMap((key) => {
        const value = metadata[key];
        return Array.isArray(value) ? value : value == null ? [] : [value];
    });
}

function supplierSignalRelevance(supplier, signal) {
    if (supplier.external_signal_ids?.includes(signal.signal_id)) {
        return { relevance: 1, reason: "已由供应商记录显式关联" };
    }

    const explicitLinks = normalizedValues(signal.affected_supply_links || []);
    const supplierId = String(supplier.supplier_id || "").trim().toLowerCase();
    const supplierName = String(supplier.name || "").trim().toLowerCase();
    if ((supplierId && explicitLinks.has(supplierId)) || (supplierName && explicitLinks.has(supplierName))) {
        return { relevance: 0.85, reason: "实时信号已明确指向该供应商" };
    }

    const affectedCountries = new Set(
        [...normalizedValues(signalMetadataValues(signal, ["affected_countries", "affected_country"]))]
            .map((country) => canonicalSupplyCountry(country).toLowerCase())
    );
    const affectedProvinces = normalizedValues(signalMetadataValues(signal, ["affected_provinces", "affected_province"]));
    const country = canonicalSupplyCountry(supplier.country).toLowerCase();
    const countryLabel = supplyCountryLabel(supplier.country).toLowerCase();
    const province = String(supplier.province || "").trim().toLowerCase();
    if ((country && (affectedCountries.has(country) || affectedCountries.has(countryLabel))) || (province && affectedProvinces.has(province))) {
        return { relevance: 0.7, reason: "实时信号的结构化受影响地区与供应商所在地一致" };
    }

    const workflowMatch = supplierWorkflowSignalMatch(supplier, signal);
    if (workflowMatch) return workflowMatch;

    const supplierTags = normalizedValues(supplier.external_tags || []);
    const signalTags = normalizedValues([
        ...signalMetadataValues(signal, ["exposure_tags", "commodity_tags", "route_tags", "industry_tags"]),
        ...(signal.affected_supply_links || []),
    ]);
    const matchedTags = [...supplierTags].filter((tag) => signalTags.has(tag));
    if (matchedTags.length) {
        return { relevance: 0.55, reason: `外部暴露标签匹配：${matchedTags.join("、")}` };
    }
    return null;
}

function signalInstrumentSymbols(signal) {
    return new Set(signalMetadataValues(signal, ["affected_instruments", "symbols", "instrument_symbols"])
        .map((symbol) => normalizeWorkflowImportSymbol(symbol))
        .filter(Boolean));
}

function supplierWorkflowRelations(supplier) {
    const supplierNode = workflowState.nodes.find((node) => node.supplierId === supplier.supplier_id);
    if (!supplierNode) return [];
    return workflowState.links.flatMap((link) => {
        // The supply-map panel must not call a drawn line an "identified
        // chain" before it has a named confirmation.  Evidence grade and
        // boundary are carried forward for the analyst to inspect.
        if (!(link.confirmedBy && link.confirmedAt)) return [];
        if (link.source === supplierNode.id) return [{ direction: "下游", node: workflowState.nodes.find((node) => node.id === link.target), link }];
        if (link.target === supplierNode.id) return [{ direction: "上游", node: workflowState.nodes.find((node) => node.id === link.source), link }];
        return [];
    }).filter((relation) => relation.node?.symbol);
}

function supplierWorkflowSignalMatch(supplier, signal) {
    const affectedSymbols = signalInstrumentSymbols(signal);
    const ownSymbol = normalizeWorkflowImportSymbol(supplier.security_code);
    if (ownSymbol && affectedSymbols.has(ownSymbol)) {
        return { relevance: 0.82, reason: "实时信号直接覆盖供应商证券代码" };
    }
    const relation = supplierWorkflowRelations(supplier)
        .find((item) => affectedSymbols.has(normalizeWorkflowImportSymbol(item.node.symbol)));
    if (relation) {
        const node = workflowNodeMeta(relation.node);
        return { relevance: 0.62, reason: `画布已确认的${relation.direction}链条节点：${node.name}` };
    }
    return null;
}

function linkedSignalsForSuppliers(suppliers) {
    const seen = new Map();
    suppliers.forEach((supplier) => {
        supplyState.externalSignals.forEach((signal) => {
            const match = supplierSignalRelevance(supplier, signal);
            const previous = seen.get(signal.signal_id);
            if (match && (!previous || match.relevance > previous.relevance)) {
                seen.set(signal.signal_id, { signal, ...match });
            }
        });
    });
    return [...seen.values()];
}

function combinedExternalExposure(linkedSignals) {
    return 1 - linkedSignals.reduce((remaining, linked) => (
        remaining * (1 - externalSignalWeight(linked.signal) * linked.relevance)
    ), 1);
}

const SUPPLY_MARKET_RISK_CHANNELS = [
    { baseline: 0.78, keywords: ["半导体", "芯片", "集成电路", "晶圆", "光刻", "存储", "gpu", "semiconductor", "chip", "memory", "wafer"] },
    { baseline: 0.68, keywords: ["能源", "石油", "天然气", "化工", "金属", "矿产", "稀土", "原料", "energy", "oil", "gas", "chemical", "metal", "mineral"] },
    { baseline: 0.64, keywords: ["航运", "海运", "物流", "货代", "港口", "跨境", "shipping", "freight", "logistics", "port", "trade"] },
    { baseline: 0.54, keywords: ["电子", "电池", "通信", "光伏", "汽车", "机械", "设备", "electronic", "battery", "telecom", "solar", "automotive", "equipment"] },
    { baseline: 0.4, keywords: ["钢铁", "建材", "纺织", "制造", "工业", "steel", "cement", "textile", "manufacturing", "industrial"] },
    { baseline: 0.3, keywords: ["消费", "食品", "饮料", "零售", "包装", "consumer", "food", "beverage", "retail", "packaging"] },
];

function supplierMarketSensitivity(supplier) {
    const profile = `${supplier.category || ""} ${(supplier.external_tags || []).join(" ")} ${supplier.notes || ""}`.toLowerCase();
    const industryBaseline = SUPPLY_MARKET_RISK_CHANNELS
        .find((channel) => channel.keywords.some((keyword) => profile.includes(keyword)))?.baseline ?? 0.38;
    const crossBorder = isChinaSupplier(supplier) ? 0 : 0.1;
    const businessCriticality = 0.12 * clampUnit(Number(supplier.criticality || 0) / 100);
    const procurementMateriality = 0.08 * clampUnit(Number(supplier.spend_share || 0) / 100);
    const replacementPressure = 0.1 * (1 - Math.min(Math.max(Number(supplier.alternate_sources || 0), 0), 3) / 3);
    return clampUnit(industryBaseline + crossBorder + businessCriticality + procurementMateriality + replacementPressure);
}

function weightedSupplierAverage(suppliers, scoreForSupplier) {
    if (!suppliers.length) return 0;
    const totalSpend = suppliers.reduce((sum, supplier) => sum + Math.max(0, Number(supplier.spend_share || 0)), 0);
    if (!totalSpend) return suppliers.reduce((sum, supplier) => sum + scoreForSupplier(supplier), 0) / suppliers.length;
    return suppliers.reduce((sum, supplier) => sum + scoreForSupplier(supplier) * Math.max(0, Number(supplier.spend_share || 0)), 0) / totalSpend;
}

function scoreSupplyLocation(suppliers) {
    const linkedSignals = linkedSignalsForSuppliers(suppliers);
    const externalBaseline = weightedSupplierAverage(suppliers, supplierMarketSensitivity);
    const realTimeSignalExposure = combinedExternalExposure(linkedSignals);
    const average = (key, fallback = 0) => suppliers.length
        ? suppliers.reduce((sum, supplier) => sum + Number(supplier[key] ?? fallback), 0) / suppliers.length / 100
        : 0;
    const components = {
        concentration: clampUnit(suppliers.reduce((sum, supplier) => sum + Number(supplier.spend_share || 0), 0) / 100),
        criticality: clampUnit(average("criticality", 50)),
        alternatives: clampUnit(suppliers.length ? suppliers.reduce((sum, supplier) => sum + (1 - Math.min(Number(supplier.alternate_sources || 0), 3) / 3), 0) / suppliers.length : 0),
        external: clampUnit(0.45 * externalBaseline + 0.55 * realTimeSignalExposure),
        compliance: clampUnit(average("compliance_risk")),
    };
    const score = 100 * (
        0.28 * components.concentration +
        0.24 * components.criticality +
        0.20 * components.alternatives +
        0.18 * components.external +
        0.10 * components.compliance
    );
    return { components, score: Math.round(score), risk: riskLevelFromScore(score), linkedSignals, externalBaseline, realTimeSignalExposure };
}

function buildSupplyLocations() {
    const locations = new Map();
    supplyState.suppliers.forEach((supplier) => {
        const key = supplyLocationKey(supplier);
        if (!key) return;
        if (!locations.has(key)) locations.set(key, []);
        locations.get(key).push(supplier);
    });
    supplyState.locations = new Map([...locations.entries()].map(([key, suppliers]) => [key, {
        key,
        label: supplyState.mapMode === "china" ? key : supplyCountryLabel(key),
        suppliers,
        ...scoreSupplyLocation(suppliers),
    }]));
    return supplyState.locations;
}

function supplyRiskFormulaTooltip() {
    return `<button class="risk-formula-info" type="button" data-supply-formula-info aria-label="查看供应链风险分计算方法" aria-describedby="supply-formula-popover"><span aria-hidden="true">i</span></button>`;
}

function supplyFormulaPopoverContent() {
    return `
        <span class="risk-formula-title">供应链风险分公式</span>
        <math class="risk-math" display="block" aria-label="Supply chain risk equals 100 times five weighted components" data-latex="${SUPPLY_RISK_FORMULA}">
            <mrow><msub><mi>R</mi><mi>sc</mi></msub><mo>=</mo><mn>100</mn><mo>(</mo><mn>0.28</mn><mi>C</mi><mo>+</mo><mn>0.24</mn><mi>K</mi><mo>+</mo><mn>0.20</mn><mi>A</mi><mo>+</mo><mn>0.18</mn><mi>E</mi><mo>+</mo><mn>0.10</mn><mi>L</mi><mo>)</mo></mrow>
        </math>
        <math class="risk-math risk-math-secondary" display="block" aria-label="External exposure equals weighted market baseline plus combined real time signal exposure">
            <mrow><mi>E</mi><mo>=</mo><mn>0.45</mn><mi>B</mi><mo>+</mo><mn>0.55</mn><mi>S</mi></mrow>
        </math>
        <span class="risk-formula-note">C 为区域采购集中度，K 为业务关键性，A 为可替代性不足，L 为合规暴露。E 参照市场风险分的组合暴露：B 由通用行业风险通道、跨境属性、关键性、采购占比和替代来源形成；S 为按置信度和关联度组合后的实时信号暴露。实时信号必须具有供应商、地区或精确标签依据。</span>
    `;
}

const supplyFormulaPopoverState = { button: null, hideTimer: null };

function supplyFormulaPopover() {
    let popover = document.getElementById("supply-formula-popover");
    if (!popover) {
        popover = document.createElement("section");
        popover.id = "supply-formula-popover";
        popover.className = "supply-formula-popover";
        popover.setAttribute("role", "tooltip");
        popover.setAttribute("aria-hidden", "true");
        document.body.appendChild(popover);
    }
    return popover;
}

function positionSupplyFormulaPopover() {
    const button = supplyFormulaPopoverState.button;
    const map = document.querySelector("#view-supply .map-center");
    const popover = supplyFormulaPopover();
    if (!button || !map) return;
    const buttonRect = button.getBoundingClientRect();
    const mapRect = map.getBoundingClientRect();
    const inset = 16;
    const availableWidth = Math.min(460, Math.max(0, mapRect.width - inset * 2));
    const desiredLeft = buttonRect.left - availableWidth - 12;
    const left = Math.max(inset, Math.min(desiredLeft, window.innerWidth - availableWidth - inset));
    popover.style.width = `${availableWidth}px`;
    popover.style.left = `${Math.round(left)}px`;
    popover.style.top = `${Math.round(Math.max(inset, buttonRect.top - 10))}px`;
}

function showSupplyFormulaPopover(button) {
    if (!button) return;
    window.clearTimeout(supplyFormulaPopoverState.hideTimer);
    supplyFormulaPopoverState.button = button;
    const popover = supplyFormulaPopover();
    popover.innerHTML = supplyFormulaPopoverContent();
    popover.classList.add("visible");
    popover.setAttribute("aria-hidden", "false");
    positionSupplyFormulaPopover();
}

function hideSupplyFormulaPopover() {
    window.clearTimeout(supplyFormulaPopoverState.hideTimer);
    supplyFormulaPopoverState.hideTimer = window.setTimeout(() => {
        const popover = supplyFormulaPopover();
        popover.classList.remove("visible");
        popover.setAttribute("aria-hidden", "true");
        supplyFormulaPopoverState.button = null;
    }, 90);
}

function setupSupplyFormulaPopover() {
    if (document.body.dataset.supplyFormulaBound) return;
    document.body.dataset.supplyFormulaBound = "true";
    document.addEventListener("pointerover", (event) => {
        const button = event.target.closest?.("[data-supply-formula-info]");
        if (button) showSupplyFormulaPopover(button);
    });
    document.addEventListener("pointerout", (event) => {
        const button = event.target.closest?.("[data-supply-formula-info]");
        if (button && !button.contains(event.relatedTarget)) hideSupplyFormulaPopover();
    });
    document.addEventListener("focusin", (event) => {
        const button = event.target.closest?.("[data-supply-formula-info]");
        if (button) showSupplyFormulaPopover(button);
    });
    document.addEventListener("focusout", (event) => {
        const button = event.target.closest?.("[data-supply-formula-info]");
        if (button && !button.contains(event.relatedTarget)) hideSupplyFormulaPopover();
    });
    window.addEventListener("resize", positionSupplyFormulaPopover);
}

function renderSupplySummary() {
    const locations = buildSupplyLocations();
    const allScore = scoreSupplyLocation(supplyState.suppliers);
    const highCount = [...locations.values()].filter((item) => item.risk === "high" || item.risk === "crit").length;
    document.getElementById("supply-supplier-count").textContent = String(supplyState.suppliers.length);
    document.getElementById("supply-location-count").textContent = String(locations.size);
    document.getElementById("supply-high-risk-count").textContent = String(highCount);
    return allScore;
}

function renderSupplyRegionList() {
    const list = document.getElementById("supply-region-list");
    if (!list) return;
    const locations = [...supplyState.locations.values()].sort((a, b) => b.score - a.score || a.label.localeCompare(b.label, "zh-CN"));
    if (!locations.length) {
        list.innerHTML = `<div class="empty-state supply-empty-list">暂无${supplyState.mapMode === "china" ? "中国省份" : "国家"}供应商记录。</div>`;
        return;
    }
    list.innerHTML = locations.map((location) => `
        <button class="region-item ${location.key === supplyState.selectedLocation ? "active" : ""}" type="button" data-supply-location="${escapeHtml(location.key)}">
            <span class="risk-dot ${location.risk}"></span><span>${escapeHtml(location.label)}</span><span class="region-item-count">${location.suppliers.length}</span>
        </button>
    `).join("");
}

function worldMapFeatures() {
    const source = window.WORLD_COUNTRIES?.features || [];
    const china = source.find((feature) => feature.properties?.name === "China");
    const taiwan = source.find((feature) => feature.properties?.name === "Taiwan");
    if (!china) return source.filter((feature) => !["Antarctica", "Taiwan"].includes(feature.properties?.name));

    const asMultiPolygon = (geometry) => {
        if (geometry?.type === "MultiPolygon") return geometry.coordinates;
        if (geometry?.type === "Polygon") return [geometry.coordinates];
        return [];
    };
    const unitedChina = {
        ...china,
        properties: { ...china.properties, name: "China" },
        geometry: {
            type: "MultiPolygon",
            coordinates: [...asMultiPolygon(china.geometry), ...asMultiPolygon(taiwan?.geometry)],
        },
    };
    return source
        .filter((feature) => !["Antarctica", "China", "Taiwan"].includes(feature.properties?.name))
        .concat(unitedChina);
}

function currentMapFeatures() {
    if (supplyState.mapMode === "china") return window.CHINA_PROVINCES?.features || [];
    return worldMapFeatures();
}

function featureLocationKey(feature) {
    const name = feature.properties?.name || "";
    return supplyState.mapMode === "china" ? name : canonicalSupplyCountry(name);
}

function applySupplyMapTransform() {
    if (!mapViewportGroup) return;
    const cx = 500;
    const cy = 390;
    const { x, y } = supplyState.mapPan;
    mapViewportGroup.setAttribute("transform", `translate(${x} ${y}) translate(${cx} ${cy}) scale(${mapZoom}) translate(${-cx} ${-cy})`);
}

function renderChinaMap() {
    const features = currentMapFeatures();
    if (!svg || !features.length) return;
    provinceMeta.clear();
    supplyState.featureLocations.clear();
    const project = createProjection(features);
    mapViewportGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
    const baseLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
    const labelLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
    const seaLabelLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
    seaLabelLayer.setAttribute("class", "supply-sea-label-layer");
    mapViewportGroup.append(baseLayer, labelLayer, seaLabelLayer);
    svg.replaceChildren(mapViewportGroup);
    svg.classList.add("supply-map-svg");
    svg.setAttribute("aria-label", supplyState.mapMode === "china" ? "中国省级供应链风险地图" : "全球国家供应链风险地图");

    features.forEach((feature) => {
        const key = featureLocationKey(feature);
        const location = supplyState.locations.get(key);
        const bounds = projectedBounds(feature, project);
        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("class", `province-path supply-map-path ${location ? `risk-${location.risk}` : ""}`);
        path.setAttribute("data-supply-location", key);
        path.setAttribute("d", pathFromGeometry(feature.geometry, project));
        path.addEventListener("mouseenter", (event) => showSupplyTooltip(event, feature, location));
        path.addEventListener("mousemove", positionTooltip);
        path.addEventListener("mouseleave", () => tooltip?.classList.remove("visible"));
        path.addEventListener("click", () => {
            if (Date.now() < supplyState.suppressClickUntil) return;
            selectSupplyLocation(key);
        });
        path.addEventListener("contextmenu", (event) => {
            event.preventDefault();
            if (location) selectSupplyLocation(key);
            openSupplyContextMenu(event, { location: key, supplierId: location?.suppliers[0]?.supplier_id || "" });
        });
        baseLayer.appendChild(path);
        supplyState.featureLocations.set(key, path);
        if (supplyState.mapMode === "china" && location) {
            const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
            label.setAttribute("class", "province-label supply-map-label");
            label.setAttribute("x", ((bounds.minX + bounds.maxX) / 2).toFixed(1));
            label.setAttribute("y", ((bounds.minY + bounds.maxY) / 2).toFixed(1));
            label.textContent = key;
            labelLayer.appendChild(label);
        }
    });
    if (supplyState.mapMode === "world") {
        [
            [155, 12, "太平洋"], [-35, 13, "大西洋"], [75, -25, "印度洋"], [0, 68, "北冰洋"],
        ].forEach(([lon, lat, label]) => {
            const [x, y] = project([lon, lat]);
            const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
            text.setAttribute("class", "supply-sea-label");
            text.setAttribute("x", x.toFixed(1));
            text.setAttribute("y", y.toFixed(1));
            text.textContent = label;
            seaLabelLayer.appendChild(text);
        });
    }
    applySupplyMapTransform();
    updateSupplyMapSelection();
}

function showSupplyTooltip(event, feature, location) {
    if (!tooltip) return;
    const label = supplyState.mapMode === "china" ? feature.properties?.name : supplyCountryLabel(feature.properties?.name);
    tooltip.innerHTML = location ? `
        <div class="tooltip-title">${escapeHtml(location.label)}<span class="risk-dot ${location.risk}"></span></div>
        <div class="tooltip-sub">${location.suppliers.length} 家供应商 · 风险分 ${location.score}/100</div>
        <div class="tooltip-row"><span>关联市场信号</span><strong>${location.linkedSignals.length}</strong></div>
    ` : `<div class="tooltip-title">${escapeHtml(label)}</div><div class="tooltip-sub">暂无已保存的供应商记录</div>`;
    tooltip.classList.add("visible");
    positionTooltip(event);
}

function updateSupplyMapSelection() {
    supplyState.featureLocations.forEach((path, key) => {
        const selected = key === supplyState.selectedLocation;
        const dimmed = Boolean(supplyState.selectedLocation) && !selected;
        path.classList.toggle("selected", selected);
        path.classList.toggle("dimmed", dimmed);
    });
}

function selectSupplyLocation(key) {
    if (supplyState.selectedLocation === key) {
        clearSupplySelection();
        return;
    }
    supplyState.selectedLocation = key;
    supplyState.selectedSupplierId = supplyState.locations.get(key)?.suppliers[0]?.supplier_id || null;
    updateSupplyMapSelection();
    renderSupplyRegionList();
    renderSupplyDetailPanel();
}

function clearSupplySelection() {
    supplyState.selectedLocation = null;
    supplyState.selectedSupplierId = null;
    updateSupplyMapSelection();
    renderSupplyRegionList();
    renderSupplyDetailPanel();
}

function selectRegion(key) {
    if (key === "china") clearSupplySelection();
}

function renderSupplyComponentRows(components) {
    return Object.entries(components).map(([key, value]) => `
        <div class="risk-component-row"><span>${SUPPLY_COMPONENT_LABELS[key]}</span><div><i style="width:${(value * 100).toFixed(1)}%"></i></div><strong>${Math.round(value * 100)}</strong></div>
    `).join("");
}

function supplySignalSourceLink(signal) {
    const source = String(signal?.source || "").trim();
    if (!/^https?:\/\//i.test(source)) return "";
    let label = "查看原始来源";
    try { label = new URL(source).hostname.replace(/^www\./, ""); } catch (_error) { /* Use the stable fallback label. */ }
    return `<a class="supply-signal-source" href="${escapeHtml(source)}" target="_blank" rel="noopener noreferrer">${escapeHtml(label)}</a>`;
}

function supplyWorkflowRelationSummary(suppliers) {
    const seen = new Set();
    return suppliers.flatMap((supplier) => supplierWorkflowRelations(supplier).map((relation) => ({ supplier, ...relation })))
        .filter((relation) => {
            const key = `${relation.supplier.supplier_id}:${relation.direction}:${relation.node.id}`;
            if (seen.has(key)) return false;
            seen.add(key);
            return true;
        });
}

function renderSupplyDetailPanel() {
    const panel = document.getElementById("detail-panel");
    if (!panel) return;
    const allScore = scoreSupplyLocation(supplyState.suppliers);
    const location = supplyState.selectedLocation ? supplyState.locations.get(supplyState.selectedLocation) : null;
    if (supplyState.selectedLocation && !location) {
        const selectedLabel = supplyState.mapMode === "china" ? supplyState.selectedLocation : supplyCountryLabel(supplyState.selectedLocation);
        panel.innerHTML = `
            <div class="detail-header"><div class="detail-title">${escapeHtml(selectedLabel)}</div><div class="detail-subtitle">此地区尚未保存供应商记录</div></div>
            <div class="empty-state supply-location-empty">可在此地区新增供应商；保存后将计算区域风险分并关联有明确暴露依据的实时信号。</div>
            <div class="detail-section"><button class="btn btn-primary supply-detail-add" type="button" data-supply-add-location="${escapeHtml(supplyState.selectedLocation)}">添加供应商</button></div>
        `;
        return;
    }
    if (!location) {
        panel.innerHTML = `
            <div class="detail-header"><div class="detail-title">供应链总览</div><div class="detail-subtitle">保存供应商后，风险分将按地区实时聚合</div></div>
            <div class="detail-section">
                <div class="detail-metric"><div>供应链风险分 ${supplyRiskFormulaTooltip()}</div><strong class="risk-text ${allScore.risk}">${allScore.score}/100</strong></div>
                <div class="risk-bar"><div style="width:${allScore.score}%; background:var(--${allScore.risk === "crit" ? "red" : allScore.risk === "high" ? "orange" : allScore.risk === "med" ? "yellow" : "green"})"></div></div>
            </div>
            <section class="risk-coefficient-detail supply-score-detail"><div class="risk-coefficient-detail-head"><span>风险构成</span><strong>关联信号 ${allScore.linkedSignals.length}</strong></div><div class="risk-component-list">${renderSupplyComponentRows(allScore.components)}</div></section>
            <div class="detail-section"><button class="btn btn-primary supply-detail-add" type="button" data-supply-add>添加供应商</button></div>
        `;
        return;
    }
    const linkedSignals = location.linkedSignals.slice(0, 5);
    const workflowRelations = supplyWorkflowRelationSummary(location.suppliers);
    panel.innerHTML = `
        <div class="detail-header"><div class="detail-title">${escapeHtml(location.label)} <span class="risk-text ${location.risk}">${riskLabels[location.risk]}</span></div><div class="detail-subtitle">${location.suppliers.length} 家供应商 · 已关联 ${linkedSignals.length} 条外部市场信号</div></div>
        <div class="detail-section"><div class="detail-metric"><div>区域风险分 ${supplyRiskFormulaTooltip()}</div><strong class="risk-text ${location.risk}">${location.score}/100</strong></div><div class="risk-bar"><div style="width:${location.score}%; background:var(--${location.risk === "crit" ? "red" : location.risk === "high" ? "orange" : location.risk === "med" ? "yellow" : "green"})"></div></div></div>
        <section class="risk-coefficient-detail supply-score-detail"><div class="risk-coefficient-detail-head"><span>风险构成</span><strong>实时联动</strong></div><div class="risk-component-list">${renderSupplyComponentRows(location.components)}</div></section>
        <div class="detail-section"><h2>供应商</h2><div class="supplier-list">${location.suppliers.map((supplier) => `
            <div class="supplier-item ${supplier.supplier_id === supplyState.selectedSupplierId ? "selected" : ""}" data-supplier-id="${escapeHtml(supplier.supplier_id)}">
                <span class="risk-dot ${riskLevelFromScore(scoreSupplyLocation([supplier]).score)}"></span><div><div class="supplier-name">${escapeHtml(supplier.name)}</div><div class="supplier-province">${escapeHtml(supplier.category)} · ${escapeHtml(supplier.city || supplier.province || supplyCountryLabel(supplier.country))}</div><div class="supplier-control-meta">${escapeHtml(SUPPLY_CONTROL_STATUS_LABELS[supplier.control_status] || "未启动")}${supplier.risk_owner ? ` · ${escapeHtml(supplier.risk_owner)}` : ""}${supplier.evidence_refs?.length ? ` · 证据 ${supplier.evidence_refs.length}` : ""}${supplier.record_scope === "competition_scenario" ? ` · ${escapeHtml(workflowEvidenceGradeLabel(supplier.mapping_evidence_grade))}` : ""}</div></div>
                <button class="supplier-row-action" type="button" data-supply-edit="${escapeHtml(supplier.supplier_id)}" title="编辑供应商" aria-label="编辑 ${escapeHtml(supplier.name)}"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m4 16.5-.8 4.3 4.3-.8L19 8.5 15.5 5zM14.5 6l3.5 3.5"/></svg></button>
            </div>`).join("")}</div></div>
        <div class="detail-section"><h2>已确认链条</h2>${workflowRelations.length ? `<div class="supply-chain-relation-list">${workflowRelations.map(({ supplier, direction, node, link }) => `<span>${escapeHtml(supplier.name)}<b>${direction}</b>${escapeHtml(workflowNodeMeta(node).name)}<small>${escapeHtml(node.symbol)} · ${escapeHtml(workflowEvidenceGradeLabel(link.evidenceGrade))} · ${escapeHtml(workflowScopeLabel(link.relationshipScope))}</small></span>`).join("")}</div><p class="supply-chain-boundary">仅展示已确认的画布连线；“演练代理”用于行业/成本传导测试，不表示真实商业关系。</p>` : `<div class="empty-state">带证券代码的供应商节点可在市场风险画布中手工连线；连线确认后才会在此展示上下游关系。</div>`}</div>
        <div class="detail-section"><h2>关联外部信号</h2>${linkedSignals.length ? `<div class="supply-signal-list">${linkedSignals.map(({ signal, relevance, reason }) => `<div class="supply-signal-entry"><button type="button" data-open-market title="${escapeHtml(reason)}"><span>${escapeHtml(externalSignalDisplayTitle(signal))}<small>${escapeHtml(reason)} · 关联度 ${Math.round(relevance * 100)}%</small></span><span class="risk-text ${normalizeRiskLevel(signal.severity)}">${riskLevelLabel(signal.severity)}</span></button>${supplySignalSourceLink(signal)}</div>`).join("")}</div>` : `<div class="empty-state">暂无具有明确地区、供应商、证券代码或链条依据的外部市场信号。</div>`}</div>
    `;
}

function renderSupplyWorkspace() {
    renderSupplySummary();
    renderSupplyRegionList();
    renderChinaMap();
    renderSupplyDetailPanel();
}

function resetSupplyMap() {
    mapZoom = supplyState.mapMode === "china" ? 1.06 : 1;
    supplyState.mapPan = { x: 0, y: 0 };
    applySupplyMapTransform();
}

function setupMapZoomControls() {
    const zoomIn = document.getElementById("map-zoom-in");
    const zoomOut = document.getElementById("map-zoom-out");
    const zoomReset = document.getElementById("map-zoom-reset");
    if (!zoomIn || zoomIn.dataset.bound) return;
    zoomIn.dataset.bound = "true";
    zoomIn.addEventListener("click", () => { mapZoom = Math.min(2.6, Number((mapZoom + 0.14).toFixed(2))); applySupplyMapTransform(); });
    zoomOut?.addEventListener("click", () => { mapZoom = Math.max(0.7, Number((mapZoom - 0.14).toFixed(2))); applySupplyMapTransform(); });
    zoomReset?.addEventListener("click", resetSupplyMap);
    svg?.addEventListener("wheel", (event) => {
        event.preventDefault();
        mapZoom = Math.max(0.7, Math.min(2.6, Number((mapZoom + (event.deltaY < 0 ? 0.08 : -0.08)).toFixed(2))));
        applySupplyMapTransform();
    }, { passive: false });
    svg?.addEventListener("pointerdown", (event) => {
        if (event.button !== 0) return;
        supplyState.drag = {
            pointerId: event.pointerId,
            startX: event.clientX,
            startY: event.clientY,
            panX: supplyState.mapPan.x,
            panY: supplyState.mapPan.y,
            moved: false,
            location: event.target.closest?.(".supply-map-path")?.dataset.supplyLocation || "",
        };
        svg.setPointerCapture?.(event.pointerId);
        svg.classList.add("is-panning");
    });
    svg?.addEventListener("pointermove", (event) => {
        const drag = supplyState.drag;
        if (!drag || drag.pointerId !== event.pointerId) return;
        const dx = event.clientX - drag.startX;
        const dy = event.clientY - drag.startY;
        if (Math.abs(dx) + Math.abs(dy) > 4) drag.moved = true;
        supplyState.mapPan = { x: drag.panX + dx, y: drag.panY + dy };
        applySupplyMapTransform();
    });
    const endDrag = (event) => {
        if (!supplyState.drag || supplyState.drag.pointerId !== event.pointerId) return;
        const moved = supplyState.drag.moved;
        const location = supplyState.drag.location;
        svg?.releasePointerCapture?.(event.pointerId);
        svg?.classList.remove("is-panning");
        supplyState.drag = null;
        if (moved || location) supplyState.suppressClickUntil = Date.now() + 120;
        if (!moved && location) selectSupplyLocation(location);
    };
    svg?.addEventListener("pointerup", endDrag);
    svg?.addEventListener("pointercancel", endDrag);
}

function openSupplyContextMenu(event, context = {}) {
    if (!contextMenu) return;
    const x = Math.min(event.clientX, window.innerWidth - 156);
    const y = Math.min(event.clientY, window.innerHeight - 110);
    contextMenu.style.left = `${Math.max(8, x)}px`;
    contextMenu.style.top = `${Math.max(8, y)}px`;
    contextMenu.dataset.supplyLocation = context.location || "";
    contextMenu.dataset.supplierId = context.supplierId || "";
    contextMenu.classList.add("open");
    contextMenu.setAttribute("aria-hidden", "false");
}

function openSupplierDialog(supplier = null, context = {}) {
    if (supplyState.source === "developer_debug") {
        document.getElementById("supply-debug-status").textContent = "当前为隔离调试场景；供应商编辑已锁定，避免写入工作区数据。";
        return;
    }
    const dialog = document.getElementById("supplier-dialog");
    const form = document.getElementById("supplier-form");
    if (!dialog || !form) return;
    form.reset();
    document.getElementById("supplier-id").value = supplier?.supplier_id || "";
    document.getElementById("supplier-dialog-title").textContent = supplier ? "编辑供应商" : "添加供应商";
    document.getElementById("supplier-name").value = supplier?.name || "";
    document.getElementById("supplier-category").value = supplier?.category || "";
    document.getElementById("supplier-country").value = supplier ? supplyCountryLabel(supplier.country) : (context.country || (supplyState.mapMode === "china" ? "中国" : ""));
    document.getElementById("supplier-province").value = supplier?.province || context.province || "";
    document.getElementById("supplier-city").value = supplier?.city || "";
    document.getElementById("supplier-security-code").value = supplier?.security_code || "";
    document.getElementById("supplier-spend-share").value = supplier?.spend_share ?? 0;
    document.getElementById("supplier-criticality").value = supplier?.criticality ?? 50;
    document.getElementById("supplier-alternate-sources").value = supplier?.alternate_sources ?? 0;
    document.getElementById("supplier-compliance-risk").value = supplier?.compliance_risk ?? 0;
    document.getElementById("supplier-external-tags").value = (supplier?.external_tags || []).join("，");
    document.getElementById("supplier-risk-owner").value = supplier?.risk_owner || "";
    document.getElementById("supplier-control-status").value = supplier?.control_status || "not_started";
    document.getElementById("supplier-last-reviewed-at").value = supplier?.last_reviewed_at || "";
    document.getElementById("supplier-evidence-refs").value = (supplier?.evidence_refs || []).join("，");
    document.getElementById("supplier-notes").value = supplier?.notes || "";
    document.getElementById("supplier-form-status").textContent = "";
    dialog.showModal();
    document.getElementById("supplier-name").focus();
}

async function saveSupplierFromDialog(event) {
    event.preventDefault();
    const supplierId = document.getElementById("supplier-id").value;
    const status = document.getElementById("supplier-form-status");
    const saveButton = document.getElementById("supplier-save-button");
    const tags = document.getElementById("supplier-external-tags").value.split(/[，,]/).map((value) => value.trim()).filter(Boolean);
    const evidenceRefs = document.getElementById("supplier-evidence-refs").value.split(/[，,]/).map((value) => value.trim()).filter(Boolean);
    const existingSupplier = supplyState.suppliers.find((supplier) => supplier.supplier_id === supplierId);
    const payload = {
        name: document.getElementById("supplier-name").value.trim(),
        category: document.getElementById("supplier-category").value.trim(),
        country: document.getElementById("supplier-country").value.trim(),
        province: document.getElementById("supplier-province").value.trim() || null,
        city: document.getElementById("supplier-city").value.trim() || null,
        spend_share: Number(document.getElementById("supplier-spend-share").value),
        criticality: Number(document.getElementById("supplier-criticality").value),
        alternate_sources: Number(document.getElementById("supplier-alternate-sources").value),
        compliance_risk: Number(document.getElementById("supplier-compliance-risk").value),
        external_tags: tags,
        external_signal_ids: existingSupplier?.external_signal_ids || [],
        security_code: document.getElementById("supplier-security-code").value.trim() || null,
        risk_owner: document.getElementById("supplier-risk-owner").value.trim() || null,
        control_status: document.getElementById("supplier-control-status").value,
        last_reviewed_at: document.getElementById("supplier-last-reviewed-at").value || null,
        evidence_refs: evidenceRefs,
        record_scope: existingSupplier?.record_scope || "business_record",
        mapping_evidence_grade: existingSupplier?.mapping_evidence_grade || "unverified",
        relationship_boundary: existingSupplier?.relationship_boundary || null,
        notes: document.getElementById("supplier-notes").value.trim() || null,
    };
    if (!payload.name || !payload.category || !payload.country) return;
    status.textContent = "正在保存";
    saveButton.disabled = true;
    try {
        await fetchBackendJson(supplierId ? `/supply-chain/suppliers/${encodeURIComponent(supplierId)}` : "/supply-chain/suppliers", {
            method: supplierId ? "PUT" : "POST",
            body: JSON.stringify(payload),
            timeoutMs: 10000,
        });
        document.getElementById("supplier-dialog").close();
        await loadSupplyChainWorkspace();
    } catch (error) {
        console.info(error);
        status.textContent = "保存失败，请检查后端服务后重试。";
    } finally {
        saveButton.disabled = false;
    }
}

async function deleteSupplySupplier(supplierId) {
    if (supplyState.source === "developer_debug") return;
    const supplier = supplyState.suppliers.find((item) => item.supplier_id === supplierId);
    if (!supplier || !window.confirm(`删除供应商“${supplier.name}”？`)) return;
    try {
        await fetchBackendJson(`/supply-chain/suppliers/${encodeURIComponent(supplierId)}`, { method: "DELETE", timeoutMs: 10000 });
        await loadSupplyChainWorkspace();
    } catch (error) {
        console.info(error);
    }
}

function setupSupplierContextMenu() {
    if (!contextMenu || contextMenu.dataset.bound) return;
    contextMenu.dataset.bound = "true";
    contextMenu.addEventListener("click", (event) => {
        const button = event.target.closest("button[data-action]");
        if (!button) return;
        const location = contextMenu.dataset.supplyLocation;
        const supplierId = contextMenu.dataset.supplierId;
        closeSupplierMenu();
        if (button.dataset.action === "add") {
            openSupplierDialog(null, supplyState.mapMode === "china" ? { country: "中国", province: location } : { country: location });
        } else if (button.dataset.action === "edit" && supplierId) {
            openSupplierDialog(supplyState.suppliers.find((item) => item.supplier_id === supplierId));
        } else if (button.dataset.action === "delete" && supplierId) {
            deleteSupplySupplier(supplierId);
        }
    });
    document.addEventListener("click", closeSupplierMenu);
    document.addEventListener("keydown", (event) => { if (event.key === "Escape") closeSupplierMenu(); });
    document.getElementById("detail-panel")?.addEventListener("click", (event) => {
        const editId = event.target.closest("[data-supply-edit]")?.dataset.supplyEdit;
        if (editId) return openSupplierDialog(supplyState.suppliers.find((item) => item.supplier_id === editId));
        const addLocation = event.target.closest("[data-supply-add-location]")?.dataset.supplyAddLocation;
        if (addLocation) return openSupplierDialog(null, supplyState.mapMode === "china" ? { country: "中国", province: addLocation } : { country: addLocation });
        if (event.target.closest("[data-supply-add]")) return openSupplierDialog();
        if (event.target.closest("[data-open-market]")) document.querySelector('.nav-item[data-tab="market"]')?.click();
    });
}

function setupSupplyChainWorkspace() {
    document.getElementById("supply-add-button")?.addEventListener("click", () => openSupplierDialog());
    document.getElementById("supply-map-mode")?.addEventListener("click", (event) => {
        const mode = event.target.closest("[data-map-mode]")?.dataset.mapMode;
        if (!mode || mode === supplyState.mapMode) return;
        supplyState.mapMode = mode;
        supplyState.selectedLocation = null;
        document.querySelectorAll("[data-map-mode]").forEach((button) => button.classList.toggle("active", button.dataset.mapMode === mode));
        resetSupplyMap();
        renderSupplyWorkspace();
    });
    document.getElementById("supply-region-list")?.addEventListener("click", (event) => {
        const key = event.target.closest("[data-supply-location]")?.dataset.supplyLocation;
        if (key) selectSupplyLocation(key);
    });
    document.getElementById("supplier-form")?.addEventListener("submit", saveSupplierFromDialog);
    document.getElementById("supply-debug-load")?.addEventListener("click", loadSelectedDeveloperDebugScenario);
    document.querySelectorAll("[data-supplier-dialog-close]").forEach((button) => button.addEventListener("click", () => document.getElementById("supplier-dialog")?.close()));
}

function setSupplyExternalSignals(signals = []) {
    supplyState.externalSignals = Array.isArray(signals) ? signals : [];
    renderSupplyWorkspace();
}

function syncSupplierWorkflowNodes() {
    if (supplyState.source === "developer_debug") return;
    if (!workflowState.loaded) return;
    const suppliersWithSymbols = supplyState.suppliers.filter((supplier) => supplier.security_code);
    let changed = false;
    // The graph is the saved relationship record.  Inventory refreshes may add
    // draft cards, but they must not remove existing graph nodes or links.

    suppliersWithSymbols.forEach((supplier, index) => {
        const id = `supplier-node-${supplier.supplier_id}`;
        const symbol = normalizeWorkflowImportSymbol(supplier.security_code);
        // A saved graph may use a business-specific node id.  Match its
        // supplier binding before considering an inventory card "missing";
        // otherwise merely opening the page duplicates a confirmed node.
        const existing = workflowState.nodes.find((node) => node.supplierId === supplier.supplier_id)
            || workflowState.nodes.find((node) => node.id === id);
        if (existing) {
            // The persisted canvas is authoritative for symbol, label,
            // position and relationship state.  Supplier inventory refreshes
            // must never rewrite it as an unconnected draft card.
            return;
        }
        workflowState.nodes.push({
            id,
            symbol,
            name: supplier.name,
            nodeKind: "supplier",
            supplierId: supplier.supplier_id,
            lane: "供应商待连线",
            group: supplier.category,
            x: 40,
            y: 1520 + index * 150,
        });
        changed = true;
    });
    if (!changed) return;
    workflowState.supplierBindingsPending = true;
    renderWorkflowPalette();
    renderWorkflowCanvas();
    suppliersWithSymbols.forEach((supplier) => {
        const node = workflowState.nodes.find((item) => item.supplierId === supplier.supplier_id);
        if (node) refreshWorkflowNodeQuote(node);
    });
    setWorkflowSaveStatus("dirty", "供应商卡片待确认；保存后才写入关系图");
}

async function loadSupplyChainWorkspace() {
    const status = document.getElementById("supply-source-status");
    if (status) status.textContent = "正在读取供应链记录";
    try {
        const payload = await fetchBackendJson("/supply-chain/suppliers", { timeoutMs: 10000 });
        supplyState.suppliers = Array.isArray(payload.items) ? payload.items : [];
        supplyState.source = "workspace";
        supplyState.debugRunId = null;
        document.getElementById("supply-add-button").disabled = false;
        if (status) status.textContent = supplyState.suppliers.length
            ? `比赛演练供应商台账 · ${supplyState.suppliers.length} 条记录 · 非实时供货核验`
            : "暂无供应商记录，可从右上角添加";
    } catch (error) {
        console.info(error);
        supplyState.suppliers = [];
        if (status) status.textContent = "供应链数据服务暂不可用";
    }
    syncSupplierWorkflowNodes();
    renderSupplyWorkspace();
}

async function loadDeveloperDebugScenarios() {
    const controls = document.getElementById("supply-debug-controls");
    const select = document.getElementById("supply-debug-scenario");
    const button = document.getElementById("supply-debug-load");
    const status = document.getElementById("supply-debug-status");
    if (!controls || !select || !button || !status) return;
    try {
        const payload = await fetchBackendJson("/developer-debug/status", { timeoutMs: 5000 });
        const scenarios = Array.isArray(payload.scenarios) ? payload.scenarios : [];
        if (!payload.enabled || !scenarios.length) throw new Error("developer debug mode is unavailable");
        select.innerHTML = scenarios.map((scenario) => `<option value="${escapeHtml(scenario.scenario_id)}">${escapeHtml(scenario.title)}</option>`).join("");
        select.disabled = false;
        button.disabled = false;
        controls.hidden = false;
        status.textContent = "本地调试模式已启用，加载不会改写工作区供应链数据。";
    } catch (error) {
        controls.hidden = true;
        select.innerHTML = "<option value=\"\">调试模式未启用</option>";
        select.disabled = true;
        button.disabled = true;
        status.textContent = "";
    }
}

async function loadSelectedDeveloperDebugScenario() {
    const select = document.getElementById("supply-debug-scenario");
    const button = document.getElementById("supply-debug-load");
    const status = document.getElementById("supply-debug-status");
    if (!select?.value || !button || !status) return;
    const originalLabel = button.textContent;
    button.disabled = true;
    button.textContent = "加载中";
    status.textContent = "正在创建隔离调试运行。";
    try {
        const run = await fetchBackendJson(`/developer-debug/scenarios/${encodeURIComponent(select.value)}/runs`, {
            method: "POST", timeoutMs: 10000,
        });
        const [context, liveSnapshot] = await Promise.all([
            fetchBackendJson(`/developer-debug/runs/${encodeURIComponent(run.run_id)}/context`, { timeoutMs: 10000 }),
            fetchBackendJson(`/developer-debug/runs/${encodeURIComponent(run.run_id)}/live-snapshot`, { method: "POST", timeoutMs: 40000 }),
        ]);
        applyDeveloperDebugContext(context, liveSnapshot);
        supplyState.source = "developer_debug";
        supplyState.debugRunId = run.run_id;
        supplyState.selectedLocation = null;
        supplyState.selectedSupplierId = null;
        document.getElementById("supply-add-button").disabled = true;
        document.getElementById("supply-source-status").textContent = `开发者隔离运行：${run.run_id}`;
        status.textContent = `已加载全生命周期隔离场景：${run.title} · 测试主体 ${liveSnapshot.selection.name}（${liveSnapshot.selection.security_code}）。`;
    } catch (error) {
        console.info(error);
        status.textContent = "加载失败，请确认后端已以开发者调试模式启动。";
    } finally {
        button.disabled = false;
        button.textContent = originalLabel;
    }
}

function applyDeveloperDebugContext(context, liveSnapshot) {
    developerDebugState.context = context;
    const supply = context?.supply_chain || {};
    supplyState.suppliers = Array.isArray(supply.suppliers) ? supply.suppliers : [];
    activeRiskIntakeCompanyId = context?.risk_intake?.scope?.company_id || activeRiskIntakeCompanyId;
    backendState.riskIntake = context?.risk_intake || null;
    backendState.internalRisk = { data: context?.internal_risk || {}, meta: { data_source: "developer_debug" } };
    backendState.product.lifecycleRisk = { data: context?.lifecycle_product || context?.lifecycle?.product || context?.lifecycle || {} };
    const externalRisk = liveSnapshot?.external_risk || {};
    applyExternalRiskDashboardData({ ...externalRisk, debug_scenario: true }, { data_source: externalRisk?.summary?.data_mode || "unavailable_live_provider" });
    workflowState.quotes.clear();
    applyDebugWorkflowGraph(liveSnapshot);
    if (liveSnapshot?.quote?.symbol) {
        quoteState.requestId += 1;
        quoteState.symbol = liveSnapshot.quote.symbol;
        quoteState.manualUntil = Date.now() + 8000;
        resetQuoteWindow();
        syncQuoteSymbolSelect(quoteState.symbol);
        renderQuoteSeries(liveSnapshot.quote);
    }
    void refreshWorkflowQuotes();
    renderSupplyWorkspace();
    renderInternalRiskDashboard(backendState.internalRisk.data);
    renderRiskGovernanceDashboard(backendState.internalRisk.data);
    renderInternalRiskWorkspace(backendState.internalRisk.data, backendState.internalRisk.meta);
    renderLifecycle();
}


restoreSidebarState();
restoreDismissedNavBadges();
renderLifecycle();
renderChinaMap();
setupMapZoomControls();
setupSupplierContextMenu();
setupSupplyFormulaPopover();
setupLegalChat();
setupDocumentUpload();
setupExternalRiskControls();
setupQuoteControls();
setupGlobalSearch();
setupRuntimeSettings();
setupSkillsWorkspace();
startQuoteAutoRefresh();
refreshQuoteSeries();
setupWorkflowControls();
setupSupplyChainWorkspace();
setupInternalRiskControls();
selectRegion("china");
activateInitialTabFromUrl();
refreshDocumentWorkspace();
loadBackendProductData();
loadSupplyChainWorkspace();
loadDeveloperDebugScenarios();
loadInternalRiskWorkflow();
