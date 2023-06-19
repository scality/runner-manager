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
        Raise an error if the method does not exist
        """
        # Check if we managed this event
        if self.event not in [method for method in dir(self) if method[:2] != "__"]:
            logger.info(f"Event {self.event} not managed")
        else:
            logger.info(f"Get event: {self.event}")
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
        if (
            payload.action == "queued"
            and "self-hosted" in payload.workflow_job.labels
            and payload.workflow_job.runner_id is None
        ):
            payload.workflow_job.labels.remove("self-hosted")
            try:
                r_m = next(
                    iter(
                        runner_m.get_runner_manager_on_demand(
                            lambda elem: elem.vm_type.tags
                            == payload.workflow_job.labels
                        )
                    ),
                    None,
                )
            except Exception as e:
                logger.error(e.with_traceback())
                return 0

            logger.info(f"{r_m} Runner manager found")
            if r_m:
                logger.info("Start create new runner " + r_m.redis_key_name())
                try:
                    r_m.create_runner()
                except Exception as e:
                    logger.error(e)

            return
        elif payload.action == "in_progress":
            status = {
                "status": "online",
                "busy": True,
            }
        elif payload.action == "completed":
            status = {
                "status": "offline",
                "busy": False,
            }

        status.update(
            {
                "name": payload.workflow_job.runner_name,
                "id": payload.workflow_job.runner_id,
                "labels": payload.workflow_job.labels,
            }
        )

        if (
            payload.action != "queued"
            and payload.workflow_job.conclusion != "skipped"
        ):
            if runner_m.redis.check_runners(payload.workflow_job.runner_name):
                runner_m.factory.cloud_manager.update_vm_metadata(
                    payload.workflow_job.runner_name,
                    dict(
                        status=status["status"],
                        repository=payload.repository.name,
                        workflow=payload.workflow_job.workflow_name,
                        job=payload.workflow_job.name
                    )
                )

        runner_m.update_runner_status(status)

    def ping(self, payload: WebHook):
        logger.info("Ping from Github")
