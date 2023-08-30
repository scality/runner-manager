from fastapi.testclient import TestClient

from runner_manager import RunnerGroup
from runner_manager.models.api import JobResponse


def test_list_groups(client: TestClient, runner_group: RunnerGroup):
    runner_group.save()
    response = client.get("/groups")
    assert response.status_code == 200
    assert response.json() == [runner_group]


def test_get_group(client: TestClient, runner_group: RunnerGroup):
    response = client.get(f"/groups/{runner_group.name}")
    assert response.status_code == 404
    runner_group.save()
    response = client.get(f"/groups/{runner_group.name}")
    assert response.status_code == 200
    assert response.json() == runner_group
    runner_group.save()


def test_delete_group(client: TestClient, runner_group: RunnerGroup):
    response = client.delete(f"/groups/{runner_group.name}")
    assert response.status_code == 404
    runner_group.save()
    response = client.delete(f"/groups/{runner_group.name}")
    assert response.status_code == 200
    assert RunnerGroup.find().count() == 0


def test_healthcheck(client: TestClient, runner_group: RunnerGroup):
    response = client.post(f"/groups/{runner_group.name}/healthcheck")
    assert response.status_code == 404
    runner_group.save()
    response = client.post(f"/groups/{runner_group.name}/healthcheck")
    assert response.status_code == 200
    job: JobResponse = JobResponse.parse_obj(response.json())
    assert job.status == "finished"
    runner_group.save()


def test_reset(client: TestClient, runner_group: RunnerGroup):
    response = client.post(f"/groups/{runner_group.name}/reset")
    assert response.status_code == 404
    runner_group.save()
    response = client.post(f"/groups/{runner_group.name}/reset")
    assert response.status_code == 200
    job: JobResponse = JobResponse.parse_obj(response.json())
    assert job.status == "finished"
    runner_group.save()
