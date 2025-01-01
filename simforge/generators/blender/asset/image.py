from simforge import Image
from simforge.generators.blender.generator import BlGenerator

# TODO: Implement Image assets (heighmaps, HDRIs, ...)


class BlImage(Image, asset_metaclass=True, asset_generator=BlGenerator):
    pass
