from typing import Optional

from redis import Redis
from redis_om import EmbeddedJsonModel, JsonModel


class BaseModel(JsonModel):
    class Meta:
        global_key_prefix = "runner-manager"
        database: Optional[Redis] = None
        abstract = True
        model_key_prefix = __build_class__.__name__.lower()


class EmbeddedBaseModel(EmbeddedJsonModel):
    pass
