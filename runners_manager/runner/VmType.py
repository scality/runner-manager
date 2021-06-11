class VmType:
    tags: list[str]
    flavor: str
    image: str
    quantity: dict[str, int]

    def __init__(self, config):
        self.tags = config['tags']
        self.flavor = config['flavor']
        self.image = config['image']
        self.quantity = config['quantity']

    def __str__(self):
        return f"{self.flavor}: {self.image}"
