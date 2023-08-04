import logging

from fastapi import Depends, FastAPI, HTTPException, Response, Security, status
from fastapi.security import APIKeyHeader, APIKeyQuery

from runner_manager.dependencies import get_queue, get_settings
from runner_manager.jobs.startup import startup

log = logging.getLogger(__name__)

app = FastAPI()
api_key_query = APIKeyQuery(name="api-key", auto_error=False)
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


def get_api_key(
    api_key_query: str = Security(api_key_query),
    api_key_header: str = Security(api_key_header),
) -> str:
    settings = get_settings()
    if not settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API Key not configured in settings",
        )
    api_key = api_key_query or api_key_header
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key required for this endpoint",
        )
    if api_key != settings.api_key.get_secret_value():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    return api_key


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
def private(api_key: str = Depends(get_api_key)):
    """A private endpoint that requires a valid API key to be provided."""
    return f"Private Endpoint. API Key: {api_key}"
