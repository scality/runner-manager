from rq import Queue

from runner_manager import RunnerGroup
from runner_manager.clients.github import GitHub
from runner_manager.jobs.leaks import runner_leaks
from runner_manager.models.runner import Runner, RunnerStatus


def test_leak_job(runner_group: RunnerGroup, queue: Queue, github: GitHub, monkeypatch):
    runner_group.save()
    runner = runner_group.create_runner(github)
    assert runner in runner_group.get_runners()
    runner.status = RunnerStatus.online
    runner.busy = True
    runner.save()
    job = queue.enqueue(
        runner_leaks,
        runner_group.pk,
    )
    # No leaks were found
    assert job.return_value() is False
    fake_runner: Runner = Runner(
        name="fake_runner",
        instance_id="fake_instance_id",
        busy=False,
        status=RunnerStatus.offline,
        runner_group_id=runner_group.id,
    )
    monkeypatch.setattr(
        "runner_manager.backend.base.BaseBackend.list",
        lambda self: [runner, fake_runner],
    )
    job = queue.enqueue(
        runner_leaks,
        runner_group.pk,
    )
    # fake_runner is a leak since it is not in the group
    assert job.return_value() is True


def test_leak_job_group_not_found(queue: Queue, github: GitHub):
    job = queue.enqueue(
        runner_leaks,
        "fake_id",
    )
    assert job.return_value() is False
