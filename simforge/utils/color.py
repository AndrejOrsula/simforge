import colorsys
import random
from functools import cache
from typing import Sequence, Tuple


@cache
def color_palette(
    num_hues: int,
    saturation_range: Tuple[float, float] = (0.1, 0.5),
    value_range: Tuple[float, float] = (0.8, 1.0),
) -> Sequence[Tuple[float, float, float]]:
    return [
        colorsys.hsv_to_rgb(
            i / num_hues,
            random.uniform(*saturation_range),
            random.uniform(*value_range),
        )
        for i in range(num_hues)
    ]
