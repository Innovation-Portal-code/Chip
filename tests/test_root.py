from fastapi.testclient import TestClient


def test_root_no_supabase(client: TestClient) -> None:
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data["greeting"] == "Hello, World!"
    assert data["message"] == "Welcome to FastAPI!"
    # In tests we don't connect to Supabase, so data is None
    assert data["data"] is None

