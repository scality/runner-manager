from typing import Union

from githubkit.webhooks.types import PingEvent, WorkflowJobEvent
from pydantic import BaseModel


class WebhookResponse(BaseModel):
    success: bool
    message: str | None = None
    job_id: str | None = None


AcceptedWebhookEvents = Union[WorkflowJobEvent, PingEvent]
