import logging
from base64 import b64encode
from typing import List, Literal

from com.vmware.content.library_client import Item
from com.vmware.content_client import Library
from com.vmware.vcenter.ovf_client import (
    IpAllocationParams,
    LibraryItem,
    Property,
    PropertyParams,
    SizeParams,
)
from com.vmware.vcenter.vm.hardware_client import Cpu, Memory
from com.vmware.vcenter.vm_client import Power
from com.vmware.vcenter_client import VM, Datacenter, Datastore, ResourcePool
from pydantic import Field
from requests import Session
from vmware.vapi.vsphere.client import VsphereClient, create_vsphere_client

from runner_manager.backend.base import BaseBackend
from runner_manager.models.backend import Backends, VsphereConfig, VsphereInstanceConfig
from runner_manager.models.runner import Runner

log = logging.getLogger(__name__)


class VsphereBackend(BaseBackend):
    name: Literal[Backends.vsphere] = Field(default=Backends.vsphere)
    config: VsphereConfig
    instance_config: VsphereInstanceConfig

    def _create_client(self) -> VsphereClient:
        session = Session()
        session.verify = self.config.verify_ssl
        return create_vsphere_client(
            server=self.config.server,
            username=self.config.username,
            password=self.config.password,
            session=session,
        )

    def get_library_id(self, client: VsphereClient, library: str) -> str:
        find_spec = Library.FindSpec(name=library)
        library_ids: List[str] = client.content.Library.find(find_spec)
        if len(library_ids) == 0:
            raise Exception("Library with name '{0}' not found".format(library))
        library_id: str = library_ids[0]
        return library_id

    def get_library_item_id(
        self, client: VsphereClient, template: str, library_id: str
    ):
        find_spec = Item.FindSpec(
            name=template,
            library_id=library_id,
        )
        item_ids = client.content.library.Item.find(find_spec)
        item_id = item_ids[0] if item_ids else None
        if item_id:
            log.debug("Library item ID: {0}".format(item_id))
        else:
            raise Exception("Library item with name '{0}' not found".format(template))
        return item_id

    def get_datacenter(self, client, datacenter_name):
        """
        Returns the identifier of a datacenter
        Note: The method assumes only one datacenter with the mentioned name.
        """

        filter_spec = Datacenter.FilterSpec(names=set([datacenter_name]))

        datacenter_summaries = client.vcenter.Datacenter.list(filter_spec)
        if len(datacenter_summaries) > 0:
            datacenter = datacenter_summaries[0].datacenter
            return datacenter
        else:
            return None

    def get_datastore(self, client, datacenter_name, datastore_name):
        """
        Returns the identifier of a datastore
        Note: The method assumes that there is only one datastore and datacenter
        with the mentioned names.
        """
        datacenter = self.get_datacenter(client, datacenter_name)
        if not datacenter:
            log.error("Datacenter '{}' not found".format(datacenter_name))
            return None

        filter_spec = Datastore.FilterSpec(
            names=set([datastore_name]), datacenters=set([datacenter])
        )

        datastore_summaries = client.vcenter.Datastore.list(filter_spec)
        if len(datastore_summaries) > 0:
            datastore = datastore_summaries[0].datastore
            return datastore
        else:
            return None

    def get_resource_pool(self, client, datacenter_name, resource_pool_name=None):
        """
        Returns the identifier of the resource pool with the given name or the
        first resource pool in the datacenter if the name is not provided.
        """
        datacenter = self.get_datacenter(client, datacenter_name)
        if not datacenter:
            log.error("Datacenter '{}' not found".format(datacenter_name))
            return None

        names = set([resource_pool_name]) if resource_pool_name else None
        filter_spec = ResourcePool.FilterSpec(
            datacenters=set([datacenter]), names=names
        )

        resource_pool_summaries = client.vcenter.ResourcePool.list(filter_spec)
        if len(resource_pool_summaries) > 0:
            resource_pool = resource_pool_summaries[0].resource_pool
            log.debug("Selecting ResourcePool '{}'".format(resource_pool))
            return resource_pool
        else:
            log.error(
                "ResourcePool not found in Datacenter '{}'".format(datacenter_name)
            )
            return None

    def get_vm(self, client, name):
        """
        Returns the identifier of a VM
        Note: The method assumes only one VM with the mentioned name.
        """
        filter_spec = VM.FilterSpec(names=set([name]))
        vm_summaries = client.vcenter.VM.list(filter_spec)
        if len(vm_summaries) > 0:
            vm = vm_summaries[0].vm
            return vm
        else:
            return None

    def create(self, runner: Runner) -> Runner:
        client = self._create_client()
        library_id = self.get_library_id(client, self.instance_config.library)
        library_item_id = self.get_library_item_id(
            client, self.instance_config.library_item, library_id
        )
        resource_pool_id = self.get_resource_pool(
            client, self.instance_config.datacenter
        )
        deployment_target = LibraryItem.DeploymentTarget(
            resource_pool_id=resource_pool_id,
        )
        ovf = client.vcenter.ovf.LibraryItem.filter(
            library_item_id,
            deployment_target,
        )
        user_data = b64encode(self.instance_config.template_startup(runner).encode())
        params = PropertyParams(
            properties=[
                Property(id="user-data", value=user_data.decode()),
                Property(id="hostname", value=runner.name),
                Property(id="instance-id", value=runner.name),
            ],
            type="PropertyParams",
        )
        ip_allocation = IpAllocationParams(
            supported_allocation_scheme=[],
            supported_ip_allocation_policy=["STATIC_MANUAL"],
            supported_ip_protocol=["IPv4"],
            ip_allocation_policy="STATIC_MANUAL",
            type="IpAllocationParams",
        )
        size_param = SizeParams(
            type="SizeParams",
            variable_disk_size=False,
            approximate_sparse_deployment_size=0,
            approximate_download_size=-1,
        )
        deployment_spec = LibraryItem.ResourcePoolDeploymentSpec(
            name=runner.name,
            annotation=ovf.annotation,
            accept_all_eula=True,
            network_mappings=None,
            storage_mappings=None,
            storage_provisioning=None,
            storage_profile_id=None,
            locale=None,
            flags=None,
            additional_parameters=[params, size_param, ip_allocation],
            default_datastore_id=None,
        )
        deploy = client.vcenter.ovf.LibraryItem.deploy(
            library_item_id,
            deployment_target,
            deployment_spec,
        )

        log.debug(deploy)
        if deploy.succeeded:
            log.info("Deployment of library item succeeded")
        runner.instance_id = deploy.resource_id.id
        vm = self.get_vm(client, runner.name)
        cpu_spec = Cpu.UpdateSpec(count=self.instance_config.cpu)
        memory = self.instance_config.memory_gb * 1024
        memory_spec = Memory.UpdateSpec(size_mib=memory)

        log.debug("Updating CPU of VM")
        client.vcenter.vm.hardware.Cpu.update(vm, cpu_spec)
        log.debug("Updating memory of VM")
        client.vcenter.vm.hardware.Memory.update(vm, memory_spec)
        client.vcenter.vm.Power.start(vm)
        return super().create(runner)

    def delete(self, runner: Runner):
        client = self._create_client()
        vm = self.get_vm(client, runner.name)
        if vm:
            state = client.vcenter.vm.Power.get(vm)
            if state == Power.Info(state=Power.State.POWERED_ON):
                client.vcenter.vm.Power.stop(vm)
            elif state == Power.Info(state=Power.State.SUSPENDED):
                client.vcenter.vm.Power.start(vm)
                client.vcenter.vm.Power.stop(vm)
            log.info(f"Deleting {vm}...")
            client.vcenter.VM.delete(vm)
        return super().delete(runner)
