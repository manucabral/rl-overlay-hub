import json
import os
from pathlib import Path

from .config import config
from .logger import get_logger
from .schemas import SettingsModel

log = get_logger(__name__)

_DEFAULTS = SettingsModel().model_dump()


def _settings_file() -> Path:
    return config.settings_file


def _normalize(data: dict) -> dict:
    return SettingsModel.model_validate({**_DEFAULTS, **data}).model_dump()


def load() -> dict:
    config.data_dir.mkdir(parents=True, exist_ok=True)
    settings_file = _settings_file()
    if not settings_file.exists():
        save(_DEFAULTS.copy())
        return _DEFAULTS.copy()
    try:
        with open(settings_file, encoding="utf-8") as f:
            data = json.load(f)
        return _normalize(data)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        log.warning("Failed to load settings from %s: %s", settings_file, exc)
        return _DEFAULTS.copy()


def save(settings: dict) -> None:
    config.data_dir.mkdir(parents=True, exist_ok=True)
    data = _normalize(settings)
    settings_file = _settings_file()
    temp_file = settings_file.with_suffix(".tmp")
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(temp_file, settings_file)


def get(key: str) -> object:
    return load().get(key, _DEFAULTS.get(key))


def set_value(key: str, value: object) -> None:
    settings = load()
    settings[key] = value
    save(settings)
