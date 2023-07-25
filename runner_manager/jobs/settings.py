from pydantic import RedisDsn

from runner_manager.dependencies import get_settings
from runner_manager.models.settings import Settings

settings: Settings = get_settings()

REDIS_URL: RedisDsn | None = settings.redis_om_url
