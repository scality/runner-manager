class VmType:
    """
    Define the Virtual machines and who much to spawn
    """
    tags: list[str]
    flavor: str
    image: str
    quantity: dict[str, int]

    def __init__(self, config):
        config['tags'].sort()
        self.tags = config['tags']
        self.flavor = config['flavor']
        self.image = config['image']
        self.quantity = config['quantity']

    def toJson(self):
        """
        The fields_to_serialized, list the field to put in the dict
        :return: dict object representative of Self
        """
        d = {}
        fields_to_serialized = ["tags", "flavor", "image", "quantity"]
        for field in fields_to_serialized:
            d[field] = self.__getattribute__(field)

        return d

    def __str__(self):
        return f"{self.flavor}: {self.image}"
