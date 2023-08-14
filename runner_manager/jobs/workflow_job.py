from githubkit.webhooks.models import (
    WorkflowJobCompleted,
    WorkflowJobInProgress,
    WorkflowJobQueued,
)
from redis_om import NotFoundError

from runner_manager.logging import log
from runner_manager.models.runner import Runner
from runner_manager.models.runner_group import RunnerGroup


def completed(webhook: WorkflowJobCompleted) -> int:
    log.info(f"Starting {webhook.action} workflow_job event")
    try:
        runner_group: RunnerGroup = RunnerGroup.find(
            RunnerGroup.id == webhook.workflow_job.runner_group_id
        ).first()
        runner: Runner = Runner.find(
            Runner.id == webhook.workflow_job.runner_id
        ).first()
    except NotFoundError:
        log.warning(f"Runner {webhook.workflow_job.runner_name} not found")
        return 0
    log.info(f"Deleting runner {runner.name} from group {runner_group.name}")
    return runner_group.delete_runner(runner)


def in_progress(webhook: WorkflowJobInProgress) -> str | None:
    log.info(f"Starting {webhook.action} workflow_job event")
    name: str | None = webhook.workflow_job.runner_name
    group: str | None = webhook.workflow_job.runner_group_name
    group_id: int | None = webhook.workflow_job.runner_group_id
    try:
        runner_group: RunnerGroup = RunnerGroup.find(RunnerGroup.id == group_id).first()
        runner: Runner = Runner.find(Runner.name == name).first()
        log.info(f"Updating runner {name} in group {group}")
        runner: Runner = runner_group.update_runner(webhook)
        log.info(f"Runner {name} in group {group} has been updated")
    except NotFoundError:
        log.warning(f"Runner {name} belonging to group {group} not found")
        return None
    except Exception:
        log.error(f"Failed to update runner {name} in group {group}")
        raise Exception
    return runner.pk


def queued(webhook: WorkflowJobQueued) -> str | None:
    log.info(f"Starting {webhook.action} workflow_job event")
    labels = webhook.workflow_job.labels
    log.info(f"Finding runner group with labels {labels}")
    try:
        runner_group: RunnerGroup = RunnerGroup.find(
            RunnerGroup.labels << labels  # pyright: ignore
        ).first()
        log.info(f"Found runner group {runner_group.name}")
    except NotFoundError:
        log.warning(f"Runner group with labels {labels} not found")
        return None
    runner: Runner = runner_group.create_runner()
    return runner.pk
