import logging

from fastapi import FastAPI, Request, Response
from githubkit.webhooks import parse
from githubkit.webhooks.types import WebhookEvent

from runner_manager.dependencies import get_queue
from runner_manager.jobs.startup import startup

log = logging.getLogger(__name__)

app = FastAPI()


@app.on_event("startup")
def startup_event():
    queue = get_queue()
    job = queue.enqueue(startup)
    status = job.get_status()
    log.info(f"Startup job is {status}")


@app.get("/_health")
def health():
    return Response(status_code=200)


@app.post("/webhook", status_code=202)
async def webhook(request: Request):
    try:
        event: WebhookEvent = parse(
            request.headers["X-GitHub-Event"], await request.body()
        )
        return "Accepted"
    except Exception as e:
        return {"error": str(e)}
