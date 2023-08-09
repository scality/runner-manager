from rq import Queue
from rq.job import Job, JobStatus

from runner_manager.jobs.startup import startup


def test_startup(queue: Queue):
    print(queue.connection)
    job: Job = queue.enqueue(startup)
    status: JobStatus = job.get_status()
    assert status == JobStatus.FINISHED
