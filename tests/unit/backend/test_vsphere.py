import os

from pytest import fixture

from runner_manager.backend.vsphere import VsphereBackend
from runner_manager.models.backend import Backends, VsphereConfig, VsphereInstanceConfig
from runner_manager.models.runner import Runner
from runner_manager.models.runner_group import RunnerGroup


@fixture()
def vsphere_group(settings) -> RunnerGroup:
    config = VsphereConfig(server=os.environ.get("GOVC_URL", ""),username=os.environ.get("GOVC_USERNAME", ""),password=os.environ.get("GOVC_PASSWORD", ""))
    runner_group: RunnerGroup = RunnerGroup(
        id=2,
        name="test",
        organization="octo-org",
        manager="runner-manager",
        backend=VsphereBackend(
            name=Backends.vsphere,
            config=config,
            instance_config=VsphereInstanceConfig(
                datacenter=os.environ.get("GOVC_DATACENTER"),
                datastore=os.environ.get("GOVC_DATASTORE"),
                folder="folder",
                portgroup="VM Network",
            ),
        ),
        labels=[
            "label",
        ],
    )

    return runner_group


def test_vsphere_client(vsphere_group: RunnerGroup, runner: Runner):
    runner = vsphere_group.backend.create(runner)
    assert runner.instance_id is not None
