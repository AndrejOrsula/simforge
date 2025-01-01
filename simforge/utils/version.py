from functools import cache
from typing import Tuple


@cache
def is_semver_compatible(
    required: Tuple[int, int, int], current: Tuple[int, int, int]
) -> bool:
    return current[0] == required[0] and (
        current[1] > required[1]
        or (current[1] == required[1] and current[2] >= required[2])
    )
