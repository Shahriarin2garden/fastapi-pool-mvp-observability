from uuid import uuid4


def test_list_users(client):
    response = client.get("/users/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_user(client):
    email = f"pytest-{uuid4().hex[:8]}@example.com"
    response = client.post("/users/", json={"name": "Test User", "email": email})
    assert response.status_code == 201
    assert response.json()["email"] == email


def test_get_missing_user(client):
    response = client.get("/users/999")
    assert response.status_code == 404
