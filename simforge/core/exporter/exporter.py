from pathlib import Path
from typing import ClassVar, List

from pydantic import BaseModel, InstanceOf

from simforge.core.asset import AssetType
from simforge.core.exporter.file_format import (
    FileFormat,
    ImageFileFormat,
    MaterialFileFormat,
    ModelFileFormat,
)


class Exporter(BaseModel, defer_build=True):
    SUPPORTED_ASSETS: ClassVar[List[AssetType]]
    file_format: InstanceOf[FileFormat]

    def __new__(cls, *args, **kwargs):
        if cls in (Exporter, ImageExporter, MaterialExporter, ModelExporter):
            raise TypeError(f"Cannot instantiate abstract class {cls.__name__}")
        return super().__new__(cls)

    def export(self, filepath: Path | str, **kwargs) -> Path:
        raise NotImplementedError


class ImageExporter(Exporter):
    SUPPORTED_ASSETS = [AssetType.IMAGE]
    file_format: ImageFileFormat = ImageFileFormat.PNG


class MaterialExporter(Exporter):
    SUPPORTED_ASSETS = [AssetType.MATERIAL]
    file_format: MaterialFileFormat = MaterialFileFormat.MDL


class ModelExporter(Exporter):
    SUPPORTED_ASSETS = [AssetType.ARTICULATION, AssetType.GEOMETRY, AssetType.MODEL]
    file_format: ModelFileFormat = ModelFileFormat.GLTF

    @property
    def supports_material(self) -> bool:
        return self.file_format.supports_material
