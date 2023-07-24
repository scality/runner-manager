from abc import ABC
from redis_om import JsonModel

# from redis import Redis
from runner_manager.dependencies import get_redis


# redis_connection = Redis.from_url(str(settings.redis_om_url))
redis = get_redis()


class BaseModel(JsonModel, ABC):
    class Meta:
        database = redis
        global_key_prefix = "runner-manager"
        abstract = True
        model_key_prefix = "base-model"

