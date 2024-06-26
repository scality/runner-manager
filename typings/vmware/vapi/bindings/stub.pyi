"""
This type stub file was generated by pyright.
"""

from vmware.vapi.core import ApiInterface

"""
Stub helper classes
"""
__author__ = ...
__copyright__ = ...
logger = ...

class StubConfiguration:
    """
    Configuration data for vAPI stub classes

    :type connector: :class:`vmware.vapi.protocol.client.connector.Connector`
    :ivar connector: Connection to be used to talk to the remote ApiProvider
    """

    def __init__(self, connector, *error_types, **kwargs) -> None:
        """
        Initialize the stub configuration

        :type  connector: :class:
                          `vmware.vapi.protocol.client.connector.Connector`
        :param connector: Connection to be used to talk to the remote
                          ApiProvider
        :type  error_types: :class:`list` of :class:
                            `vmware.vapi.bindings.type.ErrorType`
        :param error_types: error types to be registered in this configuration
        :type kwargs: :class: `ResponseExtractor`
        :param kwargs: Extract rest http response status
        """
        ...

    @property
    def connector(self):
        """
        :rtype: :class:`vmware.vapi.protocol.client.connector.Connector`
        :return: Connection to be used to talk to the remote ApiProvider
        """
        ...

    @property
    def resolver(self):  # -> NameToTypeResolver:
        """
        Type resolver that can resolve canonical names to its binding types

        :rtype: :class:`vmware.vapi.bindings.common.NameToTypeResolver`
        :return: Type resolver
        """
        ...

    @property
    def response_extractor(self):  # -> ResponseExtractor | None:
        """
        Response extractor that can retrive the raw http response status and body    # pylint: disable=line-too-long

        :rtype: :class:`vmware.vapi.bindings.http_helper.ResponseExtractor`
        :return: Response extractor
        """
        ...

class ApiInterfaceStub(ApiInterface):
    """
    Stub class for Api Interface
    """

    def __init__(
        self, iface_name, config, operations, rest_metadata=..., is_vapi_rest=...
    ) -> None:
        """
        Initialize the ApiMethod skeleton object

        :type  iface_name: :class:`str`
        :param iface_name: Interface name
        :type  config: :class:`StubConfiguration`
        :param config: Configuration data for vAPI stubs
        :type  operations: :class:`dict`
        :param operations: Dictionary of operation name to operation information
        :type  rest_metadata: :class:`dict` of :class:`str` and
            :class::`vmware.vapi.lib.rest.OperationRestMetadata`
        :param rest_metadata: Dictionary of operation name to operation REST
            metadata
        :type  is_vapi_rest: :class:`bool`
        :param is_vapi_rest: Json message format. True for Vapi Rest and False
            for Swagger Rest
        """
        ...

    def get_identifier(self):  # -> InterfaceIdentifier:
        """
        Returns interface identifier

        :rtype: :class:`InterfaceIdentifier`
        :return: Interface identifier
        """
        ...

    def get_definition(self):  # -> InterfaceDefinition:
        """
        Returns interface definition

        :rtype: :class:`InterfaceDefinition`
        :return: Interface definition
        """
        ...

    def get_method_definition(self, method_id):  # -> MethodDefinition | None:
        ...

    def invoke(self, ctx, method_id, input_value):
        """
        Invokes the specified method using the execution context and
        the input provided

        :type  ctx: :class:`vmware.vapi.core.ExecutionContext`
        :param ctx: Execution context for this method
        :type  method_id: :class:`vmware.vapi.core.MethodIdentifier`
        :param method_id: Method identifier
        :type  input_value: :class:`vmware.vapi.data.value.StructValue`
        :param input_value: Method input parameters

        :rtype: :class:`vmware.vapi.core.MethodResult`
        :return: Result of the method invocation
        """
        ...

    def native_invoke(
        self, ctx, method_name, kwargs
    ):  # -> str | Any | StructValue | list[Any] | set[Any] | VapiStruct | UnresolvedError | datetime | Enum | dict[Any, Any] | None:
        """
        Invokes the method corresponding to the given method name
        with the kwargs.

        In this method, python native values are converted to vAPI
        runtime values, operation is invoked and the result are converted
        back to python native values

        :type  ctx: :class:`vmware.vapi.core.ExecutionContext`
        :param ctx: Execution context for this method
        :type  method_name: :class:`str`
        :param method_name: Method name
        :type  kwargs: :class:`dict`
        :param kwargs: arguments to be passed to the method
        :rtype: :class:`object`
        :return: Method result
        """
        ...

class VapiInterface:
    """
    vAPI Interface class is used by the python client side bindings. This
    encapsulates the ApiInterfaceStub instance
    """

    def __init__(self, config, api_interface) -> None:
        """
        Initialize VapiInterface object

        :type  config: :class:`StubConfiguration`
        :param config: Configuration data for vAPI stubs
        :type  api_interface: :class:`ApiInterfaceStub`
        :param api_interface: Instance of ApiInterfaceStub class that can
                              execute the ApiMethods
        """
        ...

class StubFactory:
    """
    Factory for client-side vAPI stubs
    """

    def __init__(self, config) -> None:
        """
        Initialize the stub factory

        :type  config: :class:`StubConfiguration`
        :param config: Configuration data for vAPI stubs
        """
        ...

    def create_stub(self, service_name):  # -> Any:
        """
        Create a stub corresponding to the specified service name

        :type  service_name: :class:`str`
        :param service_name: Name of the service

        :rtype: :class:`VapiInterface`
        :return: The stub correspoding to the specified service name
        """
        ...

class StubFactoryBase:
    """
    Class that represents a VMODL2 package and holds the stubs for services
    which are part of that package as well as stub factories of sub-packages

    :type _attrs: :class:`dict` of :class:`str` and
        (:class:`vmware.vapi.bindings.stub.VapiInterface` or :class:`str`)
    :cvar _attrs: Dictionary of service name and service stub or sub module name
        and string reprensenting the fully qualified class path
    """

    _attrs = ...
    def __init__(self, stub_config) -> None:
        """
        Initialize StubFactoryBase

        :type  stub_config: :class:`vmware.vapi.bindings.stub.StubConfiguration`
        :param stub_config: Stub config instance
        """
        ...

    def __getattribute__(self, name):  # -> Any | StubFactoryBase | VapiInterface:
        ...

class ApiClient:
    """
    Base Class that represents an api client that client binding users can use
    to access all the service stubs
    """

    def __init__(self, stub_factory) -> None:
        """
        Initialize ApiClient

        :type  stub_factory: :class:`vmware.vapi.bindings.stub.StubFactoryBase`
        :param stub_factory: Instance for the top level stub factory for the API
            component or product
        """
        ...

    def __getattr__(self, name):  # -> Any:
        ...

    def __dir__(self):  # -> list[str]:
        ...
