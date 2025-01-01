from simforge import Articulation
from simforge.generators.blender.generator import BlGenerator

# TODO: Implement Articulated assets (interactive objects, robots, ...)


class BlArticulation(Articulation, asset_metaclass=True, asset_generator=BlGenerator):
    pass
