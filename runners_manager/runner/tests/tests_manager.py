import unittest
from unittest.mock import patch, Mock, MagicMock

from runners_manager.runner.Manager import Manager
from runners_manager.runner.VmType import VmType


class ObjectId(object):
    def __init__(self, id):
        self.id = id


class TestRunnerManager(unittest.TestCase):
    @patch('runners_manager.vm_creation.github_actions_api.GithubManager')
    @patch('runners_manager.vm_creation.openstack.OpenstackManager')
    def setUp(self, return_github_manager, return_openstack_manager) -> None:
        self.github_manager = MagicMock()
        self.github_manager.link_download_runner.return_value = 'fake_link'
        self.github_manager.create_runner_token.return_value = ''
        self.github_manager.get_runners.return_value = []
        self.github_manager.force_delete_runner.return_value = None

        self.openstack_manager = MagicMock()
        self.openstack_manager.script_init_runner.return_value = ''
        self.openstack_manager.create_vm.return_value = ObjectId('str')
        self.openstack_manager.delete_vm.return_value = None

        return_github_manager.return_value = self.github_manager
        return_openstack_manager.return_value = self.openstack_manager

    @patch('runners_manager.runner.Manager.RunnerFactory.create_runner')
    @patch('runners_manager.runner.Manager.RunnerFactory.delete_runner')
    def test_no_config(self, delete_runner: Mock, create_vm: Mock):
        r = Manager({
            'github_organization': 'test', 'runner_pool': [],
            'extra_runner_timer': {
                'minutes': 10,
                'hours': 10
            }}, self.openstack_manager, self.github_manager)
        self.assertEqual(r.factory.runner_counter, 0)
        self.assertEqual(r.runner_managers, [])

        create_vm.assert_not_called()

    @patch('runners_manager.runner.Manager.RunnerFactory.create_runner')
    @patch('runners_manager.runner.Manager.RunnerFactory.delete_runner')
    def test_runner_naming_generator(self, delete_runner: Mock, create_vm: Mock):
        vm_type_centos = VmType({'tags': ['small_tag', 'centos_tag'], 'flavor': 'small',
                                 'image': 'centos', 'quantity': 1})
        vm_type_ubuntu = VmType({'tags': ['medium_tag', 'ubuntu_tag'], 'flavor': 'medium',
                                 'image': 'ubuntu', 'quantity': 1})
        r = Manager({
            'github_organization': 'test', 'runner_pool': [],
            'extra_runner_timer': {
                'minutes': 10,
                'hours': 10
            }
        }, self.openstack_manager, self.github_manager)
        r.factory.runner_counter = 1
        g = r.factory.generate_runner_name(vm_type_centos)
        self.assertEqual(g, 'runner-test-centos_tag-small_tag-1')

        r.factory.runner_counter += 1
        g = r.factory.generate_runner_name(vm_type_ubuntu)
        self.assertEqual(g, 'runner-test-medium_tag-ubuntu_tag-2')

    @patch('runners_manager.runner.Manager.RunnerFactory.delete_runner')
    @patch('runners_manager.runner.Manager.RunnerFactory.generate_runner_name')
    def test_config_vm_type(self, name_generator: Mock,
                            delete_runner: Mock):
        name_generator.side_effect = ['0', '1', '2', '3']
        self.openstack_manager.create_vm.side_effect = [ObjectId('1'), ObjectId('2'), ObjectId('3')]
        r = Manager({'github_organization': 'test',
                           'runner_pool': [{
                               'tags': ['centos7', 'small'],
                               'flavor': 'm1.small',
                               'image': 'CentOS 7 (PVHVM)',
                               'quantity': {
                                   'min': 2,
                                   'max': 4
                               },
                           }],
                           'extra_runner_timer': {
                               'minutes': 10,
                               'hours': 10
                           }}, self.openstack_manager, self.github_manager)
        self.assertEqual(r.runner_managers.__len__(), 1)
