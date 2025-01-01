from enum import Enum, auto


class OpType(str, Enum):
    GENERATE = auto()
    MODIFY = auto()
