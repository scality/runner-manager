from rq import Queue
from rq.job import Job, JobStatus

from runner_manager import RunnerGroup, Runner
from runner_manager.jobs.startup import startup


def test_startup(queue: Queue, settings, runner_token):
    job: Job = queue.enqueue(startup, settings)
    status: JobStatus = job.get_status()
    assert status == JobStatus.FINISHED
    assert RunnerGroup.find().count() == 1
    settings_group = settings.runner_groups[0]
    runner_group: RunnerGroup = RunnerGroup.find(
        RunnerGroup.name == settings_group.name
    ).first()
    assert runner_group.backend.name == settings_group.backend.name

    # Run startup again
    job: Job = queue.enqueue(startup, settings)
    status: JobStatus = job.get_status()
    assert status == JobStatus.FINISHED
    assert RunnerGroup.find().count() == 1

    # Add leftover that should be deleted
    runner_group = RunnerGroup(
        name="leftover",
        organization="leftover",
        id=1,
        labels=[],
        manager=settings.name,
        backend={"name": "base"},
    )
    runner_group.save()
    runner_group.create_runner(runner_token)
    runners = Runner.find().count()
    assert RunnerGroup.find().count() == 2
    job: Job = queue.enqueue(startup, settings)
    # Ensure the leftover group and runner are deleted
    assert runner_group not in RunnerGroup.find().all()
    assert RunnerGroup.find().count() == 1
    assert Runner.find().count() == runners - 1
