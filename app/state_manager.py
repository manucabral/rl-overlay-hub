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
    },
}

# RL sends cumulative match totals for these fields; deltas are tracked for session totals.
_CUMULATIVE_PLAYER_FIELDS = ("goals", "assists", "saves")


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

    def apply_preview_event(self, event_name: str) -> dict | None:
        if not self.preview:
            return None
        handler = {
            "goal:scored": self._preview_goal_scored,
            "overtime:started": self._preview_overtime_started,
            "match:ended": self._preview_match_ended,
            "match:started": self._preview_match_started,
            "session:reset": self._preview_session_reset,
        }.get(event_name)
        return handler() if handler else None

    def _preview_goal_scored(self) -> dict:
        self._preview_match["blue_score"] = self._preview_match.get("blue_score", 0) + 1
        self._preview_session["goals"] = self._preview_session.get("goals", 0) + 1
        return {"player_name": self._preview_player.get("name", "DemoPlayer"), "team": "blue"}

    def _preview_overtime_started(self) -> dict:
        self._preview_match["overtime"] = True
        return {}

    def _preview_match_ended(self) -> dict:
        self._preview_match["is_active"] = False
        self._preview_session["matches"] = self._preview_session.get("matches", 0) + 1
        self._preview_session["wins"] = self._preview_session.get("wins", 0) + 1
        return {"won": True}

    def _preview_match_started(self) -> dict:
        self._preview_match = copy.deepcopy(_PREVIEW_DEFAULTS["match"])
        self._preview_player = copy.deepcopy(_PREVIEW_DEFAULTS["player"])
        return {}

    def _preview_session_reset(self) -> dict:
        self._preview_session = SessionState().model_dump()
        return {}

    def update_from_event(self, event_name: str, data: dict) -> None:
        handler = {
            "match:update": self._handle_match_update,
            "match:started": self._handle_match_started,
            "match:ended": self._handle_match_ended,
            "player:updated": self._handle_player_updated,
            "overtime:started": self._handle_overtime_started,
            "goal:scored": self._handle_goal_scored,
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
