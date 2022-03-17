import logging

from web.models import WebHook
from . import runner_m

logger = logging.getLogger("runner_manager")


class WebHookManager(object):
    """
    Run a function depending on webhook's event type
    https://docs.github.com/en/developers/webhooks-and-events/webhooks/webhook-events-and-payloads
    """
    event: str
    payload: WebHook

    def __init__(self, payload: WebHook, event: str):
        self.event = event
        self.payload = payload

    def __call__(self, *args, **kwargs):
        """
        Call the method with the same name as the event
        Raise an error if the methde does not exist
        """
        # Check if we managed this event
        if self.event not in [method for method in dir(self) if method[:2] != "__"]:
            logger.info(f"Event {self.event} not managed")
        else:
            logger.info(f'Get event: {self.event}')
            getattr(self, self.event)(self.payload)

    def workflow_run(self, payload: WebHook):
        """
        https://docs.github.com/en/developers/webhooks-and-events/webhooks/webhook-events-and-payloads#workflow_run
        """
        pass

    def workflow_job(self, payload: WebHook):
        """
        Github Action Workflow job event, received when a job
        https://docs.github.com/en/developers/webhooks-and-events/webhooks/webhook-events-and-payloads#workflow_job
        """
        status = {}
        if (payload.action == 'queued'
                or "self-hosted" not in payload.workflow_job.labels
                or payload.workflow_job.runner_id is None):
            return
        elif payload.action == 'in_progress':
            status = {
                'status': 'online',
                'busy': True,
            }
        elif payload.action == 'completed':
            status = {
                'status': 'offline',
                'busy': False,
            }

        status.update({
            'name': payload.workflow_job.runner_name,
            'id': payload.workflow_job.runner_id,
            'labels': payload.workflow_job.labels,
        })
        runner_m.update_runner_status(status)

    def ping(self, payload: WebHook):
        logger.info('Ping from Github')
