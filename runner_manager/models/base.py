from typing import Optional

from redis import Redis
from redis_om import EmbeddedJsonModel, Field, JsonModel


class BaseModel(JsonModel):
    manager: Optional[str] = Field(
        default="runner-manager", index=True, full_text_search=True
    )

    class Meta:
        global_key_prefix: Optional[str] = "runner-manager"
        database: Optional[Redis] = None
        abstract = True
        model_key_prefix = __build_class__.__name__.lower()

    def __post_init_post_parse__(self):
        """Post init."""
        self.manager = self.Meta.global_key_prefix


class EmbeddedBaseModel(EmbeddedJsonModel):
    pass
