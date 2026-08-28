/* ==========================================================================
   PSA NEXUS — admin.js
   Admin page interactivity: login, provider config, API key injection
   ========================================================================== */

(function () {
  'use strict';

  const $ = (sel) => document.querySelector(sel);

  const dom = {
    loginForm: $('#login-form'),
    loginUsername: $('#login-username'),
    loginPassword: $('#login-password'),
    loginError: $('#login-error'),
    btnLogin: $('#btn-login'),
    adminConfig: $('#admin-config'),
    btnLogout: $('#btn-logout'),
    readinessDot: $('#readiness-dot'),
    readinessText: $('#readiness-text'),
    apiKeyProvider: $('#apikey-provider'),
    apiKeyKey: $('#apikey-key'),
    btnInjectKey: $('#btn-inject-key'),
    apikeySuccess: $('#apikey-success'),
    configDisplay: $('#config-display'),
  };

  function apiBase() {
    return window.location.origin;
  }

  function escHtml(str) {
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
  }

  // ---- Login ----
  dom.loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    dom.loginError.classList.remove('visible');
    dom.btnLogin.disabled = true;
    dom.btnLogin.textContent = 'LOGGING IN...';

    const username = dom.loginUsername.value.trim();
    const password = dom.loginPassword.value;

    try {
      const res = await fetch(apiBase() + '/api/admin/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
        credentials: 'same-origin',
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Login failed' }));
        dom.loginError.textContent = err.detail || 'Invalid credentials';
        dom.loginError.classList.add('visible');
        dom.btnLogin.disabled = false;
        dom.btnLogin.textContent = 'LOGIN';
        return;
      }

      // Login successful — show config panel
      dom.loginForm.style.display = 'none';
      dom.adminConfig.classList.add('visible');
      loadConfig();
    } catch (err) {
      dom.loginError.textContent = 'Connection failed';
      dom.loginError.classList.add('visible');
      dom.btnLogin.disabled = false;
      dom.btnLogin.textContent = 'LOGIN';
    }
  });

  // ---- Load Config ----
  async function loadConfig() {
    try {
      const res = await fetch(apiBase() + '/api/admin/config', {
        credentials: 'same-origin',
      });

      if (!res.ok) {
        if (res.status === 401) {
          // Session expired
          showLogin();
          return;
        }
        dom.configDisplay.textContent = 'Failed to load config (HTTP ' + res.status + ')';
        return;
      }

      const data = await res.json();
      renderConfig(data);
    } catch (err) {
      dom.configDisplay.textContent = 'Connection error loading config';
    }
  }

  function renderConfig(data) {
    // Provider readiness
    const pr = data.provider_readiness || {};
    dom.readinessDot.className = 'admin-readiness-dot ' + (pr.ready ? 'ready' : 'not-ready');
    dom.readinessText.textContent = pr.message || 'Unknown';

    // Config display
    const llm = data.llm || {};
    const lines = [];
    lines.push('PROVIDER:    ' + (llm.provider || '--'));
    lines.push('MODEL:       ' + (llm.model || '--'));
    lines.push('BASE_URL:    ' + (llm.base_url || '--'));
    lines.push('API_TYPE:    ' + (llm.api_type || '--'));
    lines.push('API_KEY_ENV: ' + (llm.api_key_env || '--'));
    if (llm.fallback_provider) {
      lines.push('');
      lines.push('FALLBACK:');
      lines.push('  PROVIDER:  ' + (llm.fallback_provider || '--'));
      lines.push('  MODEL:     ' + (llm.fallback_model || '--'));
      lines.push('  BASE_URL:  ' + (llm.fallback_base_url || '--'));
    }
    lines.push('');
    lines.push('ACTIVE PROBLEM: ' + (data.active_problem?.id || '--'));
    lines.push('CONF THRESHOLD: ' + (data.active_problem?.confidence_threshold || '--'));

    // API key status
    const ks = data.api_key_status || {};
    lines.push('');
    lines.push('API KEY STATUS:');
    Object.keys(ks).forEach((k) => {
      lines.push('  ' + k + ': ' + ks[k]);
    });

    dom.configDisplay.textContent = lines.join('\n');

    // Pre-fill provider field
    if (llm.provider && !dom.apiKeyProvider.value) {
      dom.apiKeyProvider.value = llm.provider;
    }
  }

  // ---- API Key Injection ----
  dom.btnInjectKey.addEventListener('click', async () => {
    dom.apikeySuccess.classList.remove('visible');

    const provider = dom.apiKeyProvider.value.trim();
    const key = dom.apiKeyKey.value.trim();

    if (!provider) {
      dom.apikeySuccess.textContent = 'Provider is required';
      dom.apikeySuccess.style.color = 'var(--danger)';
      dom.apikeySuccess.classList.add('visible');
      return;
    }
    if (!key) {
      dom.apikeySuccess.textContent = 'API key is required';
      dom.apikeySuccess.style.color = 'var(--danger)';
      dom.apikeySuccess.classList.add('visible');
      return;
    }

    dom.btnInjectKey.disabled = true;
    dom.btnInjectKey.textContent = 'INJECTING...';

    try {
      const res = await fetch(apiBase() + '/api/admin/api-key', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ provider, key }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Injection failed' }));
        dom.apikeySuccess.textContent = err.detail || 'Failed';
        dom.apikeySuccess.style.color = 'var(--danger)';
        dom.apikeySuccess.classList.add('visible');
        dom.btnInjectKey.disabled = false;
        dom.btnInjectKey.textContent = 'INJECT KEY';
        return;
      }

      const data = await res.json();
      dom.apikeySuccess.textContent = data.message || 'Key injected successfully';
      dom.apikeySuccess.style.color = 'var(--success)';
      dom.apikeySuccess.classList.add('visible');
      dom.apiKeyKey.value = '';

      // Refresh config to update readiness
      loadConfig();
    } catch (err) {
      dom.apikeySuccess.textContent = 'Connection error';
      dom.apikeySuccess.style.color = 'var(--danger)';
      dom.apikeySuccess.classList.add('visible');
    }

    dom.btnInjectKey.disabled = false;
    dom.btnInjectKey.textContent = 'INJECT KEY';
  });

  // ---- Logout ----
  dom.btnLogout.addEventListener('click', () => {
    document.cookie = 'psa_admin_session=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
    showLogin();
  });

  function showLogin() {
    dom.adminConfig.classList.remove('visible');
    dom.loginForm.style.display = '';
    dom.loginUsername.value = '';
    dom.loginPassword.value = '';
    dom.loginError.classList.remove('visible');
    dom.btnLogin.disabled = false;
    dom.btnLogin.textContent = 'LOGIN';
  }

  // ---- Check existing session on load ----
  (async function init() {
    try {
      const res = await fetch(apiBase() + '/api/admin/config', {
        credentials: 'same-origin',
      });
      if (res.ok) {
        const data = await res.json();
        dom.loginForm.style.display = 'none';
        dom.adminConfig.classList.add('visible');
        renderConfig(data);
      }
    } catch (e) {
      // Not logged in — show login form
    }
  })();
})();
