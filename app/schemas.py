from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .constants import DEFAULT_PORT


class MatchStatePayload(BaseModel):
    blue_score: int = 0
    orange_score: int = 0
    clock: str = "5:00"
    overtime: bool = False
    is_active: bool = False


class PlayerStatePayload(BaseModel):
    name: str = ""
    goals: int = 0
    assists: int = 0
    saves: int = 0
    shots: int = 0
    score: int = 0
    boost: int = 0
    demos: int = 0


class SessionStatePayload(BaseModel):
    matches: int = 0
    wins: int = 0
    losses: int = 0
    goals: int = 0
    assists: int = 0
    saves: int = 0


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ActiveSession(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    started_at: datetime = Field(default_factory=utc_now)
    last_updated_at: datetime = Field(default_factory=utc_now)
    stats: SessionStatePayload = Field(default_factory=SessionStatePayload)


class ArchivedSession(BaseModel):
    id: str
    started_at: datetime
    ended_at: datetime
    stats: SessionStatePayload


class SessionStore(BaseModel):
    active_session: ActiveSession = Field(default_factory=ActiveSession)
    archived_sessions: list[ArchivedSession] = Field(default_factory=list)


class SessionSummaryResponse(BaseModel):
    active_session: ActiveSession
    archived_sessions: list[ArchivedSession]


class FullStatePayload(BaseModel):
    match: MatchStatePayload
    player: PlayerStatePayload
    session: SessionStatePayload


class SettingsModel(BaseModel):
    port: int = Field(default=DEFAULT_PORT, ge=1, le=65535)
    preview_mode: bool = False
    verbose: bool = False
    installed_overlays: list[str] = Field(default_factory=list)
    disabled_overlays: list[str] = Field(default_factory=list)
    community_installed: list[str] = Field(default_factory=list)

    @field_validator(
        "installed_overlays", "disabled_overlays", "community_installed", mode="before"
    )
    @classmethod
    def _normalize_list(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise TypeError("Expected a list")
        return [str(item).strip() for item in value if str(item).strip()]


class OverlayManifest(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    name: str
    author: str = "Unknown"
    version: str = "1.0.0"
    description: str = ""
    preview: str | None = "preview.png"

    @field_validator("id", "name")
    @classmethod
    def _require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Must not be empty")
        return value


class OverlayInstallRequest(BaseModel):
    overlay_id: str
    registry_entry: dict[str, Any]


class LocalOverlayInstallRequest(BaseModel):
    path: str

    @property
    def path_obj(self) -> Path:
        return Path(self.path)


class PreviewToggleRequest(BaseModel):
    enabled: bool


class ToggleResponse(BaseModel):
    ok: bool = True
    enabled: bool


class PreviewToggleResponse(BaseModel):
    preview: bool


class NewSessionResponse(BaseModel):
    active_session: ActiveSession
    archived_session: ArchivedSession


class StatusResponse(BaseModel):
    connected: bool
    preview: bool
    ws_clients: int
    stats_api_found: bool
    stats_api_enabled: bool


class HealthResponse(BaseModel):
    server_up: Literal[True] = True
    rl_connected: bool
    stats_api_found: bool
    stats_api_enabled: bool
    ws_clients: int


class EventEnvelope(BaseModel):
    event: str
    data: dict[str, Any]
