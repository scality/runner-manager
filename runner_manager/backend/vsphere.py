import logging
from typing import Literal

from com.vmware.vcenter.vm.hardware.boot_client import Device as BootDevice
from com.vmware.vcenter.vm_client import (Hardware, Power)
from com.vmware.vcenter.vm.hardware_client import (
    Cpu,
    Disk,
    Ethernet,
    Memory,
    ScsiAddressSpec,
    Cdrom,
    Boot,
)
from com.vmware.vcenter_client import (
    VM,
    Datacenter,
    Datastore,
    Folder,
    Network,
    ResourcePool,
)
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

    def _create_client(self):
        session = Session()
        session.verify = self.config.verify_ssl
        return create_vsphere_client(
            server=self.config.server,
            username=self.config.username,
            password=self.config.password,
            session=session,
        )

    def get_folder(self, client, datacenter_name, folder_name):
        """
        Returns the identifier of a folder
        Note: The method assumes that there is only one folder and datacenter
        with the mentioned names.
        """
        datacenter = self.get_datacenter(client, datacenter_name)
        if not datacenter:
            print("Datacenter '{}' not found".format(datacenter_name))
            return None

        filter_spec = Folder.FilterSpec(
            type=Folder.Type.VIRTUAL_MACHINE,
            names=set([folder_name]),
            datacenters=set([datacenter]),
        )

        folder_summaries = client.vcenter.Folder.list(filter_spec)
        if len(folder_summaries) > 0:
            folder = folder_summaries[0].folder
            print("Detected folder '{}' as {}".format(folder_name, folder))
            return folder
        else:
            print("Folder '{}' not found".format(folder_name))
            return None

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
            print("Datacenter '{}' not found".format(datacenter_name))
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
            print("Datacenter '{}' not found".format(datacenter_name))
            return None

        names = set([resource_pool_name]) if resource_pool_name else None
        filter_spec = ResourcePool.FilterSpec(
            datacenters=set([datacenter]), names=names
        )

        resource_pool_summaries = client.vcenter.ResourcePool.list(filter_spec)
        if len(resource_pool_summaries) > 0:
            resource_pool = resource_pool_summaries[0].resource_pool
            print("Selecting ResourcePool '{}'".format(resource_pool))
            return resource_pool
        else:
            print("ResourcePool not found in Datacenter '{}'".format(datacenter_name))
            return None

    def placement_spec(self, client):
        """
        Returns a VM placement spec for a resourcepool. Ensures that the
        vm folder and datastore are all in the same datacenter which is specified.
        """
        resource_pool = self.get_resource_pool(client, self.instance_config.datacenter)

        folder = self.get_folder(
            client, self.instance_config.datacenter, self.instance_config.folder
        )

        datastore = self.get_datastore(
            client, self.instance_config.datacenter, self.instance_config.datastore
        )

        # Create the vm placement spec with the datastore, resource pool and vm
        # folder
        placement_spec = VM.PlacementSpec(
            folder=folder, resource_pool=resource_pool, datastore=datastore
        )

        print(
            "get_placement_spec_for_resource_pool: Result is '{}'".format(
                placement_spec
            )
        )
        return placement_spec

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

    def get_boot_disk(self, client, vm):
        """Find the backing type disks that was used as the image for the VM."""

        client = self._create_client()
        disks = client.vcenter.vm.hardware.Disk.list(vm)
        for disk in disks:
            disk_info = client.vcenter.vm.hardware.Disk.get(vm, disk.disk)
            if disk_info.backing.vmdk_file == self.instance_config.vmdk_file:
                return disk.disk
        return None

    def get_network_backing(self, client, portgroup_name, datacenter_name, portgroup_type):
        """
        Gets a standard portgroup network backing for a given Datacenter
        Note: The method assumes that there is only one standard portgroup
        and datacenter with the mentioned names.
        """
        datacenter = self.get_datacenter(client, datacenter_name)
        if not datacenter:
            print("Datacenter '{}' not found".format(datacenter_name))
            return None

        filter = Network.FilterSpec(
            datacenters=set([datacenter]),
            names=set([portgroup_name]),
            types=set([portgroup_type]),
        )
        network_summaries = client.vcenter.Network.list(filter=filter)

        if len(network_summaries) > 0:
            network = network_summaries[0].network
            print(
                "Selecting {} Portgroup Network '{}' ({})".format(
                    portgroup_type, portgroup_name, network
                )
            )
            return network
        else:
            print(
                "Portgroup Network not found in Datacenter '{}'".format(datacenter_name)
            )
            return None

    def create(self, runner: Runner) -> Runner:
        client: VsphereClient = self._create_client()
        placement_spec = self.placement_spec(client)
        GiB = 1024 * 1024 * 1024
        standard_network = self.get_network_backing(
            client,
            self.instance_config.portgroup,
            self.instance_config.datacenter,
            Network.Type.STANDARD_PORTGROUP,
        )
        nic = Ethernet.CreateSpec(
            start_connected=True,
            backing=Ethernet.BackingSpec(
                type=Ethernet.BackingType.STANDARD_PORTGROUP, network=standard_network
            ),
        )
        boot_device_order = [
            BootDevice.EntryCreateSpec(BootDevice.Type.DISK),
            BootDevice.EntryCreateSpec(BootDevice.Type.ETHERNET),
        ]
        log.info("Creating vm specs...")
        vm_create_spec = VM.CreateSpec(
            guest_os=self.instance_config.guest_os,
            name=runner.name,
            placement=placement_spec,
            cpu=Cpu.UpdateSpec(count=self.instance_config.cpu),
            memory=Memory.UpdateSpec(size_mib=self.instance_config.memory),
            disks=[
                Disk.CreateSpec(
                    backing=Disk.BackingSpec(
                        type=Disk.BackingType.VMDK_FILE,
                        vmdk_file=self.instance_config.vmdk_file
                    ),
                ),
                Disk.CreateSpec(
                    type=Disk.HostBusAdapterType.SCSI,
                    scsi=ScsiAddressSpec(bus=0, unit=0),
                    new_vmdk=Disk.VmdkCreateSpec(
                        name="boot", capacity=self.instance_config.disk_size_gb * GiB
                    ),
                ),
            ],
            nics=[nic],
            boot=Boot.CreateSpec(
                type=Boot.Type.BIOS,
                delay=0,
                enter_setup_mode=False
            ),
            boot_devices=boot_device_order,

        )
        log.info("Creating vm...")
        vm = client.vcenter.VM.create(vm_create_spec)
        vm_info = client.vcenter.VM.get(vm)
        runner.instance_id = vm_info.name

        log.info("Powering on vm...")
        client.vcenter.vm.Power.start(vm)

        return super().create(runner)

    def delete(self, runner: Runner):
        client = self._create_client()
        vm = self.get_vm(client, runner.instance_id)
        if vm:
            state = client.vcenter.vm.Power.get(vm)
            if state == Power.Info(state=Power.State.POWERED_ON):
                client.vcenter.vm.Power.stop(vm)
            elif state == Power.Info(state=Power.State.SUSPENDED):
                client.vcenter.vm.Power.start(vm)
                client.vcenter.vm.Power.stop(vm)
            boot_disk = self.get_boot_disk(client, vm)
            log.info(f"Delete boot disk {boot_disk}...")
            client.vcenter.vm.hardware.Disk.delete(vm, boot_disk)
            log.info(f"Deleting {vm}...")
            client.vcenter.VM.delete(vm)
        return super().delete(runner)