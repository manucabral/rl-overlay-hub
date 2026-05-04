# Example: Event Snippets

This page is a cookbook of small `script.js` patterns for the hub's simpler events. Each snippet is designed to be copied into an overlay and adapted quickly.

Use the Preview tab in the desktop app to trigger most of these events without Rocket League running.

## Sync on connect

Events: `connected`

Preview button: turn Preview Mode on.

```javascript
const statusEl = document.getElementById("status");

RLOverlay.on("connected", (state) => {
  statusEl.textContent = state.match?.is_active ? "In match" : "In menu";
});
```

Use this pattern whenever your overlay needs an immediate first render instead of waiting for a later event.

## Match lifecycle

Events: `match:started`, `match:initialized`, `match:ended`, `match:destroyed`

Preview buttons: `New Match`, `Match Initialized`, `End Match`, `Return to Menu`.

```javascript
const bannerEl = document.getElementById("match-banner");

function flash(text) {
  bannerEl.textContent = text;
  bannerEl.classList.remove("show");
  void bannerEl.offsetWidth;
  bannerEl.classList.add("show");
}

RLOverlay.on("match:started", () => flash("Match loading"));
RLOverlay.on("match:initialized", () => flash("Match ready"));
RLOverlay.on("match:ended", ({ won }) => flash(won ? "Victory" : "Defeat"));
RLOverlay.on("match:destroyed", () => flash("Back to menu"));
```

This is useful for scene banners, intro stingers, or simple state labels around the match lifecycle.

## Overtime, countdown, and round start

Events: `overtime:started`, `countdown:begin`, `round:started`

Preview buttons: `Simulate Overtime`, `Countdown`, `Round Start`.

```javascript
const phaseEl = document.getElementById("phase");

RLOverlay.on("countdown:begin", () => {
  phaseEl.textContent = "Kickoff incoming";
});

RLOverlay.on("round:started", () => {
  phaseEl.textContent = "Live";
});

RLOverlay.on("overtime:started", () => {
  phaseEl.textContent = "Overtime";
  phaseEl.classList.add("urgent");
});
```

These events are good for overlays that need a small match-phase indicator without reading full state every frame.

## Pause and resume

Events: `match:paused`, `match:unpaused`

Preview buttons: `Pause`, `Resume`.

```javascript
const pausedEl = document.getElementById("paused-overlay");

RLOverlay.on("match:paused", () => {
  pausedEl.hidden = false;
});

RLOverlay.on("match:unpaused", () => {
  pausedEl.hidden = true;
});
```

Use this when you want to dim the overlay, freeze animations, or show a pause card.

## Hide overlay during replay

Events: `goal:replay`, `goal:replay:will-end`

Preview buttons: `Replay Start`, `Replay Will End`, `Replay End`.

```javascript
const rootEl = document.getElementById("overlay-root");

RLOverlay.on("goal:replay", ({ phase }) => {
  if (phase === "start") rootEl.classList.add("replay-hidden");
  if (phase === "end") rootEl.classList.remove("replay-hidden");
});

RLOverlay.on("goal:replay:will-end", () => {
  rootEl.classList.add("replay-returning");
});
```

This is handy for scorebugs and lower thirds that should stay out of the way during replay, then fade back smoothly.

## React to demolitions

Events: `statfeed:event`, `player:demolished`

Preview buttons: `Demolition Feed`, `Player Demo`.

```javascript
const feedEl = document.getElementById("feed");

RLOverlay.on("statfeed:event", (feed) => {
  if (feed.type !== "demolition") return;
  feedEl.textContent = `${feed.player_name} demoed ${feed.secondary_name}`;
});

RLOverlay.on("player:demolished", ({ attacker, victim }) => {
  console.log("Demo event:", attacker, "->", victim);
});
```

Use `statfeed:event` when you want the generic in-game feed style. Use `player:demolished` when you just need attacker/victim directly.

## Session totals widget

Events: `connected`, `session:updated`

Preview buttons: `End Match`, `Reset Session`, `Player Demo`.

```javascript
const winsEl = document.getElementById("wins");
const demosEl = document.getElementById("demos");
const demosTakenEl = document.getElementById("demos-taken");

function applySession(session) {
  winsEl.textContent = session.wins ?? 0;
  demosEl.textContent = session.demolitions ?? 0;
  demosTakenEl.textContent = session.demolitions_taken ?? 0;
}

RLOverlay.on("connected", (state) => applySession(state.session));
RLOverlay.on("session:updated", applySession);
```

This is the standard pattern for any overlay that tracks cumulative session totals instead of only the current match.

## Ball hit and crossbar impact

Events: `ball:hit`, `crossbar:hit`

Preview buttons: `Ball Hit`, `Crossbar Hit`.

```javascript
const fxEl = document.getElementById("impact-fx");

function pulse(label) {
  fxEl.textContent = label;
  fxEl.classList.remove("pulse");
  void fxEl.offsetWidth;
  fxEl.classList.add("pulse");
}

RLOverlay.on("ball:hit", ({ post_hit_speed }) => {
  pulse(`Ball hit: ${Math.round(post_hit_speed)} kph`);
});

RLOverlay.on("crossbar:hit", () => {
  pulse("Crossbar!");
});
```

These events work well for impact flashes, sound triggers, or reactive camera-border effects.

## Podium and replay saved

Events: `podium:started`, `replay:created`

Preview buttons: `Podium`, `Replay Saved`.

```javascript
const footerEl = document.getElementById("footer-note");

RLOverlay.on("podium:started", () => {
  footerEl.textContent = "Winners podium";
});

RLOverlay.on("replay:created", () => {
  footerEl.textContent = "Replay saved";
});
```

These are simple post-match hooks for overlays that show closing states or creator-friendly confirmation messages.

## Wildcard event logger

Events: `*`

Preview buttons: any preview button.

```javascript
RLOverlay.on("*", (data, eventName) => {
  console.log("[overlay event]", eventName, data);
});
```

This is the fastest way to inspect event flow while building a new overlay or debugging a handler.
