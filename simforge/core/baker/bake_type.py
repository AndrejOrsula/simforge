from enum import Enum, auto


class BakeType(str, Enum):
    ALBEDO = auto()
    EMISSION = auto()
    METALLIC = auto()
    NORMAL = auto()
    ROUGHNESS = auto()
