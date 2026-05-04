from app import session_storage
from app.config import config
from app.schemas import SessionStore


def test_session_store_defaults_when_missing():
    store = session_storage.load()
    assert store.active_session.stats.matches == 0
    assert store.archived_sessions == []


def test_session_store_roundtrip():
    store = SessionStore()
    store.active_session.stats.wins = 3
    session_storage.save(store)
    loaded = session_storage.load()
    assert loaded.active_session.stats.wins == 3


def test_session_store_recovers_from_invalid_json():
    config.data_dir.mkdir(parents=True, exist_ok=True)
    config.session_store_file.write_text("{invalid", encoding="utf-8")
    loaded = session_storage.load()
    assert loaded.active_session.stats.matches == 0
