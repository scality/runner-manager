class VmType:
    tags: list[str]
    flavor: str
    image: str
    quantity: int

    def __init__(self, config):
        self.tags = config['tags']
        self.flavor = config['flavor']
        self.image = config['image']
        self.quantity = config['quantity']
