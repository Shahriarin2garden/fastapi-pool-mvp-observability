def test_telemetry_accepts_allowlisted_events(client):
    response = client.post(
        "/api/telemetry",
        json={
            "session": "test-session",
            "route": "console",
            "events": [
                {"type": "event", "name": "order_submit"},
                {"type": "api", "endpoint": "orders", "status": 201, "duration": 0.05},
            ],
        },
    )
    assert response.status_code == 204


def test_telemetry_rejects_unknown_labels(client):
    response = client.post(
        "/api/telemetry",
        json={
            "session": "test-session",
            "route": "console",
            "events": [{"type": "event", "name": "not-allowed"}],
        },
    )
    assert response.status_code == 422


def test_traceparent_is_echoed(client):
    traceparent = "00-0123456789abcdef0123456789abcdef-0123456789abcdef-01"
    response = client.get("/health", headers={"traceparent": traceparent})
    assert response.headers["x-trace-id"] == "0123456789abcdef0123456789abcdef"
