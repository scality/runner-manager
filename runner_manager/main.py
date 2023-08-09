import logging

from fastapi import Depends, FastAPI, HTTPException, Response, Security, status
from fastapi.security import APIKeyHeader, APIKeyQuery

from runner_manager.dependencies import get_queue, get_settings
from runner_manager.jobs.startup import startup
from runner_manager.models.settings import Settings
from runner_manager.routers import webhook

log = logging.getLogger(__name__)

app = FastAPI()
api_key_query = APIKeyQuery(name="api-key", auto_error=False)
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


def get_api_key(
    api_key_query: str = Security(api_key_query),
    api_key_header: str = Security(api_key_header),
    settings: Settings = Depends(get_settings),
) -> str:
    if not settings.api_key:
        return ""
    if api_key_query in [settings.api_key.get_secret_value()]:
        return api_key_query
    if api_key_header in [settings.api_key.get_secret_value()]:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API Key",
    )


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


@app.get("/public")
def public():
    """A public endpoint that does not require any authentication."""
    return "Public Endpoint"


@app.get("/private")
def private(api_key: str = Security(get_api_key)):
    """A private endpoint that requires a valid API key to be provided."""
    return f"Private Endpoint. API Key: {api_key}"
