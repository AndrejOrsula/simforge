from functools import cached_property
from typing import TYPE_CHECKING

from pydantic import InstanceOf

from simforge import Material
from simforge.generators.blender.generator import BlGenerator
from simforge.generators.blender.shader import BlShader
from simforge.utils import logging

if TYPE_CHECKING:
    import bpy

    from simforge.generators.blender.asset import BlGeometry


class BlMaterial(Material, asset_metaclass=True, asset_generator=BlGenerator):
    shader: InstanceOf[BlShader]

    @property
    def mat(self) -> "bpy.types.Material":
        assert hasattr(self, "_mat"), f'"{self.setup.__name__}" not called'
        return self._mat

    @cached_property
    def is_randomizable(self) -> bool:
        return self.shader.is_randomizable

    def setup(self):
        import bpy

        mat_name = self.shader.nodes.name.replace("Shader", "Material")

        # Check if the material already exists
        if mat_name in bpy.data.materials:
            self._mat = bpy.data.materials[mat_name]
            return

        # Create a new material
        self._mat = bpy.data.materials.new(name=mat_name)
        self.mat.use_nodes = True
        node_tree: bpy.types.ShaderNodeTree = self.mat.node_tree  # type: ignore
        nodes = node_tree.nodes
        links = node_tree.links
        nodes.clear()

        # Setup the material with the shader
        output_node: bpy.types.ShaderNodeOutputMaterial = nodes.new(
            type="ShaderNodeOutputMaterial"
        )  # type: ignore
        shader_group: bpy.types.ShaderNodeGroup = node_tree.nodes.new("ShaderNodeGroup")  # type: ignore
        shader_group.node_tree = self.shader.nodes.group  # type: ignore
        shader_outputs = [
            output for output in shader_group.outputs if output.type == "SHADER"
        ]
        match len(shader_outputs):
            case 0:
                raise ValueError("Shader group has no viable outputs")
            case too_many if too_many > 1:
                logging.warning(
                    f"Shader group has {too_many} viable outputs but only the first will be used"
                )
        links.new(shader_outputs[0], output_node.inputs["Surface"])

        # Apply the shader group inputs
        self.shader.apply_inputs(shader_group)

    def cleanup(self):
        import bpy

        # Remove the material
        bpy.data.materials.remove(self.mat)

    def seed(self, seed: int, geo: "BlGeometry | None" = None):
        import bpy

        if not self.is_randomizable:
            return

        if geo is None:
            obj: bpy.types.Object = bpy.context.active_object  # type: ignore
        else:
            obj = geo.obj

        obj.modifiers[self.shader.nodes.name][
            self.shader.nodes.input_mapping["seed"]
        ] = seed
