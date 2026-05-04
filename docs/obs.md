# Adding to OBS

Overlays run in OBS as Browser Sources. A Browser Source loads a URL into a Chromium-based renderer. The overlay page communicates with the hub over WebSocket and renders on top of your game capture.

## Getting your overlay URL

In RL Overlay Hub, go to the Overlays tab. Find your overlay in the list and copy the URL. It follows this pattern:

```
http://127.0.0.1:49100/overlay/<overlay-id>/
```

Replace `49100` with the port shown in the hub if you changed it in Settings.

## Adding a Browser Source

1. In OBS, in the Sources panel, click the plus button and choose Browser.
2. Give the source a name and click OK.
3. In the properties window:
   - Set URL to your overlay URL.
   - Set Width to `1920`.
   - Set Height to `1080`.
   - Leave "Use custom frame rate" unchecked unless you have a specific reason.
   - Check "Shutdown source when not visible" if you want the overlay to stop running when the source is hidden.
   - Leave "Refresh browser when scene becomes active" unchecked unless your overlay needs to re-initialize on scene switches.
4. Click OK.

## Making the overlay fill the canvas

After adding the source, right-click it in the Sources panel, choose Transform, then Fit to screen. This scales the Browser Source to fill your output canvas.

Alternatively, hold Alt and drag the edges of the source to crop it, or use Edit, Transform, Edit Transform to set exact position and size values.

## Transparency

OBS renders the Browser Source with transparency. Your overlay's CSS must set `body { background: transparent; }` for the game capture to show through. If you see a black or white background instead of the game, check that this style is applied and not overridden.

The creator template includes this by default in `style.css`.

## Multiple overlays

You can add multiple overlays as separate Browser Sources in the same scene. Each one connects independently to the hub WebSocket. All overlays receive all events simultaneously.

## Refreshing an overlay

If you update your overlay files while OBS is running, right-click the Browser Source in the Sources panel and choose Properties, then click Refresh cache of current page. This forces OBS to reload the page and pick up your changes.

## Overlay not connecting

If your overlay renders but shows no data:

- Confirm RL Overlay Hub is running.
- Confirm the port in the URL matches the port in hub Settings.
- Enable Preview Mode in the hub and check if the overlay updates.
- Open the OBS log (Help, Log Files, View Current Log) and search for errors.
- Check the browser console by right-clicking the Browser Source, choosing Interact, then opening developer tools from there.
