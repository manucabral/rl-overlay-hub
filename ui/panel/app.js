"use strict";

const state = {
  liveWs: null,
  liveState: { match: {}, player: {}, session: {} },
  sessionSummary: { active_session: null, archived_sessions: [] },
  communityLoaded: false,
  communityData: [],
  logAutoRefresh: null,
  logPaused: false,
  searchDebounce: null,
  toastTimer: null,
};

const dom = {
  dot: document.getElementById("rl-dot"),
  label: document.getElementById("rl-label"),
  wsLbl: document.getElementById("ws-label"),
};

const api = {
  host: location.hostname || "127.0.0.1",
  port: location.port || "49100",
  ws(path) {
    return `ws://${location.host}${path}`;
  },
  async json(path, init) {
    const response = await fetch(path, init);
    const text = await response.text();
    const data = text ? JSON.parse(text) : {};
    if (!response.ok) {
      throw new Error(data.detail || `HTTP ${response.status}`);
    }
    return data;
  },
  overlayUrl(id) {
    return `http://${this.host}:${this.port}/overlay/${id}/`;
  },
};

function toast(msg, duration = 2500) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.classList.add("show");
  if (state.toastTimer) clearTimeout(state.toastTimer);
  state.toastTimer = setTimeout(() => el.classList.remove("show"), duration);
}

function esc(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

async function pollStatus() {
  try {
    const status = await api.json("/api/status");
    dom.dot.classList.toggle("connected", status.connected);
    dom.label.textContent = status.connected ? "Connected" : "Disconnected";
    dom.wsLbl.textContent = `${status.ws_clients} client${status.ws_clients !== 1 ? "s" : ""}`;

    const toggle = document.getElementById("preview-toggle");
    if (toggle && toggle.checked !== status.preview) {
      toggle.checked = status.preview;
      syncPreviewButtons(status.preview);
    }
  } catch (_) {
    dom.dot.classList.remove("connected");
    dom.label.textContent = "Unavailable";
  }
}

function syncPreviewButtons(enabled) {
  document.querySelectorAll(".preview-buttons").forEach((el) => {
    el.classList.toggle("enabled", enabled);
  });
  document.getElementById("preview-status").innerHTML =
    `Preview mode is <strong>${enabled ? "ON" : "OFF"}</strong>`;
}

function renderOverlayCard(ov) {
  const previewImg = ov.preview_url
    ? `<img src="${ov.preview_url}" alt="preview" onerror="this.style.display='none'" />`
    : "No preview";
  const disabledClass = ov.enabled ? "" : " disabled-overlay";
  const toggleLabel = ov.enabled ? "Disable" : "Enable";
  const deleteBtn = ov._source === "installed"
    ? `<button class="btn-delete" data-id="${esc(ov.id)}" title="Uninstall">✕</button>`
    : "";
  return `
  <div class="overlay-card${disabledClass}">
    <div class="card-preview">${previewImg}</div>
    <div class="card-body">
      <div class="card-name">${esc(ov.name || ov.id)}${ov.official ? '<span class="badge-official">Official</span>' : ""}</div>
      <div class="card-author">by ${esc(ov.author || "Unknown")}</div>
      <div class="card-desc">${esc(ov.description || "")}</div>
      <div class="card-url">
        <span class="url-text">${esc(ov.url || api.overlayUrl(ov.id))}</span>
        <button class="btn-copy" data-url="${esc(ov.url || api.overlayUrl(ov.id))}">Copy</button>
        <button class="btn-open" data-url="${esc(ov.url || api.overlayUrl(ov.id))}">↗</button>
      </div>
      <div class="card-actions">
        <button class="btn-toggle${ov.enabled ? "" : " btn-toggle-enable"}" data-id="${esc(ov.id)}">${toggleLabel}</button>
        ${deleteBtn}
      </div>
    </div>
  </div>`;
}

async function loadOverlays() {
  const grid = document.getElementById("overlay-grid");
  try {
    const overlays = await api.json("/api/overlays");
    if (!overlays.length) {
      grid.innerHTML = '<div class="loading">No overlays found.</div>';
      return;
    }
    grid.innerHTML = overlays.map(renderOverlayCard).join("");

    grid.querySelectorAll(".btn-copy").forEach((btn) => {
      btn.addEventListener("click", () => {
        navigator.clipboard.writeText(btn.dataset.url).then(() => toast("URL copied!"));
      });
    });
    grid.querySelectorAll(".btn-open").forEach((btn) => {
      btn.addEventListener("click", () => window.open(btn.dataset.url, "_blank"));
    });
    grid.querySelectorAll(".btn-toggle").forEach((btn) => {
      btn.addEventListener("click", () => toggleOverlay(btn.dataset.id, btn));
    });
    grid.querySelectorAll(".btn-delete").forEach((btn) => {
      btn.addEventListener("click", () => uninstallOverlay(btn.dataset.id, btn));
    });
  } catch (_) {
    grid.innerHTML = '<div class="loading">Failed to load overlays.</div>';
  }
}

async function toggleOverlay(id, btn) {
  btn.disabled = true;
  try {
    await api.json(`/api/overlays/${id}/toggle`, { method: "POST" });
    await loadOverlays();
  } catch (err) {
    toast(`Toggle failed: ${err.message}`);
    btn.disabled = false;
  }
}

async function installFromLocal(path) {
  setInstallStatus("Installing…", "info");
  document.getElementById("local-install-btn").disabled = true;
  try {
    const data = await api.json("/api/overlays/install-local", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path }),
    });
    setInstallStatus(`Installed: ${data.overlay_id}`, "success");
    await loadOverlays();
  } catch (err) {
    setInstallStatus(`Error: ${err.message}`, "error");
  } finally {
    document.getElementById("local-install-btn").disabled = false;
  }
}

function setInstallStatus(msg, type = "info") {
  const statusEl = document.getElementById("install-custom-status");
  statusEl.textContent = msg;
  statusEl.className = `install-custom-status ${type}`;
  statusEl.hidden = false;
}

function renderLive() {
  const m = state.liveState.match || {};
  const p = state.liveState.player || {};
  const s = state.liveState.session || {};

  document.getElementById("live-blue").textContent = m.blue_score ?? 0;
  document.getElementById("live-orange").textContent = m.orange_score ?? 0;
  document.getElementById("live-clock").textContent = m.clock ?? "–";
  const otEl = document.getElementById("live-overtime");
  otEl.style.display = m.overtime ? "" : "none";
  const badge = document.getElementById("live-active");
  badge.textContent = m.is_active ? "In Match" : "In Menu";
  badge.classList.toggle("active", !!m.is_active);

  document.getElementById("live-player-name").textContent = p.name || "–";
  document.getElementById("live-goals").textContent = p.goals ?? 0;
  document.getElementById("live-assists").textContent = p.assists ?? 0;
  document.getElementById("live-saves").textContent = p.saves ?? 0;
  document.getElementById("live-shots").textContent = p.shots ?? 0;
  document.getElementById("live-score").textContent = p.score ?? 0;
  document.getElementById("live-demos").textContent = p.demos ?? 0;

  const boost = p.boost ?? 0;
  document.getElementById("live-boost-val").textContent = boost;
  const bar = document.getElementById("live-boost-bar");
  bar.style.width = `${boost}%`;
  bar.style.background = boost > 50 ? "var(--green)" : boost > 20 ? "var(--yellow)" : "var(--red)";

  document.getElementById("live-matches").textContent = s.matches ?? 0;
  document.getElementById("live-wins").textContent = s.wins ?? 0;
  document.getElementById("live-losses").textContent = s.losses ?? 0;
  document.getElementById("live-s-goals").textContent = s.goals ?? 0;
  document.getElementById("live-s-assists").textContent = s.assists ?? 0;
  document.getElementById("live-s-saves").textContent = s.saves ?? 0;
  document.getElementById("live-s-demos").textContent = s.demolitions ?? 0;
  document.getElementById("live-s-demos-taken").textContent = s.demolitions_taken ?? 0;
  renderSessionSummary();
}

function formatDate(value) {
  if (!value) return "-";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "-" : date.toLocaleString();
}

function renderSessionSummary() {
  const active = state.sessionSummary.active_session;
  document.getElementById("live-session-started").textContent = active ? formatDate(active.started_at) : "-";
  document.getElementById("live-session-updated").textContent = active ? formatDate(active.last_updated_at) : "-";

  const list = document.getElementById("archived-sessions-list");
  const archived = state.sessionSummary.archived_sessions || [];
  if (!archived.length) {
    list.innerHTML = '<div class="live-session-row"><span>No archived sessions yet</span></div>';
    return;
  }
  list.innerHTML = archived.map((session) => `
    <div class="live-session-row">
      <span>${esc(formatDate(session.started_at))} → ${esc(formatDate(session.ended_at))}</span>
      <strong>${esc(`W:${session.stats.wins} L:${session.stats.losses} M:${session.stats.matches}`)}</strong>
    </div>
    <div class="live-session-row">
      <span>Goals ${session.stats.goals} · Assists ${session.stats.assists} · Saves ${session.stats.saves}</span>
    </div>
    <div class="live-session-row">
      <span>Demos ${session.stats.demolitions ?? 0} · Demos Taken ${session.stats.demolitions_taken ?? 0}</span>
    </div>
  `).join("");
}

async function loadSessionSummary() {
  try {
    state.sessionSummary = await api.json("/api/session");
    renderSessionSummary();
  } catch (_) {}
}

function connectLiveWs() {
  if (state.liveWs && state.liveWs.readyState < 2) return;
  state.liveWs = new WebSocket(api.ws("/ws"));
  state.liveWs.onmessage = (e) => {
    try {
      const msg = JSON.parse(e.data);
      if (msg.event === "connected") {
        state.liveState = msg.data;
      } else if (msg.event === "match:update") {
        Object.assign(state.liveState.match, msg.data);
      } else if (msg.event === "player:updated") {
        Object.assign(state.liveState.player, msg.data);
      } else if (msg.event === "session:updated") {
        Object.assign(state.liveState.session, msg.data);
      } else {
        return;
      }
      renderLive();
    } catch (_) {}
  };
  state.liveWs.onclose = () => {
    state.liveWs = null;
    if (document.getElementById("tab-live").classList.contains("active")) {
      setTimeout(connectLiveWs, 2000);
    }
  };
}

function disconnectLiveWs() {
  if (state.liveWs) {
    state.liveWs.close();
    state.liveWs = null;
  }
}

function renderLogLine(line) {
  let cls = "log-info";
  if (line.includes(" ERROR ")) cls = "log-error";
  else if (line.includes(" WARNING ")) cls = "log-warn";
  else if (line.includes(" DEBUG ")) cls = "log-debug";
  return `<div class="log-line ${cls}">${esc(line)}</div>`;
}

async function loadLogs() {
  if (state.logPaused) return;
  try {
    const lines = await api.json("/api/logs?lines=150");
    const el = document.getElementById("log-output");
    const atBottom = el.scrollHeight - el.scrollTop <= el.clientHeight + 40;
    el.innerHTML = lines.map(renderLogLine).join("");
    if (atBottom) el.scrollTop = el.scrollHeight;
  } catch (_) {}
}

function renderCommunityItem(ov) {
  const actions = ov.installed
    ? `<div class="install-actions">
         <button class="btn-install installed" disabled>Installed ✓</button>
         <button class="btn-uninstall" data-id="${esc(ov.id)}">Remove</button>
       </div>`
    : `<button class="btn-install" data-id="${esc(ov.id)}">Install</button>`;
  return `
  <div class="community-item">
    <div class="community-info">
      <div class="community-name">${esc(ov.name || ov.id)}</div>
      <div class="community-meta">by ${esc(ov.author || "Unknown")} · v${esc(ov.version || "1.0.0")}</div>
      <div class="community-desc">${esc(ov.description || "")}</div>
    </div>
    ${actions}
  </div>`;
}

function renderFiltered() {
  const list = document.getElementById("community-list");
  const q = (document.getElementById("community-search")?.value || "").toLowerCase().trim();
  const filtered = q
    ? state.communityData.filter((ov) =>
      (ov.name || "").toLowerCase().includes(q) ||
      (ov.author || "").toLowerCase().includes(q) ||
      (ov.description || "").toLowerCase().includes(q))
    : state.communityData;

  if (!filtered.length) {
    list.innerHTML = '<div class="loading">No overlays match your search.</div>';
    return;
  }

  list.innerHTML = filtered.map(renderCommunityItem).join("");
  list.querySelectorAll(".btn-install:not([disabled])").forEach((btn) => {
    btn.addEventListener("click", () => installOverlay(btn.dataset.id, btn));
  });
  list.querySelectorAll(".btn-uninstall").forEach((btn) => {
    btn.addEventListener("click", () => uninstallOverlay(btn.dataset.id, btn));
  });
}

async function loadCommunity() {
  if (state.communityLoaded) return;
  const list = document.getElementById("community-list");
  list.innerHTML = '<div class="loading">Loading registry…</div>';
  try {
    state.communityData = await api.json("/api/community");
    state.communityLoaded = true;
    renderFiltered();
  } catch (_) {
    list.innerHTML = '<div class="loading">Failed to load community registry.</div>';
  }
}

async function installOverlay(id, btn) {
  btn.disabled = true;
  btn.textContent = "Installing…";
  try {
    const entry = state.communityData.find((o) => o.id === id);
    await api.json("/api/overlays/install", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ overlay_id: id, registry_entry: entry }),
    });
    const ov = state.communityData.find((o) => o.id === id);
    if (ov) ov.installed = true;
    renderFiltered();
    toast(`${id} installed!`);
    await loadOverlays();
  } catch (err) {
    btn.disabled = false;
    btn.textContent = "Install";
    toast(`Install failed: ${err.message}`);
  }
}

async function uninstallOverlay(id, btn) {
  btn.disabled = true;
  try {
    await api.json(`/api/overlays/${id}`, { method: "DELETE" });
    const ov = state.communityData.find((o) => o.id === id);
    if (ov) ov.installed = false;
    renderFiltered();
    await loadOverlays();
    toast(`${id} removed`);
  } catch (err) {
    btn.disabled = false;
    toast(`Removal failed: ${err.message}`);
  }
}

async function loadRLConfig() {
  const box = document.getElementById("rl-config-box");
  if (!box) return;
  try {
    const cfg = await api.json("/api/rl-config");
    const found = cfg.found;
    const enabled = cfg.enabled;
    const path = cfg.path || "Not found";
    const statusColor = enabled ? "var(--green)" : found ? "var(--yellow)" : "var(--red)";
    const statusText = enabled ? "Enabled" : found ? "Disabled" : "File not found";
    const btnLabel = enabled ? "Disable Stats API" : "Enable Stats API";
    const btnAction = enabled ? "disable" : "enable";

    box.innerHTML = `
      <div class="rl-config-row">
        <span class="rl-config-status" style="color:${statusColor}">● ${statusText}</span>
        <button class="btn-rl-config" data-action="${btnAction}">${btnLabel}</button>
      </div>
      <div class="rl-config-path">${esc(path)}</div>
      ${cfg.warning ? `<div class="rl-config-warning">${esc(cfg.warning)}</div>` : ""}
    `;

    box.querySelector(".btn-rl-config")?.addEventListener("click", async (e) => {
      const action = e.target.dataset.action;
      try {
        await api.json(`/api/rl-config/${action}`, { method: "POST" });
        toast(action === "enable" ? "Stats API enabled - restart Rocket League" : "Stats API disabled");
        await loadRLConfig();
      } catch (err) {
        toast(err.message);
      }
    });
  } catch (_) {
    box.innerHTML = '<div class="loading">Could not load RL config status.</div>';
  }
}

async function loadSettings() {
  try {
    const settings = await api.json("/api/settings");
    document.getElementById("setting-port").value = settings.port ?? 49100;
    document.getElementById("setting-verbose").checked = settings.verbose ?? false;
  } catch (_) {}
  await loadRLConfig();
}

function setupTabs() {
  document.querySelectorAll(".tab").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");

      if (btn.dataset.tab === "community") loadCommunity();
      if (btn.dataset.tab === "settings") loadSettings();
      if (btn.dataset.tab === "live") {
        connectLiveWs();
        loadSessionSummary();
      } else disconnectLiveWs();
      if (btn.dataset.tab === "logs") {
        loadLogs();
        state.logAutoRefresh = setInterval(loadLogs, 3000);
      } else {
        clearInterval(state.logAutoRefresh);
        state.logAutoRefresh = null;
      }
    });
  });
}

function setupEventHandlers() {
  document.getElementById("overlays-refresh")?.addEventListener("click", loadOverlays);

  const customPanel = document.getElementById("custom-install-panel");
  const customToggle = document.getElementById("custom-install-toggle");
  customToggle.addEventListener("click", () => {
    const open = !customPanel.hidden;
    customPanel.hidden = open;
    customToggle.textContent = open ? "＋ Install Custom Overlay" : "✕ Close";
  });

  document.getElementById("local-browse-btn")?.addEventListener("click", async () => {
    if (window.pywebview?.api?.pick_folder) {
      const path = await window.pywebview.api.pick_folder();
      if (path) document.getElementById("local-path-input").value = path;
    }
  });

  document.getElementById("local-install-btn")?.addEventListener("click", () => {
    const path = document.getElementById("local-path-input").value.trim();
    if (path) installFromLocal(path);
  });

  document.getElementById("preview-toggle").addEventListener("change", async (e) => {
    const enabled = e.target.checked;
    try {
      await api.json("/api/preview/toggle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled }),
      });
      syncPreviewButtons(enabled);
      toast(enabled ? "Preview mode ON" : "Preview mode OFF");
      if (enabled) loadOverlays();
    } catch (_) {
      e.target.checked = !enabled;
    }
  });

  document.getElementById("tab-preview").addEventListener("click", async (e) => {
    const btn = e.target.closest(".sim-btn");
    if (!btn) return;
    try {
      await api.json(`/api/preview/simulate/${btn.dataset.event}`, { method: "POST" });
      toast(`Simulated: ${btn.dataset.event}`);
    } catch (err) {
      toast(`Simulation failed: ${err.message}`);
    }
  });

  document.getElementById("log-pause")?.addEventListener("click", (e) => {
    state.logPaused = !state.logPaused;
    e.target.textContent = state.logPaused ? "Resume" : "Pause";
    if (!state.logPaused) loadLogs();
  });

  document.getElementById("log-clear")?.addEventListener("click", () => {
    document.getElementById("log-output").innerHTML = "";
    state.logPaused = true;
    document.getElementById("log-pause").textContent = "Resume";
  });

  document.getElementById("community-search")?.addEventListener("input", () => {
    clearTimeout(state.searchDebounce);
    state.searchDebounce = setTimeout(renderFiltered, 200);
  });

  document.getElementById("community-refresh")?.addEventListener("click", () => {
    state.communityLoaded = false;
    state.communityData = [];
    loadCommunity();
  });

  document.getElementById("open-data-folder")?.addEventListener("click", () => {
    if (window.pywebview?.api?.open_data_folder) {
      window.pywebview.api.open_data_folder();
    }
  });

  document.getElementById("save-settings").addEventListener("click", async () => {
    const port = parseInt(document.getElementById("setting-port").value, 10);
    const verbose = document.getElementById("setting-verbose").checked;
    try {
      await api.json("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ port, verbose }),
      });
      state.communityLoaded = false;
      toast("Settings saved. Restart the app to apply port changes.");
    } catch (err) {
      toast(`Failed to save settings: ${err.message}`);
    }
  });

  document.getElementById("start-new-session")?.addEventListener("click", async () => {
    if (!window.confirm("Archive the current session and start a new one?")) {
      return;
    }
    try {
      const result = await api.json("/api/session/new", { method: "POST" });
      state.sessionSummary.active_session = result.active_session;
      state.sessionSummary.archived_sessions = [
        result.archived_session,
        ...(state.sessionSummary.archived_sessions || []),
      ];
      state.liveState.match = {};
      state.liveState.player = {};
      state.liveState.session = result.active_session.stats;
      renderLive();
      toast("New session started");
    } catch (err) {
      toast(`Failed to start new session: ${err.message}`);
    }
  });
}

setupTabs();
setupEventHandlers();
setInterval(pollStatus, 3000);
pollStatus();
loadOverlays();
loadSessionSummary();
