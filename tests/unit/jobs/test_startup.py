from rq import Queue
from rq.job import Job, JobStatus

from runner_manager import RunnerGroup
from runner_manager.jobs.startup import startup


def test_startup(queue: Queue, settings):
    print(queue.connection)
    job: Job = queue.enqueue(startup, settings)
    status: JobStatus = job.get_status()
    assert status == JobStatus.FINISHED
    assert RunnerGroup.find().count() == 1
    settings_group = settings.runner_groups[0]
    runner_group: RunnerGroup = RunnerGroup.find(
        RunnerGroup.name == settings_group.name
    ).first()
    assert runner_group.backend.name == settings_group.backend.name
