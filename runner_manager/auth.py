
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.types import Receive, Scope, Send


class TrustedHostHealthRoutes(TrustedHostMiddleware):
    """A healthcheck endpoint that answers to GET requests on /_health"""


    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """If the request is made on the path _health then execute the check on hosts"""
        if scope["path"] == "/_health/":
            print(scope)
            await super().__call__(scope, receive, send)
        else:
            await self.app(scope, receive, send)
