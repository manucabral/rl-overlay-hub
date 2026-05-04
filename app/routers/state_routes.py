from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from ..deps import ConnectionManagerDep, StateManagerDep
from ..schemas import EventEnvelope, HealthResponse, StatusResponse

router = APIRouter()


@router.get("/api/state")
async def api_state(state_manager: StateManagerDep) -> JSONResponse:
    return JSONResponse(state_manager.get_full_state())


@router.get("/api/status")
async def api_status(
    request: Request,
    state_manager: StateManagerDep,
    connection_manager: ConnectionManagerDep,
) -> StatusResponse:
    rl_client = request.app.state.rl_client
    connected = rl_client.connected if rl_client else False
    config_status = rl_client.get_config_status() if rl_client else None
    return StatusResponse(
        connected=connected,
        preview=state_manager.preview,
        ws_clients=connection_manager.client_count,
        stats_api_found=bool(config_status and config_status.found),
        stats_api_enabled=bool(config_status and config_status.enabled),
    )


@router.get("/api/health")
async def api_health(request: Request, connection_manager: ConnectionManagerDep) -> HealthResponse:
    rl_client = request.app.state.rl_client
    config_status = rl_client.get_config_status() if rl_client else None
    return HealthResponse(
        rl_connected=rl_client.connected if rl_client else False,
        stats_api_found=bool(config_status and config_status.found),
        stats_api_enabled=bool(config_status and config_status.enabled),
        ws_clients=connection_manager.client_count,
    )


@router.websocket("/ws")
async def ws_endpoint(ws: WebSocket) -> None:
    state_manager = ws.app.state.state_manager
    connection_manager = ws.app.state.connection_manager
    await connection_manager.connect(ws)
    try:
        await ws.send_text(
            EventEnvelope(event="connected", data=state_manager.get_full_state()).model_dump_json()
        )
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        await connection_manager.disconnect(ws)
    except Exception:
        await connection_manager.disconnect(ws)
