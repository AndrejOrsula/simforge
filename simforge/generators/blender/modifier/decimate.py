from typing import ClassVar

from pydantic import NonNegativeFloat, NonNegativeInt, PositiveFloat

from simforge.generators.blender.asset import BlGeometry
from simforge.generators.blender.modifier.modifier import BlGeometryModifier
from simforge.utils import deg_to_rad


class __BlDecimateModifier(BlGeometryModifier):
    MODIFIER_TYPE: ClassVar[str] = "DECIMATE"


class BlCollapseDecimateModifier(__BlDecimateModifier):
    ratio: PositiveFloat

    def setup(self, geo: BlGeometry):
        import bpy

        # Create a new nodes modifier
        super().setup(geo)
        mod: bpy.types.DecimateModifier = geo.obj.modifiers[self._mod_name]  # type: ignore

        # Update parameters
        mod.decimate_type = "COLLAPSE"
        mod.ratio = self.ratio


class BlUnsubdivDecimateModifier(__BlDecimateModifier):
    iterations: NonNegativeInt

    def setup(self, geo: BlGeometry):
        import bpy

        # Create a new nodes modifier
        super().setup(geo)
        mod: bpy.types.DecimateModifier = geo.obj.modifiers[self._mod_name]  # type: ignore

        # Update parameters
        mod.decimate_type = "UNSUBDIV"
        mod.iterations = self.iterations


class BlPlanarDecimateModifier(__BlDecimateModifier):
    angle_limit: NonNegativeFloat
    deg: bool = True

    def setup(self, geo: BlGeometry):
        import bpy

        # Create a new nodes modifier
        super().setup(geo)
        mod: bpy.types.DecimateModifier = geo.obj.modifiers[self._mod_name]  # type: ignore

        # Update parameters
        mod.decimate_type = "DISSOLVE"
        if self.deg:
            mod.angle_limit = deg_to_rad(self.angle_limit)
        else:
            mod.angle_limit = self.angle_limit
