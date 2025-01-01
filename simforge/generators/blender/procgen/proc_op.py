from typing import TYPE_CHECKING

from simforge import ProcOp

if TYPE_CHECKING:
    from simforge.generators.blender.asset import BlGeometry


class BlGeometryOp(ProcOp):
    def setup(self, geo: "BlGeometry"):
        super().setup()

    def cleanup(self, geo: "BlGeometry"):
        super().cleanup()

    def seed(self, seed: int, geo: "BlGeometry"):
        super().seed(seed)
