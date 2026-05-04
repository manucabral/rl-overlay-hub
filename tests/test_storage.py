import json

from app import storage
from app.config import config


def test_load_creates_defaults():
    data = storage.load()
    assert data["port"] > 0
    assert config.settings_file.exists()


def test_load_recovers_from_invalid_json():
    config.data_dir.mkdir(parents=True, exist_ok=True)
    config.settings_file.write_text("{invalid", encoding="utf-8")
    data = storage.load()
    assert data["preview_mode"] is False


def test_save_is_atomic_and_normalizes():
    storage.save({"port": 49101, "community_installed": [" one ", "", "two"]})
    data = json.loads(config.settings_file.read_text(encoding="utf-8"))
    assert data["port"] == 49101
    assert data["community_installed"] == ["one", "two"]
