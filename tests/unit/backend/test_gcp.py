import os
from typing import List

from google.api_core.exceptions import NotFound
from pytest import fixture, mark, raises
from redis_om import NotFoundError

from runner_manager.backend.gcloud import GCPBackend
from runner_manager.models.backend import Backends, GCPConfig, GCPInstanceConfig
from runner_manager.models.runner import Runner
from runner_manager.models.runner_group import RunnerGroup


@fixture()
def gcp_group() -> RunnerGroup:
    config = GCPConfig(
        project_id=os.environ.get("CLOUDSDK_CORE_PROJECT", ""),
        zone=os.environ.get("CLOUDSDK_COMPUTE_ZONE", ""),
        service_account_email="default",
    )
    runner_group: RunnerGroup = RunnerGroup(
        id=2,
        name="test",
        organization="test",
        backend=GCPBackend(
            name=Backends.gcloud,
            config=config,
            instance_config=GCPInstanceConfig(
                image_family="ubuntu-2004-lts",
                image_project="ubuntu-os-cloud",
                machine_type="e2-small",
                labels={"test": "test"},
            ),
        ),
        labels=[
            "label",
        ],
    )
    return runner_group


@fixture()
def gcp_runner(runner: Runner, gcp_group: RunnerGroup) -> Runner:
    # Cleanup and return a runner for testing
    gcp_group.backend.delete(runner)
    return runner


@mark.skipif(
    not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"), reason="GCP credentials not found"
)
def test_create_delete(gcp_runner, gcp_group):
    runner = gcp_group.backend.create(gcp_runner)
    assert runner.instance_id is not None
    assert runner.backend == "gcloud"
    assert Runner.find(Runner.instance_id == runner.instance_id).first() == runner
    gcp_group.backend.delete(runner)
    with raises(NotFoundError):
        Runner.find(Runner.instance_id == runner.instance_id).first()


def test_update(gcp_runner, gcp_group):
    runner = gcp_group.backend.create(gcp_runner)
    gcp_group.backend.update(runner)
    runner = Runner.find(Runner.labels == runner.labels).first()
    gcp_group.backend.delete(runner)
    with raises(NotFound):
        gcp_group.backend.get(runner.instance_id)


def test_get(gcp_runner, gcp_group):
    runner = gcp_group.backend.create(gcp_runner)
    assert runner == gcp_group.backend.get(runner.instance_id)
    gcp_group.backend.delete(runner)
    with raises(NotFound):
        gcp_group.backend.get(runner.instance_id)


def test_list(gcp_runner, gcp_group):
    runner = gcp_group.backend.create(gcp_runner)
    runners: List[Runner] = gcp_group.backend.list()
    assert runner in runners
    gcp_group.backend.delete(runner)
    with raises(NotFound):
        gcp_group.backend.get(runner.instance_id)
