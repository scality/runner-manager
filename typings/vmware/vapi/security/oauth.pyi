"""
This type stub file was generated by pyright.
"""

from vmware.vapi.security.rest import SecurityContextParser

"""
Oauth2 Security Helper
"""
__author__ = ...
__copyright__ = ...
OAUTH_SCHEME_ID = ...
ACCESS_TOKEN = ...
AUTHORIZATION = ...
BEARER = ...

def create_oauth_security_context(access_token):  # -> SecurityContext:
    """
    Create a security context for Oauth2 based authentication
    scheme

    :type  access_token: :class:`str`
    :param access_token: Access token
    :rtype: :class:`vmware.vapi.core.SecurityContext`
    :return: Newly created security context
    """
    ...

class OAuthSecurityContextParser(SecurityContextParser):
    """
    Security context parser used by the REST presentation layer
    that builds a security context if the REST request has OAuth2
    access token in the header.
    """

    def __init__(self) -> None:
        """
        Initialize OAuthSecurityContextParser
        """
        ...

    def build(self, request):  # -> SecurityContext | None:
        """
        Build the security context if the request has authorization
        header that contains OAuth2 access token.

        If the request authorization header doesn't have the OAuth2
        access token, this method returns None.

        :type  request: :class:`werkzeug.wrappers.Request`
        :param request: Request object
        :rtype: :class:`vmware.vapi.core.SecurityContext` or ``None``
        :return: Security context object
        """
        ...
