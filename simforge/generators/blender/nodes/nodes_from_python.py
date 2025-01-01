from typing import TYPE_CHECKING

from pydantic import FilePath

from simforge.generators.blender.nodes.nodes import BlNodes
from simforge.utils import logging

if TYPE_CHECKING:
    import bpy


class BlNodesFromPython(BlNodes):
    python_file: FilePath

    @property
    def group(
        self,
    ) -> "bpy.types.NodeTree | bpy.types.CompositorNodeTree | bpy.types.ShaderNodeTree | bpy.types.GeometryNodeTree | bpy.types.TextureNodeTree":
        import bpy

        self.load()
        return bpy.data.node_groups[self.name]

    def load(self):
        import bpy

        if self.name in bpy.data.node_groups.keys():
            return

        logging.debug(f"Loading nodes from Python script: {self.python_file}")
        bpy.ops.script.python_file_run(filepath=self.python_file.as_posix())

        if self.name not in bpy.data.node_groups.keys():
            raise ValueError(
                f'Node group "{self.name}" is not available after running the Python script: {self.python_file}'
            )
