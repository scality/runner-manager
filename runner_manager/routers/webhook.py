from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from githubkit.webhooks import verify
from githubkit.webhooks.types import WebhookEvent
from rq import Queue

from runner_manager.dependencies import get_queue, get_settings
from runner_manager.jobs.webhook import handle_webhook
from runner_manager.models.settings import Settings
from runner_manager.models.webhook import AcceptedWebhookEvents, WebhookResponse

router = APIRouter(prefix="/webhook")


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
    webhook: WebhookEvent,
    valid: bool = Depends(validate_webhook),
    queue: Queue = Depends(get_queue),
) -> WebhookResponse:

    job = queue.enqueue(handle_webhook, webhook)
    return WebhookResponse(success=True, message="Job queued", job_id=job.id)
