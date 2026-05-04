from __future__ import annotations

import json
import os
from pathlib import Path

from .config import config
from .logger import get_logger
from .schemas import SessionStore

log = get_logger(__name__)


def _store_file() -> Path:
    return config.session_store_file


def load() -> SessionStore:
    config.data_dir.mkdir(parents=True, exist_ok=True)
    store_file = _store_file()
    if not store_file.exists():
        return SessionStore()
    try:
        with open(store_file, encoding="utf-8") as handle:
            data = json.load(handle)
        return SessionStore.model_validate(data)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        log.warning("Failed to load session store from %s: %s", store_file, exc)
        return SessionStore()


def save(store: SessionStore) -> None:
    config.data_dir.mkdir(parents=True, exist_ok=True)
    store_file = _store_file()
    temp_file = store_file.with_suffix(".tmp")
    with open(temp_file, "w", encoding="utf-8") as handle:
        json.dump(store.model_dump(mode="json"), handle, indent=2)
    os.replace(temp_file, store_file)
