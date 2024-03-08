"""
This type stub file was generated by pyright.
"""

import abc
import six

"""
Connecter interface
"""
__author__ = ...
__copyright__ = ...

@six.add_metaclass(abc.ABCMeta)
class Connector:
    """Connector interface"""

    def __init__(self, api_provider, provider_filter_chain) -> None:
        """
        Connector constructor

        :type  api_provider: :class:`vmware.vapi.core.ApiProvider`
        :param api_provider: API Provider
        :type  provider_filter_chain: :class:`list` of
            :class:`vmware.vapi.provider.filter.ApiProviderFilter`
        :param provider_filter_chain: List of API filters in order they are to
            be chained
        """
        ...

    @abc.abstractmethod
    def connect(self):  # -> None:
        """rpc provider connect"""
        ...

    @abc.abstractmethod
    def disconnect(self):  # -> None:
        """rpc provider disconnect"""
        ...

    def set_application_context(self, ctx):  # -> None:
        """
        Set the application context

        All the subsequent calls made using this
        connector will use this as the application
        context in the ExecutionContext

        :type  ctx: :class:`vmware.vapi.core.ApplicationContext`
        :param ctx: New application context
        """
        ...

    def set_security_context(self, ctx):  # -> None:
        """
        Set the security context

        All the subsequent calls made using this
        connector will use this as the security
        context in the ExecutionContext

        :type  ctx: :class:`vmware.vapi.core.SecurityContext`
        :param ctx: New security context
        """
        ...

    def new_context(self, runtime_data=...):  # -> ExecutionContext:
        """
        create new execution context object

        :type  runtime_data: :class:`vmware.vapi.core.RuntimeData`    # pylint: disable=line-too-long
        :param runtime_data: Http runtime data
        :rtype:  :class:`vmware.vapi.core.ExecutionContext`
        :return: execution context
        """
        ...

    def get_api_provider(self):
        """
        get api provider

        :rtype:  :class:`vmware.vapi.core.ApiProvider`
        :return: api provider
        """
        ...
