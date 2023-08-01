from abc import ABC

from redis_om import EmbeddedJsonModel, JsonModel

from runner_manager.dependencies import get_redis, get_settings

redis = get_redis()
settings = get_settings()


class RedisModel(ABC):
    class Meta:
        database = redis
        global_key_prefix = settings.name
        abstract = True
        model_key_prefix = __build_class__.__name__.lower()


class BaseModel(JsonModel, RedisModel):
    pass


class EmbeddedBaseModel(EmbeddedJsonModel, RedisModel):
    pass
