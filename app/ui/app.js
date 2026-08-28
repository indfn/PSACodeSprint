let currentRunId = null;
let eventSource = null;
const _hitlTimers = {};
let notifCount = 0;

const PROBLEM_LABELS = {
  "pb-12-itt": "PB-12 \u2014 ITT Coordination (Flagship)",
  "pb-01-berth": "PB-01 \u2014 Berth Delay Cascade",
  "pb-02-dtqc": "PB-02 \u2014 DTQC Contamination",
  "pb-04-feeder": "PB-04 \u2014 Feeder Schedule Cascade",
  "pb-09-expressway": "PB-09 \u2014 Expressway Gridlock",
  "pb-10-sea-air": "PB-10 \u2014 Sea-Air Bifurcation",
  "pb-11-customs": "PB-11 \u2014 Customs Clearance Block",
};

const STEPS = ["Ingest","Query PPT","Query Road","Query Sea","Optimize","HITL-1","HITL-2","HITL-3","Dispatch","Tuas Update","HITL-4","Monitor","Re-plan","HITL-5","Delta Dispatch","Final Tuas","Complete"];
let _stepIdx = 0;

function populateProblemSelect() {
  const sel = document.getElementById("problem-select");
  if (!sel) return;
  sel.innerHTML = "";
  for (const [id, label] of Object.entries(PROBLEM_LABELS)) {
    const opt = document.createElement("option");
    opt.value = id;
    opt.textContent = label;
    sel.appendChild(opt);
  }
}

async function loadActiveProblem() {
  try {
    const res = await fetch("/agent/active-problem");
    if (!res.ok) return;
    const data = await res.json();
    const sel = document.getElementById("problem-select");
    if (data.active_problem_id && sel) sel.value = data.active_problem_id;
    if (data.tools) renderToolChips(data.tools);
    if (data.hitl_gates) renderGateChips(data.hitl_gates);
  } catch (_) {}
}

function renderToolChips(tools) {
  const el = document.getElementById("tool-chips");
  if (!el) return;
  const existing = el.querySelectorAll("[data-chip='gate']");
  existing.forEach((n) => n.remove());
  const base = el.querySelectorAll("[data-chip='tool']");
  base.forEach((n) => n.remove());
  if (!tools || !tools.length) return;
  for (let i = 0; i < tools.length; i++) {
    const s = document.createElement("span");
    s.dataset.chip = "tool";
    s.style.cssText = "display:inline-flex;align-items:center;gap:4px;border-radius:9999px;border:1px solid rgba(255,255,255,0.1);background:rgba(255,255,255,0.05);padding:4px 12px;font-size:11px;font-family:'JetBrains Mono',monospace;color:#CBD5E1;animation:in 300ms both;animation-delay:" + i * 60 + "ms";
    s.textContent = tools[i];
    el.appendChild(s);
  }
}

function renderGateChips(gates) {
  const el = document.getElementById("tool-chips");
  if (!el || !gates) return;
  for (let i = 0; i < gates.length; i++) {
    const s = document.createElement("span");
    s.dataset.chip = "gate";
    s.style.cssText = "display:inline-flex;align-items:center;gap:4px;border-radius:9999px;border:1px solid rgba(245,158,11,0.2);background:rgba(245,158,11,0.1);padding:4px 12px;font-size:11px;font-family:'JetBrains Mono',monospace;color:#FDE68A;animation:in 300ms both;animation-delay:" + (i + 10) * 60 + "ms";
    s.textContent = gates[i];
    el.appendChild(s);
  }
}

function renderProblemBanner(problemId, systems, tools, gates) {
  const wrap = document.getElementById("problem-banner");
  const inner = document.getElementById("problem-banner-inner");
  if (!wrap || !inner) return;
  wrap.style.display = "block";
  const label = PROBLEM_LABELS[problemId] || problemId;
  const sysN = systems ? systems.length : 0;
  const toolN = tools ? tools.length : 0;
  const gateN = gates ? gates.length : 0;
  inner.textContent = "Now running: " + label + " \u2014 " + sysN + " systems, " + toolN + " tools, " + gateN + " gates";
}

async function switchProblem(id) {
  const btn = document.getElementById("switch-problem");
  if (btn) { btn.disabled = true; btn.textContent = "Switching\u2026"; }
  try {
    const res = await fetch("/agent/switch-problem/" + encodeURIComponent(id), { method: "POST" });
    const j = await res.json();
    if (!res.ok) { showError(j.detail || "Switch failed"); return; }
    renderProblemBanner(j.problem_id, j.systems, j.tools, j.hitl_gates);
    renderToolChips(j.tools);
    renderGateChips(j.hitl_gates);
  } catch (e) {
    showError(e.message || "Switch failed");
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = "Switch"; }
  }
}

function updateProgress(stepIdx, label) {
  _stepIdx = stepIdx;
  const el = document.getElementById("agent-status");
  if (el) el.textContent = "Step " + (stepIdx + 1) + "/17: " + label;
  const rail = document.getElementById("progress-rail");
  if (!rail) return;
  rail.innerHTML = "";
  for (let i = 0; i < STEPS.length; i++) {
    const dot = document.createElement("span");
    const done = i <= stepIdx;
    dot.title = STEPS[i];
    dot.style.cssText = "width:20px;height:6px;border-radius:9999px;transition:background 0.4s;" + (done ? "background:#22C55E" : "background:rgba(255,255,255,0.1)");
    dot.dataset.step = String(i);
    rail.appendChild(dot);
  }
}

function showToolSkeletons() {
  const log = document.getElementById("tool-log");
  if (!log) return;
  log.innerHTML = "";
  for (let i = 0; i < 3; i++) {
    const sk = document.createElement("div");
    sk.style.cssText = "height:56px;border-radius:12px;background:rgba(255,255,255,0.05);animation:pulse-dot 1.2s infinite;animation-delay:" + i * 150 + "ms";
    sk.className = "shimmer";
    log.appendChild(sk);
  }
}

function appendAgentOutput(data, isThinking) {
  const el = document.getElementById("agent-output");
  if (!el) return;
  if (el.textContent.includes("No tool calls yet") || el.textContent.trim() === "") el.textContent = "";
  let text = "";
  if (typeof data === "string") text = data;
  else if (data.content) text = data.content;
  else if (data.text) text = data.text;
  else if (data.thinking) text = data.thinking;
  else text = JSON.stringify(data).slice(0, 800);
  const span = document.createElement("span");
  span.textContent = text + " ";
  span.style.animation = "in 200ms both";
  el.appendChild(span);
  el.scrollTop = el.scrollHeight;
}

function appendToolCall(data) {
  const log = document.getElementById("tool-log");
  if (!log) return;
  const skeletons = log.querySelectorAll(".shimmer");
  if (skeletons.length) log.innerHTML = "";
  if (log.textContent.includes("No tool calls yet")) log.innerHTML = "";
  const row = document.createElement("div");
  row.style.cssText = "display:flex;align-items:center;gap:10px;padding:10px 0;border-top:1px solid rgba(255,255,255,0.06);font-size:13px;animation:in 300ms both";
  const toolName = data.tool || data.name || data.tool_name || "tool";
  const args = data.args || data.arguments || data.input || {};
  let argsStr = "";
  try { argsStr = JSON.stringify(args).slice(0, 120); } catch (_) { argsStr = String(args).slice(0, 120); }
  row.innerHTML = '<span style="display:inline-flex;align-items:center;gap:6px"><i class="ph ph-wrench" style="color:#0EA5E9"></i><span class="mono" style="color:#E2E8F0;font-size:12px">' + esc(toolName) + '</span></span><span style="color:#64748B;font-size:11px" class="mono">' + esc(argsStr) + '</span><span style="margin-left:auto;font-size:10px;color:#475569" class="mono">calling\u2026</span>';
  log.appendChild(row);
  log.scrollTop = log.scrollHeight;
}

function appendToolResult(data) {
  const log = document.getElementById("tool-log");
  if (!log) return;
  const toolName = data.tool || data.name || data.tool_name || "tool";
  const result = data.result || data.output || data;
  let outStr = "";
  try {
    const r = result.output !== undefined ? result.output : result;
    outStr = JSON.stringify(r).slice(0, 200);
  } catch (_) { outStr = String(result).slice(0, 200); }
  const rows = log.children;
  let matched = false;
  for (let i = rows.length - 1; i >= 0; i--) {
    if (rows[i].textContent.includes(toolName) && rows[i].textContent.includes("calling")) {
      rows[i].style.opacity = "0.7";
      rows[i].querySelector("span:last-child").textContent = outStr.slice(0, 80);
      rows[i].querySelector("span:last-child").style.color = "#22C55E";
      matched = true;
      break;
    }
  }
  if (!matched) {
    const row = document.createElement("div");
    row.style.cssText = "display:flex;align-items:center;gap:10px;padding:10px 0;border-top:1px solid rgba(255,255,255,0.06);font-size:13px;animation:in 300ms both";
    row.innerHTML = '<span style="display:inline-flex;align-items:center;gap:6px"><i class="ph ph-check-circle" style="color:#22C55E"></i><span class="mono" style="color:#E2E8F0;font-size:12px">' + esc(toolName) + '</span></span><span style="color:#64748B;font-size:11px" class="mono">' + esc(outStr.slice(0, 80)) + '</span>';
    log.appendChild(row);
  }
  if (toolName === "dispatch_road_itt") armEdgeControls();
}

function esc(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

function renderCostSummary(card) {
  const split = card.optimal_split || card.approval_card?.optimal_split || {};
  const cb = card.approval_card?.cost_breakdown || card.cost_breakdown || {};
  const vsBaseline = cb.cost_vs_baseline || {};
  let html = "";
  if (split.road !== undefined || split.sea !== undefined) {
    html += '<span style="color:#E2E8F0">Road ' + (split.road ?? "\u2014") + ' / Sea ' + (split.sea ?? "\u2014") + '</span>';
  }
  if (split.total_transport_cost !== undefined) {
    html += ' <span style="color:#22C55E;font-weight:600">$' + Number(split.total_transport_cost).toLocaleString() + '</span>';
  }
  if (vsBaseline.savings !== undefined) {
    html += ' <span style="color:#94A3B8;font-size:11px">(save $' + Number(vsBaseline.savings).toLocaleString() + ' vs baseline)</span>';
  }
  return html || '<span style="color:#64748B">Cost breakdown pending</span>';
}

function attachHITLHandlers(wrap, card) {
  const approve = wrap.querySelector(".approve");
  const reject = wrap.querySelector(".reject");
  const modify = wrap.querySelector(".modify");
  if (approve) approve.onclick = (e) => respondHITL(card.gate_id, "approve", null, null, e);
  if (reject) reject.onclick = (e) => {
    const reason = prompt("Rejection reason:");
    if (reason === null) return;
    respondHITL(card.gate_id, "reject", reason || "rejected by operator", null, e);
  };
  if (modify) modify.onclick = () => {
    const panel = document.getElementById("modify-" + card.gate_id);
    if (panel) panel.style.display = panel.style.display === "none" ? "block" : "none";
  };
}

function getModifications(gateId) {
  const roadEl = document.getElementById("modify-road-" + gateId);
  const seaEl = document.getElementById("modify-sea-" + gateId);
  const road = parseInt(roadEl?.value) || 0;
  const sea = parseInt(seaEl?.value) || 0;
  return { road, sea };
}

function startCountdown(wrap, timeoutSec, gateId) {
  const el = wrap.querySelector(".countdown");
  if (!el) return;
  let remaining = timeoutSec;
  const fmt = (s) => Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0");
  el.textContent = fmt(remaining);
  const iid = setInterval(() => {
    remaining--;
    if (remaining <= 0) { clearInterval(iid); el.textContent = "0:00 (timed out)"; el.style.color = "#EF4444"; return; }
    el.textContent = fmt(remaining);
  }, 1000);
  _hitlTimers[gateId] = iid;
}

function wrapCountDownCleanup(gateId) {
  if (_hitlTimers[gateId]) { clearInterval(_hitlTimers[gateId]); delete _hitlTimers[gateId]; }
}

function renderHITLCard(card) {
  const list = document.getElementById("hitl-list");
  const empty = document.getElementById("hitl-empty");
  if (!list) return;
  if (empty) empty.style.display = "none";
  const labels = { "HITL-1": "Approve ITT Split", "HITL-2": "Approve Truck Dispatch", "HITL-3": "Approve Feeder Hold", "HITL-4": "Approve Loading Sequence", "HITL-5": "Escalate to Duty Manager" };
  const isEsc = card.gate_id === "HITL-5";
  const timeoutSec = card.timeout_seconds || card.approval_card?.timeout_seconds || 1800;
  const timeoutAction = card.timeout_action || card.approval_card?.timeout_action || "escalate";
  const conf = card.confidence ?? card.approval_card?.confidence ?? 0;
  const risk = card.risk_score ?? card.approval_card?.risk_score ?? 0;
  const gateCard = card.approval_card || card;
  const wrap = document.createElement("div");
  wrap.dataset.gateId = card.gate_id;
  wrap.style.cssText = "position:relative;overflow:hidden;border-radius:1.5rem;border:1px solid rgba(255,255,255,0.1);background:rgba(255,255,255,0.02);padding:20px;transition:border-color 0.2s;animation:in 400ms both;box-shadow:inset 0 1px 0 rgba(255,255,255,0.06)";
  if (isEsc) wrap.style.borderColor = "rgba(239,68,68,0.3)";
  wrap.addEventListener("mousemove", (e) => {
    const r = wrap.getBoundingClientRect();
    wrap.style.setProperty("--mx", (e.clientX - r.left) + "px");
    wrap.style.setProperty("--my", (e.clientY - r.top) + "px");
  });
  const confColor = conf < 0.85 ? "#F59E0B" : "#94A3B8";
  const confIcon = conf < 0.85 ? "warning-circle" : "check-circle";
  wrap.innerHTML =
    '<div style="position:absolute;inset:-1px;opacity:0;transition:opacity 0.3s;pointer-events:none;background:radial-gradient(400px 200px at var(--mx,50%) var(--my,50%), rgba(34,197,94,0.12), transparent 60%)" class="spotlight"></div>' +
    '<div style="display:flex;align-items:flex-start;justify-content:space-between;gap:16px;position:relative">' +
      '<h3 style="font-size:14px;font-weight:600;letter-spacing:-0.02em">' + esc(labels[card.gate_id] || card.gate_name || card.gate_id) + (isEsc ? ' <span style="margin-left:8px;display:inline-flex;align-items:center;gap:4px;border-radius:9999px;background:rgba(239,68,68,0.1);padding:2px 8px;font-size:11px;color:#FCA5A5;border:1px solid rgba(239,68,68,0.2)"><i class="ph ph-warning"></i> Escalation</span>' : "") + '</h3>' +
      '<span class="mono" style="font-size:11px;color:#64748B">' + esc(card.gate_id) + '</span>' +
    '</div>' +
    '<div style="margin-top:12px;display:grid;grid-template-columns:repeat(12,1fr);gap:16px;font-size:13px;position:relative">' +
      '<div style="grid-column:span 12 / span 12;display:flex;flex-direction:column;gap:8px" class="hitl-left">' +
        '<div class="mono" style="font-size:12px">' + renderCostSummary(card) + '</div>' +
        '<div style="display:flex;align-items:center;gap:6px;font-size:11px;color:' + confColor + '"><i class="ph ph-' + confIcon + '" style="font-size:14px"></i> Confidence ' + (conf * 100).toFixed(0) + '% ' + (conf < 0.85 ? "(below threshold \u2014 triggers escalation)" : "") + ' \u00b7 Risk ' + Number(risk).toFixed(2) + '</div>' +
        '<div class="mono" style="font-size:11px;color:#64748B">Timeout ' + Math.round(timeoutSec / 60) + ' min \u2192 ' + esc(timeoutAction) + ' \u00b7 <span class="countdown mono">' + Math.floor(timeoutSec / 60) + ":" + String(timeoutSec % 60).padStart(2, "0") + '</span></div>' +
      '</div>' +
      '<div style="grid-column:span 12 / span 12;display:flex;flex-direction:column;gap:8px" class="hitl-actions">' +
        '<button class="approve" style="display:inline-flex;align-items:center;justify-content:center;gap:8px;border-radius:9999px;background:#22C55E;padding:8px 16px;font-size:13px;font-weight:500;color:#020617;border:none;cursor:pointer;transition:all 0.15s">Approve</button>' +
        '<button class="reject" style="border-radius:9999px;border:1px solid rgba(255,255,255,0.1);background:rgba(255,255,255,0.05);padding:8px 16px;font-size:13px;color:#E2E8F0;cursor:pointer">Reject</button>' +
        '<button class="modify" style="border-radius:9999px;border:1px solid rgba(255,255,255,0.1);background:rgba(255,255,255,0.05);padding:8px 16px;font-size:13px;color:#E2E8F0;cursor:pointer">Modify</button>' +
      '</div>' +
    '</div>' +
    '<div id="modify-' + esc(card.gate_id) + '" style="display:none;margin-top:16px;border-radius:12px;border:1px solid rgba(255,255,255,0.1);background:rgba(0,0,0,0.2);padding:12px">' +
      '<label style="font-size:11px;letter-spacing:0.1em;text-transform:uppercase;color:#94A3B8">Adjust split (road / sea)</label>' +
      '<div style="margin-top:8px;display:grid;grid-template-columns:1fr 1fr;gap:8px">' +
        '<input id="modify-road-' + esc(card.gate_id) + '" type="number" placeholder="Road" style="border-radius:8px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);padding:8px 12px;font-size:13px;color:#F8FAFC;outline:none;width:100%" />' +
        '<input id="modify-sea-' + esc(card.gate_id) + '" type="number" placeholder="Sea" style="border-radius:8px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);padding:8px 12px;font-size:13px;color:#F8FAFC;outline:none;width:100%" />' +
      '</div>' +
      '<button class="modify-submit" data-gate="' + esc(card.gate_id) + '" style="margin-top:8px;border-radius:9999px;background:#22C55E;padding:6px 16px;font-size:13px;font-weight:500;color:#020617;border:none;cursor:pointer">Submit Modification</button>' +
    '</div>';
  list.appendChild(wrap);
  wrap.querySelector(".modify-submit")?.addEventListener("click", (e) => {
    const gid = e.currentTarget.dataset.gate;
    respondHITL(gid, "modify", null, getModifications(gid), e);
  });
  wrap.addEventListener("mouseenter", () => {
    const s = wrap.querySelector(".spotlight");
    if (s) s.style.opacity = "1";
  });
  wrap.addEventListener("mouseleave", () => {
    const s = wrap.querySelector(".spotlight");
    if (s) s.style.opacity = "0";
  });
  attachHITLHandlers(wrap, card);
  startCountdown(wrap, timeoutSec, card.gate_id);
  const style = document.createElement("style");
  style.textContent = "@media(min-width:768px){ .hitl-left{grid-column:span 8 / span 8 !important} .hitl-actions{grid-column:span 4 / span 4 !important} }";
  if (!document.getElementById("hitl-grid-style")) { style.id = "hitl-grid-style"; document.head.appendChild(style); }
}

async function respondHITL(gateId, decision, reason, mods, evt) {
  const btn = evt ? evt.currentTarget : document.querySelector('[data-gate-id="' + gateId + '"] .approve');
  let orig = "";
  if (btn) { orig = btn.textContent; btn.disabled = true; btn.innerHTML = '<span style="display:inline-block;width:14px;height:14px;border:2px solid currentColor;border-top-color:transparent;border-radius:50%;animation:spin 0.6s linear infinite"></span> Sending\u2026'; }
  try {
    const body = { run_id: currentRunId, gate_id: gateId, decision };
    if (reason) body.reason = reason;
    if (mods) body.modifications = mods;
    const r = await fetch("/agent/hitl/respond", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const j = await r.json().catch(() => ({}));
    if (!r.ok && r.status === 422) {
      showError(j.detail || "HITL already timed out (stale)", "alert");
      wrapCountDownCleanup(gateId);
      return;
    }
    if (!r.ok) { showError(j.detail || "HITL request failed", "alert"); if (btn) { btn.disabled = false; btn.textContent = orig; } return; }
    wrapCountDownCleanup(gateId);
    const cardEl = document.querySelector('[data-gate-id="' + gateId + '"]');
    if (cardEl) { cardEl.style.opacity = "0.5"; cardEl.style.pointerEvents = "none"; }
    if (j.status === "waiting_hitl" && j.hitl_card) {
      renderHITLCard(j.hitl_card);
      showBanner("Next approval required: " + (j.hitl_card.gate_id || ""), "info");
    } else if (j.status === "completed" || j.status === "complete") {
      renderCompletion(j.result || j.state || j);
      showBanner("Agent completed successfully", "success");
    } else if (j.hitl_card) {
      renderHITLCard(j.hitl_card);
    }
  } catch (e) {
    if (btn) { btn.disabled = false; btn.textContent = orig; }
    showError(e.message || "Network error", "alert");
  }
}

function renderCompletion(result) {
  const el = document.getElementById("agent-status");
  if (el) el.textContent = "Completed";
  const out = document.getElementById("agent-output");
  if (out) {
    const pre = document.createElement("pre");
    pre.style.cssText = "margin-top:8px;font-size:11px;color:#94A3B8;overflow:auto;white-space:pre-wrap;word-break:break-all;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:12px";
    pre.className = "mono";
    try { pre.textContent = JSON.stringify(result, null, 2).slice(0, 2000); } catch (_) { pre.textContent = String(result).slice(0, 2000); }
    const ok = document.createElement("div");
    ok.style.cssText = "color:#22C55E;font-weight:600;font-size:14px;display:flex;align-items:center;gap:6px";
    ok.innerHTML = '<i class="ph ph-check-circle"></i> Agent completed successfully';
    out.appendChild(ok);
    out.appendChild(pre);
  }
  updateProgress(STEPS.length - 1, "Complete");
}

function showError(msg, type) {
  const banner = document.createElement("div");
  banner.style.cssText = "border-radius:12px;border:1px solid rgba(239,68,68,0.2);background:rgba(239,68,68,0.1);padding:12px 16px;font-size:13px;color:#FECACA;display:flex;align-items:center;gap:8px;margin-top:12px;animation:in 300ms both";
  banner.setAttribute("role", "alert");
  banner.innerHTML = '<i class="ph ph-warning"></i> ' + esc(msg);
  const host = document.getElementById("hitl-cards");
  if (host) host.prepend(banner);
  setTimeout(() => banner.remove(), 8000);
}

function showBanner(msg, type) {
  const isWarn = type === "warning";
  const isErr = type === "alert" || type === "error";
  let bg = "rgba(34,197,94,0.1)", border = "rgba(34,197,94,0.2)", color = "#86EFAC", icon = "check-circle";
  if (isWarn) { bg = "rgba(245,158,11,0.1)"; border = "rgba(245,158,11,0.2)"; color = "#FDE68A"; icon = "warning"; }
  if (isErr) { bg = "rgba(239,68,68,0.1)"; border = "rgba(239,68,68,0.2)"; color = "#FECACA"; icon = "warning-circle"; }
  const banner = document.createElement("div");
  banner.style.cssText = "border-radius:12px;border:1px solid " + border + ";background:" + bg + ";padding:12px 16px;font-size:13px;color:" + color + ";display:flex;align-items:center;gap:8px;margin-top:12px;animation:in 300ms both";
  if (isErr) banner.setAttribute("role", "alert");
  banner.innerHTML = '<i class="ph ph-' + icon + '"></i> ' + esc(msg);
  const host = document.getElementById("hitl-cards");
  if (host) host.prepend(banner);
  setTimeout(() => banner.remove(), 6000);
}

function armEdgeControls() {
  const c = document.getElementById("inject-conflict");
  const s = document.getElementById("inject-stale");
  const hint = document.getElementById("edge-hint");
  if (c) { c.style.background = "rgba(245,158,11,0.1)"; c.style.borderColor = "rgba(245,158,11,0.2)"; c.style.color = "#FDE68A"; c.style.animation = "pulse-dot 1.2s infinite"; }
  if (s) { s.style.background = "rgba(245,158,11,0.08)"; s.style.borderColor = "rgba(245,158,11,0.15)"; }
  if (hint) hint.style.display = "inline";
}

function pulseDeviation() {
  const el = document.getElementById("agent-status");
  if (!el) return;
  el.style.color = "#F59E0B";
  el.style.transition = "color 0.3s";
  setTimeout(() => { el.style.color = ""; }, 2000);
}

function renderTraceEntry(entry) {
  const host = document.getElementById("trace-sidebar");
  const countEl = document.getElementById("trace-count");
  if (!host) return;
  const dotMap = { agent: "#22C55E", tool: "#0EA5E9", hitl: "#F59E0B", escalation: "#EF4444", monitor: "#8B5CF6", deviation: "#F97316", notification: "#E879F9" };
  const color = dotMap[entry.node] || "rgba(255,255,255,0.2)";
  const row = document.createElement("div");
  row.style.cssText = "display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:12px;padding:8px 0;border-top:1px solid rgba(255,255,255,0.05);font-size:11px;animation:in 200ms both";
  const ts = entry.timestamp ? entry.timestamp.slice(11, 19) : "";
  const risk = entry.risk_score ?? entry.result?.risk_score ?? 0;
  const dur = entry.duration_ms ?? 0;
  row.innerHTML =
    '<span style="width:6px;height:6px;border-radius:50%;background:' + color + ';display:inline-block;' + (entry.node === "agent" ? "animation:pulse-dot 1.2s infinite" : "") + '"></span>' +
    '<span class="mono" style="color:#CBD5E1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">' + esc(entry.node || "") + ' \u00b7 ' + esc(entry.action || "") + '</span>' +
    '<span class="mono" style="color:#64748B;white-space:nowrap">' + esc(ts) + ' \u00b7 ' + Number(dur).toFixed(0) + 'ms \u00b7 risk ' + Number(risk).toFixed(2) + '</span>';
  try { row.title = JSON.stringify(entry.result ?? entry, null, 2); } catch (_) {}
  host.appendChild(row);
  host.scrollTop = host.scrollHeight;
  if (countEl) countEl.textContent = host.children.length + " entries";
}

function renderEscalation(data) {
  const msg = data.message || data.reason || JSON.stringify(data).slice(0, 200);
  showBanner("Escalation: " + msg, "warning");
  pulseDeviation();
}

function renderDeviation(data) {
  const msg = data.message || data.deviation || JSON.stringify(data).slice(0, 200);
  showBanner("Deviation detected: " + msg, "warning");
  pulseDeviation();
}

function updateConfidence(data) {
  const scoreEl = document.getElementById("confidence-score");
  const barEl = document.getElementById("confidence-bar");
  const detailEl = document.getElementById("confidence-detail");
  let conf = 0;
  if (typeof data === "number") conf = data;
  else if (data.confidence !== undefined) conf = data.confidence;
  else if (data.score !== undefined) conf = data.score;
  else if (data.value !== undefined) conf = data.value;
  conf = Number(conf) || 0;
  if (scoreEl) scoreEl.textContent = conf.toFixed(2);
  if (barEl) {
    barEl.style.width = (conf * 100).toFixed(0) + "%";
    barEl.style.background = conf < 0.85 ? "#F59E0B" : "#22C55E";
  }
  if (detailEl) detailEl.textContent = conf < 0.85 ? "Below threshold (0.85) \u2014 escalation may trigger" : "Above threshold";
}

let notifBadgeEl = null;
function onNotification(data) {
  notifCount++;
  const panel = document.getElementById("notification-panel");
  const list = document.getElementById("notification-list");
  if (panel) panel.style.display = "block";
  const badge = document.getElementById("notif-badge");
  if (badge) {
    badge.textContent = String(notifCount);
    badge.style.display = "flex";
    badge.animate([{ transform: "scale(0)" }, { transform: "scale(1.2)" }, { transform: "scale(1)" }], { duration: 300, easing: "cubic-bezier(0.16,1,0.3,1)" });
  }
  if (!list) return;
  const li = document.createElement("li");
  li.style.cssText = "display:flex;align-items:center;justify-content:space-between;gap:12px;padding:8px 0;border-top:1px solid rgba(255,255,255,0.06);animation:in 300ms both";
  const parties = Array.isArray(data.parties) ? data.parties : [];
  const pills = parties.map((p) => '<span style="border-radius:9999px;border:1px solid rgba(255,255,255,0.1);background:rgba(255,255,255,0.05);padding:2px 8px;font-size:11px;color:#E2E8F0">' + esc(p) + '</span>').join("");
  const ts = data.timestamp ? data.timestamp.slice(11, 19) : "";
  const msg = data.message || "";
  li.innerHTML = '<span style="display:flex;flex-wrap:wrap;gap:4px">' + pills + '</span><span class="mono" style="font-size:11px;color:#64748B">' + esc(ts) + '</span><span style="font-size:13px;color:#E2E8F0;flex:1;text-align:right">' + esc(msg) + '</span>';
  list.prepend(li);
}

function connectSSE(runId) {
  if (eventSource) { try { eventSource.close(); } catch (_) {} }
  const es = new EventSource("/agent/stream/" + encodeURIComponent(runId));
  eventSource = es;
  es.addEventListener("agent_thinking", (e) => { try { appendAgentOutput(JSON.parse(e.data), true); } catch (_) { appendAgentOutput(e.data, true); } });
  es.addEventListener("tool_call", (e) => { try { appendToolCall(JSON.parse(e.data)); } catch (_) {} });
  es.addEventListener("tool_result", (e) => { try { const d = JSON.parse(e.data); appendToolResult(d); if ((d.tool || d.name) === "dispatch_road_itt") armEdgeControls(); } catch (_) {} });
  es.addEventListener("hitl_card", (e) => { try { renderHITLCard(JSON.parse(e.data)); } catch (_) {} });
  es.addEventListener("escalation", (e) => { try { renderEscalation(JSON.parse(e.data)); } catch (_) {} });
  es.addEventListener("trace_entry", (e) => { try { renderTraceEntry(JSON.parse(e.data)); } catch (_) {} });
  es.addEventListener("deviation", (e) => { try { renderDeviation(JSON.parse(e.data)); pulseDeviation(); } catch (_) {} });
  es.addEventListener("confidence_update", (e) => { try { updateConfidence(JSON.parse(e.data)); } catch (_) {} });
  es.addEventListener("notification", (e) => { try { onNotification(JSON.parse(e.data)); } catch (_) {} });
  es.onerror = () => {
    showError("Stream interrupted \u2014 reconnecting\u2026", "polite");
  };
}

document.getElementById("run-demo")?.addEventListener("click", async () => {
  const btn = document.getElementById("run-demo");
  if (btn) { btn.disabled = true; btn.innerHTML = '<span style="animation:pulse-dot 1s infinite">Launching\u2026</span>'; }
  showToolSkeletons();
  const out = document.getElementById("agent-output");
  if (out) out.textContent = "";
  const hitlList = document.getElementById("hitl-list");
  if (hitlList) hitlList.innerHTML = "";
  const empty = document.getElementById("hitl-empty");
  if (empty) empty.style.display = "none";
  updateProgress(0, "Agent started \u2014 querying CITOS, OptETruck, PORTNET\u2026");
  try {
    const res = await fetch("/agent/run-demo", { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
    const j = await res.json().catch(() => ({}));
    if (!res.ok) { showError(j.detail || "Run failed"); if (btn) { btn.disabled = false; btn.textContent = "Run Demo"; } return; }
    currentRunId = j.run_id;
    connectSSE(j.run_id);
    if (j.status === "waiting_hitl" && j.hitl_card) renderHITLCard(j.hitl_card);
    updateProgress(1, j.status === "waiting_hitl" ? "Awaiting approval \u2014 " + (j.hitl_card?.gate_id || "HITL") : "Running\u2026");
  } catch (e) {
    showError(e.message || "Run failed");
    if (btn) { btn.disabled = false; btn.textContent = "Run Demo"; }
  } finally {
    if (btn) { setTimeout(() => { btn.disabled = false; btn.textContent = "Run Demo"; }, 1000); }
  }
});

document.getElementById("reset")?.addEventListener("click", async () => {
  if (currentRunId) {
    try { await fetch("/agent/reset/" + encodeURIComponent(currentRunId), { method: "POST" }); } catch (_) {}
    try { if (eventSource) eventSource.close(); } catch (_) {}
  }
  try { await fetch("/agent/reset-mocks", { method: "POST" }); } catch (_) {}
  currentRunId = null;
  notifCount = 0;
  const badge = document.getElementById("notif-badge");
  if (badge) { badge.textContent = "0"; badge.style.display = "none"; }
  const p = document.getElementById("notification-panel");
  if (p) p.style.display = "none";
  const nl = document.getElementById("notification-list");
  if (nl) nl.innerHTML = "";
  const tl = document.getElementById("tool-log");
  if (tl) tl.innerHTML = '<div style="font-size:13px;color:#475569;padding:12px 0">No tool calls yet \u2014 run the demo to see orchestration</div>';
  const ts = document.getElementById("trace-sidebar");
  if (ts) ts.innerHTML = "";
  const tc = document.getElementById("trace-count");
  if (tc) tc.textContent = "0 entries";
  const hl = document.getElementById("hitl-list");
  if (hl) hl.innerHTML = "";
  const he = document.getElementById("hitl-empty");
  if (he) he.style.display = "flex";
  const out = document.getElementById("agent-output");
  if (out) out.textContent = "";
  const st = document.getElementById("agent-status");
  if (st) st.textContent = "Idle \u2014 click Run Demo to start";
  const rail = document.getElementById("progress-rail");
  if (rail) rail.innerHTML = "";
  const cs = document.getElementById("confidence-score");
  if (cs) cs.textContent = "\u2014";
  const cb = document.getElementById("confidence-bar");
  if (cb) cb.style.width = "0";
  const cd = document.getElementById("confidence-detail");
  if (cd) cd.textContent = "";
  const cbtn = document.getElementById("inject-conflict");
  if (cbtn) { cbtn.disabled = false; cbtn.style.background = ""; cbtn.style.borderColor = ""; cbtn.style.color = ""; cbtn.style.animation = ""; }
  const sbtn = document.getElementById("inject-stale");
  if (sbtn) { sbtn.disabled = false; sbtn.style.background = ""; sbtn.style.borderColor = ""; sbtn.style.color = ""; }
  const hint = document.getElementById("edge-hint");
  if (hint) hint.style.display = "none";
  for (const k of Object.keys(_hitlTimers)) wrapCountDownCleanup(k);
  showBanner("Reset complete", "info");
});

document.getElementById("inject-conflict")?.addEventListener("click", async () => {
  if (!currentRunId) { showError("Run demo first, then inject"); return; }
  try {
    const r = await fetch("/agent/inject-edge-case", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ run_id: currentRunId, type: "feeder_conflict", feeder_id: "FEEDER ATLANTIC-03", new_departure: "2026-08-19T16:00:00+08:00" }) });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) { showError(j.detail || "Inject failed"); return; }
    showBanner("Feeder berth conflict injected \u2014 monitor will detect on next check", "warning");
    document.getElementById("inject-conflict").disabled = true;
  } catch (e) { showError(e.message); }
});

document.getElementById("inject-stale")?.addEventListener("click", async () => {
  if (!currentRunId) { showError("Run demo first, then inject"); return; }
  try {
    const r = await fetch("/agent/inject-edge-case", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ run_id: currentRunId, type: "stale_data", minutes: 35 }) });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) { showError(j.detail || "Inject failed"); return; }
    showBanner("Stale data injected \u2014 next query will see aged data", "warning");
    document.getElementById("inject-stale").disabled = true;
  } catch (e) { showError(e.message); }
});

document.getElementById("switch-problem")?.addEventListener("click", () => {
  const sel = document.getElementById("problem-select");
  if (sel) switchProblem(sel.value);
});

populateProblemSelect();
loadActiveProblem();

const _spin = document.createElement("style");
_spin.textContent = "@keyframes spin{to{transform:rotate(360deg)}}";
document.head.appendChild(_spin);
