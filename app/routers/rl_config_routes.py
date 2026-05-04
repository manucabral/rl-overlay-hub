from fastapi import APIRouter, HTTPException

from ..deps import RLClientDep

router = APIRouter(prefix="/api/rl-config")


@router.get("")
async def get_config(rl_client: RLClientDep) -> dict:
    s = rl_client.get_config_status()
    return {
        "found": s.found,
        "enabled": s.enabled,
        "path": s.path,
        "packet_send_rate": s.packet_send_rate,
        "port": s.port,
        "warning": s.warning,
    }


@router.post("/enable")
async def enable_config(rl_client: RLClientDep) -> dict:
    try:
        s = rl_client.enable_stats_api()
        return {"ok": True, "enabled": s.enabled, "path": s.path}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/disable")
async def disable_config(rl_client: RLClientDep) -> dict:
    try:
        s = rl_client.disable_stats_api()
        return {"ok": True, "enabled": s.enabled}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
