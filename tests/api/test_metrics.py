from fastapi.testclient import TestClient

def test_metrics_endpoint(client: TestClient):
    response = client.get("/metrics")
    assert response.status_code == 200
