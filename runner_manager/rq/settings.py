from runner_manager.models.settings import Settings

settings = Settings()

REDIS_URL = settings.redis_om_url
