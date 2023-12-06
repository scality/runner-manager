import os
from typing import List

from google.cloud.compute import Image
from pytest import fixture, mark, raises
from redis_om import NotFoundError

from runner_manager.backend.gcloud import GCPBackend
from runner_manager.models.backend import Backends, GCPConfig, GCPInstanceConfig
from runner_manager.models.runner import Runner
from runner_manager.models.runner_group import RunnerGroup


@fixture()
def gcp_group(settings, monkeypatch) -> RunnerGroup:
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
            instance_config=GCPInstanceConfig(
                labels={
                    "key": "value",
                }
            ),
        ),
        labels=[
            "label",
        ],
    )
    fake_image = Image(
        self_link="my_image_link",
        source_image="my_image",
    )

    monkeypatch.setattr(GCPBackend, "image", fake_image)
    return runner_group


@fixture()
def gcp_runner(runner: Runner, gcp_group: RunnerGroup) -> Runner:
    # Cleanup and return a runner for testing
    gcp_group.backend.delete(runner)
    return runner


def test_gcp_network_interfaces(gcp_group: RunnerGroup):
    interfaces = gcp_group.backend.network_interfaces
    assert len(interfaces) == 1


def test_gcp_group(gcp_group: RunnerGroup):
    gcp_group.save()
    gcp_group.delete(gcp_group.pk)


def test_gcp_metadata(runner: Runner, gcp_group):
    metadata = gcp_group.backend.configure_metadata(runner)

    # Assert metadata are properly set
    startup: bool = False
    assert runner.encoded_jit_config is not None
    for item in metadata.items:
        if item.key == "startup-script":
            assert runner.name in item.value
            assert runner.labels[0].name in item.value
            assert runner.encoded_jit_config in item.value
            startup = True

    assert startup is True


def test_gcp_setup_labels(runner: Runner, gcp_group: RunnerGroup):
    labels = gcp_group.backend.setup_labels(runner)
    assert labels["status"] == runner.status
    assert labels["busy"] == str(runner.busy).lower()
    assert labels["key"] == "value"


def test_gcp_spot_config(runner: Runner, gcp_group: RunnerGroup):
    gcp_group.backend.instance_config.spot = True
    scheduling = gcp_group.backend.scheduling
    assert scheduling.provisioning_model == "SPOT"
    assert scheduling.instance_termination_action == "DELETE"
    gcp_group.backend.instance_config.spot = False
    scheduling = gcp_group.backend.scheduling
    assert scheduling.provisioning_model == "STANDARD"
    assert scheduling.instance_termination_action == "DEFAULT"


def test_gcp_disks(runner: Runner, gcp_group: RunnerGroup):
    # patch self.image.self_link to return a fake image

    disks = gcp_group.backend.disks
    zone = gcp_group.backend.config.zone
    disk_type = gcp_group.backend.instance_config.disk_type
    assert len(disks) == 1
    assert (
        disks[0].initialize_params.disk_size_gb
        == gcp_group.backend.instance_config.disk_size_gb
    )
    assert disks[0].boot is True
    assert disks[0].auto_delete is True
    assert disks[0].initialize_params.disk_type == f"zones/{zone}/diskTypes/{disk_type}"


def test_gcp_instance(runner: Runner, gcp_group: RunnerGroup):
    instance = gcp_group.backend.configure_instance(runner)
    assert instance.name == runner.name


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
