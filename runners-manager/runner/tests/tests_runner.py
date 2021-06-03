import unittest
from mock import patch, Mock

from runner.RunnerManager import RunnerManager
from runner.Runner import Runner


class TestSum(unittest.TestCase):

    def test_initialisation_runner_manager(self):
        pass

    @patch('runner.RunnerManager.create_runner_token')
    @patch('runner.RunnerManager.create_vm')
    @patch('runner.RunnerManager.RunnerManager.delete_runner')
    def test_no_config(self, delete_runner: Mock, create_vm: Mock, c_r_token: Mock):
        r = RunnerManager('test', [])
        self.assertEqual(r.runner_counter, 0)
        self.assertEqual(r.github_organization, 'test')
        self.assertEqual(r.runner_management, [])
        self.assertEqual(r.runners, {})

        c_r_token.assert_not_called()
        create_vm.assert_not_called()

    @patch('runner.RunnerManager.create_runner_token', return_value='c')
    @patch('runner.RunnerManager.create_vm', return_value='1')
    @patch('runner.RunnerManager.RunnerManager.delete_runner')
    def test_config_vm_type(self, delete_runner: Mock, create_vm: Mock, create_runner_token: Mock):
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

    @patch('runner.RunnerManager.create_runner_token', return_value='c')
    @patch('runner.RunnerManager.create_vm', return_value='1')
    @patch('runner.RunnerManager.force_delete_runner')
    @patch('runner.RunnerManager.delete_vm')
    def test_update_runner(self, delete_vm: Mock,
                           force_delete_runner: Mock,
                           create_vm: Mock,
                           create_runner_token: Mock):
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
