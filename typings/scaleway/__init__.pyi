from typing import Optional

class Client:
    def __init__(
        self,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        api_url: str = "https://api.scaleway.com",
        api_allow_insecure: bool = False,
        user_agent: str = ...,
        default_organization_id: Optional[str] = None,
        default_project_id: Optional[str] = None,
        default_region: Optional[str] = None,
        default_zone: Optional[str] = None,
        default_page_size: Optional[int] = None,
    ) -> None: ...
