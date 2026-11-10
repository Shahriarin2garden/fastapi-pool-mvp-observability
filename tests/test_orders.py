import requests


BASE_URL = "http://app:8000"


def test_order_health():
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200


def test_create_order():
    response = requests.post(
        f"{BASE_URL}/api/orders",
        json={"customer_email": "test@example.com", "item": "widget", "quantity": 2, "amount_cents": 1999},
    )
    assert response.status_code == 201
    assert response.json()["status"] == "created"


def test_invalid_order():
    response = requests.post(f"{BASE_URL}/api/orders", json={"item": "", "quantity": 0})
    assert response.status_code == 422


def test_simulated_failure():
    response = requests.post(
        f"{BASE_URL}/api/orders?simulate_failure=true",
        json={"customer_email": "test@example.com", "item": "widget", "quantity": 1, "amount_cents": 1},
    )
    assert response.status_code == 500


def test_order_metrics():
    response = requests.get(f"{BASE_URL}/metrics")
    assert response.status_code == 200
    assert "orders_created_total" in response.text
    assert "order_request_duration_seconds_bucket" in response.text
