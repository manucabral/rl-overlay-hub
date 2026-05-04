/**
 * RLOverlay API
 * Subscribe to live Rocket League data from RL Overlay Hub.
 *
 * Events:
 *  - "connected"          Full state snapshot: { match, player, session }
 *  - "match:started"      New match loaded: { match_guid }
 *  - "match:initialized"  Match ready: { match_guid }
 *  - "match:update"       Score/clock/overtime changed:
 *                          { blue_score, orange_score, clock, overtime, is_active }
 *  - "match:ended"        Match finished: { won, winner_team_num }
 *  - "match:destroyed"    Match unloaded: {}
 *  - "goal:scored"        Goal scored:
 *                          { player_name, team, assister_name, goal_speed }
 *  - "overtime:started"   Overtime started: {}
 *  - "goal:replay"        Replay phase changed: { phase }
 *  - "player:updated"     Local player stats changed:
 *                          { name, goals, assists, saves, shots, score }
 *  - "session:updated"    Session totals changed:
 *                          { matches, wins, losses, goals, assists, saves }
 *  - "statfeed:event"     In-game feed event:
 *                          { type, event_name, player_name, secondary_name }
 *  - "disconnected"       WebSocket disconnected; auto-reconnects in 3s.
 *  - "*"                  Debug listener for all events.
 *
 * Methods:
 *  - RLOverlay.on(event, fn)       Subscribe.
 *  - RLOverlay.off(event, fn)      Unsubscribe.
 *  - RLOverlay.getState()          Fetch fresh state. Returns Promise<State>.
 *  - RLOverlay.getLatestState()    Return last known state synchronously.
 *
 * OBS setup:
 *  1. Copy this folder to overlays/installed/<your-overlay-id>/
 *  2. Edit manifest.json.
 *  3. Open RL Overlay Hub -> Overlays -> copy URL.
 *  4. Add OBS Browser Source.
 *  5. Paste URL and set size to 1920×1080.
 *  6. Enable Preview Mode to test without Rocket League.
 */

// Get elements
const blueEl   = document.getElementById("blue-score");
const orangeEl = document.getElementById("orange-score");
const timerEl  = document.getElementById("timer");

// Update UI from match state
function applyMatch(match) {
  if (!match) return;
  blueEl.textContent   = match.blue_score  ?? 0;
  orangeEl.textContent = match.orange_score ?? 0;
  timerEl.textContent  = match.clock        ?? "5:00";
}

// Listen for live updates
RLOverlay.on("match:update", applyMatch);

// Sync immediately when connected (or on preview mode activation)
RLOverlay.on("connected", (state) => applyMatch(state.match));

// React to goals
RLOverlay.on("goal:scored", (goal) => {
  console.log("GOAL by", goal.player_name, "for team", goal.team);
  // Add your celebration animation here
});
