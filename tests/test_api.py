from fastapi.testclient import TestClient


def test_health_reports_version(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_create_and_list(client: TestClient) -> None:
    created = client.post("/api/todos", json={"title": "Write tests"})
    assert created.status_code == 201
    assert created.json() == {"id": 1, "title": "Write tests", "done": False}
    assert client.get("/api/todos").json() == [created.json()]


def test_title_is_trimmed(client: TestClient) -> None:
    created = client.post("/api/todos", json={"title": "  Ship it  "})
    assert created.json()["title"] == "Ship it"


def test_empty_title_rejected(client: TestClient) -> None:
    assert client.post("/api/todos", json={"title": ""}).status_code == 422


def test_mark_done(client: TestClient) -> None:
    todo_id = client.post("/api/todos", json={"title": "Review PR"}).json()["id"]
    updated = client.patch(f"/api/todos/{todo_id}", json={"done": True})
    assert updated.status_code == 200
    assert updated.json()["done"] is True


def test_delete(client: TestClient) -> None:
    todo_id = client.post("/api/todos", json={"title": "Temp"}).json()["id"]
    assert client.delete(f"/api/todos/{todo_id}").status_code == 204
    assert client.get(f"/api/todos/{todo_id}").status_code == 404


def test_missing_todo_returns_404(client: TestClient) -> None:
    assert client.get("/api/todos/999").status_code == 404
    assert client.patch("/api/todos/999", json={"done": True}).status_code == 404
    assert client.delete("/api/todos/999").status_code == 404


def test_index_serves_html(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Taskflow" in response.text
