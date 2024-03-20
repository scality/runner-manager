from typing import Union

from githubkit.versions.latest.models import WebhookPing
from githubkit.versions.latest.webhooks import WorkflowJobEvent
from pydantic import BaseModel


class WebhookResponse(BaseModel):
    success: bool
    message: str | None = None
    job_id: str | None = None


AcceptedWebhookEvents = Union[WorkflowJobEvent, WebhookPing]
