/**
 * RLOverlay - JS bridge for Rocket League overlay creators.
 */
(function () {
  "use strict";

  const WS_URL = `ws://${location.host}/ws`;
  const API_URL = `${location.protocol}//${location.host}/api/state`;

  const _listeners = {};
  let _state = {};
  let _ws = null;
  let _reconnectTimer = null;

  function _emit(event, data) {
    const handlers = _listeners[event] || [];
    const wildcards = _listeners["*"] || [];
    [...handlers, ...wildcards].forEach((fn) => {
      try {
        fn(data, event);
      } catch (e) {
        console.error("[RLOverlay] Handler error for", event, e);
      }
    });
  }

  function _connect() {
    if (_ws && (_ws.readyState === WebSocket.OPEN || _ws.readyState === WebSocket.CONNECTING)) return;

    _ws = new WebSocket(WS_URL);

    _ws.addEventListener("open", () => {
      console.log("[RLOverlay] Connected to RL Overlay Hub");
      if (_reconnectTimer) { clearTimeout(_reconnectTimer); _reconnectTimer = null; }
    });

    _ws.addEventListener("message", (evt) => {
      try {
        const msg = JSON.parse(evt.data);
        const { event, data } = msg;
        if (event === "connected") {
          _state = data;
          _emit("connected", data);
          _emit("match:update", data.match);
          _emit("player:updated", data.player);
          _emit("session:updated", data.session);
        } else {
          // Merge partial state updates
          if (event === "match:update") _state.match = { ..._state.match, ...data };
          if (event === "player:updated") _state.player = { ..._state.player, ...data };
          if (event === "session:updated") _state.session = { ..._state.session, ...data };
          _emit(event, data);
        }
      } catch (e) {
        console.error("[RLOverlay] Parse error", e);
      }
    });

    _ws.addEventListener("close", () => {
      console.warn("[RLOverlay] Disconnected - reconnecting in 3s");
      _emit("disconnected", {});
      _reconnectTimer = setTimeout(_connect, 3000);
    });

    _ws.addEventListener("error", () => {
      _ws.close();
    });
  }

  // Auto-connect when script loads
  _connect();

  const RLOverlay = {
    /**
     * Subscribe to an event.
     * @param {string} event  e.g. "match:update", "goal:scored", "*" for all
     * @param {Function} callback
     */
    on(event, callback) {
      if (!_listeners[event]) _listeners[event] = [];
      _listeners[event].push(callback);
      return this;
    },

    /**
     * Unsubscribe from an event.
     */
    off(event, callback) {
      if (!_listeners[event]) return this;
      _listeners[event] = _listeners[event].filter((fn) => fn !== callback);
      return this;
    },

    /**
     * Fetch current state from the REST API.
     * @returns {Promise<object>}
     */
    async getState() {
      const resp = await fetch(API_URL);
      const data = await resp.json();
      _state = data;
      return data;
    },

    /**
     * Return the last known state synchronously (may be stale until first WS message).
     * @returns {object}
     */
    getLatestState() {
      return _state;
    },
  };

  window.RLOverlay = RLOverlay;
})();
