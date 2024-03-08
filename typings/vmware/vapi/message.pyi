"""
This type stub file was generated by pyright.
"""

"""
vAPI Message class
"""
__author__ = ...
__copyright__ = ...

class Message:
    """
    This class encapsulates the concept of a localizable message.

    :type id_: :class:`string`
    :ivar id_: The unique message identifier
    :type def_msg: :class:`string`
    :ivar def_msg: An english language default
    :type args: :class:`list` of :class:`string`
    :ivar args: The arguments to be used for the messsage
    """

    def __init__(self, id_, def_msg, *args) -> None:
        """
        Initializes the message object

        :type  id_: :class:`string`
        :param id_: The unique message identifier
        :type  def_msg: :class:`string`
        :param def_msg: An english language default
        :type  args: :class:`list` of :class:`string`
        :param args: The arguments to be used for the messsage
        """
        ...

    def __eq__(self, other) -> bool: ...
    def __ne__(self, other) -> bool: ...
    def __repr__(self):  # -> str:
        ...

    def __str__(self) -> str: ...

class MessageFormatter:
    """
    Base class for all message formatter classes
    """

    @classmethod
    def format_msg(cls, msg, args):
        """
        Format the message using the specified arguments

        :type  msg: :class:`str`
        :param msg: Message template
        :type  args: :class:`list` of :class:`object`
        :param args: Arguments for the message
        :rtype: :class:`str`
        :return: Localized message
        """
        ...

class MessageBundle:
    """
    Base class for all message bundle classes.
    """

    def __init__(self, messages) -> None:
        """
        Initialize MessageBundle.

        :type  messages: :class:`dict` of :class:`str`, :class:`str`
        :param messages: Dictionary with message identifiers as keys and
            message templates as values.
        """
        ...

    def get(self, msg_id):
        """
        Returns the message template for the given message identifier

        :type  msg_id: :class:`str`
        :param msg_id: Message identifier
        :rtype: :class:`str`
        :return: Message template
        :raise KeyError: If the message identifier is not found
        """
        ...

class MessageFactory:
    """
    A factory class to generate localizable messages
    """

    def __init__(self, msg_bundle, formatter) -> None:
        """
        Initializes the message object

        :type  msg_bundle: :class:`MessageBundle`
        :param messages: The message dictionary for the message factory
        :type  formatter: :class:`vmware.vapi.formatter.MessageFormatter`
        :param formatter: Formatter for the message
        """
        ...

    def get_message(self, id_, *args):  # -> Message:
        """
        Return a message object for the given id with the given args.
        If the message is not found, a default unknown message is returned.

        :type  id_: string
        :param id_: The unique message identifier
        :type  args: :class:`list` of :class:`object`
        :param args: The arguments to be used for constructing this message
        :rtype: :class:`Message`
        :return: The message object constructed using the given arguments
        """
        ...
