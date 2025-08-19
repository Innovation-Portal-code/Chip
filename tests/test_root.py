from fastapi.testclient import TestClient


def test_root(client: TestClient) -> None:
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data.get("greeting") == "Hello, World!"
    assert "Welcome to FastAPI" in data.get("message", "")
