import unittest
import fakeredis
from unittest.mock import patch, MagicMock

from runners_manager.runner.Runner import Runner
from runners_manager.runner.RunnerManager import RunnerManager
from runners_manager.runner.VmType import VmType


class ObjectId(object):
    def __init__(self, id):
        self.id = id


class TestRunnerManager(unittest.TestCase):
    factory: MagicMock

    @patch('runners_manager.vm_creation.github_actions_api.GithubManager')
    @patch('runners_manager.vm_creation.openstack.OpenstackManager')
    def setUp(self, return_github_manager, return_openstack_manager) -> None:
        self.fake_redis = fakeredis.FakeStrictRedis()
        self.factory = MagicMock()
        self.vm_type_normal = VmType({
            'tags': ['centos7', 'small'],
            'flavor': 'm1.small',
            'image': 'CentOS 7 (PVHVM)',
            'quantity': {
                'min': 2,
                'max': 4
            }})

        self.vm_type_full = VmType({
            'tags': ['centos7', 'small'],
            'flavor': 'm1.small',
            'image': 'CentOS 7 (PVHVM)',
            'quantity': {
                'min': 4,
                'max': 4
            }})

    def test_init_runner_manager(self):
        self.factory.create_runner.side_effect = [
            Runner('0', None, self.vm_type_normal),
            Runner('1', None, self.vm_type_normal)
        ]
        r = RunnerManager(self.vm_type_normal, self.factory, self.fake_redis)

        self.assertEqual(self.factory.create_runner.call_count, 0)
        self.assertEqual(r.runners.__len__(), 0)
        self.assertEqual(r.need_new_runner(), True)

    def test_update_runner(self):
        self.factory.create_runner.side_effect = [
            Runner('0', None, self.vm_type_normal),
            Runner('1', None, self.vm_type_normal),
            Runner('2', None, self.vm_type_normal)
        ]
        r = RunnerManager(self.vm_type_normal, self.factory, self.fake_redis)
        r.create_runner()
        r.create_runner()
        self.factory.create_runner.reset_mock()
        self.factory.delete_runner.reset_mock()
        self.factory.respawn_runner.reset_mock()

        r.update([{
            'name': '0',
            'id': 0,
            'status': 'online',
            'busy': False
        }])
        self.assertEqual(r.runners.__len__(), 2)
        self.assertEqual(r.runners['0'].action_id, 0)
        self.assertEqual(r.runners['0'].has_run, False)
        self.assertEqual(r.runners['0'].status, 'online')
        self.factory.create_runner.assert_not_called()
        self.factory.delete_runner.assert_not_called()
        self.factory.respawn_runner.assert_not_called()

        r.update([{
            'name': '0',
            'id': 0,
            'status': 'offline',
            'busy': False
        }])
        self.assertEqual(r.runners['0'].action_id, 0)
        self.assertEqual(r.runners['0'].has_run, True)
        self.factory.create_runner.assert_not_called()
        self.factory.delete_runner.assert_not_called()
        self.factory.respawn_runner.assert_not_called()

        r.update([{
            'name': '1',
            'id': 1,
            'status': 'offline',
            'busy': False
        }])

        self.factory.create_runner.assert_not_called()
        self.factory.delete_runner.assert_not_called()
        self.factory.respawn_runner.assert_not_called()

        r.update([{
            'name': '1',
            'id': 1,
            'status': 'online',
            'busy': False
        }])
        self.factory.create_runner.assert_not_called()
        self.factory.delete_runner.assert_not_called()
        self.factory.respawn_runner.assert_not_called()

    def test_need_new_runner_current_updated(self):
        self.factory.create_runner.side_effect = [
            Runner('0', None, self.vm_type_normal),
            Runner('1', None, self.vm_type_normal),
            Runner('2', None, self.vm_type_normal)
        ]
        r = RunnerManager(self.vm_type_normal, self.factory, self.fake_redis)
        r.create_runner()
        r.create_runner()

        self.assertEqual(r.need_new_runner(), False)

        r.runners['0'].status_history = ['online']
        r.runners['0'].status = 'running'
        self.assertEqual(r.need_new_runner(), True)

        r.runners['0'].status_history = ['online', 'running']
        r.runners['0'].status = 'offline'
        self.assertEqual(r.need_new_runner(), True)

        r.runners['0'].status_history = ['online', 'running']
        r.runners['0'].status = 'offline'
        self.assertEqual(r.need_new_runner(), True)

        r.runners['0'].status_history = ['online']
        r.runners['0'].status = 'running'
        r.runners['1'].status_history = ['online']
        r.runners['1'].status = 'running'
        self.assertEqual(r.need_new_runner(), True)

    def test_need_new_runner_current_full(self):
        self.factory.create_runner.side_effect = [
            Runner('0', None, self.vm_type_full),
            Runner('1', None, self.vm_type_full),
            Runner('2', None, self.vm_type_full),
            Runner('3', None, self.vm_type_full)
        ]
        r = RunnerManager(self.vm_type_full, self.factory, self.fake_redis)
        r.create_runner()
        r.create_runner()
        r.create_runner()
        r.create_runner()
        self.assertEqual(r.need_new_runner(), False)

        r.runners['0'].status_history = ['online']
        r.runners['0'].status = 'running'
        self.assertEqual(r.need_new_runner(), False)
