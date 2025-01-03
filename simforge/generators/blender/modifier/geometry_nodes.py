from typing import TYPE_CHECKING

from simforge.generators.blender.asset import BlGeometry, BlMaterial, BlModel
from simforge.generators.blender.modifier.modifier import BlGeometryModifier
from simforge.generators.blender.nodes import BlNodesManager

if TYPE_CHECKING:
    import bpy


class BlGeometryNodesModifier(BlGeometryModifier, BlNodesManager):
    @property
    def is_randomizable(self) -> bool:
        return self.nodes.is_randomizable or self.affects_material

    def setup(self, geo: "BlGeometry"):
        import bpy

        # Create a new nodes modifier
        mod: bpy.types.NodesModifier = geo.obj.modifiers.new(
            name=self.nodes.name, type="NODES"
        )  # type: ignore

        # Save the modifier name (Blender automatically renames on collision)
        self._mod_name = mod.name

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
