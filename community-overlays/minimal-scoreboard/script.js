const blueEl   = document.getElementById("blue-score");
const orangeEl  = document.getElementById("orange-score");
const timerEl   = document.getElementById("timer");
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

// Pulse score on goal
RLOverlay.on("goal:scored", (goal) => {
  const el = goal.team === "blue" ? blueEl : orangeEl;
  el.classList.remove("pulse");
  void el.offsetWidth;
  el.classList.add("pulse");
  setTimeout(() => el.classList.remove("pulse"), 600);
});
