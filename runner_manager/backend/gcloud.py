import logging
import re
import time
from typing import List, Literal, MutableMapping

from google.api_core.exceptions import BadRequest, NotFound
from google.api_core.extended_operation import ExtendedOperation
from google.cloud.compute import (
    AccessConfig,
    AdvancedMachineFeatures,
    AttachedDisk,
    AttachedDiskInitializeParams,
    Image,
    ImagesClient,
    Instance,
    InstancesClient,
    Items,
    Metadata,
    NetworkInterface,
    Operation,
    Scheduling,
    ServiceAccount,
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

    @property
    def image(self) -> Image:
        return self.image_client.get_from_family(
            project=self.instance_config.image_project,
            family=self.instance_config.image_family,
        )

    @property
    def disks(self) -> List[AttachedDisk]:
        return [
            AttachedDisk(
                boot=True,
                auto_delete=True,
                initialize_params=AttachedDiskInitializeParams(
                    source_image=self.image.self_link,
                    disk_size_gb=self.instance_config.disk_size_gb,
                    disk_type=f"zones/{self.config.zone}/diskTypes/{self.instance_config.disk_type}",
                ),
            )
        ]

    @property
    def network_interfaces(self) -> List[NetworkInterface]:
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

    @property
    def scheduling(self) -> Scheduling:
        """Configure scheduling."""
        if self.instance_config.spot:
            return Scheduling(
                provisioning_model="SPOT", instance_termination_action="DELETE"
            )
        else:
            return Scheduling(
                provisioning_model="STANDARD", instance_termination_action="DEFAULT"
            )

    def configure_metadata(self, runner: Runner) -> Metadata:
        items: List[Items] = []
        env = self.instance_config.runner_env(runner)
        for key, value in env.dict().items():
            items.append(Items(key=key, value=value))
        # Template the startup script to install and setup the runner
        # with the appropriate configuration.
        startup_script = self.instance_config.template_startup(runner)
        items.append(Items(key="startup-script", value=startup_script))
        return Metadata(items=items)

    def configure_instance(self, runner: Runner) -> Instance:
        """Configure instance."""
        return Instance(
            name=runner.name,
            disks=self.disks,
            machine_type=(
                f"zones/{self.config.zone}/machineTypes/"
                f"{self.instance_config.machine_type}"
            ),
            network_interfaces=self.network_interfaces,
            labels=self.setup_labels(runner),
            metadata=self.configure_metadata(runner),
            advanced_machine_features=AdvancedMachineFeatures(
                enable_nested_virtualization=self.instance_config.enable_nested_virtualization
            ),
            scheduling=self.scheduling,
            service_accounts=[
                ServiceAccount(
                    email="default",
                    scopes=[
                        "https://www.googleapis.com/auth/logging.write",
                        "https://www.googleapis.com/auth/monitoring.write",
                    ],
                )
            ],
        )

    def _sanitize_label_value(self, value: str) -> str:
        value = value[:63]
        value = value.lower()
        value = re.sub(r"[^a-z0-9_-]", "-", value)
        return value

    def setup_labels(self, runner: Runner) -> MutableMapping[str, str]:
        labels: MutableMapping[str, str] = self.instance_config.labels.copy()
        if self.manager:
            labels["runner-manager"] = self.manager
        labels["status"] = self._sanitize_label_value(runner.status)
        labels["busy"] = self._sanitize_label_value(str(runner.busy))
        return labels

    def create(self, runner: Runner):
        try:
            instance: Instance = self.configure_instance(runner)

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
                return super().delete(runner)
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
                instance=runner.instance_id or runner.name,
            )
            instance.labels = self.setup_labels(runner)

            log.info(f"Updating {runner.name} labels to {instance.labels}")
            self.client.update(
                instance=runner.instance_id or runner.name,
                project=self.config.project_id,
                zone=self.config.zone,
                instance_resource=instance,
            )
            log.info(f"Updated {runner.name} labels to {instance.labels}")
        except Exception as e:
            super().update(runner)
            raise e
        return super().update(runner)
