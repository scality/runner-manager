class VmType:
    """
    Define a Virtual machine and the quantity needed
    """

    tags: list[str]
    config: dict
    quantity: dict[str, int or bool]

    def __init__(self, config):
        config["tags"].sort()
        self.tags = config["tags"]
        self.config = config["config"]
        self.quantity = config["quantity"]

    @property
    def on_demand(self) -> bool:
        return self.quantity.get("on_demand", False)

    def toJson(self) -> dict:
        """
        The fields_to_serialized, list the field to put in the dict
        :return: dict object representative of Self
        """
        d = {}
        fields_to_serialized = ["tags", "config", "quantity", "on_demand"]
        for field in fields_to_serialized:
            d[field] = self.__getattribute__(field)

        return d

    def __str__(self) -> str:
        return f"{self.tags} {self.config}"
