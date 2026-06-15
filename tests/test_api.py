import json

def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "status" in data

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"

def test_events(client):
    response = client.get("/events")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        first = data[0]
        assert "id" in first
        assert "name" in first
        assert "category" in first

def test_event_nonexistent(client):
    response = client.get("/events/nonexistent-id")
    assert response.status_code == 404

def test_narratives(client):
    response = client.get("/narratives")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        first = data[0]
        assert "id" in first
        assert "topic" in first
        assert "eventName" in first

def test_narratives_trending(client):
    response = client.get("/narratives/trending")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_entities(client):
    response = client.get("/entities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        first = data[0]
        assert "name" in first
        assert "type" in first

def test_entities_top(client):
    response = client.get("/entities/top")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_sentiment(client):
    response = client.get("/sentiment")
    assert response.status_code == 200
    data = response.json()
    assert "distribution" in data
    assert "timeline" in data

def test_predictions(client):
    response = client.get("/predictions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_graph(client):
    response = client.get("/graph")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "links" in data

def test_etl_quality(client):
    response = client.get("/etl/quality")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        first = data[0]
        assert "dataset" in first
        assert "quality_score" in first

def test_admin_status(client):
    response = client.get("/admin/status")
    assert response.status_code == 200
    data = response.json()
    assert "records" in data
    assert "postgresConfigured" in data

def test_admin_audit_log(client):
    response = client.get("/admin/audit-log")
    assert response.status_code == 200
    data = response.json()
    assert "entries" in data

def test_import_source_pack_invalid(client):
    # Empty payload — send admin key so auth passes and validation is exercised
    # If no key is set in env, auth is bypassed; if key is set, we pass it.
    import os
    admin_key = os.getenv("NARRATIVEIQ_ADMIN_KEY", "")
    headers = {"X-Admin-Key": admin_key} if admin_key else {}
    response = client.post("/admin/import/source-pack", json={}, headers=headers)
    assert response.status_code == 400

def test_import_source_pack_valid(client):
    import os
    admin_key = os.getenv("NARRATIVEIQ_ADMIN_KEY", "")
    headers = {"X-Admin-Key": admin_key} if admin_key else {}
    payload = {
        "name": "Test Pack",
        "sourceType": "news",
        "notes": "automated test",
        "content": json.dumps([{"title": "Test article", "source": "test", "url": "https://example.com"}])
    }
    response = client.post("/admin/import/source-pack", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "importId" in data
    assert "rowCount" in data

def test_topic_intelligence(client):
    response = client.get("/topic-intelligence?q=Artificial+Intelligence&live=false")
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "mode" in data

def test_reports_summary(client):
    response = client.get("/reports/summary")
    assert response.status_code == 200
    data = response.json()
    assert "title" in data
