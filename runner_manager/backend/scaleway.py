import logging
from typing import Literal
from pydantic import Field

from runner_manager.backend.base import BaseBackend
from runner_manager.models.backend import Backends, ScalewayConfig, ScalewayInstanceConfig

from scaleway import Client
from scaleway.instance.v1 import InstanceV1API
from scaleway.marketplace.v2 import MarketplaceV2API

from runner_manager.models.runner import Runner

log = logging.getLogger(__name__)


class ScalewayBackend(BaseBackend):
    name: Literal[Backends.scaleway] = Field(default=Backends.scaleway)

    config: ScalewayConfig = ScalewayConfig()
    instance_config: ScalewayInstanceConfig = ScalewayInstanceConfig()

    @property
    def scaleway_client(self) -> Client:
        return Client(
            access_key=self.config.access_key,
            secret_key=self.config.secret_key,
            default_project_id=self.config.project_id,
            default_region=self.config.region,
        )
    @property
    def client(self) -> InstanceV1API:
        """Returns a scaleway client."""
        return InstanceV1API(self.scaleway_client)

    @property
    def marketplace(self) -> MarketplaceV2API:
        """Returns a scaleway marketplace client."""
        return MarketplaceV2API(self.scaleway_client)

    def create(self, runner: Runner):
        log.info(f"Creating instance for runner {runner.name}")
        response = self.client._create_server(
            name=runner.name,
            image=self.instance_config.image,
            zone=self.instance_config.zone,
            commercial_type=self.instance_config.commercial_type,
            security_group=self.instance_config.security_group,
            placement_group=self.instance_config.placement_group,
        )
        runner.instance_id = response.server.id if response.server else None

        return super().create(runner)