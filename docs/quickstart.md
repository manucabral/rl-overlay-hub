# Quick Start

This guide walks you from an empty folder to a working overlay installed in the hub and visible in OBS.

## Step 1 - Copy the creator template

Inside the RL Overlay Hub directory there is a `creator-template` folder. Copy the entire folder to:

```
~/.rl-overlay-hub/overlays/installed/my-overlay/
```

On Windows that path expands to `C:\Users\<you>\.rl-overlay-hub\overlays\installed\my-overlay\`.

The template contains:

```
my-overlay/
    manifest.json
    index.html
    style.css
    script.js
```

You can also use the hub's own "Install local folder" button in the Overlays tab to install any folder on your machine.

## Step 2 - Edit manifest.json

Open `manifest.json` and fill in at least the `id`, `name`, and `author` fields.

```json
{
  "id": "my-overlay",
  "name": "My Overlay",
  "version": "1.0.0",
  "author": "YourName",
  "description": "A brief description of what your overlay does.",
  "entry": "index.html",
  "preview": "preview.png"
}
```

The `id` must be unique and must match the folder name. See [Manifest Reference](manifest.md) for all fields.

## Step 3 - Open the hub and verify the overlay appears

Start RL Overlay Hub (`python run.py` or the desktop app). Go to the Overlays tab. Your overlay should appear in the list. If it does not, check that `manifest.json` is valid JSON and that the folder name matches the `id` field.

## Step 4 - Enable Preview Mode

Click the Preview toggle in the hub. This activates dummy state data so you can develop without Rocket League running. The WebSocket will immediately broadcast a `"connected"` event with sample match, player, and session values.

## Step 5 - Open the overlay URL in a browser

Copy the overlay URL from the hub (it looks like `http://127.0.0.1:49100/overlay/my-overlay/`) and paste it into a browser tab. Open the browser developer console. You should see the scoreboard rendering with preview data.

## Step 6 - Edit the overlay

Edit `index.html`, `style.css`, and `script.js` to build your UI. Reload the browser tab to see changes. The template `script.js` already subscribes to `match:update` and `goal:scored` as a starting point.

```javascript
// Listen for live match state changes
RLOverlay.on("match:update", (match) => {
  document.getElementById("blue-score").textContent = match.blue_score;
  document.getElementById("orange-score").textContent = match.orange_score;
  document.getElementById("timer").textContent = match.clock;
});

// Sync immediately on first connect
RLOverlay.on("connected", (state) => {
  // state.match, state.player, state.session are all available here
});
```

## Step 7 - Add to OBS

In OBS, add a Browser Source. Paste the overlay URL. Set width to 1920 and height to 1080. Make sure the source is sized to cover the full canvas. See [Adding to OBS](obs.md) for detailed instructions.

## Step 8 - Submit it to the community registry

If you want your overlay to be installable by other users from the Community tab, submit it to the main repository:

1. Add your overlay folder to `community-overlays/` in the repository.
2. Update `community-overlays/registry.json` with your overlay metadata.
3. Open a pull request with both changes.

That PR is how a new community overlay gets added to the shared registry used by the app.

## What comes next

- [JavaScript API](api.md) lists every event and method available
- [State Reference](state.md) describes every field in the match, player, and session objects
- [Testing and Preview](testing.md) explains how to simulate goals and other events
- [Examples](examples/scoreboard.md) walks through the two built-in overlays line by line
