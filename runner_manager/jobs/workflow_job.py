from githubkit.webhooks.models import (
    WorkflowJobCompleted,
    WorkflowJobInProgress,
    WorkflowJobQueued,
)

from runner_manager.logging import log
from runner_manager.models.runner import Runner
from runner_manager.models.runner_group import RunnerGroup


def completed(webhook: WorkflowJobCompleted):
    log.info(f"Starting {webhook.action} workflow_job event")
    runner_group: RunnerGroup = RunnerGroup.find(
        RunnerGroup.id == webhook.workflow_job.runner_group_id
    ).first()
    runner: Runner = Runner.find(Runner.id == webhook.workflow_job.runner_id).first()
    log.info(f"Deleting runner {runner.name} from group {runner_group.name}")
    return runner_group.delete_runner(runner)


def in_progress(webhook: WorkflowJobInProgress) -> Runner:
    log.info(f"Starting {webhook.action} workflow_job event")
    runner_group: RunnerGroup = RunnerGroup.find(
        RunnerGroup.id == webhook.workflow_job.runner_group_id
    ).first()
    runner: Runner = Runner.find(Runner.id == webhook.workflow_job.runner_id).first()
    log.info(f"Updating runner {runner.name} in group {runner_group.name}")
    return runner_group.update_runner(runner)


def queued(webhook: WorkflowJobQueued) -> Runner:
    log.info(f"Starting {webhook.action} workflow_job event")
    labels = webhook.workflow_job.labels
    log.info(f"Finding runner group with labels {labels}")
    runner_group: RunnerGroup = RunnerGroup.find(RunnerGroup.labels << labels).first()
    return runner_group.create_runner()
