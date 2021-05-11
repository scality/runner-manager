import os
import time
import datetime
import keystoneauth1.session
import keystoneclient.auth.identity.v3
import neutronclient.v2_0.client
from novaclient import client
from pprint import PrettyPrinter

from github_actions_api import link_download_runner

pprinter = PrettyPrinter()

keystone_endpoint = 'https://scality.cloud/keystone/v3'
token = os.getenv("CLOUD_9_TOKEN")
tenant_id = '8a8b4361989f4819b271797eebdc16fc'

region = 'Europe'
session = keystoneauth1.session.Session(
    auth=keystoneclient.auth.identity.v3.Token(
        auth_url=keystone_endpoint,
        token=token,
        project_id=tenant_id)
)
nova_client = client.Client(version=2, session=session, region_name=region)
neutron = neutronclient.v2_0.client.Client(session=session, region_name=region)


def script_init_runner(name, token, labels, group):
    installer = link_download_runner('scalanga-devl')
    return f"""#!/bin/bash
sudo yum install -y bind-utils yum-utils

sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y epel-release
sudo yum install -y docker-ce docker-ce-cli containerd.io
sudo systemctl start docker
sudo usermod -aG docker centos
sudo -H -u centos bash -c 'cd /home/centos/ && mkdir actions-runner && cd actions-runner && curl -O -L {installer['download_url']} && tar xzf ./{installer['filename']}'
/home/centos/actions-runner/bin/installdependencies.sh
sudo -H -u centos bash -c '/home/centos/actions-runner/config.sh --url https://github.com/scalanga-devl --token {token} --name {name} --work _work  --labels {','.join(labels)} --runnergroup {group}'
nohup sudo -H -u centos bash -c '/home/centos/actions-runner/run.sh --once 2> /home/centos/actions-runner/logs'
"""


def create_vm(name, runner_token):
    """
    Create a small vm base on  CentOS-7-x86_64-GenericCloud-latest , with my sshkey
    :param name:
    :param runner_token:
    :return:
    """
    sec_group_id = neutron.list_security_groups()['security_groups'][0]['id']
    nic = {'net-id': neutron.list_networks(name='tenantnetwork1')['networks'][0]['id']}
    print("creating virtual machine")
    print("----------------------------")
    # print(script_init_runner(name, runner_token, ['centos'], 'default'))
    # print("----------------------------")
    instance = nova_client.servers.create(
        name=name, image='dcfbc223-d658-4077-a517-5f29984258a6',
        flavor=nova_client.flavors.find(name='m1.small'), key_name='laptot',
        security_groups=[sec_group_id], nics=[nic],
        userdata=script_init_runner(name, runner_token, ['centos'], 'default'))
    print(instance.name, instance.id)
    inst_status = instance.status
    print(inst_status)
    print("instances are in build state... ")

    while inst_status != 'ACTIVE':
        instance = nova_client.servers.get(instance.id)
        inst_status = instance.status
        time.sleep(0.5)

    print(f"Instance: {instance.name} is in {inst_status} state ")
    print("vms were successfully created at {} \n".format(datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")))

    return instance.id


def delete_vm(id):
    nova_client.servers.delete(id)


if __name__ == "__main__":
    create_vm('test-script', '')
