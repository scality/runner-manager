import logging
import time

import googleapiclient.discovery
from googleapiclient.errors import HttpError
from runners_manager.runner.Runner import Runner
from runners_manager.runner.Runner import VmType
from runners_manager.vm_creation.CloudManager import CloudManager
from runners_manager.vm_creation.gcloud.schema import GcloudConfig
from runners_manager.vm_creation.gcloud.schema import GcloudConfigVmType


logger = logging.getLogger("runner_manager")


def get_vm_config(
    runner, machine_type, disk_size_gb, disk_type, source_disk_image, startup_script
):
    return {
        "name": runner.name,
        "machineType": machine_type,
        # Specify the boot disk and the image to use as a source.
        "disks": [
            {
                "boot": True,
                "autoDelete": True,
                "initializeParams": {
                    "diskSizeGb": disk_size_gb,
                    "diskType": disk_type,
                    "sourceImage": source_disk_image,
                },
            }
        ],
        # Specify a network interface with NAT to access the public
        # internet.
        "networkInterfaces": [
            {
                "network": "global/networks/default",
                "accessConfigs": [{"type": "ONE_TO_ONE_NAT", "name": "External NAT"}],
            }
        ],
        # Allow the instance to access cloud storage and logging.
        "serviceAccounts": [
            {
                "email": "default",
                "scopes": [
                    "https://www.googleapis.com/auth/devstorage.read_write",
                    "https://www.googleapis.com/auth/logging.write",
                ],
            }
        ],
        "tags": {"items": runner.vm_type.tags},
        # Metadata is readable from the instance and allows you to
        # pass configuration from deployment scripts to instances.
        "metadata": {
            "items": [
                {
                    # Startup script is automatically executed by the
                    # instance upon startup.
                    "key": "startup-script",
                    "value": startup_script,
                }
            ]
        },
    }


class GcloudManager(CloudManager):
    CONFIG_SCHEMA = GcloudConfig
    CONFIG_VM_TYPE_SCHEMA = GcloudConfigVmType
    compute = googleapiclient.discovery.build("compute", "v1")

    def __init__(
        self,
        name: str,
        settings: dict,
        redhat_username: str,
        redhat_password: str,
        ssh_keys: str,
    ):
        super(GcloudManager, self).__init__(
            name, settings, redhat_username, redhat_password, ssh_keys
        )
        self.project_id = settings.get("project_id")
        self.zone = settings.get("zone")

    def delete_existing_runner(self, runner: Runner):
        """Delete an old runner instance from gcloud if it exists."""
        for listed_runner in self.get_all_vms(runner.name):
            if runner.name == listed_runner.name:
                logger.info(f"Found an existing instance of {runner.name}")
                return self.delete_vm(listed_runner.vm_id)
        logger.info(f"No existing instance for runner {runner.name} has been found")
        return None

    def wait_for_operation(self, operation):
        logger.info(f"Waiting for gcloud operation {operation['name']} to finish...")
        while True:
            result = (
                self.compute.zoneOperations()
                .get(
                    project=self.project_id, zone=self.zone, operation=operation["name"]
                )
                .execute()
            )
            logger.debug(f"Operation {operation['name']} is {result['status']}")

            if result["status"] == "DONE":
                logger.info(f"Operation {operation['name']} have finished")

                if "error" in result:
                    raise Exception(result["error"])
                return result
            time.sleep(1)

    def create_vm(
        self,
        runner: Runner,
        runner_token: int or None,
        github_organization: str,
        installer: str,
        call_number=0,
    ):
        try:
            logger.info(f"Creating {runner.name} instance")
            self.delete_existing_runner(runner)
            source_disk_image = (
                self.compute.images()
                .getFromFamily(
                    project=runner.vm_type.config["project"],
                    family=runner.vm_type.config["family"],
                )
                .execute()["selfLink"]
            )
            machine_type = f"zones/{self.zone}/machineTypes/{runner.vm_type.config['machine_type']}"
            startup_script = self.script_init_runner(
                runner, runner_token, github_organization, installer
            )
            disk_size_gb = runner.vm_type.config["disk_size_gb"]
            disk_type = f"projects/{self.project_id}/zones/{self.zone}/diskTypes/pd-ssd"

            config = get_vm_config(
                runner,
                machine_type,
                disk_size_gb,
                disk_type,
                source_disk_image,
                startup_script,
            )

            operation = (
                self.compute.instances()
                .insert(project=self.project_id, zone=self.zone, body=config)
                .execute()
            )

            # https://cloud.google.com/python/docs/reference/compute/latest/google.cloud.compute_v1.types.Operation
            result = self.wait_for_operation(operation)
            logger.info(f"{runner.name} instance has been created")
            return result["targetId"]
        except Exception as e:
            logger.error(e)
            raise e

    def delete_vm(self, runner: Runner):
        try:
            logger.info(f"Deleting instance of runner {runner.name}...")
            operation = (
                self.compute.instances()
                .delete(project=self.project_id, zone=self.zone, instance=runner.vm_id)
                .execute()
            )
            self.wait_for_operation(operation)
            logger.info(f"Instance of runner {runner.name} has been deleted")
        except HttpError as e:
            if e.status_code == 404:
                logger.info(f"Instance of runner {runner.name} was already deleted")
                pass

    def get_boot_disk(self, disks: list[dict]) -> dict or None:
        for disk in disks:
            if disk["boot"]:
                return disk
        return None

    def get_all_vms(self, prefix: str) -> list[Runner]:
        logger.info(
            f"Retrieving runner instances hosted on gcloud with prefix {prefix}"
        )
        result = (
            self.compute.instances()
            .list(project=self.project_id, zone=self.zone)
            .execute()
        )
        instances = result.get("items", [])
        if not instances:
            return []

        runners: list[Runner] = []

        # For ref on objects:
        # instances:
        # https://cloud.google.com/python/docs/reference/compute/latest/google.cloud.compute_v1.types.Instance
        # disk:
        # https://cloud.google.com/python/docs/reference/compute/latest/google.cloud.compute_v1.types.AttachedDisk
        # initialize_params:
        # https://cloud.google.com/python/docs/reference/compute/latest/google.cloud.compute_v1.types.AttachedDiskInitializeParams
        #
        for vm in instances:
            if vm["name"].startswith(prefix):
                runners.append(
                    Runner(
                        vm["name"],
                        vm["id"],
                        VmType(
                            {
                                "tags": [],
                                "config": {},
                                "quantity": {},
                            }
                        ),
                    )
                )
        logger.info(
            f"{len(runners)} runners with prefix {prefix} are running on gcloud"
        )
        return runners

    def delete_images_from_shelved(self, name):
        logger.info(f"nothing to do for {name}")
