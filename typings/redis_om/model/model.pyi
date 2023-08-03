"""
This type stub file was generated by pyright.
"""

import abc
import dataclasses
from enum import Enum
from typing import AbstractSet, Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple, Type, TypeVar, Union
from typing_extensions import Protocol
from .. import redis
from .._compat import BaseModel, FieldInfo as PydanticFieldInfo, ModelField, ModelMetaclass, NoArgAnyCallable, Representation, UndefinedType, validator

model_registry = ...
_T = TypeVar("_T")
Model = TypeVar("Model", bound="RedisModel")
log = ...
escaper = ...
SINGLE_VALUE_TAG_FIELD_SEPARATOR = ...
DEFAULT_REDISEARCH_FIELD_SEPARATOR = ...
ERRORS_URL = ...
class RedisModelError(Exception):
    """Raised when a problem exists in the definition of a RedisModel."""
    ...


class QuerySyntaxError(Exception):
    """Raised when a query is constructed improperly."""
    ...


class NotFoundError(Exception):
    """Raised when a query found no results."""
    ...


class Operators(Enum):
    EQ = ...
    NE = ...
    LT = ...
    LE = ...
    GT = ...
    GE = ...
    OR = ...
    AND = ...
    NOT = ...
    IN = ...
    NOT_IN = ...
    LIKE = ...
    ALL = ...
    def __str__(self) -> str:
        ...
    


ExpressionOrModelField = Union["Expression", "NegatedExpression", ModelField]
def embedded(cls): # -> None:
    """
    Mark a model as embedded to avoid creating multiple indexes if the model is
    only ever used embedded within other models.
    """
    ...

def is_supported_container_type(typ: Optional[type]) -> bool:
    ...

def validate_model_fields(model: Type[RedisModel], field_values: Dict[str, Any]): # -> None:
    ...

def decode_redis_value(obj: Union[List[bytes], Dict[bytes, bytes], bytes], encoding: str) -> Union[List[str], Dict[str, str], str]:
    """Decode a binary-encoded Redis hash into the specified encoding."""
    ...

def remove_prefix(value: str, prefix: str) -> str:
    """Remove a prefix from a string."""
    ...

class PipelineError(Exception):
    """A Redis pipeline error."""
    ...


def verify_pipeline_response(response: List[Union[bytes, str]], expected_responses: int = ...): # -> None:
    ...

@dataclasses.dataclass
class NegatedExpression:
    """A negated Expression object.

    For now, this is a separate dataclass from Expression that acts as a facade
    around an Expression, indicating to model code (specifically, code
    responsible for querying) to negate the logic in the wrapped Expression. A
    better design is probably possible, maybe at least an ExpressionProtocol?
    """
    expression: Expression
    def __invert__(self): # -> Expression:
        ...
    
    def __and__(self, other): # -> Expression:
        ...
    
    def __or__(self, other): # -> Expression:
        ...
    
    @property
    def left(self): # -> ExpressionOrModelField | None:
        ...
    
    @property
    def right(self): # -> ExpressionOrModelField | None:
        ...
    
    @property
    def op(self): # -> Operators:
        ...
    
    @property
    def name(self): # -> str:
        ...
    
    @property
    def tree(self): # -> str:
        ...
    


@dataclasses.dataclass
class Expression:
    op: Operators
    left: Optional[ExpressionOrModelField]
    right: Optional[ExpressionOrModelField]
    parents: List[Tuple[str, RedisModel]]
    def __invert__(self): # -> NegatedExpression:
        ...
    
    def __and__(self, other: ExpressionOrModelField): # -> Expression:
        ...
    
    def __or__(self, other: ExpressionOrModelField): # -> Expression:
        ...
    
    @property
    def name(self): # -> str:
        ...
    
    @property
    def tree(self): # -> str:
        ...
    


@dataclasses.dataclass
class KNNExpression:
    k: int
    vector_field: ModelField
    reference_vector: bytes
    def __str__(self) -> str:
        ...
    
    @property
    def query_params(self) -> Dict[str, Union[str, bytes]]:
        ...
    
    @property
    def score_field(self) -> str:
        ...
    


ExpressionOrNegated = Union[Expression, NegatedExpression]
class ExpressionProxy:
    def __init__(self, field: ModelField, parents: List[Tuple[str, RedisModel]]) -> None:
        ...
    
    def __eq__(self, other: Any) -> Expression:
        ...
    
    def __ne__(self, other: Any) -> Expression:
        ...
    
    def __lt__(self, other: Any) -> Expression:
        ...
    
    def __le__(self, other: Any) -> Expression:
        ...
    
    def __gt__(self, other: Any) -> Expression:
        ...
    
    def __ge__(self, other: Any) -> Expression:
        ...
    
    def __mod__(self, other: Any) -> Expression:
        ...
    
    def __lshift__(self, other: Any) -> Expression:
        ...
    
    def __rshift__(self, other: Any) -> Expression:
        ...
    
    def __getattr__(self, item): # -> ExpressionProxy | Any:
        ...
    


class QueryNotSupportedError(Exception):
    """The attempted query is not supported."""
    ...


class RediSearchFieldTypes(Enum):
    TEXT = ...
    TAG = ...
    NUMERIC = ...
    GEO = ...


NUMERIC_TYPES = ...
DEFAULT_PAGE_SIZE = ...
class FindQuery:
    def __init__(self, expressions: Sequence[ExpressionOrNegated], model: Type[RedisModel], knn: Optional[KNNExpression] = ..., offset: int = ..., limit: Optional[int] = ..., page_size: int = ..., sort_fields: Optional[List[str]] = ..., nocontent: bool = ...) -> None:
        ...
    
    def dict(self) -> Dict[str, Any]:
        ...
    
    def copy(self, **kwargs): # -> FindQuery:
        ...
    
    @property
    def pagination(self): # -> List[str]:
        ...
    
    @property
    def expression(self): # -> Any | Expression:
        ...
    
    @property
    def query(self): # -> str:
        """
        Resolve and return the RediSearch query for this FindQuery.

        NOTE: We cache the resolved query string after generating it. This should be OK
        because all mutations of FindQuery through public APIs return a new FindQuery instance.
        """
        ...
    
    @property
    def query_params(self): # -> list[str | bytes]:
        ...
    
    def validate_sort_fields(self, sort_fields: List[str]): # -> List[str]:
        ...
    
    @staticmethod
    def resolve_field_type(field: ModelField, op: Operators) -> RediSearchFieldTypes:
        ...
    
    @staticmethod
    def expand_tag_value(value): # -> str | bytes:
        ...
    
    @classmethod
    def resolve_value(cls, field_name: str, field_type: RediSearchFieldTypes, field_info: PydanticFieldInfo, op: Operators, value: Any, parents: List[Tuple[str, RedisModel]]) -> str:
        ...
    
    def resolve_redisearch_pagination(self): # -> list[Unknown]:
        """Resolve pagination options for a query."""
        ...
    
    def resolve_redisearch_sort_fields(self): # -> list[Unknown] | None:
        """Resolve sort options for a query."""
        ...
    
    @classmethod
    def resolve_redisearch_query(cls, expression: ExpressionOrNegated) -> str:
        """
        Resolve an arbitrarily deep expression into a single RediSearch query string.

        This method is complex. Note the following:

        1. This method makes a recursive call to itself when it finds that
           either the left or right operand contains another expression.

        2. An expression might be in a "negated" form, which means that the user
           gave us an expression like ~(Member.age == 30), or in other words,
           "Members whose age is NOT 30." Thus, a negated expression is one in
           which the meaning of an expression is inverted. If we find a negated
           expression, we need to add the appropriate "NOT" syntax but can
           otherwise use the resolved RediSearch query for the expression as-is.

        3. The final resolution of an expression should be a left operand that's
           a ModelField, an operator, and a right operand that's NOT a ModelField.
           With an IN or NOT_IN operator, the right operand can be a sequence
           type, but otherwise, sequence types are converted to strings.

        TODO: When the operator is not IN or NOT_IN, detect a sequence type (other
         than strings, which are allowed) and raise an exception.
        """
        ...
    
    def execute(self, exhaust_results=..., return_raw_result=...): # -> List[RedisModel]:
        ...
    
    def first(self): # -> RedisModel:
        ...
    
    def count(self): # -> RedisModel:
        ...
    
    def all(self, batch_size=...): # -> List[RedisModel]:
        ...
    
    def page(self, offset=..., limit=...): # -> List[RedisModel]:
        ...
    
    def sort_by(self, *fields: str): # -> Self@FindQuery | FindQuery:
        ...
    
    def update(self, use_transaction=..., **field_values): # -> None:
        """
        Update models that match this query to the given field-value pairs.

        Keys and values given as keyword arguments are interpreted as fields
        on the target model and the values as the values to which to set the
        given fields.
        """
        ...
    
    def delete(self): # -> int:
        """Delete all matching records in this query."""
        ...
    
    def __iter__(self): # -> Generator[RedisModel | Unknown, Any, None]:
        ...
    
    def __getitem__(self, item: int): # -> RedisModel:
        """
        Given this code:
            Model.find()[1000]

        We should return only the 1000th result.

            1. If the result is loaded in the query cache for this query,
               we can return it directly from the cache.

            2. If the query cache does not have enough elements to return
               that result, then we should clone the current query and
               give it a new offset and limit: offset=n, limit=1.
        """
        ...
    
    def get_item(self, item: int): # -> RedisModel:
        """
        Given this code:
            await Model.find().get_item(1000)

        We should return only the 1000th result.

            1. If the result is loaded in the query cache for this query,
               we can return it directly from the cache.

            2. If the query cache does not have enough elements to return
               that result, then we should clone the current query and
               give it a new offset and limit: offset=n, limit=1.

        NOTE: This method is included specifically for async users, who
        cannot use the notation Model.find()[1000].
        """
        ...
    


class PrimaryKeyCreator(Protocol):
    def create_pk(self, *args, **kwargs) -> str:
        """Create a new primary key"""
        ...
    


class UlidPrimaryKey:
    """
    A client-side generated primary key that follows the ULID spec.
    https://github.com/ulid/javascript#specification
    """
    @staticmethod
    def create_pk(*args, **kwargs) -> str:
        ...
    


def __dataclass_transform__(*, eq_default: bool = ..., order_default: bool = ..., kw_only_default: bool = ..., field_descriptors: Tuple[Union[type, Callable[..., Any]], ...] = ...) -> Callable[[_T], _T]:
    ...

class FieldInfo(PydanticFieldInfo):
    def __init__(self, default: Any = ..., **kwargs: Any) -> None:
        ...
    


class RelationshipInfo(Representation):
    def __init__(self, *, back_populates: Optional[str] = ..., link_model: Optional[Any] = ...) -> None:
        ...
    


@dataclasses.dataclass
class VectorFieldOptions:
    class ALGORITHM(Enum):
        FLAT = ...
        HNSW = ...
    
    
    class TYPE(Enum):
        FLOAT32 = ...
        FLOAT64 = ...
    
    
    class DISTANCE_METRIC(Enum):
        L2 = ...
        IP = ...
        COSINE = ...
    
    
    algorithm: ALGORITHM
    type: TYPE
    dimension: int
    distance_metric: DISTANCE_METRIC
    initial_cap: Optional[int] = ...
    block_size: Optional[int] = ...
    m: Optional[int] = ...
    ef_construction: Optional[int] = ...
    ef_runtime: Optional[int] = ...
    epsilon: Optional[float] = ...
    @staticmethod
    def flat(type: TYPE, dimension: int, distance_metric: DISTANCE_METRIC, initial_cap: Optional[int] = ..., block_size: Optional[int] = ...): # -> VectorFieldOptions:
        ...
    
    @staticmethod
    def hnsw(type: TYPE, dimension: int, distance_metric: DISTANCE_METRIC, initial_cap: Optional[int] = ..., m: Optional[int] = ..., ef_construction: Optional[int] = ..., ef_runtime: Optional[int] = ..., epsilon: Optional[float] = ...): # -> VectorFieldOptions:
        ...
    
    @property
    def schema(self): # -> str:
        ...
    


def Field(default: Any = ..., *, default_factory: Optional[NoArgAnyCallable] = ..., alias: str = ..., title: str = ..., description: str = ..., exclude: Union[AbstractSet[Union[int, str]], Mapping[Union[int, str], Any], Any] = ..., include: Union[AbstractSet[Union[int, str]], Mapping[Union[int, str], Any], Any] = ..., const: bool = ..., gt: float = ..., ge: float = ..., lt: float = ..., le: float = ..., multiple_of: float = ..., min_items: int = ..., max_items: int = ..., min_length: int = ..., max_length: int = ..., allow_mutation: bool = ..., regex: str = ..., primary_key: bool = ..., sortable: Union[bool, UndefinedType] = ..., index: Union[bool, UndefinedType] = ..., full_text_search: Union[bool, UndefinedType] = ..., vector_options: Optional[VectorFieldOptions] = ..., schema_extra: Optional[Dict[str, Any]] = ...) -> Any:
    ...

@dataclasses.dataclass
class PrimaryKey:
    name: str
    field: ModelField
    ...


class BaseMeta(Protocol):
    global_key_prefix: str
    model_key_prefix: str
    primary_key_pattern: str
    database: redis.Redis
    primary_key: PrimaryKey
    primary_key_creator_cls: Type[PrimaryKeyCreator]
    index_name: str
    embedded: bool
    encoding: str
    ...


@dataclasses.dataclass
class DefaultMeta:
    """A default placeholder Meta object.

    TODO: Revisit whether this is really necessary, and whether making
     these all optional here is the right choice.
    """
    global_key_prefix: Optional[str] = ...
    model_key_prefix: Optional[str] = ...
    primary_key_pattern: Optional[str] = ...
    database: Optional[redis.Redis] = ...
    primary_key: Optional[PrimaryKey] = ...
    primary_key_creator_cls: Optional[Type[PrimaryKeyCreator]] = ...
    index_name: Optional[str] = ...
    embedded: Optional[bool] = ...
    encoding: str = ...


class ModelMeta(ModelMetaclass):
    _meta: BaseMeta
    def __new__(cls, name, bases, attrs, **kwargs):
        ...
    


class RedisModel(BaseModel, abc.ABC, metaclass=ModelMeta):
    pk: Optional[str] = ...
    Meta = DefaultMeta
    class Config:
        orm_mode = ...
        arbitrary_types_allowed = ...
        extra = ...
    
    
    def __init__(__pydantic_self__, **data: Any) -> None:
        ...
    
    def __lt__(self, other) -> bool:
        """Default sort: compare primary key of models."""
        ...
    
    def key(self): # -> str:
        """Return the Redis key for this model."""
        ...
    
    @classmethod
    def delete(cls, pk: Any, pipeline: Optional[redis.client.Pipeline] = ...) -> int:
        """Delete data at this key."""
        ...
    
    @classmethod
    def get(cls: Type[Model], pk: Any) -> Model:
        ...
    
    def update(self, **field_values):
        """Update this model instance with the specified key-value pairs."""
        ...
    
    def save(self: Model, pipeline: Optional[redis.client.Pipeline] = ...) -> Model:
        ...
    
    def expire(self, num_seconds: int, pipeline: Optional[redis.client.Pipeline] = ...): # -> None:
        ...
    
    @validator("pk", always=True, allow_reuse=True)
    def validate_pk(cls, v):
        ...
    
    @classmethod
    def validate_primary_key(cls): # -> None:
        """Check for a primary key. We need one (and only one)."""
        ...
    
    @classmethod
    def make_key(cls, part: str): # -> str:
        ...
    
    @classmethod
    def make_primary_key(cls, pk: Any): # -> str:
        """Return the Redis key for this model."""
        ...
    
    @classmethod
    def db(cls): # -> Redis:
        ...
    
    @classmethod
    def find(cls, *expressions: Union[Any, Expression], knn: Optional[KNNExpression] = ...) -> FindQuery:
        ...
    
    @classmethod
    def from_redis(cls, res: Any): # -> list[Unknown]:
        ...
    
    @classmethod
    def get_annotations(cls): # -> dict[Unknown, Unknown]:
        ...
    
    @classmethod
    def add(cls: Type[Model], models: Sequence[Model], pipeline: Optional[redis.client.Pipeline] = ..., pipeline_verifier: Callable[..., Any] = ...) -> Sequence[Model]:
        ...
    
    @classmethod
    def delete_many(cls, models: Sequence[RedisModel], pipeline: Optional[redis.client.Pipeline] = ...) -> int:
        ...
    
    @classmethod
    def redisearch_schema(cls):
        ...
    
    def check(self): # -> None:
        """Run all validations."""
        ...
    


class HashModel(RedisModel, abc.ABC):
    def __init_subclass__(cls, **kwargs): # -> None:
        ...
    
    def save(self: Model, pipeline: Optional[redis.client.Pipeline] = ...) -> Model:
        ...
    
    @classmethod
    def all_pks(cls): # -> Generator[str, None, None]:
        ...
    
    @classmethod
    def get(cls: Type[Model], pk: Any) -> Model:
        ...
    
    @classmethod
    def redisearch_schema(cls): # -> str:
        ...
    
    def update(self, **field_values): # -> None:
        ...
    
    @classmethod
    def schema_for_fields(cls): # -> list[Unknown]:
        ...
    
    @classmethod
    def schema_for_type(cls, name, typ: Any, field_info: PydanticFieldInfo): # -> str | LiteralString:
        ...
    


class JsonModel(RedisModel, abc.ABC):
    def __init_subclass__(cls, **kwargs): # -> None:
        ...
    
    def __init__(self, *args, **kwargs) -> None:
        ...
    
    def save(self: Model, pipeline: Optional[redis.client.Pipeline] = ...) -> Model:
        ...
    
    @classmethod
    def all_pks(cls): # -> Generator[str, None, None]:
        ...
    
    def update(self, **field_values): # -> None:
        ...
    
    @classmethod
    def get(cls: Type[Model], pk: Any) -> Model:
        ...
    
    @classmethod
    def redisearch_schema(cls): # -> str:
        ...
    
    @classmethod
    def schema_for_fields(cls): # -> list[Unknown]:
        ...
    
    @classmethod
    def schema_for_type(cls, json_path: str, name: str, name_prefix: str, typ: Any, field_info: PydanticFieldInfo, parent_type: Optional[Any] = ...) -> str:
        ...
    


class EmbeddedJsonModel(JsonModel, abc.ABC):
    class Meta:
        embedded = ...
    
    


