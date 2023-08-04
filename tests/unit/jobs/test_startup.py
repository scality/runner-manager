
from runner_manager.jobs.startup import startup
from rq import Queue
from rq.job import Job, JobStatus

def test_startup(queue: Queue):
    job: Job = queue.enqueue(startup)
    # wait for job to finish and ensure it is successful
    status: JobStatus = job.get_status()
    while status != JobStatus.FINISHED:
        status = job.get_status()
        # break if job failed
        if status == JobStatus.FAILED:
            break
    assert status == JobStatus.FINISHED
