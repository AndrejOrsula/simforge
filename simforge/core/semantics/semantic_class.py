from enum import Enum, auto


class SemanticClass(str, Enum):
    MATERIAL = auto()
    ORIGIN = auto()
    PURPOSE = auto()

    def __str__(self):
        return self.name.lower()
