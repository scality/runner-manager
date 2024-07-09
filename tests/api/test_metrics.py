from fastapi.testclient import TestClient

from runner_manager import RunnerGroup
from runner_manager.clients.github import GitHub


def test_metrics_endpoint(client: TestClient, runner_group: RunnerGroup):
    runner_group.save()
    response = client.get("/metrics")
    assert response.status_code == 200
    runner_lines = [
        line for line in response.text.splitlines() if line.startswith("runners_")
    ]
    assert f'runners_count{{runner_group="{runner_group.name}"}} 0.0' in runner_lines


def test_runner_count(client: TestClient, runner_group: RunnerGroup, github: GitHub):
    runner_group.save()
    want = len(runner_group.get_runners())

    response = client.get("/metrics")
    assert response.status_code == 200
    got = [line for line in response.text.splitlines() if line.startswith("runners_")]
    print(want)
    assert f'runners_count{{runner_group="{runner_group.name}"}} {want:.1f}' in got

    runner_group.max = 2
    runner_group.min = 1
    runner_group.save()

    want = 0.0
    response = client.get("/metrics")
    assert response.status_code == 200
    before = [
        line for line in response.text.splitlines() if line.startswith("runners_")
    ]
    assert f'runners_count{{runner_group="{runner_group.name}"}} {want:.1f}' in before

    runner = runner_group.create_runner(github)
    assert runner is not None

    want = 1.0
    response = client.get("/metrics")
    assert response.status_code == 200
    after_create = [
        line for line in response.text.splitlines() if line.startswith("runners_")
    ]
    assert (
        f'runners_count{{runner_group="{runner_group.name}"}} {want:.1f}'
        in after_create
    )

    runner = runner_group.delete_runner(runner, github)
    assert runner is not None

    want = 0.0
    response = client.get("/metrics")
    assert response.status_code == 200
    after_delete = [
        line for line in response.text.splitlines() if line.startswith("runners_")
    ]
    assert (
        f'runners_count{{runner_group="{runner_group.name}"}} {want:.1f}'
        in after_delete
    )
