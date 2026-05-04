# Example: Minimal Scoreboard

The minimal-scoreboard overlay shows blue score, a timer, and orange score at the top center of the screen. It pulses the score element when a goal is scored and shows an overtime badge when the match enters overtime.

This is the simplest complete overlay in the hub and a good starting point.

If you want quick copy-paste patterns for other simple events, see [Event Snippets](event-snippets.md).

## File structure

```
minimal-scoreboard/
    manifest.json
    index.html
    style.css
    script.js
    preview.png
```

## manifest.json

```json
{
  "id": "minimal-scoreboard",
  "name": "Minimal Scoreboard",
  "version": "1.0.0",
  "author": "RL Overlay Hub",
  "description": "A clean scoreboard showing score, clock, and overtime status.",
  "entry": "index.html",
  "preview": "preview.png"
}
```

Nothing unusual here. The `id` matches the folder name. The `preview` field points to a screenshot used in the hub UI.

## script.js

```javascript
const blueEl   = document.getElementById("blue-score");
const orangeEl  = document.getElementById("orange-score");
const timerEl  = document.getElementById("timer");
const otBadge   = document.getElementById("overtime-badge");

function applyState(match) {
  if (!match) return;
  blueEl.textContent   = match.blue_score  ?? 0;
  orangeEl.textContent = match.orange_score ?? 0;
  timerEl.textContent  = match.clock        ?? "5:00";
  otBadge.classList.toggle("visible", !!match.overtime);
}

RLOverlay.on("match:update",  applyState);
RLOverlay.on("connected",     (s) => applyState(s.match));

RLOverlay.on("goal:scored", (goal) => {
  const el = goal.team === "blue" ? blueEl : orangeEl;
  el.classList.remove("pulse");
  void el.offsetWidth;
  el.classList.add("pulse");
  setTimeout(() => el.classList.remove("pulse"), 600);
});
```

### How applyState works

`applyState` takes a match object and writes each field to the DOM. The `?? 0` and `?? "5:00"` operators provide fallback values when the field is null or undefined, which can happen briefly on first load.

`otBadge.classList.toggle("visible", !!match.overtime)` adds or removes the `visible` class depending on whether overtime is true. This is cleaner than an if/else block.

### Why two listeners for applyState

`match:update` fires during a match when scores or the clock change. `connected` fires on first connect and on reconnect. Without the `connected` listener, the overlay would show default values until the first `match:update` arrives. By calling `applyState(s.match)` on connect, the overlay is immediately in sync.

### The pulse animation

When a goal is scored, the overlay identifies which team scored using `goal.team` and selects the corresponding DOM element. It then:

1. Removes the `pulse` class to reset the animation state.
2. Forces a layout reflow with `void el.offsetWidth`. This is necessary because removing and re-adding the same class in the same JavaScript task does not restart a CSS animation without a reflow in between.
3. Adds the `pulse` class to start the animation.
4. Removes it after 600 milliseconds so the animation can be triggered again on the next goal.

## What to learn from this example

- Always handle both `"connected"` and `"match:update"` so the overlay syncs on first load and on reconnect.
- Use `?? fallback` to guard against missing fields.
- The reflow trick (`void el.offsetWidth`) is the standard way to restart a CSS animation by toggling a class.
- Keep the overlay logic minimal. This script is 25 lines and handles everything correctly.
