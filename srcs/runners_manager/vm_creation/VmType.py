class VmType:
    """
    Define a Virtual machine and the quantity needed
    """

    tags: list[str]
    config: dict
    quantity: dict[str, int]

    def __init__(self, config):
        config["tags"].sort()
        self.tags = config["tags"]
        self.config = config["config"]
        self.quantity = config["quantity"]

    def toJson(self):
        """
        The fields_to_serialized, list the field to put in the dict
        :return: dict object representative of Self
        """
        d = {}
        fields_to_serialized = ["tags", "config", "quantity"]
        for field in fields_to_serialized:
            d[field] = self.__getattribute__(field)

        return d

    def __str__(self):
        return f"{self.tags} {self.config}"
