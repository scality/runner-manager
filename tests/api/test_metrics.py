from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

def test_metrics_endpoint(client: TestClient):
    response = client.get("/metrics")
    assert response.status_code == 200

def test_runner_metric():
    runners = REGISTRY.get_sample_value("runners")
    assert runners == 4
