"""
This type stub file was generated by pyright.
"""

from .. import utils

class ConfigApiMixin:
    @utils.minimum_version('1.30')
    def create_config(self, name, data, labels=..., templating=...):
        """
            Create a config

            Args:
                name (string): Name of the config
                data (bytes): Config data to be stored
                labels (dict): A mapping of labels to assign to the config
                templating (dict): dictionary containing the name of the
                                   templating driver to be used expressed as
                                   { name: <templating_driver_name>}

            Returns (dict): ID of the newly created config
        """
        ...
    
    @utils.minimum_version('1.30')
    @utils.check_resource('id')
    def inspect_config(self, id):
        """
            Retrieve config metadata

            Args:
                id (string): Full ID of the config to inspect

            Returns (dict): A dictionary of metadata

            Raises:
                :py:class:`docker.errors.NotFound`
                    if no config with that ID exists
        """
        ...
    
    @utils.minimum_version('1.30')
    @utils.check_resource('id')
    def remove_config(self, id): # -> Literal[True]:
        """
            Remove a config

            Args:
                id (string): Full ID of the config to remove

            Returns (boolean): True if successful

            Raises:
                :py:class:`docker.errors.NotFound`
                    if no config with that ID exists
        """
        ...
    
    @utils.minimum_version('1.30')
    def configs(self, filters=...):
        """
            List configs

            Args:
                filters (dict): A map of filters to process on the configs
                list. Available filters: ``names``

            Returns (list): A list of configs
        """
        ...
    


