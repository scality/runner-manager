from typing import List

from rq import Queue
from rq.job import Job, JobStatus
from rq_scheduler import Scheduler

from runner_manager import Runner, RunnerGroup, Settings
from runner_manager.clients.github import GitHub
from runner_manager.jobs.startup import startup, sync_runner_groups


def test_startup(queue: Queue, settings: Settings, github: GitHub):
    job: Job = queue.enqueue(startup, settings)
    status: JobStatus = job.get_status()
    assert status == JobStatus.FINISHED
    assert RunnerGroup.find().count() == 1
    settings_group = settings.runner_groups[0]
    runner_group: RunnerGroup = RunnerGroup.find(
        RunnerGroup.name == settings_group.name
    ).first()
    assert runner_group.backend.name == settings_group.backend.name
    assert runner_group.manager == settings.name

    # Run startup again
    settings.name = "new-name"
    job: Job = queue.enqueue(startup, settings)
    status: JobStatus = job.get_status()
    assert status == JobStatus.FINISHED
    assert RunnerGroup.find().count() == 1
    runner_group: RunnerGroup = RunnerGroup.find(
        RunnerGroup.name == settings_group.name
    ).first()
    assert runner_group.manager == settings.name
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
    runner_group.create_runner(github)
    runners = Runner.find().count()
    assert RunnerGroup.find().count() == 2
    job: Job = queue.enqueue(startup, settings)
    # Ensure the leftover group and runner are deleted
    assert runner_group not in RunnerGroup.find().all()
    assert RunnerGroup.find().count() == 1
    assert Runner.find().count() == runners - 1


def test_scheduler(
    queue: Queue, settings: Settings, github: GitHub, scheduler: Scheduler
):
    """Test that the scheduler is bootstrapped with the correct jobs."""
    queue.enqueue(startup, settings)
    jobs: List[Job] = scheduler.get_jobs()
    is_indexing: bool = False
    is_healthcheck: bool = False
    for job in jobs:
        job_type = job.meta.get("type")
        if job_type == "indexing":
            is_indexing = True
        elif job_type == "healthcheck":
            assert settings.healthcheck_interval.total_seconds() / 2 == job.timeout
            is_healthcheck = True

    assert is_indexing is True
    assert is_healthcheck is True


def test_update_group_sync(settings: Settings, github: GitHub):
    sync_runner_groups(settings)
    runner_group: RunnerGroup = RunnerGroup.find().first()
    assert runner_group.backend.name == "base"
    runner_group.labels = ["new-label"]
    runner_group.save(github=github)
    sync_runner_groups(settings)
