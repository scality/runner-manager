"""
This type stub file was generated by pyright.
"""

import json

"""
JSON encoder for double values
"""
__author__ = ...
__copyright__ = ...
logger = ...
def canonicalize_double(obj): # -> str:
    """
    Canonicalize double based on XML schema double canonical format

    The exponent must be indicated by "E". Leading zeroes and the
    preceding optional "+" sign are prohibited in the exponent. If the
    exponent is zero, it must be indicated by "E0". For the mantissa, the
    preceding optional "+" sign is prohibited and the decimal point is
    required. Leading and trailing zeroes are prohibited subject to the
    following: number representations must be normalized such that there
    is a single digit which is non-zero to the left of the decimal point
    and at least a single digit to the right of the decimal point unless
    the value being represented is zero. The canonical representation
    for zero is 0.0E0
    http://www.w3.org/TR/xmlschema-2/#double

    :type  obj: :class:`decimal.Decimal`
    :param obj: Decimal object to be canonicalized
    :rtype: :class:`str`
    :return: Canonical string representation of the decimal
    """
    ...

class DecimalEncoder(json.JSONEncoder):
    """
    Class that adds capability of encoding decimal
    in JSON
    """
    def default(self, obj): # -> Generator[text_type, None, None] | Any:
        ...
    


