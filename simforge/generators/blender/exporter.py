import math
from functools import cached_property
from pathlib import Path
from typing import Any, Dict

from simforge import ModelExporter, ModelFileFormat
from simforge.generators.blender.renderer import BlThumbnailRenderer
from simforge.utils import suppress_stdout


class BlModelExporter(ModelExporter):
    render_thumbnail: bool = True

    @cached_property
    def export_kwargs(self) -> Dict[str, Any]:
        match self.file_format:
            case ModelFileFormat.ABC:
                return {"selected": True}
            case ModelFileFormat.FBX:
                return {"use_selection": True}
            case ModelFileFormat.GLB | ModelFileFormat.GLTF | ModelFileFormat.SDF:
                return {"use_selection": True}
            case ModelFileFormat.OBJ:
                return {"export_selected_objects": True}
            case ModelFileFormat.PLY:
                return {"export_selected_objects": True}
            case ModelFileFormat.STL:
                return {"export_selected_objects": True}
            case (
                ModelFileFormat.USD
                | ModelFileFormat.USDA
                | ModelFileFormat.USDC
                | ModelFileFormat.USDZ
            ):
                return {"selected_objects_only": True, "use_instancing": True}

    @cached_property
    def renderer(self) -> BlThumbnailRenderer | None:
        if self.render_thumbnail and self.file_format == ModelFileFormat.SDF:
            renderer = BlThumbnailRenderer()
            renderer.setup()
            return renderer
        else:
            return None

    @suppress_stdout
    def export(self, filepath: Path | str, **kwargs) -> Path:
        if not isinstance(filepath, Path):
            filepath = Path(filepath)
        filepath = filepath.resolve()
        filepath.parent.mkdir(parents=True, exist_ok=True)

        export_kwargs = self.export_kwargs
        export_kwargs.update(kwargs)

        match self.file_format:
            case ModelFileFormat.ABC:
                return self._export_abc(filepath, **export_kwargs)
            case ModelFileFormat.FBX:
                return self._export_fbx(filepath, **export_kwargs)
            case ModelFileFormat.GLB | ModelFileFormat.GLTF:
                return self._export_gltf(filepath, **export_kwargs)
            case ModelFileFormat.OBJ:
                return self._export_obj(filepath, **export_kwargs)
            case ModelFileFormat.PLY:
                return self._export_ply(filepath, **export_kwargs)
            case ModelFileFormat.SDF:
                return self._export_sdf(filepath, **export_kwargs)
            case ModelFileFormat.STL:
                return self._export_stl(filepath, **export_kwargs)
            case (
                ModelFileFormat.USD
                | ModelFileFormat.USDA
                | ModelFileFormat.USDC
                | ModelFileFormat.USDZ
            ):
                return self._export_usd(filepath, **export_kwargs)

    def _export_abc(self, filepath: Path, **kwargs) -> Path:
        import bpy

        filepath = filepath.with_suffix(self.file_format.ext)
        bpy.ops.wm.alembic_export(filepath=filepath.as_posix(), **kwargs)
        return filepath

    def _export_fbx(self, filepath: Path, **kwargs) -> Path:
        import bpy

        filepath = filepath.with_suffix(self.file_format.ext)
        bpy.ops.export_scene.fbx(filepath=filepath.as_posix(), **kwargs)
        return filepath

    def _export_gltf(self, filepath: Path, **kwargs) -> Path:
        import bpy

        filepath = filepath.with_suffix(self.file_format.ext)
        bpy.ops.export_scene.gltf(filepath=filepath.as_posix(), **kwargs)
        return filepath

    def _export_obj(self, filepath: Path, **kwargs) -> Path:
        import bpy

        filepath = filepath.with_suffix(self.file_format.ext)
        bpy.ops.wm.obj_export(filepath=filepath.as_posix(), **kwargs)
        return filepath

    def _export_ply(self, filepath: Path, **kwargs) -> Path:
        import bpy

        filepath = filepath.with_suffix(self.file_format.ext)
        bpy.ops.wm.ply_export(filepath=filepath.as_posix(), **kwargs)
        return filepath

    def _export_stl(self, filepath: Path, **kwargs) -> Path:
        import bpy

        filepath = filepath.with_suffix(self.file_format.ext)
        bpy.ops.wm.stl_export(filepath=filepath.as_posix(), **kwargs)
        return filepath

    def _export_usd(self, filepath: Path, **kwargs) -> Path:
        import bpy

        filepath = filepath.with_suffix(self.file_format.ext)
        bpy.ops.wm.usd_export(filepath=filepath.as_posix(), **kwargs)
        return filepath

    def _export_sdf(self, filepath: Path, **kwargs) -> Path:
        from xml.dom import minidom
        from xml.etree import ElementTree

        import bpy

        filepath = filepath.with_suffix("")
        model_name = filepath.stem

        # Export mesh
        filepath_mesh = (
            filepath.joinpath("meshes")
            .joinpath(model_name)
            .with_suffix(ModelFileFormat.GLB.ext)
        )
        filepath_mesh.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.export_scene.gltf(filepath=filepath_mesh.as_posix(), **kwargs)

        # Write SDF
        filepath_sdf = filepath.joinpath("model.sdf")
        sdf = ElementTree.Element("sdf", attrib={"version": "1.9"})
        model = ElementTree.SubElement(sdf, "model", attrib={"name": model_name})
        link = ElementTree.SubElement(
            model, "link", attrib={"name": f"{model_name}_link"}
        )
        pose = ElementTree.SubElement(link, "pose")
        pose.text = f"0 0 0 {math.pi/2} 0 0"
        visual = ElementTree.SubElement(
            link, "visual", attrib={"name": f"{model_name}_visual"}
        )
        visual_geometry = ElementTree.SubElement(visual, "geometry")
        visual_mesh = ElementTree.SubElement(visual_geometry, "mesh")
        visual_mesh_uri = ElementTree.SubElement(visual_mesh, "uri")
        visual_mesh_uri.text = filepath_mesh.relative_to(filepath).as_posix()
        collision = ElementTree.SubElement(
            link, "collision", attrib={"name": f"{model_name}_collision"}
        )
        collision_geometry = ElementTree.SubElement(collision, "geometry")
        collision_mesh = ElementTree.SubElement(collision_geometry, "mesh")
        collision_mesh_uri = ElementTree.SubElement(collision_mesh, "uri")
        collision_mesh_uri.text = filepath_mesh.relative_to(filepath).as_posix()
        xml_str = minidom.parseString(ElementTree.tostring(sdf, encoding="unicode"))
        xml_str = xml_str.toprettyxml(indent="  ")
        sdf_file = open(filepath_sdf.as_posix(), "w")
        sdf_file.write(xml_str)
        sdf_file.close()

        # Write manifest
        filepath_manifest = filepath.joinpath("model.config")
        manifest = ElementTree.Element("model")
        name = ElementTree.SubElement(manifest, "name")
        name.text = model_name
        version = ElementTree.SubElement(manifest, "version")
        version.text = "1"
        sdf_tag = ElementTree.SubElement(manifest, "sdf", attrib={"version": "1.9"})
        sdf_tag.text = "model.sdf"
        author = ElementTree.SubElement(manifest, "author")
        producer = ElementTree.SubElement(author, "producer")
        producer.text = "SimForge"
        description = ElementTree.SubElement(manifest, "description")
        description.text = "Procedurally generated model"
        xml_str = minidom.parseString(
            ElementTree.tostring(manifest, encoding="unicode")
        )
        xml_str = xml_str.toprettyxml(indent="  ")
        manifest_file = open(filepath_manifest.as_posix(), "w")
        manifest_file.write(xml_str)
        manifest_file.close()

        if self.render_thumbnail:
            filepath_thumbnail = filepath.joinpath("thumbnails").joinpath("0.png")
            filepath_thumbnail.parent.mkdir(parents=True, exist_ok=True)
            self.renderer.render(filepath_thumbnail)  # type: ignore

        return filepath
