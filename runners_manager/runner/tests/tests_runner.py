import unittest
from unittest.mock import patch, Mock

from runners_manager.runner.RunnerManager import RunnerManager
from runners_manager.runner.Runner import Runner
from runners_manager.runner.VmType import VmType


class TestSum(unittest.TestCase):

    def test_initialisation_runner_manager(self):
        pass

    @patch('runners_manager.runner.RunnerManager.create_runner_token')
    @patch('runners_manager.runner.RunnerManager.create_vm')
    @patch('runners_manager.runner.RunnerManager.RunnerManager.delete_runner')
    def test_no_config(self, delete_runner: Mock, create_vm: Mock, c_r_token: Mock):
        r = RunnerManager('test', [])
        self.assertEqual(r.runner_counter, 0)
        self.assertEqual(r.github_organization, 'test')
        self.assertEqual(r.runner_management, [])
        self.assertEqual(r.runners, {})

        c_r_token.assert_not_called()
        create_vm.assert_not_called()

    @patch('runners_manager.runner.RunnerManager.create_runner_token')
    @patch('runners_manager.runner.RunnerManager.create_vm')
    @patch('runners_manager.runner.RunnerManager.RunnerManager.delete_runner')
    def test_runner_naming_generator(self, delete_runner: Mock, create_vm: Mock, c_r_token: Mock):
        vm_type_centos = VmType({'tags': ['small_tag', 'centos_tag'], 'flavor': 'small',
                                 'image': 'centos', 'quantity': 1})
        vm_type_ubuntu = VmType({'tags': ['medium_tag', 'ubuntu_tag'], 'flavor': 'medium',
                                 'image': 'ubuntu', 'quantity': 1})
        r = RunnerManager('test', [])
        r.runner_counter = 1
        g = r.generate_runner_name(vm_type_centos)
        self.assertEqual(g, 'runner-test-centos_tag-small_tag-1')

        r.runner_counter += 1
        g = r.generate_runner_name(vm_type_ubuntu)
        self.assertEqual(g, 'runner-test-medium_tag-ubuntu_tag-2')

    @patch('runners_manager.runner.RunnerManager.create_runner_token', return_value='c')
    @patch('runners_manager.runner.RunnerManager.create_vm', return_value='1')
    @patch('runners_manager.runner.RunnerManager.RunnerManager.delete_runner')
    @patch('runners_manager.runner.RunnerManager.RunnerManager.generate_runner_name')
    def test_config_vm_type(self, name_generator: Mock,
                            delete_runner: Mock,
                            create_vm: Mock, create_runner_token: Mock):
        name_generator.side_effect = ['0', '1', '2', '3']
        r = RunnerManager('test', [{
            'tags': ['centos7', 'small'],
            'flavor': 'm1.small',
            'image': 'CentOS 7 (PVHVM)',
            'quantity': {
                'min': 2,
                'max': 4
            },
        }])
        self.assertEqual(r.github_organization, 'test')

        self.assertEqual(r.runner_management.__len__(), 1)

        self.assertEqual(r.runners.__len__(), 2)
        self.assertEqual(r.runners['0'], Runner('0', '1', r.runner_management[0]))
        self.assertEqual(r.runners['1'], Runner('1', '1', r.runner_management[0]))
        self.assertEqual(r.runner_counter, 2)

        create_runner_token.assert_called()
        create_vm.assert_called()

    @patch('runners_manager.runner.RunnerManager.create_runner_token', return_value='c')
    @patch('runners_manager.runner.RunnerManager.create_vm', return_value='1')
    @patch('runners_manager.runner.RunnerManager.force_delete_runner')
    @patch('runners_manager.runner.RunnerManager.delete_vm')
    @patch('runners_manager.runner.RunnerManager.RunnerManager.generate_runner_name')
    def test_update_runner(self, name_generator: Mock,
                           delete_vm: Mock,
                           force_delete_runner: Mock,
                           create_vm: Mock,
                           create_runner_token: Mock):
        name_generator.side_effect = ['0', '1', '2']
        r = RunnerManager('test', [{
            'tags': ['centos7', 'small'],
            'flavor': 'm1.small',
            'image': 'CentOS 7 (PVHVM)',
            'quantity': {
                'min': 2,
                'max': 4
            },
        }])
        self.assertEqual(r.runner_counter, 2)
        self.assertEqual(r.github_organization, 'test')
        self.assertEqual(r.runners['0'].action_id, None)
        self.assertEqual(r.runners['0'].has_run, False)
        self.assertEqual(r.runners['0'].status, 'offline')

        force_delete_runner.assert_not_called()
        self.assertEqual(create_vm.call_count, 2)
        self.assertEqual(create_runner_token.call_count, 2)

        create_vm.reset_mock()
        create_runner_token.reset_mock()
        r.update([{
            'name': '0',
            'id': 0,
            'status': 'online',
            'busy': False
        }])
        self.assertEqual(r.runners['0'].action_id, 0)
        self.assertEqual(r.runners['0'].has_run, False)
        self.assertEqual(r.runners['0'].status, 'online')
        self.assertEqual(r.runner_counter, 2)

        create_vm.assert_not_called()
        create_runner_token.assert_not_called()
        force_delete_runner.assert_not_called()

        r.update([{
            'name': '0',
            'id': 0,
            'status': 'offline',
            'busy': False
        }])
        self.assertEqual(r.runners['0'].action_id, 0)
        self.assertEqual(r.runners['0'].has_run, True)
        force_delete_runner.assert_not_called()
        create_vm.assert_called()
        create_runner_token.assert_called()

        create_vm.reset_mock()
        create_runner_token.reset_mock()

        r.update([{
            'name': '1',
            'id': 1,
            'status': 'offline',
            'busy': False
        }])
        force_delete_runner.assert_not_called()
        create_vm.assert_not_called()
        create_runner_token.assert_not_called()

        r.update([{
            'name': '1',
            'id': 1,
            'status': 'online',
            'busy': False
        }])
        force_delete_runner.assert_not_called()
        create_vm.assert_not_called()
        create_runner_token.assert_not_called()
