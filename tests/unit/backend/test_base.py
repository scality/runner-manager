import pytest

from redis_om import Migrator

from runner_manager.backend.base import BaseBackend


def test_backend_create_runner(backend, runner):
    runner = backend.create(runner)
    assert runner.backend == backend.name
    assert runner.backend_instance == runner.pk


def test_backend_delete_runner(backend, runner):
    runner = backend.create(runner)
    assert backend.delete(runner) == 1


def test_backend_list_runners(backend, runner):
    runner = backend.create(runner)
    Migrator().run()
    assert runner in backend.list()


def test_backend_update_runner(backend, runner):
    runner = backend.create(runner)
    runner.busy = True
    runner.status = "online"
    runner = backend.update(runner)
    assert runner.busy is True
    assert runner.status == "online"
