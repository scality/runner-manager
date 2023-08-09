from fastapi import Depends, HTTPException, Security, status
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import APIKeyHeader, APIKeyQuery
from starlette.types import Receive, Scope, Send

from runner_manager.dependencies import get_settings
from runner_manager.models.settings import Settings


class TrustedHostHealthRoutes(TrustedHostMiddleware):
    """A healthcheck endpoint that answers to GET requests on /_health"""

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """If the request is made on the path _health then execute the check on hosts"""
        if scope["path"] == "/_health/":
            print(scope)
            await super().__call__(scope, receive, send)
        else:
            await self.app(scope, receive, send)


api_key_query = APIKeyQuery(name="api-key", auto_error=False)
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)
settings = get_settings()


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
