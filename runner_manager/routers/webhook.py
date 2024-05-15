from typing import Annotated, Set

from fastapi import APIRouter, Depends, Header, HTTPException, Security, Request
from githubkit.versions.latest.models import WebhookPing
from githubkit.webhooks import verify
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


async def validate_webhook(
    request: Request,
    settings: Settings = Depends(get_settings),
    x_hub_signature_256: Annotated[str | None, Header()] = None,
) -> bool:

    body = await request.body()

    if settings.github_webhook_secret is None:
        return True
    elif x_hub_signature_256 is None:
        raise HTTPException(status_code=401, detail="Missing signature")
    valid: bool = verify(
        settings.github_webhook_secret.get_secret_value(),
        body,
        x_hub_signature_256,
    )

    if not valid:
      raise HTTPException(status_code=401, detail="Signature values do not match - check webhook secret value")

    return valid


@router.post("/")
def post(
    webhook: AcceptedWebhookEvents,
    x_github_event: Annotated[str | None, Header()] = None,
    valid: bool = Security(validate_webhook),
    queue: Queue = Depends(get_queue),
) -> WebhookResponse:

    if not isinstance(webhook, WebhookPing):
        action = webhook.action
    else:
        action = None
    event_name = f"{x_github_event}.{action}"

    if event_name in IMPLEMENTED_WEBHOOKS:
        job_name = f"runner_manager.jobs.{event_name}"

        job = queue.enqueue(job_name, webhook)

        return WebhookResponse(success=True, message="Job queued", job_id=job.id)
    return WebhookResponse(success=False, message="Not implemented")
