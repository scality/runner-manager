import logging

from . import runner_m

logger = logging.getLogger("runner_manager")


class Webhook(object):
    event: str
    payload: dict

    def __init__(self, payload: dict, event: str):
        self.event = event
        self.payload = payload

    def __call__(self, *args, **kwargs):
        # Check if we managed this event
        if self.event not in [method for method in dir(self) if method[:2] != "__"]:
            logger.info(f"Event {self.event} not managed")
        else:
            logger.info(f'Get event: {self.event}')
            getattr(self, self.event)(self.payload)

    def workflow_run(self, payload):
        pass

    def workflow_job(self, payload):
        status = {}
        if payload['action'] == 'queued' or "self-hosted" not in payload["workflow_job"]["labels"]:
            return
        elif payload['action'] == 'in_progress':
            status = {
                'status': 'online',
                'busy': True,
            }
        elif payload['action'] == 'complete':
            status = {
                'status': 'offline',
                'busy': False,
            }

        status.update({
            'name': payload["workflow_job"]["runner_name"],
            'id': payload["workflow_job"]["runner_id"],
            'labels': payload["workflow_job"]["labels"],
        })
        runner_m.update_runner_status(status)

    def ping(self, payload):
        logger.info('Ping from Github')
