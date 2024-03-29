"""
This type stub file was generated by pyright.
"""

"""
Bindings data classes
"""
__author__ = ...
__copyright__ = ...

class VapiStruct:
    """
    Representation of IDL Structure in python language bindings
    """

    _validator_list = ...
    _canonical_to_pep_names = ...
    def __init__(self, struct_value=..., rest_converter_mode=...) -> None:
        """
        Initialize VapiStruct

        :type  mappings: :class:`dict` or :class:`None`
        :param mappings: A mapping for all field names whose canonical name does
                         not match PEP8 standard name
        :type  rest_converter_mode: :class:`str` or :class:`None`
        :param rest_converter_mode: Converter mode to be used to be be
            compatible for Vapi Rest. If None or unknown string value,
            then the default Json Rpc converter is used
        :type  struct_value: :class:`vmware.vapi.data.value.StructValue`
        :param struct_value: StructValue to be used for VapiStruct
            or :class:`None`
        """
        ...

    def get_field(self, attr):  # -> Any:
        """
        Returns the struct field value

        :type  attr: :class:`str`
        :param attr: Canonical field name
        :rtype: :class:`object`
        :return: Field value
        """
        ...

    @classmethod
    def validate_struct_value(cls, struct_value):  # -> None:
        """
        Validate if the given struct value satisfies all
        the constraints of this VapiStruct.

        :type  struct_value: :class:`vmware.vapi.data.value.StructValue`
        :param struct_value: StructValue to be validated
        :type  validators: :class:`list` of
            :class:`vmware.vapi.data.validator.Validator`
        :param validators: List of validators
        :raise :class:`vmware.vapi.exception.CoreException` if a constraint is
            not satisfied
        """
        ...

    def validate_constraints(self):  # -> None:
        """
        Validate if the current VapiStruct instance satisfies all the
        constraints of this VapiStruct type.

        :raise :class:`vmware.vapi.exception.CoreException` if a constraint is
            not satisfied
        """
        ...

    @classmethod
    def get_binding_type(cls):  # -> Any | None:
        """
        Returns the corresponding BindingType for the VapiStruct class

        :rtype: :class:`vmware.vapi.bindings.type.BindingType`
        :return: BindingType for this VapiStruct
        """
        ...

    def get_struct_value(self):  # -> StructValue:
        """
        Returns the corresponding StructValue for the VapiStruct class

        :rtype: :class:`vmware.vapi.data.value.StructValue`
        :return: StructValue for this VapiStruct
        """
        ...

    def convert_to(
        self, cls
    ):  # -> str | Any | StructValue | list[Any] | set[Any] | VapiStruct | UnresolvedError | datetime | Enum | dict[Any, Any] | None:
        """
        Convert the underlying StructValue to an instance of the provided class
        if possible.  Conversion will be possible if the StructValue contains
        all the fields expected by the provided class and the type of the value
        in each fields matches the type of the field expected by the provided
        class.

        :type  cls: :class:`vmware.vapi.data.value.StructValue`
        :param cls: The type to convert to
        :rtype: :class:'vmware.vapi.bindings.struct.VapiStruct'
        :return: The converted value
        """
        ...

    def to_json(self):  # -> str:
        """
        Convert the object into a json string.

        :rtype: :class:`str`
        :return: JSON string representation of this object
        """
        ...

    def to_dict(self):  # -> Any:
        """
        Convert the object into a python dictionary. Even the nested types
        are converted to dictionaries.

        :rtype: :class:`dict`
        :return: Dictionary representation of this object
        """
        ...

    def __eq__(self, other) -> bool: ...
    def __ne__(self, other) -> bool: ...
    def __repr__(self):  # -> str:
        ...

    def __str__(self) -> str: ...
    def __hash__(self) -> int: ...

class PrettyPrinter:
    """
    Helper class to pretty print Python native values (with special support
    for VapiStruct objects).
    """

    def __init__(self, stream=..., indent=...) -> None:
        """
        Initialize PrettyPrinter

        :type  stream: :class:`object`
        :param stream: A stream object that implements File protocol's
            write operation
        :type  indent: :class:`int`
        :param indent: Indentation to be used for new lines
        """
        ...

    def pprint(self, value, level=...):  # -> None:
        """
        Print a Python native value

        :type  value: :class:`vmware.vapi.bindings.struct.VapiStruct`
        :param value: VapiStruct to be pretty printed
        :type  level: :class:`int`
        :param level: Indentation level
        """
        ...