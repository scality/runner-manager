"""
This type stub file was generated by pyright.
"""

from vmware.vapi.lib.visitor import VapiVisitor

"""
Representation of an IDL type for the use of the Python language bindings.
"""
__author__ = ...
__copyright__ = ...
MAP_KEY_FIELD = ...
MAP_VALUE_FIELD = ...

class BindingType:
    """
    Representation of an IDL type for the use of the Python language bindings

    :type  definition: :class:`vmware.vapi.data.definition.DataDefinition`
    :param definition: Data definition corresponding to this binding type
    """

    def __init__(self) -> None: ...
    def accept(self, visitor):  # -> None:
        """
        Applies a visitor to this BindingType

        :type  visitor: :class:`BindingTypeVisitor`
        :param visitor: visitor operating on the BindingType
        """
        ...

    @property
    def definition(
        self,
    ):  # -> VoidDefinition | IntegerDefinition | DoubleDefinition | StringDefinition | BooleanDefinition | BlobDefinition | OptionalDefinition | ListDefinition | StructRefDefinition | StructDefinition | DynamicStructDefinition | AnyErrorDefinition | OpaqueDefinition | SecretDefinition | ErrorDefinition | None:
        """
        Generate the data defintion corresponding to this binding type
        """
        ...

class VoidType(BindingType):
    """
    Representation of void IDL type in Python Binding
    """

    def __init__(self) -> None: ...

class IntegerType(BindingType):
    """
    Representation of integer IDL Type in Python Binding
    """

    def __init__(self) -> None: ...

class DoubleType(BindingType):
    """
    Representation of float IDL Type in Python Binding
    """

    def __init__(self) -> None: ...

class StringType(BindingType):
    """
    Representation of string IDL Type in Python Binding
    """

    def __init__(self) -> None: ...

class SecretType(BindingType):
    """
    Representation of @secret IDL annotation in Python Binding. @secret
    annotation can only be applied to strings.
    """

    def __init__(self) -> None: ...

class BooleanType(BindingType):
    """
    Representation of boolean IDL Type in Python Binding
    """

    def __init__(self) -> None: ...

class BlobType(BindingType):
    """
    Representation of binary IDL Type in Python Binding
    """

    def __init__(self) -> None: ...

class OptionalType(BindingType):
    """
    Representation of optional IDL annotation in Python Binding

    :type element_type: :class:`BindingType`
    :ivar element_type: element type
    """

    def __init__(self, element_type) -> None: ...
    @property
    def element_type(self):  # -> BindingType:
        """
        Return the element type of this ListType

        :rtype: :class:`BindingType`
        :return: element type
        """
        ...

class ListType(BindingType):
    """
    Representation of List IDL type in Python Binding

    :type element_type: :class:`BindingType`
    :ivar element_type: element type
    """

    def __init__(self, element_type) -> None: ...
    @property
    def element_type(self):  # -> BindingType:
        """
        Return the element type of this ListType

        :rtype: :class:`BindingType`
        :return: element type
        """
        ...

class SetType(BindingType):
    """
    Representation of Set IDL type in Python Binding

    :type element_type: :class:`BindingType`
    :ivar element_type: element type
    """

    def __init__(self, element_type) -> None: ...
    @property
    def element_type(self):  # -> BindingType:
        """
        Return the element type of this SetType

        :rtype: :class:`BindingType`
        :return: element type
        """
        ...

class MapType(BindingType):
    """
    Representation of Map IDL type in Python Binding

    :type key_type: :class:`BindingType`
    :ivar key_type: map key type
    :type value_type: :class:`BindingType`
    :ivar value_type: map value type
    """

    def __init__(self, key_type, value_type) -> None: ...
    @property
    def key_type(self):  # -> BindingType:
        """
        Return the key type of this MapType

        :rtype: :class:`BindingType`
        :return: key type
        """
        ...

    @property
    def value_type(self):  # -> BindingType:
        """
        Return the value type of this MapType

        :rtype: :class:`BindingType`
        :return: value type
        """
        ...

class StructType(BindingType):
    """
    Representation of Structure IDL type in Python Binding

    :type name: :class:`str`
    :ivar name: Name of the structure
    :type binding_class: :class:`vmware.vapi.bindings.struct.VapiStruct`
    :ivar binding_class: Reference to the Python native class corresponding
                         to this structure
    :type is_model: :class:`bool`
    :ivar is_model: True if the structure is marked as Model, False otherwise
    :type model_keys: :class:`list` of :class:`str` or :class:`None`
    :ivar model_keys: List of model keys for the structure if it is marked as
        Model
    """

    def __init__(
        self, name, fields, binding_class=..., is_model=..., model_keys=...
    ) -> None: ...
    @property
    def name(self):  # -> str:
        """
        Returns the name of the StructType

        :rtype: :class:`str`
        :return: Name of the StructType
        """
        ...

    @property
    def binding_class(self):  # -> None:
        """
        Returns the reference to the Python native class
        corresponding to this structure

        :rtype: :class:`vmware.vapi.bindings.struct.VapiStruct`
        :return: Reference to the python native class
        """
        ...

    @property
    def is_model(self):  # -> bool:
        """
        Check if the Struct is marked as model

        :rtype: :class:`bool`
        :return: True if the Struct is marked as model, False otherwise
        """
        ...

    @property
    def model_keys(self):  # -> None:
        """
        Returns list of model keys for the Struct if it is marked as model

        :rtype: :class:`list` of :class:`str` or None
        :return: List of model keys for the Struct if it is marked as model
        """
        ...

    def get_field_names(self):  # -> list[Any]:
        """
        Returns the list of field names present in this StructType

        :rtype: :class:`list` of :class:`str`
        :return: List of field names
        """
        ...

    def get_field(self, field_name):  # -> None:
        """
        Returns the BindingType of the argument

        :type  field_name: :class:`str`
        :param field_name: Field name
        :rtype: :class:`BindingType`
        :return: BindingType of the field specified
        """
        ...

class ErrorType(StructType):
    """
    Representation of Error IDL type in Python Binding

    :type definition: :class:`vmware.vapi.data.ErrorDefinition`
    :ivar definition: type representation in the API runtime
    :type name: :class:`str`
    :ivar name: Name of the structure
    :type binding_class: :class:`vmware.vapi.bindings.error.VapiError`
    :ivar binding_class: Reference to the Python native class corresponding
                         to this error
    """

    def __init__(self, name, fields, binding_class=...) -> None: ...

class ReferenceType(BindingType):
    """
    Reference type to resolve references lazily.

    :type resolved_type: :class:`StructType` or :class:`EnumType`
    :ivar resolved_type: Resolved reference type
    """

    def __init__(self, context_name, type_name) -> None:
        """
        Initialize ReferenceType

        :type  context_name: :class:`str`
        :param context_name: Name of the module that has the type
        :type  type_name: :class:`str`
        :param type_name: Fully qualified name of the type reference. i.e.
            if the type Bar is nested inside type Foo, it would be Foo.Bar
        """
        ...

    @property
    def resolved_type(self):  # -> Any | None:
        """
        Returns the resolved struct type or enum type

        :rtype: :class:`StructType` or
            :class:`EnumType`
        :return: Resolved struct type or enum type
        """
        ...

class OpaqueType(BindingType):
    """
    Representation of Opaque IDL annotation in Python Binding
    """

    def __init__(self) -> None: ...

class DynamicStructType(StructType):
    """
    Representation of StructValue IDL annotation in Python Binding

    :type has_fields_of_type: :class:`ReferenceType`
    :ivar has_fields_of_type: List of reference types whose fields need to be
        present in the StructValue for this DynamicStruct type
    """

    def __init__(self, name, fields, binding_class=..., has_fields_of_type=...) -> None:
        """
        Initialize DynamicStructType

        :type  name: :class:`str`
        :param name: Name of the Structure
        :type  fields: :class:`dict` of :class:`str` and :class:`BindingType`
        :param fields: Map of field name and field binding type
        :type  binding_class:
            :class:`vmware.vapi.data.definition.DataDefinition`
        :param binding_class: Data definition for this type
        :type  has_fields_of_type: :class:`ReferenceType`
        :param has_fields_of_type: List of reference types whose fields need to
            be present in the StructValue for this DynamicStruct type
        """
        ...

    @property
    def has_fields_of_type(self):  # -> None:
        """
        Returns the has_fields_of_type

        :rtype  :class:`ReferenceType`
        :return List of reference types whose fields need to be present in the
            StructValue for this DynamicStruct type
        """
        ...

class AnyErrorType(BindingType):
    """
    Representation of Exception type in Python Binding
    """

    def __init__(self) -> None:
        """
        Initialize AnyErrorType
        """
        ...

class DateTimeType(BindingType):
    """
    Representation of datetime IDL Type in Python Binding
    """

    def __init__(self) -> None: ...

class URIType(BindingType):
    """
    Representation of URI IDL Type in Python Binding
    """

    def __init__(self) -> None: ...

class EnumType(BindingType):
    """
    Representation of enum IDL Type in Python Binding

    :type name: :class:`str`
    :ivar name: Name of the enum
    :type binding_class: :class:`vmware.vapi.bindings.struct.VapiStruct`
    :ivar binding_class: Reference to the Python native class corresponding
                         to this structure
    """

    def __init__(self, name, binding_class) -> None: ...
    @property
    def name(self):  # -> Any:
        """
        Returns the name of the EnumType

        :rtype: :class:`str`
        :return: Name of the EnumType
        """
        ...

    @property
    def binding_class(self):  # -> Any:
        """
        Returns the reference to the Python native class
        corresponding to this structure
        """
        ...

class IdType(BindingType):
    """
    Representation of ID IDL type in Python Binding

    :type resolved_types: :class:`list` of :class:`str` or :class:`str` or
        :class:`None`
    :ivar resolved_types: Resource type(s) for the ID
    :type resource_type_field_name: :class:`str` or :class:`None`
    :ivar resource_type_field_name: Name of the field specifying the resource
        type
    """

    def __init__(self, resource_types=..., resource_type_field_name=...) -> None: ...
    @property
    def resource_types(self):  # -> None:
        """
        Returns the Resource type(s) for the ID field

        :rtype: :class:`list` of :class:`str` or :class:`str` or :class:`None`
        :return: Resource type(s) for the ID
        """
        ...

    @property
    def resource_type_field_name(self):  # -> None:
        """
        Returns the name of the field specifying the resource type

        :rtype: :class:`str`
        :return: Name of the field specifying the resource type
        """
        ...

class BindingTypeVisitor(VapiVisitor):
    """
    Base no-op implementation of a BindingType visitor
    """

    def __init__(self) -> None:
        """
        Initialize BindingTypeVisitor
        """
        ...

    def visit_void(self, typ):
        """
        Visit a void value (i.e. None)

        :type  typ: :class:`VoidType`
        :param typ: Binding type of the value
        """
        ...

    def visit_integer(self, typ):
        """
        Visit an integer value

        :type  typ: :class:`IntegerType`
        :param typ: Binding type of the value
        """
        ...

    def visit_double(self, typ):
        """
        Visit a double value

        :type  typ: :class:`DoubleType`
        :param typ: Binding type of the value
        """
        ...

    def visit_string(self, typ):
        """
        Visit a string value

        :type  typ: :class:`StringType`
        :param typ: Binding type of the value
        """
        ...

    def visit_boolean(self, typ):
        """
        Visit a boolean value

        :type  typ: :class:`BooleanType`
        :param typ: Binding type of the value
        """
        ...

    def visit_blob(self, typ):
        """
        Visit a blob value

        :type  typ: :class:`BlobType`
        :param typ: Binding type of the value
        """
        ...

    def visit_optional(self, typ):
        """
        Visit an optional value

        :type  typ: :class:`OptionalType`
        :param typ: Binding type of the value
        """
        ...

    def visit_list(self, typ):
        """
        Visit a list value

        :type  typ: :class:`ListType`
        :param typ: Binding type of the value
        """
        ...

    def visit_struct(self, typ):
        """
        Visit a struct value

        :type  typ: :class:`StructType`
        :param typ: Binding type of the value
        """
        ...

    def visit_dynamic_struct(self, typ):
        """
        Visit a struct value

        :type  typ: :class:`DynamicStructType`
        :param typ: Binding type of the value
        """
        ...

    def visit_any_error(self, typ):
        """
        Visit an error value

        :type  typ: :class:`AnyErrorType`
        :param typ: Binding type of the value
        """
        ...

    def visit_opaque(self, typ):
        """
        Visit an opaque value.

        :type  typ: :class:`OpaqueType`
        :param typ: Binding type of the value
        """
        ...

    def visit_secret(self, typ):
        """
        Visit a secret value

        :type  typ: :class:`SecretType`
        :param typ: Binding type of the value
        """
        ...

    def visit_date_time(self, typ):
        """
        Visit a datetime value

        :type  typ: :class:`DateTimeType`
        :param typ: Binding type of the value
        """
        ...

    def visit_uri(self, typ):
        """
        Visit an URI value

        :type  typ: :class:`URIType`
        :param typ: Binding type of the value
        """
        ...

    def visit_enum(self, typ):
        """
        Visit a enum value

        :type  typ: :class:`EnumType`
        :param typ: Binding type of the value
        """
        ...

    def visit_error(self, typ):
        """
        Visit an error type

        :type  typ: :class:`ErrorType`
        :param typ: Binding type of the value
        """
        ...

    def visit_reference(self, typ):
        """
        Visit a reference type

        :type  typ: :class:`ReferenceType`
        :param typ: Binding type of the value
        """
        ...

    def visit_id(self, typ):
        """
        Visit a ID value

        :type  typ: :class:`IdType`
        :param typ: Binding type of the value
        """
        ...

class DataDefinitionBuilder(BindingTypeVisitor):
    """
    Builds DataDefinition by visiting a BindingType
    """

    def __init__(self, ctx, seen_structures) -> None:
        """
        Initialize DataDefinitionBuilder

        :type  ctx: :class:`vmware.vapi.data.definition.ReferenceResolver`
        :param ctx: Data definition reference resolver object
        :type  seen_structures: :class:`list` or :class:`str`
        :param seen_structures: List of structures seen
        """
        ...

    def get_out_value(
        self,
    ):  # -> VoidDefinition | IntegerDefinition | DoubleDefinition | StringDefinition | BooleanDefinition | BlobDefinition | OptionalDefinition | ListDefinition | StructRefDefinition | StructDefinition | DynamicStructDefinition | AnyErrorDefinition | OpaqueDefinition | SecretDefinition | ErrorDefinition | None:
        """
        Returns the data definition

        :rtype: :class:`vmware.vapi.data.definition.DataDefinition`
        :return: Data definition
        """
        ...

    def visit_void(self, typ):  # -> None:
        """
        Visit a void value (i.e. None)

        :type  typ: :class:`VoidType`
        :param typ: Binding type of the value
        """
        ...

    def visit_integer(self, typ):  # -> None:
        """
        Visit an integer value

        :type  typ: :class:`IntegerType`
        :param typ: Binding type of the value
        """
        ...

    def visit_double(self, typ):  # -> None:
        """
        Visit a double value

        :type  typ: :class:`DoubleType`
        :param typ: Binding type of the value
        """
        ...

    def visit_string(self, typ):  # -> None:
        """
        Visit a string value

        :type  typ: :class:`StringType`
        :param typ: Binding type of the value
        """
        ...

    def visit_boolean(self, typ):  # -> None:
        """
        Visit a boolean value

        :type  typ: :class:`BooleanType`
        :param typ: Binding type of the value
        """
        ...

    def visit_blob(self, typ):  # -> None:
        """
        Visit a blob value

        :type  typ: :class:`BlobType`
        :param typ: Binding type of the value
        """
        ...

    def visit_optional(self, typ):  # -> None:
        """
        Visit an optional value

        :type  typ: :class:`OptionalType`
        :param typ: Binding type of the value
        """
        ...

    def visit_list(self, typ):  # -> None:
        """
        Visit a list value

        :type  typ: :class:`ListType`
        :param typ: Binding type of the value
        """
        ...

    def visit_set(self, typ):  # -> None:
        """
        Visit a set value

        :type  typ: :class:`SetType`
        :param typ: Binding type of the value
        """
        ...

    def visit_map(self, typ):  # -> None:
        """
        Visit a map value

        :type  typ: :class:`MapType`
        :param typ: Binding type of the value
        """
        ...

    def visit_struct(self, typ):  # -> None:
        """
        Visit a struct value

        :type  typ: :class:`StructType`
        :param typ: Binding type of the value
        """
        ...

    def visit_dynamic_struct(self, typ):  # -> None:
        """
        Visit a struct value

        :type  typ: :class:`DynamicStructType`
        :param typ: Binding type of the value
        """
        ...

    def visit_any_error(self, typ):  # -> None:
        """
        Visit an error value

        :type  typ: :class:`AnyErrorType`
        :param typ: Binding type of the value
        """
        ...

    def visit_opaque(self, typ):  # -> None:
        """
        Visit an opaque value.

        :type  typ: :class:`OpaqueType`
        :param typ: Binding type of the value
        """
        ...

    def visit_secret(self, typ):  # -> None:
        """
        Visit a secret value

        :type  typ: :class:`SecretType`
        :param typ: Binding type of the value
        """
        ...

    def visit_date_time(self, typ):  # -> None:
        """
        Visit a datetime value

        :type  typ: :class:`DateTimeType`
        :param typ: Binding type of the value
        """
        ...

    def visit_uri(self, typ):  # -> None:
        """
        Visit an URI value

        :type  typ: :class:`URIType`
        :param typ: Binding type of the value
        """
        ...

    def visit_enum(self, typ):  # -> None:
        """
        Visit a enum value

        :type  typ: :class:`EnumType`
        :param typ: Binding type of the value
        """
        ...

    def visit_reference(self, typ):  # -> None:
        """
        Visit a reference type

        :type  typ: :class:`ReferenceType`
        :param typ: Binding type of the value
        """
        ...

    def visit_error(self, typ):  # -> None:
        """
        Visit an error type

        :type  typ: :class:`ErrorType`
        :param typ: Binding type of the value
        """
        ...

    def visit_id(self, typ):  # -> None:
        """
        Visit a ID value

        :type  typ: :class:`IdType`
        :param typ: Binding type of the value
        """
        ...

class TypeUtil:
    """
    Converts a BindingType object to DataDefinition object
    """

    @staticmethod
    def convert_to_data_definition(
        binding_type,
    ):  # -> VoidDefinition | IntegerDefinition | DoubleDefinition | StringDefinition | BooleanDefinition | BlobDefinition | OptionalDefinition | ListDefinition | StructRefDefinition | StructDefinition | DynamicStructDefinition | AnyErrorDefinition | OpaqueDefinition | SecretDefinition | ErrorDefinition | None:
        """
        Converts a BindingType object to DataDefinition object

        :type  binding_type: :class:`BindingType`
        :param binding_type: Binding type
        :rtype: :class:`vmware.vapi.data.definition.DataDefinition`
        :return: DataDefinition
        """
        ...