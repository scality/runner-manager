"""
This type stub file was generated by pyright.
"""

import threading

"""
Utility functions for managing execution context for an operation
"""
__author__ = ...
__copyright__ = ...
TLS = threading.local()

def set_context(ctx):  # -> None:
    """
    Set the execution context in thread local storage

    :type: :class:`vmware.vapi.core.ExecutionContext`
    :param: Execution context
    """
    ...

def clear_context():  # -> None:
    """
    Clear the execution context from thread local storage
    """
    ...

def get_context():  # -> Any | None:
    """
    Get the execution context from thread local storage

    :rtype: :class:`vmware.vapi.core.ExecutionContext` or :class:`NoneType`
    :return: The execution context if present
    """
    ...

def set_event(event):  # -> None:
    """
    Set the event in thread local storage

    :type: :class:`threading.Event`
    :param: Event
    """
    ...

def clear_event():  # -> None:
    """
    Clear the event from thread local storage
    """
    ...

def get_event():  # -> Any | None:
    """
    Get the event from thread local storage

    :rtype: :class:`threading.Event` or :class:`NoneType`
    :return: Event if present
    """
    ...
