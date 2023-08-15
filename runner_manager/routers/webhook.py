from typing import Annotated, Set

from fastapi import APIRouter, Depends, Header, HTTPException, Security
from githubkit.webhooks import verify
from githubkit.webhooks.types import PingEvent
from rq import Queue

from runner_manager.dependencies import get_queue, get_settings
from runner_manager.models.settings import Settings
from runner_manager.models.webhook import AcceptedWebhookEvents, WebhookResponse

router = APIRouter(prefix="/webhook")

IMPLEMENTED_WEBHOOKS: Set[str] = {
    "workflow_job.completed",
    "workflow_job.queued",
    "workflow_job.in_progress",
}


def validate_webhook(
    webhook: AcceptedWebhookEvents,
    settings: Settings = Depends(get_settings),
    x_hub_signature_256: Annotated[str | None, Header()] = None,
) -> bool:

    if settings.github_webhook_secret is None:
        return True
    elif x_hub_signature_256 is None:
        raise HTTPException(status_code=401, detail="Missing signature")
    valid: bool = verify(
        settings.github_webhook_secret.get_secret_value(),
        webhook.json(exclude_unset=True),
        x_hub_signature_256,
    )
    return valid


@router.post("/")
def post(
    webhook: AcceptedWebhookEvents,
    x_github_event: Annotated[str | None, Header()] = None,
    valid: bool = Security(validate_webhook),
    queue: Queue = Depends(get_queue),
) -> WebhookResponse:
    if not isinstance(webhook, PingEvent):
        action = webhook.action
    else:
        action = None
    event_name = f"{x_github_event}.{action}"

    if event_name in IMPLEMENTED_WEBHOOKS:
        job_name = f"runner_manager.jobs.{event_name}"

        job = queue.enqueue(job_name, webhook)

        return WebhookResponse(success=True, message="Job queued", job_id=job.id)
    return WebhookResponse(success=False, message="Not implemented")
