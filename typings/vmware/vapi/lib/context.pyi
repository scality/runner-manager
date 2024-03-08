"""
This type stub file was generated by pyright.
"""

"""
Factory methods for creating application context
"""
__author__ = ...
__copyright__ = ...
def create_operation_id(): # -> str:
    """
    Create a new operation id. It is a randomly generated uuid

    :rtype: :class:`str`
    :return: Newly created operation id
    """
    ...

def create_default_application_context(): # -> ApplicationContext:
    """
    Create a default application context. The
    created context will only have opId.

    :rtype: :class:`vmware.vapi.core.ApplicationContext`
    :return: Newly created application context
    """
    ...

def insert_operation_id(app_ctx): # -> None:
    """
    Add an operation id to the application context if there is none present.
    If an operation id is present, then this is a no op.

    :type app_ctx: :class:`vmware.vapi.core.ApplicationContext`
    :param app_ctx: Application context
    """
    ...

def insert_task_id(app_ctx, task_id): # -> None:
    """
    Add a task id to the application context.

    :type app_ctx: :class:`vmware.vapi.core.ApplicationContext`
    :param app_ctx: Application Context
    :type task_id: :class:`str`
    :param task_id: Task Id
    """
    ...

def remove_task_id(app_ctx): # -> None:
    """
    Remove a task id from the application context.

    :type app_ctx: :class:`vmware.vapi.core.ApplicationContext`
    :param app_ctx: Application Context
    """
    ...

def get_task_id(): # -> Any | None:
    """
    Return task id stored in application context.
    Return None if there's no task id present.

    :rtype: :class:`str`
    :return: Task Id
    """
    ...

def insert_header(app_ctx, key, value): # -> None:
    """
    Add a key, value pair in application context.
    If the key exists override the value.

    :type  app_ctx: :class:`vmware.vapi.core.ApplicationContext`
    :param app_ctx: Application Context
    :type  key: :class:`str`
    :param key: Application context key
    :type  value: :class:`str`
    :param value: Application context key value
    """
    ...

