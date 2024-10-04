import os
import uuid
from inspect import signature
from time import sleep
from typing import Callable

from openstack.compute.v2 import _proxy, server
from openstack.connection import Connection
from openstack.proxy import Proxy
from pytest import fixture, raises
from redis_om import NotFoundError

from runner_manager.backend.openstack import OpenstackBackend, OpenstackInstance
from runner_manager.models.backend import (
    Backends,
    OpenstackConfig,
    OpenstackInstanceConfig,
)
from runner_manager.models.runner import Runner, RunnerLabel
from runner_manager.models.runner_group import RunnerGroup


def compare_signatures(func1: Callable, func2: Callable):
    return signature(func1) == signature(func2)


class MockCompute(Proxy):
    _instances: dict[str, server.Server] = {}

    def __init__(self):
        pass

    def servers(self, details=True, all_projects=False, **query):
        for instance in self._instances.values():
            yield instance

    def create_server(self, **attrs):
        new_server = MockServer(**attrs)
        self._instances[str(new_server.id)] = new_server
        return new_server

    def delete_server(self, server, ignore_missing=True, force=False):
        return self._instances.pop(server)

    def set_server_metadata(self, server, **metadata):
        self._instances[server].set_metadata(session=None, metadata=metadata)


class MockConnection:
    compute: MockCompute = MockCompute()

    def create_server(
        self,
        name,
        image=None,
        flavor=None,
        auto_ip=True,
        ips=None,
        ip_pool=None,
        root_volume=None,
        terminate_volume=False,
        wait=False,
        timeout=180,
        reuse_ips=True,
        network=None,
        boot_from_volume=False,
        volume_size="50",
        boot_volume=None,
        volumes=None,
        nat_destination=None,
        group=None,
        **kwargs,
    ):
        return self.compute.create_server(
            name=name,
            image=image,
            flavor=flavor,
            volume_size=volume_size,
            network=network,
            **kwargs,
        )

    def delete_server(
        self, name_or_id, wait=False, timeout=180, delete_ips=False, delete_ip_retry=1
    ):
        return self.compute.delete_server(name_or_id)

    def set_server_metadata(self, name_or_id, metadata):
        self.compute.set_server_metadata(name_or_id, **metadata)

    def get_server_by_id(self, id):
        return self.compute._instances.get(id, None)


class MockServer(server.Server):
    name: str = ""
    image: str = ""
    flavor: str = ""
    volume_size: str = "20"
    userdata: str = ""
    meta: dict[str, str] = {}
    network: str = ""
    status: str = "ACTIVE"

    def __init__(
        self,
        name: str,
        image,
        flavor,
        volume_size: str,
        network,
        userdata: str = "",
        meta: dict[str, str] = {},
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.name = name
        self.image = image
        self.flavor = flavor
        self.volume_size = volume_size
        self.userdata = userdata
        self.meta = meta
        self.network = network
        self.id = str(uuid.uuid4())

    def set_metadata(self, session, metadata, *args, **kwargs) -> None:
        self.meta.update(metadata)


@fixture()
def openstack_group(settings) -> RunnerGroup:
    runner_group: RunnerGroup = RunnerGroup(
        id=1,
        name="test",
        organization="octo-org",
        manager=settings.name,
        backend=OpenstackBackend(
            name=Backends.openstack,
            config=OpenstackConfig(cloud=os.getenv("OPENSTACK_CLOUD")),
            manager=settings.name,
            instance_config=OpenstackInstanceConfig(
                image="182c6fd0-775c-4dh3-9be3-d14c95add0d3",
                network="c4d017da-c7e8-4019-bdb1-3d426d638c93",
            ),
        ),
        labels=[
            "label",
        ],
    )
    return runner_group


@fixture()
def openstack_runner(runner: Runner, openstack_group: RunnerGroup) -> Runner:
    openstack_group.backend.delete(runner)
    return runner


def use_live_openstack():
    if os.getenv("USE_LIVE_OPENSTACK") == "true":
        return True
    return False


def test_openstack_instance_config(runner: Runner):
    instance_config = OpenstackInstanceConfig(
        network="8175b591-j79a-4846-9g97-43cb083a93b5",
        meta={"test": "test"},
    )
    instance: OpenstackInstance = instance_config.configure_instance(runner)
    assert instance["image"] == instance_config.image
    assert instance["flavor"] == instance_config.flavor
    assert instance["volume_size"] == instance_config.volume_size
    assert instance["network"] == instance_config.network
    meta = instance["meta"]
    assert "Name" in meta
    assert "test" in meta


def test_create_delete(openstack_group, openstack_runner, monkeypatch):
    if not use_live_openstack():
        monkeypatch.setattr(OpenstackBackend, "client", MockConnection())
    runner = openstack_group.backend.create(openstack_runner)
    assert runner.instance_id is not None
    assert runner.backend == "openstack"
    assert Runner.find(Runner.instance_id == runner.instance_id).first() == runner
    openstack_group.backend.delete(runner)
    with raises(NotFoundError):
        Runner.find(Runner.instance_id == runner.instance_id).first()


def test_list(openstack_group, openstack_runner, monkeypatch):
    if not use_live_openstack():
        monkeypatch.setattr(OpenstackBackend, "client", MockConnection())
    runner = openstack_group.backend.create(openstack_runner)
    runners = openstack_group.backend.list()
    assert runner in runners
    openstack_group.backend.delete(runner)
    with raises(NotFoundError):
        openstack_group.backend.get(runner.instance_id)


def test_update(openstack_group, openstack_runner, monkeypatch):
    if not use_live_openstack():
        monkeypatch.setattr(OpenstackBackend, "client", MockConnection())
    runner = openstack_group.backend.create(openstack_runner)
    runner.labels = [RunnerLabel(name="test", type="custom")]
    instance: server.Server | None = openstack_group.backend.client.get_server_by_id(
        runner.instance_id
    )
    while instance and str(instance.status) == "BUILD":
        instance = openstack_group.backend.client.get_server_by_id(runner.instance_id)
        sleep(1)
    openstack_group.backend.update(runner)
    assert runner.labels == [RunnerLabel(name="test", type="custom")]
    openstack_group.backend.delete(runner)
    with raises(NotFoundError):
        openstack_group.backend.get(runner.instance_id)


def test_mock_signatures():
    assert compare_signatures(Connection.create_server, MockConnection.create_server)
    assert compare_signatures(Connection.delete_server, MockConnection.delete_server)
    assert compare_signatures(
        Connection.set_server_metadata, MockConnection.set_server_metadata
    )
    assert compare_signatures(
        Connection.get_server_by_id, MockConnection.get_server_by_id
    )
    assert compare_signatures(_proxy.Proxy.servers, MockCompute.servers)
    assert compare_signatures(_proxy.Proxy.create_server, MockCompute.create_server)
    assert compare_signatures(_proxy.Proxy.delete_server, MockCompute.delete_server)
    assert compare_signatures(
        _proxy.Proxy.set_server_metadata, MockCompute.set_server_metadata
    )
