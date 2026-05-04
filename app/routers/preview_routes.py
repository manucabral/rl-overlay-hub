from fastapi import APIRouter, HTTPException

from ..deps import ConnectionManagerDep, StateManagerDep
from ..schemas import PreviewToggleRequest, PreviewToggleResponse
from ..state_manager import StateManager
from ..websocket_events import ConnectionManager

router = APIRouter(prefix="/api/preview")


async def _broadcast_state(
    state_manager: StateManager, connection_manager: ConnectionManager
) -> None:
    full = state_manager.get_full_state()
    await connection_manager.broadcast("match:update", full["match"])
    await connection_manager.broadcast("player:updated", full["player"])
    await connection_manager.broadcast("session:updated", full["session"])


@router.post("/toggle")
async def toggle(
    body: PreviewToggleRequest,
    state_manager: StateManagerDep,
    connection_manager: ConnectionManagerDep,
) -> PreviewToggleResponse:
    state_manager.set_preview(body.enabled)
    await _broadcast_state(state_manager, connection_manager)
    return PreviewToggleResponse(preview=state_manager.preview)


@router.post("/simulate/{event_name}")
async def simulate(
    event_name: str,
    state_manager: StateManagerDep,
    connection_manager: ConnectionManagerDep,
) -> dict:
    if not state_manager.preview:
        raise HTTPException(status_code=400, detail="Not in preview mode")
    event_data = state_manager.apply_preview_event(event_name)
    if event_data is None:
        raise HTTPException(status_code=400, detail=f"Unknown event: {event_name}")
    await connection_manager.broadcast(event_name, event_data)
    await _broadcast_state(state_manager, connection_manager)
    return {"ok": True, "event": event_name}
