import logging

from fastapi import FastAPI, Response

from runner_manager.dependencies import get_queue
from runner_manager.jobs.startup import startup
from runner_manager.routers import webhook

log = logging.getLogger(__name__)

app = FastAPI()

app.include_router(webhook.router)

@app.on_event("startup")
def startup_event():
    queue = get_queue()
    job = queue.enqueue(startup)
    status = job.get_status()
    log.info(f"Startup job is {status}")


@app.get("/_health")
def health():
    return Response(status_code=200)
