import asyncio

from rlstatsapi import (
    StatsClient,
    configure_stats_api,
    get_stats_api_status,
    StatsAPIConfigStatus,
)
from rlstatsapi.types import (
    UpdateStatePayload,
    GoalScoredPayload,
    MatchEndedPayload,
    StatfeedEventPayload,
    ClockUpdatedSecondsPayload,
)
from rlstatsapi.models import EventMessage

from . import session_storage
from .constants import RL_MAX_RECONNECT_DELAY, RL_RECONNECT_DELAY, RL_STATS_API_PORT
from .logger import get_logger

log = get_logger(__name__)


def _fmt_clock(seconds: int) -> str:
    """Format a clock time given in seconds to M:SS, capping negative values at 0."""
    seconds = max(0, seconds)
    return f"{seconds // 60}:{seconds % 60:02d}"


def _persist_session(state_manager) -> None:
    session_storage.save(state_manager.get_session_summary())


class RLStatsClient:
    """Manages the connection to the Rocket League Stats API."""

    def __init__(self, state_manager, connection_manager) -> None:
        self._state = state_manager
        self._ws = connection_manager
        self._connected = False
        self._task: asyncio.Task | None = None
        self._client: StatsClient | None = None
        self._last_match_key: tuple = ()

    @property
    def connected(self) -> bool:
        return self._connected

    @staticmethod
    def get_config_status() -> StatsAPIConfigStatus:
        return get_stats_api_status()

    @staticmethod
    def enable_stats_api() -> StatsAPIConfigStatus:
        return configure_stats_api(enabled=True)

    @staticmethod
    def disable_stats_api() -> StatsAPIConfigStatus:
        return configure_stats_api(enabled=False)

    async def run(self) -> None:
        """Main async method to connect to the Stats API and listen for events."""
        self._task = asyncio.current_task()

        status = get_stats_api_status()
        if status.found and not status.enabled:
            log.info("Stats API disabled - enabling automatically")
            try:
                configure_stats_api(enabled=True)
            except Exception as exc:  # pylint: disable=broad-exception-caught
                log.warning("Could not auto-configure Stats API: %s", exc)
        elif not status.found:
            log.warning("TAStatsAPI.ini not found, launch Rocket League once to create it")

        client = StatsClient(
            host="127.0.0.1",
            port=status.port or RL_STATS_API_PORT,
            reconnect=True,
            reconnect_delay=RL_RECONNECT_DELAY,
            max_reconnect_delay=RL_MAX_RECONNECT_DELAY,
            overflow="drop",
        )
        self._client = client
        self._register_handlers(client)

        try:
            async with client:
                # block forever inside the context manager so the client stays
                # connected and can receive events. CancelledError from cancel()
                # will break out of this wait and trigger the context manager
                # cleanup (graceful disconnect).
                await asyncio.Event().wait()
        except asyncio.CancelledError:
            self._connected = False

    def _register_handlers(self, client: StatsClient) -> None:
        """Register event handlers for the StatsClient events."""
        client.on_connect(self._on_connect)
        client.on_disconnect(self._on_disconnect)
        client.on("UpdateState", self._handle_update_state)
        client.on("GoalScored", self._handle_goal_scored)
        client.on("MatchCreated", self._handle_match_created)
        client.on("MatchInitialized", self._handle_match_initialized)
        client.on("MatchEnded", self._handle_match_ended)
        client.on("MatchDestroyed", self._handle_match_destroyed)
        client.on("ClockUpdatedSeconds", self._handle_clock)
        client.on("StatfeedEvent", self._handle_statfeed)
        client.on("GoalReplayStart", lambda msg: self._handle_goal_replay(msg, "start"))
        client.on("GoalReplayEnd", lambda msg: self._handle_goal_replay(msg, "end"))

    async def _on_connect(self) -> None:
        self._connected = True
        log.info("Connected to Rocket League Stats API")

    async def _on_disconnect(self) -> None:
        self._connected = False
        log.info("Disconnected - reconnecting…")

    async def _handle_update_state(self, msg: EventMessage) -> None:
        """Handle the UpdateState event."""
        data: UpdateStatePayload = msg.data  # type: ignore[assignment]
        game = data.get("Game", {})
        players = data.get("Players", [])

        blue, orange, overtime = 0, 0, bool(game.get("bOvertime", False))
        for team in game.get("Teams", []):
            if team.get("TeamNum") == 0:
                blue = team.get("Score", 0)
            elif team.get("TeamNum") == 1:
                orange = team.get("Score", 0)

        match_key = (blue, orange, overtime)
        if match_key != self._last_match_key:
            was_overtime = self._state.match.overtime
            self._last_match_key = match_key
            payload = {"blue_score": blue, "orange_score": orange, "overtime": overtime}
            self._state.update_from_event("match:update", payload)
            await self._ws.broadcast("match:update", self._state.get_full_state()["match"])
            if overtime and not was_overtime:
                await self._ws.broadcast("overtime:started", {})

        # bHasTarget is true when the local player is actively in a match.
        # Target.Shortcut is an internal RLID we use to find the local player
        # inside the Players list and read their live stats.
        if not game.get("bHasTarget"):
            return
        target_shortcut = game.get("Target", {}).get("Shortcut")
        if target_shortcut is None:
            return
        local = next((p for p in players if p.get("Shortcut") == target_shortcut), None)
        if local is None:
            return

        player_payload = {
            "name": local.get("Name", ""),
            "goals": local.get("Goals", 0),
            "assists": local.get("Assists", 0),
            "saves": local.get("Saves", 0),
            "shots": local.get("Shots", 0),
            "score": local.get("Score", 0),
            "boost": local.get("Boost", 0),
            "demos": local.get("Demos", 0),
        }
        self._state.update_from_event("player:updated", player_payload)
        _persist_session(self._state)
        await self._ws.broadcast("player:updated", self._state.get_full_state()["player"])

    async def _handle_clock(self, msg: EventMessage) -> None:
        data: ClockUpdatedSecondsPayload = msg.data  # type: ignore[assignment]
        seconds = data.get("TimeSeconds", 0)
        overtime = bool(data.get("bOvertime", False))
        self._state.update_from_event(
            "match:update", {"clock": _fmt_clock(seconds), "overtime": overtime}
        )
        await self._ws.broadcast("match:update", self._state.get_full_state()["match"])

    async def _handle_goal_scored(self, msg: EventMessage) -> None:
        data: GoalScoredPayload = msg.data  # type: ignore[assignment]
        scorer = data.get("Scorer", {})
        # assister can be None when there is no assist
        assister = data.get("Assister") or {}
        payload = {
            "player_name": scorer.get("Name", ""),
            "team": "blue" if scorer.get("TeamNum", 0) == 0 else "orange",
            "assister_name": assister.get("Name", ""),
            "goal_speed": data.get("GoalSpeed", 0.0),
        }
        self._state.update_from_event("goal:scored", payload)
        await self._ws.broadcast("goal:scored", payload)
        await self._ws.broadcast("match:update", self._state.get_full_state()["match"])

    async def _handle_match_created(self, msg: EventMessage) -> None:
        # reset the cache so the first UpdateState of the new match always broadcasts,
        # even if the score is still 0-0 (same as the previous match final state).
        self._last_match_key = ()
        payload = {"match_guid": msg.data.get("MatchGuid", "")}
        self._state.update_from_event("match:started", payload)
        _persist_session(self._state)
        await self._ws.broadcast("match:started", payload)

    async def _handle_match_initialized(self, msg: EventMessage) -> None:
        await self._ws.broadcast("match:initialized", {"match_guid": msg.data.get("MatchGuid", "")})

    async def _handle_match_ended(self, msg: EventMessage) -> None:
        data: MatchEndedPayload = msg.data  # type: ignore[assignment]
        winner_team = data.get("WinnerTeamNum", -1)
        # determine which team the local player is on. Fall back to blue (0)
        # if the player name is unknown or the RL state tracker has no data.
        local_team = 0
        if self._state.player.name and self._client:
            tp = self._client.state.target_player
            if tp is not None:
                local_team = tp.team_num
        payload = {"won": winner_team == local_team, "winner_team_num": winner_team}
        self._state.update_from_event("match:ended", payload)
        _persist_session(self._state)
        await self._ws.broadcast("match:ended", payload)
        await self._ws.broadcast("session:updated", self._state.get_full_state()["session"])

    async def _handle_match_destroyed(self, _msg: EventMessage) -> None:
        await self._ws.broadcast("match:destroyed", {})

    async def _handle_statfeed(self, msg: EventMessage) -> None:
        data: StatfeedEventPayload = msg.data  # type: ignore[assignment]
        main = data.get("MainTarget") or {}
        secondary = data.get("SecondaryTarget") or {}
        event_name = data.get("EventName", "")
        payload = {
            "type": data.get("Type", ""),
            "event_name": event_name,
            "player_name": main.get("Name", ""),
            "secondary_name": secondary.get("Name", ""),
        }
        await self._ws.broadcast("statfeed:event", payload)
        if event_name == "Demolition":
            demolition_payload = {
                "attacker": main.get("Name", ""),
                "victim": secondary.get("Name", ""),
            }
            self._state.update_from_event("player:demolished", demolition_payload)
            _persist_session(self._state)
            await self._ws.broadcast(
                "player:demolished",
                demolition_payload,
            )
            await self._ws.broadcast("session:updated", self._state.get_full_state()["session"])

    async def _handle_goal_replay(self, _msg, phase: str) -> None:
        await self._ws.broadcast("goal:replay", {"phase": phase})

    def cancel(self, loop: asyncio.AbstractEventLoop) -> None:
        self._connected = False
        if self._task is not None:
            loop.call_soon_threadsafe(self._task.cancel)
