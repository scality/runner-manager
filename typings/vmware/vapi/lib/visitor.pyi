"""
This type stub file was generated by pyright.
"""

"""
Visitor helper class
"""
__author__ = ...
__copyright__ = ...

class VapiVisitor:
    """
    Convenience class for visitors used in vAPI Python runtime
    """

    def __init__(self, suffix=...) -> None:
        """
        Initialize VapiVisitor

        :type  suffix: :class:`str`
        :param suffix: The suffix string that should be removed from
                       class name during the dispatch
        """
        ...

    def visit(self, value):  # -> Any:
        """
        Dispatch the call to the appropriate method based
        on the type of the input argument

        :type  value: :class:`object`
        :param value: The object to be used for dispatch
        """
        ...
