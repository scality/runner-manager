from rq import Queue
from rq.job import Job, JobStatus
from starlette.testclient import TestClient

from runner_manager.jobs.startup import startup


def enqueue_startup(queue: Queue) -> bool:
    for job in queue.get_jobs():
        job: Job
        if startup == job.func:
            if job.get_status() == JobStatus.QUEUED:
                queue.enqueue_job(job)
            return job.get_status() == JobStatus.FINISHED
    return False


def test_lifespan(fastapp, queue: Queue):
    with TestClient(fastapp) as client:
        # Application's lifespan is called on entering the block.
        response = client.get("/")
        assert response.status_code == 200
        assert enqueue_startup(queue) is True
