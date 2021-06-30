import logging
import keystoneauth1.session
import keystoneclient.auth.identity.v3
import neutronclient.v2_0.client
from novaclient import client
from jinja2 import FileSystemLoader, Environment

from runners_manager.runner.VmType import VmType

logger = logging.getLogger("runner_manager")

keystone_endpoint = 'https://scality.cloud/keystone/v3'


class OpenstackManager(object):
    nova_client: client.Client
    neutron: neutronclient.v2_0.client.Client

    def __init__(self, project_name, token, username, password, region):
        if username and password:
            logger.info("Openstack auth with basic credentials")
            session = keystoneauth1.session.Session(
                auth=keystoneclient.auth.identity.v3.Password(
                    auth_url=keystone_endpoint,
                    username=username,
                    password=password,
                    user_domain_name='default',
                    project_name=project_name,
                    project_domain_id='default')
            )
        else:
            logger.info("Openstack auth with token")
            session = keystoneauth1.session.Session(
                auth=keystoneclient.auth.identity.v3.Token(
                    auth_url=keystone_endpoint,
                    token=token,
                    project_name=project_name,
                    project_domain_id='default')
            )

        self.nova_client = client.Client(version=2, session=session, region_name=region)
        self.neutron = neutronclient.v2_0.client.Client(session=session, region_name=region)

    def script_init_runner(self, name: str, token: int, vm_type: VmType,
                           github_organization: str, installer: str):
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

    def create_vm(self, name: str, runner_token: int, vm_type: VmType,
                  github_organization: str, installer: str):
        """
        Create a new VM with the parameters in VmType
        """
        sec_group_id = self.neutron.list_security_groups()['security_groups'][0]['id']
        nic = {'net-id': self.neutron.list_networks(name='tenantnetwork1')['networks'][0]['id']}
        logger.info("creating virtual machine")
        instance = self.nova_client.servers.create(
            name=name, image=self.nova_client.glance.find_image(vm_type.image),
            flavor=self.nova_client.flavors.find(name=vm_type.flavor),
            security_groups=[sec_group_id], nics=[nic],
            userdata=self.script_init_runner(name, runner_token, vm_type,
                                             github_organization, installer))
        logger.debug(f"{instance.name}, {instance.id}")
        logger.info("vm is successfully created}")

        return instance.id

    def delete_vm(self, id):
        self.nova_client.servers.delete(id)
