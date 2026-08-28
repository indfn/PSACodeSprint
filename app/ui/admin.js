async function adminLogin() {
  const user = document.getElementById("login-user").value.trim();
  const pass = document.getElementById("login-pass").value;
  const errEl = document.getElementById("login-error");
  try {
    const r = await fetch("/api/admin/login", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: user, password: pass }),
    });
    if (r.ok) {
      document.getElementById("login-screen").style.display = "none";
      const cs = document.getElementById("config-screen");
      cs.style.display = "flex";
      if (errEl) { errEl.style.display = "none"; errEl.textContent = ""; }
      loadConfig();
    } else {
      const j = await r.json().catch(() => ({}));
      if (errEl) { errEl.textContent = j.detail || "Invalid credentials"; errEl.style.display = "block"; }
    }
  } catch (e) {
    if (errEl) { errEl.textContent = "Network error: " + (e.message || e); errEl.style.display = "block"; }
  }
}

async function loadConfig() {
  try {
    const r = await fetch("/api/admin/config", { credentials: "same-origin" });
    if (r.status === 401 || r.status === 403) {
      document.getElementById("login-screen").style.display = "block";
      document.getElementById("config-screen").style.display = "none";
      return;
    }
    if (!r.ok) return;
    const data = await r.json();
    const llm = data.llm || {};
    const el = (id) => document.getElementById(id);
    if (el("cfg-provider")) el("cfg-provider").value = llm.provider || "anthropic";
    if (el("cfg-model")) el("cfg-model").value = llm.model || "";
    if (el("cfg-base-url")) el("cfg-base-url").value = llm.base_url || "";
    if (el("cfg-api-type")) el("cfg-api-type").value = llm.api_type || "openai";
    if (el("cfg-fallback-model")) el("cfg-fallback-model").value = llm.fallback_model || "";
    if (el("cfg-threshold") && data.active_problem) el("cfg-threshold").value = data.active_problem.confidence_threshold ?? 0.85;

    const ks = document.getElementById("api-key-status");
    if (ks) {
      const status = data.api_key_status || {};
      ks.innerHTML = Object.entries(status).map(([k, v]) => {
        const cls = v === "set" ? "color:#22C55E" : "color:#F59E0B";
        return '<span><span style="color:#64748B">' + esc(k) + ':</span> <span style="' + cls + '">' + esc(v) + '</span></span>';
      }).join(" \u00b7 ") || '<span style="color:#475569">No keys configured</span>';
    }

    const rb = document.getElementById("readiness-banner");
    const pr = data.provider_readiness;
    if (rb && pr) {
      rb.style.display = "block";
      if (pr.ready) {
        rb.style.background = "rgba(34,197,94,0.1)";
        rb.style.border = "1px solid rgba(34,197,94,0.2)";
        rb.style.color = "#86EFAC";
        rb.innerHTML = '<i class="ph ph-check-circle"></i> ' + esc(pr.message || "Ready");
      } else {
        rb.style.background = "rgba(245,158,11,0.1)";
        rb.style.border = "1px solid rgba(245,158,11,0.2)";
        rb.style.color = "#FDE68A";
        rb.innerHTML = '<i class="ph ph-warning-circle"></i> ' + esc(pr.message || "Key missing");
      }
    }

    loadProblemConfig();
  } catch (_) {}
}

async function loadProblemConfig() {
  try {
    const r = await fetch("/api/admin/config/problem", { credentials: "same-origin" });
    if (!r.ok) return;
    const data = await r.json();
    const el = document.getElementById("problem-config-display");
    if (el) el.textContent = JSON.stringify(data, null, 2);
  } catch (_) {}
}

function esc(s) { const d = document.createElement("div"); d.textContent = s; return d.innerHTML; }

async function saveConfig() {
  const btn = document.getElementById("cfg-save");
  const status = document.getElementById("cfg-status");
  if (btn) { btn.disabled = true; btn.textContent = "Saving\u2026"; }
  try {
    const provider = document.getElementById("cfg-provider").value;
    const model = document.getElementById("cfg-model").value.trim();
    const baseUrl = document.getElementById("cfg-base-url").value.trim();
    const apiType = document.getElementById("cfg-api-type").value;
    const fallbackModel = document.getElementById("cfg-fallback-model").value.trim();
    const thresholdRaw = document.getElementById("cfg-threshold").value;
    const threshold = thresholdRaw ? parseFloat(thresholdRaw) : undefined;
    const body = { llm: {} };
    if (provider) body.llm.provider = provider;
    if (model) body.llm.model = model;
    if (baseUrl !== undefined) body.llm.base_url = baseUrl;
    if (apiType) body.llm.api_type = apiType;
    if (fallbackModel) body.llm.fallback_model = fallbackModel;
    if (threshold !== undefined && !isNaN(threshold)) body.confidence_threshold = threshold;
    const r = await fetch("/api/admin/config", {
      method: "POST", credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const j = await r.json().catch(() => ({}));
    if (status) {
      if (r.ok) { status.textContent = j.message || "Saved \u2014 provider changes take effect on next agent run"; status.style.color = "#22C55E"; }
      else { status.textContent = j.detail || "Save failed"; status.style.color = "#FCA5A5"; }
      setTimeout(() => { status.textContent = ""; }, 5000);
    }
    if (r.ok) loadConfig();
  } catch (e) {
    const status = document.getElementById("cfg-status");
    if (status) status.textContent = e.message;
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = "Save"; }
  }
}

async function injectKey() {
  const btn = document.getElementById("key-inject");
  const status = document.getElementById("key-status");
  const provider = document.getElementById("key-provider").value;
  const key = document.getElementById("key-value").value.trim();
  if (!key) { if (status) { status.textContent = "Enter an API key"; status.style.color = "#FCA5A5"; } return; }
  if (btn) { btn.disabled = true; btn.textContent = "Injecting\u2026"; }
  try {
    const r = await fetch("/api/admin/api-key", {
      method: "POST", credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider, key }),
    });
    const j = await r.json().catch(() => ({}));
    if (r.ok) {
      document.getElementById("key-value").value = "";
      if (status) { status.textContent = j.message || "Key injected"; status.style.color = "#22C55E"; setTimeout(() => status.textContent = "", 4000); }
      loadConfig();
    } else {
      if (status) { status.textContent = j.detail || "Inject failed"; status.style.color = "#FCA5A5"; }
    }
  } catch (e) {
    if (status) status.textContent = e.message;
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = "Inject Key"; }
  }
}

document.getElementById("login-btn")?.addEventListener("click", adminLogin);
document.getElementById("login-pass")?.addEventListener("keydown", (e) => { if (e.key === "Enter") adminLogin(); });
document.getElementById("login-user")?.addEventListener("keydown", (e) => { if (e.key === "Enter") document.getElementById("login-pass")?.focus(); });
document.getElementById("cfg-save")?.addEventListener("click", saveConfig);
document.getElementById("key-inject")?.addEventListener("click", injectKey);
document.getElementById("key-value")?.addEventListener("keydown", (e) => { if (e.key === "Enter") injectKey(); });

(async () => {
  try {
    const r = await fetch("/api/admin/config", { credentials: "same-origin" });
    if (r.ok) {
      document.getElementById("login-screen").style.display = "none";
      document.getElementById("config-screen").style.display = "flex";
      const data = await r.json();
      const llm = data.llm || {};
      const el = (id) => document.getElementById(id);
      if (el("cfg-provider")) el("cfg-provider").value = llm.provider || "anthropic";
      if (el("cfg-model")) el("cfg-model").value = llm.model || "";
      if (el("cfg-base-url")) el("cfg-base-url").value = llm.base_url || "";
      if (el("cfg-api-type")) el("cfg-api-type").value = llm.api_type || "openai";
      if (el("cfg-fallback-model")) el("cfg-fallback-model").value = llm.fallback_model || "";
      if (el("cfg-threshold") && data.active_problem) el("cfg-threshold").value = data.active_problem.confidence_threshold ?? 0.85;
      const ks = document.getElementById("api-key-status");
      if (ks) {
        const status = data.api_key_status || {};
        ks.innerHTML = Object.entries(status).map(([k, v]) => {
          const cls = v === "set" ? "color:#22C55E" : "color:#F59E0B";
          return '<span><span style="color:#64748B">' + esc(k) + ':</span> <span style="' + cls + '">' + esc(v) + '</span></span>';
        }).join(" \u00b7 ") || '<span style="color:#475569">No keys configured</span>';
      }
      const rb = document.getElementById("readiness-banner");
      const pr = data.provider_readiness;
      if (rb && pr) {
        rb.style.display = "block";
        if (pr.ready) { rb.style.background = "rgba(34,197,94,0.1)"; rb.style.border = "1px solid rgba(34,197,94,0.2)"; rb.style.color = "#86EFAC"; rb.innerHTML = '<i class="ph ph-check-circle"></i> ' + esc(pr.message || "Ready"); }
        else { rb.style.background = "rgba(245,158,11,0.1)"; rb.style.border = "1px solid rgba(245,158,11,0.2)"; rb.style.color = "#FDE68A"; rb.innerHTML = '<i class="ph ph-warning-circle"></i> ' + esc(pr.message || "Key missing"); }
      }
      loadProblemConfig();
    }
  } catch (_) {}
})();
