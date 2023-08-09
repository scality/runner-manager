import logging

from fastapi import FastAPI, Security

from runner_manager.auth import TrustedHostHealthRoutes, get_api_key
from runner_manager.dependencies import get_queue, get_settings
from runner_manager.jobs.startup import startup
from runner_manager.routers import _health, webhook

log = logging.getLogger(__name__)
app = FastAPI()
settings = get_settings()


app.include_router(webhook.router)
app.include_router(_health.router)
app.add_middleware(TrustedHostHealthRoutes, allowed_hosts=settings.allowed_hosts)


@app.on_event("startup")
def startup_event():
    queue = get_queue()
    job = queue.enqueue(startup)
    status = job.get_status()
    log.info(f"Startup job is {status}")


@app.get("/public")
def public():
    """A public endpoint that does not require any authentication."""
    return "Public Endpoint"


@app.get("/private")
def private(api_key: str = Security(get_api_key)):
    """A private endpoint that requires a valid API key to be provided."""
    return f"Private Endpoint. API Key: {api_key}"
