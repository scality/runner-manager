from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

from runner_manager import RunnerGroup
from runner_manager.clients.github import GitHub


def test_metrics_endpoint(client: TestClient, runner_group: RunnerGroup):
    runner_group.save()
    response = client.get("/metrics")
    assert response.status_code == 200
    runner_lines = [
        line for line in response.text.splitlines() if line.startswith("runners_")
    ]
    assert 'runners_count{runner_group="test"} 0.0' in runner_lines
    assert 'runners_created_total{runner_group="test"} 0.0' in runner_lines
    assert 'runners_deleted_total{runner_group="test"} 0.0' in runner_lines


def test_runner_count(runner_group: RunnerGroup, github: GitHub):
    runner_group.save()
    want = len(runner_group.get_runners())
    got = REGISTRY.get_sample_value(
        "runners_count", {"runner_group": runner_group.name}
    )
    assert got is not None
    assert want == got

    runner_group.max = 2
    runner_group.min = 1
    runner_group.save()

    before = REGISTRY.get_sample_value(
        "runners_count", {"runner_group": runner_group.name}
    )
    assert before is not None
    assert before == 0

    runner = runner_group.create_runner(github)
    assert runner is not None

    after_create = REGISTRY.get_sample_value(
        "runners_count", {"runner_group": runner_group.name}
    )
    assert after_create is not None
    assert after_create == 1

    runner = runner_group.delete_runner(runner, github)
    assert runner is not None

    after_delete = REGISTRY.get_sample_value(
        "runners_count", {"runner_group": runner_group.name}
    )
    assert after_delete is not None
    assert after_delete == 0


def test_create_runner(runner_group: RunnerGroup, github: GitHub):
    runner_group.save()
    before = REGISTRY.get_sample_value(
        "runners_created_total", {"runner_group": runner_group.name}
    )
    assert before is not None

    runner_group.max = 2
    runner_group.min = 1
    runner_group.save()

    assert runner_group.need_new_runner is True
    runner = runner_group.create_runner(github)

    assert runner is not None
    after = REGISTRY.get_sample_value(
        "runners_created_total", {"runner_group": runner_group.name}
    )
    assert after is not None

    expected = before + 1
    assert after == expected


def test_delete_runner(runner_group: RunnerGroup, github: GitHub):
    runner_group.max = 2
    runner_group.min = 1
    runner_group.save()

    runner = runner_group.create_runner(github)
    assert runner is not None

    before = REGISTRY.get_sample_value(
        "runners_deleted_total", {"runner_group": runner_group.name}
    )
    assert before is not None

    runner = runner_group.delete_runner(runner, github)
    assert runner is not None

    after = REGISTRY.get_sample_value(
        "runners_deleted_total", {"runner_group": runner_group.name}
    )
    assert after is not None

    expected = before + 1
    assert after == expected
