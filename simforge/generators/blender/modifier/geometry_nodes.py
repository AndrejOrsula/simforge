from typing import TYPE_CHECKING, ClassVar

from simforge.core.procgen import OpType
from simforge.generators.blender.asset import BlGeometry, BlMaterial, BlModel
from simforge.generators.blender.modifier.modifier import BlGeometryModifier
from simforge.generators.blender.nodes import BlNodesManager

if TYPE_CHECKING:
    import bpy


class BlGeometryNodesModifier(BlGeometryModifier, BlNodesManager):
    OP_TYPE: ClassVar[OpType] = OpType.GENERATE
    MODIFIER_TYPE: ClassVar[str] = "NODES"

    @property
    def is_randomizable(self) -> bool:
        return self.nodes.is_randomizable or self.affects_material_randomized

    def setup(self, geo: "BlGeometry"):
        import bpy

        # Create a new nodes modifier
        super().setup(geo)
        mod: bpy.types.NodesModifier = geo.obj.modifiers[self._mod_name]  # type: ignore

        # Assign the nodes
        mod.node_group = self.nodes.group

        # Apply inputs
        self.apply_inputs(mod)

    def seed(self, seed: int, geo: "BlGeometry"):
        if not self.is_randomizable:
            return

        # Seed the modifier via its inputs
        geo.obj.modifiers[self._mod_name][self.nodes.input_mapping["seed"]] = seed

    def apply_inputs(self, mod: "bpy.types.NodesModifier"):
        for key, value in self.inputs.items():
            match value:
                case mat if isinstance(mat, BlMaterial):
                    mat.setup()
                    mod[self.nodes.input_mapping[key]] = mat.mat
                case geo if isinstance(geo, BlGeometry):
                    geo.setup()
                    mod[self.nodes.input_mapping[key]] = geo.obj
                case model if isinstance(model, BlModel):
                    model.setup()
                    mod[self.nodes.input_mapping[key]] = model.geo.obj
                case _:
                    mod[self.nodes.input_mapping[key]] = value

    @property
    def affects_material(self) -> bool:
        return any(
            key in self.nodes.material_input_names
            for key, value in self.inputs.items()
            if value is not None
        )

    @property
    def affects_material_randomized(self) -> bool:
        return any(
            value.is_randomizable
            for key, value in self.inputs.items()
            if value is not None and key in self.nodes.material_input_names
        )
