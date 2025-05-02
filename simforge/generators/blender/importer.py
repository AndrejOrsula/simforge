import os
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Dict

from pydantic import field_validator

from simforge import ModelFileFormat
from simforge.core.procgen import OpType
from simforge.generators.blender.procgen.proc_op import BlGeometryOp
from simforge.utils import suppress_stdout
from simforge.utils.cache import SF_CACHE_DIR

if TYPE_CHECKING:
    from simforge import BlGeometry


class BlModelImporter(BlGeometryOp):
    OP_TYPE: ClassVar[OpType] = OpType.GENERATE
    filepath: Path
    import_kwargs: Dict[str, Any] = {}

    @field_validator("filepath", mode="before")
    def relative_filepath(cls, filepath: Path) -> Path:
        return Path(os.path.relpath(filepath.resolve(), SF_CACHE_DIR))

    @cached_property
    def file_format(self) -> ModelFileFormat | None:
        return ModelFileFormat.from_ext(self.filepath.suffix)

    @suppress_stdout
    def setup(self, geo: "BlGeometry"):
        import bpy

        # Remove the original (empty) object and mesh
        bpy.data.objects.remove(geo.obj)
        bpy.data.meshes.remove(geo.mesh)

        # Import the model
        match self.file_format:
            case ModelFileFormat.ABC:
                bpy.ops.wm.alembic_import(
                    filepath=self.filepath.as_posix(), **self.import_kwargs
                )
            case ModelFileFormat.FBX:
                bpy.ops.import_scene.fbx(
                    filepath=self.filepath.as_posix(), **self.import_kwargs
                )
            case ModelFileFormat.GLB | ModelFileFormat.GLTF:
                bpy.ops.import_scene.gltf(
                    filepath=self.filepath.as_posix(), **self.import_kwargs
                )
            case ModelFileFormat.OBJ:
                bpy.ops.wm.obj_import(
                    filepath=self.filepath.as_posix(), **self.import_kwargs
                )
            case ModelFileFormat.PLY:
                bpy.ops.wm.ply_import(
                    filepath=self.filepath.as_posix(), **self.import_kwargs
                )
            case ModelFileFormat.STL:
                bpy.ops.wm.stl_import(
                    filepath=self.filepath.as_posix(), **self.import_kwargs
                )
            case (
                ModelFileFormat.USD
                | ModelFileFormat.USDA
                | ModelFileFormat.USDC
                | ModelFileFormat.USDZ
            ):
                bpy.ops.wm.usd_import(
                    filepath=self.filepath.as_posix(), **self.import_kwargs
                )
            case ModelFileFormat.SDF:
                raise NotImplementedError("Direct SDF import is not supported")
            case _:
                raise ValueError(f"Unsupported file format: {self.filepath}")

        # Join all imported objects into a single object
        bpy.ops.object.join()

        # Use the active object as the object of the geometry
        if obj := bpy.context.active_object:
            geo._obj = obj
            geo._obj.name = geo.name()
        else:
            raise ValueError(
                f"No active object is available after importing {self.filepath}"
            )
        if isinstance(geo.obj.data, bpy.types.Mesh):
            geo._mesh = geo.obj.data
            geo._mesh.name = geo.name()
        else:
            raise ValueError(f"Active object {geo.obj} does not have a mesh data block")
