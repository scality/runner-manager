import os
from typing import List

from githubkit.versions.latest.webhooks import WorkflowJobEvent
from google.cloud.compute import Image, NetworkInterface
from hypothesis import given
from pytest import fixture, mark, raises
from redis_om import NotFoundError

from runner_manager.backend.gcloud import GCPBackend
from runner_manager.models.backend import Backends, GCPConfig, GCPInstanceConfig
from runner_manager.models.runner import Runner
from runner_manager.models.runner_group import RunnerGroup

from ...strategies import WorkflowJobInProgressStrategy


@fixture()
def gcp_group(settings) -> RunnerGroup:
    config = GCPConfig(
        project_id=os.environ.get("GOOGLE_CLOUD_PROJECT", ""),
        region=os.environ.get("CLOUDSDK_COMPUTE_REGION", ""),
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
    return runner_group


@fixture()
def fake_gcp_group(gcp_group, monkeypatch):
    fake_image = Image(
        self_link="my_image_link",
        source_image="my_image",
    )

    monkeypatch.setattr(GCPBackend, "image", fake_image)
    return gcp_group


@fixture()
def gcp_runner(runner: Runner, gcp_group: RunnerGroup) -> Runner:
    # Cleanup and return a runner for testing
    gcp_group.backend.delete(runner)
    return runner


def test_gcp_network_interfaces(fake_gcp_group: RunnerGroup):
    interfaces: List[NetworkInterface] = fake_gcp_group.backend.network_interfaces
    assert len(interfaces) == 1
    assert "default" in fake_gcp_group.backend.network_interfaces[0].subnetwork
    assert interfaces[0].access_configs[0].name == "External NAT"
    # Test disabling external IP
    fake_gcp_group.backend.instance_config.enable_external_ip = False
    interfaces: List[NetworkInterface] = fake_gcp_group.backend.network_interfaces
    assert len(interfaces) == 1
    assert len(interfaces[0].access_configs) == 0


def test_gcp_group(fake_gcp_group: RunnerGroup):
    fake_gcp_group.save()
    fake_gcp_group.delete(fake_gcp_group.pk)


def test_gcp_metadata(runner: Runner, fake_gcp_group):
    metadata = fake_gcp_group.backend.configure_metadata(runner)

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


def test_gcp_setup_labels(runner: Runner, fake_gcp_group: RunnerGroup):
    labels = fake_gcp_group.backend.setup_labels(runner)
    assert labels["status"] == runner.status
    assert labels["busy"] == str(runner.busy).lower()
    assert labels["key"] == "value"


@given(webhook=WorkflowJobInProgressStrategy)
def test_gcp_setup_labels_with_webhook(webhook: WorkflowJobEvent):
    runner: Runner = Runner(
        name=webhook.workflow_job.runner_name,
        id=webhook.workflow_job.runner_id,
        busy=True,
        runner_group_name=webhook.workflow_job.runner_group_name,
        runner_group_id=webhook.workflow_job.runner_group_id,
        status="online",
    )
    backend = GCPBackend(
        config=GCPConfig(
            zone="europe-west1-a",
            project_id="project",
        ),
        instance_config=GCPInstanceConfig(),
    )
    labels = backend.setup_labels(runner, webhook)
    assert "workflow" in labels.keys()
    assert "repository" in labels.keys()

    # Test with no webhook
    labels = backend.setup_labels(runner)
    assert "workflow" not in labels.keys()


def test_gcp_spot_config(runner: Runner, fake_gcp_group: RunnerGroup):
    fake_gcp_group.backend.instance_config.spot = True
    scheduling = fake_gcp_group.backend.scheduling
    assert scheduling.provisioning_model == "SPOT"
    assert scheduling.instance_termination_action == "DELETE"
    fake_gcp_group.backend.instance_config.spot = False
    scheduling = fake_gcp_group.backend.scheduling
    assert scheduling.provisioning_model == "STANDARD"
    assert scheduling.instance_termination_action == "DEFAULT"


def test_gcp_disks(runner: Runner, fake_gcp_group: RunnerGroup):
    # patch self.image.self_link to return a fake image

    disks = fake_gcp_group.backend.disks
    zone = fake_gcp_group.backend.config.zone
    disk_type = fake_gcp_group.backend.instance_config.disk_type
    assert len(disks) == 1
    assert (
        disks[0].initialize_params.disk_size_gb
        == fake_gcp_group.backend.instance_config.disk_size_gb
    )
    assert disks[0].boot is True
    assert disks[0].auto_delete is True
    assert disks[0].initialize_params.disk_type == f"zones/{zone}/diskTypes/{disk_type}"


def test_gcp_instance(runner: Runner, fake_gcp_group: RunnerGroup):
    instance = fake_gcp_group.backend.configure_instance(runner)
    assert instance.name == runner.name


def test_sanitize_label(fake_gcp_group: RunnerGroup):
    assert "test" == fake_gcp_group.backend._sanitize_label_value("test")
    assert "42" == fake_gcp_group.backend._sanitize_label_value(42)
    assert "42" == fake_gcp_group.backend._sanitize_label_value(42.0)
    assert "" == fake_gcp_group.backend._sanitize_label_value(None)
    assert "test" == fake_gcp_group.backend._sanitize_label_value("-test-")
    assert "" == fake_gcp_group.backend._sanitize_label_value(float("nan"))


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
    assert len(runners) == 1
    gcp_group.backend.delete(runner)
    with raises(NotFoundError):
        gcp_group.backend.get(runner.instance_id)
