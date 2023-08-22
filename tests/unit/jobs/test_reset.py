from rq import Queue
from rq.job import JobStatus

from runner_manager import RunnerGroup
from runner_manager.jobs import reset
from runner_manager.models.runner import RunnerStatus


def test_reset_job(runner_group: RunnerGroup, queue: Queue, runner_token):
    # setup runner group
    runner_group.save()
    runner = runner_group.create_runner(runner_token)
    assert runner in runner_group.get_runners()
    runner.status = RunnerStatus.online
    runner.save()
    # run reset job with online runner
    job = queue.enqueue(
        reset.group,
        runner_group.pk,
    )
    assert job.get_status() == JobStatus.FINISHED
    assert runner in runner_group.get_runners()
    # run reset job with offline runner
    runner.status = RunnerStatus.offline
    runner.save()
    job = queue.enqueue(
        reset.group,
        runner_group.pk,
    )
    assert job.get_status() == JobStatus.FINISHED
    assert runner not in runner_group.get_runners()
    assert len(runner_group.get_runners()) == 1


def test_reset_job_group_not_found(queue: Queue, runner_group: RunnerGroup):
    # run job before creating runner group
    job = queue.enqueue(
        reset.group,
        runner_group.pk,
    )
    assert job.get_status() == JobStatus.FAILED
    # create runner group and run job
    runner_group.save()
    job = queue.enqueue(
        reset.group,
        runner_group.pk,
    )
    assert job.get_status() == JobStatus.FINISHED
