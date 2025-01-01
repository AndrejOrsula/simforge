from enum import Enum, auto


class SemanticTag(str, Enum):
    # Material
    METAL = auto()
    PLASTIC = auto()
    # Origin
    ARTIFICIAL = auto()
    NATURAL = auto()
    # Purpose
    PRODUCT = auto()
    RESOURCE = auto()
    TOOL = auto()

    def __str__(self):
        return self.name.lower()
