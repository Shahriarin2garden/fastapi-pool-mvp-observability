import pytest
import requests
import uuid

# Test against the running application (internal Docker network)
BASE_URL = "http://app:8000"


def test_health_check():
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_users():
    response = requests.get(f"{BASE_URL}/users/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_user():
    unique_id = str(uuid.uuid4())[:8]
    user_data = {"name": "Test User", "email": f"pytest-{unique_id}@example.com"}
    response = requests.post(f"{BASE_URL}/users/", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test User"
    assert data["email"] == f"pytest-{unique_id}@example.com"
    assert "id" in data