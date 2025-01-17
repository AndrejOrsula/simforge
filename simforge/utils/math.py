import functools
from math import pi

__DEG_TO_RAD_MUL: float = pi / 180.0


@functools.cache
def deg_to_rad(deg: float) -> float:
    return __DEG_TO_RAD_MUL * deg
