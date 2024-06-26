"""
This type stub file was generated by pyright.
"""

"""
Security context parser interface for REST presentation layer
"""
__author__ = ...
__copyright__ = ...

class SecurityContextParser:
    """
    Base class for all security context builders
    """

    def build(self, request):  # -> None:
        """
        Build the security context based on the authentication
        information in the request.

        :type  request: :class:`werkzeug.wrappers.Request`
        :param request: Request object
        :rtype: :class:`vmware.vapi.core.SecurityContext`
        :return: Security context object
        """
        ...
