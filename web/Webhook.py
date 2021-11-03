import logging

from web import runner_m

logger = logging.getLogger("runner_manager")


class Webhook(object):
    event: str
    payload: dict

    def __init__(self, payload: dict, event: str):
        logger.info(f'Get event: {event}')
        self.event = event
        self.payload = payload

    def __call__(self, *args, **kwargs):
        # Check if we managed this event
        if self.event not in [methode for methode in dir(self) if methode[:2] != "__"]:
            logger.info(f"Event {self.event} not managed")
        else:
            getattr(self, self.event)(self.payload)

    def workflow_run(self, payload):
        pass

    def workflow_job(self, payload):
        # logger.info(payload)
        status = {}
        if payload['action'] == 'queued' or "self-hosted" in payload["workflow_job"]["labels"]:
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
        # payload["action"] is "queued" then "in_progress" then "complete"
        # payload["workflow_job"]["runner_name"] is the runner name
        # With there name it can be use to change the runner status without calling the github API
        # runner_m.update(None)

    def ping(self, payload):
        logger.info('Ping from Github')

    def __del__(self):
        pass
