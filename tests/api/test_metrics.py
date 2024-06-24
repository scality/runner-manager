from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

from runner_manager import RunnerGroup

def test_metrics_endpoint(client: TestClient):
    response = client.get("/metrics")
    assert response.status_code == 200

def test_runner_metric(runner_group: RunnerGroup):
    want = len(runner_group.get_runners())
    got = REGISTRY.get_sample_value("runners", {"runner_group": runner_group.name})
    assert want == got
