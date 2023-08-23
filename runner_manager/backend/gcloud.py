import logging
import time
from typing import Dict, List, Literal

from google.api_core.exceptions import BadRequest, NotFound
from google.api_core.extended_operation import ExtendedOperation
from google.cloud.compute import (
    AccessConfig,
    AttachedDisk,
    AttachedDiskInitializeParams,
    Image,
    ImagesClient,
    Instance,
    InstancesClient,
    NetworkInterface,
    Operation,
    ZoneOperationsClient,
)
from pydantic import Field

from runner_manager.backend.base import BaseBackend
from runner_manager.models.backend import Backends, GCPConfig, GCPInstanceConfig
from runner_manager.models.runner import Runner

log = logging.getLogger(__name__)


class GCPBackend(BaseBackend):
    name: Literal[Backends.gcloud] = Field(default=Backends.gcloud)
    config: GCPConfig
    instance_config: GCPInstanceConfig

    @property
    def client(self) -> InstancesClient:
        """Returns a GCP Compute Engine client."""
        return InstancesClient()

    @property
    def image_client(self) -> ImagesClient:
        """Returns a GCP Image client."""
        return ImagesClient()

    @property
    def zone_operation_client(self) -> ZoneOperationsClient:
        """Returns a GCP Zone Operation client."""
        return ZoneOperationsClient()

    def wait_for_operation(
        self,
        project: str,
        zone: str,
        operation: str,
    ):
        while True:
            result = self.zone_operation_client.get(
                project=project, zone=zone, operation=operation
            )

            if result.status == Operation.Status.DONE:
                if result.error:
                    raise Exception(result.error)
                return result
            time.sleep(1)

    def get_image(self) -> Image:
        return self.image_client.get_from_family(
            project=self.instance_config.image_project,
            family=self.instance_config.image_family,
        )

    def get_disks(self) -> List[AttachedDisk]:
        return [
            AttachedDisk(
                boot=True,
                auto_delete=True,
                initialize_params=AttachedDiskInitializeParams(
                    source_image=self.get_image().self_link
                ),
            )
        ]

    def get_network_interfaces(self) -> List[NetworkInterface]:
        return [
            NetworkInterface(
                network=self.instance_config.network,
                access_configs=[
                    AccessConfig(
                        name="External NAT",
                    )
                ],
            )
        ]

    def create(self, runner: Runner):
        labels: Dict[str, str] = {}
        if self.manager:
            labels["runner-manager"] = self.manager
        try:
            image = self.get_image()
            disks = self.get_disks()
            network_interfaces = self.get_network_interfaces()
            self.instance_config.image = image.self_link
            self.instance_config.disks = disks
            self.instance_config.machine_type = (
                f"zones/{self.config.zone}/machineTypes/"
                f"{self.instance_config.machine_type}"
            )
            self.instance_config.network_interfaces = network_interfaces
            self.instance_config.labels = labels
            instance: Instance = self.instance_config.configure_instance(runner)
            ext_operation: ExtendedOperation = self.client.insert(
                project=self.config.project_id,
                zone=self.config.zone,
                instance_resource=instance,
            )
            self.wait_for_operation(
                project=self.config.project_id,
                zone=self.config.zone,
                operation=ext_operation.name,
            )
            runner.instance_id = runner.name

        except Exception as e:
            raise e
        return super().create(runner)

    def delete(self, runner: Runner):
        try:
            if runner.instance_id:
                self.client.delete(
                    project=self.config.project_id,
                    zone=self.config.zone,
                    instance=runner.instance_id,
                )
            else:
                self.client.delete(
                    project=self.config.project_id,
                    zone=self.config.zone,
                    instance=runner.name,
                )
        except NotFound:
            pass
        except BadRequest:
            if runner.instance_id is None:
                log.info(f"Instance {runner.name} is misconfigured and does not exist.")
                pass
            raise
        except Exception as e:
            raise e
        return super().delete(runner)

    def get(self, instance_id: str) -> Runner:
        instance: Instance = self.client.get(
            project=self.config.project_id,
            zone=self.config.zone,
            instance=instance_id,
        )
        return Runner.find(Runner.instance_id == instance.name).first()

    def list(self) -> List[Runner]:
        runners: List[Runner] = []
        try:
            instances = self.client.list(
                project=self.config.project_id,
                zone=self.config.zone,
            )
            for instance in instances:
                labels = instance.labels or {}
                if self.manager and "runner-manager" in labels:
                    runner = Runner(
                        name=instance.name,
                        instance_id=instance.name,
                        busy=False,
                    )
                    runners.append(runner)

        except Exception as e:
            raise e
        return runners

    def update(self, runner: Runner) -> Runner:
        try:
            instance: Instance = self.client.get(
                project=self.config.project_id,
                zone=self.config.zone,
                instance=runner.instance_id,
            )
            if instance.status != "RUNNING":
                raise Exception(f"Instance {instance.name} is not running.")
            labels = {}
            if runner.labels is not None:
                labels = {label.name: label.name for label in runner.labels}
            instance.labels = labels
            ext_operation: ExtendedOperation = self.client.update(
                instance_resource=instance
            )
            self.wait_for_operation(
                project=self.config.project_id,
                zone=self.config.zone,
                operation=ext_operation.name,
            )
        except Exception as e:
            raise e
        return super().update(runner)
