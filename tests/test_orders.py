from app.config import Settings


def order_payload():
    return {
        "customer_email": "test@example.com",
        "item": "widget",
        "quantity": 2,
        "amount_cents": 1999,
    }


def test_order_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_create_order(client):
    response = client.post("/api/orders", json=order_payload())
    assert response.status_code == 201
    assert response.json()["status"] == "created"


def test_invalid_order(client):
    response = client.post("/api/orders", json={"item": "", "quantity": 0})
    assert response.status_code == 422


def test_simulated_failure(client):
    response = client.post("/api/orders?simulate_failure=true", json=order_payload())
    assert response.status_code == 500


def test_failure_rate_is_safe():
    assert Settings(FAILURE_RATE="abc").FAILURE_RATE == 0
    assert Settings(FAILURE_RATE="-1").FAILURE_RATE == 0
    assert Settings(FAILURE_RATE="2").FAILURE_RATE == 1


def test_metrics_include_orders_and_increment(client):
    client.post("/api/orders", json=order_payload())
    client.post("/api/orders?simulate_failure=true", json=order_payload())
    client.post("/api/orders", json={"item": ""})
    metrics = client.get("/metrics").text
    assert 'orders_created_total{status="success"}' in metrics
    assert 'orders_created_total{status="failed"}' in metrics
    assert 'order_requests_total{status_class="2xx"}' in metrics
    assert 'order_requests_total{status_class="4xx"}' in metrics
    assert 'order_requests_total{status_class="5xx"}' in metrics
    assert "order_request_duration_seconds_bucket" in metrics
