from typing import List, Literal, Optional

import openstack
from githubkit.versions.latest.webhooks import WorkflowJobEvent
from openstack.compute.v2.server import Server
from openstack.connection import Connection
from openstack.exceptions import SDKException
from pydantic import Field
from redis_om import NotFoundError

from runner_manager.backend.base import BaseBackend
from runner_manager.logging import log
from runner_manager.models.backend import (
    Backends,
    OpenstackConfig,
    OpenstackInstance,
    OpenstackInstanceConfig,
)
from runner_manager.models.runner import Runner


class OpenstackBackend(BaseBackend):
    name: Literal[Backends.openstack] = Field(default=Backends.openstack)
    config: OpenstackConfig = OpenstackConfig()
    instance_config: OpenstackInstanceConfig = OpenstackInstanceConfig()

    @property
    def client(self) -> Connection:
        return openstack.connect(
            cloud=self.config.cloud, region_name=self.config.region_name
        )

    def create(self, runner: Runner):
        """Create a runner"""
        instance_resource: OpenstackInstance = self.instance_config.configure_instance(
            runner
        )
        try:
            instance = self.client.create_server(**instance_resource)
            runner.instance_id = instance.id
        except Exception as e:
            log.error(e)
            raise e
        return super().create(runner)

    def delete(self, runner: Runner):
        """Delete a runner"""
        if runner.instance_id:
            try:
                self.client.delete_server(name_or_id=runner.instance_id)
            except SDKException as e:
                log.error(e)
                raise e
        return super().delete(runner)

    def list(self) -> List[Runner]:
        try:
            servers: List[Server] = list(
                self.client.compute.servers(
                    tags={
                        "manager": str(self.manager),
                        "runner_group": str(self.runner_group),
                    }
                )
            )
        except Exception as e:
            log.error(e)
            raise e
        runners: List[Runner] = []
        for instance in servers:
            instance_id = instance.id
            name = instance.name
            try:
                runner = Runner.find(
                    Runner.instance_id == instance_id,
                ).first()
            except NotFoundError:
                runner = Runner(
                    name=name,
                    instance_id=instance_id,
                    runner_group_name=self.runner_group,
                    busy=False,
                    created_at=instance.launched_at,
                )
            runners.append(runner)
        return runners

    def update(
        self, runner: Runner, webhook: Optional[WorkflowJobEvent] = None
    ) -> Runner:
        """Update a runner"""
        if runner.instance_id:
            try:
                self.client.set_server_metadata(
                    runner.instance_id,
                    {"status": runner.status, "busy": str(runner.busy)},
                )
            except Exception as e:
                log.error(e)
                raise e
        return super().update(runner, webhook)
