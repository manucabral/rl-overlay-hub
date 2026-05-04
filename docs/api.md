# JavaScript API

The hub serves a script at `/overlay-api.js` that your overlay must include. This script opens a WebSocket connection to the hub and exposes a global object called `window.RLOverlay`.

## Loading the script

Always load `overlay-api.js` before your own script.

```html
<script src="/overlay-api.js"></script>
<script src="./script.js"></script>
```

The path `/overlay-api.js` is absolute and always resolves correctly regardless of which overlay is loaded.

## Methods

### RLOverlay.on(event, callback)

Subscribe to an event. The callback receives the event data as its first argument. Returns `RLOverlay` for chaining.

```javascript
RLOverlay.on("goal:scored", (goal) => {
  console.log(goal.player_name, "scored for", goal.team);
});
```

### RLOverlay.off(event, callback)

Unsubscribe a previously registered callback. The callback reference must be the same function passed to `on()`. Returns `RLOverlay` for chaining.

```javascript
function onGoal(goal) { /* ... */ }

RLOverlay.on("goal:scored", onGoal);
// later
RLOverlay.off("goal:scored", onGoal);
```

### RLOverlay.getState()

Returns a Promise that resolves to the current full state fetched from the REST API. Use this when you need guaranteed fresh data.

```javascript
RLOverlay.getState().then((state) => {
  console.log(state.match, state.player, state.session);
});
```

### RLOverlay.getLatestState()

Returns the last state object received from the WebSocket, synchronously. May be stale if the connection was interrupted. Before the first WebSocket payload arrives, this may be an empty object.

```javascript
const state = RLOverlay.getLatestState();
if (state?.match) {
  console.log(state.match.clock);
}
```

## Connection behavior

When the script loads it connects automatically to the same host and port that served the overlay page, using `/ws`. If the WebSocket drops, the script reconnects every 3 seconds without any action from you. On reconnect it emits a `"connected"` event with the full current state, so your overlay can re-sync without extra logic.

## Events

### connected

Fires when the WebSocket first connects and on every reconnect. The data is a full state snapshot. Use this to initialize your overlay UI.

```javascript
RLOverlay.on("connected", (state) => {
  applyMatch(state.match);
  applyPlayer(state.player);
  applySession(state.session);
});
```

Data shape:

```json
{
  "match": { "blue_score": 0, "orange_score": 0, "clock": "5:00", "overtime": false, "is_active": false },
  "player": { "name": "", "goals": 0, "assists": 0, "saves": 0, "shots": 0, "score": 0, "boost": 0, "demos": 0 },
  "session": { "matches": 0, "wins": 0, "losses": 0, "goals": 0, "assists": 0, "saves": 0, "demolitions": 0, "demolitions_taken": 0 }
}
```

### match:update

Fires when the match state changes: scores, clock, or overtime flag. Data is the full match object.

```javascript
RLOverlay.on("match:update", (match) => {
  document.getElementById("blue-score").textContent = match.blue_score;
  document.getElementById("orange-score").textContent = match.orange_score;
  document.getElementById("timer").textContent = match.clock;
});
```

Data shape: see [State Reference - match](state.md#match). Fields are `blue_score`, `orange_score`, `clock`, `overtime`, and `is_active`.

### match:started

Fires when a new match loads. Data contains the match GUID.

```javascript
RLOverlay.on("match:started", ({ match_guid }) => {
  console.log("New match:", match_guid);
});
```

Data shape:

```json
{ "match_guid": "abc123..." }
```

### match:initialized

Fires after `match:started` once the match is fully ready. Use this instead of `match:started` if you need match data to be populated before acting.

Data shape:

```json
{ "match_guid": "abc123..." }
```

### match:ended

Fires when a match finishes.

```javascript
RLOverlay.on("match:ended", ({ won, winner_team_num }) => {
  if (won) showWinScreen();
});
```

Data shape:

```json
{ "won": true, "winner_team_num": 0 }
```

`winner_team_num` is `0` for blue and `1` for orange.

### match:destroyed

Fires when the match unloads, for example when the player returns to the main menu.

Data shape: `{}`

### goal:scored

Fires when a goal is scored. This is the most commonly used event for animated overlays.

```javascript
RLOverlay.on("goal:scored", (goal) => {
  showBanner(goal.player_name, goal.team);
});
```

Data shape:

```json
{
  "player_name": "Jstn",
  "team": "blue",
  "assister_name": "Fairy Peak",
  "goal_speed": 143
}
```

`team` is always either `"blue"` or `"orange"`. `assister_name` is an empty string if there was no assist. `goal_speed` is in kph.

### overtime:started

Fires when the match enters overtime.

```javascript
RLOverlay.on("overtime:started", () => {
  document.getElementById("ot-badge").classList.add("visible");
});
```

Data shape: `{}`

### countdown:begin

Fires when the kickoff countdown begins.

```javascript
RLOverlay.on("countdown:begin", ({ match_guid }) => {
  showCountdown(match_guid);
});
```

Data shape:

```json
{ "match_guid": "preview-match-001" }
```

### round:started

Fires when the playable round begins after kickoff.

Data shape:

```json
{ "match_guid": "preview-match-001" }
```

### match:paused

Fires when a match is paused.

Data shape:

```json
{ "match_guid": "preview-match-001" }
```

### match:unpaused

Fires when a paused match resumes.

Data shape:

```json
{ "match_guid": "preview-match-001" }
```

### goal:replay

Fires when a goal replay starts or ends.

```javascript
RLOverlay.on("goal:replay", ({ phase }) => {
  if (phase === "start") hideOverlay();
  if (phase === "end")   showOverlay();
});
```

Data shape:

```json
{ "phase": "start" }
```

`phase` is either `"start"` or `"end"`.

### goal:replay:will-end

Fires shortly before a goal replay ends. This is useful if your overlay needs to prepare a transition back in.

Data shape:

```json
{ "match_guid": "preview-match-001" }
```

### ball:hit

Fires when the ball is struck and you want a reactive overlay effect.

Data shape:

```json
{
  "player_name": "DemoPlayer",
  "team": "blue",
  "pre_hit_speed": 82.5,
  "post_hit_speed": 109.4
}
```

### crossbar:hit

Fires when the ball hits the crossbar.

Data shape:

```json
{
  "player_name": "DemoPlayer",
  "team": "blue",
  "ball_speed": 121.7,
  "impact_force": 0.84
}
```

### player:updated

Fires when the local player's stats change during a match.

```javascript
RLOverlay.on("player:updated", (player) => {
  document.getElementById("boost").textContent = player.boost;
});
```

Data shape: see [State Reference - player](state.md#player).

### session:updated

Fires when the session totals are updated, typically at the end of a match.

```javascript
RLOverlay.on("session:updated", (session) => {
  document.getElementById("wins").textContent = session.wins;
});
```

Data shape: see [State Reference - session](state.md#session).

### statfeed:event

Fires for in-game feed items such as demolitions, epic saves, and clears.

```javascript
RLOverlay.on("statfeed:event", (feed) => {
  console.log(feed.event_name, "by", feed.player_name);
});
```

Data shape:

```json
{
  "type": "demolition",
  "event_name": "Demolition",
  "player_name": "Jstn",
  "secondary_name": "Fairy Peak"
}
```

`secondary_name` is the name of the other player involved, for example the player who was demolished.

### player:demolished

Fires when a demolition-specific overlay wants a simpler attacker/victim payload than the generic statfeed event.

Data shape:

```json
{
  "attacker": "Jstn",
  "victim": "Fairy Peak"
}
```

### podium:started

Fires when the post-match podium sequence begins.

Data shape:

```json
{ "match_guid": "preview-match-001" }
```

### replay:created

Fires when a replay is created or saved.

Data shape:

```json
{ "match_guid": "preview-match-001" }
```

### disconnected

Fires when the WebSocket connection drops. The script will automatically reconnect and emit `"connected"` once restored.

```javascript
RLOverlay.on("disconnected", () => {
  showOfflineIndicator();
});
```

Data shape: `{}`

## Transport envelope

All WebSocket messages use the same envelope:

```json
{
  "event": "match:update",
  "data": {}
}
```

The `event` field is stable and always contains the event name. The `data` field contains the payload documented above for that event.

### * (wildcard)

Fires for every event. Receives the event name and the event data.

```javascript
RLOverlay.on("*", (data, eventName) => {
  console.log(eventName, data);
});
```
