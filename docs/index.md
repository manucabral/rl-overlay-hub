# RL Overlay Hub - Creator Documentation

RL Overlay Hub is a desktop application that reads live data from Rocket League and broadcasts it to HTML-based overlays. Overlays are web pages that run inside OBS as Browser Sources. The hub serves them over a local HTTP server and pushes game events through a WebSocket connection.

This documentation covers how to build, install, and test your own overlay.

## What an overlay is

An overlay is a folder containing at minimum two files:

- `manifest.json` - metadata that tells the hub about your overlay (id, name, author)
- `index.html` - the page that OBS loads and displays on stream

You can include any additional files you need: CSS, JavaScript, images, fonts. All files in the folder are served as static assets relative to your `index.html`.

## How data reaches your overlay

The hub runs a FastAPI server on `http://127.0.0.1:49100` by default. When your `index.html` loads, it includes a script tag for `/overlay-api.js`. That script opens a WebSocket to the hub and exposes a global object called `window.RLOverlay`. You use `RLOverlay.on()` to subscribe to game events.

```
Rocket League -> rlstatsapi -> Hub (FastAPI) -> WebSocket -> Your overlay (browser)
```

Events include goal scored, match started, score updates, player stat changes, and more. The full list is in [JavaScript API](api.md).

## Pages in this documentation

- [Quick Start](quickstart.md) - create and install your first overlay in minutes
- [Manifest Reference](manifest.md) - all fields in `manifest.json`
- [JavaScript API](api.md) - `RLOverlay` methods and every event with its data shape
- [State Reference](state.md) - the match, player, and session objects in detail
- [Testing and Preview](testing.md) - test your overlay without Rocket League running
- [Adding to OBS](obs.md) - configure a Browser Source
- [Event Snippets](examples/event-snippets.md) - quick copy-paste patterns for simple events
- [Examples](examples/scoreboard.md) - annotated walkthroughs of the built-in overlays
