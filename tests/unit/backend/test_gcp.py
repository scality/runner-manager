import os
from typing import List

from pytest import fixture, mark, raises
from redis_om import NotFoundError

from runner_manager.backend.gcloud import GCPBackend
from runner_manager.models.backend import Backends, GCPConfig, GCPInstanceConfig
from runner_manager.models.runner import Runner
from runner_manager.models.runner_group import RunnerGroup


@fixture()
def gcp_group(settings) -> RunnerGroup:
    config = GCPConfig(
        project_id=os.environ.get("CLOUDSDK_CORE_PROJECT", ""),
        zone=os.environ.get("CLOUDSDK_COMPUTE_ZONE", ""),
        google_application_credentials=os.environ.get(
            "GOOGLE_APPLICATION_CREDENTIALS", ""
        ),
    )
    runner_group: RunnerGroup = RunnerGroup(
        id=2,
        name="test",
        organization="octo-org",
        manager=settings.name,
        backend=GCPBackend(
            name=Backends.gcloud,
            config=config,
            instance_config=GCPInstanceConfig(),
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


def test_gcp_instance(runner: Runner):
    gcp_instance: GCPInstanceConfig = GCPInstanceConfig()
    instance = gcp_instance.configure_instance(runner)
    # Assert name is defined
    assert instance.name == runner.name

    # Assert metadata are properly set
    startup: bool = False
    assert runner.encoded_jit_config is not None
    for item in instance.metadata.items:
        if item.key == "startup-script":
            assert runner.name in item.value
            assert runner.labels[0].name in item.value
            assert runner.encoded_jit_config in item.value
            startup = True

    assert startup is True


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


@mark.skipif(
    not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"), reason="GCP credentials not found"
)
def test_update(gcp_runner, gcp_group):
    runner = gcp_group.backend.create(gcp_runner)
    gcp_group.backend.update(runner)
    runner = Runner.find(Runner.labels == runner.labels).first()
    gcp_group.backend.delete(runner)
    with raises(NotFoundError):
        gcp_group.backend.get(runner.instance_id)


@mark.skipif(
    not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"), reason="GCP credentials not found"
)
def test_get(gcp_runner, gcp_group):
    runner = gcp_group.backend.create(gcp_runner)
    assert runner == gcp_group.backend.get(runner.instance_id)
    gcp_group.backend.delete(runner)
    with raises(NotFoundError):
        gcp_group.backend.get(runner.instance_id)


@mark.skipif(
    not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"), reason="GCP credentials not found"
)
def test_list(gcp_runner, gcp_group):
    runner = gcp_group.backend.create(gcp_runner)
    runners: List[Runner] = gcp_group.backend.list()
    assert any(runner.name == r.name for r in runners)
    gcp_group.backend.delete(runner)
    with raises(NotFoundError):
        gcp_group.backend.get(runner.instance_id)
