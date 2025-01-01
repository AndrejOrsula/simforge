from enum import Enum, auto


class AssetType(str, Enum):
    ARTICULATION = auto()
    GEOMETRY = auto()
    IMAGE = auto()
    MATERIAL = auto()
    MODEL = auto()

    def __str__(self) -> str:
        return self.name.lower()
