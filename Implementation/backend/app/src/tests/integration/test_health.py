def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert "env" in data


def test_db_health(client):
    r = client.get("/api/db-health")
    assert r.status_code == 200
    data = r.json()
    assert data["db_ok"] is True
