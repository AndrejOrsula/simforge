from typing import ClassVar

from simforge.generators.blender.modifier.modifier import BlGeometryModifier


class BlTriangulateModifier(BlGeometryModifier):
    MODIFIER_TYPE: ClassVar[str] = "TRIANGULATE"
