const internalRiskDemo = {
    gates: [
        { id: "gate-data", stage: "模型训练前", title: "客户数据训练与境外云服务核验", risk: "high", decision: "remediation_required", owner: "数据治理负责人", due: "8月3日", missing: 1, risks: ["数据出境", "模型训练数据"] },
        { id: "gate-api", stage: "商业化前", title: "第三方大模型 API 接入审查", risk: "medium", decision: "conditional", owner: "产品合规负责人", due: "8月6日", missing: 2, risks: ["客户数据", "合同责任"] },
        { id: "gate-ip", stage: "离职交接", title: "核心算法资产与开源组件交接", risk: "high", decision: "hold", owner: "研发负责人", due: "今天", missing: 2, risks: ["商业秘密", "开源许可证"] }
    ],
    ledger: [
        { id: "ir-data-001", title: "训练数据同步至境外云服务的合规风险", domain: "数据与模型治理", level: "high", stage: "模型训练前", status: "整改中", fact: "客户数据处理目的、境外接收方安全义务与评估材料尚未完整留存。", evidence: "3 项证据 / 1 项缺口", tasks: "2 项整改", review: "必须复核", updated: "今天 10:20" },
        { id: "ir-api-002", title: "第三方大模型 API 的数据责任边界不清", domain: "产品商业化", level: "medium", stage: "商业化前", status: "待补充材料", fact: "客户数据、提示词及模型输出的处理角色与留存规则尚未在合同中明确。", evidence: "2 项证据 / 2 项缺口", tasks: "1 项整改", review: "建议复核", updated: "昨天 16:40" },
        { id: "ir-ip-003", title: "离职员工接触模型权重与未审查开源组件", domain: "技术与知识资产", level: "high", stage: "人员变动", status: "暂缓放行", fact: "权限回收、代码资产核验和开源许可证核查尚未完成。", evidence: "2 项证据 / 2 项缺口", tasks: "2 项整改", review: "必须复核", updated: "今天 09:10" }
    ],
    tasks: [
        { id: "task-001", title: "补充数据授权与出境评估材料", risk: "ir-data-001", owner: "数据治理组", due: "8月3日", status: "in_progress", evidence: "授权书、评估记录、云服务条款" },
        { id: "task-002", title: "核验境外接收方安全义务", risk: "ir-data-001", owner: "法务合规", due: "8月3日", status: "open", evidence: "数据处理协议、技术安全说明" },
        { id: "task-003", title: "补充第三方模型数据处理条款", risk: "ir-api-002", owner: "产品与采购", due: "8月6日", status: "submitted", evidence: "合同红线稿、供应商确认函" },
        { id: "task-004", title: "完成模型权重与代码资产交接核验", risk: "ir-ip-003", owner: "研发负责人", due: "今天", status: "overdue", evidence: "权限回收记录、代码仓审计记录" }
    ],
    reviews: [
        { id: "review-001", risk: "ir-data-001", title: "境外云服务模型训练放行复核", level: "high", trigger: "高风险且缺少出境评估材料", suggestion: "整改后复核", evidence: "个人信息保护法相关条款、数据流程图、云服务合同", reviewer: "法务/数据合规负责人", status: "in_review", note: "等待补充境外接收方安全义务证明。" },
        { id: "review-002", risk: "ir-ip-003", title: "核心算法人员离职交接复核", level: "high", trigger: "核心技术资产与开源合规风险并存", suggestion: "暂缓推进", evidence: "权限清单、代码提交记录、开源组件清单", reviewer: "研发负责人/法务", status: "required", note: "需要先完成权限回收与组件许可证核查。" }
    ]
};

const viewLabels = { gates: "风险闸门", ledger: "风险台账", tasks: "整改任务", reviews: "人工复核" };
const riskLabel = { low: "低风险", medium: "中风险", high: "高风险", critical: "重大风险" };
const decisionLabel = { approved: "可放行", conditional: "附条件放行", remediation_required: "整改后复核", hold: "暂缓推进" };
const taskColumn = { open: "待开始", in_progress: "处理中", submitted: "待验收", overdue: "已逾期" };
const taskStatusLabel = { open: "待开始", in_progress: "处理中", submitted: "待验收", overdue: "已逾期" };
const reviewStatusLabel = { in_review: "复核中", required: "待复核" };

function renderGateSummary() {
    document.getElementById("gate-summary").innerHTML = `
        <div class="summary-lead"><div class="summary-label">当前重点</div><div class="summary-value">2 个节点不可放行</div><div class="summary-note">高风险事项必须完成材料补充和人工复核后，才可进入下一阶段。</div></div>
        <div><div class="summary-label">待复核</div><div class="summary-value">2</div><div class="summary-note">需要法务或合规负责人确认</div></div>
        <div><div class="summary-label">材料缺口</div><div class="summary-value">5</div><div class="summary-note">数据、合同与资产交接证明</div></div>
        <div><div class="summary-label">逾期任务</div><div class="summary-value">1</div><div class="summary-note">核心算法资产交接核验</div></div>`;
}

function renderGates() {
    document.getElementById("gate-list").innerHTML = internalRiskDemo.gates.map((gate) => `
        <article class="gate-card">
            <div class="gate-card-header"><span class="stage-label">${gate.stage}</span><span class="risk-pill risk-${gate.risk}">${riskLabel[gate.risk]}</span></div>
            <h3>${gate.title}</h3><p>${gate.risks.join(" · ")}</p>
            <div class="gate-card-footer"><span class="decision-pill decision-${gate.decision}">${decisionLabel[gate.decision]}</span><button class="open-detail" type="button" data-gate-id="${gate.id}">查看核验项</button></div>
        </article>`).join("");
}

function openGateDetail(gateId) {
    const gate = internalRiskDemo.gates.find((item) => item.id === gateId) || internalRiskDemo.gates[0];
    const drawer = document.getElementById("gate-detail");
    drawer.hidden = false;
    drawer.innerHTML = `<div class="row-meta"><div><span class="meta-label">${gate.stage} · ${riskLabel[gate.risk]}</span><h3>${gate.title}</h3></div><span class="decision-pill decision-${gate.decision}">${decisionLabel[gate.decision]}</span></div>
        <div class="detail-grid"><div class="detail-group"><h3>需核验材料</h3><ul><li>业务与数据处理流程图</li><li>授权或处理基础证明</li><li>关键技术资产清单</li></ul></div><div class="detail-group"><h3>当前缺口</h3><ul><li>缺少 ${gate.missing} 项关键材料</li><li>责任人：${gate.owner}</li><li>完成期限：${gate.due}</li></ul></div><div class="detail-group"><h3>放行规则</h3><ul><li>RAG 研判仅作为辅助依据</li><li>高风险必须人工复核</li><li>整改证据验收后才可更新结论</li></ul></div></div>`;
    drawer.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function renderLedger() {
    document.getElementById("ledger-list").innerHTML = internalRiskDemo.ledger.map((risk) => `
        <article class="ledger-row"><div><div class="ledger-title">${risk.title}</div><div class="ledger-fact">${risk.fact}</div></div><div class="inline-meta"><strong>${risk.domain}</strong>${risk.stage}</div><div><span class="risk-pill risk-${risk.level}">${riskLabel[risk.level]}</span><div class="inline-meta" style="margin-top:7px">${risk.status}</div></div><div class="inline-meta"><strong>${risk.review}</strong>${risk.evidence}<br>${risk.tasks}<br>${risk.updated}</div></article>`).join("");
}

function renderTasks() {
    const columns = Object.keys(taskColumn).map((status) => {
        const tasks = internalRiskDemo.tasks.filter((task) => task.status === status);
        return `<section class="task-column"><h2>${taskColumn[status]}<span class="task-count">${tasks.length}</span></h2>${tasks.map((task) => `<article class="task-card"><h3>${task.title}</h3><p>责任人：${task.owner}<br>需举证：${task.evidence}</p><div class="task-card-footer"><span>${task.due}</span><span class="status-pill status-${task.status}">${taskStatusLabel[task.status]}</span></div></article>`).join("") || '<p style="padding:8px">暂无任务</p>'}</section>`;
    });
    document.getElementById("task-board").innerHTML = columns.join("");
}

function renderReviews() {
    document.getElementById("review-list").innerHTML = internalRiskDemo.reviews.map((review) => `
        <article class="review-card"><div class="review-head"><div><span class="meta-label">${review.risk}</span><h3>${review.title}</h3><p>${review.trigger}</p></div><span class="risk-pill risk-${review.level}">${reviewStatusLabel[review.status]}</span></div>
        <dl class="review-columns"><div class="review-field"><dt>AI/RAG 建议</dt><dd>${review.suggestion}</dd></div><div class="review-field"><dt>可复核依据</dt><dd>${review.evidence}</dd></div><div class="review-field"><dt>复核人</dt><dd>${review.reviewer}<br>${review.note}</dd></div></dl>
        <div class="review-action-row"><button class="btn" type="button" data-review-action="return">退回整改</button><button class="btn btn-primary" type="button" data-review-action="approve">记录复核决定</button></div></article>`).join("");
}

function switchInternalView(view) {
    document.querySelectorAll(".internal-risk-page .nav-item").forEach((item) => item.classList.toggle("active", item.dataset.view === view));
    document.querySelectorAll(".internal-view").forEach((section) => section.classList.toggle("active", section.id === `view-${view}`));
    document.getElementById("breadcrumb").textContent = viewLabels[view];
}

document.querySelectorAll(".internal-risk-page .nav-item").forEach((item) => item.addEventListener("click", () => switchInternalView(item.dataset.view)));
document.getElementById("gate-list").addEventListener("click", (event) => { const button = event.target.closest("[data-gate-id]"); if (button) openGateDetail(button.dataset.gateId); });
document.getElementById("open-gate-detail").addEventListener("click", () => openGateDetail("gate-data"));
document.getElementById("review-list").addEventListener("click", (event) => { const button = event.target.closest("[data-review-action]"); if (button) button.textContent = button.dataset.reviewAction === "approve" ? "已记录（演示）" : "已退回（演示）"; });

renderGateSummary();
renderGates();
renderLedger();
renderTasks();
renderReviews();
