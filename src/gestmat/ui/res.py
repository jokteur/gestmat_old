from ..util import Singleton


class Ressources(metaclass=Singleton):
    def __init__(self) -> None:
        self.attributes = {}

    def __getattr__(self, key):
        if key in self.attributes:
            return self.attributes[key]
        else:
            self.attributes[key] = 0
            return self.attributes[key]

    def set_attr(self, key, value):
        self.attributes[key] = value
