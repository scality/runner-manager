import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

import fakeredis
from runners_manager.runner.Manager import Manager
from runners_manager.runner.RedisManager import RedisManager


class ObjectId(object):
    def __init__(self, id):
        self.id = id


class MockVmType:
    quantity = {"max": 5, "min": 0}


class TestRunnerManager(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_redis = RedisManager(fakeredis.FakeStrictRedis())
        self.github_manager = MagicMock()
        self.cloud_manager = MagicMock()

        self.github_manager.link_download_runner.return_value = "fake_link"
        self.github_manager.create_runner_token.return_value = ""
        self.github_manager.get_runners.return_value = []
        self.github_manager.force_delete_runner.return_value = None

        self.cloud_manager.script_init_runner.return_value = ""
        self.cloud_manager.create_vm.return_value = ObjectId("str")
        self.cloud_manager.delete_vm.return_value = None

    @patch("runners_manager.runner.Manager.RunnerManager")
    @patch("runners_manager.runner.Manager.RunnerFactory")
    def test_no_config(self, factory, manager):
        r = Manager(
            {
                "github_organization": "test",
                "runner_pool": [],
                "redis": {"host": "test", "port": 1234},
                "extra_runner_timer": {"minutes": 10, "hours": 0},
                "timeout_runner_timer": {"minutes": 0, "hours": 1},
            },
            self.cloud_manager,
            self.github_manager,
            self.fake_redis,
        )
        self.assertEqual(r.runner_managers, [])
        self.assertEqual((r.timeout_runner_timer.seconds // 60) % 60, 0)
        self.assertEqual(r.timeout_runner_timer.seconds // 3600, 1)

        self.assertEqual((r.extra_runner_online_timer.seconds // 60) % 60, 10)
        self.assertEqual(r.extra_runner_online_timer.seconds // 3600, 0)

    @patch("runners_manager.runner.Manager.RunnerManager")
    @patch("runners_manager.runner.Manager.RunnerFactory")
    def test_config_vm_type(self, factory, manager):
        r = Manager(
            {
                "github_organization": "test",
                "runner_pool": [
                    {
                        "tags": ["centos7", "small"],
                        "config": {
                            "flavor": "m1.small",
                            "image": "CentOS 7 (PVHVM)",
                        },
                        "quantity": {"min": 2, "max": 4},
                    }
                ],
                "redis": {"host": "test", "port": 1234},
                "extra_runner_timer": {"minutes": 10, "hours": 10},
                "timeout_runner_timer": {"minutes": 10, "hours": 10},
            },
            self.cloud_manager,
            self.github_manager,
            self.fake_redis,
        )
        self.assertEqual(r.runner_managers.__len__(), 1)

    @patch("runners_manager.runner.Manager.RunnerManager")
    @patch("runners_manager.runner.Manager.RunnerFactory")
    def test_update_without_changes(self, mock_manager, mock_runner_factory):
        mock_manager.min_runner_number.side_effect = 3
        mock_manager.filter_runners.side_effect = []
        mock_manager.need_new_runner.side_effect = False
        mock_manager.vm_type = MockVmType()

        r = Manager(
            {
                "github_organization": "test",
                "runner_pool": [
                    {
                        "tags": ["centos7", "small"],
                        "config": {
                            "flavor": "m1.small",
                            "image": "CentOS 7 (PVHVM)",
                        },
                        "quantity": {"on_demand": False, "min": 2, "max": 4},
                    }
                ],
                "redis": {"host": "test", "port": 1234},
                "extra_runner_timer": {"minutes": 10, "hours": 10},
                "timeout_runner_timer": {"minutes": 10, "hours": 10},
            },
            self.cloud_manager,
            self.github_manager,
            self.fake_redis,
        )
        r.update_all_runners(
            [
                {
                    "id": 1,
                    "name": "1",
                    "os": "linux",
                    "status": "online",
                    "busy": False,
                    "labels": [{"id": 77, "name": "self-hosted", "type": "read-only"}],
                },
                {
                    "id": 2,
                    "name": "2",
                    "os": "linux",
                    "status": "online",
                    "busy": False,
                    "labels": [{"id": 77, "name": "self-hosted", "type": "read-only"}],
                },
            ]
        )
        self.assertEqual(r.runner_managers[0].update_runners.call_count, 1)
        self.assertEqual(r.runner_managers[0].filter_runners.call_count, 3)
        self.assertEqual(r.runner_managers[0].respawn_runner.call_count, 0)
        self.assertEqual(r.runner_managers[0].create_runner.call_count, 0)
        self.assertEqual(r.runner_managers[0].respawn_runner.call_count, 0)
        self.assertEqual(r.runner_managers[0].delete_runner.call_count, 0)
