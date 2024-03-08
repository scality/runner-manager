"""
This type stub file was generated by pyright.
"""

"""
vAPI CoreException Class
"""
__author__ = ...
__copyright__ = ...
class CoreException(Exception):
    """
    This exception is raised by various components of the vAPI runtime
    infrastructure to indicate failures in that infrastructure.

    Server-side the exception is caught by specific components and an
    internal_server_error is reported to the client that invoked the
    request.  Client-side the exception may be raised for certain failures
    before a request was sent to the server or after the response was
    received from the server.  Similarly, server-side the exception may
    be raised for failures that occur when a provider implementation
    invokes the vAPI runtime.

    This exception is not part of the vAPI message protocol, and it must
    never be raised by provider implementations.

    :type messages: generator of :class:`vmware.vapi.message.Message`
    :ivar messages: Generator of error messages describing why the Exception
                    was raised
    """
    def __init__(self, message, cause=...) -> None:
        """
        Initialize CoreException

        :type  message: :class:`vmware.vapi.message.Message`
        :param message: Description regarding why the Exception was raised
        :type  cause: :class:`Exception`
        :type  cause: Exception that led to this Exception
        """
        ...
    
    @property
    def messages(self): # -> Generator[Any, Any, None]:
        """
        :rtype: generator of :class:`vmware.vapi.message.Message`
        :return: Generator of error messages describing why the Exception
                 was raised
        """
        ...
    
    def __eq__(self, other) -> bool:
        ...
    
    def __ne__(self, other) -> bool:
        ...
    
    def __str__(self) -> str:
        ...
    
    def __hash__(self) -> int:
        ...
    


