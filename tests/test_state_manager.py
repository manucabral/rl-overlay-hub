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
    assert full["session"]["demolitions"] == 0
    assert full["session"]["demolitions_taken"] == 0


def test_preview_mode_updates_preview_state_only():
    state = StateManager(preview=True)
    before = state.get_full_state()
    event_name, payload, mutates_state = state.apply_preview_event("goal:scored")
    after = state.get_full_state()

    assert event_name == "goal:scored"
    assert mutates_state is True
    assert payload == {
        "player_name": "DemoPlayer",
        "team": "blue",
        "assister_name": "Teammate",
        "goal_speed": 143.0,
    }
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
        "demolitions": 0,
        "demolitions_taken": 0,
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


def test_preview_alias_resolves_to_public_event():
    state = StateManager(preview=True)
    event_name, payload, mutates_state = state.apply_preview_event("goal-replay-will-end")

    assert event_name == "goal:replay:will-end"
    assert mutates_state is False
    assert payload == {"match_guid": "preview-match-001"}


def test_preview_animation_events_do_not_change_state():
    state = StateManager(preview=True)
    before = state.get_full_state()

    event_name, payload, mutates_state = state.apply_preview_event("ball-hit")
    after = state.get_full_state()

    assert event_name == "ball:hit"
    assert mutates_state is False
    assert payload["player_name"] == "DemoPlayer"
    assert after == before


def test_preview_match_destroyed_resets_match_view_without_touching_session_totals():
    state = StateManager(preview=True)
    before_session = state.get_full_state()["session"]

    event_name, payload, mutates_state = state.apply_preview_event("match:destroyed")
    after = state.get_full_state()

    assert event_name == "match:destroyed"
    assert payload == {}
    assert mutates_state is True
    assert after["match"]["is_active"] is False
    assert after["match"]["overtime"] is False
    assert after["match"]["clock"] == "5:00"
    assert after["session"] == before_session


def test_player_demolished_updates_session_totals_for_attacker_and_victim():
    state = StateManager()
    state.update_from_event("player:updated", {"name": "Player"})

    state.update_from_event("player:demolished", {"attacker": "Player", "victim": "Rival"})
    state.update_from_event("player:demolished", {"attacker": "Opponent", "victim": "Player"})

    full = state.get_full_state()
    assert full["session"]["demolitions"] == 1
    assert full["session"]["demolitions_taken"] == 1
