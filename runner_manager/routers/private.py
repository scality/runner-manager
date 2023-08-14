from fastapi import APIRouter, Security

from runner_manager.auth import get_api_key

router = APIRouter(prefix="/private")


@router.get("/")
def private(api_key: str = Security(get_api_key)):
    """A private endpoint that requires a valid API key to be provided."""
    return f"Private Endpoint. API Key: {api_key}"
