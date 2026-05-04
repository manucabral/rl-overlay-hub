from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse

from .. import storage
from ..config import config
from ..constants import DEFAULT_REGISTRY_URL
from ..deps import SettingsDep
from ..logger import get_logger
from ..overlay_registry import (
    fetch_community_registry,
    install_overlay,
    install_overlay_from_local,
    scan_local_overlays,
    uninstall_overlay,
)
from ..schemas import LocalOverlayInstallRequest, OverlayInstallRequest, ToggleResponse

log = get_logger(__name__)

router = APIRouter()

_INSTALL_DIR = config.overlays_dir / "installed"


def _find_overlay_file(overlay_id: str, filename: str) -> Path | None:
    path = _INSTALL_DIR / overlay_id / filename
    return path if path.exists() and path.is_file() else None


@router.get("/api/overlays")
async def api_overlays(settings: SettingsDep) -> JSONResponse:
    overlays = scan_local_overlays(config.overlays_dir)
    disabled = set(settings.disabled_overlays)
    community = set(settings.community_installed)
    for ov in overlays:
        ov_id = ov.get("id", "")
        ov["url"] = f"http://127.0.0.1:{settings.port or config.port}/overlay/{ov_id}/"
        has_preview = _find_overlay_file(ov_id, ov.get("preview", "preview.png")) is not None
        ov["preview_url"] = f"/overlay/{ov_id}/preview.png" if has_preview else None
        ov["enabled"] = ov_id not in disabled
        ov["official"] = ov_id in community
    return JSONResponse(overlays)


@router.post("/api/overlays/{overlay_id}/toggle")
async def api_toggle(overlay_id: str, settings: SettingsDep) -> ToggleResponse:
    disabled = list(settings.disabled_overlays)
    if overlay_id in disabled:
        disabled.remove(overlay_id)
        log.info("Overlay enabled: %s", overlay_id)
    else:
        disabled.append(overlay_id)
        log.info("Overlay disabled: %s", overlay_id)
    settings.disabled_overlays = disabled
    storage.save(settings.model_dump())
    return ToggleResponse(enabled=overlay_id not in disabled)


@router.get("/api/community")
async def api_community() -> JSONResponse:
    registry = await fetch_community_registry(DEFAULT_REGISTRY_URL)
    local = scan_local_overlays(config.overlays_dir)
    installed_ids = {ov.get("id") for ov in local if ov.get("_source") == "installed"}
    for entry in registry:
        entry["installed"] = entry.get("id") in installed_ids
    return JSONResponse(registry)


@router.post("/api/overlays/install")
async def api_install(req: OverlayInstallRequest, settings: SettingsDep) -> dict:
    raw_base = DEFAULT_REGISTRY_URL.rsplit("/", 2)[0]
    if "raw.githubusercontent.com" not in raw_base:
        raw_base = raw_base.replace("github.com", "raw.githubusercontent.com")
    error = await install_overlay(req.overlay_id, req.registry_entry, raw_base, _INSTALL_DIR)
    if error is not None:
        log.error("Overlay install failed [%s]: %s", req.overlay_id, error)
        raise HTTPException(status_code=500, detail=error)
    log.info("Overlay installed: %s", req.overlay_id)
    community = list(settings.community_installed)
    if req.overlay_id not in community:
        community.append(req.overlay_id)
    settings.community_installed = community
    storage.save(settings.model_dump())
    return {"ok": True}


@router.post("/api/overlays/install-local")
async def api_install_local(req: LocalOverlayInstallRequest) -> dict:
    overlay_id, error = install_overlay_from_local(req.path, _INSTALL_DIR)
    if error:
        log.error("Local overlay install failed: %s", error)
        raise HTTPException(status_code=400, detail=error)
    log.info("Custom overlay installed from local path: %s", overlay_id)
    return {"ok": True, "overlay_id": overlay_id}


@router.delete("/api/overlays/{overlay_id}")
async def api_uninstall(overlay_id: str, settings: SettingsDep) -> dict:
    ok = uninstall_overlay(overlay_id, _INSTALL_DIR)
    if ok:
        log.info("Overlay uninstalled: %s", overlay_id)
    community = list(settings.community_installed)
    if overlay_id in community:
        community.remove(overlay_id)
        settings.community_installed = community
        storage.save(settings.model_dump())
    return {"ok": ok}


@router.get("/overlay/{overlay_id}")
async def overlay_index_redirect(overlay_id: str) -> RedirectResponse:
    # Trailing slash required so that relative asset paths in the overlay HTML resolve correctly.
    return RedirectResponse(url=f"/overlay/{overlay_id}/", status_code=301)


@router.get("/overlay/{overlay_id}/")
async def overlay_index(overlay_id: str) -> FileResponse:
    path = _find_overlay_file(overlay_id, "index.html")
    if path:
        return FileResponse(str(path))
    raise HTTPException(status_code=404, detail=f"Overlay '{overlay_id}' not found")


@router.get("/overlay/{overlay_id}/{file_path:path}")
async def overlay_file(overlay_id: str, file_path: str) -> FileResponse:
    candidate = (_INSTALL_DIR / overlay_id / file_path).resolve()
    allowed = (_INSTALL_DIR / overlay_id).resolve()
    try:
        candidate.relative_to(allowed)
    except ValueError as exc:
        raise HTTPException(status_code=400) from exc
    path = _find_overlay_file(overlay_id, file_path)
    if path:
        return FileResponse(str(path))
    raise HTTPException(status_code=404)
