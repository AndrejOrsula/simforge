import colorsys
import random
from functools import cache
from typing import Sequence, Tuple


@cache
def color_palette_hue(
    num_colors: int,
    hue_start_range: Tuple[float, float] = (0.0, 1.0),
    saturation_range: Tuple[float, float] = (0.6, 0.8),
    value_range: Tuple[float, float] = (0.4, 0.6),
) -> Sequence[Tuple[float, float, float]]:
    hue_start = random.uniform(*hue_start_range)
    return [
        colorsys.hsv_to_rgb(
            (hue_start + i / num_colors) % 1.0,
            random.uniform(*saturation_range),
            random.uniform(*value_range),
        )
        for i in range(num_colors)
    ]
