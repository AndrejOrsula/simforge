from functools import cached_property

from pydantic import InstanceOf, SerializeAsAny

from simforge import Model
from simforge.generators.blender.asset import BlGeometry, BlMaterial
from simforge.generators.blender.generator import BlGenerator


class BlModel(Model, asset_metaclass=True, asset_generator=BlGenerator):
    geo: SerializeAsAny[InstanceOf[BlGeometry]]
    mat: SerializeAsAny[InstanceOf[BlMaterial]] | None = None

    @property
    def is_randomizable(self) -> bool:
        return self.geo.is_randomizable or (
            self.mat is not None and self.mat.is_randomizable
        )

    @cached_property
    def requires_baking(self) -> bool:
        return self.mat is not None or self.geo.affects_material

    def setup(self, name: str | None = None):
        if name is None:
            name = self.name()

        self.geo.setup(name=name)
        if material := self.mat:
            material.setup()
            self.geo.mesh.materials.append(material.mat)

    def cleanup(self):
        if material := self.mat:
            material.cleanup()
        self.geo.cleanup()

    def seed(self, seed: int):
        self.geo.seed(seed)
        if material := self.mat:
            material.seed(seed, geo=self.geo)
