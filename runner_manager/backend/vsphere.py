
from runner_manager.backend.base import BaseBackend
from runner_manager.models.backend import Backends, VsphereConfig, VsphereInstanceConfig
from runner_manager.models.runner import Runner
from pydantic import Field
from typing import Literal, Optional
from githubkit.webhooks.types import WorkflowJobEvent
from vmware.vapi.vsphere.client import create_vsphere_client, VsphereClient
from com.vmware.vcenter_client import VM, Datacenter, Datastore, ResourcePool, Folder
from com.vmware.vcenter.vm.hardware_client import Cpu, Memory, Boot
from requests import Session

import logging

log = logging.getLogger(__name__)

class VsphereBackend(BaseBackend):
    name: Literal[Backends.vsphere] = Field(default=Backends.vsphere)
    config: VsphereConfig
    instance_config: VsphereInstanceConfig

    @property
    def client(self) -> VsphereClient:
        session = Session()
        session.verify = self.config.verify_ssl
        return create_vsphere_client(
            server=self.config.server,
            username=self.config.username,
            password=self.config.password,
            bearer_token=self.config.bearer_token,
            session=session,
        )

    def get_folder(self, datacenter_name, folder_name):
        """
        Returns the identifier of a folder
        Note: The method assumes that there is only one folder and datacenter
        with the mentioned names.
        """
        datacenter = self.get_datacenter(datacenter_name)
        if not datacenter:
            print("Datacenter '{}' not found".format(datacenter_name))
            return None

        filter_spec = Folder.FilterSpec(type=Folder.Type.VIRTUAL_MACHINE,
                                        names=set([folder_name]),
                                        datacenters=set([datacenter]))

        folder_summaries = self.client.vcenter.Folder.list(filter_spec)
        if len(folder_summaries) > 0:
            folder = folder_summaries[0].folder
            print("Detected folder '{}' as {}".format(folder_name, folder))
            return folder
        else:
            print("Folder '{}' not found".format(folder_name))
            return None

    def get_datacenter(self, datacenter_name):
        """
        Returns the identifier of a datacenter
        Note: The method assumes only one datacenter with the mentioned name.
        """

        filter_spec = Datacenter.FilterSpec(names=set([datacenter_name]))

        datacenter_summaries = self.client.vcenter.Datacenter.list(filter_spec)
        if len(datacenter_summaries) > 0:
            datacenter = datacenter_summaries[0].datacenter
            return datacenter
        else:
            return None

    def get_datastore(self, datacenter_name, datastore_name):
        """
        Returns the identifier of a datastore
        Note: The method assumes that there is only one datastore and datacenter
        with the mentioned names.
        """
        datacenter = self.get_datacenter(datacenter_name)
        if not datacenter:
            print("Datacenter '{}' not found".format(datacenter_name))
            return None

        filter_spec = Datastore.FilterSpec(names=set([datastore_name]),
                                        datacenters=set([datacenter]))

        datastore_summaries = self.client.vcenter.Datastore.list(filter_spec)
        if len(datastore_summaries) > 0:
            datastore = datastore_summaries[0].datastore
            return datastore
        else:
            return None

    def get_resource_pool(self, datacenter_name, resource_pool_name=None):
        """
        Returns the identifier of the resource pool with the given name or the
        first resource pool in the datacenter if the name is not provided.
        """
        datacenter = self.get_datacenter(datacenter_name)
        if not datacenter:
            print("Datacenter '{}' not found".format(datacenter_name))
            return None

        names = set([resource_pool_name]) if resource_pool_name else None
        filter_spec = ResourcePool.FilterSpec(datacenters=set([datacenter]),
                                            names=names)

        resource_pool_summaries = self.client.vcenter.ResourcePool.list(filter_spec)
        if len(resource_pool_summaries) > 0:
            resource_pool = resource_pool_summaries[0].resource_pool
            print("Selecting ResourcePool '{}'".format(resource_pool))
            return resource_pool
        else:
            print("ResourcePool not found in Datacenter '{}'".
                format(datacenter_name))
            return None

    def placement_spec(self):
        """
        Returns a VM placement spec for a resourcepool. Ensures that the
        vm folder and datastore are all in the same datacenter which is specified.
        """
        resource_pool = self.get_resource_pool(self.instance_config.datacenter)

        folder = self.get_folder(
            self.instance_config.datacenter,
            self.instance_config.folder
        )

        datastore = self.get_datastore(self.instance_config.datacenter, self.instance_config.datastore)

        # Create the vm placement spec with the datastore, resource pool and vm
        # folder
        placement_spec = VM.PlacementSpec(folder=folder,
                                        resource_pool=resource_pool,
                                        datastore=datastore)

        print("get_placement_spec_for_resource_pool: Result is '{}'".
            format(placement_spec))
        return placement_spec


    def get_vm(self, name):
        """
        Returns the identifier of a VM
        Note: The method assumes only one VM with the mentioned name.
        """
        filter_spec = VM.FilterSpec(names=set([name]))
        vm_summaries = self.client.vcenter.VM.list(filter_spec)
        if len(vm_summaries) > 0:
            vm = vm_summaries[0].vm
            return vm
        else:
            return None

    def create(self, runner: Runner) -> Runner:
        placement_spec = self.placement_spec()
        vm_create_spec = VM.CreateSpec(
            guest_os=self.instance_config.guest_os,
            name=runner.name,
            placement=placement_spec,
            cpu=Cpu.UpdateSpec(count=self.instance_config.cpu),
            memory=Memory.UpdateSpec(size_mib=self.instance_config.memory),
            boot=Boot.CreateSpec(
        )
        vm = self.client.vcenter.VM.create(vm_create_spec)
        vm_info = self.client.vcenter.VM.get(vm)
        runner.instance_id = vm_info.vm

        return super().create(runner)

    def delete(self, runner: Runner):
        vm = self.get_vm(runner.instance_id)
        if vm:
            self.client.vcenter.VM.delete(vm)
        return super().delete(runner)
