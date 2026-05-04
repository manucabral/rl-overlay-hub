from fastapi import APIRouter

from .. import session_storage
from ..deps import ConnectionManagerDep, StateManagerDep
from ..schemas import NewSessionResponse, SessionSummaryResponse

router = APIRouter(prefix="/api/session")


@router.get("")
async def get_session_summary(state_manager: StateManagerDep) -> SessionSummaryResponse:
    summary = state_manager.get_session_summary()
    return SessionSummaryResponse(
        active_session=summary.active_session,
        archived_sessions=summary.archived_sessions,
    )


@router.post("/new")
async def start_new_session(
    state_manager: StateManagerDep,
    connection_manager: ConnectionManagerDep,
) -> NewSessionResponse:
    archived = state_manager.archive_current_and_start_new()
    session_storage.save(state_manager.get_session_summary())
    full_state = state_manager.get_full_state()
    await connection_manager.broadcast("match:update", full_state["match"])
    await connection_manager.broadcast("player:updated", full_state["player"])
    await connection_manager.broadcast("session:updated", full_state["session"])
    summary = state_manager.get_session_summary()
    return NewSessionResponse(
        active_session=summary.active_session,
        archived_session=archived,
    )
