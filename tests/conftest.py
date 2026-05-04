from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import storage
from app.config import config
from app.overlay_server import create_app
from app.schemas import SettingsModel
from app.state_manager import StateManager
from app.websocket_events import ConnectionManager


class DummyRLClient:
    def __init__(self) -> None:
        self.connected = False

    @staticmethod
    def get_config_status():
        class Status:
            found = True
            enabled = False
            path = "C:/Dummy/TAStatsAPI.ini"
            warning = ""
            packet_send_rate = 60
            port = 49123

        return Status()


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    yield tmp_path / ".rl-overlay-hub"


@pytest.fixture
def app_client() -> TestClient:
    overlays_dir = config.overlays_dir / "installed" / "sample"
    overlays_dir.mkdir(parents=True, exist_ok=True)
    (overlays_dir / "manifest.json").write_text(
        '{"id":"sample","name":"Sample","author":"Tester"}', encoding="utf-8"
    )
    (overlays_dir / "index.html").write_text("<html></html>", encoding="utf-8")
    settings = SettingsModel.model_validate(storage.load())
    app = create_app(StateManager(), ConnectionManager(), settings, DummyRLClient())
    return TestClient(app)
