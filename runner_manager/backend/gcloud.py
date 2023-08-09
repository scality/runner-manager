import time
from typing import List, Literal

from google.api_core.exceptions import NotFound
from google.api_core.extended_operation import ExtendedOperation
from google.cloud.compute import (
    Image,
    ImagesClient,
    Instance,
    InstancesClient,
    Operation,
    ZoneOperationsClient,
)
from pydantic import Field

from runner_manager.backend.base import BaseBackend
from runner_manager.models.backend import Backends, GCPConfig, GCPInstanceConfig
from runner_manager.models.runner import Runner


class GCPBackend(BaseBackend):
    name: Literal[Backends.gcloud] = Field(default=Backends.gcloud)
    config: GCPConfig
    instance_config: GCPInstanceConfig

    @property
    def compute_client(self) -> InstancesClient:
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

    def configure_instance(self, runner: Runner):
        labels = {
            "runner-manager": self.runner_manager,
        }
        source_disk_image: Image = self.image_client.get_from_family(
            project=self.instance_config.image["project"],
            family=self.instance_config.image["family"],
        )
        machine_type = (
            f"zones/{self.config.zone}/machineTypes/{self.instance_config.machine_type}"
        )
        network = f"projects/{self.config.project_id}/global/networks/{self.instance_config.network}"
        instance: Instance = Instance(
            name=runner.name,
            machine_type=machine_type,
            labels=labels,
            disks=[
                {
                    "boot": True,
                    "auto_delete": True,
                    "initialize_params": {
                        "source_image": source_disk_image.self_link,
                    },
                }
            ],
            network_interfaces=[
                {
                    "network": network,
                    "access_configs": [
                        {
                            "name": "External NAT",
                            "type_": "ONE_TO_ONE_NAT",
                        }
                    ],
                }
            ],
            service_accounts=[
                {
                    "email": self.config.service_account_email,
                    "scopes": [
                        "https://www.googleapis.com/auth/devstorage.read_write",
                        "https://www.googleapis.com/auth/logging.write",
                    ],
                }
            ],
        )
        return instance

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

    def create(self, runner: Runner):
        try:
            instance: Instance = self.configure_instance(runner)
            ext_operation: ExtendedOperation = self.compute_client.insert(
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
                self.compute_client.delete(
                    project=self.config.project_id,
                    zone=self.config.zone,
                    instance=runner.instance_id,
                )
            else:
                self.compute_client.delete(
                    project=self.config.project_id,
                    zone=self.config.zone,
                    instance=runner.name,
                )
        except NotFound:
            pass
        except Exception as e:
            raise e
        return super().delete(runner)

    def get(self, instance_id: str) -> Runner:
        instance: Instance = self.compute_client.get(
            project=self.config.project_id,
            zone=self.config.zone,
            instance=instance_id,
        )
        return Runner.find(Runner.instance_id == instance.name).first()

    def list(self) -> List[Runner]:
        runners: List[Runner] = []
        try:
            instances = self.compute_client.aggregated_list(
                project=self.config.project_id,
            )
            for zone, instance_list in instances.items():
                for instance in instance_list.instances:
                    labels = instance.labels or {}
                    if (
                        "runner-manager" in labels
                        and labels["runner-manager"] == self.runner_manager
                    ):
                        runner = Runner(
                            name=instance.name,
                            instance_id=instance.name,
                            busy=False,
                        )
                        runners.append(runner)

        except Exception as e:
            raise e
        return runners
