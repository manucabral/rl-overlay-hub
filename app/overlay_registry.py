import asyncio
import shutil
import tempfile
import time
from pathlib import Path

import httpx

from .constants import APP_VERSION, OVERLAY_REQUIRED_FILES
from .logger import get_logger
from .schemas import OverlayManifest

log = get_logger(__name__)

_REGISTRY_TTL = 300  # seconds
_REGISTRY_CACHE: list[dict] = []
_REGISTRY_CACHE_SOURCE_URL: str = ""
_REGISTRY_CACHE_TIMESTAMP: float = 0.0

_HEADERS = {"User-Agent": f"rl-overlay-hub/{APP_VERSION}"}


def _parse_manifest(folder: Path) -> dict | None:
    mf = folder / "manifest.json"
    if not mf.exists():
        return None
    try:
        data = OverlayManifest.model_validate_json(mf.read_text(encoding="utf-8")).model_dump()
        data["_path"] = str(folder)
        data["_source"] = "installed"
        return data
    except Exception:
        return None


def scan_local_overlays(base_dir: Path) -> list[dict]:
    results: list[dict] = []
    install_dir = base_dir / "installed"
    if not install_dir.exists():
        return results
    for folder in sorted(install_dir.iterdir()):
        if not folder.is_dir():
            continue
        files = {f.name for f in folder.iterdir()}
        if not OVERLAY_REQUIRED_FILES.issubset(files):
            log.warning("Overlay %s missing required files, skipping", folder.name)
            continue
        manifest = _parse_manifest(folder)
        if manifest:
            results.append(manifest)
    return results


async def fetch_community_registry(url: str) -> list[dict]:
    global _REGISTRY_CACHE, _REGISTRY_CACHE_SOURCE_URL, _REGISTRY_CACHE_TIMESTAMP  # noqa: PLW0603  # pylint: disable=global-statement
    now = time.monotonic()
    if (
        _REGISTRY_CACHE
        and _REGISTRY_CACHE_SOURCE_URL == url
        and now - _REGISTRY_CACHE_TIMESTAMP < _REGISTRY_TTL
    ):
        return _REGISTRY_CACHE
    try:
        async with httpx.AsyncClient(timeout=10, headers=_HEADERS) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            _REGISTRY_CACHE = data.get("overlays", [])
            _REGISTRY_CACHE_SOURCE_URL = url
            _REGISTRY_CACHE_TIMESTAMP = now
            return _REGISTRY_CACHE
    except Exception as exc:
        log.warning("Failed to fetch community registry: %s", exc)
        return _REGISTRY_CACHE


async def _fetch_file(client: httpx.AsyncClient, url: str, dest: Path) -> None:
    try:
        resp = await client.get(url)
        if resp.status_code == 200:
            dest.write_bytes(resp.content)
        else:
            log.warning("Failed to download %s (HTTP %d)", url, resp.status_code)
    except Exception as exc:
        log.warning("Could not fetch %s: %s", url, exc)


async def install_overlay(
    overlay_id: str,
    registry_entry: dict,
    base_url: str,
    install_dir: Path,
) -> str | None:
    """Download overlay files from GitHub raw content and install locally.

    Returns None on success, or an error string on failure.
    """
    overlay_path = registry_entry.get("path", overlay_id)
    dest = install_dir / overlay_id
    install_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix=f"{overlay_id}-", dir=install_dir))

    files_to_fetch = ["manifest.json", "index.html", "style.css", "script.js", "preview.png"]
    try:
        async with httpx.AsyncClient(timeout=15, headers=_HEADERS) as client:
            log.info("Downloading overlay files: %s", overlay_id)
            await asyncio.gather(
                *[
                    _fetch_file(client, f"{base_url}/{overlay_path}/{fn}", temp_dir / fn)
                    for fn in files_to_fetch
                ]
            )

        installed_files = {f.name for f in temp_dir.iterdir()}
        if not OVERLAY_REQUIRED_FILES.issubset(installed_files):
            missing = OVERLAY_REQUIRED_FILES - installed_files
            error = f"Missing required files after download: {', '.join(sorted(missing))}"
            log.error("Overlay %s - %s", overlay_id, error)
            shutil.rmtree(temp_dir, ignore_errors=True)
            return error
        _parse_manifest(temp_dir)
        if dest.exists():
            shutil.rmtree(dest)
        temp_dir.replace(dest)

        return None
    except Exception as exc:
        error = str(exc)
        log.error("Failed to install overlay %s: %s", overlay_id, error)
        shutil.rmtree(temp_dir, ignore_errors=True)
        return error


def install_overlay_from_local(
    src_path: str | Path, install_dir: Path
) -> tuple[str | None, str | None]:
    """Copy a local folder as an installed overlay.

    Returns (overlay_id, None) on success or (None, error_message) on failure.
    """
    src = Path(src_path)
    if not src.exists() or not src.is_dir():
        return None, f"Folder not found: {src_path}"
    files = {f.name for f in src.iterdir() if f.is_file()}
    if not OVERLAY_REQUIRED_FILES.issubset(files):
        missing = OVERLAY_REQUIRED_FILES - files
        return None, f"Missing required files: {', '.join(sorted(missing))}"
    try:
        manifest = OverlayManifest.model_validate_json(
            (src / "manifest.json").read_text(encoding="utf-8")
        ).model_dump()
    except Exception:
        return None, "Could not parse manifest.json"
    overlay_id = manifest.get("id", "").strip()
    if not overlay_id:
        return None, "manifest.json missing the 'id' field"
    dest = install_dir / overlay_id
    if dest.exists():
        shutil.rmtree(dest)
    try:
        shutil.copytree(src, dest)
    except Exception as exc:
        return None, str(exc)
    return overlay_id, None


def uninstall_overlay(overlay_id: str, install_dir: Path) -> bool:
    dest = install_dir / overlay_id
    if dest.exists():
        shutil.rmtree(dest)
        return True
    return False
