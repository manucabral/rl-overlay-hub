import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

from .constants import APP_NAME, APP_VERSION, DEFAULT_PORT


def _resolve_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class Config:
    app_name: str = APP_NAME
    app_version: str = APP_VERSION
    port: int = int(os.getenv("PORT", str(DEFAULT_PORT)))
    window_width: int = int(os.getenv("WINDOW_WIDTH", "980"))
    window_height: int = int(os.getenv("WINDOW_HEIGHT", "680"))
    window_min_width: int = 800
    window_min_height: int = 560
    window_bg_color: str = "#0f0f13"
    development_mode: bool = _env_bool("DEVELOPMENT_MODE", False)

    project_root: Path = field(default_factory=_resolve_root)

    @property
    def overlays_dir(self) -> Path:
        return self.data_dir / "overlays"

    @property
    def public_dir(self) -> Path:
        return self.project_root / "public"

    @property
    def panel_dir(self) -> Path:
        return self.project_root / "ui" / "panel"

    @property
    def data_dir(self) -> Path:
        return Path.home() / ".rl-overlay-hub"

    @property
    def log_path(self) -> Path:
        log_dir = self.project_root / "logs" if self.development_mode else self.data_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir / "app.log"

    @property
    def settings_file(self) -> Path:
        return self.data_dir / "settings.json"

    @property
    def session_store_file(self) -> Path:
        return self.data_dir / "session_store.json"


config = Config()
