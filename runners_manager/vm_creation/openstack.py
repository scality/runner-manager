import os
import logging
import keystoneauth1.session
import keystoneclient.auth.identity.v3
import neutronclient.v2_0.client
from novaclient import client
from jinja2 import FileSystemLoader, Environment

from vm_creation.github_actions_api import link_download_runner
from runner.VmType import VmType

logger = logging.getLogger("runner_manager")

keystone_endpoint = 'https://scality.cloud/keystone/v3'
token = os.getenv("CLOUD_NINE_TOKEN")
tenant_id = os.getenv("CLOUD_NINE_TENANT")
username = os.getenv("CLOUD_NINE_USERNAME")
password = os.getenv("CLOUD_NINE_PASSWORD")
region = os.getenv('CLOUD_NINE_REGION')

github_organization = os.getenv('GITHUB_ORGANIZATION')
if username and password:
    logger.info("Openstack auth with basic credentials")
    session = keystoneauth1.session.Session(
        auth=keystoneclient.auth.identity.v3.Password(
            auth_url=keystone_endpoint,
            username=username,
            password=password,
            user_domain_name='default',
            project_name=tenant_id,
            project_domain_id='default')
    )
else:
    logger.info("Openstack auth with token")
    session = keystoneauth1.session.Session(
        auth=keystoneclient.auth.identity.v3.Token(
            auth_url=keystone_endpoint,
            token=token,
            project_name=tenant_id,
            project_domain_id='default')
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
    Create a new VM with the parameters in VmType
    """
    sec_group_id = neutron.list_security_groups()['security_groups'][0]['id']
    nic = {'net-id': neutron.list_networks(name='tenantnetwork1')['networks'][0]['id']}
    logger.info("creating virtual machine")
    instance = nova_client.servers.create(
        name=name, image=nova_client.glance.find_image(vm_type.image),
        flavor=nova_client.flavors.find(name=vm_type.flavor),
        security_groups=[sec_group_id], nics=[nic],
        userdata=script_init_runner(name, runner_token, vm_type, 'default'))
    logger.debug(f"{instance.name}, {instance.id}")
    logger.info("vm is successfully created}")

    return instance.id


def delete_vm(id):
    nova_client.servers.delete(id)
