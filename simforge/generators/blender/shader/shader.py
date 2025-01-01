from typing import TYPE_CHECKING

from simforge.generators.blender.nodes import BlNodesManager

if TYPE_CHECKING:
    import bpy


class BlShader(BlNodesManager):
    def set_default_inputs(self):
        group_interface = self.nodes.group.interface
        for key, value in self.inputs.items():
            group_interface.items_tree[
                self.nodes.input_mapping[key]
            ].default_value = value  # type: ignore

    def apply_inputs(self, node: "bpy.types.Node"):
        for key, value in self.inputs.items():
            node.inputs[self.nodes.input_mapping[key]].default_value = value  # type: ignore
