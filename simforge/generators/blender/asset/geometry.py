from __future__ import annotations

from typing import TYPE_CHECKING, List

from pydantic import InstanceOf

from simforge import Geometry
from simforge.generators.blender.generator import BlGenerator
from simforge.generators.blender.procgen.proc_op import BlGeometryOp

if TYPE_CHECKING:
    import bpy


class BlGeometry(Geometry, asset_metaclass=True, asset_generator=BlGenerator):
    ops: List[InstanceOf[BlGeometryOp]]

    @property
    def obj(self) -> "bpy.types.Object":
        assert hasattr(self, "_obj"), f'"{self.setup.__name__}" not called'
        return self._obj

    @property
    def mesh(self) -> "bpy.types.Mesh":
        assert hasattr(self, "_mesh"), f'"{self.setup.__name__}" not called'
        return self._mesh

    @property
    def is_randomizable(self) -> bool:
        return any(op.is_randomizable for op in self.ops)

    @property
    def affects_material(self) -> bool:
        return any(getattr(op, "affects_material", False) for op in self.ops)

    def setup(self, name: str | None = None):
        import bpy

        if name is None:
            name = self.name

        # Create a new mesh object
        self._mesh = bpy.data.meshes.new(name)
        self._obj = bpy.data.objects.new(name, self.mesh)

        # Link, make active and select the object
        context: bpy.types.Context = bpy.context  # type: ignore
        context.scene.collection.objects.link(self.obj)
        context.view_layer.objects.active = self.obj
        self.obj.select_set(True)

        # Process all operations
        for op in self.ops:
            op.setup(self)

        # Update the mesh
        self.mesh.update()

    def cleanup(self):
        import bpy

        # Cleanup all operations
        for op in self.ops:
            op.cleanup(self)

        # Remove the object and mesh
        bpy.data.objects.remove(self.obj)
        bpy.data.meshes.remove(self.mesh)

    def seed(self, seed: int):
        if not self.is_randomizable:
            return

        # Seed all operations
        for op in self.ops:
            op.seed(seed, self)

        # Update the mesh
        self.mesh.update()

    def duplicate(self, name: str = "{NAME}") -> BlGeometry:
        import bpy

        # Duplicate the object
        duplicate_obj = self.obj.copy()
        duplicate_obj.data = self.mesh.copy()

        # Rename the object
        duplicate_obj.name = name.replace("{NAME}", self.obj.name)
        duplicate_obj.data.name = name.replace("{NAME}", self.mesh.name)

        # Link, make active and select the object
        context: bpy.types.Context = bpy.context  # type: ignore
        context.scene.collection.objects.link(duplicate_obj)
        context.view_layer.objects.active = duplicate_obj
        self.obj.select_set(False)
        duplicate_obj.select_set(True)

        # Duplicate the asset
        duplicate_asset = self.model_copy()
        duplicate_asset._obj = duplicate_obj
        duplicate_asset._mesh = duplicate_obj.data

        return duplicate_asset
