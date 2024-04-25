from __future__ import annotations

import logging
from datetime import datetime, timedelta

from githubkit.versions.latest.models import (
    WebhookWorkflowJobCompleted as WorkflowJobCompleted,
)
from githubkit.versions.latest.models import (
    WebhookWorkflowJobInProgress as WorkflowJobInProgress,
)
from githubkit.versions.latest.models import (
    WebhookWorkflowJobQueued as WorkflowJobQueued,
)
from githubkit.versions.latest.webhooks import WorkflowJobEvent

from runner_manager import Settings
from runner_manager.clients.github import GitHub
from runner_manager.dependencies import get_github, get_settings
from runner_manager.models.runner import Runner
from runner_manager.models.runner_group import RunnerGroup

log = logging.getLogger(__name__)


def log_workflow_job(webhook: WorkflowJobEvent) -> None:
    log.info(
        f"Starting workflow_job event (status: {webhook.workflow_job.status}, "
        f"conclusion: {webhook.workflow_job.conclusion}, "
        f"repository: {webhook.repository.full_name})"
    )


def time_to_start(webhook: WorkflowJobEvent) -> timedelta:
    """From a given webhook, calculate the time it took to start the job"""

    if isinstance(webhook.workflow_job.created_at, str):
        created_at = datetime.fromisoformat(webhook.workflow_job.created_at)
    else:
        created_at = webhook.workflow_job.created_at

    if isinstance(webhook.workflow_job.started_at, str):
        started_at = datetime.fromisoformat(webhook.workflow_job.started_at)
    else:
        started_at = webhook.workflow_job.started_at

    assert isinstance(started_at, datetime)
    assert isinstance(created_at, datetime)

    return started_at - created_at


def completed(webhook: WorkflowJobCompleted) -> int:
    log_workflow_job(webhook)
    runner: Runner | None = Runner.find_from_webhook(webhook)
    if not runner:
        log.info(f"Runner {webhook.workflow_job.runner_name} not found")
        return 0
    runner_group: RunnerGroup | None = RunnerGroup.find_from_webhook(webhook)
    if not runner_group:
        log.warning(f"Runner group for {runner} not found")
        return 0
    log.info(f"Found {runner_group} for {runner}")
    github: GitHub = get_github()
    log.info(f"Deleting runner {runner} in group {runner_group}")
    delete = runner_group.delete_runner(runner, github)
    if runner_group.need_new_runner:
        log.info(f"Runner group {runner_group.name} needs a new runner")
        runner_group.create_runner(github)
    return delete


def in_progress(webhook: WorkflowJobInProgress) -> str | None:
    log_workflow_job(webhook)
    settings: Settings = get_settings()
    name: str | None = webhook.workflow_job.runner_name
    runner_group: RunnerGroup | None = RunnerGroup.find_from_webhook(webhook)
    if not runner_group:
        log.info(f"Runner group for {name} not found")
        return None
    log.info(f"Updating runner {name} in group {runner_group.name}")
    runner: Runner = runner_group.update_runner(webhook=webhook)
    log.info(f"Runner {name} in group {runner_group.name} has been updated")
    tts = time_to_start(webhook)
    log.info(f"{runner} took {tts} to start")
    # If the time to start is greater than settings.timeout_runner,
    # create an extra runner.
    # The main reason we perform this action is to ensure that
    # in the case we have missed a webhook, we still have a runner
    # available for the jobs that are requesting it.
    if tts > settings.timeout_runner and runner_group.is_full is False:
        log.info(
            f"Time to start too high ({tts}), creating runner for {runner_group.name}"
        )
        github: GitHub = get_github()
        runner_group.create_runner(github)
    return runner.pk


def queued(webhook: WorkflowJobQueued) -> str | None:
    log_workflow_job(webhook)
    labels = webhook.workflow_job.labels
    log.info(f"Finding runner group with labels {labels}")
    runner_group: RunnerGroup = RunnerGroup.find_from_labels(
        webhook.workflow_job.labels
    )
    if not runner_group:
        log.info(f"Runner group with labels {labels} not found")
        return None
    github: GitHub = get_github()
    log.info(f"Creating runner for {runner_group}")
    runner: Runner | None = runner_group.create_runner(github)
    return runner.pk if runner else None
