"""Jobs to run on startup."""

import logging
from datetime import datetime
from typing import List

from redis_om import Migrator
from rq.job import Job
from rq_scheduler import Scheduler

from runner_manager.clients.github import GitHub
from runner_manager.dependencies import get_github, get_scheduler, get_settings
from runner_manager.jobs import healthcheck, leaks
from runner_manager.models.runner_group import RunnerGroup
from runner_manager.models.settings import Settings

log = logging.getLogger(__name__)


def sync_runner_groups(settings: Settings):
    """Sync runner groups between the settings of the database and GitHub.

    Args:
        settings (Settings): Settings of the application
        github (GitHub): GitHub client
    """

    github: GitHub = get_github()
    runner_groups_configs = settings.runner_groups
    existing_groups: List[RunnerGroup] = RunnerGroup.find().all()
    for runner_group_config in runner_groups_configs:
        if runner_group_config.name in [group.name for group in existing_groups]:
            runner_group: RunnerGroup = RunnerGroup.find_from_base(runner_group_config)
            existing_groups.remove(runner_group)
            runner_group.update(manager=settings.name, **runner_group_config.dict())
            runner_group.save(github=github)
        else:
            runner_group: RunnerGroup = RunnerGroup(
                manager=settings.name, **runner_group_config.dict()
            )
            runner_group.save(github=github)

    for runner_group in existing_groups:
        log.info(f"Deleting runner group {runner_group.name}")
        runner_group.delete(pk=runner_group.pk, github=github)


def bootstrap_scheduler(
    settings: Settings,
):
    scheduler: Scheduler = get_scheduler()
    jobs: List[Job] = scheduler.get_jobs()
    groups: List[RunnerGroup] = RunnerGroup.find().all()
    for job in jobs:
        # Cancel any existing healthcheck jobs
        job_type = job.meta.get("type")
        if job_type == "healthcheck" or job_type == "indexing" or job_type == "leaks":
            log.info(f"Canceling {job_type} job: {job.id}")
            scheduler.cancel(job)

    # Scheduling indexing job
    scheduler.schedule(
        scheduled_time=datetime.utcnow(),
        func=indexing,
        interval=settings.indexing_interval.total_seconds(),
        meta={"type": "indexing"},
        result_ttl=settings.indexing_interval.total_seconds() * 10,
        repeat=None,
    )
    for group in groups:
        log.info(f"Scheduling healthcheck for group {group.name}")
        scheduler.schedule(
            scheduled_time=datetime.utcnow(),
            func=healthcheck.group,
            args=[
                group.pk,
                settings.time_to_live,
                settings.timeout_runner,
            ],
            meta={
                "type": "healthcheck",
                "group": group.name,
            },
            interval=settings.healthcheck_interval.total_seconds(),
            # As described in the documentation of rq-scheduler, the result_ttl
            # must be set to a value greater than the interval, otherwise
            # the entry job with the details will expire and the job will not get
            # rescheduled.
            result_ttl=settings.healthcheck_interval.total_seconds() * 10,
            repeat=None,
            timeout=settings.healthcheck_interval.total_seconds() / 2,
        )
        log.info(f"Scheduling leaks job for group {group.name}")
        scheduler.schedule(
            scheduled_time=datetime.utcnow(),
            func=leaks.runner_leaks,
            args=[group.pk],
            meta={
                "type": "leaks",
                "group": group.name,
            },
            interval=settings.healthcheck_interval.total_seconds() * 4,
            result_ttl=60,
            repeat=None,
        )


def indexing():
    """For RedisSearch to work, we need to run the Migrator to create the indexes.

    This job is required when:
    - Upon the first creation of the redis instance.
    - A new schema is introduced.
    - The Redis instance is rebooted.
    - Changes are made to the RedisSearch schema.
    """

    log.info("Running indexing job...")
    Migrator().run()
    log.info("Indexing job complete.")


def startup(settings: Settings = get_settings()):
    """Bootstrap the application."""
    log.info("Startup initiated.")
    indexing()
    log.info("Creating runner groups...")
    sync_runner_groups(settings)
    log.info("Runner groups created.")
    log.info("Bootstrapping healthchecks...")
    bootstrap_scheduler(settings)
    log.info("Healthchecks bootstrapped.")
    log.info("Startup complete.")
