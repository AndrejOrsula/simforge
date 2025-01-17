from typing import ClassVar

from simforge.core.procgen import OpType
from simforge.generators.blender.asset import BlGeometry
from simforge.generators.blender.procgen import BlGeometryOp
from simforge.utils import convert_to_snake_case


class BlGeometryModifier(BlGeometryOp):
    OP_TYPE: ClassVar[OpType] = OpType.MODIFY
    MODIFIER_TYPE: ClassVar[str]

    def setup(self, geo: BlGeometry):
        import bpy

        # Create a new nodes modifier
        mod: bpy.types.Modifier = geo.obj.modifiers.new(
            name=convert_to_snake_case(self.MODIFIER_TYPE),
            type=self.MODIFIER_TYPE,  # type: ignore
        )

        # Save the modifier name (Blender automatically renames on collision)
        self._mod_name = mod.name
