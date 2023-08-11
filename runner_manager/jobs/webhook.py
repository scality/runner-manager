from rq import Queue
from githubkit.webhooks.types import WorkflowJobEvent
from runner_manager.models.webhook import AcceptedWebhookEvents
from runner_manager.logging import log
from runner_manager.jobs import workflow_job

def handle_webhook(webhook: AcceptedWebhookEvents, queue: Queue):
    """Receives a webhook from GitHub and handles it.

    This method will:

    - Check if the webhook is a workflow_job event.
        - if the workflow_job is queued call workflow_job_queued job.
        - if the workflow_job is completed call workflow_job_completed job.
        - if the workflow_job is in_progress call workflow_job_in_progress job.
    """
    pass
