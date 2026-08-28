/* ==========================================================================
   PSA NEXUS — app.js
   All interactivity: SSE, tabs, HITL, edge controls, history, notifications
   ========================================================================== */

(function () {
  'use strict';

  // ---- State ----
  const state = {
    runId: null,
    activeTab: 'dashboard',
    confidence: null,
    risk: null,
    notifications: [],
    traceEntries: [],
    hitlCard: null,
    hitlTimer: null,
    hitlTimeout: null,
    hitlTimeoutAction: null,
    sseSource: null,
    historyRuns: [],
    mockStatus: 'CLEAN — No injections active',
  };

  // ---- DOM Refs ----
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  const dom = {
    // Header
    problemSelect: $('#problem-select'),
    scoreConfidence: $('#score-confidence'),
    scoreRisk: $('#score-risk'),
    bellBtn: $('#bell-btn'),
    bellBadge: $('#bell-badge'),
    notifPanel: $('#notification-panel'),
    notifList: $('#notification-list'),
    // Tabs
    tabBtns: $$('.tab-btn'),
    panels: $$('.tab-panel'),
    // Demo strip
    scenarioSelect: $('#scenario-select'),
    btnStart: $('#btn-start'),
    btnGear: $('#btn-gear'),
    // Top strip
    stripProblem: $('#strip-problem'),
    stripSystems: $('#strip-systems'),
    // Data viz
    metricCitosContainers: $('#metric-citos-containers'),
    citos40ft: $('#citos-40ft'),
    citos20ft: $('#citos-20ft'),
    citosDg: $('#citos-dg'),
    citosBlocks: $('#citos-blocks'),
    barCitos: $('#bar-citos'),
    statusCitos: $('#status-citos'),

    metricTrucks: $('#metric-trucks'),
    truckFleet: $('#truck-fleet'),
    truckTransit: $('#truck-transit'),
    barTrucks: $('#bar-trucks'),
    statusOptetruck: $('#status-optetruck'),

    metricFeederCapacity: $('#metric-feeder-capacity'),
    feederCap: $('#feeder-cap'),
    feederOcc: $('#feeder-occ'),
    barFeeder: $('#bar-feeder'),
    statusFeeder: $('#status-feeder'),

    metricTuas: $('#metric-tuas'),
    tuasRoad: $('#tuas-road'),
    tuasSea: $('#tuas-sea'),
    tuasTotal: $('#tuas-total'),
    barTuas: $('#bar-tuas'),
    statusTuas: $('#status-tuas'),

    // HITL
    hitlCardBody: $('#hitl-card-body'),
    hitlEmpty: $('#hitl-empty'),
    hitlCardContent: $('#hitl-card-content'),
    hitlActions: $('#hitl-actions'),
    hitlCountdown: $('#hitl-countdown'),
    hitlError: $('#hitl-error'),
    hitlLoading: $('#hitl-loading'),
    btnApprove: $('#btn-approve'),
    btnReject: $('#btn-reject'),
    btnModify: $('#btn-modify'),
    hitlRejectSection: $('#hitl-reject-section'),
    rejectReason: $('#reject-reason'),
    btnSubmitReject: $('#btn-submit-reject'),
    hitlModifySection: $('#hitl-modify-section'),
    modifyFields: $('#modify-fields'),
    modifyReason: $('#modify-reason'),
    btnSubmitModify: $('#btn-submit-modify'),

    // Trace
    traceList: $('#trace-list'),
    traceEmpty: $('#trace-empty'),

    // History
    historyGrid: $('#history-grid'),
    historyEmpty: $('#history-empty'),

    // Sidebar
    sidebarOverlay: $('#sidebar-overlay'),
    sidebar: $('#sidebar'),
    sidebarClose: $('#sidebar-close'),
    sidebarMockStatus: $('#sidebar-mock-status'),
    btnInjectFeeder: $('#btn-inject-feeder'),
    staleMinutes: $('#stale-minutes'),
    btnInjectStale: $('#btn-inject-stale'),
    btnResetMocks: $('#btn-reset-mocks'),
  };

  // ---- Helpers ----
  function apiBase() {
    return window.location.origin;
  }

  function timeAgo(ts) {
    const diff = Date.now() - new Date(ts).getTime();
    if (diff < 60000) return Math.floor(diff / 1000) + 's ago';
    if (diff < 3600000) return Math.floor(diff / 60000) + 'm ago';
    return Math.floor(diff / 3600000) + 'h ago';
  }

  function formatTime(ts) {
    try {
      return new Date(ts).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return '--:--:--';
    }
  }

  function setScoreColor(el, val) {
    el.className = 'score-value';
    if (val === null || val === undefined) {
      el.textContent = '--';
      return;
    }
    el.textContent = typeof val === 'number' ? val.toFixed(2) : val;
    if (typeof val === 'number') {
      if (val >= 0.85) el.classList.add('green');
      else if (val >= 0.70) el.classList.add('amber');
      else el.classList.add('red');
    }
  }

  function setDataBlockStatus(statusEl, barEl, level) {
    statusEl.className = 'data-block-status ' + level;
    statusEl.textContent = level.toUpperCase();
    barEl.className = 'status-bar-fill ' + level;
  }

  // ---- Tabs ----
  function switchTab(tabId) {
    state.activeTab = tabId;
    dom.tabBtns.forEach((btn) => {
      const active = btn.dataset.tab === tabId;
      btn.classList.toggle('active', active);
      btn.setAttribute('aria-selected', active);
    });
    dom.panels.forEach((panel) => {
      const id = panel.id.replace('panel-', '');
      panel.classList.toggle('active', id === tabId);
    });
    if (tabId === 'history') loadHistory();
  }

  dom.tabBtns.forEach((btn) => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
  });

  // ---- Notification Bell ----
  dom.bellBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    dom.notifPanel.classList.toggle('open');
    if (dom.notifPanel.classList.contains('open')) {
      state.notifications = [];
      dom.bellBadge.textContent = '';
      dom.bellBadge.dataset.count = '0';
      renderNotifications();
    }
  });

  document.addEventListener('click', () => {
    dom.notifPanel.classList.remove('open');
  });

  function addNotification(msg, ts) {
    state.notifications.unshift({ msg, ts: ts || new Date().toISOString() });
    if (state.notifications.length > 20) state.notifications.length = 20;
    const count = parseInt(dom.bellBadge.dataset.count || '0') + 1;
    dom.bellBadge.dataset.count = count;
    dom.bellBadge.textContent = count;
    renderNotifications();
  }

  function renderNotifications() {
    if (state.notifications.length === 0) {
      dom.notifList.innerHTML = '<div class="notification-empty">[ NO NOTIFICATIONS ]</div>';
      return;
    }
    dom.notifList.innerHTML = state.notifications
      .map((n) => `<div class="notification-item">${escHtml(n.msg)}<span class="notif-time">${timeAgo(n.ts)}</span></div>`)
      .join('');
  }

  function escHtml(str) {
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
  }

  // ---- Problem Switcher ----
  dom.problemSelect.addEventListener('change', async () => {
    const pid = dom.problemSelect.value;
    try {
      const res = await fetch(apiBase() + '/agent/switch-problem/' + encodeURIComponent(pid), { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        dom.stripProblem.textContent = pid.replace('pb-', 'PB-').replace('-', ' ') + ' COORDINATION';
        renderSystems(data.systems || []);
      }
    } catch (err) {
      console.error('Problem switch failed:', err);
    }
  });

  function renderSystems(systems) {
    dom.stripSystems.innerHTML = systems
      .map((s) => `<span class="system-badge connected">${escHtml(s.toUpperCase())}</span>`)
      .join('');
  }

  // ---- Scenario List ----
  async function loadScenarios() {
    try {
      const res = await fetch(apiBase() + '/agent/scenarios');
      if (!res.ok) return;
      const data = await res.json();
      dom.scenarioSelect.innerHTML = data.scenarios
        .map((s) => `<option value="${escHtml(s.id)}">${escHtml(s.name)} — ${escHtml(s.description)}</option>`)
        .join('');
    } catch (err) {
      console.error('Failed to load scenarios:', err);
    }
  }

  // ---- Active Problem ----
  async function loadActiveProblem() {
    try {
      const res = await fetch(apiBase() + '/agent/active-problem');
      if (!res.ok) return;
      const data = await res.json();
      const pid = data.active_problem_id || 'pb-12-itt';
      dom.problemSelect.value = pid;
      dom.stripProblem.textContent = pid.replace('pb-', 'PB-').replace('-', ' ') + ' COORDINATION';
      renderSystems(data.systems || []);
    } catch (err) {
      console.error('Failed to load active problem:', err);
    }
  }

  // ---- Data Visualizer ----
  async function loadDashboardData() {
    try {
      const [contRes, truckRes, feederRes] = await Promise.allSettled([
        fetch(apiBase() + '/api/citos/ppt/containers?vessel_id=MV%20PACIFIC%20STAR'),
        fetch(apiBase() + '/api/optetruck/capacity'),
        fetch(apiBase() + '/api/feeder/FEEDER%20ATLANTIC-03'),
      ]);

      // CITOS PPT
      if (contRes.status === 'fulfilled' && contRes.value.ok) {
        const d = await contRes.value.json();
        const total = d.total_containers || d.total || 0;
        const fortyft = d.fortyft || d.stats?.fortyft || 0;
        const twentyft = d.twentyft || d.stats?.twentyft || 0;
        const dg = d.dg_containers || d.stats?.dg || 0;
        const blocks = (d.blocks_affected || d.stats?.blocks_affected || []).length;
        dom.metricCitosContainers.textContent = total;
        dom.citos40ft.textContent = fortyft;
        dom.citos20ft.textContent = twentyft;
        dom.citosDg.textContent = dg;
        dom.citosBlocks.textContent = blocks;
        const pct = Math.min(100, (total / 150) * 100);
        dom.barCitos.style.width = pct + '%';
        setDataBlockStatus(dom.statusCitos, dom.barCitos, total > 100 ? 'warning' : 'healthy');
        dom.metricCitosContainers.className = 'data-block-metric ' + (total > 100 ? 'amber' : 'green');
      } else {
        setDataBlockStatus(dom.statusCitos, dom.barCitos, 'critical');
      }

      // OptETruck
      if (truckRes.status === 'fulfilled' && truckRes.value.ok) {
        const d = await truckRes.value.json();
        const avail = d.available_trucks || d.available || 0;
        const fleet = d.total_fleet || d.fleet_size || 55;
        const transit = d.transit_time_minutes || d.transit_time || '--';
        dom.metricTrucks.textContent = avail;
        dom.truckFleet.textContent = fleet;
        dom.truckTransit.textContent = transit;
        const pct = (avail / fleet) * 100;
        dom.barTrucks.style.width = pct + '%';
        const level = pct > 70 ? 'healthy' : pct > 40 ? 'warning' : 'critical';
        setDataBlockStatus(dom.statusOptetruck, dom.barTrucks, level);
        dom.metricTrucks.className = 'data-block-metric ' + (level === 'healthy' ? 'green' : level === 'warning' ? 'amber' : 'red');
      } else {
        setDataBlockStatus(dom.statusOptetruck, dom.barTrucks, 'critical');
      }

      // Feeder
      if (feederRes.status === 'fulfilled' && feederRes.value.ok) {
        const d = await feederRes.value.json();
        const capacity = d.capacity_teu || d.capacity || 800;
        const occupied = d.occupancy_teu || d.occupied || 0;
        const available = capacity - occupied;
        dom.metricFeederCapacity.textContent = available;
        dom.feederCap.textContent = capacity;
        dom.feederOcc.textContent = occupied;
        const pct = (occupied / capacity) * 100;
        dom.barFeeder.style.width = pct + '%';
        const level = pct < 80 ? 'healthy' : pct < 95 ? 'warning' : 'critical';
        setDataBlockStatus(dom.statusFeeder, dom.barFeeder, level);
        dom.metricFeederCapacity.className = 'data-block-metric ' + (level === 'healthy' ? 'green' : level === 'warning' ? 'amber' : 'red');
      } else {
        setDataBlockStatus(dom.statusFeeder, dom.barFeeder, 'critical');
      }

      // Tuas QC — derive from split data or loading sequence
      try {
        const seqRes = await fetch(apiBase() + '/api/citos/tuas/loading-sequence', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ vessel_id: 'MV PACIFIC STAR', containers: [] }),
        });
        if (seqRes.ok) {
          const d = await seqRes.json();
          const totalCost = d.total_cost || d.cost || 0;
          const roadCost = d.road_cost || 0;
          const seaCost = d.sea_handling_cost || d.sea_cost || 0;
          dom.metricTuas.textContent = '$' + totalCost.toLocaleString();
          dom.tuasRoad.textContent = '$' + roadCost.toLocaleString();
          dom.tuasSea.textContent = '$' + seaCost.toLocaleString();
          dom.tuasTotal.textContent = '$' + totalCost.toLocaleString();
          const pct = Math.min(100, (totalCost / 30000) * 100);
          dom.barTuas.style.width = pct + '%';
          setDataBlockStatus(dom.statusTuas, dom.barTuas, 'healthy');
          dom.metricTuas.className = 'data-block-metric green';
        }
      } catch (e) {
        // Tuas block shows fallback
      }
    } catch (err) {
      console.error('Dashboard data load error:', err);
    }
  }

  // ---- Start Demo ----
  dom.btnStart.addEventListener('click', async () => {
    dom.btnStart.disabled = true;
    dom.btnStart.textContent = 'STARTING...';
    resetHITL();

    const scenario = dom.scenarioSelect.value;
    try {
      const res = await fetch(apiBase() + '/agent/run-demo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Failed' }));
        dom.btnStart.disabled = false;
        dom.btnStart.textContent = 'START DEMO';
        showHitlError(err.detail || 'Run failed');
        return;
      }
      const data = await res.json();
      state.runId = data.run_id;

      // If HITL card returned immediately, show it
      if (data.hitl_card) {
        showHitlCard(data.hitl_card);
      }

      // Start SSE
      connectSSE(data.run_id);

      // Refresh dashboard data
      loadDashboardData();

      dom.btnStart.disabled = false;
      dom.btnStart.textContent = 'START DEMO';
    } catch (err) {
      console.error('Start demo error:', err);
      dom.btnStart.disabled = false;
      dom.btnStart.textContent = 'START DEMO';
      showHitlError('Connection failed');
    }
  });

  // ---- SSE ----
  function connectSSE(runId) {
    if (state.sseSource) {
      state.sseSource.close();
    }

    const url = apiBase() + '/agent/stream/' + encodeURIComponent(runId);
    const es = new EventSource(url);
    state.sseSource = es;

    es.onopen = () => {
      console.log('[SSE] Connected for run', runId);
    };

    es.onerror = (e) => {
      console.error('[SSE] Error:', e);
    };

    // Listen for all event types
    const eventTypes = [
      'agent_thinking', 'tool_call', 'tool_result', 'hitl_card',
      'escalation', 'confidence_update', 'trace_entry', 'deviation', 'notification',
    ];

    eventTypes.forEach((type) => {
      es.addEventListener(type, (e) => {
        try {
          const data = JSON.parse(e.data);
          handleSSEEvent(type, data);
        } catch (err) {
          console.error('[SSE] Parse error:', type, err);
        }
      });
    });
  }

  function handleSSEEvent(type, data) {
    switch (type) {
      case 'hitl_card':
        showHitlCard(data);
        break;

      case 'trace_entry':
        addTraceEntry(data);
        break;

      case 'confidence_update':
        state.confidence = data.confidence;
        state.risk = data.risk_score;
        setScoreColor(dom.scoreConfidence, data.confidence);
        setScoreColor(dom.scoreRisk, data.risk_score);
        break;

      case 'deviation':
        addNotification('Deviation: ' + (data.type || data.action_taken || 'Unknown'), data.timestamp);
        break;

      case 'notification':
        addNotification(data.message || 'Notification received', data.timestamp);
        break;

      case 'tool_call':
        addTraceEntry({
          step: state.traceEntries.length + 1,
          node: 'tool',
          action: 'TOOL_CALL: ' + (data.tool_name || ''),
          tool_name: data.tool_name,
          result_summary: JSON.stringify(data.params || {}),
          confidence: state.confidence,
          risk_score: state.risk,
          timestamp: new Date().toISOString(),
        });
        break;

      case 'tool_result':
        addTraceEntry({
          step: state.traceEntries.length + 1,
          node: 'tool',
          action: 'TOOL_RESULT: ' + (data.tool_name || ''),
          tool_name: data.tool_name,
          result_summary: typeof data.output === 'string' ? data.output.substring(0, 200) : JSON.stringify(data.output || {}).substring(0, 200),
          confidence: state.confidence,
          risk_score: state.risk,
          timestamp: new Date().toISOString(),
        });
        break;

      case 'escalation':
        addNotification('ESCALATION: ' + (data.message || JSON.stringify(data)), data.timestamp);
        break;

      case 'agent_thinking':
        addTraceEntry({
          step: state.traceEntries.length + 1,
          node: 'agent',
          action: 'AGENT_THINKING',
          result_summary: data.reasoning || data.thought || 'Processing...',
          confidence: data.confidence || state.confidence,
          risk_score: data.risk_score || state.risk,
          timestamp: new Date().toISOString(),
        });
        break;
    }
  }

  // ---- HITL Card ----
  function showHitlCard(data) {
    state.hitlCard = data;
    dom.hitlEmpty.classList.add('hidden');
    dom.hitlCardContent.classList.remove('hidden');
    dom.hitlActions.classList.remove('hidden');
    dom.hitlError.classList.add('hidden');
    dom.hitlLoading.classList.add('hidden');
    resetHitlInputs();

    const gateId = data.gate_id || '';
    const gateName = data.gate_name || gateId;
    const card = data.approval_card || {};
    const confidence = data.confidence;
    const risk = data.risk_score;
    const timeout = data.timeout_seconds || 60;
    state.hitlTimeoutAction = data.timeout_action;

    let html = `<div class="hitl-gate-name">${escHtml(gateName)}</div>`;

    // Render approval card fields
    const cardKeys = Object.keys(card);
    if (cardKeys.length > 0) {
      html += '<div class="hitl-approval-cards">';
      cardKeys.forEach((key) => {
        const val = typeof card[key] === 'object' ? JSON.stringify(card[key]) : card[key];
        html += `<div class="hitl-approval-card">
          <div class="card-key">${escHtml(key)}</div>
          <div class="card-value">${escHtml(String(val))}</div>
        </div>`;
      });
      html += '</div>';
    }

    // Scores
    html += '<div class="hitl-scores">';
    html += `<div class="score-item"><span class="score-label">CONF</span><span class="score-value ${getColorClass(confidence)}">${confidence !== undefined ? confidence.toFixed(2) : '--'}</span></div>`;
    html += `<div class="score-item"><span class="score-label">RISK</span><span class="score-value ${getColorClass(risk)}">${risk !== undefined ? risk.toFixed(2) : '--'}</span></div>`;
    html += '</div>';

    dom.hitlCardContent.innerHTML = html;

    // Countdown
    startHitlCountdown(timeout);
  }

  function getColorClass(val) {
    if (val === undefined || val === null) return '';
    if (val >= 0.85) return 'green';
    if (val >= 0.70) return 'amber';
    return 'red';
  }

  function startHitlCountdown(seconds) {
    clearHitlCountdown();
    state.hitlTimeout = seconds;
    dom.hitlCountdown.classList.remove('hidden');
    updateCountdownDisplay();

    state.hitlTimer = setInterval(() => {
      state.hitlTimeout--;
      updateCountdownDisplay();
      if (state.hitlTimeout <= 0) {
        clearHitlCountdown();
        showHitlError('HITL timed out — ' + (state.hitlTimeoutAction || 'halted'));
      }
    }, 1000);
  }

  function updateCountdownDisplay() {
    dom.hitlCountdown.textContent = state.hitlTimeout + 's';
  }

  function clearHitlCountdown() {
    if (state.hitlTimer) {
      clearInterval(state.hitlTimer);
      state.hitlTimer = null;
    }
    dom.hitlCountdown.classList.add('hidden');
  }

  function resetHITL() {
    clearHitlCountdown();
    state.hitlCard = null;
    dom.hitlEmpty.classList.remove('hidden');
    dom.hitlCardContent.classList.add('hidden');
    dom.hitlActions.classList.add('hidden');
    dom.hitlError.classList.add('hidden');
    dom.hitlLoading.classList.add('hidden');
    resetHitlInputs();
    dom.hitlCardContent.innerHTML = '';
  }

  function resetHitlInputs() {
    dom.hitlRejectSection.classList.remove('open');
    dom.hitlModifySection.classList.remove('open');
    dom.rejectReason.value = '';
    dom.modifyReason.value = '';
    dom.modifyFields.innerHTML = '';
  }

  function showHitlError(msg) {
    dom.hitlError.textContent = msg;
    dom.hitlError.classList.remove('hidden');
    dom.hitlLoading.classList.add('hidden');
  }

  // ---- HITL Actions ----
  dom.btnApprove.addEventListener('click', () => submitHITL('approve'));
  dom.btnReject.addEventListener('click', () => {
    dom.hitlRejectSection.classList.toggle('open');
    dom.hitlModifySection.classList.remove('open');
  });
  dom.btnModify.addEventListener('click', () => {
    dom.hitlModifySection.classList.toggle('open');
    dom.hitlRejectSection.classList.remove('open');
    renderModifyFields();
  });

  dom.btnSubmitReject.addEventListener('click', () => {
    submitHITL('reject', { reason: dom.rejectReason.value });
  });

  dom.btnSubmitModify.addEventListener('click', () => {
    const mods = collectModifyFields();
    submitHITL('modify', { reason: dom.modifyReason.value, modifications: mods });
  });

  function renderModifyFields() {
    if (!state.hitlCard) return;
    const card = state.hitlCard.approval_card || {};
    const keys = Object.keys(card);
    if (keys.length === 0) {
      dom.modifyFields.innerHTML = '<div class="data-block-label">No editable fields in this card</div>';
      return;
    }
    dom.modifyFields.innerHTML = keys
      .map((key) => {
        const val = typeof card[key] === 'object' ? JSON.stringify(card[key]) : String(card[key]);
        return `<div class="hitl-modify-field">
          <label for="mod-${key}">${escHtml(key)}</label>
          <input type="text" id="mod-${key}" data-key="${escHtml(key)}" value="${escHtml(val)}">
        </div>`;
      })
      .join('');
  }

  function collectModifyFields() {
    const mods = {};
    dom.modifyFields.querySelectorAll('input').forEach((input) => {
      mods[input.dataset.key] = input.value;
    });
    return mods;
  }

  async function submitHITL(decision, extra) {
    if (!state.runId || !state.hitlCard) return;

    dom.hitlLoading.classList.remove('hidden');
    dom.hitlActions.classList.add('hidden');
    dom.hitlError.classList.add('hidden');

    const payload = {
      run_id: state.runId,
      decision: decision,
      gate_id: state.hitlCard.gate_id,
      ...extra,
    };

    try {
      const res = await fetch(apiBase() + '/agent/hitl/respond', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Request failed' }));
        dom.hitlLoading.classList.add('hidden');
        showHitlError(err.detail || 'HITL response failed');
        return;
      }

      const data = await res.json();
      clearHitlCountdown();

      // If another HITL card returned, show it
      if (data.status === 'waiting_hitl' && data.hitl_card) {
        showHitlCard(data.hitl_card);
        dom.hitlLoading.classList.add('hidden');
        return;
      }

      // Run completed or moved on
      dom.hitlLoading.classList.add('hidden');
      resetHITL();

      // Update scores from returned state
      if (data.result) {
        if (data.result.confidence !== undefined) {
          state.confidence = data.result.confidence;
          setScoreColor(dom.scoreConfidence, data.result.confidence);
        }
        if (data.result.risk_score !== undefined) {
          state.risk = data.result.risk_score;
          setScoreColor(dom.scoreRisk, data.result.risk_score);
        }
      }

      addNotification('HITL ' + decision.toUpperCase() + ' — ' + (state.hitlCard.gate_name || ''), new Date().toISOString());
      loadHistory();
    } catch (err) {
      console.error('HITL submit error:', err);
      dom.hitlLoading.classList.add('hidden');
      showHitlError('Connection error');
    }
  }

  // ---- Agent Trace ----
  function addTraceEntry(entry) {
    // Dedup by step+action+timestamp
    const key = entry.step + '|' + entry.action + '|' + entry.timestamp;
    if (state.traceEntries.find((e) => e.step === entry.step && e.action === entry.action)) {
      return;
    }
    state.traceEntries.push(entry);
    renderTraceEntry(entry);
  }

  function renderTraceEntry(entry) {
    dom.traceEmpty.style.display = 'none';

    const el = document.createElement('div');
    el.className = 'trace-entry';

    const isHitl = entry.action && entry.action.toUpperCase().includes('HITL');
    const isComplete = entry.action && entry.action.toUpperCase().includes('COMPLETE');
    let badgeClass = '';
    if (isHitl) badgeClass = 'hitl';
    else if (isComplete) badgeClass = 'complete';

    el.innerHTML = `
      <div class="trace-entry-header">
        <div class="trace-step-badge ${badgeClass}">${entry.step || ''}</div>
        <div class="trace-action">${escHtml(entry.action || '')}</div>
        <div class="trace-summary">${escHtml(entry.result_summary || '')}</div>
        <div class="trace-time">${formatTime(entry.timestamp)}</div>
      </div>
      <div class="trace-detail">
        <pre>${escHtml(JSON.stringify(entry, null, 2))}</pre>
      </div>
    `;

    el.querySelector('.trace-entry-header').addEventListener('click', () => {
      el.classList.toggle('expanded');
    });

    dom.traceList.appendChild(el);

    // Auto-scroll if at bottom
    const container = dom.traceList.parentElement;
    if (container.scrollHeight - container.scrollTop - container.clientHeight < 100) {
      container.scrollTop = container.scrollHeight;
    }
  }

  // ---- History ----
  async function loadHistory() {
    try {
      const res = await fetch(apiBase() + '/webhook/runs');
      if (!res.ok) return;
      const data = await res.json();
      state.historyRuns = data.runs || [];
      renderHistory();
    } catch (err) {
      console.error('History load error:', err);
    }
  }

  function renderHistory() {
    if (state.historyRuns.length === 0) {
      dom.historyEmpty.style.display = '';
      dom.historyGrid.innerHTML = '';
      dom.historyGrid.appendChild(dom.historyEmpty);
      return;
    }

    dom.historyEmpty.style.display = 'none';
    dom.historyGrid.innerHTML = '';

    state.historyRuns.slice().reverse().forEach((run) => {
      const card = document.createElement('div');
      card.className = 'history-card';

      const status = run.status || 'unknown';
      const statusClass = ['completed', 'waiting_hitl', 'halted', 'failed', 'running', 'accepted'].includes(status) ? status : '';
      const problem = run.event?.event_type || run.scenario || '';
      const ts = run.event?.timestamp || run.timestamp || '';
      const runId = run.run_id || '';
      const summary = run.hitl_card
        ? 'HITL gate: ' + (run.hitl_card.gate_name || run.hitl_card.gate_id || '')
        : status === 'completed'
        ? 'Run completed successfully'
        : status === 'waiting_hitl'
        ? 'Awaiting HITL approval'
        : 'Status: ' + status;

      card.innerHTML = `
        <div class="history-card-header">
          <span class="history-run-id">${escHtml(runId.substring(0, 20))}</span>
          <span class="history-status ${statusClass}">${escHtml(status.toUpperCase())}</span>
        </div>
        <div class="history-card-body">
          <div class="history-problem">${escHtml(problem)}</div>
          <div class="history-timestamp">${ts ? timeAgo(ts) : '--'}</div>
          <div class="history-summary">${escHtml(summary)}</div>
        </div>
        <div class="history-detail">
          <pre>${escHtml(JSON.stringify(run, null, 2))}</pre>
        </div>
      `;

      card.querySelector('.history-card-header').addEventListener('click', () => {
        card.classList.toggle('expanded');
      });

      dom.historyGrid.appendChild(card);
    });
  }

  // ---- Sidebar ----
  function openSidebar() {
    dom.sidebarOverlay.classList.add('open');
    dom.sidebar.classList.add('open');
    dom.sidebarMockStatus.textContent = state.mockStatus;
  }

  function closeSidebar() {
    dom.sidebarOverlay.classList.remove('open');
    dom.sidebar.classList.remove('open');
  }

  dom.btnGear.addEventListener('click', openSidebar);
  dom.sidebarClose.addEventListener('click', closeSidebar);
  dom.sidebarOverlay.addEventListener('click', closeSidebar);

  dom.btnInjectFeeder.addEventListener('click', async () => {
    try {
      const res = await fetch(apiBase() + '/agent/inject-edge-case', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ case: 'feeder_berth_conflict' }),
      });
      if (res.ok) {
        state.mockStatus = 'FEEDER BERTH CONFLICT INJECTED';
        dom.sidebarMockStatus.textContent = state.mockStatus;
        addNotification('Edge injected: feeder berth conflict', new Date().toISOString());
      }
    } catch (err) {
      console.error('Inject feeder error:', err);
    }
  });

  dom.btnInjectStale.addEventListener('click', async () => {
    const minutes = parseInt(dom.staleMinutes.value) || 25;
    try {
      const res = await fetch(apiBase() + '/agent/inject-edge-case', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ case: 'stale_data', minutes }),
      });
      if (res.ok) {
        state.mockStatus = 'STALE DATA INJECTED — ' + minutes + 'min offset';
        dom.sidebarMockStatus.textContent = state.mockStatus;
        addNotification('Edge injected: stale data (' + minutes + 'min)', new Date().toISOString());
      }
    } catch (err) {
      console.error('Inject stale error:', err);
    }
  });

  dom.btnResetMocks.addEventListener('click', async () => {
    try {
      const res = await fetch(apiBase() + '/agent/reset-mocks', { method: 'POST' });
      if (res.ok) {
        state.mockStatus = 'CLEAN — No injections active';
        dom.sidebarMockStatus.textContent = state.mockStatus;
        addNotification('Mocks reset to clean state', new Date().toISOString());
      }
    } catch (err) {
      console.error('Reset mocks error:', err);
    }
  });

  // ---- Init ----
  loadActiveProblem();
  loadScenarios();
  loadDashboardData();
  loadHistory();
})();
