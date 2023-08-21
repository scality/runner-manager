from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, APIKeyQuery

from runner_manager.dependencies import get_settings
from runner_manager.models.settings import Settings

api_key_query = APIKeyQuery(name="api-key", auto_error=False)
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


def get_api_key(
    api_key_query: str = Security(api_key_query),
    api_key_header: str = Security(api_key_header),
    settings: Settings = Depends(get_settings),
) -> str:
    """Get the API key from either the query parameter or the header"""
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
