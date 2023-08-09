import os

from pytest import fixture, mark, raises
from redis_om import NotFoundError

from runner_manager.backend.gcloud import GCPBackend
from runner_manager.models.backend import Backends, GCPConfig, GCPInstanceConfig
from runner_manager.models.runner import Runner
from runner_manager.models.runner_group import RunnerGroup


@fixture()
def gcp_group() -> RunnerGroup:
    runner_group: RunnerGroup = RunnerGroup(
        id=2,
        name="test",
        organization="test",
        backend=GCPBackend(
            name=Backends.gcloud,
            config=GCPConfig(
                project_id=os.getenv("GCP_PROJECT_ID"),
                zone=os.getenv("GCP_ZONE"),
                service_account_email="default",
            ),
            instance_config=GCPInstanceConfig(
                machine_type="e2-small",
                image={
                    "project": "ubuntu-os-cloud",
                    "family": "ubuntu-2004-lts",
                },
                network="default",
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
