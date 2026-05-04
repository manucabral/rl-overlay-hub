# Testing and Preview

You do not need Rocket League running to develop and test overlays. The hub includes a Preview Mode that injects dummy state and lets you simulate game events.

## Enabling Preview Mode

In the hub, go to the Preview tab and toggle the Preview switch. When Preview Mode is active:

- The hub populates all state objects with realistic dummy data
- A `"connected"` event is broadcast to all connected overlays with the preview state
- Simulated events can be triggered from the hub

Preview state values:

```json
{
  "match": {
    "blue_score": 3,
    "orange_score": 2,
    "clock": "0:42",
    "overtime": false,
    "is_active": true
  },
  "player": {
    "name": "DemoPlayer",
    "goals": 2,
    "assists": 1,
    "saves": 4,
    "shots": 6,
    "score": 810,
    "boost": 72,
    "demos": 0
  },
  "session": {
    "matches": 5,
    "wins": 3,
    "losses": 2,
    "goals": 12,
    "assists": 7,
    "saves": 18
  }
}
```

## Simulating events

While Preview Mode is on, the hub shows buttons to simulate individual events. Click a button and the corresponding event is broadcast to all connected overlays via WebSocket.

| Button | Event fired | What changes |
|---|---|---|
| Goal scored | `goal:scored` | Blue score increments; event includes player and assister names |
| Overtime | `overtime:started` | Match `overtime` field becomes `true` |
| Match started | `match:started` | Match and player stats reset |
| Match ended | `match:ended` | Session wins increment |
| Reset session | `session:reset` then `session:updated` | Session totals reset to zero |

## Development workflow

1. Start the hub.
2. Enable Preview Mode.
3. Open your overlay URL in a browser tab.
4. Open the browser developer console to see errors and logs.
5. Edit your HTML, CSS, and JS files.
6. Reload the browser tab to pick up changes.
7. Click the simulation buttons in the hub to trigger events and verify your animations and logic.

The hub does not auto-reload overlays when you save files. You must reload the browser tab manually.

## Verbose logging

If you need to see detailed server logs while developing, go to the hub Settings tab, enable the Verbose logging checkbox, and click Save Settings. The log level changes immediately without a restart. Logs are written to `~/.rl-overlay-hub/logs/app.log` and also displayed in the terminal if you launched the hub from the command line.

## Checking the WebSocket directly

If your overlay is not receiving events, you can verify the WebSocket is working by opening the browser console on the overlay page and checking for connection logs. You can also use a tool like `wscat` to connect manually:

```
wscat -c ws://127.0.0.1:49100/ws
```

The hub sends a `connected` message immediately on connection with the current full state.
