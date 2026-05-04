# State Reference

The hub maintains three state objects: `match`, `player`, and `session`. All three are included in the `"connected"` event and are also available via `RLOverlay.getState()`.

## match

Represents the current match.

| Field | Type | Description |
|---|---|---|
| `blue_score` | number | Goals scored by the blue team |
| `orange_score` | number | Goals scored by the orange team |
| `clock` | string | Remaining time in `M:SS` format, e.g. `"4:32"` |
| `overtime` | boolean | Whether the match is in overtime |
| `is_active` | boolean | Whether a match is currently in progress |

Example:

```json
{
  "blue_score": 2,
  "orange_score": 1,
  "clock": "1:14",
  "overtime": false,
  "is_active": true
}
```

The `match:update` event delivers this object every time any field changes. The `connected` event includes it inside `state.match`.

## player

Represents the local player's current match stats.

| Field | Type | Description |
|---|---|---|
| `name` | string | Player name as shown in-game |
| `goals` | number | Goals scored in the current match |
| `assists` | number | Assists in the current match |
| `saves` | number | Saves in the current match |
| `shots` | number | Shots on goal in the current match |
| `score` | number | Match score (points) |
| `boost` | number | Current boost amount, 0 to 100 |
| `demos` | number | Demolitions in the current match |

Example:

```json
{
  "name": "Jstn",
  "goals": 2,
  "assists": 1,
  "saves": 3,
  "shots": 5,
  "score": 720,
  "boost": 64,
  "demos": 0
}
```

All stats reset at the start of each new match. The `player:updated` event delivers this object when stats change.

## session

Cumulative totals for the current play session. These persist across matches and across app restarts until you explicitly start a new session from the hub.

| Field | Type | Description |
|---|---|---|
| `matches` | number | Total matches played this session |
| `wins` | number | Matches won this session |
| `losses` | number | Matches lost this session |
| `goals` | number | Total goals across all session matches |
| `assists` | number | Total assists across all session matches |
| `saves` | number | Total saves across all session matches |

Example:

```json
{
  "matches": 7,
  "wins": 4,
  "losses": 3,
  "goals": 18,
  "assists": 9,
  "saves": 22
}
```

The `session:updated` event delivers this object when totals update. Session totals are driven by live player stat deltas and match results. The active session is persisted by the app and restored on launch. Preview Mode can simulate a `session:reset` event for testing without changing the persisted live session.

## Accessing state

The recommended pattern is to initialize from the `"connected"` event and update from individual events:

```javascript
function applyMatch(match) {
  if (!match) return;
  document.getElementById("blue-score").textContent  = match.blue_score  ?? 0;
  document.getElementById("orange-score").textContent = match.orange_score ?? 0;
  document.getElementById("timer").textContent        = match.clock        ?? "5:00";
}

RLOverlay.on("connected",    (state) => applyMatch(state.match));
RLOverlay.on("match:update", applyMatch);
```

If you need state outside an event handler, use `RLOverlay.getLatestState()` for cached state or `await RLOverlay.getState()` for a guaranteed fresh fetch from the server.
