const banner = document.getElementById("banner");
const scorerEl = document.getElementById("scorer-name");
const teamBar = document.getElementById("team-bar");

let hideTimer = null;

function showGoal(goal) {
  if (hideTimer) {
    clearTimeout(hideTimer);
    hideTimer = null;
  }

  scorerEl.textContent = goal.player_name || "Goal!";
  teamBar.className = `team-bar ${goal.team || ""}`;

  banner.classList.remove("hide", "show");
  void banner.offsetWidth; // force reflow
  banner.classList.add("show");

  hideTimer = setTimeout(() => {
    banner.classList.remove("show");
    banner.classList.add("hide");
  }, 4000);
}

RLOverlay.on("goal:scored", showGoal);
