import time
from typing import List, Literal

from google.api_core.exceptions import NotFound
from google.api_core.extended_operation import ExtendedOperation
from google.cloud.compute import (
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
            instance: Instance = self.instance_config.instance
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
