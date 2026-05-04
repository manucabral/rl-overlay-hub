def test_status_endpoint(app_client):
    response = app_client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["connected"] is False
    assert data["stats_api_found"] is True


def test_settings_roundtrip(app_client):
    response = app_client.post("/api/settings", json={"port": 49200, "verbose": True})
    assert response.status_code == 200
    response = app_client.get("/api/settings")
    data = response.json()
    assert data["port"] == 49200
    assert data["verbose"] is True


def test_preview_toggle_and_state(app_client):
    response = app_client.post("/api/preview/toggle", json={"enabled": True})
    assert response.status_code == 200
    assert response.json()["preview"] is True
    state_response = app_client.get("/api/state")
    assert state_response.status_code == 200
    assert state_response.json()["match"]["is_active"] is True


def test_overlay_listing(app_client):
    response = app_client.get("/api/overlays")
    assert response.status_code == 200
    data = response.json()
    assert data[0]["id"] == "sample"
    assert data[0]["enabled"] is True


def test_get_session_summary(app_client):
    response = app_client.get("/api/session")
    assert response.status_code == 200
    data = response.json()
    assert data["active_session"]["stats"]["matches"] == 0
    assert data["archived_sessions"] == []


def test_start_new_session_archives_previous(app_client):
    app_client.app.state.state_manager.update_from_event(
        "player:updated", {"goals": 1, "assists": 1}
    )
    response = app_client.post("/api/session/new")
    assert response.status_code == 200
    data = response.json()
    assert data["archived_session"]["stats"]["goals"] == 1
    assert data["active_session"]["stats"]["goals"] == 0
    summary = app_client.get("/api/session").json()
    assert len(summary["archived_sessions"]) == 1


def test_websocket_connected_event(app_client):
    with app_client.websocket_connect("/ws") as ws:
        message = ws.receive_json()
        assert message["event"] == "connected"
        assert "match" in message["data"]
