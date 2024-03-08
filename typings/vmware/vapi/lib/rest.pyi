"""
This type stub file was generated by pyright.
"""

"""
Common REST classes/lib
"""
__author__ = ...
__copyright__ = ...

class OperationRestMetadata:
    """
    This class holds the metadata for making a REST request

    :type http_method: :class:`str`
    :ivar http_method: HTTP method
    :type request_body_parameter: :class:`str`
    :ivar request_body_parameter: Python runtime name of the parameter that
                                  forms the HTTP request body
    """

    def __init__(
        self,
        http_method,
        url_template=...,
        request_body_parameter=...,
        path_variables=...,
        query_parameters=...,
        dispatch_parameters=...,
        header_parameters=...,
        dispatch_header_parameters=...,
        content_type=...,
    ) -> None:
        """
        Initialze the rest metadata class

        :type  http_method: :class:`str`
        :param http_method: HTTP method
        :type  url_template: :class:`str`
        :param url_template: URL path template
        :type  path_variables: :class:`dict` of :class:`str` and :class:`str`
        :param path_variables: Map of python runtime name and the path
                               variable name used in the URL template
        :type  query_parameters: :class:`dict` of :class:`str` and :class:`str`
        :param query_parameters: Map of python runtime name and query parameter
                                 name
        :type  request_body_parameter: :class:`str`
        :param request_body_parameter: Python runtime name of the parameter that
                                       forms the HTTP request body
        :type  dispatch_parameters: :class:`str`
        :param dispatch_parameters: Map of query parameter wit its value
                                    defined in interface Verb annotation
        :type  header_parameters: :class:`str`
        :param header_parameters: Map of header name with variable name
        :type  dispatch_header_parameters: :class:`str`
        :param dispatch_header_parameters: Map of header name with its value
                                           defined in interface Verb annotation
        """
        ...

    def get_url_path(self, path_variable_fields, query_parameter_fields):  # -> str:
        """
        Get the final URL path by substituting the actual values in the template
        and adding the query parameters

        :type  path_variable_fields: :class:`dict` of :class:`str` and
                                     :class:`str`
        :param path_variable_fields: Map of python runtime name for URL path
                                     variable and its value
        :type  query_parameter_fields: :class:`dict` of :class:`str` and
                                       :class:`str`
        :param query_parameter_fields: Map of python runtime name for query
                                       parameter variable and its value
        :rtype: :class:`unicode` for Python 2 and :class:`str` for Python 3
        :return: URL path
        """
        ...

    def get_path_variable_field_names(self):  # -> list[Any]:
        """
        Get the list of field names used in the URL path template

        :rtype: :class:`list` of :class:`str`
        :return: List of fields used in the URL path template
        """
        ...

    def get_query_parameter_field_names(self):  # -> list[Any]:
        """
        Get the list of field names used as query parameters

        :rtype: :class:`list` of :class:`str`
        :return: List of fields used as query parameters
        """
        ...

    def get_header_field_names(self):  # -> dict[Any, Any]:
        """
        Get the list of field names used as headers

        :rtype: :class:`list` of :class:`str`
        :return: List of fields used as header
        """
        ...

    def get_dispatch_header(self):  # -> dict[Any, Any]:
        """
        Get the map of field names and value as dispatch headers

        :rtype: :class:`list` of :class:`str`
        :return: Map of name and value as dispatch header
        """
        ...
