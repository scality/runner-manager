from fastapi.testclient import TestClient

from runner_manager import RunnerGroup


def test_list_groups(client: TestClient, runner_group: RunnerGroup):
    runner_group.save()
    response = client.get("/groups")
    assert response.status_code == 200
    assert response.json() == [runner_group.name]


def test_delete_group(client: TestClient, runner_group: RunnerGroup):
    runner_group.save()
    response = client.delete(f"/groups/{runner_group.name}")
    assert response.status_code == 200
    assert RunnerGroup.find().count() == 0
