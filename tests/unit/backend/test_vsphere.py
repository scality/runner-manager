import os

from pytest import fixture, mark

from runner_manager.backend.vsphere import VsphereBackend
from runner_manager.models.backend import Backends, VsphereConfig, VsphereInstanceConfig
from runner_manager.models.runner import Runner
from runner_manager.models.runner_group import RunnerGroup


@fixture()
def vsphere_group(settings) -> RunnerGroup:
    config = VsphereConfig(
        server=os.environ.get("GOVC_URL", ""),
        username=os.environ.get("GOVC_USERNAME", ""),
        password=os.environ.get("GOVC_PASSWORD", ""),
    )
    runner_group: RunnerGroup = RunnerGroup(
        id=2,
        name="test",
        organization="octo-org",
        manager="runner-manager",
        backend=VsphereBackend(
            name=Backends.vsphere,
            config=config,
            instance_config=VsphereInstanceConfig(
                library="runners",
                library_item="jammy-server-cloudimg-amd64",
                datacenter=os.environ.get("GOVC_DATACENTER", ""),
                datastore=os.environ.get("GOVC_DATASTORE", ""),
            ),
        ),
        labels=[
            "label",
        ],
    )

    return runner_group


@mark.skipif(not os.getenv("GOVC_URL"), reason="GOVC_URL environment variable not set")
def test_vsphere_client(vsphere_group: RunnerGroup, runner: Runner):
    # deleting the runner should not raise an exception
    runner.instance_id = "i-1234"
    vsphere_group.backend.delete(runner)
    runner = vsphere_group.backend.create(runner)
    assert runner.instance_id is not None
    vsphere_group.backend.delete(runner)
