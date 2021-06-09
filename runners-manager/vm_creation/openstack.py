import os
import datetime
import keystoneauth1.session
import keystoneclient.auth.identity.v3
import neutronclient.v2_0.client
from novaclient import client
from jinja2 import FileSystemLoader, Environment
from pprint import PrettyPrinter

from vm_creation.github_actions_api import link_download_runner
from runner.VmType import VmType

pprinter = PrettyPrinter()

keystone_endpoint = 'https://scality.cloud/keystone/v3'
token = os.getenv("CLOUD_NINE_TOKEN")
tenant_id = os.getenv("CLOUD_NINE_TENANT")
github_organization = os.getenv('GITHUB_ORGANIZATION')

region = 'Europe'
session = keystoneauth1.session.Session(
    auth=keystoneclient.auth.identity.v3.Token(
        auth_url=keystone_endpoint,
        token=token,
        project_id=tenant_id)
)
nova_client = client.Client(version=2, session=session, region_name=region)
neutron = neutronclient.v2_0.client.Client(session=session, region_name=region)


def script_init_runner(name: str, token: int, vm_type: VmType, group: str):
    installer = link_download_runner(github_organization)
    file_loader = FileSystemLoader('templates')
    env = Environment(loader=file_loader)
    env.trim_blocks = True
    env.lstrip_blocks = True
    env.rstrip_blocks = True
    template = env.get_template('init_runner_script.sh')
    output = template.render(image=vm_type.image.lower(), installer=installer,
                             github_organization=github_organization,
                             token=token, name=name, tags=','.join(vm_type.tags))
    return output


def create_vm(name: str, runner_token: int, vm_type: VmType):
    """
    Create a small vm base on  CentOS-7-x86_64-GenericCloud-latest , with my sshkey
    """
    sec_group_id = neutron.list_security_groups()['security_groups'][0]['id']
    nic = {'net-id': neutron.list_networks(name='tenantnetwork1')['networks'][0]['id']}
    print("creating virtual machine")
    print("----------------------------")
    # print(script_init_runner(name, runner_token, ['centos'], 'default'))
    # print("----------------------------")
    instance = nova_client.servers.create(
        name=name, image=nova_client.glance.find_image(vm_type.image),
        flavor=nova_client.flavors.find(name=vm_type.flavor), key_name='laptot',
        security_groups=[sec_group_id], nics=[nic],
        userdata=script_init_runner(name, runner_token, vm_type, 'default'))
    print(instance.name, instance.id)
    inst_status = instance.status

    print(f"Instance: {instance.name} is in {inst_status} state ")
    print(
        f"vms were successfully created at {datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')}"
    )

    return instance.id


def delete_vm(id):
    nova_client.servers.delete(id)
