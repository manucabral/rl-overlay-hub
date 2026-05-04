from typing import Annotated

from fastapi import Depends, HTTPException, Request

from .rlstats_client import RLStatsClient
from .schemas import SettingsModel
from .state_manager import StateManager
from .websocket_events import ConnectionManager


def _get_state_manager(request: Request) -> StateManager:
    return request.app.state.state_manager


def _get_connection_manager(request: Request) -> ConnectionManager:
    return request.app.state.connection_manager


def _get_settings(request: Request) -> SettingsModel:
    return request.app.state.settings


def _get_rl_client(request: Request) -> RLStatsClient:
    client = request.app.state.rl_client
    if client is None:
        raise HTTPException(status_code=503, detail="RL client unavailable")
    return client


# pylint: disable=invalid-name
StateManagerDep = Annotated[StateManager, Depends(_get_state_manager)]
ConnectionManagerDep = Annotated[ConnectionManager, Depends(_get_connection_manager)]
SettingsDep = Annotated[SettingsModel, Depends(_get_settings)]
RLClientDep = Annotated[RLStatsClient, Depends(_get_rl_client)]
