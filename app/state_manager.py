import copy

from pydantic import BaseModel

from .schemas import (
    ActiveSession,
    ArchivedSession,
    FullStatePayload,
    SessionStatePayload,
    SessionStore,
    utc_now,
)


class MatchState(BaseModel):
    blue_score: int = 0
    orange_score: int = 0
    clock: str = "5:00"
    overtime: bool = False
    is_active: bool = False


class PlayerState(BaseModel):
    name: str = ""
    goals: int = 0
    assists: int = 0
    saves: int = 0
    shots: int = 0
    score: int = 0
    boost: int = 0
    demos: int = 0


class SessionState(BaseModel):
    matches: int = 0
    wins: int = 0
    losses: int = 0
    goals: int = 0
    assists: int = 0
    saves: int = 0
    demolitions: int = 0
    demolitions_taken: int = 0


_PREVIEW_DEFAULTS = {
    "match": {
        "blue_score": 3,
        "orange_score": 2,
        "clock": "0:42",
        "overtime": False,
        "is_active": True,
    },
    "player": {
        "name": "DemoPlayer",
        "goals": 2,
        "assists": 1,
        "saves": 4,
        "shots": 6,
        "score": 810,
        "boost": 72,
        "demos": 0,
    },
    "session": {
        "matches": 5,
        "wins": 3,
        "losses": 2,
        "goals": 12,
        "assists": 7,
        "saves": 18,
        "demolitions": 4,
        "demolitions_taken": 2,
    },
}

# RL sends cumulative match totals for these fields; deltas are tracked for session totals.
_CUMULATIVE_PLAYER_FIELDS = ("goals", "assists", "saves")
_PREVIEW_MATCH_GUID = "preview-match-001"

_PREVIEW_EVENT_ALIASES = {
    "goal-replay-start": "goal:replay:start",
    "goal-replay-will-end": "goal:replay:will-end",
    "goal-replay-end": "goal:replay:end",
    "countdown-begin": "countdown:begin",
    "round-started": "round:started",
    "match-paused": "match:paused",
    "match-unpaused": "match:unpaused",
    "ball-hit": "ball:hit",
    "crossbar-hit": "crossbar:hit",
    "podium-started": "podium:started",
    "replay-created": "replay:created",
    "statfeed-demo": "statfeed:event",
    "player-demolished": "player:demolished",
}


class StateManager:
    def __init__(self, preview: bool = False, session_store: SessionStore | None = None) -> None:
        self.match = MatchState()
        self.player = PlayerState()
        self._session_store = session_store or SessionStore()
        self.session = SessionState.model_validate(
            self._session_store.active_session.stats.model_dump()
        )
        self._preview_match: dict = {}
        self._preview_player: dict = {}
        self._preview_session: dict = {}
        self._preview_match_guid = _PREVIEW_MATCH_GUID
        self.preview = False
        if preview:
            self.set_preview(True)

    def get_full_state(self) -> dict:
        if self.preview:
            payload = {
                "match": dict(self._preview_match),
                "player": dict(self._preview_player),
                "session": dict(self._preview_session),
            }
        else:
            payload = {
                "match": self.match.model_dump(),
                "player": self.player.model_dump(),
                "session": self.session.model_dump(),
            }
        return FullStatePayload.model_validate(payload).model_dump()

    def set_preview(self, enabled: bool) -> None:
        self.preview = enabled
        if enabled:
            self._preview_match = copy.deepcopy(_PREVIEW_DEFAULTS["match"])
            self._preview_player = copy.deepcopy(_PREVIEW_DEFAULTS["player"])
            self._preview_session = copy.deepcopy(_PREVIEW_DEFAULTS["session"])
            self._preview_match_guid = _PREVIEW_MATCH_GUID

    def apply_preview_event(self, event_name: str) -> tuple[str, dict, bool] | None:
        if not self.preview:
            return None
        public_event = _PREVIEW_EVENT_ALIASES.get(event_name, event_name)
        event_meta = {
            "goal:scored": (self._preview_goal_scored, True),
            "overtime:started": (self._preview_overtime_started, True),
            "match:ended": (self._preview_match_ended, True),
            "match:started": (self._preview_match_started, True),
            "match:initialized": (self._preview_match_initialized, False),
            "match:destroyed": (self._preview_match_destroyed, True),
            "session:reset": (self._preview_session_reset, True),
            "goal:replay:start": (self._preview_goal_replay_start, False),
            "goal:replay:will-end": (self._preview_goal_replay_will_end, False),
            "goal:replay:end": (self._preview_goal_replay_end, False),
            "statfeed:event": (self._preview_statfeed_event, False),
            "player:demolished": (self._preview_player_demolished, False),
            "countdown:begin": (self._preview_countdown_begin, False),
            "round:started": (self._preview_round_started, False),
            "match:paused": (self._preview_match_paused, False),
            "match:unpaused": (self._preview_match_unpaused, False),
            "ball:hit": (self._preview_ball_hit, False),
            "crossbar:hit": (self._preview_crossbar_hit, False),
            "podium:started": (self._preview_podium_started, False),
            "replay:created": (self._preview_replay_created, False),
        }.get(public_event)
        if event_meta is None:
            return None
        handler, mutates_state = event_meta
        return public_event, handler(), mutates_state

    def _preview_goal_scored(self) -> dict:
        self._preview_match["blue_score"] = self._preview_match.get("blue_score", 0) + 1
        self._preview_session["goals"] = self._preview_session.get("goals", 0) + 1
        return {
            "player_name": self._preview_player.get("name", "DemoPlayer"),
            "team": "blue",
            "assister_name": "Teammate",
            "goal_speed": 143.0,
        }

    def _preview_overtime_started(self) -> dict:
        self._preview_match["overtime"] = True
        self._preview_match["clock"] = "0:00"
        return {}

    def _preview_match_ended(self) -> dict:
        self._preview_match["is_active"] = False
        self._preview_session["matches"] = self._preview_session.get("matches", 0) + 1
        self._preview_session["wins"] = self._preview_session.get("wins", 0) + 1
        return {"won": True, "winner_team_num": 0}

    def _preview_match_started(self) -> dict:
        self._preview_match = copy.deepcopy(_PREVIEW_DEFAULTS["match"])
        self._preview_player = copy.deepcopy(_PREVIEW_DEFAULTS["player"])
        return {"match_guid": self._preview_match_guid}

    def _preview_match_initialized(self) -> dict:
        return {"match_guid": self._preview_match_guid}

    def _preview_match_destroyed(self) -> dict:
        self._preview_match["is_active"] = False
        self._preview_match["clock"] = "5:00"
        self._preview_match["overtime"] = False
        return {}

    def _preview_session_reset(self) -> dict:
        self._preview_session = SessionState().model_dump()
        return {}

    def _preview_goal_replay_start(self) -> dict:
        return {"phase": "start"}

    def _preview_goal_replay_will_end(self) -> dict:
        return {"match_guid": self._preview_match_guid}

    def _preview_goal_replay_end(self) -> dict:
        return {"phase": "end"}

    def _preview_statfeed_event(self) -> dict:
        return {
            "type": "demolition",
            "event_name": "Demolition",
            "player_name": self._preview_player.get("name", "DemoPlayer"),
            "secondary_name": "RivalPlayer",
        }

    def _preview_player_demolished(self) -> dict:
        return {"attacker": self._preview_player.get("name", "DemoPlayer"), "victim": "RivalPlayer"}

    def _preview_countdown_begin(self) -> dict:
        return {"match_guid": self._preview_match_guid}

    def _preview_round_started(self) -> dict:
        return {"match_guid": self._preview_match_guid}

    def _preview_match_paused(self) -> dict:
        return {"match_guid": self._preview_match_guid}

    def _preview_match_unpaused(self) -> dict:
        return {"match_guid": self._preview_match_guid}

    def _preview_ball_hit(self) -> dict:
        return {
            "player_name": self._preview_player.get("name", "DemoPlayer"),
            "team": "blue",
            "pre_hit_speed": 82.5,
            "post_hit_speed": 109.4,
        }

    def _preview_crossbar_hit(self) -> dict:
        return {
            "player_name": self._preview_player.get("name", "DemoPlayer"),
            "team": "blue",
            "ball_speed": 121.7,
            "impact_force": 0.84,
        }

    def _preview_podium_started(self) -> dict:
        return {"match_guid": self._preview_match_guid}

    def _preview_replay_created(self) -> dict:
        return {"match_guid": self._preview_match_guid}

    def update_from_event(self, event_name: str, data: dict) -> None:
        handler = {
            "match:update": self._handle_match_update,
            "match:started": self._handle_match_started,
            "match:ended": self._handle_match_ended,
            "player:updated": self._handle_player_updated,
            "overtime:started": self._handle_overtime_started,
            "goal:scored": self._handle_goal_scored,
            "player:demolished": self._handle_player_demolished,
        }.get(event_name)
        if handler:
            handler(data)

    def _handle_match_update(self, data: dict) -> None:
        for field in ("blue_score", "orange_score", "clock", "overtime"):
            if field in data:
                setattr(self.match, field, data[field])

    def _handle_match_started(self, _data: dict) -> None:
        self.match = MatchState(is_active=True)
        self.player = PlayerState()
        self._preview_match = {}
        self._preview_player = {}
        self._touch_active_session()

    def _handle_match_ended(self, data: dict) -> None:
        self.match.is_active = False
        self.session.matches += 1
        if data.get("won"):
            self.session.wins += 1
        else:
            self.session.losses += 1
        self._touch_active_session()

    def _handle_player_updated(self, data: dict) -> None:
        if "name" in data:
            self.player.name = data["name"]
        for field in _CUMULATIVE_PLAYER_FIELDS:
            if field in data:
                self._apply_cumulative(field, data[field])
        for field in ("shots", "score", "boost", "demos"):
            if field in data:
                setattr(self.player, field, data[field])
        self._touch_active_session()

    def _apply_cumulative(self, field: str, new_val: int) -> None:
        delta = new_val - getattr(self.player, field)
        if delta > 0:
            setattr(self.session, field, getattr(self.session, field) + delta)
        setattr(self.player, field, new_val)

    def _handle_goal_scored(self, _data: dict) -> None:
        # Match/player/session state should be driven by authoritative RL updates.
        # Goal events are broadcast for overlay reactions, not state mutation.
        return None

    def _handle_overtime_started(self, _data: dict) -> None:
        self.match.overtime = True

    def _handle_player_demolished(self, data: dict) -> None:
        player_name = self.player.name
        attacker = data.get("attacker", "")
        victim = data.get("victim", "")
        if player_name and attacker == player_name:
            self.session.demolitions += 1
        if player_name and victim == player_name:
            self.session.demolitions_taken += 1
        self._touch_active_session()

    def reset_session(self) -> None:
        self.session = SessionState()
        self._session_store.active_session = ActiveSession(stats=SessionStatePayload())

    def _touch_active_session(self) -> None:
        if self.preview:
            return
        self._session_store.active_session.stats = SessionStatePayload.model_validate(
            self.session.model_dump()
        )
        self._session_store.active_session.last_updated_at = utc_now()

    def get_session_summary(self) -> SessionStore:
        self._touch_active_session()
        return self._session_store.model_copy(deep=True)

    def set_session_store(self, session_store: SessionStore) -> None:
        self._session_store = session_store
        self.session = SessionState.model_validate(session_store.active_session.stats.model_dump())

    def archive_current_and_start_new(self) -> ArchivedSession:
        self._touch_active_session()
        current = self._session_store.active_session
        archived = ArchivedSession(
            id=current.id,
            started_at=current.started_at,
            ended_at=utc_now(),
            stats=SessionStatePayload.model_validate(current.stats.model_dump()),
        )
        self._session_store.archived_sessions.insert(0, archived)
        self._session_store.active_session = ActiveSession(stats=SessionStatePayload())
        self.session = SessionState()
        self.match = MatchState()
        self.player = PlayerState()
        return archived
