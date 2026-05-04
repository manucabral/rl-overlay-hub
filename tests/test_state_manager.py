from app.schemas import SessionStore
from app.state_manager import StateManager


def test_match_and_session_flow():
    state = StateManager()
    state.update_from_event("match:started", {})
    state.update_from_event(
        "player:updated",
        {"name": "Player", "goals": 1, "assists": 1, "saves": 2, "shots": 3, "score": 500},
    )
    state.update_from_event("overtime:started", {})
    state.update_from_event("match:ended", {"won": True})

    full = state.get_full_state()
    assert full["match"]["is_active"] is False
    assert full["match"]["overtime"] is True
    assert full["player"]["name"] == "Player"
    assert full["session"]["matches"] == 1
    assert full["session"]["wins"] == 1
    assert full["session"]["goals"] == 1
    assert full["session"]["assists"] == 1
    assert full["session"]["saves"] == 2


def test_preview_mode_updates_preview_state_only():
    state = StateManager(preview=True)
    before = state.get_full_state()
    payload = state.apply_preview_event("goal:scored")
    after = state.get_full_state()

    assert payload == {"player_name": "DemoPlayer", "team": "blue"}
    assert after["match"]["blue_score"] == before["match"]["blue_score"] + 1
    assert after["session"]["goals"] == before["session"]["goals"] + 1


def test_reset_session():
    state = StateManager()
    state.update_from_event("player:updated", {"goals": 2, "assists": 1, "saves": 1})
    state.reset_session()
    assert state.get_full_state()["session"] == {
        "matches": 0,
        "wins": 0,
        "losses": 0,
        "goals": 0,
        "assists": 0,
        "saves": 0,
    }


def test_restore_session_from_store():
    store = SessionStore()
    store.active_session.stats.wins = 4
    store.active_session.stats.matches = 7
    state = StateManager(session_store=store)
    full = state.get_full_state()
    assert full["session"]["wins"] == 4
    assert full["session"]["matches"] == 7


def test_archive_current_and_start_new_session():
    state = StateManager()
    state.update_from_event("player:updated", {"goals": 2, "assists": 1, "saves": 3})
    archived = state.archive_current_and_start_new()
    summary = state.get_session_summary()
    assert archived.stats.goals == 2
    assert summary.active_session.stats.matches == 0
    assert len(summary.archived_sessions) == 1


def test_preview_does_not_change_persisted_session():
    state = StateManager(preview=True)
    before = state.get_session_summary().active_session.stats.model_dump()
    state.apply_preview_event("goal:scored")
    after = state.get_session_summary().active_session.stats.model_dump()
    assert after == before
