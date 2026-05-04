import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse

from .. import storage
from ..config import config
from ..deps import SettingsDep
from ..schemas import SettingsModel

router = APIRouter()


@router.get("/")
async def root() -> RedirectResponse:
    return RedirectResponse(url="/panel")


@router.get("/panel")
async def panel() -> FileResponse:
    return FileResponse(str(config.panel_dir / "index.html"))


@router.get("/panel/{filename}")
async def panel_file(filename: str) -> FileResponse:
    path = config.panel_dir / filename
    if path.exists() and path.is_file():
        return FileResponse(str(path))
    raise HTTPException(status_code=404)


@router.get("/overlay-api.js")
async def overlay_api_js() -> FileResponse:
    return FileResponse(
        str(config.public_dir / "overlay-api.js"), media_type="application/javascript"
    )


@router.get("/api/logs")
async def api_logs(lines: int = 150) -> JSONResponse:
    try:
        path = config.log_path
        if not path.exists():
            return JSONResponse([])
        text = path.read_text(encoding="utf-8", errors="replace")
        return JSONResponse(text.splitlines()[-lines:])
    except Exception:
        return JSONResponse([])


@router.get("/api/settings")
async def api_get_settings(settings: SettingsDep) -> JSONResponse:
    return JSONResponse(settings.model_dump())


@router.post("/api/settings")
async def api_save_settings(body: SettingsModel, settings: SettingsDep) -> dict:
    updated = settings.model_copy(update=body.model_dump())
    storage.save(updated.model_dump())
    settings.port = updated.port
    settings.preview_mode = updated.preview_mode
    settings.verbose = updated.verbose
    settings.installed_overlays = updated.installed_overlays
    settings.disabled_overlays = updated.disabled_overlays
    settings.community_installed = updated.community_installed
    level = logging.DEBUG if updated.verbose else logging.INFO
    logging.getLogger().setLevel(level)
    return {"ok": True}
