from githubkit.webhooks.models import WorkflowJobCompleted, WorkflowJobInProgress, WorkflowJobQueued
from runner_manager.models.runner import Runner
from runner_manager.models.runner_group import RunnerGroup
from runner_manager.logging import log

def completed(webhook: WorkflowJobCompleted):
    log.info(f"Handle {webhook.action} workflow_job event")
    runner_group: RunnerGroup = RunnerGroup.find(RunnerGroup.id == webhook.workflow_job.runner_group_id).first()
    runner: Runner = Runner.find(Runner.id == webhook.workflow_job.runner_id).first()
    log.info(f"Deleting runner {runner.name} from group {runner_group.name}")
    runner_group.delete_runner(runner)
    log.info(f"Runner {runner.name} deleted from group {runner_group.name}")


def in_progress(webhook: WorkflowJobInProgress):
    pass

def queued(webhook: WorkflowJobQueued):
    pass

