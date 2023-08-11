import logging

from fastapi import FastAPI

from runner_manager.auth import TrustedHostHealthRoutes
from runner_manager.dependencies import get_queue, get_settings
from runner_manager.jobs.startup import startup
from runner_manager.routers import _health, private, public, webhook

log = logging.getLogger(__name__)
app = FastAPI()
settings = get_settings()


app.include_router(webhook.router)
app.include_router(_health.router)
app.include_router(private.router)
app.include_router(public.router)
app.add_middleware(TrustedHostHealthRoutes, allowed_hosts=settings.allowed_hosts)


@app.on_event("startup")
def startup_event():
    queue = get_queue()
    job = queue.enqueue(startup)
    status = job.get_status()
    log.info(f"Startup job is {status}")
