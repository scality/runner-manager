from abc import ABC

from redis_om import EmbeddedJsonModel, JsonModel


class BaseModel(JsonModel, ABC):
    class Meta:
        global_key_prefix = "runner-manager"
        abstract = True
        model_key_prefix = __build_class__.__name__.lower()


class EmbeddedBaseModel(EmbeddedJsonModel):
    pass
