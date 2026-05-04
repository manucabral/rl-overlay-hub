# Example: Goal Banner

The goal-banner overlay shows an animated banner at the top of the screen when a goal is scored. The banner displays the scorer's name and uses a color bar to indicate which team scored. It disappears automatically after 4 seconds.

This example demonstrates event-triggered animations and cleanup logic for rapid events.

## File structure

```
goal-banner/
    manifest.json
    index.html
    style.css
    script.js
    preview.png
```

## script.js

```javascript
const banner   = document.getElementById("banner");
const scorerEl = document.getElementById("scorer-name");
const teamBar  = document.getElementById("team-bar");

let hideTimer = null;

function showGoal(goal) {
  if (hideTimer) {
    clearTimeout(hideTimer);
    hideTimer = null;
  }

  scorerEl.textContent  = goal.player_name || "Goal!";
  teamBar.className     = `team-bar ${goal.team || ""}`;

  banner.classList.remove("hide", "show");
  void banner.offsetWidth;
  banner.classList.add("show");

  hideTimer = setTimeout(() => {
    banner.classList.remove("show");
    banner.classList.add("hide");
  }, 4000);
}

RLOverlay.on("goal:scored", showGoal);
```

### How showGoal works

Every call to `showGoal` follows the same steps:

1. Cancel any pending hide timer. If two goals are scored within 4 seconds, the banner stays visible and restarts from the new goal rather than disappearing mid-display.

2. Write the scorer's name. The `|| "Goal!"` fallback handles the case where `player_name` is empty or undefined.

3. Set the team color bar. The `teamBar.className` assignment replaces all classes on the element with `team-bar blue` or `team-bar orange`. CSS rules in `style.css` use these classes to set the bar color.

4. Reset and restart the animation. Removing both `show` and `hide` classes clears the animation state. `void banner.offsetWidth` forces a layout reflow so the browser registers the class removal before the new class is added. Adding `show` starts the entry animation.

5. Schedule the hide. After 4000 milliseconds, the `show` class is replaced with `hide`, which triggers the exit animation. The timer reference is saved in `hideTimer` so it can be cancelled if a new goal arrives before it fires.

### The animation CSS

```css
.banner.show {
  animation: bannerIn 0.4s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}

.banner.hide {
  animation: bannerOut 0.35s ease-in forwards;
}

@keyframes bannerIn {
  from { opacity: 0; transform: translateY(-60px) scale(0.7); }
  to   { opacity: 1; transform: translateY(0)     scale(1);   }
}

@keyframes bannerOut {
  from { opacity: 1; transform: scale(1);   }
  to   { opacity: 0; transform: scale(1.08); }
}
```

`bannerIn` slides the banner down from above while scaling it up. The `cubic-bezier(0.22, 1, 0.36, 1)` easing produces a springy overshoot feel. `bannerOut` fades it out while scaling it up slightly, giving the impression it pops away.

The `forwards` fill mode keeps the final animation frame applied after the animation ends. Without it, the banner would snap back to its initial state when the animation completes.

## What to learn from this example

- Store the timeout reference in a variable and cancel it at the start of each new event. Without this, overlapping events produce unpredictable behavior.
- The `|| "fallback"` pattern on string fields prevents blank or broken UI when data is missing.
- Replacing `className` entirely is the simplest way to switch between a fixed set of CSS state classes.
- The reflow trick (`void el.offsetWidth`) is required any time you need to restart an animation by toggling classes.
- The overlay only listens to one event (`goal:scored`) and ignores everything else. Keep overlays focused on the data they actually use.
